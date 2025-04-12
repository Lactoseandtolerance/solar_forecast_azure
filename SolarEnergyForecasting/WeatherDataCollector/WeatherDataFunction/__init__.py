import datetime
import logging
import os
import json
import requests
import azure.functions as func
from azure.storage.blob import BlobServiceClient, BlobClient, ContentSettings

def main(mytimer: func.TimerRequest) -> None:
    utc_timestamp = datetime.datetime.utcnow().replace(
        tzinfo=datetime.timezone.utc).isoformat()
    
    if mytimer.past_due:
        logging.info('The timer is past due!')

    logging.info('Python timer trigger function ran at %s', utc_timestamp)
    
    # Get OpenWeatherMap API key from environment variable
    api_key = os.environ["OPENWEATHERMAP_API_KEY"]
    
    # Define locations for data collection (latitude, longitude)
    locations = [
        {"name": "solar_farm_1", "lat": 40.7128, "lon": -74.0060},  # Example: New York
        {"name": "solar_farm_2", "lat": 34.0522, "lon": -118.2437}  # Example: Los Angeles
    ]
    
    # Connect to blob storage
    connection_string = os.environ["AzureWebJobsStorage"]
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    container_name = "solar-data"
    
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
        
        # Extract relevant features for solar forecasting
        data = {
            "timestamp": utc_timestamp,
            "location": location["name"],
            "latitude": location["lat"],
            "longitude": location["lon"],
            "current": {
                "temperature": current_weather.get("main", {}).get("temp"),
                "clouds": current_weather.get("clouds", {}).get("all"),  # Cloud coverage in %
                "weather_description": current_weather.get("weather", [{}])[0].get("description"),
                "wind_speed": current_weather.get("wind", {}).get("speed")
            },
            "forecast": forecast_data.get("list", [])
        }
        
        # Save to blob storage
        date_str = datetime.datetime.utcnow().strftime("%Y-%m-%d")
        time_str = datetime.datetime.utcnow().strftime("%H-%M-%S")
        blob_name = f"{location['name']}/{date_str}/{time_str}.json"
        
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
        
        blob_client.upload_blob(
            json.dumps(data, indent=2),
            overwrite=True,
            content_settings=ContentSettings(content_type="application/json")
        )
        
        logging.info(f"Data for {location['name']} saved to {blob_name}")