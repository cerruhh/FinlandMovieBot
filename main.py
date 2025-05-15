from openpyxl import load_workbook
import colorama
import requests
import datetime as dt
import pandas as pd
import json
import html
import re


from bs4 import BeautifulSoup
from os.path import abspath
from os.path import exists as file_exsits

from MovieClass import MovieClass
import sources
import emailfunc
import colorama
from settings_get import read_settings
from sources import normalizeTitle

all_settings=read_settings()
#from update_json import MovieUpdateFunction
#MovieUpdateFunction()


DAYOFFSET = all_settings["days_offset"] # 1 = tomorrow, 2 = the day after tomorrow, -1 yesterday, 0:today
SEND_MAIL=all_settings["send_mail"]
banned_theaters = all_settings["banned_theaters"]
banned_genres = all_settings["banned_genres"]

Enabled=True
if not Enabled:
    exit(6)

now_Date=dt.datetime.now()
Cur_WeekDay=now_Date.weekday()


class MovieNotFound(Exception):
    pass

class NainDeStainError(Exception):
    pass

def ExtractTime(time:str):
    """ extract time from source string, time is only relevant if there are more than 10 chaarcters"""
    #print(time[11:16])
    if len(time) < 15:
        return "NA"
    else:
        return time[11:16]

def ExtractDate(time:str):
    if len(time) < 10:
        return "NA"
    else:
        return time[0:10]

def list_to_string(input_list, delimiter=','):
    return delimiter.join(input_list)

def clean_string(s):
    # Convert to lowercase
    s = s.lower()
    # Remove spaces and punctuation
    s = re.sub(r'[^a-z0-9]', '', s)
    return s

def compare_strings(s1, s2):
    # Clean both strings
    cleaned_s1 = clean_string(s1)
    cleaned_s2 = clean_string(s2)

    # Compare the cleaned strings
    return cleaned_s1 == cleaned_s2

def extract_number(s):
    '''function is used to extract a number from the percentages used in the tomato scores'''
    match = re.search(r'\d{1,3}', s)
    return int(match.group()) if match else None



import json
import requests
from bs4 import BeautifulSoup
from tmdb import return_movie_details

def lookup_movie_score_tm(movie_title:str):
    """
    Lookup argument: movie title
    Returns dictionary that contains tomatometer score, audience score, average score, movie title as it is
    on rottentomatoes.com, release year, status, and summary of the movie.
    """


    tmdb_title, tmdb_original_title, tmdb_release_date, tmdb_genre_string, tmdb_score, tmdb_language, tmdb_synopsis= return_movie_details(movie_title)

    search_term = tmdb_title.lower().replace(" ", "_")
    search_url = f"https://www.rottentomatoes.com/search?search={search_term}"
    response = requests.get(search_url)
    soup = BeautifulSoup(response.content, 'html.parser')

    if soup.find('div', class_='search__no-results-copy-group'):
        return {"tomatometer": "NA", "audience_score": "NA", "average": "NA", "release_year": "NA", "tm_title": "NA", "synopsis": "NA", "status": 404, "genres": ["NA"]}

    movie_link = soup.find("h2", {"slot": "title", "data-qa": "search-result-title"}).find_next("a")["href"]
    movie_url = f"{movie_link}"
    movie_response = requests.get(movie_url)
    print(f"Looking for {movie_title} on tomato: {movie_url} ")
    # print(f"reference: {tmdb_title}, original title: {tmdb_original_title}, release: {tmdb_release_date}, synopsis: {tmdb_synopsis}, genre: {tmdb_genre_string}")
    movie_soup = BeautifulSoup(movie_response.content, 'html.parser')

    script_tag = movie_soup.find('script', {'data-json': 'vanity', 'type': 'application/json'})
    json_data = json.loads(script_tag.string.strip())
    tm_title = normalizeTitle(json_data.get('title', "NA"))
    release_date_text = json_data.get('lifecycleWindow', {}).get('date', "NA")
    if release_date_text == "NA":
        release_date_text = tmdb_release_date
    release_year = release_date_text.split("-")[0] if release_date_text != "NA" else "NA"

    critic_score = movie_soup.find('rt-text', {"slot": "criticsScore"})
    tomatometer_value = extract_number(critic_score.text) if critic_score else "NA"

    audience_score = movie_soup.find('rt-text', {"slot": "audienceScore"})
    audience_score_value = extract_number(audience_score.text) if audience_score else "NA"
    if audience_score_value == None:
        audience_score = tmdb_score

    if tomatometer_value is not None and audience_score_value is not None:
        average = f"{(tomatometer_value + audience_score_value) / 2:.1f}%"
    else:
        average = "NA"

   # average = f"{(tomatometer_value + audience_score_value) / 2:.1f}%" if tomatometer_value != "NA" and audience_score_value != "NA" else "NA"

    #synopsis_div = movie_soup.find('div', class_='synopsis-wrap')
    #synopsis = synopsis_div.find('rt-text', class_=None).get_text(strip=True) if synopsis_div else "NA"
    synopsis = tmdb_synopsis

    #genres = [genre.text for genre in movie_soup.find_all('rt-text', slot='metadataGenre')] or ["NA"]
    genres = tmdb_genre_string
    if compare_strings(tmdb_title, tm_title):
        tm_title = "match ok"
    else:
        tomatometer_value = audience_score_value = average = release_year = synopsis = genres = "NA"
        #genres = ["NA"]
        tm_title = "no match"

    return {"TomatoScore": tomatometer_value, "AudienceScore": audience_score_value, "Average": average, "TomatoYear": release_year, "TomatoTitle": tm_title, "Status": 200, "Synopsis": synopsis, "Genres": genres}


