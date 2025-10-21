# GitHub Actions Workflows

This directory contains GitHub Actions workflows for deploying and managing Azure AI Foundry infrastructure.

## 🚀 Workflows

### 1. Deploy Infrastructure (`deploy-infrastructure.yml`)

Manually deploy Azure AI Foundry infrastructure with full configuration options.

**Trigger**: Manual (`workflow_dispatch`)

**Features**:
- ✅ Choose environment (dev, staging, prod)
- ✅ Select deployment type (basic or standard)
- ✅ Configure resource group and location
- ✅ Customize AI Foundry and project names
- ✅ Select model and deployment settings
- ✅ BICEP validation before deployment
- ✅ What-If analysis (shows resources that will be created)
- ✅ Automatic resource group creation
- ✅ Resource tagging
- ✅ Post-deployment verification
- ✅ Deployment summary with quick links

**Required Secrets**:
- `AZURE_CLIENT_ID` - Service Principal Client ID
- `AZURE_TENANT_ID` - Azure Tenant ID
- `AZURE_SUBSCRIPTION_ID` - Azure Subscription ID

**How to Run**:
1. Go to **Actions** tab in GitHub
2. Select **Deploy Azure AI Foundry Infrastructure**
3. Click **Run workflow**
4. Fill in the parameters
5. Click **Run workflow**

### 2. Destroy Infrastructure (`destroy-infrastructure.yml`)

Safely delete Azure AI Foundry resources with confirmation.

**Trigger**: Manual (`workflow_dispatch`)

**Features**:
- ⚠️ Requires explicit "DELETE" confirmation
- 📋 Lists resources before deletion
- 🗑️ Async deletion (non-blocking)
- 📊 Deletion summary

**Required Secrets**:
Same as deploy workflow

**How to Run**:
1. Go to **Actions** tab in GitHub
2. Select **Destroy Azure AI Foundry Infrastructure**
3. Click **Run workflow**
4. Select environment
5. Enter resource group name
6. **Type "DELETE"** in confirmation field
7. Click **Run workflow**

## 🔐 Setup Instructions

