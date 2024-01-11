import datetime as dt

from selenium.webdriver.support import expected_conditions as EC

import xmltodict
import re
import requests

from selenium.webdriver import Chrome
from selenium.webdriver import ChromeOptions
from bs4 import BeautifulSoup
from time import sleep as wait

#from selenium.webdriver import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select

#calcDate converts offset day to date in format 2025-05-18, where 0 is today, 1 is tomorrow
def calcDate(offset:int):
    targetDate = dt.datetime.today()  + dt.timedelta(days=offset)
    return targetDate.strftime("%Y-%m-%d")

def normalizeTitle(title: str):
    removeWords= (["BARNSÖNDAGAR: ", "testingtesting"])
    for censoredWord in removeWords:
        title = title.replace(censoredWord,"")
        return title


def convertOneDigit2Two(digit:str):
    if len(digit)==1:
        return f"0{digit}"
    else:
        return digit[:2]
def load_finnkino(day_offset:int,give_all:bool=False):
    hdr = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
    currentDate = dt.datetime.now()
    tomorrowDate = currentDate + dt.timedelta(day_offset)
    searchString = tomorrowDate.strftime("%d.%m.%Y")
    searchParameters = {
        "area": 1002,
        "dt": searchString
    }
    requestUrl = f"https://www.finnkino.fi/xml/Schedule/?"

    requestXML = requests.get(url=requestUrl, params=searchParameters, headers=hdr)
    print(f"Opening API with URL: {requestUrl}/{searchParameters}")
    requestXML.encoding = "UTF-8"
    requestXML.raise_for_status()

    data_dict = xmltodict.parse(requestXML.text)

    if data_dict["Schedule"]["Shows"] == None:
        print("No shows tomorrow!")
        exit(code=123456)
    if give_all:
        return data_dict
    elif not give_all:
        return data_dict["Schedule"]["Shows"]["Show"]


def load_biorex(day_offset:int):
    URL = "https://biorex.fi/"
    ch_opt=ChromeOptions()
    ch_opt.add_argument("--headless")

    driver = Chrome(ch_opt)
    print(f"Opening headless Chrome browser with URL: {URL}")
    driver.get(URL)

    # Set up headless Chrome browser
    # chromeOptions = ChromeOptions()
    # chromeOptions.add_experimental_option(value=True, name="detach")
    # chromeOptions.add_argument("--headless")

    # Click the "Hyväksi kaikki evästeet" button
    webWait = WebDriverWait(driver, 5)
    accept_button = webWait.until(EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler")))
    accept_button.click()

    # Select "Tripla" from the "Valitse teatteri" dropdown
    teatteri_dropdown = Select(driver.find_element(by=By.ID, value="choose_location"))
    teatteri_dropdown.select_by_visible_text("Helsinki (Tripla)")

    # Wait for the page to load
    wait(5)

    # Get the page source and parse it with BeautifulSoup
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'html.parser')

    # Find all the movie cards and extract the relevant information
    movies = []
    for movie_card in soup.select('div.movie-card'):
        if re.search(r'class="movie-card__title"', str(movie_card)) and re.search(
                r'class="movie-carousel__showtime-time"', str(movie_card)):
            title = movie_card.select_one('h3.movie-card__title').text.split(" (")[0].strip()
            time_and_date = movie_card.select_one('span.movie-carousel__showtime-time').text.strip()

            time = time_and_date.split(" ")[2].strip()
            date_day = convertOneDigit2Two(time_and_date.split(" ")[1].split(".")[0].strip())
            date_month = convertOneDigit2Two(time_and_date.split(" ")[1].split(".")[1].strip())
            date = f"{dt.datetime.now().year}-{date_month}-{date_day}"
            auditorium = movie_card.select_one('span.movie-carousel__showtime-screen').text.strip()
            if calcDate(day_offset) == date:
                movies.append({'OriginalTitle': title, 'TheatreAuditorium': auditorium,"dttmShowStart":f"{date}T{time}:00", "Theatre":"Biorex, Tripla","ProductionYear":"","dttmShowEnd":"","PresentationMethod":""})
                print(f"{title} - {date} - {time} - Biorex Tripla -  {auditorium}")
    # Close the driver
    driver.quit()
    return movies



def load_kinotfi(day_offset):

    URL = "https://www.kinot.fi/"
    LOAD_TIME = 4

    # Set up headless Chrome browser
    chOptions = ChromeOptions()
    chOptions.add_experimental_option(value=True, name="detach")
    chOptions.add_argument("--headless")

    # Set up logging
    #logging.basicConfig(level=logging.INFO)

    with Chrome(options=chOptions) as browser:
        browser.get(URL)
        print(f"Opening headless Chrome browser with URL: {URL}")
        wait(LOAD_TIME)
        html = browser.page_source

    soup = BeautifulSoup(html, "html.parser")

    # Find all the date elements and loop through them
    dates = soup.find_all("div", class_="date-label")
    # print(dates)
    i = 0
    movies = []  # Create an empty dictionary to store the movie information
    for date in dates:
        i += 1
        #logging.info(f"## {i} date: {date}")
        date_str = date.text.strip()
        for movie in date.find_next_siblings():
            # check if the html contains class="show-item"
            if re.search(r'class="show-item"', str(movie)):
                title = normalizeTitle(str((movie.select_one(".movie-title-container h3")).text).split(" (")[0].strip())
                times = [time.text.strip() for time in movie.select(".time")]
                theater = movie.select_one(".theater").text.strip()
                # logging.info(f"#### {i} title: {title} times {times} theater {theater}")
                for time in times:
                    day_of_month = date_str.split(sep=" ")[1].split(".")
                    datestring = f"{dt.datetime.now().year}-{convertOneDigit2Two(day_of_month[1])}-{convertOneDigit2Two(day_of_month[0])}"
                    if calcDate(day_offset) == datestring:
                        movies.append({'OriginalTitle': title, 'TheatreAuditorium':"" ,"dttmShowStart":f"{datestring}T{time}:00", "Theatre":theater,"ProductionYear":"", "dttmShowEnd":"","PresentationMethod":"NA"})
                        print(f"{title} - {datestring} - {time} - {theater}")
    return movies


def load_all(day_offset:int=1):
    dataarray =  []
    dataarray =  load_biorex(day_offset=day_offset)
    dataarray += load_kinotfi(day_offset=day_offset)
    dataarray += load_finnkino(day_offset=day_offset)
    return dataarray



