import os
import requests
import logging
from dotenv import load_dotenv
from config import CITY, REGION, DEBUG_MODE

load_dotenv()

API_KEY = os.getenv("OPENWEATHERMAP_API_KEY")

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
    url = f"https://api.openweathermap.org/data/2.5/weather?q={CITY},{REGION}&appid={API_KEY}&units=metric&lang=fa"
    try:
        logging.debug(f"Fetching weather data for {CITY}, {REGION}")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        weather_main = data['weather'][0]['main']
        weather_desc = data['weather'][0]['description']
        temp = data['main']['temp']
        humidity = data['main']['humidity']
        wind_speed = data['wind']['speed']
        weather_data = {
            'main': weather_main,
            'description': weather_desc,
            'temp': temp,
            'humidity': humidity,
            'wind_speed': wind_speed,
            'pressure': data['main'].get('pressure'),
            'visibility': data.get('visibility')
        }
        logging.debug(f"Weather data retrieved successfully: {weather_data}")
        return weather_data
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
    except requests.exceptions.ConnectionError as conn_err:
        logging.error(f"Connection error occurred: {conn_err}")
    except requests.exceptions.Timeout as timeout_err:
        logging.error(f"Timeout error occurred: {timeout_err}")
    except requests.exceptions.RequestException as req_err:
        logging.error(f"Request error occurred: {req_err}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
    return None