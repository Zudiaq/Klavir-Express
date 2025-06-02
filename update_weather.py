import logging
import os
import requests
from weather import get_weather
from telegram_bot import edit_message
from send_quote import stylize_text
from telegram_bot import append_channel_id

DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"
GITHUB_REPO = "Zudiaq/youtube-mp3-apis"
WEATHER_MSG_FILE = "weather_msg_id.txt"
GH_PAT = os.getenv("GH_PAT")

logging.basicConfig(
    level=logging.DEBUG if DEBUG_MODE else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def pull_weather_message_id_from_github():
    """
    Pull the weather message ID from the private GitHub repository.
    """
    url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/{WEATHER_MSG_FILE}"
    headers = {"Authorization": f"token {GH_PAT}"}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        with open(WEATHER_MSG_FILE, "w", encoding="utf-8") as f:
            f.write(response.text)
        with open(WEATHER_MSG_FILE, "r", encoding="utf-8") as f:
            message_id = f.read().strip()
        logging.info(f"Weather message ID pulled from GitHub: {message_id}")
        return message_id
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to pull weather message ID from GitHub: {e}")
        return None

def update_weather_message():
    """
    Update the previously sent weather message with the latest weather data.
    """
    logging.info("Updating weather message...")
    weather = get_weather()
    if weather:
        weather_message = (
            f"⛅️ {stylize_text('Weather Update', 'bold')}\n"
            f"🌡️ Temperature: {weather['temp']}°C\n"
            f"💧 Humidity: {weather['humidity']}%\n"
            f"🌬️ Wind Speed: {weather['wind_speed']} m/s\n"
            f"📜 Description: {weather['description']}"
        )
        # Append channel hyperlink using append_channel_id
        weather_message = append_channel_id(weather_message)
        message_id = pull_weather_message_id_from_github()
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
