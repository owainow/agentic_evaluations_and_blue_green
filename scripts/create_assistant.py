#!/usr/bin/env python3
"""
Assistant Creation Script for Azure OpenAI
Creates an AI assistant using the Assistants API with specified model deployment
"""

import os
import sys
import json
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential

def create_assistant(
    azure_endpoint: str,
    model_deployment_name: str,
    assistant_name: str,
    assistant_instructions: str,
    api_version: str = "2024-05-01-preview"
):
    """
    Create an AI assistant in Azure OpenAI using the Assistants API
    
    Args:
        azure_endpoint: Azure OpenAI endpoint (e.g., https://xxx.openai.azure.com/)
        model_deployment_name: Name of the deployed model to use
        assistant_name: Name for the assistant
        assistant_instructions: Instructions for the assistant behavior
        api_version: Azure OpenAI API version
    
    Returns:
        dict: Assistant metadata including ID and details
    """
    try:
        # Authenticate using DefaultAzureCredential (supports Azure CLI, Managed Identity, etc.)
        print("Authenticating with Azure...")
        credential = DefaultAzureCredential()
        token = credential.get_token("https://cognitiveservices.azure.com/.default")
        
        # Create Azure OpenAI client
        print(f"Connecting to Azure OpenAI: {azure_endpoint}")
        client = AzureOpenAI(
            api_version=api_version,
            azure_endpoint=azure_endpoint,
            azure_ad_token=token.token
        )
        
        # Create the assistant
        print(f"Creating assistant '{assistant_name}' with model deployment '{model_deployment_name}'...")
        assistant = client.beta.assistants.create(
            model=model_deployment_name,
            name=assistant_name,
            instructions=assistant_instructions,
            description=f"Assistant using {model_deployment_name} deployment"
        )
        
        print(f"✅ Assistant created successfully!")
        print(f"  Assistant ID: {assistant.id}")
        print(f"  Assistant Name: {assistant.name}")
        print(f"  Model: {assistant.model}")
        
        # Return assistant details
        return {
            "id": assistant.id,
            "name": assistant.name,
            "model": assistant.model,
            "instructions": assistant.instructions
        }
        
    except Exception as e:
        print(f"❌ Error creating assistant: {str(e)}")
        import traceback
        traceback.print_exc()
        raise

def main():
    """Main entry point for the script"""
    
    # Get environment variables
    azure_endpoint = os.environ.get('AZURE_OPENAI_ENDPOINT')
    model_deployment_name = os.environ.get('MODEL_DEPLOYMENT_NAME')
    assistant_name = os.environ.get('ASSISTANT_NAME', 'Default Assistant')
    assistant_instructions = os.environ.get('ASSISTANT_INSTRUCTIONS', 'You are a helpful AI assistant.')
    api_version = os.environ.get('API_VERSION', '2024-05-01-preview')
    
    # Validate required parameters
    if not azure_endpoint:
        print("❌ Error: AZURE_OPENAI_ENDPOINT environment variable is required")
        print("Example: https://your-resource.openai.azure.com/")
        sys.exit(1)
    
    if not model_deployment_name:
        print("❌ Error: MODEL_DEPLOYMENT_NAME environment variable is required")
        sys.exit(1)
    
    print("=" * 60)
    print("Azure OpenAI Assistant Creation")
    print("=" * 60)
    print(f"Endpoint: {azure_endpoint}")
    print(f"Model Deployment: {model_deployment_name}")
    print(f"Assistant Name: {assistant_name}")
    print(f"API Version: {api_version}")
    print("=" * 60)
    
    try:
        # Create the assistant
        assistant_info = create_assistant(
            azure_endpoint=azure_endpoint,
            model_deployment_name=model_deployment_name,
            assistant_name=assistant_name,
            assistant_instructions=assistant_instructions,
            api_version=api_version
        )
        
        # Output for GitHub Actions
        github_output = os.environ.get('GITHUB_OUTPUT')
        if github_output:
            with open(github_output, 'a', encoding='utf-8') as f:
                f.write(f"assistant_id={assistant_info['id']}\n")
                f.write(f"assistant_name={assistant_info['name']}\n")
                f.write(f"assistant_model={assistant_info['model']}\n")
            print(f"\n✓ Outputs written to: {github_output}")
        
        # Output JSON for programmatic use
        print("\n" + "=" * 60)
        print("Assistant Details (JSON):")
        print("=" * 60)
        print(json.dumps(assistant_info, indent=2))
        
        sys.exit(0)
        
    except Exception as e:
        print(f"\n❌ Failed to create assistant: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
