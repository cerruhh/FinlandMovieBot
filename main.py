import requests
import datetime as dt
import pandas as pd
import json
import html
from os.path import abspath

from MovieClass import MovieClass
import sources
import emailfunc
#from update_json import MovieUpdateFunction
#MovieUpdateFunction()
Enabled=True
DAYOFFSET = 1 # 1 = tomorrow, 2 = the day after tomorrow, -1 yesterday, 0:today
SEND_MAIL=False
if Enabled==False:

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

def fetch_data(*,update:bool=False,json_cache:str,url:str,moviename:str,movieyear:str="2023"):


    if update:
        json_data=None
        print("json data Update true")
    else:
        try:
            with open(file=json_cache,mode="r+") as file:
                json_data=json.load(file)
                #print(json_data["Movies"])
                print(f"Cache:True, moviename: {html.unescape(moviename)}")
        except(FileNotFoundError,json.JSONDecodeError) as errorMessage:
            with open(file=json_cache,mode="r+",encoding="UTF-8",newline=None) as json_file:
                json.dump({
                    "Movies":{

                    }
                },file)
            json_data=None
        if json_data!=None:
            try:
                jsonresponse = json_data["Movies"][html.unescape(moviename)]

            except(IndexError,KeyError):
                #print("Cache: not found movie in cache")
                json_data=None

            else: #If no exception

                jsondate  = dt.datetime.strptime(ExtractDate(jsonresponse["updated"]), "%Y-%m-%d")
                thirtyDaysAgo = dt.datetime.now() - dt.timedelta(days=30)
                #print(type(jsondate))
                if jsondate < thirtyDaysAgo:
                    print("Cache is outdated, cache: False")
                    json_data=None
                else:
                    return jsonresponse   #tomato object returned from cache (and is uptodate)

######### nothing found in the cache, now check API ################################
        now = str(dt.datetime.now())
        if json_data==None or json_data["Movies"]=={}: # or dateinjson < thirtyDaysAgo
            url=f"{url}{moviename}"
            print("Cache not found: now searching via API: " + url)
            JSD=requests.get(url=url)

            if (str(JSD)== "<Response [500]>"):
#                print("404:could not find movie on tomatometer.")
                movieFound = False
            else:
                movieFound = True
                json_data = JSD.json()
                # print(JSD.json())

            with open(file=json_cache,mode="r+",encoding="UTF-8") as file:
                jsd=json.load(file)

            if movieFound:
                #json_data["status"]=200
                json_data["status"]=200
                json_data["updated"]=now
                jsd["Movies"][html.unescape(moviename)] = json_data

            else:
                # print(jsd)
                jsd["Movies"][html.unescape(moviename)]={
                    "status":404,
                    "audience_score":"NA",
                    "tomatometer":"NA",
                    "updated":now
                }

            with open(file=json_cache, mode="w", encoding="UTF-8") as file:
                json.dump(jsd,file,indent=3)

            #print(f"Cache: False, moviename: {moviename}, IsMovieFound: {movieFound}")
            if movieFound:
                return jsd["Movies"][html.unescape(moviename)]
    #if not json_data[moviename]:
    #print(json_data)
    #print("JsonDataBottm")
    #print(json_data)
    return {
        "status":404,
        "audience_score":"NA",
        "tomatometer":"NA"
    }


# def searchTomatoMeterScore(movienName:str, year:int):
#     return
#
# def searchTomatoAudienceScore(movienName:str, year:int):
#     return
def returnMovieDetails(movienametest:str, movieyearFinnKino:str):
    """Returns all data from a film from tomatometer (if found)
    :rtype: object
    """

    fetchedData:dict =fetch_data(update=False, json_cache=abspath("Data/tomato.json"),url=f"https://rotten-tomatoes-api.ue.r.appspot.com/movie/",moviename=movienametest,movieyear=movieyearFinnKino)
    #print(fetchedData)
    if fetchedData["status"]!=404:
        # print(f'ftchdata {fetchedData["year"]},movieyear Finnkino: {movieyearFinnKino}')
        try:
            #print(fetchedData)
            if str(fetchedData["year"]) != movieyearFinnKino and movieyearFinnKino != "NA":
                print( f"mismatch between movieyear FinnKino: {movieyearFinnKino}  and Tomato: {fetchedData['year']}")
                fetchedData["audience_score"] = "NA"
                fetchedData["tomatometer"] = "NA"
                fetchedData["status"] = 404
        except KeyError:
            print(f" Key Error!!! returnMovieDetails {fetchedData}")
            # temp = str(fetchedData["year"])
            # print(f"fetchedData - {movienametest} - {temp} - {movieyearFinnKino}")
            return {}

    return fetchedData


#fetchedData:dict =fetch_data(update=False, json_cache="Data/tomato.json",url=f"https://rotten-tomatoes-api.ue.r.appspot.com/movie/{movienametest}",moviename=movienametest,movieyear="2023")

#MAIN
if __name__ == "__main__":

    showsDict=sources.load_all(DAYOFFSET)

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
            "AudienceScore": "-",
            "TomatoScore": "-",
    },index=[False])

    #df.set_index('ID', inplace=True)
    counter = 0
    for show in showsDict:
        counter += 1

        tomatoObjectN1 = returnMovieDetails(movienametest=html.unescape(show["OriginalTitle"]), movieyearFinnKino=str(show["ProductionYear"]))
        if tomatoObjectN1 != {}:
            show["audience_score"]=tomatoObjectN1["audience_score"]
            show["tomatometer"]=tomatoObjectN1["tomatometer"]
            movie_class=MovieClass(show)
            dataframe.loc[len(dataframe)] =movie_class.datasample
        else:

            show["audience_score"]="NA"
            show["tomatometer"]="NA"
            movie_class=MovieClass(show)
            dataframe.loc[len(dataframe)] =movie_class.datasample


    # print all to output file
    dataframe = dataframe.reset_index()
    dataframe = dataframe.sort_values(by=["ShowStart"])
    dataframe.to_excel(abspath("Data/output.xlsx"),index=False)
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
            Name=sn[1].iloc[3]
            ProdYear=sn[1].iloc[8]
            Tomato=sn[1].iloc[10]
            AudienceScore=sn[1].iloc[9]
            ShowStart=sn[1].iloc[1]
            ShowEnd=sn[1].iloc[2]
            Audo=sn[1].iloc[4]
            PresMethod=sn[1].iloc[6]
            #Movie: Original title (ProductionYear) - Tomatometer% + audience score%
            #When & Where: dttmShowStart - dttmShowEndTheater - TheatreAuditorium, PresentationMethod
            txtfile.write(f"Movie: {Name} ({ProdYear}) - {Tomato}% + {AudienceScore}% -- {ShowStart}-{ShowEnd} - {Audo}, {PresMethod} \n")



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