import logging
import os
from mood import map_weather_to_mood
from weather import get_weather
from spotify import get_song_by_mood_spotify
from lastfm import get_song_by_mood
from telegram_bot import send_music_recommendation as send_to_telegram

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def process_music_recommendation():
    """
    Process and send a music recommendation based on current weather and mood.
    Chooses the music API (Spotify or Last.fm) and sends the recommendation to Telegram.
    Implements improved error handling for API failures.
    """
    logging.info("Starting music recommendation process...")
    weather = get_weather()
    if not weather:
        logging.error("Failed to retrieve weather data.")
        return

    mood = map_weather_to_mood(weather)
    logging.info(f"Mapped weather to mood: {mood}")

    music_api = os.getenv('API_SELECTION', 'spotify')
    song = None

    if music_api.lower() == 'spotify':
        logging.info("Attempting to get song recommendation from Spotify...")
        song = get_song_by_mood_spotify(mood)
    else:
        logging.info("Attempting to get song recommendation from Last.fm...")
        song = get_song_by_mood(mood)

    if not song and music_api.lower() == 'spotify':
        logging.warning("Spotify recommendation failed, trying Last.fm as fallback...")
        song = get_song_by_mood(mood)
    elif not song:
        logging.warning("Last.fm recommendation failed, trying Spotify as fallback...")
        song = get_song_by_mood_spotify(mood)

    if song:
        track_name, artist_name, album_name, album_image, preview_url = song
        try:
            result = send_to_telegram(
                track_name, artist_name, album_name, album_image, preview_url, mood
            )
            logging.info(f"Music recommendation for '{track_name}' by '{artist_name}' sent successfully.")
        except Exception as e:
            logging.error(f"Failed to send music recommendation to Telegram: {e}")
    else:
        logging.error("Failed to retrieve song from all available music APIs.")
        from telegram_bot import send_message
        send_message(f"⚠️ Failed to retrieve a song recommendation for mood: {mood}. Please try again later.")
    logging.info("Music recommendation process completed.")

if __name__ == "__main__":
    process_music_recommendation()
