import logging
import os
import json
from datetime import datetime
from weather import get_weather
from telegram_bot import send_message

DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"
WEATHER_MESSAGE_FILE = "weather_message.json"

logging.basicConfig(
    level=logging.DEBUG if DEBUG_MODE else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def save_weather_message_id(message_id):
    """
    Save the weather message ID and the current date to a file for later updates.
    """
    data = {
        "message_id": message_id,
        "date": datetime.now().strftime("%Y-%m-%d")
    }
    with open(WEATHER_MESSAGE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f)

def load_weather_message_id():
    """
    Load the weather message ID from the file if it corresponds to the current date.
    """
    if os.path.exists(WEATHER_MESSAGE_FILE):
        with open(WEATHER_MESSAGE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if data.get("date") == datetime.now().strftime("%Y-%m-%d"):
                return data.get("message_id")
    return None

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
            save_weather_message_id(result["message_id"])
            logging.info(f"Weather message sent successfully with ID: {result['message_id']}")
        else:
            logging.error(f"Failed to send weather message. Response: {result}")
    else:
        logging.error("Failed to retrieve weather data.")

if __name__ == "__main__":
    send_weather_update()
