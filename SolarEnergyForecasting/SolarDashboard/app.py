# app.py - Flask Web App for Solar Forecast Dashboard
from flask import Flask, render_template, request, jsonify
import os
import requests
import json
import pandas as pd
from datetime import datetime, timedelta
import plotly
import plotly.express as px
import plotly.graph_objects as go

app = Flask(__name__)

# Azure ML endpoint info
endpoint_url = os.environ.get("ML_ENDPOINT_URL")
api_key = os.environ.get("ML_API_KEY")

# Mock data for testing without the actual endpoint
def get_mock_forecast_data():
    # Create a date range for the next 7 days
    dates = [(datetime.now() + timedelta(hours=i)).isoformat() for i in range(168)]  # 24*7 hours
    
    # Generate mock solar production values
    # Higher during day, zero at night, variation by cloud cover
    forecast_values = []
    for i in range(168):
        hour = (datetime.now() + timedelta(hours=i)).hour
        if 6 <= hour <= 18:  # Daytime
            # Simulate bell curve for solar production during the day
            hour_factor = 1 - abs((hour - 12) / 6)  # Peak at noon
            # Random factor for weather (0.5-1.0)
            weather_factor = 0.5 + 0.5 * ((i % 3) / 3)
            value = 100 * hour_factor * weather_factor
        else:
            value = 0  # No production at night
        forecast_values.append(value)
    
    return {
        "timestamps": dates,
        "forecast_values": forecast_values
    }

# Get forecast from the Azure ML endpoint
def get_forecast_from_endpoint(location_data):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    
    try:
        response = requests.post(endpoint_url, json=location_data, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error calling endpoint: {response.status_code}, {response.text}")
            return None
    except Exception as e:
        print(f"Exception calling endpoint: {str(e)}")
        return None

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/forecast', methods=['GET', 'POST'])
def forecast():
    if request.method == 'POST':
        # Get form data
        location = request.form.get('location')
        forecast_days = int(request.form.get('forecast_days', 7))
        
        # In a real app, you would prepare the actual weather forecast data 
        # from a weather API based on the selected location
        
        # For demonstration, we'll use mock data
        mock_data = get_mock_forecast_data()
        
        # In a production app, you would call the ML endpoint:
        # forecast_data = get_forecast_from_endpoint(weather_data)
        
        # Create a DataFrame for visualization
        df = pd.DataFrame({
            'timestamp': [datetime.fromisoformat(ts.replace('Z', '+00:00')) 
                         for ts in mock_data['timestamps']],
            'forecast_kwh': mock_data['forecast_values']
        })
        
        # Calculate daily totals
        df['date'] = df['timestamp'].dt.date
        daily_totals = df.groupby('date')['forecast_kwh'].sum().reset_index()
        
        # Create plots
        hourly_fig = px.line(df, x='timestamp', y='forecast_kwh', 
                            title=f'Hourly Solar Energy Forecast for {location}',
                            labels={'timestamp': 'Time', 'forecast_kwh': 'Energy (kWh)'},
                            line_shape='spline')
                            
        daily_fig = px.bar(daily_totals, x='date', y='forecast_kwh',
                          title=f'Daily Solar Energy Forecast for {location}',
                          labels={'date': 'Date', 'forecast_kwh': 'Energy (kWh)'})
        
        # Convert plots to JSON for the template
        hourly_plot_json = json.dumps(hourly_fig, cls=plotly.utils.PlotlyJSONEncoder)
        daily_plot_json = json.dumps(daily_fig, cls=plotly.utils.PlotlyJSONEncoder)
        
        # Calculate some statistics
        total_energy = daily_totals['forecast_kwh'].sum()
        avg_daily = daily_totals['forecast_kwh'].mean()
        peak_hour = df.loc[df['forecast_kwh'].idxmax(), 'timestamp']
        peak_production = df['forecast_kwh'].max()
        
        return render_template(
            'forecast.html',
            location=location,
            hourly_plot=hourly_plot_json,
            daily_plot=daily_plot_json,
            total_energy=round(total_energy, 2),
            avg_daily=round(avg_daily, 2),
            peak_hour=peak_hour.strftime('%Y-%m-%d %H:%M'),
            peak_production=round(peak_production, 2)
        )
    
    # If GET request, show the form
    return render_template('forecast_form.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))