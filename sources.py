from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select

from selenium.webdriver import Chrome
from selenium.webdriver import ChromeOptions
from os.path import abspath


import xmltodict
import json
import xmltodict
import re
import requests
import datetime as dt
from time import sleep as wait
from bs4 import BeautifulSoup
from settings_get import read_settings

all_settings=read_settings()

def calcDate(offset:int):
    """
    calcDate converts offset day to date in format 2025-05-18, where arg offset 0 is today, 1 is tomorrow
    """

    targetDate = dt.datetime.today()  + dt.timedelta(days=offset)
    return targetDate.strftime("%Y-%m-%d")

def calcDateFinnish(offset:int):
    """
    calcDateFinnish converts offset day to date in format 18.05.2024, where arg offset 0 is today, 1 is tomorrow
    """

    targetDate = dt.datetime.today()  + dt.timedelta(days=offset)
    return targetDate.strftime("%d.%m.%Y")

def calcDateShort(offset:int):
    """
    calcDateShort converts offset day to date in format 8-5-2024, where arg offset=0 is today, 1 is tomorrow
    """

    targetDate = dt.datetime.today() + dt.timedelta(days=offset)
    return targetDate.strftime("%d-").lstrip("0") +  targetDate.strftime("%m-%Y").lstrip("0")

def properCapitals(text):
    return ' '.join(word.capitalize() for word in text.split())

def normalizeTitle(title: str):
    """
    function that will remove or censor words from any text
    """

    removeWords=("BARNSÖNDAGAR: ","Pieni elokuvakerho: ", "KESÄKINO: ", "Espoo Ciné: ", "Seniorikino: ", "Perhekino: ")
    for censoredWord in removeWords:
        title = title.replace(censoredWord,"")
        title = properCapitals(title)
    return title


def convertOneDigit2Two(digit:str):
    if len(digit)==1:
        return f"0{digit}"
    else:
        return digit[:2]


def translate_value(value):
    # Define the dictionary with translations
    translations = {
    "Tennispalatsi, Helsinki": "TP",
    "BioRex Tripla": "TRIPLA",
    "Lasipalatsi": "LP",
    "Kinopalatsi, Helsinki": "KP",
    "Itis, Helsinki": "ITIS",
    "Konepaja": "KONEPJ",
    "BioRex Redi": "REDI",
    "Maxim, Helsinki": "MAX",
    "Gilda": "LASIP",
    "Kino Engel": "ENGEL",
    "Kino Konepaja": "KONEPJ",
    "Cinema Orion": "ORION"

    }
    # Check if the value is in the dictionary
    if value in translations:
        return translations[value]
    else:
        return value


def load_finnkino(day_offset:int,give_all:bool=False):
    # hdr = {
     #   'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
    hdr = {
        'User-Agent': 'Mozilla/5.0 (iPad; CPU OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148'}
    currentDate = dt.datetime.now()
    tomorrowDate = currentDate + dt.timedelta(day_offset)
    searchString = tomorrowDate.strftime("%d.%m.%Y")
    # searchParameters = {
    #    "area": 1002,
    #    "dt": searchString
    # }

    requestUrl = f"https://www.finnkino.fi/xml/Schedule/?area=1002&dt={calcDateFinnish(day_offset)}"
