import os
import sys
import asyncio
import time
import json
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes


# --- Configuration: Load Secrets ---
try:
    with open("Data/secrets.json", "r") as secret_file:
        secrets = json.load(secret_file)
        TOKEN = secrets["telegram_token"]
        # Convert the ID to an integer since Telegram checks it as a number
        ALLOWED_USER_ID = int(secrets["telegram_user_id"])
except FileNotFoundError:
    print("❌ ERROR: Data/secrets.json not found! Please create it.")
    sys.exit(1)
except KeyError as e:
    print(f"❌ ERROR: Missing key {e} in Data/secrets.json.")
    sys.exit(1)
except ValueError:
    print("❌ ERROR: telegram_user_id in secrets.json must be a number.")
    sys.exit(1)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a greeting when you type /start"""
    if update.effective_user.id != ALLOWED_USER_ID:
        return

    await update.message.reply_text(
        "Hello! I am your Cinema Scraper.\n"
        "Commands:\n"
        "/scrape - Runs tomorrow\n"
        "/scrape today - Runs for today\n"
        "/scrape 1 - Runs for today\n"
        "/scrape tomorrow - Runs for tomorrow\n"
        "/scrape 2 - Runs for the day after tomorrow"
    )


async def run_scraper(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Triggers main.py and streams the output back to Telegram"""
    if update.effective_user.id != ALLOWED_USER_ID:
        await update.message.reply_text("Unauthorized user.")
        return

    # 1. Parse the command argument
    offset_arg = ""
    display_name = "the default day: tomorrow"

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

    # 2. Create the live status message
    status_msg = await update.message.reply_text(f"🎬 Starting the scraper for {display_name}...")

    # Build the command
    cmd = [sys.executable, "-u", "main.py"]
    if offset_arg:
        cmd.append(offset_arg)

    try:
        # 3. Start the subprocess asynchronously
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT  # Combine errors into standard output
        )

        output_buffer = []
        last_update_time = time.time()

        # 4. Read the output line-by-line as it prints
        while True:
            line = await process.stdout.readline()
            if not line:
                break

            decoded_line = line.decode('utf-8', errors='ignore').strip()
            if decoded_line:
                output_buffer.append(decoded_line)
                # Keep only the last 15 lines so the Telegram message doesn't become massive
                output_buffer = output_buffer[-15:]

                # Update the Telegram message every 2 seconds to avoid rate limits
                if time.time() - last_update_time > 2.0:
                    try:
                        # Format as a code block for easy reading
                        display_text = f"⏳ **Running Scraper ({display_name})...**\n```text\n" + "\n".join(
                            output_buffer) + "\n```"
                        await status_msg.edit_text(display_text, parse_mode="Markdown")
                        last_update_time = time.time()
                    except Exception:
                        pass  # Ignore minor Telegram errors like "Message is not modified"

        # Wait for the process to fully close
        await process.wait()

        # Final update to the status box
        final_text = f"✅ **Scraping Finished!**\n```text\n" + "\n".join(output_buffer[-5:]) + "\n```"
        try:
            await status_msg.edit_text(final_text, parse_mode="Markdown")
        except Exception:
            pass

        # 5. Check results and send files
        if process.returncode == 0:
            excel_path = "Data/output.xlsx"
            txt_path = "Data/output.txt"

            if os.path.exists(excel_path) and os.path.exists(txt_path):
                await update.message.reply_document(document=open(txt_path, 'rb'))
                await update.message.reply_document(document=open(excel_path, 'rb'))
            else:
                await update.message.reply_text("⚠️ Script finished, but output files were missing.")
        else:
            await update.message.reply_text("❌ The script crashed or returned an error code.")

    except Exception as e:
        await update.message.reply_text(f"❌ Failed to run subprocess: {e}")

async def notify_startup(application: Application):
    """Sends a message to the admin when the bot boots up."""
    try:
        await application.bot.send_message(
            chat_id=ALLOWED_USER_ID,
            text="🤖 *FinlandMovieBot* is online and ready on morko! \nUse /scrape to get started.",
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"Failed to send startup message: {e}")


if __name__ == '__main__':
    print("Starting Telegram Bot...")
    app = Application.builder().token(TOKEN).post_init(notify_startup).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("scrape", run_scraper))

    print("Bot is listening! Send /start to it on Telegram.")
    app.run_polling()