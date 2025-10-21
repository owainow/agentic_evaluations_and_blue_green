# Azure AI Foundry Infrastructure

This directory contains BICEP templates to deploy an Azure AI Foundry project with agent support.

## What Gets Deployed

1. **Azure AI Foundry Resource** (`Microsoft.CognitiveServices/accounts` with kind `AIServices`)
   - System-assigned managed identity
   - S0 SKU
   - Project management enabled
   - EntraID authentication (local auth disabled for security)

2. **Azure AI Foundry Project** (`Microsoft.CognitiveServices/accounts/projects`)
   - Nested under the AI Foundry resource
   - Ready for agent development

3. **Model Deployment** (default: GPT-4o)
   - Configured with Standard SKU
   - 10K TPM capacity
   - Latest model version (2024-11-20)

4. **Capability Hosts for Agents**
   - Account-level capability host (enables agent service)
   - Project-level capability host (configures agent storage)
   - Uses managed multitenant storage (basic setup)

## Prerequisites

- Azure CLI or Azure PowerShell
- Azure subscription with appropriate permissions
- Bicep CLI installed (comes with Azure CLI 2.20.0+)

## Deployment Instructions

### Option 1: Using Azure CLI

```bash
# Login to Azure
az login

# Set your subscription
az account set --subscription "<your-subscription-id>"

# Create resource group
az group create --name rg-aifoundry-dev --location eastus

# Deploy the template
az deployment group create \
  --resource-group rg-aifoundry-dev \
  --template-file main.bicep \
  --parameters main.parameters.json
```

### Option 2: Using Azure PowerShell

```powershell
# Login to Azure
Connect-AzAccount

# Set your subscription
Set-AzContext -Subscription "<your-subscription-id>"

# Create resource group
New-AzResourceGroup -Name rg-aifoundry-dev -Location eastus

# Deploy the template
New-AzResourceGroupDeployment `
  -ResourceGroupName rg-aifoundry-dev `
  -TemplateFile main.bicep `
  -TemplateParameterFile main.parameters.json
```

### Option 3: Custom Parameters

```bash
# Deploy with inline parameters
az deployment group create \
  --resource-group rg-aifoundry-dev \
  --template-file main.bicep \
  --parameters \
    aiFoundryName=myai-foundry \
    aiProjectName=my-agent-project \
    enableAgents=true \
    modelDeploymentName=gpt-4o \
    location=eastus
```

## Creating an Agent

After deployment, you can create an agent using the Azure AI Foundry SDK or REST API:

### Python Example

```python
import os
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

# Get project endpoint from deployment outputs
project_endpoint = os.environ["PROJECT_ENDPOINT"]

# Create client
project_client = AIProjectClient(
    endpoint=project_endpoint,
    credential=DefaultAzureCredential()
)

# Create an agent
with project_client:
    agents_client = project_client.agents
    
    agent = agents_client.create_agent(
        model="gpt-4o",  # Your deployment name
        name="my-assistant",
        instructions="You are a helpful AI assistant."
    )
    
    print(f"Created agent: {agent.id}")
```

### REST API Example

```bash
# Get access token
TOKEN=$(az account get-access-token --resource https://cognitiveservices.azure.com --query accessToken -o tsv)

# Create agent
curl --request POST \
  --url "https://<your-foundry-endpoint>/assistants?api-version=2024-05-01-preview" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "instructions": "You are a helpful assistant.",
    "name": "my-agent",
    "model": "gpt-4o",
    "tools": [{"type": "code_interpreter"}]
  }'
```

## Agent Storage (Basic vs Standard Setup)

This template uses **Basic Setup** with managed multitenant storage, which is:
- ✅ Simpler to deploy
- ✅ Managed by Microsoft
- ✅ Good for development and testing

For **Standard Setup** (production-ready with your own resources):
1. Add Azure Storage Account, Cosmos DB, and Azure AI Search
2. Create connections to these resources
3. Update the `projectCapabilityHost` resource with connection IDs
4. See: https://github.com/azure-ai-foundry/foundry-samples/tree/main/samples/microsoft/infrastructure-setup

## Configuration Options

Edit `main.parameters.json` to customize:

- **aiFoundryName**: Unique name for your AI Foundry resource
- **aiProjectName**: Name for your project
- **enableAgents**: Set to `true` to enable agent capabilities
- **modelDeploymentName**: Name of your model deployment
- **modelName**: Model to deploy (gpt-4o, gpt-4o-mini, etc.)
- **modelVersion**: Specific version of the model
- **deploymentSkuName**: `Standard` or `GlobalStandard`
- **deploymentCapacity**: TPM capacity in thousands

## Verification

After deployment, verify resources:

```bash
# List resources in the group
az resource list --resource-group rg-aifoundry-dev --output table

# Get AI Foundry resource details
az cognitiveservices account show \
  --name <your-ai-foundry-name> \
  --resource-group rg-aifoundry-dev
```

## Security Best Practices

✅ **Implemented:**
- Managed identity enabled
- Local auth disabled (EntraID only)
- Project management enabled

🔒 **Consider for Production:**
- Enable private endpoints
- Use customer-managed keys
- Implement network isolation
- Use standard agent setup with your own storage

## Troubleshooting

### Deployment Failures

1. **Name conflicts**: AI Foundry resource names must be globally unique
2. **Quota limits**: Check subscription quotas for Cognitive Services
3. **Region availability**: Ensure the region supports AI Foundry

### Agent Creation Issues

1. **Authentication**: Ensure you have appropriate RBAC roles (Cognitive Services User)
2. **Model deployment**: Verify the model deployment is successful
3. **Capability hosts**: Confirm both account and project capability hosts are created

## Clean Up

To remove all resources:

```bash
# Delete the resource group (deletes all resources)
az group delete --name rg-aifoundry-dev --yes --no-wait
```

## References

- [Azure AI Foundry Documentation](https://learn.microsoft.com/azure/ai-foundry/)
- [Official BICEP Samples](https://github.com/azure-ai-foundry/foundry-samples)
- [Agent Service Documentation](https://learn.microsoft.com/azure/ai-foundry/agents/)
- [Capability Hosts](https://learn.microsoft.com/azure/ai-foundry/agents/concepts/capability-hosts)
