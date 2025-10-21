# PowerShell deployment script for Azure AI Foundry

param(
    [Parameter(Mandatory=$false)]
    [string]$ResourceGroupName = "rg-aifoundry-dev",
    
    [Parameter(Mandatory=$false)]
    [string]$Location = "eastus",
    
    [Parameter(Mandatory=$false)]
    [string]$SubscriptionId,
    
    [Parameter(Mandatory=$false)]
    [string]$TemplateFile = "main.bicep",
    
    [Parameter(Mandatory=$false)]
    [string]$ParametersFile = "main.parameters.json"
)

# Set error action preference
$ErrorActionPreference = "Stop"

Write-Host "🚀 Starting Azure AI Foundry deployment..." -ForegroundColor Cyan

# Check if logged in
try {
    $context = Get-AzContext
    if (-not $context) {
        throw "Not logged in"
    }
    Write-Host "✅ Already logged in as: $($context.Account.Id)" -ForegroundColor Green
}
catch {
    Write-Host "⚠️  Not logged in to Azure. Initiating login..." -ForegroundColor Yellow
    Connect-AzAccount
}

# Set subscription if provided
if ($SubscriptionId) {
    Write-Host "📝 Setting subscription to: $SubscriptionId" -ForegroundColor Cyan
    Set-AzContext -Subscription $SubscriptionId
}

# Get current subscription
$currentSub = (Get-AzContext).Subscription
Write-Host "📋 Using subscription: $($currentSub.Name) ($($currentSub.Id))" -ForegroundColor Cyan

# Create resource group if it doesn't exist
$rg = Get-AzResourceGroup -Name $ResourceGroupName -ErrorAction SilentlyContinue
if (-not $rg) {
    Write-Host "📦 Creating resource group: $ResourceGroupName in $Location" -ForegroundColor Cyan
    New-AzResourceGroup -Name $ResourceGroupName -Location $Location
    Write-Host "✅ Resource group created" -ForegroundColor Green
}
else {
    Write-Host "✅ Resource group already exists: $ResourceGroupName" -ForegroundColor Green
}

# Deploy the template
Write-Host "" 
Write-Host "🔨 Deploying BICEP template..." -ForegroundColor Cyan
Write-Host "   Template: $TemplateFile" -ForegroundColor Gray
Write-Host "   Parameters: $ParametersFile" -ForegroundColor Gray
Write-Host ""

try {
    $deployment = New-AzResourceGroupDeployment `
        -ResourceGroupName $ResourceGroupName `
        -TemplateFile $TemplateFile `
        -TemplateParameterFile $ParametersFile `
        -Verbose

    Write-Host ""
    Write-Host "✅ Deployment completed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📊 Deployment Outputs:" -ForegroundColor Cyan
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
    
    foreach ($key in $deployment.Outputs.Keys) {
        $value = $deployment.Outputs[$key].Value
        Write-Host "  $key : " -NoNewline -ForegroundColor Yellow
        Write-Host "$value" -ForegroundColor White
    }
    
    Write-Host ""
    Write-Host "🎉 Your Azure AI Foundry project is ready!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "  1. Navigate to https://ai.azure.com" -ForegroundColor White
    Write-Host "  2. Select your project: $($deployment.Outputs.projectName.Value)" -ForegroundColor White
    Write-Host "  3. Start building agents!" -ForegroundColor White
    Write-Host ""
}
catch {
    Write-Host ""
    Write-Host "❌ Deployment failed!" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    exit 1
}
