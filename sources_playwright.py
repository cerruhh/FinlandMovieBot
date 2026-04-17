import datetime as dt
import re
import time
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import random

# Try to import settings, otherwise default to True for all (for testing)
try:
    from settings_get import read_settings

    all_settings = read_settings()
except ImportError:
    print("[WARN] settings_get.py not found. Defaulting all sources to TRUE.")
    all_settings = {
        "sources": {
            "biorex": True,
            "kinot.fi": True,
            "konepaja": True,
            "gilda": True,
            "finnkino": False
        }
    }


# --- Helper Functions (Preserved from original) ---

def human_sleep(min_seconds=3.0, max_seconds=6.0):
    """Sleeps for a random amount of time to mimic human irregularity."""
    time.sleep(random.uniform(min_seconds, max_seconds))

def human_mouse_move(page):
    """Moves the mouse randomly to trick bot detection."""
    try:
        x = random.randint(100, 500)
        y = random.randint(100, 500)
        page.mouse.move(x, y, steps=10)
        time.sleep(random.uniform(0.2, 0.7))
    except Exception:
        pass

def calcDate(offset: int):
    targetDate = dt.datetime.today() + dt.timedelta(days=offset)
    return targetDate.strftime("%Y-%m-%d")


def convertOneDigit2Two(digit: str):
    if len(digit) == 1:
        return f"0{digit}"
    else:
        return digit[:2]


def properCapitals(text):
    return ' '.join(word.capitalize() for word in text.split())


def normalizeTitle(title: str):
    # some censoring, banned words, boycot
    removeWords = (
        "BARNSÖNDAGAR: ", "Pieni elokuvakerho: ", "KESÄKINO: ", "Espoo Ciné: ", "Seniorikino: ", "Perhekino: ",
        "Kesäkino: ", "Barnfestival: ")
    for censoredWord in removeWords:
        title = title.replace(censoredWord, "")
        title = properCapitals(title)
    return title


def translate_value(value):
    translations = {
        "Tennispalatsi, Helsinki": "TP",
        "BioRex Tripla": "TRIPLA",
        "Lasipalatsi": "LP",
        "Kinopalatsi, Helsinki": "KP",
        "Itis, Helsinki": "ITIS",
        "Konepaja": "KONEPJ",
        "BioRex Redi": "REDI",
        "Maxim, Helsinki": "MAX",
        "Gilda": "GILDA",
        "Kino Engel": "ENGEL",
        "Kino Konepaja": "KONEPJ",
        "Cinema Orion": "ORION"
    }
    return translations.get(value, value)


# --- Scraper Functions ---

