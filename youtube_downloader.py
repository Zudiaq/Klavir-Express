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

# Define the usage limit for API keys (can be adjusted by the developer)
API_USAGE_LIMIT = 300
CLOUD_API_USAGE_LIMIT = 150
CLOUD_API_KEYS_FILE = "cloud-api-hub-youtube-downloader.yaml"

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
    
    The function implements two key mechanisms:
    1. Usage limit: If a key's usage reaches API_USAGE_LIMIT, it won't be updated further
    2. Monthly reset: Each key has a designated reset_day in the month. When the current day
       matches this reset_day, the usage is reset to 1 (counting the current usage), but only
       if the key hasn't already been reset today (checked via last_reset date)
    """
    if not os.path.exists(YAML_KEYS_FILE):
        logging.error(f"YAML keys file not found: {YAML_KEYS_FILE}")
        return

    try:
        with open(YAML_KEYS_FILE, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        keys = data.get(f"{service_name} keys", [])
        today = datetime.now().day
        today_date = str(datetime.now().date())
        
        for entry in keys:
            if entry["key"] == key:
                # Ensure we only update keys that are below the usage limit
                if entry["usage"] < API_USAGE_LIMIT:
                    # Check if today is the reset day for this key
                    if today == entry["reset_day"]:
                        # Check if the key has already been reset today
                        if entry.get("last_reset") != today_date:
                            # Reset usage to 1 (counting the current usage)
                            entry["usage"] = 1
                            entry["last_reset"] = today_date
                            logging.info(f"Usage reset for key: {key} on reset day {reset_day}")
                        else:
                            # Key already reset today, just increment usage
                            entry["usage"] += 1
                            logging.info(f"Key {key} already reset today. Incremented usage to {entry['usage']}")
                    else:
                        # Not reset day, just increment usage
                        entry["usage"] += 1
                        logging.info(f"Incremented usage for key: {key} to {entry['usage']}")
                else:
                    logging.warning(f"Key {key} has reached the usage limit ({API_USAGE_LIMIT}) and will not be updated.")
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
    Skips keys that have reached the usage limit.
    """
    keys = load_service_keys(service_name)
    for entry in keys:
        if entry["usage"] < API_USAGE_LIMIT:  # Check against the usage limit
            logging.info(f"Using API key: {entry['key']} with usage: {entry['usage']}")
            return entry["key"], entry["reset_day"]
        else:
            logging.info(f"Skipping API key: {entry['key']} with usage: {entry['usage']} (limit reached)")
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

        # Update usage only after successful request
        update_key_usage(service_name, api_key, reset_day)

        return download_link
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON response: {e}")
    except Exception as e:
        logging.error(f"Error fetching YouTube download link: {e}")
        notify_admins(f"Unexpected error fetching download link for video ID {video_id}: {e}")
    return None


