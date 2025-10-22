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
// APP SERVICE PLAN (for Azure Functions Flex Consumption)
// ============================================================================
// Using Flex Consumption plan - no "Dynamic VMs" quota needed, better performance

resource appServicePlan 'Microsoft.Web/serverfarms@2023-12-01' = {
  name: '${baseName}-asp-${environment}-${uniqueSuffix}'
  location: location
  tags: tags
  sku: {
    name: 'FC1'
    tier: 'FlexConsumption'
  }
  properties: {
    reserved: true // Required for Linux
  }
}

// ============================================================================
// FUNCTION APP (Agent Tool Functions - Flex Consumption)
// ============================================================================

resource functionApp 'Microsoft.Web/sites@2023-12-01' = {
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
    functionAppConfig: {
      deployment: {
        storage: {
          type: 'blobContainer'
          value: '${storageAccount.properties.primaryEndpoints.blob}deployments'
          authentication: {
            type: 'SystemAssignedIdentity'
          }
        }
      }
      scaleAndConcurrency: {
        maximumInstanceCount: 100
        instanceMemoryMB: 2048
      }
      runtime: {
        name: 'python'
        version: '3.11'
      }
    }
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.11'
      appSettings: [
        {
          name: 'AzureWebJobsStorage__accountName'
          value: storageAccount.name
        }
        {
          name: 'AzureWebJobsStorage__credential'
          value: 'managedidentity'
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
// RBAC ASSIGNMENTS (Managed Identity Permissions)
// ============================================================================

// Function App needs Storage Blob Data Owner to access deployment storage
resource functionAppStorageBlobDataOwner 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storageAccount.id, functionApp.id, 'b7e6dc6d-f1e8-4753-8033-0f276bb0955b')
  scope: storageAccount
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'b7e6dc6d-f1e8-4753-8033-0f276bb0955b') // Storage Blob Data Owner
    principalId: functionApp.identity.principalId
    principalType: 'ServicePrincipal'
    description: 'Grants Function App access to storage for deployments and data'
  }
}

// Function App needs Storage Account Contributor for WebJobs storage
resource functionAppStorageAccountContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storageAccount.id, functionApp.id, 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')
  scope: storageAccount
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe') // Storage Account Contributor
    principalId: functionApp.identity.principalId
    principalType: 'ServicePrincipal'
    description: 'Grants Function App management access to storage account'
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
