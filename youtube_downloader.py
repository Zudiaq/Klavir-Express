import os
import logging
import subprocess
import json

def record_youtube_stream(track_name, artist_name, album_name=None, duration_limit=600):
    """
    Record a YouTube livestream or video stream directly as MP3 using yt-dlp and ffmpeg.
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
        # Step 1: Use yt-dlp to search for the video and get the audio stream URL
        command = [
            "yt-dlp",
            f"ytsearch:{query}",
            "--print-json",
            "--quiet",
            "--format", "bestaudio"
        ]
        logging.info(f"Running command: {' '.join(command)}")
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        output = result.stdout.strip()
        if not output:
            logging.error("No output from yt-dlp.")
            return None

        # Parse the JSON output to extract the stream URL
        try:
            video_data = json.loads(output.splitlines()[0])  # Take the first result
            stream_url = video_data.get("url")
            if not stream_url:
                logging.error("No stream URL found in yt-dlp output.")
                return None
            logging.info(f"Found audio stream URL: {stream_url}")
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse yt-dlp output: {e}")
            return None

        # Step 2: Record the stream using ffmpeg
        output_dir = os.getcwd()
        mp3_path = os.path.join(output_dir, f"{track_name} - {artist_name}.mp3")
        command = [
            "ffmpeg",
            "-i", stream_url,
            "-c", "copy",
            "-t", str(duration_limit),
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
        logging.error(f"Command failed: {e}")
        logging.error(f"Command output: {e.stderr}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

    logging.error("All recording methods failed.")
    return None
