import os
import requests
import logging
from dotenv import load_dotenv
from mood import map_weather_to_mood
from weather import get_weather

load_dotenv()

ZENQUOTE_API_URL = "https://zenquotes.io/api/random"

# Set DEBUG_MODE from environment variable or default to False
DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() in ("true", "1", "yes")

# Set up logging
logging.basicConfig(
    level=logging.DEBUG if DEBUG_MODE else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def get_quote():
    try:
        logging.debug("Fetching quote from ZenQuotes API")
        response = requests.get(ZENQUOTE_API_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        quote = data[0]['q']
        author = data[0]['a']
        logging.info(f"Quote retrieved: '{quote}' by {author}")
        return quote, author
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
    except requests.exceptions.ConnectionError as conn_err:
        logging.error(f"Connection error occurred: {conn_err}")
    except requests.exceptions.Timeout as timeout_err:
        logging.error(f"Timeout error occurred: {timeout_err}")
    except requests.exceptions.RequestException as req_err:
        logging.error(f"Request error occurred: {req_err}")
    except Exception as e:
        logging.error(f"Error fetching quote: {e}")
    return None, None


def main():
    logging.info("Starting quote retrieval process")
    weather = get_weather()
    if weather:
        mood = map_weather_to_mood(weather)
        logging.info(f"Current mood based on weather: {mood}")
        quote, author = get_quote()
        if quote:
            logging.info(f"Retrieved quote for mood '{mood}'")
            print(f"Today's mood is {mood}. Here's a quote for you: '{quote}' - {author}")
        else:
            logging.warning("Could not retrieve a quote")
            print("Could not retrieve a quote.")
    else:
        logging.error("Could not retrieve weather data")
        print("Could not retrieve weather data.")
    logging.info("Quote retrieval process completed")


if __name__ == "__main__":
    main()
