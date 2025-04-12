from flask import Flask, render_template, request
import os
import json
import pandas as pd
from datetime import datetime, timedelta
import plotly
import plotly.express as px

app = Flask(__name__)

def get_mock_forecast_data():
    start_time = datetime.now().replace(minute=0, second=0, microsecond=0)
    timestamps = [(start_time + timedelta(hours=i)).isoformat() for i in range(24 * 7)]
    
    forecast_values = []
    for i in range(24 * 7):
        hour = (start_time + timedelta(hours=i)).hour
        if hour < 6 or hour > 18:
            forecast_values.append(0)
        else:
            hour_factor = 1 - abs(hour - 12) / 6
            base_value = hour_factor * 80
            forecast_values.append(round(base_value * (0.8 + 0.4 * (i % 7) / 6), 2))
    
    return {"timestamps": timestamps, "forecast_values": forecast_values}

# Change forecast route to handle both GET and POST
@app.route('/forecast', methods=['GET', 'POST'])
def forecast():
    if request.method == 'POST':
        # Get form data
        location = request.form.get('location')
        forecast_days = int(request.form.get('forecast_days', 7))
        
        # Get mock forecast data
        forecast_data = get_mock_forecast_data()
        
        # Create DataFrame
        df = pd.DataFrame({
            'timestamp': [datetime.fromisoformat(ts) for ts in forecast_data['timestamps']],
            'forecast_kwh': forecast_data['forecast_values']
        })
        
        # Calculate daily totals
        df['date'] = df['timestamp'].dt.date
        daily_totals = df.groupby('date')['forecast_kwh'].sum().reset_index()
        
        # Create plots
        hourly_fig = px.line(df, x='timestamp', y='forecast_kwh', 
                            title=f'Hourly Solar Energy Forecast for {location}')
        daily_fig = px.bar(daily_totals, x='date', y='forecast_kwh',
                          title=f'Daily Solar Energy Forecast for {location}')
        
        # Convert plots to JSON
        hourly_plot_json = json.dumps(hourly_fig, cls=plotly.utils.PlotlyJSONEncoder)
        daily_plot_json = json.dumps(daily_fig, cls=plotly.utils.PlotlyJSONEncoder)
        
        # Calculate stats
        total_energy = daily_totals['forecast_kwh'].sum()
        avg_daily = daily_totals['forecast_kwh'].mean()
        peak_hour_idx = df['forecast_kwh'].idxmax()
        peak_hour = df.loc[peak_hour_idx, 'timestamp']
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

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/forecast', methods=['GET'])
def forecast_form():
    return render_template('forecast_form.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)