def load_biorex(page, day_offset: int):
    URL = "https://biorex.fi/en/movies/?type=showtimes"
    target_date = calcDate(day_offset)
    print(f"[INFO] BioRex: Loading URL {URL} for date {target_date}...")

    try:
        page.goto(URL, timeout=60000)

        # 1. Handle Cookiebot (Using the ID you identified)
        try:
            #print("[DEBUG] BioRex: Waiting for cookie banner...")
            # Wait specifically for the Allow All button
            page.wait_for_selector("#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll", state="visible",
                                   timeout=5000)
            page.click("#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll")
            #print("[DEBUG] BioRex: Cookies accepted.")
        except PlaywrightTimeoutError:
            print("[DEBUG] BioRex: Cookie banner not found or already accepted.")

        # 2. Select "Tripla"
        #print("[DEBUG] BioRex: Selecting 'Helsinki (Tripla)'...")
        page.select_option("#choose_location", label="Helsinki (Tripla)")

        # 3. Select "All" Helsinki movies (button data-slug='all')
        # Wait for the filter buttons to be interactive
        page.wait_for_selector("button[data-slug='all']", state="visible")
        page.click("button[data-slug='all']")
        time.sleep(1)  # Small pause for JS filter to apply

        # 4. Click "Show times" tab
        #print("[DEBUG] BioRex: Clicking 'Show times' tab...")
        page.click("a[data-type='showtimes']")

        # 5. Handle Date Selection (Dropdown Logic)
        # BioRex uses a custom JS dropdown (choices__list)
        #print(f"[DEBUG] BioRex: Selecting date with offset {day_offset}...")

        # Click the dropdown to open it
        page.click(".choices__list")
        time.sleep(0.5)

        # Simulate arrow keys exactly like the Selenium script
        for _ in range(day_offset + 1):
            page.keyboard.press("ArrowDown")
            time.sleep(0.1)

        page.keyboard.press("Enter")

        # Wait for results to load
        #print("[DEBUG] BioRex: Waiting for showtime results...")
        time.sleep(3)  # Essential wait for AJAX reload
        page.wait_for_selector("div.showtime-item__entry", timeout=10000)

        # 6. Parse Data using BeautifulSoup (Ported logic)
        html = page.content()
        soup = BeautifulSoup(html, 'html.parser')

        movies = []
        entries = soup.select('div.showtime-item__entry')

        for movie_card in entries:
            try:
                title_el = movie_card.select_one('span.showtime-item__movie-name__value')
                if not title_el: continue

                title = title_el.text.split(" (")[0].strip()
                title = normalizeTitle(title)

                time_val = movie_card.find('div', {'class': 'showtime-item__start'}).text.strip()

                location_text = movie_card.select_one("div.showtime-item__place__value").text.strip()
                location_parts = location_text.split(",")

                theater_raw = location_parts[0].strip()
                theater = translate_value(theater_raw)

                auditorium = location_parts[1].strip() if len(location_parts) > 1 else "NA"

                movies.append({
                    'ShowTitle': title,
                    'Auditorium': auditorium,
                    "ShowDate": target_date,
                    "ShowStart": time_val,
                    "Theatre": theater,
                    "ProductionYear": 'NA',
                    'ShowEnd': 'NA',
                    'PresentationMethod': 'NA'
                })
            except Exception as e:
                print(f"[ERROR] BioRex: Error parsing card: {e}")

        print(f"[SUCCESS] BioRex: Retrieved {len(movies)} showtimes.")
        return movies

    except Exception as e:
        print(f"[ERROR] BioRex failed: {e}")
        return []


def load_kinotfi(page, day_offset: int):
    URL = "https://www.kinot.fi/"
    target_date = calcDate(day_offset)
    print(f"[INFO] Kinot.fi: Loading URL {URL}...")

    try:
        page.goto(URL, timeout=60000)

        # Calculate value for select box
        value_to_select = "today" if day_offset == 0 else target_date

        #print(f"[DEBUG] Kinot.fi: Selecting date value '{value_to_select}'...")
        page.wait_for_selector("#date-select")
        page.select_option("#date-select", value=value_to_select)

        # Wait for reload/loading
        time.sleep(2)

        # Scroll to bottom to trigger lazy load
        #print("[DEBUG] Kinot.fi: Scrolling to load content...")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        # Parse
        html = page.content()
        soup = BeautifulSoup(html, "html.parser")
        text_wrappers = soup.find_all(class_="text-wrapper")

        shows = []
        for wrapper in text_wrappers:
            try:
                title_div = wrapper.find("div", class_="movie-title-container")
                if not title_div: continue

                title = normalizeTitle(title_div.get_text(strip=True))
                time_val = wrapper.find("div", class_="time").get_text(strip=True)

                theater_span = wrapper.find("span", class_="theater-name")
                theater = translate_value(theater_span.get_text(strip=True)) if theater_span else "NA"

                shows.append({
                    'ShowTitle': title,
                    'Auditorium': "NA",
                    "ShowDate": target_date,
                    "ShowStart": time_val,
                    "Theatre": theater,
                    "ProductionYear": 'NA',
                    'ShowEnd': 'NA',
                    'PresentationMethod': 'NA'
                })
            except AttributeError:
                continue

        print(f"[SUCCESS] Kinot.fi: Retrieved {len(shows)} showtimes.")
        return shows

    except Exception as e:
        print(f"[ERROR] Kinot.fi failed: {e}")
        return []


