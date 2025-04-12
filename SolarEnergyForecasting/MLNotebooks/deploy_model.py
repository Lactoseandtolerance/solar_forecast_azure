import os
import joblib
from azure.ai.ml import MLClient
from azure.ai.ml.entities import ManagedOnlineEndpoint, ManagedOnlineDeployment
from azure.ai.ml.constants import AssetTypes
from azure.identity import DefaultAzureCredential

# Load the model
model = joblib.load("solar_forecast_rf_model.joblib")

# Azure ML details
subscription_id = "YOUR_SUBSCRIPTION_ID"
resource_group = "solar-forecasting-rg"
workspace_name = "solar-forecast-ml"

# Initialize ML Client
ml_client = MLClient(
    DefaultAzureCredential(),
    subscription_id,
    resource_group,
    workspace_name
)

# Define model and endpoint names
model_name = "solar-forecast-model"
endpoint_name = "solar-forecast-endpoint"

# Register the model
model = ml_client.models.create_or_update(
    model_name,
    path="solar_forecast_rf_model.joblib",
    description="Solar energy production forecasting model",
    type=AssetTypes.CUSTOM_MODEL
)

# Create endpoint
endpoint = ManagedOnlineEndpoint(
    name=endpoint_name,
    description="Endpoint for solar energy forecasting",
    auth_mode="key"
)

endpoint = ml_client.online_endpoints.begin_create_or_update(endpoint).result()

# Create deployment
deployment = ManagedOnlineDeployment(
    name="solar-forecast-deployment",
    endpoint_name=endpoint_name,
    model=model,
    instance_type="Standard_DS2_v2",
    instance_count=1
)

deployment = ml_client.begin_create_or_update(deployment).result()

# Set the deployment as default
endpoint.traffic = {"solar-forecast-deployment": 100}
ml_client.online_endpoints.begin_create_or_update(endpoint).result()

print(f"Model deployed! Endpoint URL: {endpoint.scoring_uri}")