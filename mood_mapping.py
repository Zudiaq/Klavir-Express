# mood_mapping.py
import random
import logging
import os
from datetime import datetime

DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"

logging.basicConfig(
    level=logging.DEBUG if DEBUG_MODE else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

PLAYLIST_GENRES = [
    # Rock and Metal genres
    "classic rock", "psychedelic rock", "progressive rock", "art rock", "album rock",
    "hard rock", "blues rock", "alternative rock", "indie rock", "indie pop", "dream pop",
    "shoegaze", "post-punk", "new wave", "gothic rock", "darkwave", "grunge", "britpop",
    "punk rock", "pop punk", "emo", "alternative metal", "nu metal", "heavy metal",
    "symphonic metal", "gothic metal", "doom metal", "progressive metal", "neue deutsche härte",

    # Electronic and Dance genres
    "new age", "ambient", "trip hop", "downtempo", "electronica", "synth-pop", "industrial",
    "techno", "house", "trance", "eurodance", "dubstep", "drum and bass", "synthwave",
    "electropop", "art pop", "dance pop", "chillwave", "future bass", "idm", "deep house",

    # Pop and R&B genres
    "pop", "traditional pop", "vocal jazz", "disco", "bedroom pop", "latin pop",
    "soul", "funk", "motown", "neo soul", "alternative r&b", "chill pop", "funk rap",

    # Hip-Hop and Rap genres
    "hip hop", "g-funk", "conscious hip hop", "alternative hip hop", "jazz rap", "trap",
    "cloud rap", "emo rap", "pop rap", "melodic rap",

    # Jazz and Blues genres
    "jazz", "blues", "smooth jazz", "soul jazz", "acid jazz", "bebop", "cool jazz",

    # Folk and Country genres
    "folk", "contemporary folk", "singer-songwriter", "americana", "country", "country rock",
    "chamber folk", "indie folk", "bluegrass",

    # World and Experimental genres
    "celtic", "latin alternative", "reggae", "afrobeat", "bossa nova", "flamenco",
    "bollywood", "anime score", "russian post-punk", "chanson", "city pop", "tango",
    "world fusion", "ethereal wave", "experimental", "avant-garde",

    # Classical and Instrumental genres
    "classical", "orchestral", "film score", "video game music", "minimalism", "piano",
    "instrumental ballads", "string quartet", "baroque", "romantic era",

    # Rare/Niche genres (minimal inclusion)
    "hyperpop", "phonk", "vaporwave", "chillhop", "lo-fi beats", "future funk"
]

MOOD_MAPPING = {
    "09:00_start_day_warm": {
        "seed_genres": ["indie folk", "acoustic", "chill pop"],
        "target_valence": (0.5, 0.8),
        "target_energy": (0.3, 0.5),
        "target_acousticness": (0.6, 1.0)
    },
    "10:30_focus_motivation": {
        "seed_genres": ["lo-fi", "chillhop", "instrumental hip-hop"],
        "target_valence": (0.4, 0.7),
        "target_energy": (0.4, 0.6),
        "target_instrumentalness": (0.5, 1.0)
    },
    "12:00_peak_energy": {
        "seed_genres": ["hip-hop", "funk rap", "trap"],
        "target_valence": (0.6, 0.9),
        "target_energy": (0.7, 1.0),
        "target_tempo": (90, 120)
    },
    "13:30_post_lunch_rest": {
        "seed_genres": ["jazz", "neo soul", "r&b"],
        "target_valence": (0.4, 0.6),
        "target_energy": (0.3, 0.5),
        "target_acousticness": (0.5, 0.8)
    },
    "15:00_mid_energy_variety": {
        "seed_genres": ["soft rock", "chill rock", "dream rock"],
        "target_valence": (0.5, 0.7),
        "target_energy": (0.5, 0.7),
        "target_danceability": (0.4, 0.6)
    },
    "16:30_afternoon_excitement": {
        "seed_genres": ["reggaeton", "indie dance", "funk"],
        "target_valence": (0.7, 0.9),
        "target_energy": (0.6, 0.8),
        "target_danceability": (0.6, 0.9)
    },
    "18:00_work_release": {
        "seed_genres": ["rock’n’roll", "garage rock", "alt rock"],
        "target_valence": (0.6, 0.8),
        "target_energy": (0.7, 0.9),
        "target_tempo": (100, 130)
    },
    "19:30_emotional_evening": {
        "seed_genres": ["melodic rap", "conscious hip-hop", "lo-fi r&b"],
        "target_valence": (0.4, 0.6),
        "target_energy": (0.3, 0.5),
        "target_instrumentalness": (0.3, 0.6)
    },
    "21:00_calm_night": {
        "seed_genres": ["ambient", "piano", "dream pop"],
        "target_valence": (0.3, 0.5),
        "target_energy": (0.2, 0.4),
        "target_acousticness": (0.7, 1.0)
    },
    "22:30_end_day_emotional": {
        "seed_genres": ["classical", "instrumental ballads", "acoustic piano"],
        "target_valence": (0.3, 0.5),
        "target_energy": (0.1, 0.3),
        "target_instrumentalness": (0.8, 1.0)
    },
}

def get_spotify_recommendations_params(mood_key, force_genre_category=None, current_actual_mood_key=None):

    base_mood_data = None
    final_mood_key_for_logging = mood_key

    if force_genre_category == "hiphop":
        final_mood_key_for_logging = f"forced_hiphop_for_actual_mood_{current_actual_mood_key or mood_key}"
    
        if current_actual_mood_key and ('energetic' in current_actual_mood_key or 'upbeat' in current_actual_mood_key or 'focus' in current_actual_mood_key or 'party' in current_actual_mood_key):
            base_mood_data = MOOD_MAPPING.get("quota_hiphop_upbeat")
        else:
            base_mood_data = MOOD_MAPPING.get("quota_hiphop_chill")
    elif force_genre_category == "rock":
        final_mood_key_for_logging = f"forced_rock_for_actual_mood_{current_actual_mood_key or mood_key}"
        if current_actual_mood_key and ('energetic' in current_actual_mood_key or 'upbeat' in current_actual_mood_key or 'focus' in current_actual_mood_key or 'party' in current_actual_mood_key or 'dramatic' in current_actual_mood_key):
            base_mood_data = MOOD_MAPPING.get("quota_rock_energetic")
        else:
            base_mood_data = MOOD_MAPPING.get("quota_rock_mellow")
    
    if not base_mood_data: 
        base_mood_data = MOOD_MAPPING.get(mood_key.lower(), MOOD_MAPPING.get("neutral_calm"))

    raw_seed_genres = base_mood_data.get("seed_genres", ["pop"]) 
    
    
    valid_seed_genres = [genre for genre in raw_seed_genres if genre in PLAYLIST_GENRES]

    if not valid_seed_genres:
        logging.warning(f"No valid seed genres found for mood '{final_mood_key_for_logging}' after filtering. Trying broad fallback.")
        fallback_options = []
        if force_genre_category == "hiphop": fallback_options = [g for g in ["hip hop", "rap"] if g in PLAYLIST_GENRES]
        elif force_genre_category == "rock": fallback_options = [g for g in ["rock", "hard rock", "classic rock"] if g in PLAYLIST_GENRES]
        
        if not fallback_options: 
            fallback_options = [g for g in ["pop", "rock", "indie"] if g in PLAYLIST_GENRES] 

        if not fallback_options and PLAYLIST_GENRES:
             valid_seed_genres = [random.choice(PLAYLIST_GENRES)] 
        elif not fallback_options: 
            valid_seed_genres = ["pop"] 
        else:
            valid_seed_genres = fallback_options

    num_seeds_to_pick = min(len(valid_seed_genres), 5)
    chosen_seeds = random.sample(valid_seed_genres, num_seeds_to_pick) if valid_seed_genres else ["pop"]


    params = {
        "seed_genres": ",".join(chosen_seeds),
        "limit": 1 
    }

 
    for feature in ["valence", "energy", "danceability", "tempo", "acousticness", "instrumentalness", "liveness", "speechiness"]:
        target_feature_key = f"target_{feature}"
        if target_feature_key in base_mood_data:
            feature_value_or_range = base_mood_data[target_feature_key]
            if isinstance(feature_value_or_range, tuple) and len(feature_value_or_range) == 2:
                params[target_feature_key] = random.uniform(*feature_value_or_range)
            else: 
                params[target_feature_key] = feature_value_or_range
    
    logging.debug(f"Spotify recommendation params for mood '{final_mood_key_for_logging}': {params}")
    return params

    # Adjust mood mapping based on time and day of the week
    now = datetime.now()
    hour = now.hour
    weekday = now.weekday()

    # Map time-based moods
    if 9 <= hour < 10:
        mood_key = "09:00_start_day_warm"
    elif 10 <= hour < 12:
        mood_key = "10:30_focus_motivation"
    elif 12 <= hour < 13:
        mood_key = "12:00_peak_energy"
    elif 13 <= hour < 15:
        mood_key = "13:30_post_lunch_rest"
    elif 15 <= hour < 16:
        mood_key = "15:00_mid_energy_variety"
    elif 16 <= hour < 18:
        mood_key = "16:30_afternoon_excitement"
    elif 18 <= hour < 19:
        mood_key = "18:00_work_release"
    elif 19 <= hour < 21:
        mood_key = "19:30_emotional_evening"
    elif 21 <= hour < 22:
        mood_key = "21:00_calm_night"
    elif 22 <= hour < 24:
        mood_key = "22:30_end_day_emotional"
