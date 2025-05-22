import os
import re
import logging
from yt_dlp import YoutubeDL

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
    query = f"{track_name} {artist_name} official audio"
    if album_name:
        query += f" {album_name}"
    cookies_path = os.getenv('COOKIES_FILE_PATH', 'cookies.txt')  
    if not os.path.exists(cookies_path):
        logging.error(f"Cookies file not found at {cookies_path}. Ensure the file exists and is accessible.")
        return None
    logging.info(f"Using cookies file at {cookies_path}")
    try:
        with open(cookies_path, 'r') as f:
            logging.debug(f"Cookies file contents:\n{f.read()}")
    except Exception as e:
        logging.error(f"Failed to read cookies file: {e}")
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
        'extract_flat': False,
        'nocheckcertificate': True,
        'cookies': cookies_path,  
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
                # Require both track and artist name in title, avoid live/concert/cover/remix/karaoke
                if track_name.lower() in title and artist_name.lower() in title:
                    if re.search(r'(live|concert|cover|remix|karaoke)', title):
                        continue
                    info = ydl.extract_info(entry['webpage_url'], download=True)
                    filename = ydl.prepare_filename(info)
                    mp3_path = re.sub(r'\.[^.]+$', '.mp3', filename)
                    if os.path.exists(mp3_path):
                        return mp3_path
            # If no strict match, try the first short enough result
            for entry in search_results:
                if entry is None:
                    continue
                duration = entry.get('duration')
                if duration and duration > duration_limit:
                    continue
                info = ydl.extract_info(entry['webpage_url'], download=True)
                filename = ydl.prepare_filename(info)
                mp3_path = re.sub(r'\.[^.]+$', '.mp3', filename)
                if os.path.exists(mp3_path):
                    return mp3_path
    except Exception as e:
        logging.error(f"YouTube download failed: {e}")
    finally:
        if os.path.exists(cookies_path):
            os.remove(cookies_path)  # Delete cookies file after use
    return None
