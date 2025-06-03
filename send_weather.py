import logging
import os
from weather import get_weather
from telegram_bot import send_message
from spotify import push_file_to_github
from telegram_bot import append_channel_id

DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"
GITHUB_REPO = "Zudiaq/youtube-mp3-apis"
WEATHER_MSG_FILE = "weather_msg_id.txt"
GH_PAT = os.getenv("GH_PAT")
CITY = "Tehran"

logging.basicConfig(
    level=logging.DEBUG if DEBUG_MODE else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

FONT_MAPPING = {
    "bold": {
        "A": "𝐀", "B": "𝐁", "C": "𝐂", "D": "𝐃", "E": "𝐄", "F": "𝐅", "G": "𝐆", "H": "𝐇", "I": "𝐈", "J": "𝐉",
        "K": "𝐊", "L": "𝐋", "M": "𝐌", "N": "𝐍", "O": "𝐎", "P": "𝐏", "Q": "𝐐", "R": "𝐑", "S": "𝐒", "T": "𝐓",
        "U": "𝐔", "V": "𝐕", "W": "𝐖", "X": "𝐗", "Y": "𝐘", "Z": "𝐙",
        "1": "𝟏", "2": "𝟐", "3": "𝟑", "4": "𝟒", "5": "𝟓", "6": "𝟔", "7": "𝟕", "8": "𝟖", "9": "𝟗", "0": "𝟎",
        "a": "𝐚", "b": "𝐛", "c": "𝐜", "d": "𝐝", "e": "𝐞", "f": "𝐟", "g": "𝐠", "h": "𝐡", "i": "𝐢", "j": "𝐣",
        "k": "𝐤", "l": "𝐥", "m": "𝐦", "n": "𝐧", "o": "𝐨", "p": "𝐩", "q": "𝐪", "r": "𝐫", "s": "𝐬", "t": "𝐭",
        "u": "𝐮", "v": "𝐯", "w": "𝐰", "x": "𝐱", "y": "𝐲", "z": "𝐳",
        " ": " ",  
    },
    "italic": {
        "A": "𝘼", "B": "𝘽", "C": "𝘾", "D": "𝘿", "E": "𝙀", "F": "𝙁", "G": "𝙂", "H": "𝙃", "I": "𝙄", "J": "𝙅",
        "K": "𝙆", "L": "𝙇", "M": "𝙈", "N": "𝙉", "O": "𝙊", "P": "𝙋", "Q": "𝙌", "R": "𝙍", "S": "𝙎", "T": "𝙏",
        "U": "𝙐", "V": "𝙑", "W": "𝙒", "X": "𝙓", "Y": "𝙔", "Z": "𝙕",
        "1": "𝟏", "2": "𝟐", "3": "𝟑", "4": "𝟒", "5": "𝟓", "6": "𝟔", "7": "𝟕", "8": "𝟖", "9": "𝟗", "0": "𝟎",
        "a": "𝙖", "b": "𝙗", "c": "𝙘", "d": "𝙙", "e": "𝙚", "f": "𝙛", "g": "𝙜", "h": "𝙝", "i": "𝙞", "j": "𝙟",
        "k": "𝙠", "l": "𝙡", "m": "𝙢", "n": "𝙣", "o": "𝙤", "p": "𝙥", "q": "𝙦", "r": "𝙧", "s": "𝙨", "t": "𝙩",
        "u": "𝙪", "v": "𝙫", "w": "𝙬", "x": "𝙭", "y": "𝙮", "z": "𝙯",
        " ": " ",  
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

def save_weather_message_id_to_github(message_id):
    """
    Save the weather message ID to the private GitHub repository.
    """
    try:
        with open(WEATHER_MSG_FILE, "w", encoding="utf-8") as f:
            f.write(str(message_id))
        with open(WEATHER_MSG_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        push_file_to_github(WEATHER_MSG_FILE, content, "Update weather message ID", GH_PAT)
        logging.info(f"Weather message ID saved to GitHub: {message_id}")
    except Exception as e:
        logging.error(f"Failed to save weather message ID to GitHub: {e}")

def get_uv_risk_level(uv_index):
    """
    Determine the risk level of the UV index and return an emoji representation.
    Args:
        uv_index (float): The UV index value.
    Returns:
        str: Emoji representing the UV risk level.
    """
    if uv_index is None:
        return "❓"  # Unknown
    if uv_index < 3:
        return "🟢 Low"
    elif 3 <= uv_index < 6:
        return "🟡 Moderate"
    elif 6 <= uv_index < 8:
        return "🟠 High"
    elif 8 <= uv_index < 11:
        return "🔴 Very High"
    else:
        return "⚫️ Extreme"

def send_weather_update():
    """
    Retrieve the current weather and send a formatted update via Telegram.
    """
    logging.info("Sending weather update...")
    weather = get_weather()
    if weather:
        uv_risk = get_uv_risk_level(weather['uv_index'])
        weather_message = (
            f"⛅️ {stylize_text('Weather Update', 'bold')}\n"
            f"===================\n"
            f"🌡 {stylize_text('Temperature:', 'italic')} {stylize_text(str(weather['temp']), 'bold')}°{stylize_text('C', 'italic')}\n"
            f"💧 {stylize_text('Humidity:', 'italic')} {stylize_text(str(weather['humidity']), 'bold')}%\n"
            f"🌬 {stylize_text('Wind Speed:', 'italic')} {stylize_text(str(weather['wind_speed']), 'bold')} {stylize_text('m/s', 'italic')}\n"
            f"💬 {stylize_text('Description:', 'italic')} {stylize_text(weather['description'], 'italic')}\n"
            f"🌞 {stylize_text('UV Index:', 'italic')} {stylize_text(str(weather['uv_index']), 'bold')} ({uv_risk})\n\n"
            f"📍{stylize_text(CITY, 'italic')}"
        )
        weather_message = append_channel_id(weather_message)  # Add footer with bot and channel IDs
        result = send_message(weather_message)
        if result and "result" in result and "message_id" in result["result"]:
            message_id = result["result"]["message_id"]
            save_weather_message_id_to_github(message_id)
            logging.info(f"Weather message sent successfully with ID: {message_id}")
        else:
            logging.error(f"Failed to send weather message. Response: {result}")
    else:
        logging.error("Failed to retrieve weather data.")

if __name__ == "__main__":
    send_weather_update()

