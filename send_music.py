import logging
import os
from mood import map_weather_to_mood
from weather import get_weather
from spotify import get_song_by_mood_spotify
from lastfm import get_song_by_mood
from telegram_bot import send_music_recommendation as send_to_telegram
from config import DEFAULT_MUSIC_API

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def process_music_recommendation():
    """
    Process and send a music recommendation based on current weather and mood.
    Chooses the music API (Spotify or Last.fm) and sends the recommendation to Telegram.
    """
    logging.info("Processing music recommendation...")
    weather = get_weather()
    if weather:
        mood = map_weather_to_mood(weather)
        music_api = os.getenv('API_SELECTION', DEFAULT_MUSIC_API)
        if music_api.lower() == 'spotify':
            song = get_song_by_mood_spotify(mood)
        else:
            song = get_song_by_mood(mood)
        if song:
            track_name, artist_name, album_name, album_image, preview_url = song
            result = send_to_telegram(
                track_name, artist_name, album_name, album_image, preview_url, mood
            )
            logging.debug(f"Music recommendation send result: {result}")
        else:
            logging.error("Failed to retrieve song.")
    else:
        logging.error("Failed to retrieve weather data.")

if __name__ == "__main__":
    process_music_recommendation()
