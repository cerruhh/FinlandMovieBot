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

all_settings=read_settings()
#from update_json import MovieUpdateFunction
#MovieUpdateFunction()


DAYOFFSET = all_settings["days_offset"] # 1 = tomorrow, 2 = the day after tomorrow, -1 yesterday, 0:today
SEND_MAIL=all_settings["send_mail"]

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


def clean_string(s):
    # Convert to lowercase
    s = s.lower()
    # Remove spaces and punctuation
    s = re.sub(r'[^\\w\\s]', '', s).replace(' ', '')
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

def lookup_movie_score_tm(movie_title):
    """ lookup argument: movie title
    returns dictionary that contains tomatometer score, the audience score, the average score, the movie title as it is
    on rottentomatoes.com, the release year, the status and the summary of the movie"""
    # Convert movie title to lowercase and replace spaces with underscores
    search_term = movie_title.lower().replace(" ", "_")

    # Create the search URL
    search_url = f"https://www.rottentomatoes.com/search?search={search_term}"

    # Send a GET request to the search URL
    response = requests.get(search_url)
    soup = BeautifulSoup(response.content, 'html.parser')


    no_results_tag = soup.find('div', class_='search__no-results-copy-group')
    print(f"no results tag: {no_results_tag}" )
    #print(f"no results tag bool: {bool(no_results_tag)}")
    if bool(no_results_tag):
        # no results
        return {"tomatometer": "NA", "audience_score": "NA", "average": "NA", "release_year": "NA", "tm_title": "NA", "synopsis": "NA", "status": 404}

    # Find the first movie link after the "Movies" section
    movie_link = soup.find("h2", {"slot": "title", "data-qa": "search-result-title"}).find_next("a")["href"]

    # Create the full movie URL
    movie_url = f"{movie_link}"
    print(movie_url)
    # Send a GET request to the movie URL
    movie_response = requests.get(movie_url)
    movie_soup = BeautifulSoup(movie_response.content, 'html.parser')

    # Send a GET request to the movie URL
    movie_response = requests.get(movie_url)
    movie_soup = BeautifulSoup(movie_response.content, 'html.parser')

    # Find the movie title and if it is similar to the movie_title then change it to "match ok"
    tm_title = movie_soup.find('h1', {'slot': 'titleIntro'}).find('span').text
    if compare_strings(movienametest, tm_title):
            tm_title = "match ok"

    # Find the tomato score and the audience score
    critic_score_element = movie_soup.find("rt-button", {"slot": "criticsScore"})
    critic_score = critic_score_element.find("rt-text").text
    # print(f"tomatometer: {critic_score}")
    audience_score_element = movie_soup.find("rt-button", {"slot": "audienceScore"})
    audience_score = audience_score_element.find("rt-text").text
    # print(f"audience score: {audience_score}")
    # Find the release date element

    tomatometer_value = extract_number(critic_score)
    audience_score_value = extract_number(audience_score)
    if tomatometer_value is not None and audience_score_value is not None:
        # Calculate the average
        average_number = (tomatometer_value + audience_score_value) / 2
        # Add the % symbol
        average = f"{average_number:.1f}%"
        print(f"tomatometer number: {tomatometer_value}, audience number: {audience_score_value}, average: {average_number}, average with percent: {average}")
    else:
        average = None

    #release_date_element = movie_soup.find( string='Release Date (Theaters)')
    release_date_element = movie_soup.find('rt-text', attrs={'slot': 'releaseDate'})
    synopsis_div = movie_soup.find('div', class_='synopsis-wrap')

    if synopsis_div:
        # Extract the text from the synopsis div, excluding the "Synopsis" key
        synopsis = synopsis_div.find('rt-text', class_=None).get_text(strip=True)
        #print("Synopsis:")
        #print(synopsis)
    else:
        synopsis = None

    if release_date_element:
        release_year = release_date_element.get_text(strip=True).replace(',', '')
    else:
        release_year = None

    return {"tomatometer": critic_score, "audience_score": audience_score, "average": average, "release_year": release_year, "tm_title":tm_title, "status":200, "synopsis":synopsis}


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
        updated_date = dt.datetime.strptime(movie_details["updated"], "%Y-%m-%d %H:%M:%S.%f")
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


