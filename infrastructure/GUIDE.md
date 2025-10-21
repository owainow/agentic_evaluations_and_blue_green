# Azure AI Foundry BICEP Templates - Complete Guide

This directory contains complete BICEP infrastructure-as-code templates to deploy Azure AI Foundry with agent support, based on the **latest Microsoft documentation** (as of October 2025).

## 📁 Files Overview

### Basic Setup (Recommended for Getting Started)
- **`main.bicep`** - Basic setup with managed multitenant storage
- **`main.parameters.json`** - Parameters for basic deployment
- **`deploy.ps1`** - PowerShell deployment script
- **`deploy.sh`** - Bash deployment script

### Standard Setup (Production-Ready)
- **`main.standard.bicep`** - Standard setup with dedicated resources (Storage, Cosmos DB, AI Search)
- **`main.standard.parameters.json`** - Parameters for standard deployment

### Documentation
- **`README.md`** - Detailed deployment and usage guide
- **`GUIDE.md`** - This comprehensive guide

## 🎯 What Gets Deployed

### Basic Setup (`main.bicep`)
✅ **Azure AI Foundry Resource** (Cognitive Services kind: AIServices)
✅ **Azure AI Foundry Project** 
✅ **Model Deployment** (GPT-4o by default)
✅ **Capability Hosts** (Account + Project level for agent support)
✅ **Managed Identity** with EntraID authentication

**Use Case:** Development, testing, proof-of-concept

### Standard Setup (`main.standard.bicep`)
✅ Everything in Basic Setup, PLUS:
✅ **Azure Storage Account** (dedicated blob containers for files and system data)
✅ **Azure Cosmos DB** (dedicated containers for threads, messages, and agent metadata)
✅ **Azure AI Search** (vector store for agent retrieval)
✅ **Managed Identity RBAC** (proper permissions configured)
✅ **Project-level data isolation**

**Use Case:** Production, enterprise deployments with data sovereignty requirements

## 🚀 Quick Start

### Prerequisites
```powershell
# Check Azure CLI
az --version

# Check Bicep
az bicep version

# Login
az login
```

### Deploy Basic Setup
```powershell
# PowerShell
cd infrastructure
.\deploy.ps1 -ResourceGroupName "rg-aifoundry-dev" -Location "eastus"
```

```bash
# Bash
cd infrastructure
chmod +x deploy.sh
./deploy.sh
```

### Deploy Standard Setup
```powershell
# PowerShell
az deployment group create `
  --resource-group rg-aifoundry-prod `
  --template-file main.standard.bicep `
  --parameters main.standard.parameters.json
```

## 📋 Key Concepts

### Capability Hosts
**Capability Hosts** enable agent functionality in Azure AI Foundry:

1. **Account-Level Capability Host**
   - Created at the AI Foundry resource level
   - Specifies `capabilityHostKind: 'Agents'`
   - Enables agent service for the account

2. **Project-Level Capability Host**
   - Created at the project level
   - Specifies resource connections for agent data
   - **Basic Setup**: Uses managed multitenant storage (no connections specified)
   - **Standard Setup**: Uses your own resources (connections specified)

### Agent Storage Models

#### Basic Setup (Managed)
```bicep
resource projectCapabilityHost 'Microsoft.CognitiveServices/.../capabilityHosts@2025-06-01' = {
  properties: {
    capabilityHostKind: 'Agents'
    // No connections = uses Microsoft-managed multitenant storage
  }
}
```

#### Standard Setup (Bring Your Own)
```bicep
resource projectCapabilityHost 'Microsoft.CognitiveServices/.../capabilityHosts@2025-06-01' = {
  properties: {
    capabilityHostKind: 'Agents'
    threadStorageConnections: ['cosmos-connection']    // For threads/messages
    vectorStoreConnections: ['search-connection']      // For vector search
    storageConnections: ['storage-connection']         // For files
  }
}
```

## 🔧 Configuration

### Model Selection
Edit parameters to deploy different models:

```json
{
  "modelDeploymentName": { "value": "gpt-4o-mini" },
  "modelName": { "value": "gpt-4o-mini" },
  "modelVersion": { "value": "2024-07-18" },
  "modelFormat": { "value": "OpenAI" }
}
```

Supported models:
- **OpenAI**: gpt-4o, gpt-4o-mini, gpt-4, gpt-35-turbo
- **Microsoft**: Phi-4, Phi-3
- **Meta**: Llama models
- **Mistral AI**: Mistral models
- **Cohere**: Command models

### SKU Options
- **Standard**: Regional deployment
- **GlobalStandard**: Global deployment (serverless)

### Capacity
Specified in thousands of tokens per minute (TPM):
- `deploymentCapacity: 10` = 10K TPM
- `deploymentCapacity: 50` = 50K TPM

## 🛠️ Building an Agent

After deployment, create agents using the SDK:

### Python
```python
import os
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

# Initialize client
project_client = AIProjectClient(
    endpoint=os.environ["PROJECT_ENDPOINT"],
    credential=DefaultAzureCredential()
)

