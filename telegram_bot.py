import requests
import os
import logging
from mutagen.mp3 import MP3, ID3, APIC, TIT2, TPE1, TALB
from config import DEBUG_MODE, ENABLE_TELEGRAM

logging.basicConfig(
    level=logging.DEBUG if DEBUG_MODE else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def send_audio_with_caption(audio_path, caption, metadata=None):
    """
    Send an audio file with caption to Telegram, embedding metadata if provided.
    Args:
        audio_path (str): Path to the audio file.
        caption (str): Caption text to send.
        metadata (dict, optional): Metadata for the audio file (e.g., track_name, artist_name, album_name, album_image).
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

    # Embed metadata into MP3 file
    if metadata:
        try:
            audio = MP3(audio_path, ID3=ID3)
            try:
                audio.add_tags()
            except Exception:
                pass
            audio.tags.add(TIT2(encoding=3, text=metadata.get('track_name', '')))
            audio.tags.add(TPE1(encoding=3, text=metadata.get('artist_name', '')))
            if metadata.get('album_name'):
                audio.tags.add(TALB(encoding=3, text=metadata['album_name']))
            if metadata.get('album_image'):
                img_data = requests.get(metadata['album_image']).content
                audio.tags.add(APIC(
                    encoding=3,
                    mime='image/jpeg',
                    type=3,
                    desc='Cover',
                    data=img_data
                ))
            audio.save()
            logging.info("Metadata embedded successfully into MP3 file.")
        except Exception as e:
            logging.error(f"Error embedding metadata: {e}")

    # Send audio file to Telegram
    url = f'https://api.telegram.org/bot{token}/sendAudio'
    try:
        with open(audio_path, 'rb') as audio_file:
            files = {'audio': audio_file}
            data = {'chat_id': chat_id, 'caption': caption, 'parse_mode': 'HTML'}
            logging.debug(f"Sending audio to Telegram chat {chat_id}")
            response = requests.post(url, files=files, data=data)
            response.raise_for_status()
            logging.info("Audio sent successfully to Telegram.")
            return response.json()
    except FileNotFoundError:
        logging.error(f"Audio file not found: {audio_path}")
        return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending audio: {e}")
        return None
