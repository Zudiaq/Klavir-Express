import logging
from weather import get_weather
from telegram_bot import send_message
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def send_weather_update():
    """
    Send weather updates, date, time, and day of the week as a text message to Telegram.
    """
    logging.info("Retrieving weather data...")
    weather = get_weather()
    if not weather:
        logging.error("Failed to retrieve weather data.")
        return

    now = datetime.now()
    current_time = now.strftime("%H:%M")
    current_date = now.strftime("%Y-%m-%d")
    current_weekday = now.strftime("%A")

    message = (f"⛅️ Weather =>\n"
               f"Temperature: {weather['temp']}°C\n"
               f"Status: {weather['description']}\n\n"
               f"📅 {current_weekday}, {now.strftime('%B %d')}\n")

    logging.info("Sending weather update to Telegram...")
    result = send_message(message)
    logging.debug(f"Message send result: {result}")


if __name__ == "__main__":
    send_weather_update()