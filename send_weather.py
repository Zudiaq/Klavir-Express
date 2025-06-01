import logging
import os
from weather import get_weather
from telegram_bot import send_message

DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"

logging.basicConfig(
    level=logging.DEBUG if DEBUG_MODE else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def update_environment_variable(key, value):
    """
    Update an environment variable in the Deployment 1 environment.
    """
    env_file = "/github/workspace/.env"  # Path to the environment file
    try:
        with open(env_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        with open(env_file, "w", encoding="utf-8") as f:
            updated = False
            for line in lines:
                if line.startswith(f"{key}="):
                    f.write(f"{key}={value}\n")
                    updated = True
                else:
                    f.write(line)
            if not updated:
                f.write(f"{key}={value}\n")
        logging.info(f"Updated environment variable: {key}={value}")
    except Exception as e:
        logging.error(f"Failed to update environment variable {key}: {e}")

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
            update_environment_variable("WEATHER_MESSAGE_ID", message_id)
            logging.info(f"Weather message sent successfully with ID: {message_id}")
        else:
            logging.error(f"Failed to send weather message. Response: {result}")
    else:
        logging.error("Failed to retrieve weather data.")

if __name__ == "__main__":
    send_weather_update()
