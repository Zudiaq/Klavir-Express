import logging
import os
from datetime import datetime
from pytz import timezone  # Import timezone for handling Tehran time
from quote import get_quote
from google_translate import translate_to_persian
from telegram_bot import send_message
from telegram_bot import append_channel_id

DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"

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
        " ": " ",  # Ensure spaces are preserved
    },
    "italic": {
        "A": "𝘼", "B": "𝘽", "C": "𝘾", "D": "𝘿", "E": "𝙀", "F": "𝙁", "G": "𝙂", "H": "𝙃", "I": "𝙄", "J": "𝙅",
        "K": "𝙆", "L": "𝙇", "M": "𝙈", "N": "𝙉", "O": "𝙊", "P": "𝙋", "Q": "𝙌", "R": "𝙍", "S": "𝙎", "T": "𝙏",
        "U": "𝙐", "V": "𝙑", "W": "𝙒", "X": "𝙓", "Y": "𝙔", "Z": "𝙕",
        "1": "𝟏", "2": "𝟐", "3": "𝟑", "4": "𝟒", "5": "𝟓", "6": "𝟔", "7": "𝟕", "8": "𝟖", "9": "𝟗", "0": "𝟎",
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

def send_quote_message():
    """
    Retrieve a quote, translate it to Persian, and send it via Telegram with proper formatting.
    Add conditional morning or night greetings based on Tehran time.
    """
    logging.info("Sending quote message...")
    tehran_time = datetime.now(timezone("Asia/Tehran"))  # Get current time in Tehran
    quote, author = get_quote()
    if quote:
        translated_quote = translate_to_persian(quote)
        styled_quote = f"""✨ \"{stylize_text(quote, 'italic')}\"\n\n{stylize_text(translated_quote, 'bold')}"""
        if author and author.lower() != "unknown":
            styled_quote += f"\n\n— {stylize_text(author, 'italic')}"

        # Add conditional greetings based on Tehran time
        if 6 <= tehran_time.hour < 17:  # Morning
            styled_quote += f"\n\n☀️ {stylize_text('Good Morning', 'italic')}"
        elif 18 <= tehran_time.hour < 24:  # Night
            styled_quote += f"\n\n🌙 {stylize_text('Good Night', 'italic')}"

        # Append footer with bot and channel IDs only once
        if "bot_id" not in styled_quote and "channel_id" not in styled_quote:
            styled_quote = append_channel_id(styled_quote)
        
        result = send_message(styled_quote)
        logging.debug(f"Quote message send result: {result}")
    else:
        logging.error("Failed to retrieve quote.")

if __name__ == "__main__":
    send_quote_message()
