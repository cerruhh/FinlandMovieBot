import requests
import datetime as dt
import pandas as pd
import xmltodict
import json
import openpyxl
import html
import smtplib as smtp
from os.path import basename
from os.path import abspath
from MovieClass import MovieClass
import sources


# from email.mime.text import MIMEText
# from email.mime.multipart import MIMEMultipart
# from email.mime.application import MIMEAppliation

import emailfunc
#from update_json import MovieUpdateFunction
#MovieUpdateFunction()
Enabled=True
DAYOFFSET = 1 # 1 = tomorrow, 2 = the day after tomorrow, -1 yesterday, 0:today
SEND_MAIL=False
if Enabled==False:
    exit(6)


# now = dt.datetime.now()
# #opa
# if now.month==10 and now.day ==21:
#     connection = smtp.SMTP("smtp.gmail.com", port=587)
#     connection.starttls()Content-Type: text/html; charset=Shift_JIS
#     connection.login(user=EMAIL, password=KEY)
#     connection.sendmail(from_addr=EMAIL, to_addrs=family_emails[0],
#                         msg="Subject:waar is de man van toadish?\n\nDit is een belangrijke vraag")
#     connection.close()
now_Date=dt.datetime.now()
Cur_WeekDay=now_Date.weekday()




class MovieNotFound(Exception):
    pass

class NainDeStainError(Exception):
    pass

# with open(file="Data/tomato.json",encoding="UTF-8",mode="r+") as file:
#     js = json.load(file)
#     try:
#         jsResponse=js["Movies"]
#     except(KeyError,json.JSONDecodeError):
#         js["Movies"]={}



def ExtractTime(time:str):
    #print(time[11:16])
    return time[11:16]

def ExtractDate(time:str):
    return time[0:10]

def fetch_data(*,update:bool=False,json_cache:str="Data/tomato.json",url:str,moviename:str="wonka",movieyear:str="2023"):
    if __name__!="__main__":
        raise NainDeStainError
        return 0
    if update==True:
        json_data=None
        print("json data Update true")
    else:
        try:
            with open(file=json_cache,mode="r+") as file:
                json_data=json.load(file)
                #print(json_data["Movies"])
                print(f"Cache:True, moviename: {html.unescape(moviename)},status:Cache")
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
                    print("Cache is outdate, cache: False")
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
                # print("write movie without result to cache")
                # jsd["Movies"][moviename]={
                #     "status":404
                # }

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
def returnMovieDetals(movienametest:str,movieyearFinnKino:str):
    """Returns all data from a film from tomatometer (if found)"""
    if __name__=="__main__":
        fetchedData:dict =fetch_data(update=False, json_cache=abspath("Data/tomato.json"),url=f"https://rotten-tomatoes-api.ue.r.appspot.com/movie/",moviename=movienametest,movieyear=movieyearFinnKino)
    #print(fetchedData)
    if fetchedData["status"]!=404:
        # print(f'ftchdata {fetchedData["year"]},movieyear Finnkino: {movieyearFinnKino}')
        if str(fetchedData["year"])!=movieyearFinnKino:
            fetchedData["audience_score"]="NA"
            fetchedData["tomatometer"]="NA"
            fetchedData["status"]=404
    return fetchedData



#fetchedData:dict =fetch_data(update=False, json_cache="Data/tomato.json",url=f"https://rotten-tomatoes-api.ue.r.appspot.com/movie/{movienametest}",moviename=movienametest,movieyear="2023")




#MAIN

#data download from FINNKINO API
showsDict=sources.load_finnkino(DAYOFFSET)

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
    # if counter>11: #print max 11 records for testing
    #     continue
    counter += 1
    # if counter==1:
    #     continue
    tomatoObjectN1 = returnMovieDetals(movienametest=html.unescape(show["OriginalTitle"]), movieyearFinnKino=str(show["ProductionYear"]))
    show["audience_score"]=tomatoObjectN1["audience_score"]
    show["tomatometer"]=tomatoObjectN1["tomatometer"]
    #
    # showStart=ExtractTime(show["dttmShowStart"])
    # showEnd=ExtractTime(show["dttmShowEnd"])
    # showOriginalTitle=
    # showTheatre=show["Theatre"]
    # TheatreAuditorium=show["TheatreAuditorium"]
    # PressMethod=show["PresentationMethod"]
    # ShowDate = ExtractDate(show["dttmShowStart"])
    # ShowCreationDate = show["ProductionYear"]

    # print("movie: " + showOriginalTitle + " FinnKino production year: " + str(ShowCreationDate))


    #print("TomatoooObjectok1")
    #print(tomatoObject)
    movie_class=MovieClass(show)

    #print("movie: " + showOriginalTitle + " tomatoObject2: " + str(tomatoObjectN1))
    dataframe.loc[len(dataframe)] =movie_class.datasample
    #     {
    #     "ShowStart":showStart,
    #     "ShowEnd":showEnd,
    #     "ShowTitle":showOriginalTitle,
    #     "Theatre":showTheatre,
    #     "Auditorium":TheatreAuditorium,
    #     "PresentationMethod":PressMethod,
    #     "ShowDate": ShowDate,
    #     "ProductionYear": ShowCreationDate,
    #     "AudienceScore":tomatoObjectN1["audience_score"],
    #     "TomatoScore":tomatoObjectN1["tomatometer"],
    # }

# print all to output file
dataframe = dataframe.reset_index()
dataframe.to_excel(abspath("Data/output.xlsx"),index=False)
#encoding="UTF-8"
dataframe.to_csv(abspath("Data/output.csv"),index=False,encoding="UTF-8")
showsDict=sources.load_finnkino(day_offset=DAYOFFSET,give_all=False)
# Print Finnkino data for analysis:
json_data = json.dumps(showsDict,indent=2)
json_data.encode("UTF-8")
with open(file=abspath("Data/finnkino.json"),mode="w") as json_file:
    json_file.write(json_data)

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


