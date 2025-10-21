# Azure AI Foundry - Automated Agent Evaluation and Blue/Green Deployment

A comprehensive repository demonstrating Azure AI Foundry infrastructure deployment, automated agentic evaluations, and blue/green model deployment strategies using GitHub Actions.

## 🏗️ Infrastructure

This repository includes complete **BICEP infrastructure-as-code templates** to deploy Azure AI Foundry with full agent support.

### Quick Deploy

```powershell
# Deploy using PowerShell
cd infrastructure
.\deploy.ps1 -ResourceGroupName "rg-aifoundry-dev" -Location "eastus"
```

### What Gets Deployed

✅ **Azure AI Foundry Resource** with managed identity and EntraID authentication  
✅ **Azure AI Foundry Project** ready for agent development  
✅ **Model Deployment** (GPT-4o by default, configurable)  
✅ **Capability Hosts** for agent support (account + project level)  
✅ **Optional Standard Setup** with dedicated Storage, Cosmos DB, and AI Search  

### Templates Available

- **`infrastructure/main.bicep`** - Basic setup (managed storage, quick start)
- **`infrastructure/main.standard.bicep`** - Production setup (dedicated resources)
- **Deployment scripts** for PowerShell and Bash
- **Complete documentation** in `infrastructure/GUIDE.md`

📖 **Full documentation**: See [`infrastructure/README.md`](infrastructure/README.md) and [`infrastructure/GUIDE.md`](infrastructure/GUIDE.md)

## 🎯 Project Goals

This repository demonstrates:
- ✅ Infrastructure-as-code deployment of Azure AI Foundry
- ✅ Model deployment and agent creation workflows
- 🔄 GitHub Actions for agentic evaluations  
- 🚦 Blue/green model deployment strategies  
- 🤖 Agent creation and management best practices

## 🤖 Model Deployment & Agent Creation

Deploy AI models and create agents using the **Azure AI Foundry Agent Service**.

### What's Deployed

✅ **Model Deployment** - Deploy any supported model (gpt-4o, gpt-4, gpt-35-turbo, etc.)  
✅ **Weather Agent** - AI agent with custom function calling for weather queries  
✅ **Standardized JSON Responses** - Structured output for weather-related questions  
✅ **Function Tools** - Custom Python functions the agent can call  

### Weather Agent Features

The agent includes a **weather function tool** that:
- Provides weather information for any location
- Returns responses in **standardized JSON format**
- Supports both Celsius and Fahrenheit units
- Works with natural language weather queries

Example response:
```json
{
    "location": "Seattle, WA",
    "temperature": 15,
    "temperature_unit": "°C",
    "condition": "Rainy",
    "humidity_percent": 85,
    "wind_speed_kmh": 12,
    "timestamp": "2025-10-21T12:00:00Z"
}
```

📖 **Full documentation**: See [`docs/WEATHER_AGENT.md`](docs/WEATHER_AGENT.md)  
✅ **Code Interpreter** - Run Python code for analysis and calculations  
✅ **File Search** - Search through uploaded documents  
✅ **Function Calling** - Connect to external tools and APIs  

### Quick Start

1. **Go to Actions** → **Deploy Model and Create Agent**
2. **Select your configuration**:
   - Model: `gpt-4o`, `gpt-4o-mini`, `gpt-4`, `gpt-35-turbo`, etc.
   - Model Version: `2024-11-20` (or latest available)
   - Environment: dev/test/prod
   - Assistant name and instructions
   - SKU and capacity
3. **Run workflow** - Model deploys and assistant is created automatically

### Two Options Available

#### Option 1: Azure OpenAI Assistants API (Current Implementation) ✅
- **Status**: Preview
- **Setup**: Works immediately with existing infrastructure
- **Features**: Threads, code interpreter, file search, function calling
- **Use for**: Quick start, development, A/B testing
- **Pricing**: Token usage only (+ code interpreter if used)

#### Option 2: Azure AI Foundry Agent Service (Alternative)
- **Status**: Generally Available
- **Setup**: Requires additional infrastructure (capability hosts)
- **Features**: Everything in Option 1 + multi-agent, Bing search, non-OpenAI models
- **Use for**: Production, enterprise features, multi-model support
- **Pricing**: Token usage + infrastructure costs

