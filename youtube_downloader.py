import os
import re
import logging
import requests
from pytube import Search, YouTube
from yt_dlp import YoutubeDL

def search_and_download_youtube_mp3(track_name, artist_name, album_name=None, duration_limit=600):
    """
    Search YouTube for the specified track and download as MP3, first using pytube, then yt-dlp as fallback.
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

    # Attempt download using pytube
    try:
        logging.info(f"Searching YouTube with pytube for: {query}")
        search_results = Search(query).results
        for video in search_results:
            if video.length > duration_limit:
                continue
            title = video.title.lower()
            if track_name.lower() in title and artist_name.lower() in title:
                if re.search(r'(live|concert|cover|remix|karaoke)', title):
                    continue
                logging.info(f"Downloading video with pytube: {video.watch_url}")
                yt = YouTube(video.watch_url)
                stream = yt.streams.filter(only_audio=True).first()
                output_path = stream.download()
                mp3_path = re.sub(r'\.[^.]+$', '.mp3', output_path)
                os.rename(output_path, mp3_path)
                return mp3_path
    except Exception as e:
        logging.warning(f"pytube download failed: {e}")

    # Fallback to yt-dlp
    logging.info("Falling back to yt-dlp for download")
    cookies_path = os.getenv('COOKIES_FILE_PATH', 'cookies.txt')
    if not os.path.exists(cookies_path):
        logging.error(f"Cookies file not found at {cookies_path}. Ensure the file exists and is accessible.")
        return None

    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'default_search': 'ytsearch5',
        'outtmpl': '%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'cookiefile': cookies_path,
    }
    try:
        with YoutubeDL(ydl_opts) as ydl:
            search_results = ydl.extract_info(query, download=False)['entries']
            for entry in search_results:
                if entry is None:
                    continue
                duration = entry.get('duration')
                title = entry.get('title', '').lower()
                if duration and duration > duration_limit:
                    continue
                if track_name.lower() in title and artist_name.lower() in title:
                    if re.search(r'(live|concert|cover|remix|karaoke)', title):
                        continue
                    info = ydl.extract_info(entry['webpage_url'], download=True)
                    filename = ydl.prepare_filename(info)
                    mp3_path = re.sub(r'\.[^.]+$', '.mp3', filename)
                    if os.path.exists(mp3_path):
                        return mp3_path
    except Exception as e:
        logging.error(f"yt-dlp download failed: {e}")
    return None

def trigger_refresh_cookies_workflow():
    """
    Trigger the workflow in the private repository to refresh cookies.
    """
    github_token = os.getenv('GITHUB_TOKEN')  # GitHub token for authentication
    if not github_token:
        logging.error("GITHUB_TOKEN is not set in environment variables.")
        return
    repo = "Zudiaq/Cookies"  # Replace with the private repo name
    workflow = "refresh_cookies.yml"  # Replace with the workflow filename in the private repo
    url = f"https://api.github.com/repos/{repo}/actions/workflows/{workflow}/dispatches"
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    payload = {"ref": "main"}  # Replace 'main' with the branch name if different
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        logging.info("Successfully triggered the refresh cookies workflow.")
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to trigger the refresh cookies workflow: {e}")
