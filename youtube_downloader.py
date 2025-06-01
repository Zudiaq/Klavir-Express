import os
import logging
import http.client
import json
import yaml
import requests
import base64
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

YAML_KEYS_FILE = "youtube-mp3-api-stats.yaml"
GH_PAT = os.getenv("GH_PAT")
GITHUB_REPO = "Zudiaq/youtube-mp3-apis"  # Replace with actual repo
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# ==========================
# Utility Functions
# ==========================
def pull_yaml_keys():
    """
    Pull the YAML file containing API keys from the private GitHub repository.
    """
    url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/{YAML_KEYS_FILE}"
    headers = {"Authorization": f"token {GH_PAT}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    with open(YAML_KEYS_FILE, "w", encoding="utf-8") as f:
        f.write(response.text)

def load_service_keys(service_name):
    """
    Load API keys for the specified service from the YAML file.
    """
    if not os.path.exists(YAML_KEYS_FILE):
        logging.info(f"YAML keys file not found. Pulling keys from GitHub.")
        pull_yaml_keys()
    try:
        with open(YAML_KEYS_FILE, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data.get(f"{service_name} keys", [])
    except yaml.YAMLError as e:
        logging.error(f"Error parsing YAML file: {e}")
        return []
    except Exception as e:
        logging.error(f"Unexpected error loading service keys: {e}")
        return []

def push_yaml_keys():
    """
    Push the updated YAML file back to the private GitHub repository.
    """
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{YAML_KEYS_FILE}"
    headers = {
        "Authorization": f"token {GH_PAT}",
        "Content-Type": "application/json"
    }
    try:
        with open(YAML_KEYS_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        # Get the SHA of the existing file
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        sha = response.json().get("sha", "")

        # Encode content in base64
        encoded_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")

        # Push the updated file
        payload = {
            "message": "Update YAML keys file",
            "content": encoded_content,
            "sha": sha
        }
        response = requests.put(url, headers=headers, json=payload)
        response.raise_for_status()
        logging.info("Successfully pushed YAML keys file to GitHub.")
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to push YAML keys file: {e}")

def update_key_usage(service_name, key, reset_day):
    """
    Update the usage count of an API key and handle daily reset logic.
    """
    if not os.path.exists(YAML_KEYS_FILE):
        logging.error(f"YAML keys file not found: {YAML_KEYS_FILE}")
        return

    try:
        with open(YAML_KEYS_FILE, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        keys = data.get(f"{service_name} keys", [])
        today = datetime.now().day
        for entry in keys:
            if entry["key"] == key:
                # Reset usage if it's the reset day and hasn't been reset today
                if today == reset_day and entry.get("last_reset") != str(datetime.now().date()):
                    entry["usage"] = 1
                    entry["last_reset"] = str(datetime.now().date())
                    logging.info(f"Usage reset for key: {key}")
                else:
                    # Increment usage
                    entry["usage"] += 1
                break
        else:
            logging.warning(f"Key {key} not found in the YAML file for service {service_name}.")

        # Save the updated YAML file locally
        with open(YAML_KEYS_FILE, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f)

        # Push the updated YAML file to GitHub
        push_yaml_keys()
        logging.info(f"Updated usage for key: {key}")
    except yaml.YAMLError as e:
        logging.error(f"Error parsing YAML file: {e}")
    except Exception as e:
        logging.error(f"Unexpected error updating key usage: {e}")

def get_available_key(service_name):
    """
    Get the first available API key for the specified service.
    """
    keys = load_service_keys(service_name)
    for entry in keys:
        if entry["usage"] < 300:
            return entry["key"], entry["reset_day"]
    notify_admins(f"All API keys for {service_name} are exhausted!")
    return None, None

def notify_admins(message):
    """
    Notify admins via Telegram when an issue occurs.
    """
    admin_chat_ids = os.getenv("ADMIN_CHAT_ID", "").split(",")
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token or not admin_chat_ids:
        logging.error("Telegram bot token or admin chat IDs are not set.")
        return

    for admin_id in admin_chat_ids:
        admin_id = admin_id.strip()
        if not admin_id:
            continue
        payload = {'chat_id': admin_id, 'text': message, 'parse_mode': 'HTML'}
        try:
            url = f'https://api.telegram.org/bot{token}/sendMessage'
            response = requests.post(url, json=payload)
            response.raise_for_status()
            logging.info(f"Notification sent to admin {admin_id}")
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to notify admin {admin_id}: {e}")

# ==========================
# API Integration
# ==========================
def fetch_youtube_download_link(video_id):
    """
    Fetch the YouTube MP3 download link using the web service.
    """
    service_name = "youtube-mp3-2025.p.rapidapi.com"
    api_key, reset_day = get_available_key(service_name)
    if not api_key:
        logging.error(f"No available API keys for {service_name}.")
        return None

    conn = http.client.HTTPSConnection("youtube-mp3-2025.p.rapidapi.com")
    payload = json.dumps({"id": video_id})
    headers = {
        'x-rapidapi-key': api_key,
        'x-rapidapi-host': service_name,
        'Content-Type': "application/json"
    }
    try:
        logging.info(f"Sending request to fetch MP3 download link for video ID {video_id}.")
        conn.request("POST", "/v1/social/youtube/audio", payload, headers)
        response = conn.getresponse()
        data = response.read().decode("utf-8")
        result = json.loads(data)

        if result.get("error"):
            logging.error(f"Error in API response: {result}")
            notify_admins(f"Error fetching download link for video ID {video_id}: {result}")
            return None

        download_link = result.get("linkDownload")
        if not download_link:
            logging.error(f"No download link found in the response for video ID {video_id}. Full response: {result}")
            return None

        logging.info(f"Download link fetched successfully for video ID {video_id}: {download_link}")
        update_key_usage(service_name, api_key, reset_day)
        return download_link
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON response: {e}")
    except Exception as e:
        logging.error(f"Error fetching YouTube download link: {e}")
        notify_admins(f"Unexpected error fetching download link for video ID {video_id}: {e}")
    return None

# ==========================
# Main Functionality
# ==========================
def search_and_download_youtube_mp3(track_name, artist_name, album_name=None):
    """
    Search YouTube for the track and download the audio as MP3.
    Returns the path to the downloaded MP3 file or None if failed.
    """
    try:
        query = f"{track_name} {artist_name}"
        if album_name:
            query += f" {album_name}"
        video_url = search_youtube_video(query, artist_name)
        if not video_url:
            logging.error("No YouTube video found for the query")
            return None

        mp3_url = fetch_youtube_download_link(video_url)
        if not mp3_url:
            logging.error("Failed to fetch YouTube MP3 download link")
            return None

        response = requests.get(mp3_url, stream=True)
        if response.status_code == 200:
            file_name = f"{track_name}_{artist_name}.mp3".replace(" ", "_")
            logging.info(f"Saving MP3 file to: {file_name}")
            with open(file_name, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            logging.info(f"MP3 file downloaded successfully: {file_name}")
            return file_name
        else:
            logging.error(f"Failed to download MP3 file. HTTP status code: {response.status_code}. Response: {response.text}")
            return None
    except Exception as e:
        logging.error(f"Error in search_and_download_youtube_mp3: {e}")
        return None

def search_youtube_video(query, artist_name):
    """
    Search for a YouTube video and validate it.
    """
    search_url = f"https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": query,
        "key": os.getenv("YOUTUBE_API_KEY"),
        "type": "video",
        "maxResults": 5
    }
    try:
        logging.info(f"Searching YouTube for query: {query}")
        response = requests.get(search_url, params=params)
        response.raise_for_status()
        results = response.json().get("items", [])
        logging.debug(f"Search results: {results}")

        for item in results:
            title = item["snippet"]["title"].lower()
            video_id = item["id"]["videoId"]
            logging.debug(f"Checking video: {title} (ID: {video_id})")
            if artist_name.lower() in title and not any(
                keyword in title for keyword in ["live", "karaoke", "cover", "remix", "loop"]
            ):
                logging.info(f"Found matching video: {title} (ID: {video_id})")
                return video_id

        logging.warning("No suitable video found in search results.")
    except requests.exceptions.HTTPError as e:
        if response.status_code == 403:
            logging.error("YouTube API returned 403 Forbidden. Check your API key or quota.")
            notify_admins("YouTube API returned 403 Forbidden. Please check the API key or quota.")
        else:
            logging.error(f"HTTP error during YouTube search: {e}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Error during YouTube search: {e}")
    except Exception as e:
        logging.error(f"Unexpected error during YouTube search: {e}")
    return None
