#!/bin/bash
#
# Diagnostic Script - Check GitHub Actions Service Principal Permissions
# Run this in Azure Cloud Shell or locally with Azure CLI
#
# Usage: bash scripts/check-permissions.sh
#

set -e

# ==============================================================================
# CONFIGURATION
# ==============================================================================

SERVICE_PRINCIPAL_NAME="github-actions-aifoundry"
SERVICE_PRINCIPAL_ID="5e27f043-f184-43bc-9997-72e5478cbda6"  # From error message
SUBSCRIPTION_ID="269eee56-58bc-45eb-9dca-4d22421c45fa"
RESOURCE_GROUP="rg-aifoundry-dev"

# ==============================================================================
# Diagnostic checks
# ==============================================================================

echo "=========================================="
echo "Permission Diagnostics"
echo "=========================================="
echo ""
echo "Service Principal ID: ${SERVICE_PRINCIPAL_ID}"
echo "Subscription: ${SUBSCRIPTION_ID}"
echo "Resource Group: ${RESOURCE_GROUP}"
echo ""

# Set the subscription context
echo "1. Setting subscription context..."
az account set --subscription "${SUBSCRIPTION_ID}"
echo "✅ Subscription set"
echo ""

# Get service principal details
echo "2. Service Principal Details..."
SP_INFO=$(az ad sp show --id "${SERVICE_PRINCIPAL_ID}" --query "{DisplayName:displayName, AppId:appId, ObjectId:id}" -o json 2>/dev/null || echo "{}")
if [ "$SP_INFO" != "{}" ]; then
  echo "$SP_INFO" | jq '.'
else
  echo "⚠️  Could not retrieve service principal details"
  echo "   Trying by name: ${SERVICE_PRINCIPAL_NAME}"
  az ad sp list --display-name "${SERVICE_PRINCIPAL_NAME}" --query "[].{DisplayName:displayName, AppId:appId, ObjectId:id}" -o table
fi
echo ""

# Find AI Foundry resource
echo "3. Finding AI Foundry resource..."
AI_FOUNDRY_NAME=$(az cognitiveservices account list \
  --resource-group "${RESOURCE_GROUP}" \
  --query "[?kind=='AIServices'].name | [0]" -o tsv)

if [ -z "$AI_FOUNDRY_NAME" ]; then
  echo "❌ No AI Foundry resource found"
  echo "Available resources:"
  az cognitiveservices account list --resource-group "${RESOURCE_GROUP}" -o table
  exit 1
fi

echo "✅ Found AI Foundry: ${AI_FOUNDRY_NAME}"

AI_FOUNDRY_ID=$(az cognitiveservices account show \
  --resource-group "${RESOURCE_GROUP}" \
  --name "${AI_FOUNDRY_NAME}" \
  --query id -o tsv)
echo "   Resource ID: ${AI_FOUNDRY_ID}"
echo ""

# Check role assignments at AI Foundry resource level
echo "4. Role Assignments on AI Foundry Resource..."
ROLES=$(az role assignment list \
  --assignee "${SERVICE_PRINCIPAL_ID}" \
  --scope "${AI_FOUNDRY_ID}" \
  --query "[].{Role:roleDefinitionName, Scope:scope}" \
  -o json)

if [ "$ROLES" == "[]" ]; then
  echo "❌ NO roles assigned at AI Foundry resource level"
else
  echo "✅ Roles assigned:"
  echo "$ROLES" | jq -r '.[] | "   - \(.Role)"'
fi
echo ""

# Check for specific roles
echo "5. Checking Required Roles..."
HAS_AI_USER=$(az role assignment list \
  --assignee "${SERVICE_PRINCIPAL_ID}" \
  --scope "${AI_FOUNDRY_ID}" \
  --query "[?roleDefinitionName=='Azure AI User'].roleDefinitionName | [0]" -o tsv)

if [ ! -z "$HAS_AI_USER" ]; then
  echo "✅ Azure AI User role: ASSIGNED (Required for agent creation)"
