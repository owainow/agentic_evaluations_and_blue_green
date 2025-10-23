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

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: '${baseName}st${environment}${uniqueSuffix}'
  location: location
  tags: tags
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    accessTier: 'Hot'
    allowBlobPublicAccess: false
    allowSharedKeyAccess: false // Disable shared key access for security
    dnsEndpointType: 'Standard'
    minimumTlsVersion: 'TLS1_2'
    networkAcls: {
      bypass: 'AzureServices'
      defaultAction: 'Allow'
    }
    publicNetworkAccess: 'Enabled'
  }
  
  resource blobServices 'blobServices' = {
    name: 'default'
    properties: {
      deleteRetentionPolicy: {}
    }
    
    resource deploymentContainer 'containers' = {
      name: 'app-package-${take(baseName, 32)}-${take(uniqueSuffix, 7)}'
      properties: {
        publicAccess: 'None'
      }
    }
  }
}

// ============================================================================
// MANAGED IDENTITY (for Function App)
// ============================================================================
// User-assigned managed identity is recommended for Flex Consumption

resource userAssignedIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: '${baseName}-identity-${environment}-${uniqueSuffix}'
  location: location
  tags: tags
}

// ============================================================================
// APP SERVICE PLAN (for Azure Functions Flex Consumption)
// ============================================================================
// Using Flex Consumption plan - no "Dynamic VMs" quota needed, better performance

resource appServicePlan 'Microsoft.Web/serverfarms@2024-04-01' = {
  name: '${baseName}-asp-${environment}-${uniqueSuffix}'
  location: location
  tags: tags
  kind: 'functionapp'
  sku: {
    tier: 'FlexConsumption'
    name: 'FC1'
  }
  properties: {
    reserved: true // Required for Linux
  }
}

// ============================================================================
// FUNCTION APP (Agent Tool Functions - Flex Consumption)
// ============================================================================

resource functionApp 'Microsoft.Web/sites@2024-04-01' = {
  name: functionAppName != '' ? functionAppName : '${baseName}-func-${environment}-${uniqueSuffix}'
  location: location
  tags: union(tags, {
    Purpose: 'Agent Function Tools'
  })
  kind: 'functionapp,linux'
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${userAssignedIdentity.id}': {}
    }
  }
  properties: {
    serverFarmId: appServicePlan.id
    httpsOnly: true
    siteConfig: {
      minTlsVersion: '1.2'
    }
    functionAppConfig: {
      deployment: {
        storage: {
          type: 'blobContainer'
          value: '${storageAccount.properties.primaryEndpoints.blob}${storageAccount::blobServices::deploymentContainer.name}'
          authentication: {
            type: 'UserAssignedIdentity'
            userAssignedIdentityResourceId: userAssignedIdentity.id
          }
        }
      }
      scaleAndConcurrency: {
        alwaysReady: [
          {
            name: 'http'
            instanceCount: 1
          }
        ]
        maximumInstanceCount: 100
        instanceMemoryMB: 2048
      }
      runtime: {
        name: 'python'
        version: '3.11'
      }
    }
  }
  
  resource configAppSettings 'config' = {
    name: 'appsettings'
    properties: {
      AzureWebJobsStorage__accountName: storageAccount.name
      AzureWebJobsStorage__credential: 'managedidentity'
      AzureWebJobsStorage__clientId: userAssignedIdentity.properties.clientId
      FUNCTIONS_EXTENSION_VERSION: '~4'
      APPLICATIONINSIGHTS_CONNECTION_STRING: applicationInsights.properties.ConnectionString
      APPLICATIONINSIGHTS_AUTHENTICATION_STRING: 'ClientId=${userAssignedIdentity.properties.clientId};Authorization=AAD'
      PYTHON_ISOLATE_WORKER_DEPENDENCIES: '1'
      // Enable detailed logging
      AzureWebJobsDisableHomepage: 'true'
      // Note: FUNCTIONS_WORKER_RUNTIME is automatically set by Flex Consumption plan
      // Note: ENABLE_ORYX_BUILD and SCM_DO_BUILD_DURING_DEPLOYMENT are not supported in Flex Consumption
      // Build process is handled by the function app deployment command instead
    }
  }
}

