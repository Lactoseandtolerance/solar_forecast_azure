#!/bin/bash
# Deploy Flask Web App to Azure App Service

# Variables - customize these
RESOURCE_GROUP="solar-forecasting-rg"
LOCATION="eastus"
APP_NAME="solar-forecast-dashboard"
APP_SERVICE_PLAN="solar-forecast-plan"

# Login to Azure
az login

# Create App Service Plan
echo "Creating App Service Plan..."
az appservice plan create \
    --name $APP_SERVICE_PLAN \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION \
    --sku B1

# Create Web App
echo "Creating Web App..."
az webapp create \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --plan $APP_SERVICE_PLAN \
    --runtime "PYTHON:3.9"

# Configure Web App settings
echo "Configuring Web App settings..."
az webapp config set \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --startup-file "gunicorn app:app"

# Set environment variables
echo "Setting environment variables..."
az webapp config appsettings set \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --settings \
    ML_ENDPOINT_URL="YOUR_ML_ENDPOINT_URL" \
    ML_API_KEY="YOUR_ML_API_KEY"

# Create deployment package
echo "Creating deployment package..."
mkdir -p deployment
cp app.py deployment/
cp -r templates deployment/
pip freeze > deployment/requirements.txt

# Add gunicorn to requirements
echo "gunicorn==20.1.0" >> deployment/requirements.txt

# Deploy the application
echo "Deploying application..."
cd deployment
az webapp deploy \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --src-path . \
    --type zip

echo "Deployment completed!"
echo "Web App URL: https://$APP_NAME.azurewebsites.net"