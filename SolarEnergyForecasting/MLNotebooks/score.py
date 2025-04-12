import json
import joblib
import numpy as np
import pandas as pd

def init():
    global model
    model_path = 'solar_forecast_rf_model.joblib'
    model = joblib.load(model_path)

def run(raw_data):
    try:
        # Parse input data
        data = json.loads(raw_data)
        location = data.get('location')
        forecast_days = data.get('forecast_days', 7)
        
        # Generate timestamps for the forecast period
        timestamps = []
        forecast_values = []
        
        # Current time as starting point
        start_time = pd.Timestamp.now().floor('H')
        
        for i in range(forecast_days * 24):
            current_time = start_time + pd.Timedelta(hours=i)
            
            # Extract features
            hour = current_time.hour
            month = current_time.month
            
            # Create cyclical time features
            hour_sin = np.sin(2 * np.pi * hour / 24)
            hour_cos = np.cos(2 * np.pi * hour / 24)
            month_sin = np.sin(2 * np.pi * month / 12)
            month_cos = np.cos(2 * np.pi * month / 12)
            
            # Get weather data for this timestamp
            # In a production system, this would come from a weather API or database
            # For now, we'll use placeholder values
            temperature = 25  # Placeholder
            cloud_cover = 30  # Placeholder
            wind_speed = 5    # Placeholder
            
            # Create feature vector
            features = [temperature, cloud_cover, wind_speed, 
                        hour_sin, hour_cos, month_sin, month_cos]
            
            # Make prediction
            prediction = model.predict([features])[0]
            
            # No production at night (simplification)
            if hour < 6 or hour > 18:
                prediction = 0
                
            # Add to results
            timestamps.append(current_time.isoformat())
            forecast_values.append(float(prediction))
        
        # Return the forecast
        return json.dumps({
            "timestamps": timestamps,
            "forecast_values": forecast_values
        })
        
    except Exception as e:
        return json.dumps({"error": str(e)})