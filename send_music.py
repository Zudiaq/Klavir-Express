import os
import re
import logging
import http.client
import requests
import yaml
import json
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
        pull_yaml_keys()
    with open(YAML_KEYS_FILE, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get(service_name, [])

def update_key_usage(service_name, key, reset_day):
    """
    Update the usage count of an API key and handle monthly reset logic.
    """
    with open(YAML_KEYS_FILE, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    keys = data.get(service_name, [])
    today = datetime.now().day
    for entry in keys:
        if entry["key"] == key:
            if today == reset_day and entry["last_reset"] != str(datetime.now().date()):
                entry["usage"] = 1
                entry["last_reset"] = str(datetime.now().date())
            else:
                entry["usage"] += 1
            break
    with open(YAML_KEYS_FILE, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f)

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

def fetch_youtube_download_link(video_id):
    """
    Fetch the YouTube download link using the web service.
    """
    service_name = "youtube-mp3-2025.p.rapidapi.com"
    retry_attempts = 3  # Retry up to 3 times if API keys are exhausted
    for attempt in range(retry_attempts):
        api_key, reset_day = get_available_key(service_name)
        if not api_key:
            logging.error(f"Attempt {attempt + 1}/{retry_attempts}: No available API keys for {service_name}.")
            notify_admins(f"Attempt {attempt + 1}/{retry_attempts}: All API keys for {service_name} are exhausted!")
            continue

        conn = http.client.HTTPSConnection("youtube-mp36.p.rapidapi.com")
        headers = {
            'x-rapidapi-key': api_key,
            'x-rapidapi-host': service_name
        }
        try:
            conn.request("GET", f"/dl?id={video_id}", headers=headers)
            response = conn.getresponse()
            data = response.read().decode("utf-8")
            result = json.loads(data)  # Safely parse JSON
            if result.get("error"):
                logging.error(f"Error fetching download link: {result}")
                notify_admins(f"Error fetching download link for video ID {video_id}: {result}")
                return None
            update_key_usage(service_name, api_key, reset_day)
            return result.get("linkDownload")
        except json.JSONDecodeError as e:
            logging.error(f"Error decoding JSON response: {e}")
        except Exception as e:
            logging.error(f"Error fetching YouTube download link: {e}")
            notify_admins(f"Unexpected error fetching download link for video ID {video_id}: {e}")
    logging.error(f"All attempts to fetch the download link for video ID {video_id} failed.")
    return None

def search_youtube_video(track_name, artist_name):
    """
    Search for a YouTube video and validate it.
    """
    query = f"{track_name} {artist_name} official audio"
    search_url = f"https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": query,
        "key": os.getenv("YOUTUBE_API_KEY"),
        "type": "video",
        "maxResults": 5
    }
    response = requests.get(search_url, params=params)
    response.raise_for_status()
    results = response.json().get("items", [])
    for item in results:
        title = item["snippet"]["title"].lower()
        if any(keyword in title for keyword in ["live", "karaoke", "cover", "remix", "loop"]):
            continue
        return item["id"]["videoId"]
    return None

def search_and_download_youtube_mp3(track_name, artist_name, album_name=None, duration_limit=600):
    """
    Search YouTube for the specified track and download as MP3, filtering out long videos (e.g., concerts).
    Args:
        track_name (str): Name of the track
        artist_name (str): Name of the artist
        album_name (str, optional): Name of the album
        duration_limit (int): Maximum allowed duration in seconds (default 10 minutes)
    Returns:
        str: Path to the downloaded MP3 file, or None if not found
    """
    video_id = search_youtube_video(track_name, artist_name)
    if not video_id:
        return None
    download_link = fetch_youtube_download_link(video_id)
    if download_link:
        response = requests.get(download_link)
        filename = f"{track_name} - {artist_name}.mp3"
        with open(filename, "wb") as f:
            f.write(response.content)
        return os.path.abspath(filename)
    return None

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