def fetch_data(*,update:bool=False,json_cache:str,moviename:str,movieyear:str="2023"):
    """ This function acts like a buffer, checking if the movie is already in the json file, if not it will trigger
        a lookup.
        This function requires these args:
        update: set true to enforce update
        json_cache: the name of the json file with the buffer information,
        moviename: the movie name
        movieyear: the movie year

        return:
        status: like 200,
        audience_scor:e percentage
        tomatometer: percentage
        tm_title: tomatometer name of the movie
        tm_year: tomatomet year of the movie
        updated: when the movie was looked up
        """

    movietitle = html.unescape(moviename)
    if update:
        # to enforce an update
        json_data=None
        print("json data Update true")
    else: #no update enforced
        try:
            with open(file=json_cache,mode="r+") as file: #try opening json file
                json_data=json.load(file)
                #print(json_data["Movies"])
                print(f"Cache:True, movietitle: {movietitle}")
        except(FileNotFoundError,json.JSONDecodeError) as errorMessage: #if the json file with buffer is not found then
            # create an emptie file
            with open(file=json_cache,mode="r+",encoding="UTF-8",newline=None) as json_file:
                json.dump({},file)
            json_data=None
        if json_data!=None:
            try: # try and find the movie name from the buffer file
                jsonresponse = json_data[movietitle]

            except(IndexError,KeyError):
                #print("Cache: not found movie in cache")
                json_data=None

            else: #If no movie found in the buffer

                jsondate  = dt.datetime.strptime(ExtractDate(jsonresponse["updated"]), "%Y-%m-%d")
                thirtyDaysAgo = dt.datetime.now() - dt.timedelta(days=30)
                #print(type(jsondate))
                if jsondate < thirtyDaysAgo:
                    print("Cache is outdated, cache: False")
                    json_data=None
                else:
                    return jsonresponse   #tomato object returned from cache (and is uptodate)

######### nothing found in the cache, now check rotten tomato website ################################
        now = str(dt.datetime.now())
        if json_data==None or json_data=={}: # or dateinjson < thirtyDaysAgo
            url=f"{movietitle}"

            if all_settings["ratings_enabled"]:
                print("Cache not found: now searching Rotten Tomato: " + movietitle)
                movie_dict=lookup_movie_score_tm(movietitle) #actual lookup
            else:
                print("Cache not found, but not doing website lookup as ratings_enabled: False in settings.json")
                return

            with open(file=json_cache,mode="r+",encoding="UTF-8") as file:
                jsd=json.load(file) #load the whole file into jsd

            #now add the new movie
            jsd[movietitle]={
                "status":200,
                "audience_score":movie_dict["audience_score"],
                "tomatometer":movie_dict["tomatometer"],
                "average": movie_dict["average"],
                "tm_title": movie_dict["tm_title"],
                "tm_year": movie_dict["release_year"],
                "synopsis": movie_dict["synopsis"],
                "updated":now
            }

            #and write the full file back to the json
            with open(file=json_cache, mode="w", encoding="UTF-8") as file:
                json.dump(jsd,file,indent=3)

            #print(f"Cache: False, moviename: {moviename}, IsMovieFound: {movieFound}")
            if True:
                return jsd[movietitle]
    #if not json_data[moviename]:
    #print(json_data)
    #print("JsonDataBottm")
    #print(json_data)
    # something funny happened and we send this back
    return {
        "status":404,
        "audience_score":"NA",
        "tomatometer":"NA"
    }



