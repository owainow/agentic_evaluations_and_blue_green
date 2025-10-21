#!/usr/bin/env python3
"""
Agent Creation Script for Azure AI Foundry
Creates an AI agent with specified model deployment
"""

import os
import sys
import json
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

def create_agent(
    project_endpoint: str,
    model_deployment_name: str,
    agent_name: str,
    agent_instructions: str,
    agent_description: str = None
):
    """
    Create an AI agent in Azure AI Foundry
    
    Args:
        project_endpoint: Azure AI Foundry project endpoint
        model_deployment_name: Name of the deployed model to use
        agent_name: Name for the agent
        agent_instructions: Instructions for the agent behavior
        agent_description: Optional description of the agent
    
    Returns:
        dict: Agent metadata including ID and details
    """
    try:
        # Authenticate using DefaultAzureCredential (supports Azure CLI, Managed Identity, etc.)
        credential = DefaultAzureCredential()
        
        # Create project client
        print(f"Connecting to project: {project_endpoint}")
        project_client = AIProjectClient(
            endpoint=project_endpoint,
            credential=credential
        )
        
        # Create the agent
        print(f"Creating agent '{agent_name}' with model '{model_deployment_name}'...")
        agent = project_client.agents.create_agent(
            model=model_deployment_name,
            name=agent_name,
            instructions=agent_instructions,
            description=agent_description or f"Agent using {model_deployment_name}"
        )
        
        print(f"✓ Agent created successfully!")
        print(f"  Agent ID: {agent.id}")
        print(f"  Agent Name: {agent.name}")
        print(f"  Model: {agent.model}")
        
        # Return agent details
        return {
            "id": agent.id,
            "name": agent.name,
            "model": agent.model,
            "instructions": agent.instructions,
            "description": agent.description,
            "created_at": str(agent.created_at) if hasattr(agent, 'created_at') else None
        }
        
    except Exception as e:
        print(f"✗ Error creating agent: {str(e)}", file=sys.stderr)
        raise

def main():
    """Main entry point for the script"""
    # Get configuration from environment variables
    project_endpoint = os.environ.get('PROJECT_ENDPOINT')
    model_deployment_name = os.environ.get('MODEL_DEPLOYMENT_NAME')
    agent_name = os.environ.get('AGENT_NAME', 'test-agent')
    agent_instructions = os.environ.get('AGENT_INSTRUCTIONS', 'You are a helpful AI assistant.')
    agent_description = os.environ.get('AGENT_DESCRIPTION')
    
    # Validate required parameters
    if not project_endpoint:
        print("Error: PROJECT_ENDPOINT environment variable is required", file=sys.stderr)
        print("Format: https://<resource>.services.ai.azure.com/api/projects/<project>", file=sys.stderr)
        sys.exit(1)
    
    if not model_deployment_name:
        print("Error: MODEL_DEPLOYMENT_NAME environment variable is required", file=sys.stderr)
        sys.exit(1)
    
    print("=" * 60)
    print("Azure AI Foundry Agent Creation")
    print("=" * 60)
    print(f"Project: {project_endpoint}")
    print(f"Model Deployment: {model_deployment_name}")
    print(f"Agent Name: {agent_name}")
    print("=" * 60)
    
    # Create the agent
    agent_info = create_agent(
        project_endpoint=project_endpoint,
        model_deployment_name=model_deployment_name,
        agent_name=agent_name,
        agent_instructions=agent_instructions,
        agent_description=agent_description
    )
    
    # Output agent information as JSON for GitHub Actions
    output_file = os.environ.get('GITHUB_OUTPUT')
    if output_file:
        with open(output_file, 'a') as f:
            f.write(f"agent_id={agent_info['id']}\n")
            f.write(f"agent_name={agent_info['name']}\n")
    
    # Also output as JSON for logging
    print("\nAgent Details (JSON):")
    print(json.dumps(agent_info, indent=2))
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
