# Solar Energy Forecasting - Data Processing and Model Training
# To be run in Azure Machine Learning

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import json
import os
from azure.storage.blob import BlobServiceClient
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from prophet import Prophet

# Set display options
pd.set_option('display.max_columns', None)
sns.set(style="whitegrid")

# Connect to Azure Storage
connection_string = os.environ["STORAGE_CONNECTION_STRING"]
container_name = "solar-data"
blob_service_client = BlobServiceClient.from_connection_string(connection_string)
container_client = blob_service_client.get_container_client(container_name)

# Function to load data from blob storage
def load_data_from_blob(location_name):
    data_list = []
    
    # List blobs in the location folder
    location_prefix = f"{location_name}/"
    blobs = container_client.list_blobs(name_starts_with=location_prefix)
    
    for blob in blobs:
        blob_client = container_client.get_blob_client(blob.name)
        data = json.loads(blob_client.download_blob().readall())
        data_list.append(data)
    
    return data_list

# Load data for location
location_name = "solar_farm_1"  # Change as needed
raw_data = load_data_from_blob(location_name)

print(f"Loaded {len(raw_data)} data points for {location_name}")

# Function to process raw data into a clean DataFrame
def process_weather_data(raw_data):
    records = []
    
    for entry in raw_data:
        # Current weather
        current = entry.get('current', {})
        timestamp = datetime.fromisoformat(entry.get('timestamp').replace('Z', '+00:00'))
        
        record = {
            'timestamp': timestamp,
            'location': entry.get('location'),
            'temperature': current.get('temperature'),
            'cloud_cover': current.get('clouds'),
            'wind_speed': current.get('wind_speed'),
            'weather_description': current.get('weather_description')
        }
        
        records.append(record)
        
        # Process forecast entries
        for forecast in entry.get('forecast', []):
            forecast_time = datetime.fromtimestamp(forecast.get('dt'))
            
            forecast_record = {
                'timestamp': forecast_time,
                'location': entry.get('location'),
                'temperature': forecast.get('main', {}).get('temp'),
                'cloud_cover': forecast.get('clouds', {}).get('all'),
                'wind_speed': forecast.get('wind', {}).get('speed'),
                'weather_description': forecast.get('weather', [{}])[0].get('description'),
                'is_forecast': True
            }
            
            records.append(forecast_record)
    
    df = pd.DataFrame(records)
    return df

# Process the data
weather_df = process_weather_data(raw_data)
print(f"Processed data shape: {weather_df.shape}")
weather_df.head()

# Load sample solar production data
# In a real project, you would load actual solar production data
# For this example, we'll create synthetic data based on weather conditions

def generate_synthetic_solar_data(weather_df):
    # Filter out forecast data
    actual_weather = weather_df[weather_df.get('is_forecast', False) == False].copy()
    
    # Simple model: more sun (less cloud) = more energy
    # Temperature also affects panel efficiency
    actual_weather['solar_energy_kwh'] = (
        (100 - actual_weather['cloud_cover']) / 100 * 
        (1 + (actual_weather['temperature'] - 25) * 0.005) *  # Temperature coefficient
        100  # Base energy for a 100kW installation
    )
    
    # Add noise to make it more realistic
    actual_weather['solar_energy_kwh'] += np.random.normal(0, 5, size=len(actual_weather))
    
    # No production at night (simplification)
    actual_weather['hour'] = actual_weather['timestamp'].dt.hour
    night_mask = (actual_weather['hour'] < 6) | (actual_weather['hour'] > 18)
    actual_weather.loc[night_mask, 'solar_energy_kwh'] = 0
    
    return actual_weather

solar_df = generate_synthetic_solar_data(weather_df)
print(f"Solar data shape: {solar_df.shape}")
solar_df.head()

# Exploratory Data Analysis

# Plot solar energy production over time
plt.figure(figsize=(14, 7))
plt.plot(solar_df['timestamp'], solar_df['solar_energy_kwh'])
plt.title('Solar Energy Production Over Time')
plt.xlabel('Date')
plt.ylabel('Energy (kWh)')
plt.grid(True)
plt.tight_layout()
plt.show()

