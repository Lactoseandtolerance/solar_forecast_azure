import requests
import json
import datetime

# OpenWeatherMap API key
api_key = "db5789f6264a997c47c8f42349cd8ae8"

# Define locations for data collection
locations = [
    {"name": "solar_farm_1", "lat": 40.7128, "lon": -74.0060},  # New York
    {"name": "solar_farm_2", "lat": 34.0522, "lon": -118.2437}  # Los Angeles
]

# Current timestamp
utc_timestamp = datetime.datetime.utcnow().replace(
    tzinfo=datetime.timezone.utc).isoformat()
print(f"Running weather data collection at {utc_timestamp}")

# Collect data for each location
for location in locations:
    # Get current weather data
    weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={location['lat']}&lon={location['lon']}&appid={api_key}&units=metric"
    weather_response = requests.get(weather_url)
    current_weather = weather_response.json()
    
    # Get weather forecast data
    forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={location['lat']}&lon={location['lon']}&appid={api_key}&units=metric"
    forecast_response = requests.get(forecast_url)
    forecast_data = forecast_response.json()
    
    # Extract relevant features
    data = {
        "timestamp": utc_timestamp,
        "location": location["name"],
        "latitude": location["lat"],
        "longitude": location["lon"],
        "current": {
            "temperature": current_weather.get("main", {}).get("temp"),
            "clouds": current_weather.get("clouds", {}).get("all"),
            "weather_description": current_weather.get("weather", [{}])[0].get("description"),
            "wind_speed": current_weather.get("wind", {}).get("speed")
        },
        "forecast": forecast_data.get("list", [])[:5]  # Just first 5 periods
    }
    
    # Print to console (instead of saving to blob)
    print(f"\nData for {location['name']}:")
    print(json.dumps(data["current"], indent=2))
    print(f"Forecast sample ({len(forecast_data.get('list', []))} periods):")
    for i, forecast in enumerate(data["forecast"]):
        print(f"  Period {i+1}: {forecast.get('dt_txt', '')} - {forecast.get('main', {}).get('temp')}°C, {forecast.get('weather', [{}])[0].get('description', '')}")