import datetime as dt
import xmltodict
import re
import requests
import logging
from selenium.webdriver import Chrome
from selenium.webdriver import ChromeOptions
from bs4 import BeautifulSoup
from time import sleep as wait


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


def load_kinotfi(day_offset):


    URL = "https://www.kinot.fi/"
    LOAD_TIME = 4

    # Set up headless Chrome browser
    chOptions = ChromeOptions()
    chOptions.add_experimental_option(value=True, name="detach")
    chOptions.add_argument("--headless")

    # Set up logging
    logging.basicConfig(level=logging.INFO)

    with Chrome(options=chOptions) as browser:
        browser.get(URL)
        logging.info(f"Opening headless Chrome browser with URL: {URL}")
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
        logging.info(f"## {i} date: {date}")
        date_str = date.text.strip()
        for movie in date.find_next_siblings():
            # check if the html contains class="show-item"
            if re.search(r'class="show-item"', str(movie)):
                title = movie.select_one(".movie-title-container h3").text.strip()
                times = [time.text.strip() for time in movie.select(".time")]
                theater = movie.select_one(".theater").text.strip()
                # logging.info(f"#### {i} title: {title} times {times} theater {theater}")
                for time in times:
                    day_of_month = date_str.split(sep=" ")[1].split(".")
                    datestring = f"{dt.datetime.now().year}-{day_of_month[1]}-{day_of_month[0]}"
                    # print(L_time)
                    movies.append({"date": datestring, "title": title, "time": time, "theater": theater})

    print(movies)

