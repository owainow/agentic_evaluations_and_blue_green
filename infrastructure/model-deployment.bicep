// Parameters
@description('Name of the AI Services account where the model will be deployed')
param aiServicesName string

@description('Name for the model deployment')
param deploymentName string

@description('Model to deploy')
@allowed([
  'gpt-4o'
  'gpt-4o-mini'
  'gpt-4'
  'gpt-4-turbo'
  'gpt-35-turbo'
  'gpt-35-turbo-16k'
])
param modelName string = 'gpt-4o'

@description('Model version to deploy')
param modelVersion string = '2024-11-20'

@description('Model format (provider)')
param modelFormat string = 'OpenAI'

@description('SKU name for the deployment type')
@allowed([
  'Standard'
  'GlobalStandard'
  'DataZoneStandard'
  'GlobalBatch'
  'ProvisionedManaged'
])
param skuName string = 'Standard'

@description('Capacity (TPM in thousands for Standard, PTUs for Provisioned)')
param capacity int = 10

// Reference existing AI Services account
resource aiServices 'Microsoft.CognitiveServices/accounts@2024-10-01' existing = {
  name: aiServicesName
}

// Create model deployment
resource modelDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  parent: aiServices
  name: deploymentName
  sku: {
    name: skuName
    capacity: capacity
  }
  properties: {
    model: {
      format: modelFormat
      name: modelName
      version: modelVersion
    }
    versionUpgradeOption: 'OnceNewDefaultVersionAvailable'
  }
}

// Outputs
output deploymentId string = modelDeployment.id
output deploymentName string = modelDeployment.name
output modelName string = modelName
output modelVersion string = modelVersion
output endpoint string = aiServices.properties.endpoint
