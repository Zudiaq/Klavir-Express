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
    is_weekend = day_of_week >= 5  

    mood = "neutral_calm"  # Default mood

    if 9 <= hour < 10:
        mood = "09:00_start_day_warm"
    elif 10 <= hour < 12:
        mood = "10:30_focus_motivation"
    elif 12 <= hour < 13:
        mood = "12:00_peak_energy"
    elif 13 <= hour < 15:
        mood = "13:30_post_lunch_rest"
    elif 15 <= hour < 16:
        mood = "15:00_mid_energy_variety"
    elif 16 <= hour < 18:
        mood = "16:30_afternoon_excitement"
    elif 18 <= hour < 19:
        mood = "18:00_work_release"
    elif 19 <= hour < 21:
        mood = "19:30_emotional_evening"
    elif 21 <= hour < 22:
        mood = "21:00_calm_night"
    elif 22 <= hour < 24:
        mood = "22:30_end_day_emotional"

    # Adjust mood based on weather conditions
    if 'clear' in main_condition:
        if current_season == 'spring':
            mood = 'spring_uplifting_energetic' if time_slot in ['mid_morning', 'late_morning', 'afternoon'] else 'spring_peaceful_evening'
        elif current_season == 'summer':
            mood = 'summer_bright_energetic' if time_slot not in ['night', 'late_evening'] else 'summer_warm_night_chill'
        elif current_season == 'autumn':
            mood = 'autumn_crisp_reflective' if time_slot in ['mid_morning', 'afternoon'] else 'autumn_cozy_evening'
        elif current_season == 'winter':
            mood = 'winter_bright_calm' if time_slot in ['mid_morning', 'late_morning'] else 'winter_still_night'

    elif 'clouds' in main_condition:
        mood = 'cloudy_thoughtful_daydream'
        if 'overcast' in description: mood = 'overcast_melancholic_pensive'

    elif 'rain' in main_condition or 'drizzle' in main_condition:
        mood = 'rainy_nostalgic_reading'
        if 'light rain' in description: mood = 'light_rain_cozy_acoustic'
        if 'thunderstorm' in description: mood = 'stormy_dramatic_epic'

    elif 'snow' in main_condition:
        mood = 'snowy_wonderland_magical'

    elif 'mist' in main_condition or 'fog' in main_condition:
        mood = 'foggy_mysterious_atmospheric'

    # Special adjustments for specific days
    if day_of_week == 0 and time_slot in ['dawn', 'mid_morning']: 
        mood = 'monday_morning_focus_upbeat'
    elif day_of_week == 4 and time_slot in ['early_evening', 'late_evening']: 
        mood = 'friday_evening_party_celebration'

    logging.info(f"Weather: {main_condition} ({description}), Temp: {temp}°C, Time: {time_slot} ({hour}h), Season: {current_season}, Day: {day_of_week}. Determined mood: {mood}")
    return mood
