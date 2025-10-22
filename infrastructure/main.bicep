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

@description('Custom name for the Function App (optional)')
param functionAppName string = ''

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
// STORAGE ACCOUNT (Required for Azure Functions)
// ============================================================================

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: '${baseName}st${environment}${uniqueSuffix}'
  location: location
  tags: tags
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    supportsHttpsTrafficOnly: true
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
    networkAcls: {
      defaultAction: 'Allow'
      bypass: 'AzureServices'
    }
  }
}

// ============================================================================
// APP SERVICE PLAN (for Azure Functions)
// ============================================================================
// Using Consumption (Y1) plan for cost-effective serverless scaling

resource appServicePlan 'Microsoft.Web/serverfarms@2023-01-01' = {
  name: '${baseName}-asp-${environment}-${uniqueSuffix}'
  location: location
  tags: tags
  sku: {
    name: 'Y1'
    tier: 'Dynamic'
  }
  properties: {
    reserved: true // Required for Linux
  }
}

// ============================================================================
// FUNCTION APP (Agent Tool Functions)
// ============================================================================

resource functionApp 'Microsoft.Web/sites@2023-01-01' = {
  name: functionAppName != '' ? functionAppName : '${baseName}-func-${environment}-${uniqueSuffix}'
  location: location
  tags: union(tags, {
    Purpose: 'Agent Function Tools'
  })
  kind: 'functionapp,linux'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    serverFarmId: appServicePlan.id
    httpsOnly: true
    reserved: true
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.11'
      appSettings: [
        {
          name: 'AzureWebJobsStorage'
          value: 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};AccountKey=${storageAccount.listKeys().keys[0].value};EndpointSuffix=${az.environment().suffixes.storage}'
        }
        {
          name: 'WEBSITE_CONTENTAZUREFILECONNECTIONSTRING'
          value: 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};AccountKey=${storageAccount.listKeys().keys[0].value};EndpointSuffix=${az.environment().suffixes.storage}'
        }
        {
          name: 'WEBSITE_CONTENTSHARE'
          value: toLower('${baseName}-func-${environment}')
        }
        {
          name: 'FUNCTIONS_EXTENSION_VERSION'
          value: '~4'
        }
        {
          name: 'FUNCTIONS_WORKER_RUNTIME'
          value: 'python'
        }
        {
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
          value: applicationInsights.properties.ConnectionString
        }
        {
          name: 'PYTHON_ISOLATE_WORKER_DEPENDENCIES'
          value: '1'
        }
        {
          name: 'ENABLE_ORYX_BUILD'
          value: 'true'
        }
        {
          name: 'SCM_DO_BUILD_DURING_DEPLOYMENT'
          value: 'true'
        }
      ]
      cors: {
        allowedOrigins: [
          'https://portal.azure.com'
          'https://ms.portal.azure.com'
        ]
        supportCredentials: false
      }
      ftpsState: 'Disabled'
      minTlsVersion: '1.2'
      use32BitWorkerProcess: false
      pythonVersion: '3.11'
    }
  }
}

// ============================================================================
// APPLICATION INSIGHTS (for monitoring Functions)
// ============================================================================

resource applicationInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: '${baseName}-appins-${environment}-${uniqueSuffix}'
  location: location
  tags: tags
  kind: 'web'
  properties: {
    Application_Type: 'web'
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
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

// Function App outputs
output functionAppName string = functionApp.name
output functionAppUrl string = 'https://${functionApp.properties.defaultHostName}'
output functionAppPrincipalId string = functionApp.identity.principalId
output storageAccountName string = storageAccount.name
output applicationInsightsName string = applicationInsights.name
output applicationInsightsConnectionString string = applicationInsights.properties.ConnectionString
