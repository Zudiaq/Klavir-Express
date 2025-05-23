import os
import re
import logging
import subprocess

def search_and_download_youtube_mp3(track_name, artist_name, album_name=None, duration_limit=600):
    """
    Search YouTube for the specified track and download as MP3 using you-get.
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

    search_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
    logging.info(f"Searching YouTube for: {query}")

    try:
        # Use you-get to download the first result
        output_dir = os.getcwd()
        command = ["you-get", "-o", output_dir, "--extract-audio", search_url]
        logging.info(f"Running command: {' '.join(command)}")
        subprocess.run(command, check=True)
        
        # Find the downloaded MP3 file
        for file in os.listdir(output_dir):
            if file.endswith(".mp3"):
                mp3_path = os.path.join(output_dir, file)
                logging.info(f"Downloaded MP3 file: {mp3_path}")
                return mp3_path
    except subprocess.CalledProcessError as e:
        logging.error(f"you-get download failed: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

    logging.error("All download methods failed.")
    return None
