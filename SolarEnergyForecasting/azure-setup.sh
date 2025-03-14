#!/bin/bash
# Azure Resource Setup for Solar Forecasting Project

# Variables - customize these
RESOURCE_GROUP="solar-forecasting-rg"
LOCATION="eastus"  # Choose a location close to you
STORAGE_ACCOUNT="solarstore2477"  # Must be globally unique
CONTAINER_NAME="solar-data"
FUNCTION_APP_NAME="solar-forecast-func-py312"  # Must be globally unique
ML_WORKSPACE="solar-forecast-ml"

# Login to Azure
az login

# Create a resource group
echo "Creating resource group..."
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create a storage account
echo "Creating storage account..."
az storage account create \
    --name $STORAGE_ACCOUNT \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION \
    --sku Standard_LRS \
    --kind StorageV2 \
    --enable-hierarchical-namespace true

# Get storage account key
STORAGE_KEY=$(az storage account keys list --resource-group $RESOURCE_GROUP --account-name $STORAGE_ACCOUNT --query "[0].value" -o tsv)

# Create a container in the storage account
echo "Creating storage container..."
az storage container create \
    --name $CONTAINER_NAME \
    --account-name $STORAGE_ACCOUNT \
    --account-key $STORAGE_KEY

# Create a consumption plan for Azure Functions
echo "Creating Function App consumption plan..."
az functionapp create \
    --name solar-forecast-func-py312 \
    --resource-group solar-forecasting-rg \
    --storage-account solarstore2477 \
    --consumption-plan-location eastus \
    --runtime python \
    --runtime-version 3.12 \
    --functions-version 4 \
    --os-type Linux

az functionapp config appsettings set \
    --name solar-forecast-func-py312 \
    --resource-group solar-forecasting-rg \
    --settings OPENWEATHERMAP_API_KEY="db5789f6264a997c47c8f42349cd8ae8"

# Create an Azure Machine Learning workspace
echo "Creating Machine Learning workspace..."
az ml workspace create \
    --name $ML_WORKSPACE \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION

# Create an Application Insights resource
az monitor app-insights component create \
    --app solar-forecast-insights \
    --location eastus \
    --resource-group solar-forecasting-rg \
    --application-type web

# Get the instrumentation key
INSTRUMENTATION_KEY=$(az monitor app-insights component show \
    --app solar-forecast-insights \
    --resource-group solar-forecasting-rg \
    --query instrumentationKey \
    --output tsv)

# Add the instrumentation key to your function app settings
az functionapp config appsettings set \
    --name solar-forecast-func-py312 \
    --resource-group solar-forecasting-rg \
    --settings APPINSIGHTS_INSTRUMENTATIONKEY=$INSTRUMENTATION_KEY

echo "Setup complete!"
echo "Resource Group: $RESOURCE_GROUP"
echo "Storage Account: $STORAGE_ACCOUNT"
echo "Function App: $FUNCTION_APP_NAME"
echo "ML Workspace: $ML_WORKSPACE"