#    requestXML = requests.get(url=requestUrl, params=searchParameters, headers=hdr)

    #print(f"Opening API with URL: {requestUrl}")

    ch_opt=ChromeOptions()
    # ch_opt.add_argument("--headless")
    ch_opt.add_experimental_option("detach", True)

    with Chrome(options=ch_opt) as browser:
        browser.get(requestUrl)
        print(f"Opening headless Chrome browser with URL: {requestUrl}")
        wait(3)
        html = browser.page_source

    requestXML = BeautifulSoup(html, "xml")
    long_result = (requestXML.text)
    #    print(long_result)
    target = "<Schedule xmlns:xsd" # text starts with some warning text about xml that should be removed, only part we want starts with <Schedule
    index = long_result.find(target)

    result = long_result[index:]
    if "&" in result:
        result = result.replace("&", "&#38;") ## xmltodict cannot handle "&"
    #print(result)
    #requestXML.encoding = "UTF-8"
    #requestXML.raise_for_status()

    data_dict = xmltodict.parse(result)
    showsDict = data_dict["Schedule"]["Shows"]["Show"]

    # Print Finnkino data for analysis:
    json_data = json.dumps(showsDict, indent=2)
    json_data.encode("UTF-8")
    with open(file=abspath("Data/finnkino.json"), mode="w") as json_file:
        json_file.write(json_data)

    if data_dict["Schedule"]["Shows"] == None:
        print("No shows tomorrow!")
        exit(code=123456)

    new_shows_list = []
    movies = []
    for show in showsDict:
        # Extract basic fields
        title = show.get('Title')

        # Split datetime into date and time components
        start_datetime = show.get('dttmShowStart', '')
        if start_datetime:
            date_part, time_part = start_datetime.split('T')[:2]  # Split at 'T'
            start_date = date_part  # "2025-04-21"
            start_time = time_part[:5]  # "10:30" (ignores seconds/timezone)
        else:
            start_date, start_time = None, None


        movies.append({'ShowTitle': show.get('OriginalTitle'), 'Auditorium': show.get('TheatreAuditorium'),
                       "ShowDate": f"{start_date}", "ShowStart": f"{start_time}",
                       "Theatre": translate_value(show.get('Theatre')), "ProductionYear": show.get('ProductionYear'),
                       'ShowEnd': 'NA', 'PresentationMethod':  show.get('PresentationMethod')})

    print(f"    The number of movies retrieved: {len(movies)}.")
    return movies


def load_biorex(day_offset:int):
    #URL = "https://biorex.fi/"
    URL = "https://biorex.fi/en/movies/?type=showtimes"
    ch_opt=ChromeOptions()
    ch_opt.add_argument("--headless")

    #ch_opt.add_experimental_option("detach", True)

    driver = Chrome(ch_opt)
    date = calcDate(day_offset)
    print(f"Opening headless Chrome browser with URL: {URL} with {date}")
    driver.get(URL)

    # Click the "Hyväksi kaikki evästeet" button
    webWait = WebDriverWait(driver, 3)
    accept_button = webWait.until(EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler")))
    accept_button.click()

    # Select "Tripla" from the "Valitse teatteri" dropdown
    teatteri_dropdown = Select(driver.find_element(by=By.ID, value="choose_location"))
    teatteri_dropdown.select_by_visible_text("Helsinki (Tripla)")

    #select all Helsinki movies
    wait(2)
    # Find the button by its data-slug attribute (select all theaters in Helsinki
    button = driver.find_element(By.CSS_SELECTOR, "button[data-slug='all']")
    button.click()
    #print("select all cinema's")

    # Locate the “Show times” button using its data-type attribute and click it:
    show_times_button = driver.find_element(By.CSS_SELECTOR, "a[data-type='showtimes']")
    show_times_button.click()
    #print("select Show times instead Movies")

#    dropdown  = Select(driver.find(by=By.ID, value="dayselect"))


    #print (targetDate)

    dropdown = driver.find_element(by=By.CLASS_NAME, value="choices__list")
    dropdown.click()
    #print("Select date: " + calcDate((day_offset)))
    wait(1)
    action = ActionChains(driver)
    counter = 0
    for i in range(day_offset+1):
        counter += 1
        action.send_keys(Keys.DOWN).perform(); #press down key arrow depending on the date
    action.send_keys(Keys.ENTER).perform() #press ENTER


    # Wait for the page to load
    wait(5)

    # Get the page source and parse it with BeautifulSoup
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'html.parser')

    # Find all the movie cards and extract the relevant information
    movies = []
    for movie_card in soup.select('div.showtime-item__entry'):
        title = movie_card.select_one('span.showtime-item__movie-name__value').text.split(" (")[0].strip()
        title = normalizeTitle(title)
        time = movie_card.find('div', {'class': 'showtime-item__start'}).text.strip()
        location = movie_card.select_one("div.showtime-item__place__value").text.strip().split(",")
        theater = translate_value(location[0].strip()) # convert Kinopalatsi, Helsinki to KP
        auditorium = location[1].strip()
        movies.append({'ShowTitle': title, 'Auditorium': auditorium,"ShowDate":f"{date}", "ShowStart":f"{time}",
                       "Theatre":f"{theater}", "ProductionYear":'NA','ShowEnd':'NA','PresentationMethod':'NA'})
        #print(f"{title} - {date} - {time} - {theater} - {auditorium}")
    # Close the driver
    #driver.quit()
    print(f"    The number of movies retrieved: {len(movies)}.")
    return movies



