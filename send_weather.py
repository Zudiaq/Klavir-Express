import logging
import os
from weather import get_weather
from telegram_bot import send_message
from spotify import push_file_to_github
from send_quote import stylize_text  

DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"
GITHUB_REPO = "Zudiaq/youtube-mp3-apis"
WEATHER_MSG_FILE = "weather_msg_id.txt"
GH_PAT = os.getenv("GH_PAT")

logging.basicConfig(
    level=logging.DEBUG if DEBUG_MODE else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

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

def send_weather_update():
    """
    Retrieve the current weather and send a formatted update via Telegram.
    """
    logging.info("Sending weather update...")
    weather = get_weather()
    if weather:
        weather_message = (
            f"{stylize_text('Weather Update', 'bold')}\n"
            f"🌡️ {stylize_text('Temperature:', 'italic')} {weather['temp']}°C\n"
            f"💧 {stylize_text('Humidity:', 'italic')} {weather['humidity']}%\n"
            f"🌬️ {stylize_text('Wind Speed:', 'italic')} {weather['wind_speed']} m/s\n"
            f"📜 {stylize_text('Description:', 'italic')} {weather['description']}"
        )
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
