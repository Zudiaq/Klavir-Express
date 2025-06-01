import logging
import os
from send_weather import send_weather_update
from send_quote import send_quote_message
from send_music import process_music_recommendation

DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"

logging.basicConfig(
    level=logging.DEBUG if DEBUG_MODE else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    """
    Entry point for running all bot features: weather update, quote, and music recommendation.
    """
    logging.info("Starting the bot...")
    send_weather_update()
    send_quote_message()
    process_music_recommendation()
    logging.info("Bot process completed!")

if __name__ == "__main__":
    main()