def load_konepajakino(page, day_offset: int):
    URL = "https://kinokonepaja.fi/"
    target_date = calcDate(day_offset)  # format YYYY-MM-DD
    print(f"[INFO] Konepaja: Loading URL {URL}...")

    try:
        page.goto(URL, timeout=60000)
        page.wait_for_selector('div.kinola-event', timeout=10000)

        html = page.content()
        soup = BeautifulSoup(html, "html.parser")

        shows = []
        movies = soup.find_all('div', class_='kinola-event')

        for movie in movies:
            try:
                title_el = movie.find('h6', class_='kinola-event-title-text')
                if not title_el: continue
                title = normalizeTitle(title_el.text.strip())

                # Date parsing: "Ke 21.5." -> needs year
                date_el = movie.find('span', class_='kinola-event-date')
                if not date_el: continue

                date_str = date_el.text.strip()  # e.g. "Ke 21.5."
                # Extract 21 and 5
                parts = date_str.split(" ")[1].split(".")
                current_year = dt.datetime.now().year

                movie_date_iso = f"{current_year}-{convertOneDigit2Two(parts[1])}-{convertOneDigit2Two(parts[0])}"

                # Check if this movie matches requested date
                if movie_date_iso == target_date:
                    time_val = movie.find('span', class_='kinola-event-time').text.strip()

                    shows.append({
                        'ShowTitle': title,
                        'Auditorium': "Kp1",
                        "ShowDate": movie_date_iso,
                        "ShowStart": time_val,
                        "Theatre": "KONEPJ",
                        "ProductionYear": 'NA',
                        'ShowEnd': 'NA',
                        'PresentationMethod': 'NA'
                    })
            except Exception:
                continue

        print(f"[SUCCESS] Konepaja: Retrieved {len(shows)} showtimes.")
        return shows

    except Exception as e:
        print(f"[ERROR] Konepaja failed: {e}")
        return []


def load_gilda(page, day_offset: int):
    URL = "https://www.gilda.fi/elokuvat/"
    target_date = calcDate(day_offset)
    print(f"[INFO] Gilda: Loading URL {URL}...")

    try:
        page.goto(URL, timeout=60000)
        page.wait_for_selector('div.movie', timeout=10000)

        html = page.content()
        soup = BeautifulSoup(html, "html.parser")

        shows = []
        movies = soup.find_all('div', class_='movie movielist__item show')

        for movie in movies:
            try:
                title_el = movie.find('h3', class_='title')
                if not title_el: continue
                title = normalizeTitle(title_el.text.strip())

                showtimes = movie.find_all('div', class_='movie-meta')

                for showtime in showtimes:
                    date_el = showtime.find('div', class_='movie-meta__stuff date nobr')
                    if not date_el: continue

                    # Parse "21.5." -> "2025-05-21"
                    date_str = date_el.text.strip()
                    parts = date_str.split(" ")[0].split(".")
                    current_year = dt.datetime.now().year
                    movie_date_iso = f"{current_year}-{convertOneDigit2Two(parts[1])}-{convertOneDigit2Two(parts[0])}"

                    if movie_date_iso == target_date:
                        time_str = showtime.find('div', class_='movie-meta__stuff time').text.strip()
                        time_val = time_str.replace('.', ':')

                        theater_el = showtime.find('div', class_='movie-meta__stuff theater movie_meta__screen_name')
                        theater = theater_el.text.strip() if theater_el else "Gilda"

                        shows.append({
                            'ShowTitle': title,
                            'Auditorium': theater,
                            "ShowDate": movie_date_iso,
                            "ShowStart": time_val,
                            "Theatre": "GILDA",
                            "ProductionYear": 'NA',
                            'ShowEnd': 'NA',
                            'PresentationMethod': 'NA'
                        })
            except Exception:
                continue

        print(f"[SUCCESS] Gilda: Retrieved {len(shows)} showtimes.")
        return shows

    except Exception as e:
        print(f"[ERROR] Gilda failed: {e}")
        return []


