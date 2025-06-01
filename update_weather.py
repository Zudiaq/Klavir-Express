import logging
from weather import get_weather
from telegram_bot import send_message

logging.basicConfig(level=logging.INFO)

def update_weather_message():
    """
    Update the weather message in the Telegram channel.
    """
    weather = get_weather()
    if weather:
        weather_message = (
            f"\U0001F324 <b>Weather Update</b>\n"
            f"\U0001F321 Temperature: {weather['temp']}°C\n"
            f"\U0001F4A7 Humidity: {weather['humidity']}%\n"
            f"\U0001F32C Wind Speed: {weather['wind_speed']} m/s\n"
            f"\U0001F4DC Description: {weather['description']}"
        )
        send_message(weather_message)
    else:
        logging.error("Failed to retrieve weather data.")

if __name__ == "__main__":
    update_weather_message()
