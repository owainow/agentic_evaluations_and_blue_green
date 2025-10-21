# Model Deployment and Agent Creation

This guide explains how to deploy AI models and create agents in Azure AI Foundry for testing and evaluation purposes.

## Overview

The `deploy-model-and-agent.yml` workflow allows you to:

1. **Deploy different AI models** (GPT-4o, GPT-4, GPT-3.5-turbo, etc.) to Azure AI Services
2. **Create agents** that use those specific model deployments
3. **Run A/B testing** by deploying multiple models with different agents
4. **Compare performance** across different model versions

## Quick Start

### 1. Run the Workflow

Navigate to **Actions** → **Deploy Model and Create Agent** → **Run workflow**

![Run Workflow](https://docs.github.com/assets/cb-26156/images/help/actions/workflow-dispatch-button.png)

### 2. Configure Your Deployment

| Parameter | Description | Example |
|-----------|-------------|---------|
| **Environment** | Target environment (dev/test/prod) | `dev` |
| **Model Name** | Which model to deploy | `gpt-4o` |
| **Model Version** | Specific version | `2024-11-20` |
| **Deployment Name** | Custom name (optional, auto-generated if empty) | `gpt-4o-experiment-1` |
| **SKU Name** | Deployment type | `Standard` |
| **Capacity** | TPM in thousands | `10` |
| **Agent Name** | Name for your agent | `customer-support-agent` |
| **Agent Instructions** | Behavior instructions | `You are a helpful customer support agent...` |

### 3. View Results

After the workflow completes, check the **Summary** for:
- Model deployment details
- Agent ID and configuration
- Useful commands for management

## Use Cases

### A/B Testing Different Models

Deploy the same agent with different models to compare:

```yaml
# Deployment 1: GPT-4o
Model: gpt-4o
Version: 2024-11-20
Agent: customer-support-agent
Instructions: "You are a helpful customer support agent."

# Deployment 2: GPT-4o-mini
Model: gpt-4o-mini
Version: 2024-07-18
Agent: customer-support-agent-mini
Instructions: "You are a helpful customer support agent."
```

Then run evaluations against both agents to compare:
- Response quality
- Latency
- Cost efficiency

### Blue/Green Deployment

1. **Deploy new model version (Green)**:
   - Model: `gpt-4o`
   - Version: `2024-11-20` (latest)
   - Deployment: `gpt-4o-green`
   - Agent: `support-agent-green`

2. **Keep existing model (Blue)**:
   - Model: `gpt-4o`
   - Version: `2024-08-06` (previous)
   - Deployment: `gpt-4o-blue`
   - Agent: `support-agent-blue`

3. **Run evaluations** on both
4. **Switch traffic** to green if successful
5. **Decommission blue** after validation

### Model Version Testing

Test new model versions before production:

```bash
# Test version 1
Deployment: gpt-4-test-v1
Model: gpt-4
Version: 0613

# Test version 2
Deployment: gpt-4-test-v2
Model: gpt-4
Version: turbo-2024-04-09
```

## Architecture

### What Gets Deployed

```
Azure AI Services Account (already exists)
  ├─ Model Deployment (new)
  │   ├─ Model: gpt-4o
  │   ├─ Version: 2024-11-20
  │   ├─ SKU: Standard
  │   └─ Capacity: 10K TPM
  │
Azure AI Foundry Project (already exists)
  └─ Agent (new)
      ├─ Name: customer-support-agent
      ├─ Model Deployment: gpt-4o-dev-20241021
      └─ Instructions: "You are a helpful..."
```

### Resource Naming

Auto-generated deployment names follow this pattern:
```
{model_name}-{environment}-{timestamp}

Examples:
- gpt-4o-dev-20241021-143022
- gpt-35-turbo-test-20241021-143145
```

## Available Models

| Model | Use Case | Cost | Speed |
|-------|----------|------|-------|
| **gpt-4o** | Best quality, reasoning | High | Medium |
| **gpt-4o-mini** | Balanced quality & cost | Low | Fast |
| **gpt-4** | Legacy quality | High | Medium |
| **gpt-4-turbo** | Quality + speed | High | Fast |
| **gpt-35-turbo** | Basic tasks, cost-effective | Low | Fast |
| **gpt-35-turbo-16k** | Longer context | Medium | Fast |

## SKU Types

| SKU | Description | Use Case |
|-----|-------------|----------|
| **Standard** | Regional deployment, pay-per-token | Development, testing |
| **GlobalStandard** | Global load balancing | Production with global users |
| **DataZoneStandard** | Data residency requirements | Compliance needs |

## Managing Deployments

### List All Deployments

```bash
az cognitiveservices account deployment list \
  --resource-group rg-aifoundry-dev \
  --name <ai-services-name> \
  --query '[].{Name:name, Model:properties.model.name, Version:properties.model.version, State:properties.provisioningState}' \
  -o table
```

### Delete a Deployment

```bash
az cognitiveservices account deployment delete \
  --resource-group rg-aifoundry-dev \
  --name <ai-services-name> \
  --deployment-name <deployment-name>
```

### Get Deployment Details

```bash
az cognitiveservices account deployment show \
  --resource-group rg-aifoundry-dev \
  --name <ai-services-name> \
  --deployment-name <deployment-name>
```

## Python Script Usage

You can also create agents programmatically:

```python
import os
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

credential = DefaultAzureCredential()
project_client = AIProjectClient.from_connection_string(
    credential=credential,
    conn_str="https://<resource>.services.ai.azure.com/api/projects/<project>"
)

agent = project_client.agents.create_agent(
    model="gpt-4o-dev-20241021",
    name="my-test-agent",
    instructions="You are a helpful assistant."
)

print(f"Agent created: {agent.id}")
```

## Troubleshooting

### Error: "No AI Services account found"

**Cause**: The infrastructure hasn't been deployed yet.

**Solution**: Run the `deploy-infrastructure.yml` workflow first.

### Error: "Insufficient quota for deployment"

**Cause**: Not enough TPM quota available.

**Solution**: 
1. Check current quota: `az cognitiveservices account list-usage`
2. Request quota increase in Azure portal
3. Reduce capacity parameter
4. Delete unused deployments

### Error: "Model version not available"

**Cause**: The specified model version doesn't exist in your region.

**Solution**:
1. Check available versions: [Azure OpenAI Models](https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/models)
2. Use a different version
3. Deploy in a different region

### Error: "Agent creation failed"

**Cause**: Project endpoint or authentication issues.

**Solution**:
1. Verify the project exists: `az ml workspace show`
2. Check RBAC permissions (need "Azure AI User" role)
3. Ensure Azure CLI is authenticated: `az login`

## Cost Optimization

### Model Selection

- **Development**: Use `gpt-4o-mini` for most testing
- **Quality Testing**: Use `gpt-4o` for final validation
- **Production**: Use `gpt-4o-mini` for high-volume, `gpt-4o` for critical tasks

### Capacity Planning

| Environment | Recommended TPM | Example Capacity |
|-------------|-----------------|------------------|
| **Dev** | 1K - 10K | 10 |
| **Test** | 10K - 50K | 30 |
| **Prod** | 50K+ | 100 |

### Cleanup Strategy

Delete unused deployments regularly:

```bash
# List old deployments
az cognitiveservices account deployment list \
  --resource-group rg-aifoundry-dev \
  --name <ai-services-name> \
  --query '[].{Name:name, Created:systemData.createdAt}' \
  -o table

# Delete deployments older than 7 days
# (Add your cleanup script here)
```

## Next Steps

1. **Deploy your first model and agent** using the workflow
2. **Create evaluation tests** in `evaluations/` directory
3. **Run evaluations** against different agent deployments
4. **Compare results** and choose the best performing model
5. **Promote to production** once validated

## Additional Resources

- [Azure AI Foundry Documentation](https://learn.microsoft.com/en-us/azure/ai-foundry/)
- [Azure OpenAI Models](https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/models)
- [Agent Development Guide](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/)
- [Evaluation Best Practices](https://learn.microsoft.com/en-us/azure/ai-foundry/evaluation/)