def load_finnkino(page, day_offset: int):
    # --- Configuration ---
    # Finnkino Internal IDs for the Schedule Page
    THEATERS = [
        {"name": "Kinopalatsi", "id": "1031", "code": "KP"},
        {"name": "Maxim", "id": "1032", "code": "MAX"},
        {"name": "Tennispalatsi", "id": "1033", "code": "TP"}
    ]

    # Calculate target date
    target_date_obj = dt.datetime.today() + dt.timedelta(days=day_offset)
    target_date_ui = target_date_obj.strftime("%d.%m.%Y")
    target_date_iso = target_date_obj.strftime("%Y-%m-%d")

    print(f"[INFO] Finnkino: Starting Desktop Schedule Journey for {target_date_ui}...")

    all_shows = []

    try:
        # ---------------------------------------------------------
        # STEP 1: Go Home
        # ---------------------------------------------------------
        #print("[DEBUG] Navigating to Home...")
        page.goto("https://www.finnkino.fi/en/", timeout=90000)
        human_sleep(3, 5)

        # ---------------------------------------------------------
        # STEP 2: Cookies (Wait Patiently)
        # ---------------------------------------------------------
        try:
            # Wait for banner to appear
            if page.locator("#onetrust-accept-btn-handler").count() == 0:
                #print("[DEBUG] Waiting for cookie banner...")
                page.wait_for_selector("#onetrust-accept-btn-handler", state="visible", timeout=5000)

            human_sleep(1, 2)
            page.click("#onetrust-accept-btn-handler")
            #print("[DEBUG] Cookies accepted.")
            human_sleep(2, 3)
        except Exception:
            print("[DEBUG] No cookie banner found.")

        # ---------------------------------------------------------
        # STEP 3: Navigate to Schedule (Ohjelmisto)
        # ---------------------------------------------------------
        # Instead of guessing the URL, we click the navigation link.
        print("[DEBUG] Looking for 'Schedule' link...")

        # Find link containing 'Schedule' or 'Ohjelmisto'
        try:
            # Desktop header link usually
            schedule_btn = page.locator("ul.navbar-nav a").filter(
                has_text=re.compile("Schedule|Ohjelmisto", re.IGNORECASE)).first
            schedule_btn.click()
            print("[DEBUG] Clicked Schedule button.")
        except Exception:
            print("[WARN] Navbar link not found. Trying direct URL fallback.")
            page.goto("https://www.finnkino.fi/en/ohjelmisto", timeout=60000)

        human_sleep(4, 6)  # Wait for big page load

        # ---------------------------------------------------------
        # STEP 4: Process Each Theater
        # ---------------------------------------------------------
        for theater in THEATERS:
            print(f"--------------------------------------------------")
            print(f"[DEBUG] Switching to {theater['name']} (ID: {theater['id']})...")

            try:
                # 1. Select Theater Area
                # The dropdown name is 'area' on the schedule page
                page.wait_for_selector("select[name='area']", timeout=15000)

                # Jiggle mouse before clicking (Stealth)
                page.mouse.move(random.randint(100, 500), random.randint(100, 500))
                human_sleep(0.5, 1)

                page.select_option("select[name='area']", value=theater['id'])

                print("[DEBUG] Waiting for area refresh...")
                human_sleep(3, 5)  # Important wait for AJAX

                # 2. Select Date (If available)
                if page.locator("select[name='dt']").count() > 0:
                    print(f"[DEBUG] Selecting date: {target_date_ui}")
                    try:
                        page.select_option("select[name='dt']", label=target_date_ui)
                        print("[DEBUG] Waiting for date refresh...")
                        human_sleep(3, 5)
                    except Exception:
                        print(f"[WARN] Date {target_date_ui} not available (using default).")

                # 3. Scrape Data
                print(f"[DEBUG] Scraping {theater['name']}...")

                # Wait for cards
                try:
                    page.wait_for_selector("div.schedule-card", timeout=8000)
                except PlaywrightTimeoutError:
                    print(f"[WARN] No shows found for {theater['name']}.")
                    continue

                # Scroll Down (Human-like)
                # Scroll in 3 chunks
                for _ in range(3):
                    page.evaluate("window.scrollBy(0, 500)")
                    human_sleep(0.5, 1)

                # Parse
                html = page.content()
                soup = BeautifulSoup(html, 'html.parser')
                cards = soup.select("div.schedule-card")

                count_local = 0
                for card in cards:
                    try:
                        title_el = card.select_one("a.schedule-card__title")
                        if not title_el: continue
                        title = normalizeTitle(title_el.text.strip())

                        time_el = card.select_one("div.schedule-card__time span.time")
                        start_time = time_el.text.strip() if time_el else "NA"

                        # Auditorium
                        place_el = card.select_one("div.schedule-card__place")
                        auditorium = "NA"
                        if place_el:
                            place_text = place_el.text.strip()
                            if "," in place_text:
                                auditorium = place_text.split(",")[-1].strip()
                            else:
                                auditorium = place_text

                        all_shows.append({
                            'ShowTitle': title,
                            'Auditorium': auditorium,
                            "ShowDate": target_date_iso,
                            "ShowStart": start_time,
                            "Theatre": theater['code'],
                            "ProductionYear": 'NA',
                            'ShowEnd': 'NA',
                            'PresentationMethod': 'NA'
                        })
                        count_local += 1
                    except Exception:
                        continue

                print(f"[SUCCESS] {theater['name']}: Found {count_local} shows.")

            except Exception as e:
                print(f"[ERROR] Failed processing {theater['name']}: {e}")

    except Exception as e:
        print(f"[ERROR] Finnkino journey failed: {e}")

    print(f"--------------------------------------------------")
    print(f"[SUMMARY] Finnkino: Total {len(all_shows)} shows collected.")
    return all_shows


