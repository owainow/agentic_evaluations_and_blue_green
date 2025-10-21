# Azure CLI Commands to Debug and Fix Permissions

## Quick Diagnostic Commands

Run these commands in Azure Cloud Shell to check the current state:

### 1. Check Service Principal Details
```bash
# Using the Service Principal ID from the error
SP_ID="5e27f043-f184-43bc-9997-72e5478cbda6"

az ad sp show --id "${SP_ID}" --query "{DisplayName:displayName, AppId:appId, ObjectId:id}" -o table
```

### 2. Find Your AI Foundry Resource
```bash
RESOURCE_GROUP="rg-aifoundry-dev"

# Get AI Foundry resource name
AI_FOUNDRY_NAME=$(az cognitiveservices account list \
  --resource-group "${RESOURCE_GROUP}" \
  --query "[?kind=='AIServices'].name | [0]" -o tsv)

echo "AI Foundry: ${AI_FOUNDRY_NAME}"

# Get full resource ID
AI_FOUNDRY_ID=$(az cognitiveservices account show \
  --resource-group "${RESOURCE_GROUP}" \
  --name "${AI_FOUNDRY_NAME}" \
  --query id -o tsv)

echo "Resource ID: ${AI_FOUNDRY_ID}"
```

### 3. Check Current Role Assignments
```bash
SP_ID="5e27f043-f184-43bc-9997-72e5478cbda6"
RESOURCE_GROUP="rg-aifoundry-dev"
AI_FOUNDRY_NAME="aif-foundry-dev-mf77j5"  # From your logs

# Get AI Foundry resource ID
AI_FOUNDRY_ID=$(az cognitiveservices account show \
  --resource-group "${RESOURCE_GROUP}" \
  --name "${AI_FOUNDRY_NAME}" \
  --query id -o tsv)

# Check roles assigned to the service principal
az role assignment list \
  --assignee "${SP_ID}" \
  --scope "${AI_FOUNDRY_ID}" \
  --query "[].{Role:roleDefinitionName, Scope:scope}" \
  -o table
```

### 4. Check for Azure AI User Role Specifically
```bash
SP_ID="5e27f043-f184-43bc-9997-72e5478cbda6"
AI_FOUNDRY_ID="/subscriptions/269eee56-58bc-45eb-9dca-4d22421c45fa/resourceGroups/rg-aifoundry-dev/providers/Microsoft.CognitiveServices/accounts/aif-foundry-dev-mf77j5"

az role assignment list \
  --assignee "${SP_ID}" \
  --scope "${AI_FOUNDRY_ID}" \
  --query "[?roleDefinitionName=='Azure AI User']" \
  -o table
```

## Fix: Assign the Required Role

### Option 1: One-Line Fix
```bash
# Set variables
SP_ID="5e27f043-f184-43bc-9997-72e5478cbda6"
RESOURCE_GROUP="rg-aifoundry-dev"
AI_FOUNDRY_NAME="aif-foundry-dev-mf77j5"

# Get resource ID and assign role in one command
az role assignment create \
  --assignee "${SP_ID}" \
  --role "Azure AI User" \
  --scope $(az cognitiveservices account show \
    --resource-group "${RESOURCE_GROUP}" \
    --name "${AI_FOUNDRY_NAME}" \
    --query id -o tsv)
```

### Option 2: Step-by-Step
```bash
# 1. Set variables
SP_ID="5e27f043-f184-43bc-9997-72e5478cbda6"
RESOURCE_GROUP="rg-aifoundry-dev"
AI_FOUNDRY_NAME="aif-foundry-dev-mf77j5"

# 2. Get AI Foundry resource ID
AI_FOUNDRY_ID=$(az cognitiveservices account show \
  --resource-group "${RESOURCE_GROUP}" \
  --name "${AI_FOUNDRY_NAME}" \
  --query id -o tsv)

echo "Resource ID: ${AI_FOUNDRY_ID}"

# 3. Assign the role
az role assignment create \
  --assignee "${SP_ID}" \
  --role "Azure AI User" \
  --scope "${AI_FOUNDRY_ID}"
```

### Option 3: Use the Setup Script
```bash
# Run the provided setup script
bash scripts/setup-github-actions-permissions.sh
```

## Verify the Fix

After assigning the role, verify it was successful:

```bash
SP_ID="5e27f043-f184-43bc-9997-72e5478cbda6"
RESOURCE_GROUP="rg-aifoundry-dev"
AI_FOUNDRY_NAME="aif-foundry-dev-mf77j5"

AI_FOUNDRY_ID=$(az cognitiveservices account show \
  --resource-group "${RESOURCE_GROUP}" \
  --name "${AI_FOUNDRY_NAME}" \
  --query id -o tsv)

# List all roles
az role assignment list \
  --assignee "${SP_ID}" \
  --scope "${AI_FOUNDRY_ID}" \
  --output table
```

## What the Azure AI User Role Provides

Check the data actions included in the role:

```bash
az role definition list \
  --name "Azure AI User" \
  --query "[0].permissions[0].dataActions" \
  -o json
```

This role includes the wildcard data action:
- `Microsoft.CognitiveServices/*` - This covers ALL Cognitive Services data actions including:
  - `Microsoft.CognitiveServices/accounts/AIServices/agents/write`
  - `Microsoft.CognitiveServices/accounts/AIServices/agents/read`
  - `Microsoft.CognitiveServices/accounts/AIServices/agents/delete`
  - Plus other actions needed for creating and managing agents

## All-in-One Diagnostic Script

Run the comprehensive diagnostic script:

```bash
bash scripts/check-permissions.sh
```

## Important Notes

1. **Role Propagation Delay**: After assigning a role, it can take 5-10 minutes to propagate. If the workflow still fails immediately after assignment, wait a few minutes and try again.

2. **Multiple Scopes**: The service principal may have roles at different levels:
   - Subscription level (inherited by all resources)
   - Resource Group level (inherited by resources in the RG)
   - Resource level (specific to the AI Foundry resource)
   
   For agent creation, you need the role at least at the AI Foundry resource level.

3. **Verify Service Principal ID**: Make sure you're using the correct Service Principal Object ID (not the Application ID). The error message shows: `5e27f043-f184-43bc-9997-72e5478cbda6`

## Quick Copy-Paste Commands

Just set your subscription and run these:

```bash
# Set subscription
az account set --subscription "269eee56-58bc-45eb-9dca-4d22421c45fa"

# Assign the role (all in one command)
az role assignment create \
  --assignee "5e27f043-f184-43bc-9997-72e5478cbda6" \
  --role "Azure AI User" \
  --scope "/subscriptions/269eee56-58bc-45eb-9dca-4d22421c45fa/resourceGroups/rg-aifoundry-dev/providers/Microsoft.CognitiveServices/accounts/aif-foundry-dev-mf77j5"

# Verify
az role assignment list \
  --assignee "5e27f043-f184-43bc-9997-72e5478cbda6" \
  --scope "/subscriptions/269eee56-58bc-45eb-9dca-4d22421c45fa/resourceGroups/rg-aifoundry-dev/providers/Microsoft.CognitiveServices/accounts/aif-foundry-dev-mf77j5" \
  --output table
```

Then wait 5-10 minutes and re-run your GitHub Actions workflow.