def purge_old_items(json_cache:str, days=30):
    """
    Purges items from the data dictionary that have an "updated" value older than the specified number of days.

    Args:
        json_cache (str): The json file with the data
        days (int): Number of days to consider as "old". Default is 30.

    Returns:
        empty: the json_cache is updated
    """
    with open(file=json_cache, mode="r+", encoding="UTF-8") as file:
        data = json.load(file)  # load the whole json file into dictionary "data"

    # Get the current date
    current_date = dt.datetime.now()
    items_to_remove = []

    # Iterate over the data dictionary and collect movies to remove
    for movie in data.items():
        movie_details = movie[1] # item[0] is the movie name, item[1] has the movie details
        #print(movie_details["updated"])
        # Parse the "updated" value as a datetime object
        updated_date = dt.datetime.fromisoformat(movie_details["Updated"])
        #print(f"updated_date: {updated_date}")
        # Calculate the difference between current date and updated date
        days_difference = (current_date - updated_date).days
        #print(f"days difference: {days_difference}")
        # If the difference is greater than the specified days, mark the item for removal
        if days_difference > days:
            items_to_remove.append(movie[0])
            #print(f"movie to remove: {movie[0]}")
        # Remove the marked items
    print(f"# items in dictionary before purge: {len(data)}")
    for movie in items_to_remove:
        # print (movie)
        data.pop(movie) #remove the movie from the dictionary
    print(f"# items in dictionary after purge: {len(data)}")

    # and write the full file back to the json
    with open(file=json_cache, mode="w", encoding="UTF-8") as file:
        json.dump(data, file, indent=3)

    return


def conditional_purge(json_cache: str, key_to_check: str):
    """
    Purges items from the data dictionary where the specified key has a value of None.

    Args:
        json_cache (str): The path to the JSON file with the data.
        key_to_check (str): The key to check for None values.

    Returns:
        None: The json_cache is updated.

    Examples:
        conditional_purge("Data/tomato.json", "tomatometer")
        conditional_purge("Data/tomato.json", "audience_score")
        conditional_purge("Data/tomato.json", "tm_year")
    """
    with open(file=json_cache, mode="r+", encoding="UTF-8") as file:
        data = json.load(file)  # Load the whole JSON file into dictionary "data"

    # Collect items to remove
    items_to_remove = [key for key, value in data.items() if value.get(key_to_check) is None]

    # Remove the marked items
    print(f"# items in dictionary before purge: {len(data)}")
    for key in items_to_remove:
        data.pop(key)  # Remove the item from the dictionary
    print(f"# items in dictionary after purge: {len(data)}")

    # Write the full file back to the JSON
    with open(file=json_cache, mode="w", encoding="UTF-8") as file:
        json.dump(data, file, indent=3)
    return



