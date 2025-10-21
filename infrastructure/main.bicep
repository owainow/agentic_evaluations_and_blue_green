// Azure AI Foundry Project with Agent Support - Main Template
// Based on official Microsoft documentation and samples

@description('Location for all resources')
param location string = resourceGroup().location

@description('Base name for the AI Foundry resource (will have suffixes added)')
param aiFoundryName string

@description('Name of the AI Foundry project')
param aiProjectName string

@description('Enable capability hosts for agents (required for agent support)')
param enableAgents bool = true

@description('Model deployment name')
param modelDeploymentName string = 'gpt-4o'

@description('Model name')
param modelName string = 'gpt-4o'

@description('Model version')
param modelVersion string = '2024-11-20'

@description('Model format/provider')
@allowed([
  'OpenAI'
  'Microsoft'
  'Meta'
  'Mistral AI'
  'Cohere'
])
param modelFormat string = 'OpenAI'

@description('SKU name for model deployment')
@allowed([
  'Standard'
  'GlobalStandard'
])
param deploymentSkuName string = 'Standard'

@description('Deployment capacity (TPM in thousands)')
param deploymentCapacity int = 10

// Create the Azure AI Foundry resource (Cognitive Services account of kind AIServices)
resource aiFoundryResource 'Microsoft.CognitiveServices/accounts@2025-06-01' = {
  name: aiFoundryName
  location: location
  kind: 'AIServices'
  identity: {
    type: 'SystemAssigned'
  }
  sku: {
    name: 'S0'
  }
  properties: {
    // Required for AI Foundry project management
    allowProjectManagement: true
    
    // Custom subdomain for EntraID authentication
    customSubDomainName: aiFoundryName
    
    // Disable API key authentication (use EntraID instead - recommended)
    disableLocalAuth: true
    
    // Public network access
    publicNetworkAccess: 'Enabled'
  }
}

// Create the Azure AI Foundry Project
resource aiFoundryProject 'Microsoft.CognitiveServices/accounts/projects@2025-06-01' = {
  name: aiProjectName
  parent: aiFoundryResource
  location: location
  properties: {
    description: 'Azure AI Foundry project for agent development'
    displayName: aiProjectName
  }
}

// Deploy the AI model (e.g., GPT-4o)
resource modelDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  name: modelDeploymentName
  parent: aiFoundryResource
  sku: {
    name: deploymentSkuName
    capacity: deploymentCapacity
  }
  properties: {
    model: {
      format: modelFormat
      name: modelName
      version: modelVersion
    }
  }
}

// Create Capability Host at Account level (required for agents)
resource accountCapabilityHost 'Microsoft.CognitiveServices/accounts/capabilityHosts@2025-06-01' = if (enableAgents) {
  name: 'agents-capability-host'
  parent: aiFoundryResource
  properties: {
    capabilityHostKind: 'Agents'
  }
  dependsOn: [
    aiFoundryProject
  ]
}

// Create Capability Host at Project level (for agent support)
// This uses the default managed multitenant storage (basic setup)
// For production, consider standard setup with your own storage resources
resource projectCapabilityHost 'Microsoft.CognitiveServices/accounts/projects/capabilityHosts@2025-06-01' = if (enableAgents) {
  name: 'agents-project-capability-host'
  parent: aiFoundryProject
  properties: {
    capabilityHostKind: 'Agents'
    // For basic setup, omit connection parameters to use managed storage
    // For standard setup, add: threadStorageConnections, vectorStoreConnections, storageConnections
  }
  dependsOn: [
    accountCapabilityHost
  ]
}

// Outputs
output aiFoundryResourceId string = aiFoundryResource.id
output aiFoundryResourceName string = aiFoundryResource.name
output aiFoundryEndpoint string = aiFoundryResource.properties.endpoint
output aiFoundryApiEndpoint string = aiFoundryResource.properties.endpoints['AI Foundry API']
output projectId string = aiFoundryProject.id
output projectName string = aiFoundryProject.name
output modelDeploymentName string = modelDeployment.name
output location string = location
