#!/bin/bash
#
# Setup Script for GitHub Actions Service Principal
# Run this in Azure Cloud Shell to configure permissions for assistant creation
#
# Usage:
#   1. Open https://shell.azure.com
#   2. Copy and paste this script
#   3. Update the variables below
#   4. Run: bash setup-github-actions-permissions.sh
#

set -e  # Exit on error

# ==============================================================================
# CONFIGURATION - Update these values for your environment
# ==============================================================================

SERVICE_PRINCIPAL_NAME="github-actions-aifoundry"
RESOURCE_GROUP="rg-aifoundry-dev"
# The AI Foundry resource name (kind=AIServices)
AI_FOUNDRY_NAME=""  # Leave empty to auto-detect

# ==============================================================================
# Script starts here
# ==============================================================================

echo "=========================================="
echo "GitHub Actions Permission Setup"
echo "=========================================="
echo ""

# Get the service principal object ID
echo "1. Finding service principal: ${SERVICE_PRINCIPAL_NAME}"
SP_ID=$(az ad sp list --display-name "${SERVICE_PRINCIPAL_NAME}" --query "[0].id" -o tsv)

if [ -z "$SP_ID" ]; then
  echo "❌ Error: Service principal '${SERVICE_PRINCIPAL_NAME}' not found"
  echo ""
  echo "Create it first with:"
  echo "  az ad sp create-for-rbac \\"
  echo "    --name '${SERVICE_PRINCIPAL_NAME}' \\"
  echo "    --role Contributor \\"
  echo "    --scopes /subscriptions/\$(az account show --query id -o tsv)"
  exit 1
fi

echo "✅ Found service principal: ${SP_ID}"
echo ""

# Get the AI Foundry resource ID
echo "2. Finding AI Foundry resource..."
if [ -z "$AI_FOUNDRY_NAME" ]; then
  echo "   Auto-detecting AI Foundry resource (kind=AIServices)..."
  AI_FOUNDRY_NAME=$(az cognitiveservices account list \
    --resource-group "${RESOURCE_GROUP}" \
    --query "[?kind=='AIServices'].name | [0]" -o tsv)
  
  if [ -z "$AI_FOUNDRY_NAME" ]; then
    echo "❌ Error: No AI Foundry resource found in resource group '${RESOURCE_GROUP}'"
    echo "Available Cognitive Services accounts:"
    az cognitiveservices account list --resource-group "${RESOURCE_GROUP}" --query "[].{Name:name, Kind:kind}" -o table
    exit 1
  fi
  echo "   Detected: ${AI_FOUNDRY_NAME}"
fi

AI_FOUNDRY_ID=$(az cognitiveservices account show \
  --resource-group "${RESOURCE_GROUP}" \
  --name "${AI_FOUNDRY_NAME}" \
  --query id -o tsv)

if [ -z "$AI_FOUNDRY_ID" ]; then
  echo "❌ Error: AI Foundry resource '${AI_FOUNDRY_NAME}' not found in resource group '${RESOURCE_GROUP}'"
  exit 1
fi

echo "✅ Found AI Foundry: ${AI_FOUNDRY_NAME}"
echo "   Resource ID: ${AI_FOUNDRY_ID}"
echo ""

# Check if role is already assigned
echo "3. Checking existing role assignments..."
EXISTING_ROLE=$(az role assignment list \
  --assignee "${SP_ID}" \
  --scope "${AI_FOUNDRY_ID}" \
  --query "[?roleDefinitionName=='Azure AI User'].roleDefinitionName | [0]" \
  -o tsv)

if [ ! -z "$EXISTING_ROLE" ]; then
  echo "✅ Role 'Azure AI User' is already assigned"
  echo ""
  echo "Current role assignments:"
  az role assignment list \
    --assignee "${SP_ID}" \
    --scope "${AI_FOUNDRY_ID}" \
    --query "[].{Role:roleDefinitionName, Scope:scope}" \
    -o table
  echo ""
  echo "✅ Setup complete! No changes needed."
  exit 0
fi

# Assign the Azure AI User role (required for agent creation)
echo "4. Assigning 'Azure AI User' role..."
echo "   This role provides the required data action: Microsoft.CognitiveServices/* (includes agents/write)"
az role assignment create \
  --assignee "${SP_ID}" \
  --role "Azure AI User" \
  --scope "${AI_FOUNDRY_ID}" \
  --output none

echo "✅ Role assigned successfully!"
echo ""

# Verify the assignment
echo "5. Verifying role assignments..."
az role assignment list \
  --assignee "${SP_ID}" \
  --scope "${AI_FOUNDRY_ID}" \
  --query "[].{Role:roleDefinitionName, Scope:scope}" \
  -o table

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "The service principal '${SERVICE_PRINCIPAL_NAME}' now has:"
echo "  ✅ Azure AI User role on ${AI_FOUNDRY_NAME}"
echo ""
echo "This role provides permissions for:"
echo "  • Creating and managing AI agents (via data action: Microsoft.CognitiveServices/*)"
echo "  • Using deployed models"
echo "  • Building and developing in AI Foundry projects"
echo ""
echo "⚠️  IMPORTANT: Role propagation can take 5-10 minutes."
echo "If GitHub Actions still fails, wait a few minutes and try again."
echo ""
echo "Next steps:"
echo "  1. Wait 5-10 minutes for role propagation"
echo "  2. Go to your GitHub repository"
echo "  3. Navigate to: Actions → Deploy Model and Create Agent"
echo "  4. Click 'Run workflow'"
echo ""
echo "For GitHub secrets setup, ensure these exist in your repo:"
echo "  - AZURE_CLIENT_ID"
echo "  - AZURE_TENANT_ID"
echo "  - AZURE_SUBSCRIPTION_ID (optional, can be set in workflow)"
echo ""
