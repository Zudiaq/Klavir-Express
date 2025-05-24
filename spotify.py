import requests
import os
import logging
from dotenv import load_dotenv
from mood_mapping import get_spotify_recommendations_params
from config import DEBUG_MODE, SPOTIFY_PLAYLIST_URL
import json

load_dotenv()

SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')  
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')  
SPOTIFY_API_URL = "https://api.spotify.com/v1/"

# Set up logging
logging.basicConfig(
    level=logging.DEBUG if DEBUG_MODE else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def get_spotify_token():
    """
    Get Spotify API access token using client credentials flow
    
    Returns:
        str: Spotify access token
    """
    if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
        logging.error("Spotify API credentials are not set in environment variables")
        return None
        
    auth_url = "https://accounts.spotify.com/api/token"
    try:
        auth_response = requests.post(auth_url, {
            'grant_type': 'client_credentials',
            'client_id': SPOTIFY_CLIENT_ID,
            'client_secret': SPOTIFY_CLIENT_SECRET,
        })
        auth_response.raise_for_status()
        auth_response_data = auth_response.json()
        return auth_response_data['access_token']
    except requests.exceptions.RequestException as e:
        logging.error(f"Error getting Spotify token: {e}")
        return None


SENT_SONGS_FILE = "sent_songs.json"


def load_sent_songs():
    """
    Load the list of sent songs from the JSON file.
    Returns a set of tuples (track_name, artist_name, album_name)
    """
    if not os.path.exists(SENT_SONGS_FILE):
        logging.warning(f"Sent songs file not found. Initializing as an empty set.")
        return set()
    try:
        with open(SENT_SONGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not data:  # Handle empty file
                logging.warning(f"Sent songs file is empty. Initializing as an empty set.")
                return set()
            return set(tuple(item) for item in data)
    except json.JSONDecodeError as e:
        logging.warning(f"Could not load sent songs file: {e}. Initializing as an empty set.")
        return set()
    except Exception as e:
        logging.warning(f"Unexpected error while loading sent songs file: {e}")
        return set()


def save_sent_song(track_name, artist_name, album_name):
    """
    Save a new sent song to the JSON file and update the public repository.
    """
    sent_songs = load_sent_songs()
    sent_songs.add((track_name, artist_name, album_name))
    try:
        with open(SENT_SONGS_FILE, "w", encoding="utf-8") as f:
            json.dump(list(sent_songs), f, ensure_ascii=False, indent=2)
        update_sent_songs_in_repo()
    except Exception as e:
        logging.warning(f"Could not save sent song: {e}")


def update_sent_songs_in_repo():
    """
    Push the updated sent_songs.json file to the public repository.
    """
    github_token = os.getenv('KLAVIR_TOKEN')
    if not github_token:
        logging.error("KLAVIR_TOKEN is not set in environment variables. Skipping repository update.")
        return
    repo = "Zudiaq/Klavir-Express"
    file_path = "sent_songs.json"
    url = f"https://api.github.com/repos/{repo}/contents/{file_path}"
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    try:
        with open(SENT_SONGS_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        sha = response.json().get("sha")
        payload = {
            "message": "Update sent_songs.json",
            "content": content.encode("utf-8").decode("latin1"),
            "sha": sha
        }
        response = requests.put(url, headers=headers, json=payload)
        response.raise_for_status()
        logging.info("Successfully updated sent_songs.json in the repository.")
    except Exception as e:
        logging.error(f"Failed to update sent_songs.json in the repository: {e}")


def get_song_by_mood_spotify(mood):
    """
    Get song recommendations based on mood using Spotify's recommendation API or a specific playlist if configured.
    Returns:
        tuple: (track_name, artist_name, album_name, album_image, preview_url, spotify_link) or None if error.
    """
    token = get_spotify_token()
    if not token:
        logging.error("Failed to get Spotify token")
        return None
    headers = {
        'Authorization': f'Bearer {token}'
    }
    sent_songs = load_sent_songs()
    max_attempts = 10

    # If a playlist is specified in config, use it
    if SPOTIFY_PLAYLIST_URL:
        # Extract playlist ID from URL or use as is if it's just an ID
        import re
        playlist_id = None
        match = re.search(r'playlist[\/:]?([a-zA-Z0-9]+)', str(SPOTIFY_PLAYLIST_URL))
        if match:
            playlist_id = match.group(1)
        else:
            playlist_id = str(SPOTIFY_PLAYLIST_URL)
        playlist_url = f"{SPOTIFY_API_URL}playlists/{playlist_id}/tracks"
        try:
            response = requests.get(playlist_url, headers=headers, params={'limit': 100})
            response.raise_for_status()
            playlist_data = response.json()
            if 'items' in playlist_data and playlist_data['items']:
                valid_tracks = []
                for item in playlist_data['items']:
                    track = item.get('track')
                    if not track:
                        continue
                    valid_tracks.append(track)
                import random
                attempts = 0
                while attempts < max_attempts and valid_tracks:
                    track = random.choice(valid_tracks)
                    track_name = track.get('name')
                    artist_name = track['artists'][0]['name'] if track.get('artists') else None
                    album_name = track['album']['name'] if track.get('album') else None
                    album_image = track['album']['images'][0]['url'] if track.get('album') and track['album'].get('images') else None
                    preview_url = track.get('preview_url')
                    spotify_link = track.get('external_urls', {}).get('spotify')
                    song_key = (track_name, artist_name, album_name)
                    if song_key not in sent_songs:
                        save_sent_song(track_name, artist_name, album_name)
                        return track_name, artist_name, album_name, album_image, preview_url, spotify_link
                    attempts += 1
                logging.error("Could not find a unique song from the playlist after several attempts.")
                return None
            else:
                logging.warning("No items found in playlist data.")
                return None
        except Exception as e:
            logging.error(f"Error retrieving tracks from playlist: {e}")
            return None

    # Otherwise, use the global Spotify search logic
    for _ in range(max_attempts):
        result = direct_search(mood, headers)
        if not result:
            return None
        track_name, artist_name, album_name, album_image, preview_url, spotify_link = result
        song_key = (track_name, artist_name, album_name)
        if song_key not in sent_songs:
            save_sent_song(track_name, artist_name, album_name)
            return track_name, artist_name, album_name, album_image, preview_url, spotify_link
        else:
            logging.info(f"Duplicate song found: {song_key}, retrying...")
    logging.error("Could not find a unique song after several attempts.")
    return None

def direct_search(mood, headers):
    """
    Direct search method using Spotify's search API.
    Returns:
        tuple: (track_name, artist_name, album_name, album_image, preview_url, spotify_link) or None if error.
    """
    search_url = f"{SPOTIFY_API_URL}search"
    params = {'q': mood, 'type': 'track', 'limit': 10}
    try:
        response = requests.get(search_url, headers=headers, params=params)
        response.raise_for_status()
        response_data = response.json()
        if 'tracks' in response_data and response_data['tracks']['items']:
            import random
            track = random.choice(response_data['tracks']['items'])
            track_name = track['name']
            artist_name = track['artists'][0]['name']
            album_name = track['album']['name']
            album_image = track['album']['images'][0]['url'] if track['album']['images'] else None
            preview_url = track['preview_url']
            spotify_link = track.get('external_urls', {}).get('spotify')
            logging.info(f"Found track via search: {track_name} by {artist_name}")
            return track_name, artist_name, album_name, album_image, preview_url, spotify_link
    except requests.exceptions.RequestException as e:
        logging.error(f"Error in direct search: {e}")
    return None

def fallback_search(mood, headers):
    """
    Fallback method using search when recommendations fail
    
    Args:
        mood (str): The mood to search for
        headers (dict): Authorization headers
        
    Returns:
        tuple: (track_name, artist_name, None, None, None) or None if error
    """
    search_url = f"{SPOTIFY_API_URL}search"
    params = {
        'q': mood,
        'type': 'track',
        'limit': 1
    }
    
    try:
        logging.debug(f"Falling back to search for mood: {mood}")
        response = requests.get(search_url, headers=headers, params=params)
        response.raise_for_status()
        response_data = response.json()
        
        if response_data['tracks']['items']:
            track = response_data['tracks']['items'][0]
            track_name = track['name']
            artist_name = track['artists'][0]['name']
            album_name = track['album']['name']
            album_image = track['album']['images'][0]['url'] if track['album']['images'] else None
            preview_url = track['preview_url']
            
            logging.info(f"Found track via search: {track_name} by {artist_name}")
            return track_name, artist_name, album_name, album_image, preview_url
        else:
            logging.error("No tracks found for the given mood via search")
            return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Error in fallback search: {e}")
        return None
