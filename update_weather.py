import logging
import os
import requests
from weather import get_weather
from telegram_bot import edit_message
from send_quote import stylize_text
from telegram_bot import append_channel_id
from datetime import datetime
from pytz import timezone

DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"
GITHUB_REPO = "Zudiaq/youtube-mp3-apis"
WEATHER_MSG_FILE = "weather_msg_id.txt"
GH_PAT = os.getenv("GH_PAT")
CITY = "Tehran"

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

def get_uv_risk_level(uv_index, is_after_sunset=False):
    """
    Determine the risk level of the UV index and return an emoji representation.
    If it's after sunset, return the entire UV index text with a strikethrough.
    """
    if uv_index is None:
        return "❓"  # Unknown
    risk_text = ""
    if uv_index < 3:
        risk_text = "🟢 Low"
    elif 3 <= uv_index < 6:
        risk_text = "🟡 Moderate"
    elif 6 <= uv_index < 8:
        risk_text = "🟠 High"
    elif 8 <= uv_index < 11:
        risk_text = "🔴 Very High"
    else:
        risk_text = "⚫️ Extreme"
    
    uv_text = f"{uv_index} ({risk_text})"
    return f"~~{uv_text}~~" if is_after_sunset else uv_text

def update_weather_message():
    """
    Update the previously sent weather message with the latest weather data.
    """
    logging.info("Updating weather message...")
    weather = get_weather()
    if weather:
        tehran_time = datetime.now(timezone("Asia/Tehran"))
        is_after_sunset = tehran_time.hour >= 19  # Check if it's after 7 PM
        uv_risk = get_uv_risk_level(weather['uv_index'], is_after_sunset)
        weather_message = (
            f"⛅️ {stylize_text('Weather Update', 'bold')}\n"
            f"===================\n"
            f"🌡 {stylize_text('Temperature:', 'italic')} {stylize_text(str(weather['temp']), 'bold')}°{stylize_text('C', 'italic')}\n"
            f"💧 {stylize_text('Humidity:', 'italic')} {stylize_text(str(weather['humidity']), 'bold')}%\n"
            f"🌬 {stylize_text('Wind Speed:', 'italic')} {stylize_text(str(weather['wind_speed']), 'bold')} {stylize_text('m/s', 'italic')}\n"
            f"💬 {stylize_text('Description:', 'italic')} {stylize_text(weather['description'], 'italic')}\n"
            f"🌞 {stylize_text('UV Index:', 'italic')} {uv_risk}\n\n"
            f"📍{stylize_text(CITY, 'italic')}"
        )
        weather_message = append_channel_id(weather_message)  # Add footer with channel and bot IDs
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
