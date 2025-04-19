from os.path import abspath

print(abspath(".\\"))
import unittest

from main import returnMovieDetails
from main import lookup_movie_score_tm
from main import conditional_purge
from main import fetch_data
from main import purge_old_items
from main import compare_strings
from main import clean_string
from icecream import ic



class TestClass(unittest.TestCase):

   def test_one(self):
       #print("lookup_movie_score_tm('Flow 2':)")
       #purge_old_items("../Data/tomato.json", 10)  # purge the oldest items from the buffer, with value -1 all items are purged
       # conditional_purge("../Data/tomato.json", "tm_year") # will remove all values from tomato.json where tm_year = None
       print(lookup_movie_score_tm("Muistojen matka"))
       print(returnMovieDetails("Rosalie",  "../Data/tomato.json"))
       print(compare_strings("Halve gare 2.8", "halve_gare %&/"))
       sample_text = "This is a sample text with punctuation @#"
       cleaned_text = ic(clean_string(sample_text))
       print(ic(cleaned_text))  # Output: "thisissampletextwithpunctuation"
       print(fetch_data(update=False, json_cache="../Data/tomato.json",moviename="Dune: Part Two",movieyear=2023))
       score = lookup_movie_score_tm("Past Lives")["release_year"]
       self.assertEqual(score, "2023", "lookup movie resulted in error")
       self.assertEqual(lookup_movie_score_tm("Twisters")["release_year"],"2024", "lookup movie resulted in error")
       self.assertEqual(lookup_movie_score_tm("Opettajainhuone")["status"], 404, "status lookup incorrect")
       #self.assertEqual(returnMovieDetails("Dune: Part Two", "2024","../Data/tomato.json")["tm_year"],"2024", "error")

#print (read_settings())
if __name__ == '__main__':
    print("THOMAS")

    #print(f"lookup movie opettajainhuone: {lookup_movie_score_tm('Opettajainhuone')}")
    #print(lookup_movie_score_tm("Stormskärs Maja"))
    #print(returnMovieDetails("HAMMARSKJÖLD", "../Data/tomato.json"))
    unittest.main()
    # print(returnMovieDetails("Dune: Part Two", "2024","../Data/tomato.json"))
    # print(fetch_data(update=False, json_cache="../Data/tomato.json",moviename="Dune: Part Two",movieyear=2023))
    # print(fetch_data(update=False, json_cache="../Data/tomato.json",moviename="Dune: Part Two",movieyear=2024))

    # test = purge_old_items("../Data/tomato.json", 0)
    # tomatoObjectN1 = returnMovieDetails(movienametest="Dune 2", movieyearFinnKino="2023", path="../Data/tomato.json")
    # print(f"tomato object: {tomatoObjectN1}")
    #conditional_purge("tomato.json", "tm_year")
    print(lookup_movie_score_tm("Rosalie"))
    print(lookup_movie_score_tm("One Life"))
