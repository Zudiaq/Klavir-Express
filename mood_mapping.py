# mood_mapping.py
import random
import logging
import os

DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"

logging.basicConfig(
    level=logging.DEBUG if DEBUG_MODE else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

PLAYLIST_GENRES = [
    "classic rock", "psychedelic rock", "progressive rock", "art rock", "album rock",
    "hard rock", "blues rock", "alternative rock", "indie rock", "indie pop", "dream pop",
    "shoegaze", "post-punk", "new wave", "gothic rock", "darkwave", "grunge", "britpop",
    "punk rock", "pop punk", "emo", "alternative metal", "nu metal", "heavy metal",
    "symphonic metal", "gothic metal", "doom metal", "progressive metal", "neue deutsche härte",
    "new age", "ambient", "trip hop", "downtempo", "electronica", "synth-pop", "industrial",
    "techno", "house", "trance", "eurodance", "dubstep", "drum and bass", "synthwave",
    "pop", "traditional pop", "vocal jazz", "disco", "dance pop", "electropop", "art pop",
    "bedroom pop", "latin pop",
    "hip hop", "g-funk", "conscious hip hop", "alternative hip hop", "jazz rap", "trap",
    "cloud rap", "emo rap", "pop rap",
    "soul", "funk", "motown", "neo soul", "alternative r&b",
    "folk", "contemporary folk", "singer-songwriter", "americana", "country", "country rock",
    "jazz", "blues",
    "celtic", "latin alternative", "reggae", "bollywood", "j-pop", "j-rock", "anime score",
    "russian post-punk", "chanson", "city pop",
    "classical", "orchestral", "film score", "video game music", "minimalism"
]

MOOD_MAPPING = {

    "neutral_calm": {
        "seed_genres": ["ambient", "chillout", "lo-fi beats", "acoustic", "classical piano"],
        "target_valence": (0.3, 0.6), "target_energy": (0.1, 0.4), "target_tempo": (60, 90)
    },
    "spring_uplifting_energetic": {
        "seed_genres": ["indie pop", "britpop", "power pop", "jangle pop", "folk pop"],
        "target_valence": (0.6, 0.9), "target_energy": (0.6, 0.8), "target_tempo": (110, 140)
    },
    "spring_peaceful_evening": {
        "seed_genres": ["acoustic", "singer-songwriter", "chamber folk", "new age"],
        "target_valence": (0.4, 0.7), "target_energy": (0.2, 0.5)
    },
    "summer_bright_energetic": {
        "seed_genres": ["pop rock", "surf rock", "funk", "dance pop", "reggae fusion"],
        "target_valence": (0.7, 1.0), "target_energy": (0.7, 1.0), "target_danceability": (0.6, 0.9)
    },
    "summer_warm_night_chill": {
        "seed_genres": ["alternative r&b", "soul", "downtempo", "trip hop", "chillwave"],
        "target_valence": (0.4, 0.7), "target_energy": (0.3, 0.6)
    },
    "autumn_crisp_reflective": {
        "seed_genres": ["folk rock", "americana", "indie folk", "post-rock", "singer-songwriter"],
        "target_valence": (0.3, 0.6), "target_energy": (0.3, 0.6), "target_acousticness": (0.6, 1.0)
    },
    "rainy_nostalgic_reading": {
        "seed_genres": ["jazz piano", "classical", "sad indie", "shoegaze", "slowcore", "folk"],
        "target_valence": (0.2, 0.5), "target_energy": (0.1, 0.4)
    },
     "rainy_night_blues_jazz": {
        "seed_genres": ["jazz noir", "soul jazz", "vocal jazz", "blues", "dark jazz"],
        "target_valence": (0.3, 0.6), "target_energy": (0.2, 0.5)
    },
    "monday_morning_focus_upbeat":{
        "seed_genres": ["electronic", "idm", "progressive house", "focus beats", "indie dance", "synth-pop"],
        "target_valence": (0.5, 0.8), "target_energy": (0.6, 0.9), "target_instrumentalness": (0.3, 0.8) # Instrumentalness could be higher
    },
    "friday_evening_party_celebration":{
        "seed_genres": ["dance pop", "house", "funk", "disco", "80s pop", "new wave", "pop rap"],
        "target_valence": (0.7, 1.0), "target_energy": (0.7, 1.0), "target_danceability": (0.7, 1.0)
    },
 
    "quota_hiphop_upbeat": {
        "seed_genres": ["hip hop", "trap", "g-funk", "pop rap", "conscious hip hop", "east coast hip hop", "west coast hip hop"],
        "target_valence": (0.6, 0.9), "target_energy": (0.6, 0.9), "target_danceability": (0.5, 0.8)
    },
    "quota_hiphop_chill": {
        "seed_genres": ["lo-fi hip hop", "jazz rap", "alternative hip hop", "cloud rap", "abstract hip hop", "downtempo hip hop"],
        "target_valence": (0.3, 0.6), "target_energy": (0.2, 0.5)
    },
    "quota_rock_energetic": { # "Rock and Roll and similar"
        "seed_genres": ["hard rock", "classic rock", "punk rock", "garage rock", "alternative rock", "glam rock", "heavy metal", "rock-and-roll"],
        "target_valence": (0.5, 1.0), "target_energy": (0.7, 1.0)
    },
    "quota_rock_mellow": {
        "seed_genres": ["soft rock", "acoustic rock", "blues rock", "folk rock", "psychedelic rock", "post-rock", "art rock"],
        "target_valence": (0.3, 0.7), "target_energy": (0.3, 0.6)
    },
}

def get_spotify_recommendations_params(mood_key, force_genre_category=None, current_actual_mood_key=None):
    """
    مود ورودی را به پارامترهای پیشنهادی اسپاتیفای تبدیل می‌کند.
    همچنین می‌تواند برای برآورده کردن سهمیه، انتخاب از یک دسته ژانر خاص را اجبار کند.
    """
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
