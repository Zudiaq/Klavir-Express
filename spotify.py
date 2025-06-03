import requests
import os
import logging
import base64
import yaml
from dotenv import load_dotenv
from mood_mapping import get_spotify_recommendations_params
from youtube_downloader import update_key_usage

load_dotenv()

SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
SPOTIFY_API_URL = "https://api.spotify.com/v1/"
SPOTIFY_PLAYLIST_URL = ""

GH_PAT = os.getenv('GH_PAT')  # GitHub Personal Access Token
GITHUB_REPO = "Zudiaq/youtube-mp3-apis"
SENT_SONGS_FILE = "sent_songs.yaml"  # Corrected file path

DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"

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


def pull_sent_songs():
    """
    Pull the sent_songs.yaml file from the private GitHub repository.
    """
    url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/{SENT_SONGS_FILE}"
    headers = {"Authorization": f"token {GH_PAT}"}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        with open(SENT_SONGS_FILE, "w", encoding="utf-8") as f:
            f.write(response.text)
        logging.info("Successfully pulled sent_songs.yaml from GitHub.")
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            logging.warning(f"{SENT_SONGS_FILE} not found in the repository. Initializing a new file.")
            with open(SENT_SONGS_FILE, "w", encoding="utf-8") as f:
                yaml.dump([], f)  # Initialize an empty file
        else:
            logging.error(f"Failed to pull {SENT_SONGS_FILE}: {e}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to pull {SENT_SONGS_FILE}: {e}")
        with open(SENT_SONGS_FILE, "w", encoding="utf-8") as f:
            yaml.dump([], f)  # Initialize an empty file if pull fails

def push_file_to_github(file_path, content, commit_message, gh_pat):
    """
    Push a file to the private GitHub repository.
    
    Args:
        file_path (str): Path to the file in the repository.
        content (str): Content to write to the file.
        commit_message (str): Commit message for the update.
        gh_pat (str): GitHub Personal Access Token for authentication.
    """
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{file_path}"
    headers = {
        "Authorization": f"token {gh_pat}",
        "Content-Type": "application/json"
    }
    try:
        # Fetch the latest SHA of the file
        response = requests.get(url, headers=headers)
        sha = response.json().get("sha", "") if response.status_code == 200 else None

        # Encode content in base64
        encoded_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")

        # Push the updated file
        payload = {
            "message": commit_message,
            "content": encoded_content,
            "sha": sha
        }
        response = requests.put(url, headers=headers, json=payload)
        response.raise_for_status()
        logging.info(f"Successfully pushed {file_path} to GitHub.")
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 409:
            logging.warning(f"Conflict detected while pushing {file_path}. Retrying with the latest SHA.")
            # Retry by fetching the latest SHA
            response = requests.get(url, headers=headers)
            sha = response.json().get("sha", "")
            payload["sha"] = sha
            response = requests.put(url, headers=headers, json=payload)
            response.raise_for_status()
            logging.info(f"Successfully resolved conflict and pushed {file_path} to GitHub.")
        else:
            logging.error(f"Failed to push {file_path} to GitHub: {e}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to push {file_path} to GitHub: {e}")

