import logging
from datetime import datetime

DEBUG_MODE = False

logging.basicConfig(
    level=logging.DEBUG if DEBUG_MODE else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def determine_time_of_day(hour):
    """
    Determine the time of day based on the hour.
    """
    if 5 <= hour < 8:
        return 'dawn'
    elif 8 <= hour < 12:
        return 'morning'
    elif 12 <= hour < 15:
        return 'noon'
    elif 15 <= hour < 18:
        return 'afternoon'
    elif 18 <= hour < 21:
        return 'evening'
    else:
        return 'night'

def determine_season(month):
    """
    Determine the season based on the month.
    """
    if month in [12, 1, 2]:
        return 'winter'
    elif month in [3, 4, 5]:
        return 'spring'
    elif month in [6, 7, 8]:
        return 'summer'
    else:
        return 'autumn'

def map_weather_to_mood(weather):
    """
    Map weather, time, and other parameters to a mood.
    """
    if not weather:
        logging.warning("No weather data provided, defaulting to 'neutral' mood")
        return "neutral"

    main = weather.get('main', '').lower()
    desc = weather.get('description', '').lower()
    temp = weather.get('temp', 20)
    humidity = weather.get('humidity', 50)
    wind_speed = weather.get('wind_speed', 0)

    now = datetime.now()
    hour = now.hour
    weekday = now.weekday()
    month = now.month

    time_of_day = determine_time_of_day(hour)
    season = determine_season(month)
    is_weekend = weekday in [4, 5]

    # Define mood mapping logic based on weather and time
    if main == 'clear':
        if time_of_day in ['morning', 'noon']:
            return 'energetic' if is_weekend else 'focused'
        elif time_of_day == 'evening':
            return 'romantic'
        else:
            return 'calm'
    elif main in ['rain', 'drizzle']:
        return 'nostalgic' if time_of_day in ['morning', 'afternoon'] else 'relaxed'
    elif main == 'clouds':
        return 'thoughtful' if time_of_day in ['morning', 'evening'] else 'melancholic'
    elif main == 'snow':
        return 'cozy'
    elif main in ['mist', 'fog']:
        return 'mysterious'
    elif temp > 30:
        return 'exhausted'
    elif temp < 5:
        return 'solemn'

    # Default mood
    return 'neutral'
