import logging
import os
from weather import get_weather
from telegram_bot import send_message
from spotify import push_file_to_github

DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"
GITHUB_REPO = "Zudiaq/youtube-mp3-apis"
WEATHER_MSG_FILE = "weather_msg_id.txt"

logging.basicConfig(
    level=logging.DEBUG if DEBUG_MODE else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def save_weather_message_id_to_github(message_id):
    """
    Save the weather message ID to the private GitHub repository.
    """
    try:
        push_file_to_github(WEATHER_MSG_FILE, message_id, "Update weather message ID")
        logging.info(f"Weather message ID saved to GitHub: {message_id}")
    except Exception as e:
        logging.error(f"Failed to save weather message ID to GitHub: {e}")

def send_weather_update():
    """
    Retrieve the current weather and send a formatted update via Telegram.
    """
    logging.info("Sending weather update...")
    weather = get_weather()
    if weather:
        weather_message = (
            f"\U0001F324 <b>Weather</b>\n"
            f"\U0001F321 Temperature: {weather['temp']}\u00B0C\n"
            f"\U0001F4A7 Humidity: {weather['humidity']}%\n"
            f"\U0001F32C Wind Speed: {weather['wind_speed']} m/s\n"
            f"\U0001F4DC Description: {weather['description']}"
        )
        result = send_message(weather_message)
        if result and "message_id" in result:
            message_id = result["message_id"]
            save_weather_message_id_to_github(str(message_id))
            logging.info(f"Weather message sent successfully with ID: {message_id}")
        else:
            logging.error(f"Failed to send weather message. Response: {result}")
    else:
        logging.error("Failed to retrieve weather data.")

if __name__ == "__main__":
    send_weather_update()