else
  echo "❌ Azure AI User role: NOT ASSIGNED (Required!)"
fi

HAS_CONTRIBUTOR=$(az role assignment list \
  --assignee "${SERVICE_PRINCIPAL_ID}" \
  --scope "${AI_FOUNDRY_ID}" \
  --query "[?roleDefinitionName=='Contributor'].roleDefinitionName | [0]" -o tsv)

if [ ! -z "$HAS_CONTRIBUTOR" ]; then
  echo "✅ Contributor role: ASSIGNED"
else
  echo "⚠️  Contributor role: NOT ASSIGNED (Optional, but helpful)"
fi
echo ""

# Check role assignments at resource group level
echo "6. Role Assignments at Resource Group Level..."
RG_ROLES=$(az role assignment list \
  --assignee "${SERVICE_PRINCIPAL_ID}" \
  --resource-group "${RESOURCE_GROUP}" \
  --query "[].{Role:roleDefinitionName, Scope:scope}" \
  -o json)

if [ "$RG_ROLES" != "[]" ]; then
  echo "Resource Group roles:"
  echo "$RG_ROLES" | jq -r '.[] | "   - \(.Role)"'
else
  echo "⚠️  No roles at resource group level"
fi
echo ""

# Check role assignments at subscription level
echo "7. Role Assignments at Subscription Level..."
SUB_ROLES=$(az role assignment list \
  --assignee "${SERVICE_PRINCIPAL_ID}" \
  --scope "/subscriptions/${SUBSCRIPTION_ID}" \
  --query "[].{Role:roleDefinitionName}" \
  -o json)

if [ "$SUB_ROLES" != "[]" ]; then
  echo "Subscription roles:"
  echo "$SUB_ROLES" | jq -r '.[] | "   - \(.Role)"'
else
  echo "⚠️  No roles at subscription level"
fi
echo ""

# Show the required data action
echo "8. Required Data Action..."
echo "   The error indicates the missing data action:"
echo "   • Microsoft.CognitiveServices/accounts/AIServices/agents/write"
echo ""
echo "   This is provided by the 'Azure AI Developer' role"
echo ""

# Get role definition details
echo "9. Azure AI User Role Definition..."
ROLE_DEF=$(az role definition list --name "Azure AI User" --query "[0].{Name:roleName, Id:id, DataActions:permissions[0].dataActions}" -o json)
if [ ! -z "$ROLE_DEF" ] && [ "$ROLE_DEF" != "null" ]; then
  echo "   Role includes these data actions:"
  echo "$ROLE_DEF" | jq -r '.DataActions[]' | sed 's/^/     • /'
  echo ""
  echo "   Note: Microsoft.CognitiveServices/* is a wildcard that covers ALL"
  echo "         Cognitive Services data actions, including AIServices/agents/*"
else
  echo "   ⚠️  Could not retrieve role definition"
fi
echo ""

# Summary and recommendation
echo "=========================================="
echo "SUMMARY"
echo "=========================================="
echo ""

if [ ! -z "$HAS_AI_USER" ]; then
  echo "✅ The service principal HAS the required 'Azure AI User' role"
  echo ""
  echo "⚠️  If you're still seeing permission errors:"
  echo "   1. Role propagation can take 5-10 minutes"
  echo "   2. Try waiting a few minutes and run the workflow again"
  echo "   3. Check if the role was just assigned recently"
else
  echo "❌ ISSUE FOUND: Missing 'Azure AI User' role"
  echo ""
  echo "🔧 FIX: Run the following command:"
  echo ""
  echo "   az role assignment create \\"
  echo "     --assignee \"${SERVICE_PRINCIPAL_ID}\" \\"
  echo "     --role \"Azure AI User\" \\"
  echo "     --scope \"${AI_FOUNDRY_ID}\""
  echo ""
  echo "   OR run: bash scripts/setup-github-actions-permissions.sh"
fi
echo ""

