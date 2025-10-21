// Azure AI Foundry Project with Standard Agent Setup
// Includes dedicated Storage Account, Cosmos DB, and Azure AI Search for agent data isolation

@description('Location for all resources')
param location string = resourceGroup().location

@description('Base name for resources (will have suffixes added)')
param baseName string

@description('Enable capability hosts for agents')
param enableAgents bool = true

@description('Model deployment configuration')
param modelDeploymentName string = 'gpt-4o'
param modelName string = 'gpt-4o'
param modelVersion string = '2024-11-20'
param modelFormat string = 'OpenAI'
param deploymentSkuName string = 'Standard'
param deploymentCapacity int = 10

// Generate unique names
var uniqueSuffix = uniqueString(resourceGroup().id)
var aiFoundryName = '${baseName}-aifoundry-${uniqueSuffix}'
var projectName = '${baseName}-project'
var storageAccountName = toLower(replace('${baseName}${uniqueSuffix}', '-', ''))
var cosmosDbAccountName = '${baseName}-cosmos-${uniqueSuffix}'
var searchServiceName = '${baseName}-search-${uniqueSuffix}'

// Storage Account for agent file storage
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: length(storageAccountName) > 24 ? substring(storageAccountName, 0, 24) : storageAccountName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    accessTier: 'Hot'
    supportsHttpsTrafficOnly: true
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
  }
}

// Blob service and containers for agent data
resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' = {
  name: 'default'
  parent: storageAccount
}

resource filesContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  name: 'agent-files'
  parent: blobService
}

resource systemDataContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  name: 'agent-system-data'
  parent: blobService
}

// Cosmos DB for thread/message storage
resource cosmosDbAccount 'Microsoft.DocumentDB/databaseAccounts@2024-05-15' = {
  name: cosmosDbAccountName
  location: location
  kind: 'GlobalDocumentDB'
  properties: {
    databaseAccountOfferType: 'Standard'
    consistencyPolicy: {
      defaultConsistencyLevel: 'Session'
    }
    locations: [
      {
        locationName: location
        failoverPriority: 0
      }
    ]
    enableAutomaticFailover: false
    enableMultipleWriteLocations: false
  }
}

resource cosmosDatabase 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2024-05-15' = {
  name: 'agent-database'
  parent: cosmosDbAccount
  properties: {
    resource: {
      id: 'agent-database'
    }
  }
}

resource threadsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-05-15' = {
  name: 'threads'
  parent: cosmosDatabase
  properties: {
    resource: {
      id: 'threads'
      partitionKey: {
        paths: ['/id']
        kind: 'Hash'
      }
    }
  }
}

resource messagesContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-05-15' = {
  name: 'messages'
  parent: cosmosDatabase
  properties: {
    resource: {
      id: 'messages'
      partitionKey: {
        paths: ['/threadId']
        kind: 'Hash'
      }
    }
  }
}

resource agentsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-05-15' = {
  name: 'agents'
  parent: cosmosDatabase
  properties: {
    resource: {
      id: 'agents'
      partitionKey: {
        paths: ['/id']
        kind: 'Hash'
      }
    }
  }
}

// Azure AI Search for vector store
resource searchService 'Microsoft.Search/searchServices@2024-06-01-preview' = {
  name: searchServiceName
  location: location
  sku: {
    name: 'standard'
  }
  properties: {
    replicaCount: 1
    partitionCount: 1
    hostingMode: 'default'
  }
}

// Create the Azure AI Foundry resource
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
    allowProjectManagement: true
    customSubDomainName: aiFoundryName
    disableLocalAuth: true
    publicNetworkAccess: 'Enabled'
  }
}

// Create the Azure AI Foundry Project
resource aiFoundryProject 'Microsoft.CognitiveServices/accounts/projects@2025-06-01' = {
  name: projectName
  parent: aiFoundryResource
  location: location
  properties: {
    description: 'Azure AI Foundry project with standard agent setup'
    displayName: projectName
  }
}

// Deploy the AI model
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

// Create connections for the agent resources
resource storageConnection 'Microsoft.CognitiveServices/accounts/projects/connections@2025-06-01' = {
  name: 'agent-storage-connection'
  parent: aiFoundryProject
  properties: {
    category: 'AzureBlob'
    target: storageAccount.properties.primaryEndpoints.blob
    authType: 'ManagedIdentity'
    isSharedToAll: false
    metadata: {
      resourceId: storageAccount.id
      location: location
    }
  }
}

resource cosmosConnection 'Microsoft.CognitiveServices/accounts/projects/connections@2025-06-01' = {
  name: 'agent-cosmos-connection'
  parent: aiFoundryProject
  properties: {
    category: 'CosmosDb'
    target: cosmosDbAccount.properties.documentEndpoint
    authType: 'ManagedIdentity'
    isSharedToAll: false
    metadata: {
      resourceId: cosmosDbAccount.id
      databaseName: cosmosDatabase.name
      location: location
    }
  }
}

resource searchConnection 'Microsoft.CognitiveServices/accounts/projects/connections@2025-06-01' = {
  name: 'agent-search-connection'
  parent: aiFoundryProject
  properties: {
    category: 'CognitiveSearch'
    target: 'https://${searchService.name}.search.windows.net'
    authType: 'ManagedIdentity'
    isSharedToAll: false
    metadata: {
      resourceId: searchService.id
      location: location
    }
  }
}

// Grant AI Foundry managed identity access to resources
// Storage Blob Data Contributor role
resource storageRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storageAccount.id, aiFoundryResource.id, 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')
  scope: storageAccount
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')
    principalId: aiFoundryResource.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// Cosmos DB Built-in Data Contributor role
resource cosmosRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(cosmosDbAccount.id, aiFoundryResource.id, '00000000-0000-0000-0000-000000000002')
  scope: cosmosDbAccount
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '00000000-0000-0000-0000-000000000002')
    principalId: aiFoundryResource.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// Search Index Data Contributor role
resource searchRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(searchService.id, aiFoundryResource.id, '8ebe5a00-799e-43f5-93ac-243d3dce84a7')
  scope: searchService
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '8ebe5a00-799e-43f5-93ac-243d3dce84a7')
    principalId: aiFoundryResource.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// Create Capability Host at Account level
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

// Create Capability Host at Project level with BYO resources (Standard Setup)
resource projectCapabilityHost 'Microsoft.CognitiveServices/accounts/projects/capabilityHosts@2025-06-01' = if (enableAgents) {
  name: 'agents-project-capability-host'
  parent: aiFoundryProject
  properties: {
    capabilityHostKind: 'Agents'
    // Standard setup: specify your own resources for agent data
    threadStorageConnections: [cosmosConnection.name]
    vectorStoreConnections: [searchConnection.name]
    storageConnections: [storageConnection.name]
  }
  dependsOn: [
    accountCapabilityHost
    storageRoleAssignment
    cosmosRoleAssignment
    searchRoleAssignment
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
output storageAccountName string = storageAccount.name
output cosmosDbAccountName string = cosmosDbAccount.name
output searchServiceName string = searchService.name
output location string = location
