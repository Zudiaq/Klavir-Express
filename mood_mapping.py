# Mood mapping dataset for weather-based music recommendations
import random

MOOD_MAPPING = {
    "energetic": {
        "description": "Bright, sunny day with moderate temperature and low humidity",
        "seed_genres": ["pop", "dance", "electronic", "edm", "house"],
        "target_valence": (0.5, 1.0),
        "target_energy": (0.6, 1.0)
    },
    "happy": {
        "description": "Clear sky with comfortable temperature",
        "seed_genres": ["happy", "pop", "indie-pop", "summer"],
        "target_valence": (0.5, 1.0),
        "target_energy": (0.5, 0.9)
    },
    "calm": {
        "description": "Clear sky with mild temperature",
        "seed_genres": ["chill", "ambient", "acoustic", "piano"],
        "target_valence": (0.3, 0.7),
        "target_energy": (0.1, 0.5)
    },
    "thoughtful": {
        "description": "Clear but cool day, possibly with some clouds",
        "seed_genres": ["indie", "folk", "singer-songwriter"],
        "target_valence": (0.2, 0.7),
        "target_energy": (0.2, 0.6)
    },
    "relaxed": {
        "description": "Light rain with good visibility",
        "seed_genres": ["chill", "jazz", "lofi", "bossa-nova"],
        "target_valence": (0.3, 0.7),
        "target_energy": (0.0, 0.5)
    },
    "dramatic": {
        "description": "Heavy rain, thunderstorm, or intense weather conditions",
        "seed_genres": ["classical", "epic", "soundtrack", "orchestral", "cinematic", "opera", "world-music"],
        "target_valence": (0.1, 0.6),
        "target_energy": (0.4, 1.0)
    },
    "nostalgic": {
        "description": "Moderate rain or cloudy conditions",
        "seed_genres": ["indie", "singer-songwriter", "folk", "acoustic", "sad", "emo", "alt-rock"],
        "target_valence": (0.1, 0.6),
        "target_energy": (0.2, 0.7)
    },
    "romantic": {
        "description": "Partly cloudy with pleasant temperature or light snow",
        "seed_genres": ["romance", "r-n-b", "soul", "jazz", "pop", "blues", "gospel"],
        "target_valence": (0.3, 0.8),
        "target_energy": (0.2, 0.7)
    },
    "melancholic": {
        "description": "Mostly cloudy with cool temperature",
        "seed_genres": ["sad", "indie", "alt-rock", "emo", "melancholy", "grunge", "post-punk"],
        "target_valence": (0.0, 0.5),
        "target_energy": (0.1, 0.7)
    },
    "cozy": {
        "description": "Very cold with snow",
        "seed_genres": ["acoustic", "indie-folk", "coffee-house", "piano", "winter", "chamber", "baroque"],
        "target_valence": (0.3, 0.7),
        "target_energy": (0.1, 0.5)
    },
    "adventurous": {
        "description": "Very windy conditions",
        "seed_genres": ["rock", "alt-rock", "indie-rock", "folk-rock", "road-trip", "garage", "psychedelic"],
        "target_valence": (0.3, 0.9),
        "target_energy": (0.5, 1.0)
    },
    "free-spirited": {
        "description": "Moderately windy with clear skies",
        "seed_genres": ["indie", "folk", "indie-pop", "alt-rock", "singer-songwriter", "americana", "roots"],
        "target_valence": (0.4, 0.9),
        "target_energy": (0.3, 0.9)
    },
    "mysterious": {
        "description": "Foggy or misty conditions",
        "seed_genres": ["ambient", "electronic", "trip-hop", "downtempo", "experimental", "glitch", "idm"],
        "target_valence": (0.2, 0.7),
        "target_energy": (0.2, 0.8)
    },
    "exhausted": {
        "description": "Hot and humid conditions",
        "seed_genres": ["chill", "ambient", "sleep", "lo-fi", "minimal", "drone", "slowcore"],
        "target_valence": (0.1, 0.6),
        "target_energy": (0.0, 0.5)
    },
    "cautious": {
        "description": "Poor air quality or potentially hazardous conditions",
        "seed_genres": ["ambient", "classical", "piano", "meditation", "minimal", "neoclassical", "avant-garde"],
        "target_valence": (0.2, 0.7),
        "target_energy": (0.1, 0.6)
    },
    "content": {
        "description": "Light rain for someone who enjoys rainy weather",
        "seed_genres": ["rainy-day", "jazz", "coffee-house", "acoustic", "piano", "bossa-nova", "lounge"],
        "target_valence": (0.3, 0.8),
        "target_energy": (0.1, 0.7)
    },
    "joyful": {
        "description": "Warm, pleasant day after a period of good mood",
        "seed_genres": ["happy", "pop", "dance", "summer", "feel-good", "electro-pop", "synth-pop"],
        "target_valence": (0.5, 1.0),
        "target_energy": (0.5, 1.0)
    },
    "neutral": {
        "description": "Average weather conditions with no strong characteristics",
        "seed_genres": ["pop", "indie", "alt-rock", "chill", "acoustic", "soft-rock", "easy-listening"],
        "target_valence": (0.2, 0.8),
        "target_energy": (0.1, 0.9)
    },
    "uplifting": {
        "description": "Any weather that feels positive or hopeful",
        "seed_genres": ["pop", "indie", "dance", "happy", "folk", "electronic", "summer", "tropical"],
        "target_valence": (0.5, 1.0),
        "target_energy": (0.4, 1.0)
    },
    "moody": {
        "description": "Weather that is ambiguous, mixed, or hard to define",
        "seed_genres": ["indie", "alt-rock", "ambient", "trip-hop", "electronic", "chill", "experimental"],
        "target_valence": (0.2, 0.7),
        "target_energy": (0.1, 0.8)
    },
    "serene": {
        "description": "Clear sky at dawn or dusk with perfect temperature",
        "seed_genres": ["ambient", "chill", "classical", "piano", "meditation"],
        "target_valence": (0.5, 0.7),
        "target_energy": (0.1, 0.3)
    },
    "hopeful": {
        "description": "Clearing skies after rain or storm",
        "seed_genres": ["indie", "folk", "acoustic", "singer-songwriter", "inspirational"],
        "target_valence": (0.6, 0.8),
        "target_energy": (0.4, 0.6)
    },
    "awestruck": {
        "description": "Dramatic sunset or sunrise with spectacular colors",
        "seed_genres": ["post-rock", "ambient", "classical", "cinematic", "instrumental"],
        "target_valence": (0.5, 0.7),
        "target_energy": (0.5, 0.7)
    },
    "focused": {
        "description": "Stable, clear weather with moderate temperature",
        "seed_genres": ["focus", "electronic", "study", "minimal", "instrumental"],
        "target_valence": (0.4, 0.6),
        "target_energy": (0.3, 0.5)
    },
    "contemplative": {
        "description": "Overcast day with steady temperature",
        "seed_genres": ["ambient", "classical", "piano", "minimal", "contemporary"],
        "target_valence": (0.2, 0.7),
        "target_energy": (0.1, 0.6)
    },
    "restless": {
        "description": "Rapidly changing weather conditions or approaching storm",
        "seed_genres": ["electronic", "alt-rock", "indie-rock", "experimental", "industrial"],
        "target_valence": (0.3, 0.5),
        "target_energy": (0.6, 0.8)
    },
    "tranquil": {
        "description": "Still air with light cloud cover and comfortable temperature",
        "seed_genres": ["sleep", "ambient", "piano", "meditation", "classical"],
        "target_valence": (0.4, 0.6),
        "target_energy": (0.0, 0.2)
    },
    "refreshed": {
        "description": "Cool, crisp morning after rain",
        "seed_genres": ["acoustic", "indie-folk", "morning", "folk", "chill"],
        "target_valence": (0.6, 0.8),
        "target_energy": (0.3, 0.5)
    },
    "solemn": {
        "description": "Heavy, dark clouds with still air",
        "seed_genres": ["classical", "piano", "ambient", "contemporary", "minimal"],
        "target_valence": (0.1, 0.3),
        "target_energy": (0.2, 0.4)
    },
    "playful": {
        "description": "Mild temperature with light breeze and scattered clouds",
        "seed_genres": ["indie-pop", "pop", "funk", "disco", "happy"],
        "target_valence": (0.7, 0.9),
        "target_energy": (0.6, 0.8)
    }
}


