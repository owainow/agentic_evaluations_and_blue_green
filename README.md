# Azure AI Foundry - Automated Agent Evaluation and Blue/Green Deployment

A comprehensive repository demonstrating Azure AI Foundry infrastructure deployment, automated agentic evaluations, and blue/green model deployment strategies using GitHub Actions.

## 🏗️ Infrastructure

This repository includes complete **BICEP infrastructure-as-code templates** to deploy Azure AI Foundry with full agent support.

### Quick Deploy

```powershell
# Deploy using PowerShell
cd infrastructure
.\deploy.ps1 -ResourceGroupName "rg-aifoundry-dev" -Location "eastus"
```

### What Gets Deployed

✅ **Azure AI Foundry Resource** with managed identity and EntraID authentication  
✅ **Azure AI Foundry Project** ready for agent development  
✅ **Model Deployment** (GPT-4o by default, configurable)  
✅ **Capability Hosts** for agent support (account + project level)  
✅ **Optional Standard Setup** with dedicated Storage, Cosmos DB, and AI Search  

### Templates Available

- **`infrastructure/main.bicep`** - Basic setup (managed storage, quick start)
- **`infrastructure/main.standard.bicep`** - Production setup (dedicated resources)
- **Deployment scripts** for PowerShell and Bash
- **Complete documentation** in `infrastructure/GUIDE.md`

📖 **Full documentation**: See [`infrastructure/README.md`](infrastructure/README.md) and [`infrastructure/GUIDE.md`](infrastructure/GUIDE.md)

## 🎯 Project Goals

This repository demonstrates:
- ✅ Infrastructure-as-code deployment of Azure AI Foundry
- ✅ Model deployment and agent creation workflows
- 🔄 GitHub Actions for agentic evaluations  
- 🚦 Blue/green model deployment strategies  
- 🤖 Agent creation and management best practices

## 🤖 Model Deployment & Agent Creation

Deploy AI models and create agents with different configurations for testing and evaluation.

### Quick Start

1. **Go to Actions** → **Deploy Model and Create Agent**
2. **Select your configuration**:
   - Model: `gpt-4o`, `gpt-4o-mini`, `gpt-35-turbo`, etc.
   - Environment: dev/test/prod
   - Agent name and instructions
3. **Run workflow** - Model deploys and agent is created automatically

### Use Cases

- **A/B Testing**: Deploy same agent with different models (GPT-4o vs GPT-4o-mini)
- **Blue/Green**: Test new model versions before production switch
- **Cost Optimization**: Compare model performance vs cost
- **Version Testing**: Validate new model versions

📖 **Full Guide**: See [`docs/MODEL_DEPLOYMENT_GUIDE.md`](docs/MODEL_DEPLOYMENT_GUIDE.md) 
