# mood.py
import logging
from datetime import datetime
import os

DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"

logging.basicConfig(
    level=logging.DEBUG if DEBUG_MODE else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def determine_detailed_time_of_day(hour):
    if 5 <= hour < 7: return 'dawn'
    elif 7 <= hour < 10: return 'mid_morning'
    elif 10 <= hour < 12: return 'late_morning'
    elif 12 <= hour < 14: return 'midday'
    elif 14 <= hour < 17: return 'afternoon'
    elif 17 <= hour < 19: return 'early_evening'
    elif 19 <= hour < 22: return 'late_evening'
    else: return 'night'

def determine_season(month):
    if month in [3, 4, 5]: return 'spring'
    elif month in [6, 7, 8]: return 'summer'
    elif month in [9, 10, 11]: return 'autumn'
    else: return 'winter'

def map_weather_to_mood(weather_data): 
    if not weather_data:
        logging.warning("No weather data provided, defaulting to 'neutral_calm'")
        return "neutral_calm"

    main_condition = weather_data.get('main', '').lower()
    description = weather_data.get('description', '').lower()
    temp = weather_data.get('temp', 20)

    now = datetime.now() 
    hour = now.hour
    day_of_week = now.weekday() 
    month = now.month

    time_slot = determine_detailed_time_of_day(hour)
    current_season = determine_season(month)
    is_weekend = day_of_week >= 4  

    mood = "neutral_ambient"  

    

    if 'clear' in main_condition:
        if current_season == 'spring':
            mood = 'spring_uplifting_energetic' if time_slot in ['mid_morning', 'late_morning', 'afternoon'] else 'spring_peaceful_evening'
            if is_weekend: mood = 'spring_weekend_joyful'
        elif current_season == 'summer':
            mood = 'summer_bright_energetic' if time_slot not in ['night', 'late_evening'] else 'summer_warm_night_chill'
            if temp > 30 : mood = 'summer_hot_lazy' if time_slot in ['midday', 'afternoon'] else mood
            if is_weekend and time_slot not in ['night', 'late_evening']: mood = 'summer_weekend_fun'
        elif current_season == 'autumn':
            mood = 'autumn_crisp_reflective' if time_slot in ['mid_morning', 'afternoon'] else 'autumn_cozy_evening'
            if time_slot == 'early_evening': mood = 'autumn_golden_hour_folk'
        elif current_season == 'winter':
            mood = 'winter_bright_calm' if time_slot in ['mid_morning', 'late_morning'] else 'winter_still_night'
            if temp < 5: mood = 'winter_cold_introspective'

    elif 'clouds' in main_condition:
        mood = 'cloudy_thoughtful_daydream'
        if 'overcast' in description: mood = 'overcast_melancholic_pensive'
        if current_season in ['autumn', 'winter']: mood = 'cloudy_autumn_brooding'
        if time_slot in ['late_evening', 'night']: mood = 'cloudy_night_mellow'

    elif 'rain' in main_condition or 'drizzle' in main_condition:
        mood = 'rainy_nostalgic_reading'
        if 'light rain' in description: mood = 'light_rain_cozy_acoustic'
        if 'thunderstorm' in description: mood = 'stormy_dramatic_epic'
        if time_slot in ['late_evening', 'night']: mood = 'rainy_night_blues_jazz'
        if is_weekend: mood = 'rainy_weekend_chill_lofi'

    elif 'snow' in main_condition:
        mood = 'snowy_wonderland_magical'
        if is_weekend: mood = 'snowy_weekend_cozy_fireplace'
        if time_slot in ['night']: mood = 'snowy_silent_night_ambient'

    elif 'mist' in main_condition or 'fog' in main_condition:
        mood = 'foggy_mysterious_atmospheric'
        if time_slot in ['dawn', 'night']: mood = 'misty_ethereal_dreamlike'


    if day_of_week == 0 and time_slot in ['dawn', 'mid_morning']: 
        mood = 'monday_morning_focus_upbeat'
    elif day_of_week == 4 and time_slot in ['early_evening', 'late_evening']: 
        mood = 'friday_evening_party_celebration'
    elif day_of_week == 5 and time_slot in ['mid_morning', 'afternoon']: 
        mood = 'saturday_adventure_exploration'

    logging.info(f"Weather: {main_condition} ({description}), Temp: {temp}°C, Time: {time_slot} ({hour}h), Season: {current_season}, Day: {day_of_week}. Determined mood: {mood}")
    return mood