def push_sent_songs():
    """
    Push the updated sent_songs.yaml file back to the private GitHub repository.
    """
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{SENT_SONGS_FILE}"
    headers = {
        "Authorization": f"token {GH_PAT}",
        "Content-Type": "application/json"
    }
    try:
        with open(SENT_SONGS_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        # Get the SHA of the existing file
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        sha = response.json().get("sha", "")

        # Encode content in base64
        encoded_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")

        # Push the updated file
        payload = {
            "message": "Update sent_songs.yaml",
            "content": encoded_content,
            "sha": sha
        }
        response = requests.put(url, headers=headers, json=payload)
        response.raise_for_status()
        logging.info("Successfully pushed sent_songs.yaml to GitHub.")
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to push sent_songs.yaml: {e}")

def load_sent_songs():
    """
    Load the list of sent songs from the YAML file.
    Returns a set of tuples (track_name, artist_name, album_name)
    """
    pull_sent_songs()  # Ensure the latest file is pulled
    if not os.path.exists(SENT_SONGS_FILE):
        with open(SENT_SONGS_FILE, "w", encoding="utf-8") as f:
            yaml.dump([], f)
        return set()
    try:
        with open(SENT_SONGS_FILE, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or []  # Initialize as an empty list if the file is empty
            return set(tuple(item.values()) for item in data)
    except (yaml.YAMLError, ValueError) as e:
        logging.warning(f"Could not load sent songs file: {e}. Reinitializing file.")
        with open(SENT_SONGS_FILE, "w", encoding="utf-8") as f:
            yaml.dump([], f)
        return set()

def save_sent_song(track_name, artist_name, album_name):
    """
    Save a new sent song to the YAML file and push it to GitHub.
    """
    sent_songs = load_sent_songs()
    sent_songs.add((track_name, artist_name, album_name))
    try:
        with open(SENT_SONGS_FILE, "w", encoding="utf-8") as f:
            yaml.dump([{"track_name": t, "artist_name": a, "album_name": al} for t, a, al in sent_songs], f)
        push_sent_songs()  # Push the updated file to GitHub
    except Exception as e:
        logging.warning(f"Could not save sent song: {e}")


def get_song_by_mood_spotify(mood):
    """
    Get song recommendations based on mood using Spotify's recommendation API or a specific playlist if configured.
    """
    token = get_spotify_token()
    if not token:
        logging.error("Failed to get Spotify token")
        return None
    headers = {
        'Authorization': f'Bearer {token}'
    }
    sent_songs = load_sent_songs()
    logging.info(f"Loaded sent songs: {sent_songs}")
    max_attempts = 10

    # If a playlist URL is provided, fetch songs from the playlist
    if SPOTIFY_PLAYLIST_URL:
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
            if not playlist_data or 'items' not in playlist_data:
                logging.error("Invalid playlist data received.")
                return None
            valid_tracks = [item['track'] for item in playlist_data['items'] if item.get('track')]
            logging.info(f"Valid tracks retrieved from playlist: {len(valid_tracks)}")
            import random
            attempts = 0
            while attempts < max_attempts and valid_tracks:
                track = random.choice(valid_tracks)
                track_name = track.get('name')
                artist_name = track['artists'][0]['name'] if track.get('artists') else None
                album_name = track['album']['name'] if track.get('album') else None
                album_image = track['album']['images'][0]['url'] if track.get('album') and track['album'].get('images') else None
                preview_url = track.get('preview_url')
                song_key = (track_name, artist_name, album_name)

                # Update usage for every attempt
                update_key_usage("spotify", SPOTIFY_CLIENT_ID, reset_day=None)

                if song_key not in sent_songs:
                    logging.info(f"Selected unique song: {song_key}")
                    save_sent_song(track_name, artist_name, album_name)
                    return track_name, artist_name, album_name, album_image, preview_url
                logging.info(f"Duplicate song found: {song_key}, retrying...")
                attempts += 1
            logging.error("Could not find a unique song from the playlist after several attempts.")
            return None
        except Exception as e:
            logging.error(f"Error retrieving tracks from playlist: {e}")
            return None

    # If no playlist URL is provided, search Spotify globally
    logging.info("No playlist URL provided. Searching Spotify globally.")
    for _ in range(max_attempts):
        result = direct_search(mood, headers)
        if not result:
            # Update usage for every failed attempt
            update_key_usage("spotify", SPOTIFY_CLIENT_ID, reset_day=None)
            return None
        track_name, artist_name, album_name, album_image, preview_url = result
        song_key = (track_name, artist_name, album_name)

        # Update usage for every attempt
        update_key_usage("spotify", SPOTIFY_CLIENT_ID, reset_day=None)

        if song_key not in sent_songs:
            logging.info(f"Selected unique song: {song_key}")
            save_sent_song(track_name, artist_name, album_name)
            return track_name, artist_name, album_name, album_image, preview_url
        else:
            logging.info(f"Duplicate song found: {song_key}, retrying...")
    logging.error("Could not find a unique song after several attempts.")
    return None
    

def direct_search(mood, headers):
    """
    Direct search method using Spotify's search API
    
    Args:
        mood (str): The mood to search for
        headers (dict): Authorization headers
        
    Returns:
        tuple: (track_name, artist_name, album_name, album_image, preview_url) or None if error
    """
    search_url = f"{SPOTIFY_API_URL}search"
    
    # Try different search strategies in order of preference
    search_strategies = [
        # Strategy 1: Search for tracks with the mood in the name
        {'q': f'genre:{mood}', 'type': 'track', 'limit': 5},
        # Strategy 2: Search for playlists with the mood and get a track
        {'q': f'playlist:{mood}', 'type': 'playlist', 'limit': 3},
        # Strategy 3: General search with the mood
        {'q': mood, 'type': 'track', 'limit': 10}
    ]
    
    for strategy in search_strategies:
        try:
            logging.debug(f"Trying search strategy with params: {strategy}")
            response = requests.get(search_url, headers=headers, params=strategy)
            response.raise_for_status()
            response_data = response.json()
            
            # Handle track search results
            if 'tracks' in response_data and response_data['tracks']['items']:
                # Get a random track from the results for variety
                import random
                tracks = response_data['tracks']['items']
                track = random.choice(tracks)
                
                track_name = track['name']
                artist_name = track['artists'][0]['name']
                album_name = track['album']['name']
                album_image = track['album']['images'][0]['url'] if track['album']['images'] else None
                preview_url = track['preview_url']
                
                logging.info(f"Found track via search: {track_name} by {artist_name}")
                return track_name, artist_name, album_name, album_image, preview_url
                
            # Handle playlist search results by getting a track from a playlist
            elif 'playlists' in response_data and response_data['playlists']['items']:
                # Find the first valid playlist with an 'id'
                playlist = next((pl for pl in response_data['playlists']['items'] if pl and 'id' in pl), None)
                if playlist and 'id' in playlist:
                    playlist_id = playlist['id']
                    # Get tracks from the playlist
                    playlist_url = f"{SPOTIFY_API_URL}playlists/{playlist_id}/tracks"
                    try:
                        playlist_response = requests.get(playlist_url, headers=headers, params={'limit': 10})
                        playlist_response.raise_for_status()
                        playlist_data = playlist_response.json()
                        if 'items' in playlist_data and playlist_data['items']:
                            # Get a random track from the playlist
                            import random
                            valid_tracks = [item['track'] for item in playlist_data['items'] if item and 'track' in item and item['track']]
                            if valid_tracks:
                                playlist_track = random.choice(valid_tracks)
                                track_name = playlist_track.get('name')
                                artist_name = playlist_track['artists'][0]['name'] if playlist_track.get('artists') else None
                                album_name = playlist_track['album']['name'] if playlist_track.get('album') else None
                                album_image = playlist_track['album']['images'][0]['url'] if playlist_track.get('album') and playlist_track['album'].get('images') else None
                                preview_url = playlist_track.get('preview_url')
                                logging.info(f"Found track from playlist: {track_name} by {artist_name}")
                                return track_name, artist_name, album_name, album_image, preview_url
                            else:
                                logging.warning("No valid tracks found in playlist.")
                        else:
                            logging.warning("No items found in playlist data.")
                    except Exception as e:
                        logging.warning(f"Error retrieving tracks from playlist: {e}")
                else:
                    logging.warning("No valid playlist with 'id' found in playlists response.")
        
        except requests.exceptions.RequestException as e:
            logging.warning(f"Search strategy failed: {e}")
            continue
    
    # If all strategies fail, try a very generic search
    try:
        logging.debug("Trying fallback generic search")
        fallback_params = {'q': 'popular', 'type': 'track', 'limit': 1}
        response = requests.get(search_url, headers=headers, params=fallback_params)
        response.raise_for_status()
        response_data = response.json()
        
        if 'tracks' in response_data and response_data['tracks']['items']:
            track = response_data['tracks']['items'][0]
            track_name = track['name']
            artist_name = track['artists'][0]['name']
            album_name = track['album']['name']
            album_image = track['album']['images'][0]['url'] if track['album']['images'] else None
            preview_url = track['preview_url']
            
            logging.info(f"Found track via fallback search: {track_name} by {artist_name}")
            return track_name, artist_name, album_name, album_image, preview_url
    except requests.exceptions.RequestException as e:
        logging.error(f"Final fallback search failed: {e}")
    
    logging.error("All search strategies failed")
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
