import os
import logging
from mood import map_weather_to_mood
from weather import get_weather
from spotify import get_song_by_mood_spotify, load_sent_songs, save_sent_song
from lastfm import get_song_by_mood
from telegram_bot import send_music_recommendation as send_to_telegram
from telegram_bot import notify_admins
from send_quote import stylize_text
from telegram_bot import append_channel_id

DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"

logging.basicConfig(
    level=logging.DEBUG if DEBUG_MODE else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def process_music_recommendation():
    """
    Process and send a music recommendation based on current weather and mood.
    Chooses the music API (Spotify or Last.fm) and sends the recommendation to Telegram.
    Retries with alternative queries or fallback songs if the first attempt fails.
    """
    logging.info("Processing music recommendation...")
    weather = get_weather()
    if not weather:
        logging.error("Failed to retrieve weather data.")
        notify_admins("Failed to retrieve weather data. Please check the weather API.")
        return

    mood = map_weather_to_mood(weather)
    logging.info(f"Determined mood: {mood}")
    music_api = os.getenv('API_SELECTION', 'spotify')
    max_retries = 3  # Number of retries for alternative queries or fallback songs

    for attempt in range(max_retries):
        logging.info(f"Attempt {attempt + 1} for mood: {mood}")
        if music_api.lower() == 'spotify':
            song = get_song_by_mood_spotify(mood)
        else:
            song = get_song_by_mood(mood)

        if song:
            track_name, artist_name, album_name, album_image, preview_url = song
            logging.info(f"Selected song: {track_name} by {artist_name} (Album: {album_name})")
            message = f"\U0001F3B5 {stylize_text(track_name, 'bold')}\n"
            if album_name:
                message += f"\U0001F4BF {stylize_text(album_name, 'italic')}"
            message = append_channel_id(message)  # Add footer with channel and bot IDs
            result = send_to_telegram(
                track_name, artist_name, album_name, album_image, preview_url, mood
            )
            if result:
                logging.info("Music recommendation sent successfully.")
                try:
                    save_sent_song(track_name, artist_name, album_name)
                    logging.info(f"Saved song to sent_songs.yaml: {track_name} by {artist_name}")
                except Exception as e:
                    logging.error(f"Error saving sent song: {e}")
                return  # Exit after successful recommendation
            else:
                logging.error("Failed to send music recommendation.")
        else:
            logging.warning("No song found. Retrying with a different query or fallback.")

    # Notify admins if all attempts fail
    logging.error("Failed to retrieve or send a music recommendation after multiple attempts.")
    notify_admins("Failed to retrieve or send a music recommendation. Possible API key exhaustion or no suitable songs found.")

if __name__ == "__main__":
    process_music_recommendation()
