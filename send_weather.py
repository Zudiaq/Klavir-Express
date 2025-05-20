import logging
from weather import get_weather
from telegram_bot import send_message

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

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
        logging.debug(f"Weather message send result: {result}")
    else:
        logging.error("Failed to retrieve weather data.")

if __name__ == "__main__":
    send_weather_update()
