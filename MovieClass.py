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

        self.showStart = ExtractTime(showdict["dttmShowStart"])
        self.showEnd = ExtractTime(showdict["dttmShowEnd"])
        self.showOriginalTitle = html.unescape(showdict["OriginalTitle"])
        self.showTheatre = showdict["Theatre"]
        self.TheatreAuditorium = showdict["TheatreAuditorium"]
        self.PressMethod = showdict["PresentationMethod"]
        self.ShowDate = ExtractDate(showdict["dttmShowStart"])
        self.ShowCreationDate = showdict["ProductionYear"]
        self.audience_score=showdict["audience_score"]
        self.tomato_meter=showdict["tomatometer"]

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

