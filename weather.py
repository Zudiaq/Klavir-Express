# ==========================
# Weather API Integration
# ==========================
import os
import requests
import logging
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENWEATHERMAP_API_KEY")
CITY = os.getenv("CITY", "Tehran")
REGION = os.getenv("REGION", "IR")
DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"

logging.basicConfig(
    level=logging.DEBUG if DEBUG_MODE else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def get_weather():
    """
    Fetch current weather data for the configured city and region.
    Returns:
        dict: Weather data with main condition, description, temperature, humidity, wind speed,
              pressure, visibility, and other available metrics.
        None: If there was an error fetching the data.
    """
    if not API_KEY:
        logging.error("OPENWEATHERMAP_API_KEY is not set in environment variables.")
        return None
    url = f"https://api.openweathermap.org/data/2.5/weather?q={CITY},{REGION}&appid={API_KEY}&units=metric&lang=en"
    try:
        logging.debug(f"Fetching weather data for {CITY}, {REGION}")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        weather_data = {
            'main': data['weather'][0]['main'],
            'description': data['weather'][0]['description'],
            'temp': data['main']['temp'],
            'humidity': data['main']['humidity'],
            'wind_speed': data['wind']['speed'],
            'pressure': data['main'].get('pressure'),
            'visibility': data.get('visibility')
        }
        logging.debug(f"Weather data retrieved successfully: {weather_data}")
        return weather_data
    except requests.exceptions.RequestException as req_err:
        logging.error(f"Request error occurred: {req_err}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
    return None
