import os
import re
import logging
import base64
from yt_dlp import YoutubeDL

def get_youtube_cookies():
    """
    Get YouTube cookies from environment variable and decode from base64
    Returns:
        str: Path to cookies file or None if not available
    """
    cookies_b64 = os.getenv('YOUTUBE_COOKIES')
    if not cookies_b64:
        logging.info("No YouTube cookies found in environment variables")
        return None
    
    try:
        # Decode base64 cookies
        cookies_data = base64.b64decode(cookies_b64).decode('utf-8')
        
        # Write cookies to temporary file
        cookies_file = 'youtube_cookies.txt'
        with open(cookies_file, 'w', encoding='utf-8') as f:
            f.write(cookies_data)
        
        logging.info("YouTube cookies successfully decoded and saved to file")
        return cookies_file
    except Exception as e:
        logging.error(f"Error decoding YouTube cookies: {e}")
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
    query = f"{track_name} {artist_name} official audio"
    if album_name:
        query += f" {album_name}"
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
    }
    
    # Add cookies if available
    cookies_file = get_youtube_cookies()
    if cookies_file and os.path.exists(cookies_file):
        ydl_opts['cookiefile'] = cookies_file
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
    return None
