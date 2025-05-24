import os
import logging
import subprocess
from shutil import which
import re

def sanitize_query(query):
    """
    Sanitize the query to remove or escape problematic characters.
    Args:
        query (str): The query string to sanitize.
    Returns:
        str: Sanitized query string.
    """
    # Remove problematic characters like slashes, colons, and excessive whitespace
    query = re.sub(r"[\/\\:]", " ", query)
    query = re.sub(r"\s+", " ", query).strip()
    return query

def download_song_with_spotdl(spotify_link):
    """
    Download a song directly from Spotify using spotdl.
    Args:
        spotify_link (str): Spotify track link.
    Returns:
        str: Path to the downloaded MP3 file, or None if not found.
    """
    logging.info(f"Downloading song from Spotify link: {spotify_link}")

    # Locate spotdl binary
    spotdl_path = which("spotdl")
    if not spotdl_path:
        logging.error("spotdl is not installed or not in PATH.")
        return None

    try:
        # Step 1: Use spotdl to download the song
        output_dir = os.getcwd()
        output_template = os.path.join(output_dir, "{artist} - {title}")
        command = [
            spotdl_path,
            "download",
            spotify_link,
            "--output", f"{output_template}.mp3"
        ]
        logging.info(f"Running command: {' '.join(command)}")
        subprocess.run(command, check=True)

        # Step 2: Find the downloaded MP3 file
        downloaded_files = [
            os.path.join(output_dir, f) for f in os.listdir(output_dir)
            if f.endswith(".mp3")
        ]
        if downloaded_files:
            mp3_path = downloaded_files[0]
            logging.info(f"Downloaded MP3 file: {mp3_path}")
            return mp3_path
        else:
            logging.error("MP3 file not found after downloading.")
            return None
    except subprocess.CalledProcessError as e:
        logging.error(f"Command failed: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

    logging.error("All download methods failed.")
    return None
