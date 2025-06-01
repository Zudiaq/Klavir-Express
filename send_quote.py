import logging
import os
from quote import get_quote
from google_translate import translate_to_persian
from telegram_bot import send_message

DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"

logging.basicConfig(
    level=logging.DEBUG if DEBUG_MODE else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def send_quote_message():
    """
    Retrieve a quote, translate it to Persian, and send it via Telegram with proper formatting.
    """
    logging.info("Sending quote message...")
    quote, author = get_quote()
    if quote:
        translated_quote = translate_to_persian(quote)
        styled_quote = f"""✨ \"{quote}\"\n\n{translated_quote}"""
        if author and author.lower() != "unknown":
            styled_quote += f"\n\n— {author}"
        result = send_message(styled_quote)
        logging.debug(f"Quote message send result: {result}")
    else:
        logging.error("Failed to retrieve quote.")

if __name__ == "__main__":
    send_quote_message()
