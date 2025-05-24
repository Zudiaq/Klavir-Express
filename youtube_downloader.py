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
    logging.info(f"Starting download for Spotify link: {spotify_link}")

    # Locate spotdl binary
    spotdl_path = which("spotdl")
    if not spotdl_path:
        logging.error("spotdl is not installed or not in PATH.")
        return None

    # Ensure output directory exists
    output_dir = os.getcwd()
    if not os.path.exists(output_dir):
        logging.error(f"Output directory does not exist: {output_dir}")
        return None

    audio_providers = ["youtube-music", "youtube"]  # Primary and fallback providers
    output_template = os.path.join(output_dir, "{artist} - {title}")

    for provider in audio_providers:
        try:
            # Step 1: Use spotdl to download the song
            command = [
                spotdl_path,
                "download",
                spotify_link,
                "--output", f"{output_template}.mp3",
                "--audio", provider
            ]
            logging.info(f"Running command with provider '{provider}': {' '.join(command)}")
            result = subprocess.run(command, capture_output=True, text=True)

            # Log command output
            logging.debug(f"Command stdout: {result.stdout}")
            logging.debug(f"Command stderr: {result.stderr}")

            # Check for errors
            if result.returncode != 0:
                logging.error(f"Command failed with provider '{provider}': {result.stderr.strip()}")
                continue

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
        except Exception as e:
            logging.error(f"An unexpected error occurred with provider '{provider}': {e}")

    logging.error(f"All download methods failed for Spotify link: {spotify_link}. Skipping this song.")
    return None
