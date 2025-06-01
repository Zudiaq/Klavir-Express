# ==========================
# Last.fm API Integration
# ==========================
import requests
import os
import logging
from dotenv import load_dotenv

load_dotenv()

LASTFM_API_KEY = os.getenv('LASTFM_API_KEY')
LASTFM_API_SECRET = os.getenv('LASTFM_API_SECRET')
LASTFM_API_URL = "http://ws.audioscrobbler.com/2.0/"
DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"  # Fix: Initialize DEBUG_MODE here

logging.basicConfig(
    level=logging.DEBUG if DEBUG_MODE else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def get_song_by_mood(mood):
    """
    Retrieve a song recommendation based on mood using the Last.fm API.
    Args:
        mood (str): The mood derived from weather conditions.
    Returns:
        tuple: (track_name, artist_name) if successful, otherwise None.
    """
    if not LASTFM_API_KEY:
        logging.error("LASTFM_API_KEY is not set in environment variables.")
        return None

    refined_mood = mood.lower().strip()
    params = {
        'method': 'tag.gettoptracks',
        'tag': refined_mood,
        'api_key': LASTFM_API_KEY,
        'format': 'json'
    }
    try:
        logging.debug(f"Requesting songs for mood: {refined_mood}")
        response = requests.get(LASTFM_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logging.debug(f"Received data: {data}")
        if 'tracks' in data and 'track' in data['tracks']:
            top_track = data['tracks']['track'][0]
            track_name = top_track['name']
            artist_name = top_track['artist']['name']
            logging.info(f"Found track: {track_name} by {artist_name}")
            return track_name, artist_name
        else:
            logging.warning("No tracks found for the given mood.")
            return None
    except requests.exceptions.RequestException as req_err:
        logging.error(f"Request error occurred: {req_err}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
    return None
