import re
import requests
import html5lib
import logging
from selenium.webdriver import Chrome
from selenium.webdriver import ChromeOptions
from bs4 import BeautifulSoup
from time import sleep as wait

URL = "https://www.kinot.fi/"

# Set up headless Chrome browser
chOptions=ChromeOptions()
chOptions.add_experimental_option(value=True,name="detach")
chOptions.add_argument("--headless")

# Set up logging
logging.basicConfig(level=logging.INFO)

with Chrome(options=chOptions) as browser:
    browser.get(URL)
    logging.info(f"Opening headless Chrome browser with URL: {URL}")
    wait(10)
    html = browser.page_source

soup = BeautifulSoup(html, "html5lib")

# Find all the date elements and loop through them
dates = soup.find_all("div", class_="date-label")
#print(dates)
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
            logging.info(f"#### {i} title: {title} times {times} theater {theater}")
            for time in times:
                movies.append({"date": date_str, "title": title, "time": time, "theater": theater})
print(movies)