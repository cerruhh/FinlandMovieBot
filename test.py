#import unittest

from main import returnMovieDetails
from main import lookup_movie_score_tm
from main import fetch_data
from main import purge_old_items
from settings_get import read_settings

#class TestClass(unittest.TestCase)
 #   def test_one
#print(lookup_movie_score_tm("Past Lives"))
#print(lookup_movie_score_tm("Twisters"))
#print(lookup_movie_score_tm("Opettajainhuone"))
#print(lookup_movie_score_tm("Stormskärs Maja"))
#print(returnMovieDetails("HAMMARSKJÖLD",2023, "../Data/tomato.json"))
#print(returnMovieDetails("Dune: Part Two", "2024","../Data/tomato.json"))
#print(fetch_data(update=False, json_cache="../Data/tomato.json",moviename="Dune: Part Two",movieyear=2023))
#print(fetch_data(update=False, json_cache="../Data/tomato.json",moviename="Dune: Part Two",movieyear=2024))

#test = purge_old_items("../Data/tomato.json", 0)
#tomatoObjectN1 = returnMovieDetails(movienametest="Dune 2", movieyearFinnKino="2023", path="../Data/tomato.json")
#print(f"tomato object: {tomatoObjectN1}")

print (read_settings())