def load_all(day_offset: int = 1):
    dataarray = []

    with sync_playwright() as p:
        # print("[DEBUG] Launching High-Stealth Desktop Browser...")

        # 1. Launch Arguments to hide automation
        browser = p.chromium.launch(
            headless=True,  # <--- 1. CHANGED TO TRUE
            slow_mo=200,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--start-maximized",
                "--no-sandbox",  # <--- 2. CRITICAL FOR LINUX (especially if running as root/Docker)
                "--disable-dev-shm-usage"
                # <--- 3. ADD THIS (Prevents Chrome from crashing due to limited shared memory on servers)
            ]
        )

        # 2. Desktop User Agent
        desktop_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"

        # 3. Create Context with No Viewport (Allows window to set size)
        context = browser.new_context(
            viewport=None,
            user_agent=desktop_ua,
            locale="en-US",
            timezone_id="Europe/Helsinki"
        )

        # 4. INJECT STEALTH SCRIPTS (The Magic Fix)
        # This deletes the 'navigator.webdriver' property that sites check
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        page = context.new_page()

        # ... Your source loading logic ...
        sources = all_settings.get("sources", {})

        if sources.get("finnkino", False):
            dataarray += load_finnkino(page, day_offset)
        else:
            print("[INFO] Finnkino search disabled.")

        if sources.get("biorex", False):
            dataarray += load_biorex(page, day_offset)
        else:
            print("[INFO] BioRex search disabled.")

        if sources.get("kinot.fi", False):
            dataarray += load_kinotfi(page, day_offset)
        else:
            print("[INFO] Kinot.fi search disabled.")

        if sources.get("konepaja", False):
            dataarray += load_konepajakino(page, day_offset)
        else:
            print("[INFO] Konepaja search disabled.")

        if sources.get("gilda", False):
            dataarray += load_gilda(page, day_offset)
        else:
            print("[INFO] Gilda search disabled.")






        browser.close()

    print(f"\n[SUMMARY] Total movies retrieved: {len(dataarray)}")
    return dataarray


# --- Execution Block (for testing) ---
if __name__ == "__main__":
    print("Starting Playwright scraper...")
    # Test with offset 0 (today) or 1 (tomorrow)
    results = load_all(day_offset=0)
    # print(json.dumps(results, indent=2, ensure_ascii=False))