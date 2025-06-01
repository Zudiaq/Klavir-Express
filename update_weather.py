import logging
import os
from weather import get_weather
from telegram_bot import edit_message
from spotify import pull_file_from_github

DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"
GITHUB_REPO = "Zudiaq/youtube-mp3-apis"
WEATHER_MSG_FILE = "weather_msg_id.txt"

logging.basicConfig(
    level=logging.DEBUG if DEBUG_MODE else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def load_weather_message_id_from_github():
    """
    Load the weather message ID from the private GitHub repository.
    """
    try:
        message_id = pull_file_from_github(WEATHER_MSG_FILE).strip()
        logging.info(f"Weather message ID loaded from GitHub: {message_id}")
        return message_id
    except Exception as e:
        logging.error(f"Failed to load weather message ID from GitHub: {e}")
        return None

def update_weather_message():
    """
    Update the previously sent weather message with the latest weather data.
    """
    logging.info("Updating weather message...")
    weather = get_weather()
    if weather:
        weather_message = (
            f"\U0001F324 <b>Weather Update</b>\n"
            f"\U0001F321 Temperature: {weather['temp']}°C\n"
            f"\U0001F4A7 Humidity: {weather['humidity']}%\n"
            f"\U0001F32C Wind Speed: {weather['wind_speed']} m/s\n"
            f"\U0001F4DC Description: {weather['description']}"
        )
        message_id = load_weather_message_id_from_github()
        if message_id:
            result = edit_message(message_id, weather_message)
            if result:
                logging.info("Weather message updated successfully.")
            else:
                logging.error("Failed to update weather message.")
        else:
            logging.error("No weather message ID found. Cannot update.")
    else:
        logging.error("Failed to retrieve weather data.")

if __name__ == "__main__":
    update_weather_message()
