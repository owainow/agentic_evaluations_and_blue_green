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
AI_SERVICES_NAME="aif-ais-dev-mf77j5"

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

# Get the AI Services resource ID
echo "2. Finding AI Services resource: ${AI_SERVICES_NAME}"
AI_SERVICES_ID=$(az cognitiveservices account show \
  --resource-group "${RESOURCE_GROUP}" \
  --name "${AI_SERVICES_NAME}" \
  --query id -o tsv)

if [ -z "$AI_SERVICES_ID" ]; then
  echo "❌ Error: AI Services resource '${AI_SERVICES_NAME}' not found in resource group '${RESOURCE_GROUP}'"
  exit 1
fi

echo "✅ Found AI Services: ${AI_SERVICES_ID}"
echo ""

# Check if role is already assigned
echo "3. Checking existing role assignments..."
EXISTING_ROLE=$(az role assignment list \
  --assignee "${SP_ID}" \
  --scope "${AI_SERVICES_ID}" \
  --query "[?roleDefinitionName=='Cognitive Services OpenAI User'].roleDefinitionName | [0]" \
  -o tsv)

if [ ! -z "$EXISTING_ROLE" ]; then
  echo "✅ Role 'Cognitive Services OpenAI User' is already assigned"
  echo ""
  echo "Current role assignments:"
  az role assignment list \
    --assignee "${SP_ID}" \
    --scope "${AI_SERVICES_ID}" \
    --query "[].{Role:roleDefinitionName, Scope:scope}" \
    -o table
  echo ""
  echo "✅ Setup complete! No changes needed."
  exit 0
fi

# Assign the role
echo "4. Assigning 'Cognitive Services OpenAI User' role..."
az role assignment create \
  --assignee "${SP_ID}" \
  --role "Cognitive Services OpenAI User" \
  --scope "${AI_SERVICES_ID}" \
  --output none

echo "✅ Role assigned successfully!"
echo ""

# Verify the assignment
echo "5. Verifying role assignments..."
az role assignment list \
  --assignee "${SP_ID}" \
  --scope "${AI_SERVICES_ID}" \
  --query "[].{Role:roleDefinitionName, Scope:scope}" \
  -o table

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "The service principal '${SERVICE_PRINCIPAL_NAME}' now has:"
echo "  ✅ Cognitive Services OpenAI User role"
echo ""
echo "Note: Role propagation can take 5-10 minutes."
echo "If GitHub Actions still fails, wait a few minutes and try again."
echo ""
echo "Next steps:"
echo "  1. Go to your GitHub repository"
echo "  2. Navigate to: Settings → Secrets and variables → Actions"
echo "  3. Verify these secrets exist:"
echo "     - AZURE_CLIENT_ID"
echo "     - AZURE_CLIENT_SECRET"
echo "     - AZURE_TENANT_ID"
echo "     - AZURE_SUBSCRIPTION_ID"
echo "  4. Run the 'Deploy Model and Create Agent' workflow"
echo ""