def load_kinotfi(day_offset):

    URL = "https://www.kinot.fi/"
    LOAD_TIME = 6

    # Set up headless Chrome browser
    chOptions = ChromeOptions()
    #chOptions.add_experimental_option(value=True, name="detach")
    chOptions.add_argument("--headless")

    # Set up logging
    #logging.basicConfig(level=logging.INFO)

    with Chrome(options=chOptions) as browser:
        browser.get(URL)
        print(f"Opening headless Chrome browser with URL: {URL}")
        wait(LOAD_TIME)


        # Find the select box element by its ID
        select_box = Select(browser.find_element(By.ID, "date-select"))
        # Get today's date
        today = dt.datetime.today()
        intended_date = calcDate(day_offset)

        # Calculate the value to be selected based on the intended date
        if day_offset ==0:
            value_to_select = "today"
        else:
            value_to_select = intended_date

        # Select the option based on the calculated value
        select_box.select_by_value(value_to_select)
        wait(LOAD_TIME)

        # Scroll to the bottom of the webpage to load dynamic content
        browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        wait(LOAD_TIME)

        # Scroll to the bottom of the webpage to load dynamic content
        browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        wait(LOAD_TIME)

        html = browser.page_source
    soup = BeautifulSoup(html, "html.parser")

    # Find all elements with the class 'text-wrapper'
    text_wrappers = soup.find_all(class_="text-wrapper")

    # Initialize a list to store the extracted information
    shows = []

    # Iterate over each text wrapper element
    for wrapper in text_wrappers:
        # Extract the title, time, and theater from the element
        title = wrapper.find("div", class_="movie-title-container").get_text(strip=True)
        title = normalizeTitle(title)
        time = wrapper.find("div", class_="time").get_text(strip=True)
        theater = wrapper.find("span", class_="theater-name").get_text(strip=True)
        theater = translate_value(theater)

        # Append the extracted information to the list
        shows.append(
            {'ShowTitle': title, 'Auditorium': "NA", "ShowDate": f"{intended_date}", "ShowStart": f"{time}",
             "Theatre": theater, "ProductionYear": 'NA', 'ShowEnd': 'NA',
             'PresentationMethod': 'NA'})

    browser.quit()
    print(f"    The number of movies retrieved: {len(shows)}.")
    return shows