# Correlation between cloud cover and energy production
plt.figure(figsize=(10, 6))
plt.scatter(solar_df['cloud_cover'], solar_df['solar_energy_kwh'], alpha=0.6)
plt.title('Cloud Cover vs Solar Energy Production')
plt.xlabel('Cloud Cover (%)')
plt.ylabel('Energy (kWh)')
plt.grid(True)
plt.tight_layout()
plt.show()

# Feature Engineering

def engineer_features(df):
    # Extract time components
    df['hour'] = df['timestamp'].dt.hour
    df['day'] = df['timestamp'].dt.day
    df['month'] = df['timestamp'].dt.month
    df['year'] = df['timestamp'].dt.year
    df['dayofweek'] = df['timestamp'].dt.dayofweek
    
    # Time features: sin and cos transformations for cyclical features
    df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
    df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
    df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
    df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
    
    # Weather description encoding (one-hot)
    if 'weather_description' in df.columns:
        weather_dummies = pd.get_dummies(df['weather_description'], prefix='weather')
        df = pd.concat([df, weather_dummies], axis=1)
    
    return df

solar_df = engineer_features(solar_df)
print(f"Data shape after feature engineering: {solar_df.shape}")
solar_df.head()

# Train-Test Split for Model Training

# Select features and target
features = ['temperature', 'cloud_cover', 'wind_speed', 
            'hour_sin', 'hour_cos', 'month_sin', 'month_cos']

# Add weather dummies if they exist
weather_cols = [col for col in solar_df.columns if col.startswith('weather_')]
features.extend(weather_cols)

X = solar_df[features]
y = solar_df['solar_energy_kwh']

# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

print(f"Training set: {X_train.shape}, Test set: {X_test.shape}")

# Train Random Forest Model
rf_model = RandomForestRegressor(
    n_estimators=100, 
    max_depth=15,
    random_state=42,
    n_jobs=-1
)

rf_model.fit(X_train, y_train)

# Evaluate the model
y_pred = rf_model.predict(X_test)

mae = mean_absolute_error(y_test, y_pred)
rmse = mean_squared_error(y_test, y_pred, squared=False)
r2 = r2_score(y_test, y_pred)

print(f"Model Performance:")
print(f"MAE: {mae:.2f} kWh")
print(f"RMSE: {rmse:.2f} kWh")
print(f"R²: {r2:.4f}")

# Feature importance
feature_importance = pd.DataFrame({
    'Feature': features,
    'Importance': rf_model.feature_importances_
}).sort_values('Importance', ascending=False)

plt.figure(figsize=(10, 8))
sns.barplot(x='Importance', y='Feature', data=feature_importance)
plt.title('Feature Importance')
plt.tight_layout()
plt.show()

# Save the model
import joblib
model_file = "solar_forecast_rf_model.joblib"
joblib.dump(rf_model, model_file)
print(f"Model saved to {model_file}")

# Time Series Forecasting with Prophet

# Prepare data for Prophet (requires 'ds' and 'y' columns)
prophet_df = solar_df[['timestamp', 'solar_energy_kwh']].copy()
prophet_df.columns = ['ds', 'y']

# Filter for complete days only
prophet_df = prophet_df.sort_values('ds')

# Initialize and train Prophet model
m = Prophet(
    daily_seasonality=True,
    yearly_seasonality=True,
    weekly_seasonality=True
)

# Add weather as regressors
for feature in ['temperature', 'cloud_cover', 'wind_speed']:
    if feature in solar_df.columns:
        prophet_df[feature] = solar_df[feature].values
        m.add_regressor(feature)

m.fit(prophet_df)

# Create a dataframe for future predictions
future = m.make_future_dataframe(periods=24*7, freq='H')  # 7 days ahead

# Add the regressor values for the forecast period
# In a real application, you would use weather forecast data
for feature in ['temperature', 'cloud_cover', 'wind_speed']:
    if feature in solar_df.columns:
        # This is a simplification - in reality you'd use actual forecasts
        # Here we're just using the last 24*7 values as a placeholder
        future[feature] = list(solar_df[feature].values) + list(solar_df[feature].values[-24*7:])

# Make the forecast
forecast = m.predict(future)

# Plot the forecast
fig = m.plot(forecast)
plt.title('Solar Energy Production Forecast')
plt.ylabel('Energy (kWh)')
plt.xlabel('Date')
plt.tight_layout()
plt.show()

# Plot the components
fig = m.plot_components(forecast)
plt.tight_layout()
plt.show()

print("Data processing and model training complete!")