with project_client:
    agents_client = project_client.agents
    
    # Create agent
    agent = agents_client.create_agent(
        model="gpt-4o",
        name="my-assistant",
        instructions="You are a helpful AI assistant that can help with coding questions.",
        tools=[
            {"type": "code_interpreter"},
            {"type": "file_search"}
        ]
    )
    
    print(f"Agent created: {agent.id}")
    
    # Create thread
    thread = agents_client.create_thread()
    
    # Add message
    message = agents_client.create_message(
        thread_id=thread.id,
        role="user",
        content="Write Python code to calculate fibonacci numbers"
    )
    
    # Run agent
    run = agents_client.create_and_process_run(
        thread_id=thread.id,
        assistant_id=agent.id
    )
    
    # Get messages
    messages = agents_client.list_messages(thread_id=thread.id)
    for msg in messages:
        print(f"{msg.role}: {msg.content[0].text.value}")
```

### REST API
```bash
# Get token
TOKEN=$(az account get-access-token \
  --resource https://cognitiveservices.azure.com \
  --query accessToken -o tsv)

# Create agent
curl -X POST \
  "https://<your-endpoint>/assistants?api-version=2024-05-01-preview" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o",
    "name": "Code Helper",
    "instructions": "You help users write better code.",
    "tools": [{"type": "code_interpreter"}]
  }'
```

## 🔐 Security Best Practices

### ✅ Implemented in Templates
- ✅ Managed Identity enabled
- ✅ Local auth (API keys) disabled
- ✅ EntraID authentication required
- ✅ HTTPS only for storage
- ✅ Public blob access disabled
- ✅ TLS 1.2 minimum

### 🔒 Production Recommendations
- Add Private Endpoints for network isolation
- Enable Customer-Managed Keys (CMK) for encryption
- Implement Azure Policy for governance
- Use Azure Key Vault for secrets
- Enable diagnostic logging
- Configure Azure Monitor alerts

## 📊 Monitoring & Troubleshooting

### View Deployment Status
```powershell
# List resources
az resource list --resource-group rg-aifoundry-dev --output table

# Check AI Foundry status
az cognitiveservices account show \
  --name <ai-foundry-name> \
  --resource-group rg-aifoundry-dev
```

### Common Issues

#### 1. Name Already Exists
**Error**: "The specified account name is already taken"
**Solution**: AI Foundry names must be globally unique. Change `aiFoundryName` parameter.

#### 2. Quota Exceeded
**Error**: "The subscription has reached its quota"
**Solution**: Request quota increase or delete unused resources.

#### 3. Region Not Supported
**Error**: "The location is not supported"
**Solution**: Use supported regions: eastus, westus2, northeurope, etc.

#### 4. Capability Host Conflict
**Error**: "There is an existing Capability Host"
**Solution**: Only one capability host per project. Delete existing or use existing.

#### 5. RBAC Permissions Delay
**Issue**: Agent fails to access storage immediately after deployment
**Solution**: Wait 1-2 minutes for RBAC propagation, then retry.

## 📚 References

### Official Documentation
- [Azure AI Foundry Documentation](https://learn.microsoft.com/azure/ai-foundry/)
- [Agent Service Documentation](https://learn.microsoft.com/azure/ai-foundry/agents/)
- [Capability Hosts Concept](https://learn.microsoft.com/azure/ai-foundry/agents/concepts/capability-hosts)
- [Standard Agent Setup](https://learn.microsoft.com/azure/ai-foundry/agents/concepts/standard-agent-setup)

### Official Samples
- [Azure AI Foundry Samples Repository](https://github.com/azure-ai-foundry/foundry-samples)
- [Basic Infrastructure Setup](https://github.com/azure-ai-foundry/foundry-samples/tree/main/samples/microsoft/infrastructure-setup/00-basic)
- [Agent Setup with Customization](https://github.com/azure-ai-foundry/foundry-samples/tree/main/samples/microsoft/infrastructure-setup/42-basic-agent-setup-with-customization)

### API References
- [Cognitive Services REST API](https://learn.microsoft.com/rest/api/cognitiveservices/)
- [BICEP Template Reference](https://learn.microsoft.com/azure/templates/microsoft.cognitiveservices/accounts)
- [Azure AI Projects SDK](https://learn.microsoft.com/python/api/azure-ai-projects/)

## 🧹 Clean Up

```powershell
# Delete resource group (removes all resources)
az group delete --name rg-aifoundry-dev --yes --no-wait
```

## 💡 Tips & Tricks

1. **Use unique names**: Add timestamps or GUIDs to avoid naming conflicts
2. **Start with Basic**: Test with basic setup before moving to standard
3. **Monitor costs**: Standard setup creates multiple billable resources
4. **Check region availability**: Not all regions support all models
5. **Test RBAC**: Verify managed identity has proper permissions after deployment
6. **Enable diagnostics**: Add diagnostic settings for production monitoring
7. **Tag resources**: Use tags for cost tracking and organization

## 🎓 Next Steps

After deploying your infrastructure:

1. **Visit Azure AI Foundry Portal**: https://ai.azure.com
2. **Select your project** from the project list
3. **Explore the playground** to test your model
4. **Create your first agent** using the SDK
5. **Add tools** like code interpreter, file search, or function calling
6. **Test agent capabilities** with different prompts
7. **Integrate into your application** using the REST API or SDK

## 🤝 Support

For issues or questions:
- **Azure Support**: https://azure.microsoft.com/support/
- **GitHub Issues**: https://github.com/Azure/azure-ai-foundry/issues
- **Documentation**: https://learn.microsoft.com/azure/ai-foundry/

---

**Last Updated**: October 2025
**API Version Used**: 2025-06-01
**Based on**: Official Microsoft Azure AI Foundry documentation and samples
