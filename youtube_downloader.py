import os
import re
import logging
import requests
from yt_dlp import YoutubeDL
from dotenv import load_dotenv

load_dotenv()

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
    
    # Get YouTube credentials from environment variables
    youtube_username = os.getenv('YOUTUBE_USERNAME')
    youtube_password = os.getenv('YOUTUBE_PASSWORD')
    
    if not youtube_username or not youtube_password:
        logging.error("YouTube credentials are not set in environment variables. Set YOUTUBE_USERNAME and YOUTUBE_PASSWORD.")
        return None
        
    logging.info(f"Using YouTube account authentication for {youtube_username}")
    
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
        'username': youtube_username,
        'password': youtube_password,
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
        if "authentication failed" in str(e).lower() or "login failed" in str(e).lower():
            logging.error("YouTube authentication failed. Please check your username and password.")
        else:
            logging.error(f"YouTube download failed: {e}")
    return None


