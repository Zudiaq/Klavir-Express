import mutagen
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB
from youtube_downloader import search_youtube_video, fetch_youtube_download_link
import requests
import os
import logging
from dotenv import load_dotenv
from config import DEBUG_MODE, ENABLE_TELEGRAM

load_dotenv()

logging.basicConfig(
    level=logging.DEBUG if DEBUG_MODE else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def send_message(message):
    """
    Send a text message to the configured Telegram chat.
    Args:
        message (str): The message text to send.
    Returns:
        dict: Telegram API response or None if error.
    """
    if not ENABLE_TELEGRAM:
        logging.info("Telegram messaging is disabled in config")
        return None
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    if not token or not chat_id:
        logging.error("Telegram credentials are not set in environment variables")
        return None
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    payload = {'chat_id': chat_id, 'text': message, 'parse_mode': 'HTML'}
    try:
        logging.debug(f"Sending message to Telegram chat {chat_id}")
        response = requests.post(url, json=payload)
        response.raise_for_status()
        logging.debug("Message sent successfully")
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending message: {e}")
        return None

def send_audio_with_caption(audio_path, caption):
    """
    Send an audio file with caption to the configured Telegram chat.
    Args:
        audio_path (str): Path to the audio file.
        caption (str): Caption text for the audio.
    Returns:
        dict: Telegram API response or None if error.
    """
    if not ENABLE_TELEGRAM:
        logging.info("Telegram messaging is disabled in config")
        return None
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    if not token or not chat_id:
        logging.error("Telegram credentials are not set in environment variables")
        return None
    url = f'https://api.telegram.org/bot{token}/sendAudio'
    try:
        with open(audio_path, 'rb') as audio_file:
            files = {'audio': audio_file}
            data = {'chat_id': chat_id, 'caption': caption, 'parse_mode': 'HTML'}
            logging.debug(f"Sending audio to Telegram chat {chat_id}")
            response = requests.post(url, files=files, data=data)
            response.raise_for_status()
            logging.debug("Audio sent successfully")
            return response.json()
    except FileNotFoundError:
        logging.error(f"Audio file not found: {audio_path}")
        return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending audio: {e}")
        return None

def send_music_recommendation(track_name, artist_name, album_name=None, album_image=None, preview_url=None, mood=None):
    """
    Send a music recommendation to Telegram with available metadata.
    Downloads the MP3 from YouTube, embeds metadata and cover, and sends the MP3 file.
    """
    if not ENABLE_TELEGRAM:
        logging.info("Telegram messaging is disabled in config")
        return None

    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    if not token or not chat_id:
        logging.error("Telegram credentials are not set in environment variables")
        return None

    message = f"\U0001F3B5 <b>{track_name}</b>\n"
    message += f"\U0001F464 {artist_name}\n"
    if album_name:
        message += f"\U0001F4BF {album_name}\n"

    # Search and download MP3 from YouTube
    mp3_path = search_and_download_youtube_mp3(track_name, artist_name, album_name)
    if mp3_path and os.path.exists(mp3_path):
        try:
            # Embed metadata
            audio = MP3(mp3_path, ID3=ID3)
            try:
                audio.add_tags()
            except Exception:
                pass
            audio.tags.add(TIT2(encoding=3, text=track_name))
            audio.tags.add(TPE1(encoding=3, text=artist_name))
            if album_name:
                audio.tags.add(TALB(encoding=3, text=album_name))
            if album_image:
                img_data = requests.get(album_image).content
                audio.tags.add(APIC(
                    encoding=3,
                    mime='image/jpeg',
                    type=3,
                    desc='Cover',
                    data=img_data
                ))
            audio.save()

            # Send MP3 to Telegram
            url = f'https://api.telegram.org/bot{token}/sendAudio'
            with open(mp3_path, 'rb') as audio_file:
                files = {'audio': audio_file}
                data = {'chat_id': chat_id, 'caption': message, 'parse_mode': 'HTML'}
                logging.debug(f"Sending MP3 to Telegram chat {chat_id}")
                response = requests.post(url, files=files, data=data)
                response.raise_for_status()
                logging.debug("MP3 sent successfully")
                os.remove(mp3_path)
                return response.json()
        except Exception as e:
            logging.error(f"Error sending MP3: {e}")
            if os.path.exists(mp3_path):
                os.remove(mp3_path)
    else:
        logging.error("Failed to download MP3 from YouTube.")

    # Fallback: Send preview URL if available
    if preview_url:
        try:
            logging.debug(f"Sending preview URL: {preview_url}")
            result = send_message(f"{message}\n<a href='{preview_url}'>Preview</a>")
            return result
        except Exception as e:
            logging.error(f"Error sending preview URL: {e}")

    return None

from google_translate import translate_to_persian

def search_and_download_youtube_mp3(track_name, artist_name, album_name=None):
    """
    Search YouTube for the track and download the audio as MP3.
    Returns the path to the downloaded MP3 file or None if failed.
    """
    try:
        # Search for the video
        query = f"{track_name} {artist_name}"
        if album_name:
            query += f" {album_name}"
        video_url = search_youtube_video(query)
        if not video_url:
            logging.error("No YouTube video found for the query")
            return None
        # Get the download link
        mp3_url = fetch_youtube_download_link(video_url)
        if not mp3_url:
            logging.error("Failed to fetch YouTube MP3 download link")
            return None
        # Download the MP3 file
        response = requests.get(mp3_url, stream=True)
        if response.status_code == 200:
            file_name = f"{track_name}_{artist_name}.mp3".replace(" ", "_")
            with open(file_name, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            return file_name
        else:
            logging.error("Failed to download MP3 file")
            return None
    except Exception as e:
        logging.error(f"Error in search_and_download_youtube_mp3: {e}")
        return None

def notify_admins(message):
    """
    Notify admins via Telegram when an issue occurs.
    """
    admin_chat_ids = os.getenv('ADMIN_CHAT_ID', '')
    if not admin_chat_ids:
        logging.error("ADMIN_CHAT_ID is not set in environment variables")
        return
    admin_ids = admin_chat_ids.split(",")
    for admin_id in admin_ids:
        payload = {'chat_id': admin_id.strip(), 'text': message, 'parse_mode': 'HTML'}
        try:
            response = requests.post(f'https://api.telegram.org/bot{os.getenv("TELEGRAM_BOT_TOKEN")}/sendMessage', json=payload)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to notify admin {admin_id}: {e}")
