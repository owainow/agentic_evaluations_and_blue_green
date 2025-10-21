// Standard BICEP template for Azure AI Foundry with Agent (Production Configuration)
// This template creates production-ready Azure AI Foundry Hub and Project with dedicated resources
// Architecture: Hub (kind: 'hub') + Project (kind: 'Project') + AI Services + optional Cosmos DB + AI Search

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
param environment string = 'prod'

@description('Tags to apply to all resources')
param tags object = {
  Environment: environment
  ManagedBy: 'Bicep'
  Project: 'AzureAIFoundry'
}

@description('Enable Cosmos DB for project storage')
param enableCosmosDb bool = true

@description('Enable AI Search for enhanced capabilities')
param enableAISearch bool = true

// Variables
var uniqueSuffix = substring(uniqueString(resourceGroup().id), 0, 6)
var aiHubName = '${baseName}-hub-${environment}-${uniqueSuffix}'
var projectName = '${baseName}-project-${environment}-${uniqueSuffix}'
var aiServicesName = '${baseName}-ais-${environment}-${uniqueSuffix}'
var storageName = replace('${baseName}st${environment}${uniqueSuffix}', '-', '')
var keyVaultName = '${baseName}-kv-${environment}-${uniqueSuffix}'
var appInsightsName = '${baseName}-ai-${environment}-${uniqueSuffix}'
var containerRegistryName = replace('${baseName}cr${environment}${uniqueSuffix}', '-', '')
var cosmosDbAccountName = '${baseName}-cosmos-${environment}-${uniqueSuffix}'
var searchServiceName = '${baseName}-search-${environment}-${uniqueSuffix}'

// ============================================================================
// STORAGE ACCOUNT (Premium with GRS)
// ============================================================================

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageName
  location: location
  tags: tags
  sku: {
    name: 'Standard_GRS' // Geo-redundant for production
  }
  kind: 'StorageV2'
  properties: {
    accessTier: 'Hot'
    allowBlobPublicAccess: false
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    encryption: {
      services: {
        blob: {
          enabled: true
        }
        file: {
          enabled: true
        }
      }
      keySource: 'Microsoft.Storage'
    }
    networkAcls: {
      defaultAction: 'Deny'
      bypass: 'AzureServices'
    }
  }
}

// ============================================================================
// KEY VAULT (Premium)
// ============================================================================

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: keyVaultName
  location: location
  tags: tags
  properties: {
    sku: {
      family: 'A'
      name: 'premium' // Premium SKU for production
    }
    tenantId: subscription().tenantId
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 90
    enablePurgeProtection: true // Required for production
    enabledForDeployment: false
    enabledForDiskEncryption: true
    enabledForTemplateDeployment: false
    publicNetworkAccess: 'Enabled'
  }
}

// ============================================================================
// APPLICATION INSIGHTS
// ============================================================================

resource applicationInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  tags: tags
  kind: 'web'
  properties: {
    Application_Type: 'web'
    DisableIpMasking: false
    DisableLocalAuth: false
    Flow_Type: 'Bluefield'
    ForceCustomerStorageForProfiler: false
    ImmediatePurgeDataOn30Days: false // Keep logs longer in production
    IngestionMode: 'ApplicationInsights'
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
    Request_Source: 'rest'
  }
}

// ============================================================================
// CONTAINER REGISTRY (Standard for production)
// ============================================================================

resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: containerRegistryName
  location: location
  tags: tags
  sku: {
    name: 'Standard' // Standard SKU for production
  }
  properties: {
    adminUserEnabled: true
    publicNetworkAccess: 'Enabled'
  }
}

// ============================================================================
// COSMOS DB (Optional)
// ============================================================================

resource cosmosDbAccount 'Microsoft.DocumentDB/databaseAccounts@2024-05-15' = if (enableCosmosDb) {
  name: cosmosDbAccountName
  location: location
  tags: tags
  kind: 'GlobalDocumentDB'
  properties: {
    consistencyPolicy: {
      defaultConsistencyLevel: 'Session'
    }
    databaseAccountOfferType: 'Standard'
    enableAutomaticFailover: true
    locations: [
      {
        locationName: location
        failoverPriority: 0
        isZoneRedundant: true
      }
    ]
    publicNetworkAccess: 'Enabled'
  }
}

// ============================================================================
// AI SEARCH (Optional)
// ============================================================================

resource searchService 'Microsoft.Search/searchServices@2024-06-01-preview' = if (enableAISearch) {
  name: searchServiceName
  location: location
  tags: tags
  sku: {
    name: 'standard'
  }
  properties: {
    replicaCount: 1
    partitionCount: 1
    hostingMode: 'default'
    publicNetworkAccess: 'enabled'
  }
}

// ============================================================================
// AI SERVICES (COGNITIVE SERVICES) - As dependency
// ============================================================================

resource aiServices 'Microsoft.CognitiveServices/accounts@2024-10-01' = {
  name: aiServicesName
  location: location
  tags: tags
  sku: {
    name: 'S0'
  }
  kind: 'AIServices'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    customSubDomainName: aiServicesName
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      defaultAction: 'Deny'
      ipRules: []
      virtualNetworkRules: []
    }
    apiProperties: {
      statisticsEnabled: false
    }
  }
}

// ============================================================================
// AI FOUNDRY HUB (Azure Machine Learning Workspace - kind: Hub)
// ============================================================================

