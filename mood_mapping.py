# ==========================
# Mood Mapping Dataset
# ==========================
import random
import logging

# Default fallback genres
PLAYLIST_GENRES = ["pop", "rock", "indie", "hip-hop", "jazz"]

# Define mood mapping with diverse genres
MOOD_MAPPING = {
    "energetic": {
        "description": "Bright, sunny day with moderate temperature and low humidity",
        "seed_genres": ["pop", "dance", "rock", "edm", "house"],
        "target_valence": (0.7, 1.0),
        "target_energy": (0.8, 1.0)
    },
    "happy": {
        "description": "Clear sky with comfortable temperature",
        "seed_genres": ["indie-pop", "pop", "britpop", "dance-pop"],
        "target_valence": (0.6, 1.0),
        "target_energy": (0.6, 0.9)
    },
    "calm": {
        "description": "Clear sky with mild temperature",
        "seed_genres": ["ambient", "chill", "acoustic", "piano"],
        "target_valence": (0.4, 0.7),
        "target_energy": (0.2, 0.5)
    },
    "thoughtful": {
        "description": "Cloudy day with cool temperature",
        "seed_genres": ["indie", "folk", "singer-songwriter", "post-rock"],
        "target_valence": (0.3, 0.6),
        "target_energy": (0.3, 0.6)
    },
    "relaxed": {
        "description": "Light rain with good visibility",
        "seed_genres": ["jazz", "lofi", "bossa-nova", "soul"],
        "target_valence": (0.4, 0.7),
        "target_energy": (0.2, 0.5)
    },
    "romantic": {
        "description": "Pleasant evening with clear skies",
        "seed_genres": ["soul", "r-n-b", "jazz", "soft-rock"],
        "target_valence": (0.5, 0.8),
        "target_energy": (0.3, 0.6)
    },
    "hiphop": {
        "description": "Dynamic and rhythmic mood for hip-hop or rap",
        "seed_genres": ["hip-hop", "rap", "trap", "alternative-hip-hop"],
        "target_valence": (0.5, 0.8),
        "target_energy": (0.6, 1.0)
    },
    "rock": {
        "description": "High-energy mood for rock and roll",
        "seed_genres": ["rock", "hard-rock", "classic-rock", "punk-rock"],
        "target_valence": (0.6, 1.0),
        "target_energy": (0.7, 1.0)
    },
    # Add more moods as needed
}

def get_spotify_recommendations_params(mood):
    """
    Convert a mood string to Spotify recommendation parameters.
    """
    mood_data = MOOD_MAPPING.get(mood.lower(), MOOD_MAPPING.get("neutral"))
    genres = mood_data["seed_genres"]
    valid_genres = [genre for genre in genres if genre in PLAYLIST_GENRES]
    if not valid_genres:
        valid_genres = ["pop", "indie", "rock"]  # Fallback genres
    params = {
        "seed_genres": ",".join(valid_genres[:5]),
        "target_valence": random.uniform(*mood_data["target_valence"]),
        "target_energy": random.uniform(*mood_data["target_energy"]),
        "limit": 1
    }
    return params
