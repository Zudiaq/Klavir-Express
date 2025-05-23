import os
import re
import logging
import subprocess

def search_and_download_youtube_mp3(track_name, artist_name, album_name=None, duration_limit=600):
    """
    Search YouTube for the specified track and download as MP3 using you-get and ffmpeg.
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
        command = ["you-get", "-o", output_dir, search_url]
        logging.info(f"Running command: {' '.join(command)}")
        subprocess.run(command, check=True)

        # Find the downloaded file (assume it's the most recent file in the directory)
        downloaded_files = sorted(
            [os.path.join(output_dir, f) for f in os.listdir(output_dir)],
            key=os.path.getmtime,
            reverse=True
        )
        video_path = next((f for f in downloaded_files if f.endswith(('.mp4', '.webm', '.mkv'))), None)
        if not video_path:
            logging.error("No video file found after download.")
            return None

        # Convert the video to MP3 using ffmpeg
        mp3_path = re.sub(r'\.[^.]+$', '.mp3', video_path)
        command = ["ffmpeg", "-i", video_path, "-q:a", "0", "-map", "a", mp3_path]
        logging.info(f"Converting video to MP3: {' '.join(command)}")
        subprocess.run(command, check=True)

        # Remove the original video file
        os.remove(video_path)
        logging.info(f"Downloaded MP3 file: {mp3_path}")
        return mp3_path
    except subprocess.CalledProcessError as e:
        logging.error(f"Command failed: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

    logging.error("All download methods failed.")
    return None
