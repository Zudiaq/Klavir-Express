import os
import logging
import subprocess
from shutil import which

def download_song_with_spotdl(track_name, artist_name, album_name=None):
    """
    Download a song directly from Spotify using spotdl.
    Args:
        track_name (str): Name of the track
        artist_name (str): Name of the artist
        album_name (str, optional): Name of the album
    Returns:
        str: Path to the downloaded MP3 file, or None if not found
    """
    query = f"{track_name} {artist_name}"
    if album_name:
        query += f" {album_name}"

    # Filter out unwanted versions (live, karaoke, remix, etc.)
    query += " -live -karaoke -remix -cover"

    logging.info(f"Searching Spotify for: {query}")

    # Locate spotdl binary
    spotdl_path = which("spotdl")
    if not spotdl_path:
        logging.error("spotdl is not installed or not in PATH.")
        return None

    try:
        # Step 1: Use spotdl to download the song
        output_dir = os.getcwd()
        command = [
            spotdl_path,
            "download",
            "--output", output_dir,
            "--format", "mp3",
            query
        ]
        logging.info(f"Running command: {' '.join(command)}")
        subprocess.run(command, check=True)

        # Step 2: Find the downloaded MP3 file
        downloaded_files = [
            os.path.join(output_dir, f) for f in os.listdir(output_dir)
            if f.endswith(".mp3") and track_name.lower() in f.lower() and artist_name.lower() in f.lower()
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