def get_spotify_recommendations_params(mood):
    """
    Convert a mood string to Spotify recommendation parameters with added diversity.
    Args:
        mood (str): Mood string from weather mapping.
    Returns:
        dict: Parameters for Spotify recommendations API.
    """
    import logging
    default_params = {
        "seed_genres": "pop,rock,indie",
        "target_valence": 0.5,
        "target_energy": 0.5,
        "limit": 1
    }
    mood_data = MOOD_MAPPING.get(mood.lower(), MOOD_MAPPING.get("neutral"))
    shuffled_genres = random.sample(mood_data["seed_genres"], len(mood_data["seed_genres"]))
    verified_genres = [
        "acoustic", "afrobeat", "alt-rock", "alternative", "ambient", "blues",
        "chill", "classical", "club", "country", "dance", "deep-house", "disco",
        "drum-and-bass", "dubstep", "edm", "electro", "electronic", "folk",
        "funk", "garage", "gospel", "happy", "hard-rock", "hip-hop", "house",
        "indie", "indie-pop", "jazz", "k-pop", "latin", "metal", "new-age",
        "opera", "party", "piano", "pop", "r-n-b", "reggae", "reggaeton",
        "rock", "romance", "sad", "salsa", "sleep", "soul", "study", "summer",
        "techno", "trance", "trip-hop", "world-music"
    ]
    valid_genres = [genre for genre in shuffled_genres if genre in verified_genres]
    if not valid_genres:
        logging.warning(f"No valid Spotify genres found for mood '{mood}', using defaults")
        valid_genres = ["pop", "indie", "chill"]
    valid_genres = valid_genres[:5]
    params = {
        "seed_genres": ",".join(valid_genres),
        "limit": 1
    }
    range_keys = [k for k in mood_data.keys() if k.startswith("target_") and k != "seed_genres"]
    added = 0
    for key in range_keys:
        if added >= 2:
            break
        value = mood_data[key]
        if isinstance(value, tuple) and len(value) == 2:
            params[key] = value
            added += 1
    logging.debug(f"Generated Spotify recommendation parameters: {params}")
    return params