> **💡 Tip**: Run these commands in [Azure Cloud Shell](https://shell.azure.com) (bash mode) for the easiest setup experience. Cloud Shell is pre-configured with Azure CLI and proper authentication.

### 1. Create Azure Service Principal

Open [Azure Cloud Shell](https://shell.azure.com) and run:

```bash
# Get your subscription ID
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
echo "Subscription ID: $SUBSCRIPTION_ID"

# Create service principal with Contributor role
SP_OUTPUT=$(az ad sp create-for-rbac \
  --name "github-actions-aifoundry" \
  --role Contributor \
  --scopes /subscriptions/$SUBSCRIPTION_ID \
  --json-auth)

# Extract values
CLIENT_ID=$(echo $SP_OUTPUT | jq -r '.clientId')
TENANT_ID=$(echo $SP_OUTPUT | jq -r '.tenantId')

echo ""
echo "✅ Service Principal created successfully!"
echo ""
echo "📋 Save these values as GitHub Secrets:"
echo "   AZURE_CLIENT_ID: $CLIENT_ID"
echo "   AZURE_TENANT_ID: $TENANT_ID"
echo "   AZURE_SUBSCRIPTION_ID: $SUBSCRIPTION_ID"
echo ""
```

### 2. Configure GitHub OIDC Federation

Continue in Azure Cloud Shell:

```bash
# Set your GitHub repository details
REPO_OWNER="owainow"
REPO_NAME="agentic_evaluations_and_blue_green"

# Use the CLIENT_ID from step 1 (or set it manually)
# CLIENT_ID="<paste-your-client-id>"

echo "Setting up OIDC federation for $REPO_OWNER/$REPO_NAME..."

# Add federated credential for main branch
az ad app federated-credential create --id $CLIENT_ID --parameters "{
    \"name\": \"github-actions-main\",
    \"issuer\": \"https://token.actions.githubusercontent.com\",
    \"subject\": \"repo:$REPO_OWNER/$REPO_NAME:ref:refs/heads/main\",
    \"audiences\": [\"api://AzureADTokenExchange\"]
  }"

echo "✅ OIDC federation configured for main branch"

# Optional: Add federated credential for pull requests
az ad app federated-credential create \
  --id $CLIENT_ID \
  --parameters "{
    \"name\": \"github-actions-pr\",
    \"issuer\": \"https://token.actions.githubusercontent.com\",
    \"subject\": \"repo:$REPO_OWNER/$REPO_NAME:pull_request\",
    \"audiences\": [\"api://AzureADTokenExchange\"]
  }"

echo "✅ OIDC federation configured for pull requests"

# Verify federated credentials
echo ""
echo "📋 Configured federated credentials:"
az ad app federated-credential list --id $CLIENT_ID --query "[].{Name:name, Subject:subject}" -o table
```

### 3. Add Secrets to GitHub

#### Option A: Using GitHub CLI (Recommended)

If you have GitHub CLI installed locally (not available in Azure Cloud Shell):

```bash
# Copy these values from step 1 output
export CLIENT_ID="your-client-id"
export TENANT_ID="your-tenant-id"
export SUBSCRIPTION_ID="your-subscription-id"
export REPO_OWNER="owainow"
export REPO_NAME="agentic_evaluations_and_blue_green"

# Login to GitHub
gh auth login

# Set the secrets
gh secret set AZURE_CLIENT_ID --body "$CLIENT_ID" --repo $REPO_OWNER/$REPO_NAME
gh secret set AZURE_TENANT_ID --body "$TENANT_ID" --repo $REPO_OWNER/$REPO_NAME
gh secret set AZURE_SUBSCRIPTION_ID --body "$SUBSCRIPTION_ID" --repo $REPO_OWNER/$REPO_NAME

echo "✅ GitHub secrets configured!"
```

#### Option B: Using GitHub Web UI

1. Go to your repository: `https://github.com/owainow/agentic_evaluations_and_blue_green`
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add the following secrets (copy values from step 1 output):
   - `AZURE_CLIENT_ID`: Your service principal client ID
   - `AZURE_TENANT_ID`: Your Azure tenant ID
   - `AZURE_SUBSCRIPTION_ID`: Your Azure subscription ID

### 4. Configure Environments (Optional but Recommended)

Create GitHub environments for approval gates:

1. **Settings** → **Environments**
2. Create environments: `dev`, `staging`, `prod`
3. For `prod`, add:
   - **Required reviewers**: Add team members
   - **Wait timer**: 5 minutes
   - **Deployment branches**: Only `main`

## 📋 Workflow Parameters

### Deploy Infrastructure

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `environment` | choice | `dev` | Deployment environment |
| `deployment_type` | choice | `basic` | Basic or Standard setup |
| `resource_group_name` | string | `rg-aifoundry-dev` | Resource group name |
| `location` | choice | `eastus` | Azure region |
| `ai_foundry_name` | string | auto-generated | AI Foundry resource name |
| `ai_project_name` | string | `agent-project` | Project name |
| `model_deployment_name` | string | `gpt-4o` | Model deployment name |
| `model_name` | choice | `gpt-4o` | Model to deploy |

### Destroy Infrastructure

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `environment` | choice | `dev` | Environment to destroy |
| `resource_group_name` | string | `rg-aifoundry-dev` | Resource group to delete |
| `confirm_delete` | string | (required) | Type "DELETE" to confirm |

## 🎯 Best Practices

### Development Workflow

1. **Start with Dev**
   - Deploy to `dev` environment first
   - Test agent creation and functionality
   - Validate deployment outputs

2. **Progress to Staging**
   - Use same configuration as prod
   - Run integration tests
   - Validate with standard setup

3. **Deploy to Production**
   - Require manual approval
   - Use standard deployment type
   - Enable all monitoring

### Security

✅ **Use OIDC Federation** (passwordless authentication)  
✅ **Protect production environment** with required reviewers  
✅ **Tag all resources** for cost tracking  
✅ **Use managed identities** (templates already do this)  
✅ **Disable local auth** (templates already do this)  

### Cost Management

💰 **Dev Environment**:
- Use basic deployment type
- Lower model capacity (10K TPM)
- Delete when not in use

💰 **Production Environment**:
- Use standard deployment type
- Appropriate model capacity
- Enable monitoring and alerts

## 📊 Workflow Outputs

After successful deployment, the workflow provides:

1. **GitHub Step Summary**:
   - Deployment details table
   - Quick links to Azure Portal and AI Foundry
   - Code sample for creating first agent

2. **Artifact**:
   - `deployment-info-{environment}.txt` with all outputs
   - Retained for 90 days

3. **Job Outputs**:
   - `ai_foundry_name`: Resource name
   - `project_name`: Project name
   - `endpoint`: API endpoint
   - `resource_group`: Resource group name

## 🐛 Troubleshooting

### Authentication Issues

**Error**: "Failed to login to Azure"

**Solution**: Verify OIDC federation is configured correctly (in Azure Cloud Shell):
```bash
# Check federated credentials
az ad app federated-credential list --id $CLIENT_ID --output table

# Verify the subject matches your repository
# Should show: repo:owainow/agentic_evaluations_and_blue_green:ref:refs/heads/main
```

**Error**: "AADSTS70021: No matching federated identity record found"

**Solution**: The repository subject doesn't match. Verify repository name and branch:
```bash
# Delete incorrect credential
az ad app federated-credential delete --id $CLIENT_ID --federated-credential-id <CREDENTIAL-ID>

# Re-create with correct values
az ad app federated-credential create \
  --id $CLIENT_ID \
  --parameters "{
    \"name\": \"github-actions-main\",
    \"issuer\": \"https://token.actions.githubusercontent.com\",
    \"subject\": \"repo:owainow/agentic_evaluations_and_blue_green:ref:refs/heads/main\",
    \"audiences\": [\"api://AzureADTokenExchange\"]
  }"
```

### Deployment Failures

**Error**: "The specified account name is already taken"

**Solution**: Provide a unique `ai_foundry_name` parameter in the workflow or let it auto-generate

**Error**: "Quota exceeded"

**Solution**: Check and request quota increase:
```bash
# Check current quota usage
az cognitiveservices account list-usage \
  --name <your-resource-name> \
  --resource-group <your-rg>

# Request quota increase via Azure Portal or support ticket
```

### Permission Issues

**Error**: "Authorization failed"

**Solution**: Verify service principal has Contributor role:
```bash
# Check role assignments
az role assignment list \
  --assignee $CLIENT_ID \
  --output table

# If missing, add Contributor role
az role assignment create \
  --assignee $CLIENT_ID \
  --role Contributor \
  --scope /subscriptions/$SUBSCRIPTION_ID
```

### BICEP Validation Errors

**Error**: BICEP compilation fails in workflow

**Solution**: Test locally in Cloud Shell:
```bash
# Clone your repository
git clone https://github.com/owainow/agentic_evaluations_and_blue_green.git
cd agentic_evaluations_and_blue_green

# Test BICEP compilation
az bicep build --file infrastructure/main.bicep
az bicep build --file infrastructure/main.standard.bicep

# Run what-if to preview changes
az deployment group what-if \
  --resource-group rg-aifoundry-dev \
  --template-file infrastructure/main.bicep \
  --parameters aiFoundryName=test-foundry location=eastus
```

## 📚 Additional Resources

- [Azure AI Foundry Documentation](https://learn.microsoft.com/azure/ai-foundry/)
- [GitHub Actions Documentation](https://docs.github.com/actions)
- [OIDC with Azure](https://docs.github.com/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-azure)
- [Infrastructure Templates](../infrastructure/README.md)

## 🔄 Example Workflow Run

```bash
# Typical dev deployment:
Environment: dev
Deployment Type: basic
Resource Group: rg-aifoundry-dev
Location: eastus
Model: gpt-4o

# Results in:
- 1 AI Foundry resource
- 1 Project
- 1 Model deployment
- 2 Capability hosts
- Total time: ~5-7 minutes
```

---

**Last Updated**: October 2025  
**GitHub Actions Version**: v4  
**Azure CLI Version**: Latest