def get_movie_data(buffer_file:str, movie_title:str) -> dict:
    """
     Retrieve movie data from a buffer file or fetch it from a website if not found.

     Args:
     movie_title (str): The title of the movie to retrieve data for.
     buffer_file (str): The path to the buffer file. Default is 'tomato.json'.

     Returns:
     dict: The movie data retrieved from the buffer file or fetched from the website.
     """

    # Try to read the buffer file
    try:
        with open(buffer_file, 'r') as file:
            buffer_data = json.load(file)
    except FileNotFoundError:
        buffer_data = {}

    # Check if the movie data is already in the buffer
    if movie_title in buffer_data:
       # print(f"Retrieving data for '{movie_title}' from buffer.")
       return buffer_data[movie_title]
    else:
        print(f"Fetching data for '{movie_title}' from website.")
        # Example URL (replace with actual URL and parameters)
        movie_data  = lookup_movie_score_tm(movie_title)
         # Add timestamp to the fetched data
        movie_data['Updated'] = dt.datetime.now().isoformat()
         # Store the fetched data in the buffer
        buffer_data[movie_title] = movie_data
        with open(buffer_file, 'w') as file:
           json.dump(buffer_data, file, indent=4)
        return movie_data

def returnMovieDetails(movie_title:str, path:str="Data/tomato.json"):
    """Returns all data from a film from tomatometer (if found)
    args:
        moviename: string
        movieyearFinnKino: string, used to check if the movie queried is the same as the movie result
        path: location to the json file that is used as buffer
    returns: dictionary with
        'Status': 200
        'AudienceScore': '95%',
        'TomatoScore': '92%',
        'TomatoTitle': 'Dune: Part Two',
        'TomatoYear': '2024',
        'updated': '2024-07-13 21:05:02.218696'
        'Synopsis': 'summary'
        'Average': 93.5%
    """


#    fetchedData:dict=get_movie_data(buffer_file=path,movie_title=movie_title)
#    if (fetchedData == None):
#        return
#    else:
#        return fetchedData
# Function to check if any banned genre is in the genres string
def contains_banned_genre(genres, banned_genres):
    genres_list = genres.split(', ')
    for genre in genres_list:
        if genre in banned_genres:
            return True
    return False