resource aiHub 'Microsoft.MachineLearningServices/workspaces@2024-10-01-preview' = {
  name: aiHubName
  location: location
  tags: tags
  kind: 'hub'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    friendlyName: aiHubName
    description: 'Production Azure AI Foundry Hub with enhanced capabilities'
    keyVault: keyVault.id
    storageAccount: storageAccount.id
    applicationInsights: applicationInsights.id
    containerRegistry: containerRegistry.id
    systemDatastoresAuthMode: 'identity'
  }

  // AI Services Connection
  resource aiServicesConnection 'connections@2024-10-01-preview' = {
    name: '${aiHubName}-connection-AIServices'
    properties: {
      category: 'AIServices'
      target: aiServices.properties.endpoint
      authType: 'AAD'
      isSharedToAll: true
      metadata: {
        ApiType: 'Azure'
        ResourceId: aiServices.id
      }
    }
  }

  // AI Search Connection (if enabled)
  resource searchConnection 'connections@2024-10-01-preview' = if (enableAISearch) {
    name: '${aiHubName}-connection-AISearch'
    properties: {
      category: 'CognitiveSearch'
      target: enableAISearch ? 'https://${searchService.name}.search.windows.net' : ''
      authType: 'AAD'
      isSharedToAll: true
      metadata: {
        ApiType: 'Azure'
        ResourceId: enableAISearch ? searchService.id : ''
      }
    }
  }
}

// ============================================================================
// AI FOUNDRY PROJECT (Azure Machine Learning Workspace - kind: Project)
// ============================================================================

resource project 'Microsoft.MachineLearningServices/workspaces@2024-10-01-preview' = {
  name: projectName
  location: location
  tags: tags
  kind: 'Project'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    friendlyName: projectName
    description: 'Production AI Foundry project with enhanced capabilities'
    hubResourceId: aiHub.id
    systemDatastoresAuthMode: 'identity'
  }
}

// ============================================================================
// ROLE ASSIGNMENTS
// ============================================================================

// Azure AI Developer role definition ID
// Reference: https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles#azure-ai-developer
var azureAIDeveloperRoleId = '64702f94-c441-49e6-a78b-ef80e0188fee'

// Assign Azure AI Developer role to Project's managed identity on AI Services
resource projectAIDeveloperRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(aiServices.id, project.id, azureAIDeveloperRoleId)
  scope: aiServices
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', azureAIDeveloperRoleId)
    principalId: project.identity.principalId
    principalType: 'ServicePrincipal'
    description: 'Grants Azure AI Developer permissions to the AI Foundry Project managed identity on AI Services'
  }
}

// Cognitive Services OpenAI User role definition ID
// This allows the project to use OpenAI API including Assistants
var cognitiveServicesOpenAIUserRoleId = '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'

// Assign Cognitive Services OpenAI User role to Project's managed identity
resource projectOpenAIUserRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(aiServices.id, project.id, cognitiveServicesOpenAIUserRoleId)
  scope: aiServices
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', cognitiveServicesOpenAIUserRoleId)
    principalId: project.identity.principalId
    principalType: 'ServicePrincipal'
    description: 'Grants OpenAI API access including Assistants to the AI Foundry Project managed identity'
  }
}

// Assign Azure AI Developer role to Hub's managed identity on AI Services
resource hubAIDeveloperRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(aiServices.id, aiHub.id, azureAIDeveloperRoleId)
  scope: aiServices
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', azureAIDeveloperRoleId)
    principalId: aiHub.identity.principalId
    principalType: 'ServicePrincipal'
    description: 'Grants Azure AI Developer permissions to the AI Foundry Hub managed identity on AI Services'
  }
}

// Assign role to AI Search if enabled
resource projectSearchContributorRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (enableAISearch) {
  name: guid(searchService.id, project.id, 'Search-Contributor')
  scope: enableAISearch ? searchService : aiServices // Conditional scope
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7ca78c08-252a-4471-8644-bb5ff32d4ba0') // Search Service Contributor
    principalId: project.identity.principalId
    principalType: 'ServicePrincipal'
    description: 'Grants Search Service Contributor permissions to the AI Foundry Project on AI Search'
  }
}

// Assign role to Cosmos DB if enabled
resource projectCosmosDbContributorRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (enableCosmosDb) {
  name: guid(cosmosDbAccount.id, project.id, 'Cosmos-Contributor')
  scope: enableCosmosDb ? cosmosDbAccount : aiServices // Conditional scope
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '00000000-0000-0000-0000-000000000002') // Cosmos DB Built-in Data Contributor
    principalId: project.identity.principalId
    principalType: 'ServicePrincipal'
    description: 'Grants Cosmos DB data access to the AI Foundry Project'
  }
}

// ============================================================================
// OUTPUTS
// ============================================================================

output aiHubName string = aiHub.name
output aiHubId string = aiHub.id
output projectName string = project.name
output projectId string = project.id
output aiServicesName string = aiServices.name
output aiServicesEndpoint string = aiServices.properties.endpoint
output aiServicesId string = aiServices.id
output storageAccountName string = storageAccount.name
output storageAccountId string = storageAccount.id
output keyVaultName string = keyVault.name
output keyVaultId string = keyVault.id
output applicationInsightsName string = applicationInsights.name
output containerRegistryName string = containerRegistry.name
output cosmosDbAccountName string = enableCosmosDb ? cosmosDbAccount.name : ''
output cosmosDbAccountId string = enableCosmosDb ? cosmosDbAccount.id : ''
output searchServiceName string = enableAISearch ? searchService.name : ''
output searchServiceId string = enableAISearch ? searchService.id : ''
output resourceGroupName string = resourceGroup().name
output location string = location
