import requests
import os
import logging
import yaml
import json
import http.client
from dotenv import load_dotenv
from mood_mapping import get_spotify_recommendations_params
from config import DEBUG_MODE, SPOTIFY_PLAYLIST_URL
from telegram_bot import send_audio_with_caption

load_dotenv()

SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
SPOTIFY_API_URL = "https://api.spotify.com/v1/"
GH_PAT = os.getenv('GH_PAT')
YAML_REPO = "Zudiaq/youtube-mp3-apis"
YAML_FILE_PATH = "youtube-mp3-api-stats.yaml"

logging.basicConfig(
    level=logging.DEBUG if DEBUG_MODE else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def fetch_yaml_file():
    """
    Fetch the YAML file from the private GitHub repository.
    Returns:
        dict: Parsed YAML content.
    """
    url = f"https://raw.githubusercontent.com/{YAML_REPO}/main/{YAML_FILE_PATH}"
    headers = {"Authorization": f"token {GH_PAT}"}
    try:
        response = requests.get(url, headers=headers, timeout=10)  # Add timeout for reliability
        response.raise_for_status()
        return yaml.safe_load(response.text)
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch YAML file: {e}")
        return None

def update_yaml_file(content):
    """
    Update the YAML file in the private GitHub repository.
    Args:
        content (dict): Updated YAML content.
    """
    url = f"https://api.github.com/repos/{YAML_REPO}/contents/{YAML_FILE_PATH}"
    headers = {"Authorization": f"token {GH_PAT}"}
    try:
        # Fetch the current file to get the SHA
        response = requests.get(url, headers=headers, timeout=10)  # Add timeout
        response.raise_for_status()
        sha = response.json()["sha"]

        # Prepare the updated content
        updated_content = yaml.dump(content, default_flow_style=False)
        payload = {
            "message": "Update API key usage",
            "content": updated_content.encode("utf-8").decode("base64"),
            "sha": sha
        }
        response = requests.put(url, headers=headers, json=payload)
        response.raise_for_status()
        logging.info("YAML file updated successfully.")
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to update YAML file: {e}")

def get_api_key():
    """
    Select a usable API key from the YAML file.
    Returns:
        str: API key.
    """
    yaml_content = fetch_yaml_file()
    if not yaml_content:
        return None

    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    for key_entry in yaml_content["keys"]:
        if key_entry["usage"] < 300:
            # Reset logic optimization
            if key_entry["reset_day"] == datetime.now().day and key_entry["last_reset"] != today:
                key_entry.update({"usage": 0, "last_reset": today})
            key_entry["usage"] += 1
            update_yaml_file(yaml_content)
            return key_entry["key"]
    logging.error("No usable API key found.")
    return None

def download_mp3_from_youtube(video_id):
    """
    Use the RapidAPI to download the MP3 file for the given YouTube video ID.
    Args:
        video_id (str): YouTube video ID.
    Returns:
        str: Path to the downloaded MP3 file.
    """
    api_key = get_api_key()
    if not api_key:
        return None

    conn = http.client.HTTPSConnection("youtube-mp36.p.rapidapi.com")
    headers = {
        'x-rapidapi-key': api_key,
        'x-rapidapi-host': "youtube-mp36.p.rapidapi.com"
    }
    try:
        conn.request("GET", f"/dl?id={video_id}", headers=headers)
        res = conn.getresponse()
        data = res.read()
        response = json.loads(data.decode("utf-8"))

        if response.get("status") == "ok":
            mp3_link = response.get("link")
            mp3_path = "downloaded_song.mp3"
            with requests.get(mp3_link, stream=True) as r:
                r.raise_for_status()
                with open(mp3_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            return mp3_path
        else:
            logging.error(f"Failed to download MP3: {response}")
            return None
    except http.client.HTTPException as e:
        logging.error(f"HTTP error during MP3 download: {e}")
        return None

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
        }, timeout=10)  # Add timeout
        auth_response.raise_for_status()
        return auth_response.json().get('access_token')
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
        return set()
    try:
        with open(SENT_SONGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return set(tuple(item) for item in data)
    except Exception as e:
        logging.warning(f"Could not load sent songs file: {e}")
        return set()


def save_sent_song(track_name, artist_name, album_name):
    """
    Save a new sent song to the JSON file.
    """
    sent_songs = load_sent_songs()
    sent_songs.add((track_name, artist_name, album_name))
    try:
        with open(SENT_SONGS_FILE, "w", encoding="utf-8") as f:
            json.dump(list(sent_songs), f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.warning(f"Could not save sent song: {e}")


def get_song_by_mood_spotify(mood):
    """
    Get song recommendations based on mood using Spotify's recommendation API.
    Then search for the corresponding YouTube link and download the MP3.
    """
    token = get_spotify_token()
    if not token:
        logging.error("Failed to get Spotify token")
        return None

    headers = {'Authorization': f'Bearer {token}'}
    mood_params = get_spotify_recommendations_params(mood)
    search_url = f"{SPOTIFY_API_URL}search"
    params = {'q': mood_params["seed_genres"], 'type': 'track', 'limit': 1}

    try:
        response = requests.get(search_url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        track = response.json()["tracks"]["items"][0]
        track_name = track["name"]
        artist_name = track["artists"][0]["name"]
        album_name = track["album"]["name"]
        album_image = track["album"]["images"][0]["url"]

        # Search YouTube for the song
        youtube_query = f"{track_name} {artist_name} official audio"
        youtube_search_url = f"https://www.googleapis.com/youtube/v3/search"
        youtube_params = {
            "part": "snippet",
            "q": youtube_query,
            "key": os.getenv("YOUTUBE_API_KEY"),
            "maxResults": 1
        }
        youtube_response = requests.get(youtube_search_url, params=youtube_params, timeout=10)
        youtube_response.raise_for_status()
        video_id = youtube_response.json()["items"][0]["id"]["videoId"]

        # Download MP3 from YouTube
        mp3_path = download_mp3_from_youtube(video_id)
        if mp3_path:
            metadata = {
                "track_name": track_name,
                "artist_name": artist_name,
                "album_name": album_name,
                "album_image": album_image
            }
            send_audio_with_caption(mp3_path, f"🎵 {track_name} by {artist_name}", metadata)
        else:
            logging.error("Failed to download MP3.")
    except requests.exceptions.RequestException as e:
        logging.error(f"Error in Spotify to YouTube workflow: {e}")
