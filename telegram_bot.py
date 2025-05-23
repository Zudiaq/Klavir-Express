import mutagen
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB
from youtube_downloader import record_youtube_stream
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
    Records the MP3 from YouTube, embeds metadata and cover, and sends the MP3 file.
    Args:
        track_name (str): Name of the track.
        artist_name (str): Name of the artist.
        album_name (str, optional): Name of the album.
        album_image (str, optional): URL of the album cover image.
        preview_url (str, optional): URL of the track preview.
        mood (str, optional): Mood associated with the recommendation.
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
    message = f"\U0001F3B5 <b>{track_name}</b>\n"
    message += f"\U0001F464 {artist_name}\n"
    if album_name:
        message += f"\U0001F4BF {album_name}\n"
    mp3_path = record_youtube_stream(track_name, artist_name, album_name)
    if mp3_path and os.path.exists(mp3_path):
        try:
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
    if preview_url:
        try:
            logging.debug(f"Downloading preview from {preview_url}")
            preview_response = requests.get(preview_url, stream=True)
            preview_response.raise_for_status()
            temp_path = "temp_preview.mp3"
            with open(temp_path, 'wb') as f:
                for chunk in preview_response.iter_content(chunk_size=8192):
                    f.write(chunk)
            result = send_audio_with_caption(temp_path, message)
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return None
        except requests.exceptions.RequestException as e:
            logging.error(f"Error downloading preview: {e}")
    return None

from google_translate import translate_to_persian