def load_konepajakino(day_offset):

    URL = "https://kinokonepaja.fi/"
    LOAD_TIME = 4

    # Set up headless Chrome browser
    chOptions = ChromeOptions()
    #chOptions.add_experimental_option(value=True, name="detach")
    chOptions.add_argument("--headless")

    showDate = calcDate(day_offset)
    # Set up logging
    # logging.basicConfig(level=logging.INFO)

    with Chrome(options=chOptions) as browser:
        browser.get(URL)
        print(f"Opening headless Chrome browser with URL: {URL}")
        wait(LOAD_TIME)
        html = browser.page_source

    soup = BeautifulSoup(html, "html.parser")

    shows = []
    # Find all movie elements
    movies = soup.find_all('div', class_='kinola-event')

    # Loop through each movie element and extract information
    for movie in movies:
        title = normalizeTitle(movie.find('h6', class_='kinola-event-title-text').text.strip())
        date_str = movie.find('span', class_='kinola-event-date').text.strip()
        day_of_month = date_str.split(sep=" ")[1].split(".")
        date = f"{dt.datetime.now().year}-{convertOneDigit2Two(day_of_month[1])}-{convertOneDigit2Two(day_of_month[0])}"

        time = movie.find('span', class_='kinola-event-time').text.strip()
        #theater = showtime.find('div', class_='movie-meta__stuff theater movie_meta__screen_name').text.strip()
        if date == showDate:
            shows.append(
                {'ShowTitle': title, 'Auditorium': "Kp1", "ShowDate":f"{date}", "ShowStart":f"{time}",
                 "Theatre": "KoneP", "ProductionYear": 'NA', 'ShowEnd': 'NA',
                 'PresentationMethod': 'NA'})

    browser.quit()
    print(f"    The number of movies retrieved: {len(shows)}.")
    return shows


def load_gilda(day_offset):

    URL = "https://www.gilda.fi/elokuvat/"
    LOAD_TIME = 4

    # Set up headless Chrome browser
    chOptions = ChromeOptions()
    #chOptions.add_experimental_option(value=True, name="detach")
    chOptions.add_argument("--headless")

    showDate = calcDate(day_offset)
    print(f"Opening headless Chrome browser with URL: {URL} with {showDate}")
    # Set up logging
    #logging.basicConfig(level=logging.INFO)

    with Chrome(options=chOptions) as browser:
        browser.get(URL)
        wait(LOAD_TIME)
        html = browser.page_source

    soup = BeautifulSoup(html, "html.parser")


    shows = []
    # Find all movie elements
    movies = soup.find_all('div', class_='movie movielist__item show')

    # Loop through each movie element and extract information
    for movie in movies:
        title = normalizeTitle(movie.find('h3', class_='title').text.strip())
        showtimes = movie.find_all('div', class_='movie-meta')

        for showtime in showtimes:
            date_str = showtime.find('div', class_='movie-meta__stuff date nobr').text.strip()
            day_of_month = date_str.split(sep=" ")[0].split(".")
            date = f"{dt.datetime.now().year}-{convertOneDigit2Two(day_of_month[1])}-{convertOneDigit2Two(day_of_month[0])}"

            time_str = showtime.find('div', class_='movie-meta__stuff time').text.strip()
            time = time_str.replace('.', ':')
            theater = showtime.find('div', class_='movie-meta__stuff theater movie_meta__screen_name').text.strip()
            if date == showDate:
                shows.append({'ShowTitle': title, 'Auditorium': f"{theater}", "ShowDate":f"{date}", "ShowStart":f"{time}",
                       "Theatre": "LP", "ProductionYear": 'NA', 'ShowEnd': 'NA',
                       'PresentationMethod': 'NA'})

    browser.quit()
    print(f"    The number of movies retrieved: {len(shows)}.")
    return shows

def load_all(day_offset:int=1):
    dataarray =  []
    all_sources=all_settings["sources"]
    if all_sources["biorex"] :
        dataarray =  load_biorex(day_offset=day_offset)
    else:
        print("biorex search is disabled in settings.json")
    if all_sources["kinot.fi"] :
        dataarray += load_kinotfi(day_offset=day_offset)
    else:
        print("kinot.fi search is disabled in settings.json")
    if all_sources["finnkino"]:
        dataarray += load_finnkino(day_offset=day_offset)
    else:
        print("finnkino search is disabled in settings.json")
    if all_sources["konepaja"] :
        dataarray +=  load_konepajakino(day_offset=day_offset)
    else:
        print("konepaja search is disabled in settings.json")
    if all_sources["gilda"] :
        dataarray +=  load_gilda(day_offset=day_offset)
    else:
        print("gilda search is disabled in settings.json")
    return dataarray



