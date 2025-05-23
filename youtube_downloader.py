import os
import logging
import subprocess
from shutil import which

def record_youtube_stream(track_name, artist_name, album_name=None, duration_limit=600):
    """
    Record a YouTube livestream or video stream directly as MP3 using youtube-dl-exec.
    Args:
        track_name (str): Name of the track
        artist_name (str): Name of the artist
        album_name (str, optional): Name of the album
        duration_limit (int): Maximum allowed duration in seconds (default 10 minutes)
    Returns:
        str: Path to the recorded MP3 file, or None if not found
    """
    query = f"{track_name} {artist_name} official audio"
    if album_name:
        query += f" {album_name}"

    logging.info(f"Searching YouTube for: {query}")

    # Locate youtube-dl-exec binary
    youtube_dl_exec_path = which("youtube-dl-exec")
    if not youtube_dl_exec_path:
        logging.error("youtube-dl-exec is not installed or not in PATH.")
        return None

    try:
        # Step 1: Use youtube-dl-exec to search and download the audio stream
        output_dir = os.getcwd()
        mp3_path = os.path.join(output_dir, f"{track_name} - {artist_name}.mp3")
        command = [
            youtube_dl_exec_path,
            f"ytsearch:{query}",
            "--extract-audio",
            "--audio-format", "mp3",
            "--audio-quality", "192K",
            "-o", mp3_path
        ]
        logging.info(f"Running command: {' '.join(command)}")
        subprocess.run(command, check=True)

        if os.path.exists(mp3_path):
            logging.info(f"Recorded MP3 file: {mp3_path}")
            return mp3_path
        else:
            logging.error("MP3 file not found after recording.")
            return None
    except subprocess.CalledProcessError as e:
        logging.error(f"Command failed: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

    logging.error("All recording methods failed.")
    return None
