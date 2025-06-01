import os
import logging
from mood import map_weather_to_mood
from weather import get_weather
from spotify import get_song_by_mood_spotify
from lastfm import get_song_by_mood
from telegram_bot import send_music_recommendation as send_to_telegram
from telegram_bot import notify_admins
import json

DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"

logging.basicConfig(
    level=logging.DEBUG if DEBUG_MODE else logging.INFO,
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
        music_api = os.getenv('API_SELECTION', 'spotify')
        if music_api.lower() == 'spotify':
            song = get_song_by_mood_spotify(mood)
        else:
            song = get_song_by_mood(mood)
        if song:
            track_name, artist_name, album_name, album_image, preview_url = song
            result = send_to_telegram(
                track_name, artist_name, album_name, album_image, preview_url, mood
            )
            if result:
                logging.info("Music recommendation sent successfully.")
            else:
                logging.error("Failed to send music recommendation.")
            # Save the song to sent_songs.json
            try:
                save_sent_song(track_name, artist_name, album_name)
            except Exception as e:
                logging.error(f"Error saving sent song: {e}")
        else:
            logging.error("Failed to retrieve song.")
            notify_admins("Failed to retrieve a song recommendation. Possible API key exhaustion.")
    else:
        logging.error("Failed to retrieve weather data.")
        notify_admins("Failed to retrieve weather data. Please check the weather API.")

def save_sent_song(track_name, artist_name, album_name, file_path="sent_songs.json"):
    """
    Save the sent song information to a JSON file to avoid recommending the same song again.
    """
    song_entry = {
        "track_name": track_name,
        "artist_name": artist_name,
        "album_name": album_name
    }
    try:
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                sent_songs = json.load(f)
        else:
            sent_songs = []
        sent_songs.append(song_entry)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(sent_songs, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logging.error(f"Failed to save sent song: {e}")

if __name__ == "__main__":
    process_music_recommendation()
