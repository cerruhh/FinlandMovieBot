import datetime as dt
import html

#self,moviename:str,movieyear:str,movietheater:str,moviehall:str,moviestart:str, movie_end,tomato_score, audience_score,show_date, movie_2Dor3D


def ExtractDate(time: str):
    return time[0:10]

def ExtractTime(time: str):
    # print(time[11:16])
    return time[11:16]
class MovieClass:
    def __init__(self, showdict:dict):
        # self.movie_name=moviename
        # self.movie_year=movieyear
        # self.movie_theater=movietheater
        # self.movie_hall=moviehall
        # self.movie_start_time=moviestart
        # self.movie_end = movie_end
        # self.tomato_score = tomato_score
        # self.audience_score=audience_score
        # self.showdate=show_date
        # self.movie_year = movieyear
        # self.movie2D_or_3D = movie_2Dor3D

        if ("dttmShowStart" in showdict):
            self.showStart = ExtractTime(showdict["dttmShowStart"])
        else:
            self.showStart = "NA"

        if ("dttmShowEnd" in showdict):
            self.showEnd = ExtractTime(showdict["dttmShowEnd"])
        else:
            self.showEnd = "NA"

        if ("OriginalTitle" in showdict):
            self.showOriginalTitle = html.unescape(showdict["OriginalTitle"])
        else:
            self.showOriginalTitle = "NA"

        if ("Theatre" in showdict):
            self.showTheatre = showdict["Theatre"]
        else:
            self.showTheatre = "NA"

        if ("TheatreAuditorium" in showdict):
            self.TheatreAuditorium = showdict["TheatreAuditorium"]
        else:
            self.TheatreAuditorium = "NA"

        if ("PresentationMethod" in showdict):
            self.PressMethod = showdict["PresentationMethod"]
        else:
            self.PressMethod = "NA"

        if ("dttmShowStart" in showdict):
            self.ShowDate = ExtractDate(showdict["dttmShowStart"])
        else:
            self.ShowDate = "NA"

        if ("ProductionYear" in showdict):
            self.ShowCreationDate = showdict["ProductionYear"]
        else:
            self.ShowCreationDate = "NA"

        if ("audience_score" in showdict):
            self.audience_score=showdict["audience_score"]
        else:
            self.audience_score = "NA"

        if ("tomatometer" in showdict):
            self.tomato_meter=showdict["tomatometer"]
        else:
            self.tomato_meter = "NA"

        self.datasample={
            "ShowStart": self.showStart,
            "ShowEnd": self.showEnd,
            "ShowTitle": self.showOriginalTitle,
            "Theatre": self.showTheatre,
            "Auditorium": self.TheatreAuditorium,
            "PresentationMethod": self.PressMethod,
            "ShowDate": self.ShowDate,
            "ProductionYear": self.ShowCreationDate,
            "AudienceScore": self.audience_score,
            "TomatoScore": self.tomato_meter,
        }

