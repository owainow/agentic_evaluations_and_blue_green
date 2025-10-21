# Quick Reference - Azure AI Foundry BICEP Deployment

## 🚀 One-Command Deployment

### PowerShell
```powershell
cd infrastructure; .\deploy.ps1
```

### Bash
```bash
cd infrastructure && ./deploy.sh
```

## 📝 Files You Need to Edit

### 1. Parameters File (`main.parameters.json`)
```json
{
  "aiFoundryName": { "value": "YOUR-UNIQUE-NAME" },
  "aiProjectName": { "value": "YOUR-PROJECT-NAME" }
}
```

### 2. Model Configuration (Optional)
```json
{
  "modelDeploymentName": { "value": "gpt-4o" },
  "modelName": { "value": "gpt-4o" },
  "deploymentCapacity": { "value": 10 }
}
```

## 🎯 Deployment Outputs

After successful deployment, you'll get:
- `aiFoundryResourceName` - Your AI Foundry resource name
- `aiFoundryEndpoint` - API endpoint for the service
- `aiFoundryApiEndpoint` - AI Foundry API endpoint
- `projectName` - Your project name
- `modelDeploymentName` - Deployed model name

## 🔗 Quick Links After Deployment

1. **Azure AI Foundry Portal**: https://ai.azure.com
2. **Your Project**: Find it in the portal using the `projectName` output
3. **Azure Portal**: Check resources in your resource group

## 🤖 Create Your First Agent (Python)

```python
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

# Use endpoint from deployment output
client = AIProjectClient(
    endpoint="YOUR_PROJECT_ENDPOINT",
    credential=DefaultAzureCredential()
)

with client:
    agent = client.agents.create_agent(
        model="gpt-4o",
        name="my-first-agent",
        instructions="You are a helpful assistant."
    )
    print(f"Created: {agent.id}")
```

## 🛠️ Common Commands

### Check Deployment Status
```bash
az deployment group show \
  --name <deployment-name> \
  --resource-group <rg-name> \
  --query properties.outputs
```

### List Resources
```bash
az resource list --resource-group <rg-name> --output table
```

### Delete Everything
```bash
az group delete --name <rg-name> --yes --no-wait
```

## ⚡ Template Comparison

| Feature | Basic Setup | Standard Setup |
|---------|-------------|----------------|
| File | `main.bicep` | `main.standard.bicep` |
| Storage | Managed (Microsoft) | Your own (Storage Account) |
| Cosmos DB | Managed | Your own |
| AI Search | Managed | Your own |
| Best For | Dev/Test/POC | Production |
| Setup Time | ~5 min | ~10 min |
| Cost | Lower | Higher |

## 🔐 Authentication

Templates use **EntraID authentication only** (API keys disabled for security).

To authenticate:
```bash
# Azure CLI
az login

# Get token
TOKEN=$(az account get-access-token \
  --resource https://cognitiveservices.azure.com \
  --query accessToken -o tsv)
```

## 💰 Cost Estimate (Basic Setup)

- AI Foundry (S0): ~$0 + usage
- Model Deployment (10K TPM): Pay-as-you-go
- Managed Storage: Minimal
- **Total**: Depends on usage, typically $10-50/month for light dev use

## 📞 Need Help?

- 📖 Full Guide: `infrastructure/GUIDE.md`
- 📘 README: `infrastructure/README.md`
- 🌐 Docs: https://learn.microsoft.com/azure/ai-foundry/
- 💬 Issues: https://github.com/Azure/azure-ai-foundry/issues

## ✅ Pre-Deployment Checklist

- [ ] Azure CLI installed (`az --version`)
- [ ] Logged into Azure (`az login`)
- [ ] Correct subscription selected
- [ ] Unique name chosen for `aiFoundryName`
- [ ] Region supports AI Foundry (eastus, westus2, etc.)
- [ ] Sufficient quota in subscription

## 🎉 You're Ready!

Just run:
```powershell
cd infrastructure
.\deploy.ps1
```

Wait ~5 minutes, and your Azure AI Foundry project with agent support will be ready! 🚀