def returnMovieDetails(movienametest:str, path:str="Data/tomato.json"):
    """Returns all data from a film from tomatometer (if found)
    args:
        moviename: string
        movieyearFinnKino: string, used to check if the movie queried is the same as the movie result
        path: location to the json file that is used as buffer
    returns: dictionary with
        'status': 200
        'audience_score': '95%',
        'tomatometer': '92%',
        'tm_title': 'Dune: Part Two',
        'tm_year': '2024',
        'updated': '2024-07-13 21:05:02.218696'
        'synopsis': 'summary'
        'average': 93.5%
    """

    fetchedData:dict=fetch_data(update=False, json_cache=path,moviename=movienametest,movieyear=movieyearFinnKino)
    if (fetchedData == None):
        return
    else:
        return fetchedData



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
    },index=[False])

    #df.set_index('ID', inplace=True)
    counter = 0
    for show in showsDict:
        counter += 1
        tomatoObjectN1={}
        tomatoObjectN1 = returnMovieDetails(movienametest=html.unescape(show["OriginalTitle"]), movieyearFinnKino=str(show["ProductionYear"]), path="Data/tomato.json")

        if tomatoObjectN1 != {} and tomatoObjectN1 != None:
            show["audience_score"]=tomatoObjectN1["audience_score"]
            show["tomatometer"]=tomatoObjectN1["tomatometer"]
            show["tm_title"] = tomatoObjectN1["tm_title"]
            show["tm_year"] = tomatoObjectN1["tm_year"]
            show["average"] = tomatoObjectN1["average"]
            show["synopsis"] = tomatoObjectN1["synopsis"]
            movie_class=MovieClass(show)
            # example of show
            # show: {'OriginalTitle': 'A Quiet Place:\xa0Day One', 'TheatreAuditorium': '3 REX',
            # 'dttmShowStart': '2024-07-14T21:00:00', 'Theatre': 'BioRex Kulttuurikasarmi', 'ProductionYear': 'NA',
            # 'dttmShowEnd': 'NA', 'PresentationMethod': 'NA', 'audience_score': '73%', 'tomatometer': '87%',
            # 'tm_title': 'A Quiet Place: Day One'}

            #print(f"movie class: {movie_class}")
            dataframe.loc[len(dataframe)] =movie_class.datasample
        else:
            if tomatoObjectN1 == {} :
                show["audience_score"]="NA"
                show["tomatometer"]="NA"
                movie_class=MovieClass(show)
                dataframe.loc[len(dataframe)] =movie_class.datasample
        # print(f"tomato object: {tomatoObjectN1}")

    # print all to output file
    dataframe = dataframe.reset_index()
    dataframe = dataframe.sort_values(by=["ShowStart"])

    ######  SHEET 2 in the output.xls -> make list of all movies in output_movies.xlsx
    dataframe_sheet2 = dataframe.loc[:, ['ShowTitle', 'TomatoYear', 'TomatoTitle', 'AudienceScore', 'TomatoScore', 'Average', 'Synopsis']]
    print(dataframe_sheet2.head())
    # drop the empty row with index = 0
    dataframe_sheet2=dataframe_sheet2.drop(index=0)
    print(dataframe_sheet2.head())
    # change all "NA" and "" values to None
    dataframe_sheet2 = dataframe_sheet2.replace({'NA': None, '': None})
    print(dataframe_sheet2.head())
    # remove all duplicates from database
    dataframe_sheet2 = dataframe_sheet2.drop_duplicates()
    print(dataframe_sheet2.head())


    # Sort in descending order dataframe
    dataframe_sheet2 = dataframe_sheet2.sort_values(by='Average', ascending=False)


    # Move one column (e.g., 'A') to the last position
    columns = list(dataframe_sheet2.columns)
    columns.remove('Synopsis')
    columns.append('Synopsis')
    dataframe_sheet2 = dataframe_sheet2[columns]

    print(dataframe_sheet2.head())
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
            # 7 is the date that the movie is displayed in the theater
            #8 is the production year in the FInnkino theater data
            ProdYear=sn[1].iloc[9] #production year according to tomato website
            # 10 is the movie title as returned by rotten tomato website if different from the movietitle
            AudienceScore = sn[1].iloc[11]  # audience score rottentomato
            Tomato=sn[1].iloc[12]  # tomatoscore


            #Movie: Original title (ProductionYear) - Tomatometer% + audience score%
            #When & Where: dttmShowStart - dttmShowEndTheater - TheatreAuditorium, PresentationMethod
            txtfile.write(f"Movie: {Name} ({ProdYear}) - {Tomato} + {AudienceScore} -- {ShowStart}-{ShowEnd} - {Theatername}, {PresMethod} \n")

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