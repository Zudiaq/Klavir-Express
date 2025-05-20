import logging
from config import DEBUG_MODE
from datetime import datetime

logging.basicConfig(
    level=logging.DEBUG if DEBUG_MODE else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def map_weather_to_mood(weather):
    """
    Optimized mapping of weather, time, weekday, and month to mood using mapping tables and helper functions.
    Now includes time-slot-based genre/mood mapping for 1.5-hour intervals between 10:00 and 22:00.
    """
    if not weather:
        logging.warning("No weather data provided, defaulting to 'nostalgic' mood")
        return "nostalgic"

    main = weather.get('main', '').lower()
    desc = weather.get('description', '').lower()
    temp = weather.get('temp', 20)
    humidity = weather.get('humidity', 50)
    wind_speed = weather.get('wind_speed', 0)
    air_quality = weather.get('air_quality', 'good').lower()
    user_preferences = weather.get('user_preferences', {})

    now = datetime.now()
    hour = now.hour
    minute = now.minute
    weekday = now.weekday()
    month = now.month
    season = (
        'winter' if month in [12,1,2] else
        'spring' if month in [3,4,5] else
        'summer' if month in [6,7,8] else
        'autumn'
    )

    # Define 1.5-hour slots from 10:00 to 22:00
    time_slots = [
        (10, 0), (11, 30), (13, 0), (14, 30), (16, 0), (17, 30), (19, 0), (20, 30)
    ]
    slot_labels = [
        'slot1', 'slot2', 'slot3', 'slot4', 'slot5', 'slot6', 'slot7', 'slot8'
    ]
    # Map each slot to a genre/mood profile
    slot_moods = {
        'slot1': {'mood': 'energetic', 'genre': 'pop'},           # 10:00-11:29
        'slot2': {'mood': 'happy', 'genre': 'indie'},             # 11:30-12:59
        'slot3': {'mood': 'uplifting', 'genre': 'dance'},         # 13:00-14:29
        'slot4': {'mood': 'focused', 'genre': 'hip-hop'},         # 14:30-15:59 
        'slot5': {'mood': 'playful', 'genre': 'funk'},            # 16:00-17:29
        'slot6': {'mood': 'romantic', 'genre': 'rap'},            # 17:30-18:59 
        'slot7': {'mood': 'chill', 'genre': 'chill'},             # 19:00-20:29
        'slot8': {'mood': 'calm', 'genre': 'acoustic'},           # 20:30-21:59
    }
    # Determine current slot
    slot_idx = None
    for i, (h, m) in enumerate(time_slots):
        slot_start = h * 60 + m
        slot_end = slot_start + 89  # 1.5 hours = 90 minutes - 1
        now_min = hour * 60 + minute
        if slot_start <= now_min <= slot_end:
            slot_idx = i
            break
    # Default to night if outside 10:00-22:00
    if slot_idx is not None:
        slot_label = slot_labels[slot_idx]
        slot_mood = slot_moods[slot_label]['mood']
        return slot_mood
    # Night time (22:00-09:59)
    if hour >= 22 or hour < 10:
        return 'soothing'  # or 'calm', 'sleep', etc.

    tod_map = [
        (range(5,8), 'dawn'),
        (range(8,12), 'morning'),
        (range(12,15), 'noon'),
        (range(15,18), 'afternoon'),
        (range(18,21), 'evening'),
    ]
    tod = next((label for rng, label in tod_map if hour in rng), 'night')
    is_weekend = weekday in [4,5]

    weekend_map = {
        ('clear', 'morning'): 'playful',
        ('clear', 'noon'): 'playful',
        ('clear', 'evening'): 'romantic',
        ('rain', None): 'relaxed',
        ('drizzle', None): 'relaxed',
        ('clouds', 'night'): 'thoughtful',
        ('snow', None): 'cozy',
    }
    weekday_map = {
        ('clear', 'morning'): 'energetic',
        ('clear', 'noon'): 'happy',
        ('clear', 'evening'): 'romantic',
        ('clear', 'night'): 'calm',
        ('clouds', 'morning'): 'thoughtful',
        ('clouds', 'evening'): 'melancholic',
        ('rain', 'morning'): 'nostalgic',
        ('rain', 'evening'): 'mysterious',
        ('drizzle', 'morning'): 'nostalgic',
        ('drizzle', 'evening'): 'mysterious',
    }
    seasonal_map = {
        ('spring', 'clear', 'afternoon'): 'uplifting',
        ('summer', 'clear', 'noon'): 'joyful',
        ('autumn', 'clouds', None): 'contemplative',
        ('winter', 'snow', None): 'cozy',
        (1, 'clear', 'morning'): 'refreshed',
        (12, 'clouds', 'night'): 'solemn',
    }
    clear_map = {
        'dawn': 'serene',
        'morning': 'energetic',
        'noon': 'happy',
        'afternoon': 'uplifting',
        'evening': 'romantic',
        'night': 'calm',
    }
    rain_map = {
        'heavy': 'dramatic',
        'storm': 'dramatic',
        'light': 'relaxed',
        'night': 'mysterious',
        'morning': 'nostalgic',
    }
    clouds_map = {
        'overcast': 'thoughtful',
        'broken': 'melancholic',
        'morning': 'focused',
        'afternoon': 'contemplative',
        'evening': 'melancholic',
        'night': 'neutral',
    }
    snow_map = {
        'cold': 'cozy',
        'morning': 'refreshed',
        'evening': 'tranquil',
        'default': 'romantic',
    }
    wind_map = [
        (20, 'adventurous'),
        (15, 'free-spirited'),
        (10, 'restless'),
    ]
    mist_map = {
        'night': 'mysterious',
        'morning': 'serene',
        'default': 'contemplative',
    }

    def get_from_map(map_obj, key1, key2=None):
        if key2 is not None and (key1, key2) in map_obj:
            return map_obj[(key1, key2)]
        if (key1, None) in map_obj:
            return map_obj[(key1, None)]
        return None

    if is_weekend:
        mood = get_from_map(weekend_map, main, tod)
        if mood:
            return mood
    else:
        mood = get_from_map(weekday_map, main, tod)
        if mood:
            return mood

    # Seasonal/monthly moods
    mood = get_from_map(seasonal_map, season, main, tod)
    if not mood:
        mood = get_from_map(seasonal_map, month, main, tod)
    if mood:
        return mood

    # Generalized mapping
    if main == 'clear':
        return clear_map.get(tod, 'neutral')
    elif main in ['rain','drizzle','thunderstorm']:
        if any(x in desc for x in ['heavy','storm']) or wind_speed > 15:
            return rain_map['heavy']
        elif 'light' in desc or humidity > 70:
            return rain_map['light']
        elif tod == 'night':
            return rain_map['night']
        elif tod == 'morning':
            return rain_map['morning']
        else:
            return 'content'
    elif main == 'clouds':
        if 'overcast' in desc:
            return clouds_map['overcast']
        elif 'broken' in desc:
            return clouds_map['broken']
        elif tod in clouds_map:
            return clouds_map[tod]
        else:
            return 'content'
    elif main == 'snow':
        if temp < -5:
            return snow_map['cold']
        elif tod in snow_map:
            return snow_map[tod]
        else:
            return snow_map['default']
    elif main == 'wind' or wind_speed > 10:
        for speed, mood in wind_map:
            if wind_speed > speed:
                return mood
        return 'moody'
    elif main in ['mist','fog','haze']:
        if tod in mist_map:
            return mist_map[tod]
        else:
            return mist_map['default']

    # Temperature extremes
    if temp > 35:
        return 'exhausted'
    elif temp < 0:
        return 'solemn'
    elif temp < 8:
        return 'nostalgic'

    if air_quality in ['poor','very poor']:
        return 'cautious'

    if user_preferences.get('likes_rain') and main in ['rain','drizzle']:
        return 'content'

    if 15 <= temp <= 25 and humidity < 70 and wind_speed < 12:
        if tod in ['morning','noon']:
            return 'content'
        elif tod == 'evening':
            return 'romantic'
        else:
            return 'neutral'
    if 25 < temp <= 32 and humidity < 60:
        return 'joyful'
    if 10 <= temp < 15:
        return 'playful'
    logging.debug("No specific mood mapping found, defaulting to 'neutral'")
    return 'neutral'
