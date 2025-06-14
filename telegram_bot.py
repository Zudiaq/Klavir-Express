import mutagen
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB
from youtube_downloader import search_youtube_video, fetch_youtube_download_link
import requests
import os
import logging
from dotenv import load_dotenv
from pydub import AudioSegment
from pydub.exceptions import CouldntDecodeError
import yaml

load_dotenv()

DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"
ENABLE_TELEGRAM = os.getenv("ENABLE_TELEGRAM", "True").lower() == "true"

logging.basicConfig(
    level=logging.DEBUG if DEBUG_MODE else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

AudioSegment.converter = "ffmpeg"  
FONT_MAPPING = {
    "bold": {
        "A": "𝐀", "B": "𝐁", "C": "𝐂", "D": "𝐃", "E": "𝐄", "F": "𝐅", "G": "𝐆", "H": "𝐇", "I": "𝐈", "J": "𝐉",
        "K": "𝐊", "L": "𝐋", "M": "𝐌", "N": "𝐍", "O": "𝐎", "P": "𝐏", "Q": "𝐐", "R": "𝐑", "S": "𝐒", "T": "𝐓",
        "U": "𝐔", "V": "𝐕", "W": "𝐖", "X": "𝐗", "Y": "𝐘", "Z": "𝐙",
        "a": "𝐚", "b": "𝐛", "c": "𝐜", "d": "𝐝", "e": "𝐞", "f": "𝐟", "g": "𝐠", "h": "𝐡", "i": "𝐢", "j": "𝐣",
        "k": "𝐤", "l": "𝐥", "m": "𝐦", "n": "𝐧", "o": "𝐨", "p": "𝐩", "q": "𝐪", "r": "𝐫", "s": "𝐬", "t": "𝐭",
        "u": "𝐮", "v": "𝐯", "w": "𝐰", "x": "𝐱", "y": "𝐲", "z": "𝐳",
        " ": " ",  # Ensure spaces are preserved
    },
    "italic": {
        "A": "𝘼", "B": "𝘽", "C": "𝘾", "D": "𝘿", "E": "𝙀", "F": "𝙁", "G": "𝙂", "H": "𝙃", "I": "𝙄", "J": "𝙅",
        "K": "𝙆", "L": "𝙇", "M": "𝙈", "N": "𝙉", "O": "𝙊", "P": "𝙋", "Q": "𝙌", "R": "𝙍", "S": "𝙎", "T": "𝙏",
        "U": "𝙐", "V": "𝙑", "W": "𝙒", "X": "𝙓", "Y": "𝙔", "Z": "𝙕",
        "a": "𝙖", "b": "𝙗", "c": "𝙘", "d": "𝙙", "e": "𝙚", "f": "𝙛", "g": "𝙜", "h": "𝙝", "i": "𝙞", "j": "𝙟",
        "k": "𝙠", "l": "𝙡", "m": "𝙢", "n": "𝙣", "o": "𝙤", "p": "𝙥", "q": "𝙦", "r": "𝙧", "s": "𝙨", "t": "𝙩",
        "u": "𝙪", "v": "𝙫", "w": "𝙬", "x": "𝙭", "y": "𝙮", "z": "𝙯",
        " ": " ",  # Ensure spaces are preserved
    }
}

def stylize_text(text, font="bold"):
    """
    Stylize text using the specified font mapping.
    Args:
        text (str): The text to stylize.
        font (str): The font style ('bold' or 'italic').
    Returns:
        str: Stylized text.
    """
    mapping = FONT_MAPPING.get(font, {})
    return ''.join(mapping.get(char, char) for char in text)

def append_channel_id(message):
    """
    Append the bot ID and channel ID as hyperlinks to the message.
    Disable the preview for the hyperlinks.
    """
    bot_id = os.getenv("TELEGRAM_BOT_ID", "@Klavir_Express_Bot")
    channel_id = os.getenv("TELEGRAM_CHANNEL_ID", "@Klavir_Express")
    stylized_bot = stylize_text("Klavir Bot", "italic")
    stylized_channel = stylize_text("Klavir Express", "bold")
    bot_hyperlink = f"<a href='https://t.me/{bot_id.lstrip('@')}'>{stylized_bot}</a>"
    channel_hyperlink = f"<a href='https://t.me/{channel_id.lstrip('@')}'>{stylized_channel}</a>"
    footer = f"\n\n🤖 {bot_hyperlink}\n🎹 {channel_hyperlink}"
    # Ensure the footer is appended only once
    if footer not in message:
        message += footer
    return message

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
    payload = {
        'chat_id': chat_id,
        'text': append_channel_id(message),
        'parse_mode': 'HTML',
        'disable_web_page_preview': True  # Disable preview for hyperlinks
    }
    try:
        logging.debug(f"Sending message to Telegram chat {chat_id} with payload: {payload}")
        response = requests.post(url, json=payload)
        response.raise_for_status()
        logging.debug("Message sent successfully")
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending message: {e}")
        logging.error(f"Payload causing error: {payload}")
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
            data = {'chat_id': chat_id, 'caption': append_channel_id(caption), 'parse_mode': 'HTML'}
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

def format_mp3_filename(track_name, artist_name, album_name=None):
    """
    Format the MP3 file name to include track name, artist name, and album name in a clean format.
    """
    if album_name:
        file_name = f"{artist_name} - {track_name} ({album_name}).mp3"
    else:
        file_name = f"{artist_name} - {track_name}.mp3"
    # Remove unwanted characters and ensure a clean filename
    return file_name.replace("_", " ").replace("/", "-").replace("+", "and").strip()

def send_music_recommendation(track_name, artist_name, album_name=None, album_image=None, preview_url=None, mood=None):
    """
    Send a music recommendation to Telegram with available metadata.
    """
    if not ENABLE_TELEGRAM:
        logging.info("Telegram messaging is disabled in config")
        return None

    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    if not token or not chat_id:
        logging.error("Telegram credentials are not set in environment variables")
        return None

    # Prepare the message without the artist name in the description
    message = f"\U0001F3B5 {stylize_text(track_name, 'bold')}\n"
    if album_name:
        message += f"\U0001F4BF {stylize_text(album_name, 'italic')}"

    logging.info(f"Sending music recommendation: {message}")
    # Search and download audio from YouTube
    audio_path = search_and_download_youtube_mp3(track_name, artist_name, album_name)
    if audio_path and os.path.exists(audio_path):
        # Format the MP3 file name properly
        formatted_name = format_mp3_filename(track_name, artist_name, album_name)
        formatted_path = os.path.join(os.path.dirname(audio_path), formatted_name)
        os.rename(audio_path, formatted_path)
        audio_path = formatted_path

        try:
            # Embed metadata
            logging.info(f"Embedding metadata into MP3 file: {audio_path}")
            audio = MP3(audio_path, ID3=ID3)
            try:
                audio.add_tags()
            except Exception:
                pass
            audio.tags.add(TIT2(encoding=3, text=track_name))  # Track name
            audio.tags.add(TPE1(encoding=3, text=artist_name if artist_name else "Unknown Artist"))  # Artist name
            if album_name:
                audio.tags.add(TALB(encoding=3, text=album_name))  # Album name
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
            logging.info(f"Metadata embedded successfully into MP3 file: {audio_path}")

            # Send MP3 to Telegram
            return send_audio_with_caption(audio_path, message)
        except Exception as e:
            logging.error(f"Error sending MP3: {e}")
            if os.path.exists(audio_path):
                os.remove(audio_path)
    else:
        logging.error("Failed to download audio from YouTube.")

    # Fallback: Send preview URL if available
    if preview_url:
        try:
            logging.debug(f"Sending preview URL: {preview_url}")
            return send_message(f"{message}\n<a href='{preview_url}'>Preview</a>")
        except Exception as e:
            logging.error(f"Error sending preview URL: {e}")

    return None

def is_valid_mp3(file_path):
    """
    Validate if the given file is a valid MP3 file.
    Args:
        file_path (str): Path to the file to validate.
    Returns:
        bool: True if the file is a valid MP3, False otherwise.
    """
    try:
        logging.info(f"Validating MP3 file: {file_path}")
        MP3(file_path)  # Attempt to load the file as an MP3
        logging.info(f"MP3 validation successful: {file_path}")
        return True
    except Exception as e:
        logging.error(f"MP3 validation failed for {file_path}: {e}")
        return False

def increment_api_usage():
    """
    Increment the API usage count in a YAML file.
    """
    yaml_file = os.getenv("API_USAGE_FILE", "api_usage.yaml")
    try:
        if os.path.exists(yaml_file):
            with open(yaml_file, "r") as file:
                data = yaml.safe_load(file) or {}
        else:
            data = {}

        data["usage_count"] = data.get("usage_count", 0) + 1

        with open(yaml_file, "w") as file:
            yaml.safe_dump(data, file)
    except Exception as e:
        logging.error(f"Failed to increment API usage: {e}")

def search_and_download_youtube_mp3(track_name, artist_name, album_name=None):
    """
    Search YouTube for the track and download the audio as MP3.
    Retry up to 3 times if the initial attempt fails.
    Returns the path to the downloaded MP3 file or None if failed.
    """
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Increment API usage only for YouTube API requests
            increment_api_usage()

            # Search for the video
            query = f"{track_name} {artist_name}"
            if album_name:
                query += f" {album_name}"
            video_url = search_youtube_video(query, artist_name)  # Pass artist_name explicitly
            if not video_url:
                logging.error(f"No YouTube video found for the query (Attempt {attempt + 1}/{max_retries})")
                continue

            # Get the download link
            mp3_url = fetch_youtube_download_link(video_url)
            if not mp3_url:
                logging.error(f"Failed to fetch YouTube MP3 download link (Attempt {attempt + 1}/{max_retries})")
                continue

            # Download the MP3 file
            response = requests.get(mp3_url, stream=True)
            if response.status_code == 200:
                file_name = f"{track_name}_{artist_name}.mp3".replace(" ", "_")
                with open(file_name, 'wb') as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)
                return file_name
            else:
                logging.error(f"Failed to download MP3 file (Attempt {attempt + 1}/{max_retries})")
                continue
        except Exception as e:
            logging.error(f"Error in search_and_download_youtube_mp3 (Attempt {attempt + 1}/{max_retries}): {e}")

    logging.error("All attempts to fetch YouTube MP3 download link failed.")
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
            logging.info(f"Notification sent to admin {admin_id}")
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to notify admin {admin_id}: {e}")

def edit_message(message_id, new_text):
    """
    Edit a previously sent message in the configured Telegram chat.
    Args:
        message_id (int): The ID of the message to edit.
        new_text (str): The new text for the message.
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
    url = f'https://api.telegram.org/bot{token}/editMessageText'
    # Convert message_id to integer to ensure proper format for Telegram API
    try:
        message_id = int(message_id)
    except (ValueError, TypeError):
        logging.error(f"Invalid message_id format: {message_id}. Must be convertible to integer.")
        return None
        
    payload = {
        'chat_id': chat_id,
        'message_id': message_id,
        'text': append_channel_id(new_text),
        'parse_mode': 'HTML',
        'disable_web_page_preview': True  # Disable preview for hyperlinks
    }
    try:
        logging.debug(f"Editing message {message_id} in Telegram chat {chat_id} with payload: {payload}")
        response = requests.post(url, json=payload)
        response.raise_for_status()
        logging.debug("Message edited successfully")
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error editing message: {e}")
        logging.error(f"Payload causing error: {payload}")
        return None
