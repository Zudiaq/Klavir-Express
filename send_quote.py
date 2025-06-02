import logging
import os
from datetime import datetime
from quote import get_quote
from google_translate import translate_to_persian
from telegram_bot import send_message

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
        "1": "𝟏", "2": "𝟐", "3": "𝟑", "4": "𝟒", "5": "𝟓", "6": "𝟔", "7": "𝟕", "8": "𝟖", "9": "𝟗", "0": "𝟎"
    },
    "italic": {
        "A": "𝘼", "B": "𝘽", "C": "𝘾", "D": "𝘿", "E": "𝙀", "F": "𝙁", "G": "𝙂", "H": "𝙃", "I": "𝙄", "J": "𝙅",
        "K": "𝙆", "L": "𝙇", "M": "𝙈", "N": "𝙉", "O": "𝙊", "P": "𝙋", "Q": "𝙌", "R": "𝙍", "S": "𝙎", "T": "𝙏",
        "U": "𝙐", "V": "𝙑", "W": "𝙒", "X": "𝙓", "Y": "𝙔", "Z": "𝙕",
        "1": "𝟏", "2": "𝟐", "3": "𝟑", "4": "𝟒", "5": "𝟓", "6": "𝟔", "7": "𝟕", "8": "𝟖", "9": "𝟗", "0": "𝟎"
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
    Add conditional morning or night greetings based on the time.
    """
    logging.info("Sending quote message...")
    quote, author = get_quote()
    if quote:
        translated_quote = translate_to_persian(quote)
        styled_quote = f"""✨ \"{quote}\"\n\n{translated_quote}"""
        if author and author.lower() != "unknown":
            styled_quote += f"\n\n— {author}"

        # Add conditional greetings
        now = datetime.now()
        if 6 <= now.hour < 17:  # Morning
            styled_quote += f"\n\n☀️ {stylize_text('GM', 'italic')}"
        elif 18 <= now.hour < 24:  # Night
            styled_quote += f"\n\n🌙 {stylize_text('GN', 'italic')}"

        result = send_message(styled_quote)
        logging.debug(f"Quote message send result: {result}")
    else:
        logging.error("Failed to retrieve quote.")

if __name__ == "__main__":
    send_quote_message()
