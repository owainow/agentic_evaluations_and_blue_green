#!/bin/bash

# Bash deployment script for Azure AI Foundry

set -e

# Default values
RESOURCE_GROUP="${RESOURCE_GROUP:-rg-aifoundry-dev}"
LOCATION="${LOCATION:-eastus}"
TEMPLATE_FILE="${TEMPLATE_FILE:-main.bicep}"
PARAMETERS_FILE="${PARAMETERS_FILE:-main.parameters.json}"

# Colors
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
GRAY='\033[0;90m'
NC='\033[0m' # No Color

echo -e "${CYAN}🚀 Starting Azure AI Foundry deployment...${NC}"
echo ""

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo -e "${RED}❌ Azure CLI is not installed. Please install it first.${NC}"
    echo "   Visit: https://docs.microsoft.com/cli/azure/install-azure-cli"
    exit 1
fi

# Check if logged in
echo -e "${CYAN}🔐 Checking Azure login status...${NC}"
if ! az account show &> /dev/null; then
    echo -e "${YELLOW}⚠️  Not logged in to Azure. Initiating login...${NC}"
    az login
else
    ACCOUNT=$(az account show --query user.name -o tsv)
    echo -e "${GREEN}✅ Already logged in as: ${ACCOUNT}${NC}"
fi

# Set subscription if provided
if [ ! -z "$SUBSCRIPTION_ID" ]; then
    echo -e "${CYAN}📝 Setting subscription to: ${SUBSCRIPTION_ID}${NC}"
    az account set --subscription "$SUBSCRIPTION_ID"
fi

# Display current subscription
CURRENT_SUB=$(az account show --query name -o tsv)
CURRENT_SUB_ID=$(az account show --query id -o tsv)
echo -e "${CYAN}📋 Using subscription: ${CURRENT_SUB} (${CURRENT_SUB_ID})${NC}"
echo ""

# Create resource group if it doesn't exist
echo -e "${CYAN}📦 Checking resource group: ${RESOURCE_GROUP}${NC}"
if ! az group show --name "$RESOURCE_GROUP" &> /dev/null; then
    echo -e "${CYAN}   Creating resource group in ${LOCATION}...${NC}"
    az group create --name "$RESOURCE_GROUP" --location "$LOCATION"
    echo -e "${GREEN}✅ Resource group created${NC}"
else
    echo -e "${GREEN}✅ Resource group already exists${NC}"
fi
echo ""

# Deploy the template
echo -e "${CYAN}🔨 Deploying BICEP template...${NC}"
echo -e "${GRAY}   Template: ${TEMPLATE_FILE}${NC}"
echo -e "${GRAY}   Parameters: ${PARAMETERS_FILE}${NC}"
echo ""

DEPLOYMENT_NAME="aifoundry-deployment-$(date +%Y%m%d-%H%M%S)"

if az deployment group create \
    --name "$DEPLOYMENT_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --template-file "$TEMPLATE_FILE" \
    --parameters "$PARAMETERS_FILE"; then
    
    echo ""
    echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
    echo ""
    echo -e "${CYAN}📊 Deployment Outputs:${NC}"
    echo -e "${GRAY}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    # Get outputs
    az deployment group show \
        --name "$DEPLOYMENT_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --query properties.outputs \
        --output table
    
    echo ""
    echo -e "${GREEN}🎉 Your Azure AI Foundry project is ready!${NC}"
    echo ""
    echo -e "${CYAN}Next steps:${NC}"
    echo -e "${NC}  1. Navigate to https://ai.azure.com${NC}"
    
    PROJECT_NAME=$(az deployment group show \
        --name "$DEPLOYMENT_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --query properties.outputs.projectName.value -o tsv)
    
    echo -e "${NC}  2. Select your project: ${YELLOW}${PROJECT_NAME}${NC}"
    echo -e "${NC}  3. Start building agents!${NC}"
    echo ""
    
else
    echo ""
    echo -e "${RED}❌ Deployment failed!${NC}"
    exit 1
fi
