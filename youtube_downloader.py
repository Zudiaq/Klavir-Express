import os
import re
import logging
import subprocess

def record_youtube_stream(track_name, artist_name, album_name=None, duration_limit=600):
    """
    Record a YouTube livestream or video stream directly as MP3 using ffmpeg.
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

    try:
        # Step 1: Search YouTube for the video
        search_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
        response = subprocess.run(
            ["youtube-dl", "--get-url", search_url],
            capture_output=True,
            text=True,
            check=True
        )
        stream_url = response.stdout.strip().split("\n")[0]
        if not stream_url:
            logging.error("No stream URL found for the given query.")
            return None
        logging.info(f"Found stream URL: {stream_url}")

        # Step 2: Record the stream using ffmpeg
        output_dir = os.getcwd()
        mp3_path = os.path.join(output_dir, f"{track_name} - {artist_name}.mp3")
        command = [
            "ffmpeg",
            "-i", stream_url,
            "-t", str(duration_limit),
            "-q:a", "0",
            "-map", "a",
            mp3_path
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
        logging.error(f"ffmpeg command failed: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

    logging.error("All recording methods failed.")
    return None