#MAIN
if __name__ == "__main__":
    purge_old_items("Data/tomato.json", 30)  # purge the oldest items from the buffer, with value -1 all items are purged
    showsDict=sources.load_all(DAYOFFSET) #loads all the source data from the different theater websites

    #first data-row, does not contain relevant data
    dataframe=pd.DataFrame(data={
            "ShowStart": "-",
            "ShowEnd": "-",
            "ShowTitle": "-",
            "Theatre": "-",
            "Auditorium": "-",
            "PresentationMethod": "-",
            "ShowDate": "-",
            "ProductionYear": "-",
            "TomatoYear": "-",
            "TomatoTitle": "-",
            "AudienceScore": "-",
            "TomatoScore": "-",
            "Average": "-",
            "Synopsis": "-",
            "Genres": "-",
    },index=[False])

    #remove unwanted items

    #df.set_index('ID', inplace=True)
    counter = 0
    for show in showsDict:
        counter += 1
        # print (show)
        movie_result = get_movie_data(movie_title=html.unescape(show["ShowTitle"]), buffer_file="Data/tomato.json")
        # print(movie_result)
        merged_dict = {**show, **movie_result}
        # Convert the dictionary to a DataFrame
        new_data = pd.DataFrame([merged_dict])
        # Concatenate the new DataFrame with the existing one
        dataframe = pd.concat([dataframe, new_data], ignore_index=True)

    print(f"original dataframe: {len(dataframe)} items")
    dataframe = dataframe[~dataframe['Genres'].apply(lambda x: contains_banned_genre(x, banned_genres))]
    print(f"dataframe filtered on genre: {len(dataframe)} items")
    dataframe = dataframe[~dataframe['Theatre'].isin(banned_theaters)]
    print(f"dataframe filtered on theaters: {len(dataframe)} items")



    # print all to output file
    dataframe = dataframe.reset_index()
    dataframe = dataframe.sort_values(by=["ShowStart"])

    ######  SHEET 2 in the output.xls -> make list of all movies in output_movies.xlsx
    dataframe_sheet2 = dataframe.loc[:, ['ShowTitle', 'TomatoYear', 'TomatoTitle', 'AudienceScore', 'TomatoScore', 'Average', 'Synopsis', "Genres"]]
    #print(dataframe_sheet2.head())
    # drop the empty row with index = 0
    dataframe_sheet2=dataframe_sheet2.drop(index=0)
    #print(dataframe_sheet2.head())
    # change all "NA" and "" values to None
    dataframe_sheet2 = dataframe_sheet2.replace({'NA': None, '': None})
    #print(dataframe_sheet2.head())
    # remove all duplicates from database

    dataframe_sheet2['Genres'] = dataframe_sheet2['Genres'].apply(
        lambda x: ', '.join([str(genre) for genre in x]) if isinstance(x, list) else str(x))

    dataframe_sheet2 = dataframe_sheet2.drop_duplicates()

    #print(dataframe_sheet2.head())


    # Sort in descending order dataframe
    dataframe_sheet2 = dataframe_sheet2.sort_values(by='Average', ascending=False)


    # Move one column (e.g., 'A') to the last position
    columns = list(dataframe_sheet2.columns)
    columns.remove('Synopsis')
    columns.append('Synopsis')
    dataframe_sheet2 = dataframe_sheet2[columns]

    #print(dataframe_sheet2.head())
    ######  SHEET 2 in the output.xls -> make list of all movies in output_movies.xlsx

    try:
        dataframe.to_excel(abspath("Data/output.xlsx"),index=False)
    except PermissionError:
        print(colorama.Fore.YELLOW + "Please close Excel and try again.")

    filename = "Data/output.xlsx"

    existing_sheet = pd.read_excel(filename)

    with pd.ExcelWriter(path=filename, engine='openpyxl', mode='a') as writer:
        try:
            dataframe_sheet2.to_excel(writer, sheet_name='Sheet2', index=False, header=True)
        except PermissionError:
            print("Close the file in Excel and try again.")



    dataframe = dataframe.drop(columns=['Synopsis'])

    #encoding="UTF-8"
    dataframe.to_csv(abspath("Data/output.csv"),index=False,encoding="UTF-8")

    with open(file=abspath("Data/output.txt"),mode="w",encoding="UTF-8") as file:
        file.truncate(0)

    with open(file=abspath("Data/output.txt"),mode="a",encoding="UTF-8") as txtfile:
        counter=0
        for sn in dataframe.iterrows():
            if counter==0:
                counter=1
                continue
            ShowStart = sn[1].iloc[1]  # start time of show
            ShowEnd = sn[1].iloc[2]  # end time of show, only works for Finnkino
            Name=sn[1].iloc[3] # movietitle
            Theatername=sn[1].iloc[4] # theater where movie shows
            # 5 is the movie room
            PresMethod = sn[1].iloc[6]  # if move is 2D or 3D
            if PresMethod != "3D":
                PresMethod = ""
            # 7 is the date that the movie is displayed in the theater
            #8 is the production year in the FInnkino theater data
            ProdYear=sn[1].iloc[9] #production year according to tomato website
            # 10 is the movie title as returned by rotten tomato website if different from the movietitle
            AudienceScore = sn[1].iloc[11]  # audience score rottentomato
            Tomato=sn[1].iloc[12]  # tomatoscore


            #Movie: Original title (ProductionYear) - Tomatometer% + audience score%
            #When & Where: dttmShowStart - dttmShowEndTheater - TheatreAuditorium, PresentationMethod
            txtfile.write(f"{ShowStart} - {Name} ({ProdYear}) - {Tomato}+{AudienceScore} - {Theatername} {PresMethod} \n")

    # con.send_message(msg)
    FILE_LIST=[
        "Data/output.csv",
        "Data/output.txt",
        "Data/output.xlsx",
        # "Data/tomato.json",
        # "Data/finnkino.json"
    ]

    if SEND_MAIL and __name__=="__main__":
        print("preparing sending files by email")
        emailfunc.SendMail()