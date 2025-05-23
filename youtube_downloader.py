import os
import re
import logging
import requests

def search_and_download_youtube_mp3(track_name, artist_name, album_name=None, duration_limit=600):
    """
    Search YouTube for the specified track and download as MP3 using y2mate.
    Args:
        track_name (str): Name of the track
        artist_name (str): Name of the artist
        album_name (str, optional): Name of the album
        duration_limit (int): Maximum allowed duration in seconds (default 10 minutes)
    Returns:
        str: Path to the downloaded MP3 file, or None if not found
    """
    query = f"{track_name} {artist_name} official audio"
    if album_name:
        query += f" {album_name}"

    logging.info(f"Searching YouTube for: {query}")

    try:
        # Step 1: Search YouTube for the video
        search_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
        response = requests.get(search_url)
        response.raise_for_status()
        video_id = re.search(r"watch\?v=([\w-]+)", response.text)
        if not video_id:
            logging.error("No video found for the given query.")
            return None
        video_url = f"https://www.youtube.com/watch?v={video_id.group(1)}"
        logging.info(f"Found video: {video_url}")

        # Step 2: Use y2mate API to download the MP3
        y2mate_api_url = "https://api.y2mate.com/api/v1/convert"
        payload = {
            "url": video_url,
            "format": "mp3",
            "quality": "128kbps"
        }
        logging.info(f"Requesting MP3 conversion from y2mate for: {video_url}")
        response = requests.post(y2mate_api_url, json=payload)
        response.raise_for_status()
        data = response.json()

        if data.get("status") != "success" or "download_url" not in data:
            logging.error("Failed to convert video to MP3 using y2mate.")
            return None

        download_url = data["download_url"]
        output_dir = os.getcwd()
        mp3_path = os.path.join(output_dir, f"{track_name} - {artist_name}.mp3")
        logging.info(f"Downloading MP3 from: {download_url}")
        with requests.get(download_url, stream=True) as r:
            r.raise_for_status()
            with open(mp3_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        logging.info(f"Downloaded MP3 file: {mp3_path}")
        return mp3_path
    except requests.exceptions.RequestException as e:
        logging.error(f"Error during MP3 download: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

    logging.error("All download methods failed.")
    return None
