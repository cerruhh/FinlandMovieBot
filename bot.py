import os
import sys
import asyncio
import time
import json
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from logging_config import setup_uniform_logging

# Initialize the logger
logger = setup_uniform_logging("FinlandMovieBot")

# Mute the noisy network logs from Telegram's background libraries
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

# --- Configuration: Load Secrets ---
try:
    with open("Data/secrets.json", "r") as secret_file:
        secrets = json.load(secret_file)
        TOKEN = secrets["telegram_token"]
        ALLOWED_USER_IDS = secrets["allowed_user_ids"] # Now a list!
except Exception as e:
    logger.error(f"❌ ERROR loading secrets: {e}")
    sys.exit(1)
except FileNotFoundError:
    logger.error("❌ ERROR: Data/secrets.json not found! Please create it.")
    sys.exit(1)
except KeyError as e:
    logger.error(f"❌ ERROR: Missing key {e} in Data/secrets.json.")
    sys.exit(1)
except ValueError:
    logger.error("❌ ERROR: telegram_user_id in secrets.json must be a number.")
    sys.exit(1)

# Create a lock so only one person can scrape at a time
scrape_lock = asyncio.Lock()


async def add_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Adds a new user ID to the secrets.json file."""
    # SECURITY: Only the first person in the list (you) can add others
    if update.effective_user.id != ALLOWED_USER_IDS[0]:
        await update.message.reply_text("⛔ Only the primary admin can add new users.")
        return

    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("⚠️ Please provide a numeric User ID. Usage: `/add_user 123456789`",
                                        parse_mode="Markdown")
        return

    new_id = int(context.args[0])

    if new_id in ALLOWED_USER_IDS:
        await update.message.reply_text("ℹ️ That user is already authorized.")
        return

    # Update the local list
    ALLOWED_USER_IDS.append(new_id)

    # Save to secrets.json permanently
    try:
        # Load current file to preserve other keys (like the token)
        with open("Data/secrets.json", "r") as f:
            data = json.load(f)

        data["allowed_user_ids"] = ALLOWED_USER_IDS

        with open("Data/secrets.json", "w") as f:
            json.dump(data, f, indent=4)

        await update.message.reply_text(f"✅ User `{new_id}` has been authorized and saved to secrets!",
                                        parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Failed to save to secrets.json: {e}")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a greeting when you type /start"""
    if update.effective_user.id not in ALLOWED_USER_IDS:
        await update.message.reply_text("Sorry, you are not authorized to use this bot.")
        return

    await update.message.reply_text(
        "Hello! I this is Helsinki Film Scraper.\n"
        "Commands:\n"
        "/scrape today - Runs for today, tomorrow\n"
        "/scrape # - Runs over # days\n"
        "/add_user ###### - Adds a user_id -> @userinfobot"
    )


async def run_scraper(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in ALLOWED_USER_IDS:
        logger.warning(f"Unauthorized scrape attempt by {user.id}")
        return

    if scrape_lock.locked():
        logger.info(f"Scrape requested by {user.id} while lock is active.")
        await update.message.reply_text("⏳ The scraper is currently busy with another user. Please wait.")
        return

    # Lock the doors! Only one scrape runs inside this block at a time.
    async with scrape_lock:
        logger.info(f"Scrape started by {user.first_name} ({user.id})")

        # 1. Parse Arguments
        offset_arg = "1"  # Default
        display_name = "tomorrow"

        if context.args:
            user_input = context.args[0].lower()
            if user_input == "today":
                offset_arg = "0"
                display_name = "today"
            elif user_input == "tomorrow":
                offset_arg = "1"
                display_name = "tomorrow"
            elif user_input.isdigit() or (user_input.startswith('-') and user_input[1:].isdigit()):
                offset_arg = user_input
                display_name = f"offset {user_input}"
            else:
                await update.message.reply_text("⚠️ Invalid argument. Use: /scrape today, /scrape tomorrow, or /scrape 2")
                return


        status_msg = await update.message.reply_text(f"🎬 Starting the scraper for {display_name}...")

        # 2. Run Subprocess with Unbuffered Output
        # We use sys.executable to ensure we use the venv's python
        cmd = [sys.executable, "-u", "main.py", offset_arg]
        #if offset_arg:
        #    cmd.append(offset_arg)

        try:
            # 3. Start the subprocess asynchronously
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT  # Combine errors into standard output
            )

            output_buffer = []
            last_update_time = time.time()

            # 3. Stream output to log file
            while True:
                line = await process.stdout.readline()
                if not line:
                    break

                decoded_line = line.decode('utf-8', errors='ignore').strip()
                if decoded_line:
                    # Save to your uniform log file
                    logger.info(f"[SCRAPER] {decoded_line}")

                    # Add to Telegram buffer
                    output_buffer.append(decoded_line)
                    # Keep only the last 15 lines so the Telegram message doesn't become massive
                    output_buffer = output_buffer[-15:]

                    # Update the Telegram message every 2 seconds to avoid rate limits
                    if time.time() - last_update_time > 2.0:
                        try:
                            display_text = f"⏳ **Running Scraper ({display_name})...**\n```text\n" + "\n".join(
                                output_buffer) + "\n```"
                            await status_msg.edit_text(display_text, parse_mode="Markdown")
                            last_update_time = time.time()
                        except Exception:
                            pass  # Ignore minor Telegram errors like "Message is not modified"

            # Wait for the process to fully close
            await process.wait()

            # Final update to the status box
            try:
                final_text = f"✅ **Scraping Finished!**\n```text\n" + "\n".join(output_buffer[-5:]) + "\n```"
                await status_msg.edit_text(final_text, parse_mode="Markdown")
            except Exception:
                pass

            if process.returncode == 0:
                logger.info("Scraper finished successfully. Sending files.")

                excel_path = "Data/output.xlsx"
                txt_path = "Data/output.txt"

                if os.path.exists(excel_path) and os.path.exists(txt_path):
                    # Send the files to the user
                    await update.message.reply_document(document=open(txt_path, 'rb'))
                    await update.message.reply_document(document=open(excel_path, 'rb'))

                    # CLEANUP: Delete the files so the next user gets a fresh slate
                    os.remove(excel_path)
                    os.remove(txt_path)

                    # Optional: Send a final success message
                    await update.message.reply_text("✅ Scraping completed and files delivered!")
                else:
                    logger.warning("Script finished, but output files were missing.")
                    await update.message.reply_text("⚠️ Script finished, but output files were missing.")
            else:
                logger.error(f"Scraper exited with error code {process.returncode}")
                await update.message.reply_text("❌ Scraper encountered an error.")

        except Exception as e:
            logger.error(f"Subprocess crash: {e}")
            await update.message.reply_text(f"❌ System error: {e}")


async def notify_startup(application: Application):
    """Sends a message to the first admin in the list when the bot boots up."""
    try:
        # Use the first ID in the list
        admin_id = ALLOWED_USER_IDS[0]
        await application.bot.send_message(
            chat_id=admin_id,
            text="🤖 *FinlandMovieBot* is online and ready on morko! \nUse /scrape to get started.",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.info(f"Failed to send startup message: {e}")


if __name__ == '__main__':
    logger.info("Starting FinlandMovieBot engine...")
    app = Application.builder().token(TOKEN).post_init(notify_startup).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("scrape", run_scraper))
    app.add_handler(CommandHandler("add_user", add_user))

    logger.info("Bot is listening! Send /start to it on Telegram.")
    app.run_polling()