// ============================================================================
// LOG ANALYTICS WORKSPACE (for Application Insights)
// ============================================================================

resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: '${baseName}-logs-${environment}-${uniqueSuffix}'
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
    features: {
      enableLogAccessUsingOnlyResourcePermissions: true
    }
    workspaceCapping: {
      dailyQuotaGb: 1 // Set a daily quota to control costs
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
    DisableLocalAuth: true
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
    WorkspaceResourceId: logAnalyticsWorkspace.id
  }
}

// ============================================================================
// RBAC ASSIGNMENTS (Managed Identity Permissions)
// ============================================================================

// Define role IDs as variables for clarity
var storageBlobDataOwnerRoleId = 'b7e6dc6d-f1e8-4753-8033-0f276bb0955b'
var storageBlobDataContributorRoleId = 'ba92f5b4-2d11-453d-a403-e96b0029c9fe'
var storageQueueDataContributorRoleId = '974c5e8b-45b9-4653-ba55-5f855dd0fb88'
var storageTableDataContributorRoleId = '0a9a7e1f-b9d0-4cc4-a60d-0319b160aaa3'
var monitoringMetricsPublisherRoleId = '3913510d-42f4-4e42-8a64-420c390055eb'

// User-assigned identity needs Storage Blob Data Owner
resource roleAssignmentBlobDataOwner 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(subscription().id, storageAccount.id, userAssignedIdentity.id, 'Storage Blob Data Owner')
  scope: storageAccount
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', storageBlobDataOwnerRoleId)
    principalId: userAssignedIdentity.properties.principalId
    principalType: 'ServicePrincipal'
    description: 'Grants managed identity access to storage blobs'
  }
}

// User-assigned identity needs Storage Blob Data Contributor  
resource roleAssignmentBlob 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(subscription().id, storageAccount.id, userAssignedIdentity.id, 'Storage Blob Data Contributor')
  scope: storageAccount
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', storageBlobDataContributorRoleId)
    principalId: userAssignedIdentity.properties.principalId
    principalType: 'ServicePrincipal'
    description: 'Grants managed identity access to storage blob operations'
  }
}

// User-assigned identity needs Storage Queue Data Contributor
resource roleAssignmentQueueStorage 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(subscription().id, storageAccount.id, userAssignedIdentity.id, 'Storage Queue Data Contributor')
  scope: storageAccount
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', storageQueueDataContributorRoleId)
    principalId: userAssignedIdentity.properties.principalId
    principalType: 'ServicePrincipal'
    description: 'Grants managed identity access to storage queues'
  }
}

// User-assigned identity needs Storage Table Data Contributor
resource roleAssignmentTableStorage 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(subscription().id, storageAccount.id, userAssignedIdentity.id, 'Storage Table Data Contributor')
  scope: storageAccount
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', storageTableDataContributorRoleId)
    principalId: userAssignedIdentity.properties.principalId
    principalType: 'ServicePrincipal'
    description: 'Grants managed identity access to storage tables'
  }
}

// User-assigned identity needs Monitoring Metrics Publisher for Application Insights
resource roleAssignmentAppInsights 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(subscription().id, applicationInsights.id, userAssignedIdentity.id, 'Monitoring Metrics Publisher')
  scope: applicationInsights
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', monitoringMetricsPublisherRoleId)
    principalId: userAssignedIdentity.properties.principalId
    principalType: 'ServicePrincipal'
    description: 'Grants managed identity access to publish metrics to Application Insights'
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
output functionAppPrincipalId string = userAssignedIdentity.properties.principalId
output userAssignedIdentityId string = userAssignedIdentity.id
output userAssignedIdentityClientId string = userAssignedIdentity.properties.clientId
output storageAccountName string = storageAccount.name
output applicationInsightsName string = applicationInsights.name
output applicationInsightsConnectionString string = applicationInsights.properties.ConnectionString
output applicationInsightsInstrumentationKey string = applicationInsights.properties.InstrumentationKey
output logAnalyticsWorkspaceName string = logAnalyticsWorkspace.name
output logAnalyticsWorkspaceId string = logAnalyticsWorkspace.id
