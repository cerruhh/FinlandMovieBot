import datetime as dt
#import xmltodict
import json

UPDATED = str(dt.datetime.now()-dt.timedelta(3)) # "2023-12-26 22:17:21.203960"
with open(file="Data/tomato.json", mode="r+",encoding="UTF-8") as file:
    datadict=json.load(file)



def MovieUpdateFunction():
    try: #if movies doesn't exsist
        datadict["Movies"]
    except(KeyError, IndexError, json.JSONDecodeError): #create it
        datadict["Movies"] = {"Movies": {}}

    for movie in datadict["Movies"]: #loop through all movies

        moviedict = datadict["Movies"][movie]
        print(moviedict,movie)
        try: #if updated exsists
            #print(type(datadict["Movies"]))
            test = moviedict["updated"] #Check

        except(KeyError,IndexError,json.JSONDecodeError): #doesnt exsist
            moviedict["updated"]=UPDATED # create it

    with open(file="Data/tomato.json",mode="r+",encoding="UTF-8") as jsonfile: # open file
        jsonfile.truncate(0) #delete all contents
        json.dump(datadict,jsonfile,indent=3) # dump new contents
# if __name__=="__main__":
#     MovieUpdateFunction()