📖 **Detailed Comparison**: See [`docs/AGENTS_VS_ASSISTANTS.md`](docs/AGENTS_VS_ASSISTANTS.md)

### Use Cases

- **A/B Testing**: Deploy same assistant with different models (GPT-4o vs GPT-4o-mini)
- **Blue/Green**: Test new model versions before production switch
- **Cost Optimization**: Compare model performance vs cost
- **Version Testing**: Validate new model versions against evaluations

📖 **Full Guide**: See [`docs/MODEL_DEPLOYMENT_GUIDE.md`](docs/MODEL_DEPLOYMENT_GUIDE.md)

## 🧪 Dual Evaluation System

The repository includes **two parallel evaluation flows** that run simultaneously when you deploy an agent:

### 1. AI Foundry Evaluation (AI-Powered)
Uses **microsoft/ai-agent-evals@v2-beta** action with multiple AI evaluators:
- ✅ **RelevanceEvaluator** - Are responses relevant to the query?
- ✅ **CoherenceEvaluator** - Are responses well-structured and logical?
- ✅ **GroundednessEvaluator** - Are responses based on provided context?
- ✅ **ToolCallAccuracyEvaluator** - Are function tools used correctly?
- ✅ **IndirectAttackEvaluator** - Does agent resist prompt injections?

### 2. JSON Validation (Format Testing)
Custom validation script that tests response formatting:
- ✅ **Valid JSON** - Can responses be parsed as JSON?
- ✅ **Pure JSON** - No markdown formatting or extra text?
- ✅ **Required Fields** - Contains expected weather/news fields?
- ✅ **Data Type Detection** - Correct response type (weather/news)?
- ✅ **Rejection Handling** - Properly rejects out-of-scope queries?

### Evaluation Flow

```
┌─────────────────────────────────┐
│  Deploy Model & Create Agent    │
└────────────┬────────────────────┘
             │
    ┌────────┴────────┐
    │                 │
    ▼                 ▼
┌─────────┐      ┌──────────────┐
│ AI Eval │      │ JSON Validation│
│ (Foundry│      │   (Custom)   │
│  Evals) │      │              │
└────┬────┘      └──────┬───────┘
     │                  │
     └────────┬─────────┘
              ▼
     📊 GitHub Actions Summary
        • Agent Details
        • AI Evaluation Results
        • JSON Validation Results
        • Test Pass Rates
        • Detailed Test Breakdown
```

### What You See in GitHub Actions

Both evaluation jobs run in parallel and display results side-by-side:

**AI Foundry Evaluation Tab**:
- Relevance, coherence, groundedness scores
- Tool calling accuracy metrics
- Security/attack resistance results

**JSON Validation Tab**:
- Overall pass rate (e.g., 8/8 tests = 100%)
- Category breakdown (Weather: 3/3, News: 2/2, Security: 3/3)
- Individual test results with JSON validation status
- Response previews and function calls made

### Test Categories

| Category | Tests | Purpose |
|----------|-------|---------|
| 🌤️ **Weather** | Valid weather queries | Ensure JSON weather responses |
| 📰 **News** | News article requests | Validate news data format |
| 🛡️ **Security** | Injection attempts | Verify scope enforcement |
| ❌ **Rejection** | Out-of-scope queries | Confirm proper rejections |

### Running Evaluations

Evaluations run automatically when you:
1. Deploy an agent with `run_evaluation: true`
2. Trigger the "AI Agent Evaluation" workflow manually

Both flows execute in parallel, providing comprehensive validation of agent behavior and response quality.

📖 **Evaluation Documentation**: 
- [`docs/JSON_VALIDATION.md`](docs/JSON_VALIDATION.md) - JSON validation details
- [`docs/EVALUATION_DATA_FORMAT.md`](docs/EVALUATION_DATA_FORMAT.md) - AI eval format
- [`docs/AGENT_ENHANCEMENTS.md`](docs/AGENT_ENHANCEMENTS.md) - Agent features 
