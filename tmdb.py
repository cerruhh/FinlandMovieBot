import requests
import json
from urllib.parse import quote
from pathlib import Path

def load_secrets():
    # Get path to secrets.json relative to this file
    current_dir = Path(__file__).parent  # src/ directory
    secrets_path = current_dir / "Data" / "secrets.json"

    try:
        with open(secrets_path) as f:
            return json.load(f)
    except FileNotFoundError:
        raise RuntimeError(f"Secrets file not found at {secrets_path}")
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON format in secrets file")

def tmdb_search_movie(search_string:str)-> str:
    """Search for a movie using the TMDb API and return the first result.

       Args: search_string: The movie title to search for.

       Returns:
           Union[Dict, str]: Dictionary of the first movie result if found,
           "NA" if no results or errors occur.

       Raises:
           RuntimeError: If secrets file is missing or API key is invalid.
           ConnectionError: If network-related errors occur.
       """
    try:
        # URL-encode the search string to handle special characters
        encoded_search = quote(search_string)
        url = f"https://api.themoviedb.org/3/search/movie?query={encoded_search}&include_adult=true&page=1"

        # Load secrets with validation
        secrets = load_secrets()
        if "tmdb_api_key" not in secrets:
            raise RuntimeError("TMDB API key missing in secrets.json")

        headers = {
            "accept": "application/json",
            "Authorization": secrets["tmdb_api_key"]
        }

        # Handle network errors
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Raises HTTPError for 4xx/5xx status codes

        data = response.json()

        # Validate response structure
        if data.get("total_results", 0) > 0:
            return data["results"][0]
        return "NA"

    except (requests.ConnectionError, requests.Timeout) as e:
        raise ConnectionError(f"Network error occurred: {str(e)}")
    except requests.HTTPError as e:
        return f"NA (HTTP Error: {e.response.status_code})"
    except KeyError as e:
        raise RuntimeError(f"Missing expected key in API response: {str(e)}")
    except json.JSONDecodeError:
        raise RuntimeError("Failed to decode API response")
    except Exception as e:
        raise RuntimeError(f"Unexpected error: {str(e)}")

def tmdb_genres() -> dict:
    url = f"https://api.themoviedb.org/3/genre/movie/list"

    secrets = load_secrets()
    tmdb_api = secrets["tmdb_api_key"]

    headers = {
        "accept": "application/json",
        "Authorization": tmdb_api
    }

    response  = requests.get(url, headers=headers)
    genres = response.json()["genres"]
    # Create a dictionary: {id: name}
    genre_dict = {genre["id"]: genre["name"] for genre in genres}

    return genre_dict

def return_movie_details(search_string:str):
    genre_dict = tmdb_genres()
    movie = tmdb_search_movie(search_string)

    if movie == "NA":
        return "NA","NA","NA","NA","NA","NA","NA"
    genre_names = [genre_dict[gid] for gid in movie["genre_ids"]]
    genre_string = ', '.join(genre_names) if genre_names else 'N/A'
    title = movie["title"]
    original_title = movie["original_title"]
    release_date = movie.get("release_date", "NA")
    language = movie.get("original_language")
    synopsis = movie.get("overview", "NA")
    score =  movie.get("vote_average", "NA")
    if score != "NA":
        score = round(10*score)

    return title, original_title, release_date, genre_string, score, language, synopsis,

#from tmdb import return_movie_details
#title, original_title, release_date, synopsis, genre_string = return_movie_details("trois amies")
#print(tmdb_search_movie("trois amies"))