def pull_cloud_api_keys():
    """
    Pull the YAML file containing Cloud API Hub keys from the private GitHub repository.
    """
    url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/{CLOUD_API_KEYS_FILE}"
    headers = {"Authorization": f"token {GH_PAT}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    with open(CLOUD_API_KEYS_FILE, "w", encoding="utf-8") as f:
        f.write(response.text)

def load_cloud_api_keys():
    """
    Load Cloud API Hub keys from the YAML file.
    """
    if not os.path.exists(CLOUD_API_KEYS_FILE):
        logging.info(f"Cloud API keys file not found. Pulling keys from GitHub.")
        pull_cloud_api_keys()
    try:
        with open(CLOUD_API_KEYS_FILE, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data.get("cloud-api-hub-youtube-downloader keys", [])
    except yaml.YAMLError as e:
        logging.error(f"Error parsing Cloud API YAML file: {e}")
        return []
    except Exception as e:
        logging.error(f"Unexpected error loading Cloud API keys: {e}")
        return []

def push_cloud_api_keys():
    """
    Push the updated Cloud API YAML file back to the private GitHub repository.
    """
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{CLOUD_API_KEYS_FILE}"
    headers = {
        "Authorization": f"token {GH_PAT}",
        "Content-Type": "application/json"
    }
    try:
        with open(CLOUD_API_KEYS_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        sha = response.json().get("sha", "")
        encoded_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")
        payload = {
            "message": "Update Cloud API keys file",
            "content": encoded_content,
            "sha": sha
        }
        response = requests.put(url, headers=headers, json=payload)
        response.raise_for_status()
        logging.info("Successfully pushed Cloud API keys file to GitHub.")
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to push Cloud API keys file: {e}")

def update_cloud_api_key_usage(key, reset_day):
    """
    Update the usage count of a Cloud API key and handle monthly reset logic.
    """
    if not os.path.exists(CLOUD_API_KEYS_FILE):
        logging.error(f"Cloud API keys file not found: {CLOUD_API_KEYS_FILE}")
        return
    try:
        with open(CLOUD_API_KEYS_FILE, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        keys = data.get("cloud-api-hub-youtube-downloader keys", [])
        today = datetime.now().day
        today_date = str(datetime.now().date())
        for entry in keys:
            if entry["key"] == key:
                if entry["usage"] < CLOUD_API_USAGE_LIMIT:
                    if today == entry["reset_day"]:
                        if entry.get("last_reset") != today_date:
                            entry["usage"] = 1
                            entry["last_reset"] = today_date
                            logging.info(f"Cloud API usage reset for key: {key} on reset day {reset_day}")
                        else:
                            entry["usage"] += 1
                            logging.info(f"Cloud API key {key} already reset today. Incremented usage to {entry['usage']}")
                    else:
                        entry["usage"] += 1
                        logging.info(f"Incremented Cloud API usage for key: {key} to {entry['usage']}")
                else:
                    logging.warning(f"Cloud API key {key} has reached the usage limit ({CLOUD_API_USAGE_LIMIT}) and will not be updated.")
                break
        else:
            logging.warning(f"Cloud API key {key} not found in the YAML file.")
        with open(CLOUD_API_KEYS_FILE, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f)
        push_cloud_api_keys()
        logging.info(f"Updated usage for Cloud API key: {key}")
    except yaml.YAMLError as e:
        logging.error(f"Error parsing Cloud API YAML file: {e}")
    except Exception as e:
        logging.error(f"Unexpected error updating Cloud API key usage: {e}")

def get_available_cloud_api_key():
    """
    Get the first available Cloud API key under the usage limit.
    """
    keys = load_cloud_api_keys()
    for entry in keys:
        if entry["usage"] < CLOUD_API_USAGE_LIMIT:
            logging.info(f"Using Cloud API key: {entry['key']} with usage: {entry['usage']}")
            return entry["key"], entry["reset_day"]
        else:
            logging.info(f"Skipping Cloud API key: {entry['key']} with usage: {entry['usage']} (limit reached)")
    notify_admins(f"All Cloud API keys are exhausted!")
    return None, None

def fetch_cloud_api_hub_download_link(video_id):
    """
    Fetch the MP3 download link using the new Cloud API Hub service.
    """
    service_name = "cloud-api-hub-youtube-downloader.p.rapidapi.com"
    api_key, reset_day = get_available_cloud_api_key()
    if not api_key:
        logging.error(f"No available Cloud API keys.")
        return None
    conn = http.client.HTTPSConnection("cloud-api-hub-youtube-downloader.p.rapidapi.com")
    headers = {
        'x-rapidapi-key': api_key,
        'x-rapidapi-host': service_name
    }
    try:
        logging.info(f"Sending request to fetch MP3 download link for video ID {video_id} using Cloud API Hub.")
        conn.request("GET", f"/mux?id={video_id}&quality=max&codec=h264&audioFormat=mp3&language=en&audioOnly=true", headers=headers)
        response = conn.getresponse()
        data = response.read().decode("utf-8")
        result = json.loads(data)
        if result.get("status") != "tunnel":
            logging.error(f"Error in Cloud API response: {result}")
            notify_admins(f"Error fetching download link for video ID {video_id} using Cloud API Hub: {result}")
            return None
        download_link = result.get("url")
        if not download_link:
            logging.error(f"No download link found in the Cloud API response for video ID {video_id}. Full response: {result}")
            return None
        logging.info(f"Download link fetched successfully for video ID {video_id} using Cloud API Hub: {download_link}")
        update_cloud_api_key_usage(api_key, reset_day)
        return download_link
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding Cloud API JSON response: {e}")
    except Exception as e:
        logging.error(f"Error fetching download link using Cloud API Hub: {e}")
        notify_admins(f"Unexpected error fetching download link for video ID {video_id} using Cloud API Hub: {e}")
    finally:
        update_cloud_api_key_usage(api_key, reset_day)
    return None


async def search_and_download_youtube_mp3(track_name, artist_name, album_name=None):
    """
    Search YouTube for the track and download the audio as MP3.
    Retry up to 3 times if the initial attempt fails.
    Returns the path to the downloaded MP3 file or None if failed.
    """
    max_retries = 3
    timeout_errors = 0
    for attempt in range(max_retries):
        try:
            # Increment API usage only for YouTube API requests
            # increment_api_usage()  # If you have this function, otherwise remove
            # Search for the video
            query = f"{track_name} {artist_name}"
            if album_name:
                query += f" {album_name}"
            video_url = search_youtube_video(query, artist_name)
            if not video_url:
                logging.error(f"No YouTube video found for the query (Attempt {attempt + 1}/{max_retries})")
                continue
            # Try the old API first
            mp3_url = fetch_youtube_download_link(video_url)
            if not mp3_url:
                # Check for timeout error in logs (simulate by catching specific error if possible)
                last_log = logging.getLogger().handlers[0].stream.getvalue() if hasattr(logging.getLogger().handlers[0].stream, 'getvalue') else ""
                if "timed out" in last_log or timeout_errors > 0:
                    timeout_errors += 1
                if timeout_errors >= 2:
                    logging.warning(f"Timeout error occurred twice. Switching to Cloud API Hub.")
                    mp3_url = fetch_cloud_api_hub_download_link(video_url)
                    if not mp3_url:
                        logging.error(f"Failed to fetch MP3 download link using Cloud API Hub (Attempt {attempt + 1}/{max_retries})")
                        continue
            if not mp3_url:
                logging.error(f"Failed to fetch YouTube MP3 download link (Attempt {attempt + 1}/{max_retries})")
                continue
            response = requests.get(mp3_url, stream=True)
            if response.status_code == 200:
                file_name = f"{track_name}_{artist_name}.mp3".replace(" ", "_")
                with open(file_name, 'wb') as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)
                return file_name
            else:
                logging.error(f"Failed to download MP3 file (Attempt {attempt + 1}/{max_retries})")
                continue
        except Exception as e:
            if "timed out" in str(e):
                timeout_errors += 1
            logging.error(f"Error in search_and_download_youtube_mp3 (Attempt {attempt + 1}/{max_retries}): {e}")
            if timeout_errors >= 2:
                logging.warning(f"Timeout error occurred twice. Switching to Cloud API Hub.")
                mp3_url = fetch_cloud_api_hub_download_link(video_url)
                if mp3_url:
                    response = requests.get(mp3_url, stream=True)
                    if response.status_code == 200:
                        file_name = f"{track_name}_{artist_name}.mp3".replace(" ", "_")
                        with open(file_name, 'wb') as f:
                            for chunk in response.iter_content(1024):
                                f.write(chunk)
                        return file_name
    logging.error("All attempts to fetch YouTube MP3 download link failed.")
    return None

def search_youtube_video(query, artist_name):
    """
    Search for a YouTube video and validate it.
    Retries with alternative queries if the initial search fails.
    """
    search_url = f"https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "key": os.getenv("YOUTUBE_API_KEY"),
        "type": "video",
        "maxResults": 5
    }
    alternative_queries = [
        query,
        f"{artist_name} {query.split()[0]}",  # Artist name + first word of the query
        artist_name  # Only the artist name
    ]

    for alt_query in alternative_queries:
        params["q"] = alt_query
        try:
            logging.info(f"Searching YouTube for query: {alt_query}")
            response = requests.get(search_url, params=params)
            response.raise_for_status()
            results = response.json().get("items", [])
            logging.debug(f"Search results for query '{alt_query}': {results}")

            for item in results:
                title = item["snippet"]["title"].lower()
                video_id = item["id"]["videoId"]
                logging.debug(f"Checking video: {title} (ID: {video_id})")
                if artist_name.lower() in title and not any(
                    keyword in title for keyword in ["live", "karaoke", "cover", "remix", "loop"]
                ):
                    logging.info(f"Found matching video: {title} (ID: {video_id})")
                    return video_id

            logging.warning(f"No suitable video found for query: {alt_query}")
        except requests.exceptions.RequestException as e:
            logging.error(f"Error during YouTube search for query '{alt_query}': {e}")
        except Exception as e:
            logging.error(f"Unexpected error during YouTube search for query '{alt_query}': {e}")

    # Notify admins only if all alternative queries fail
    logging.error("All alternative queries failed.")
    notify_admins("⚠️ No suitable YouTube video found for the given queries.")
    return None
