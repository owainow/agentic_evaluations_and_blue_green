// Azure AI Foundry Template (Correct Architecture for Agent Service GA)
// This uses Microsoft.CognitiveServices/accounts (NEW) instead of Microsoft.MachineLearningServices/workspaces (OLD)

@description('Azure region for all resources')
param location string = resourceGroup().location

@description('Base name for all resources')
@minLength(2)
@maxLength(10)
param baseName string = 'aif'

@description('Environment name (dev, test, prod)')
@allowed([
  'dev'
  'test'
  'prod'
])
param environment string = 'dev'

@description('Tags to apply to all resources')
param tags object = {
  Environment: environment
  ManagedBy: 'Bicep'
  Project: 'AzureAIFoundry'
}

// Variables
var uniqueSuffix = substring(uniqueString(resourceGroup().id), 0, 6)
var aiFoundryName = '${baseName}-foundry-${environment}-${uniqueSuffix}'
var projectName = '${baseName}-project-${environment}-${uniqueSuffix}'

// ============================================================================
// AZURE AI FOUNDRY RESOURCE (New Architecture - CognitiveServices)
// ============================================================================
// This is the correct resource type for Azure AI Foundry Agent Service (GA)
// Endpoint format: https://{aiFoundryName}.services.ai.azure.com/api/projects/{projectName}

resource aiFoundry 'Microsoft.CognitiveServices/accounts@2025-04-01-preview' = {
  name: aiFoundryName
  location: location
  tags: tags
  kind: 'AIServices'
  sku: {
    name: 'S0'
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    // Required for project management
    allowProjectManagement: true
    
    // This becomes the subdomain for the endpoint
    // Endpoint will be: https://{customSubDomainName}.services.ai.azure.com/api/projects/{projectName}
    customSubDomainName: aiFoundryName
    
    // Networking
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      defaultAction: 'Allow'
      virtualNetworkRules: []
      ipRules: []
    }
    
    // Authentication
    disableLocalAuth: false
  }
}

// ============================================================================
// AZURE AI FOUNDRY PROJECT (Child Resource)
// ============================================================================

resource aiProject 'Microsoft.CognitiveServices/accounts/projects@2025-04-01-preview' = {
  parent: aiFoundry
  name: projectName
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    description: 'Azure AI Foundry Project for Agent deployment'
    displayName: projectName
  }
}

// ============================================================================
// OUTPUTS
// ============================================================================

output aiFoundryName string = aiFoundry.name
output aiFoundryId string = aiFoundry.id
output aiFoundryEndpoint string = aiFoundry.properties.endpoint
output projectName string = aiProject.name
output projectId string = aiProject.id

// This is the endpoint format needed for the Agent Service SDK
output projectEndpoint string = 'https://${aiFoundry.name}.services.ai.azure.com/api/projects/${aiProject.name}'
