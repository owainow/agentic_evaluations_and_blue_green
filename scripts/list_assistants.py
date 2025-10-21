#!/usr/bin/env python3
"""
List all OpenAI Assistants in an Azure OpenAI resource.
"""

import os
import sys
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential

def main():
    # Get Azure OpenAI endpoint from environment or command line
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    if not endpoint and len(sys.argv) > 1:
        endpoint = sys.argv[1]
    
    if not endpoint:
        print("❌ Error: Azure OpenAI endpoint not provided")
        print("Usage: python list_assistants.py <endpoint>")
        print("Or set AZURE_OPENAI_ENDPOINT environment variable")
        sys.exit(1)
    
    # Ensure endpoint format
    if not endpoint.startswith("http"):
        endpoint = f"https://{endpoint}.openai.azure.com/"
    if not endpoint.endswith("/"):
        endpoint += "/"
    
    print("=" * 60)
    print("Azure OpenAI Assistants Listing")
    print("=" * 60)
    print(f"Endpoint: {endpoint}")
    print()
    
    try:
        # Authenticate with Azure using DefaultAzureCredential
        print("Authenticating with Azure...")
        credential = DefaultAzureCredential()
        token = credential.get_token("https://cognitiveservices.azure.com/.default")
        
        # Create Azure OpenAI client
        print("Connecting to Azure OpenAI...")
        client = AzureOpenAI(
            api_version="2024-05-01-preview",
            azure_endpoint=endpoint,
            azure_ad_token=token.token
        )
        
        # List all assistants
        print("Fetching assistants...\n")
        assistants = client.beta.assistants.list(limit=100)
        
        if not assistants.data:
            print("❌ No assistants found in this Azure OpenAI resource.")
            print()
            print("This could mean:")
            print("  1. No assistants have been created yet")
            print("  2. You're checking the wrong resource")
            print("  3. Assistants were deleted")
            sys.exit(0)
        
        print(f"✅ Found {len(assistants.data)} assistant(s):\n")
        print("-" * 60)
        
        for i, assistant in enumerate(assistants.data, 1):
            print(f"{i}. Name: {assistant.name or '(unnamed)'}")
            print(f"   ID: {assistant.id}")
            print(f"   Model: {assistant.model}")
            print(f"   Created: {assistant.created_at}")
            if assistant.instructions:
                instructions_preview = assistant.instructions[:80] + "..." if len(assistant.instructions) > 80 else assistant.instructions
                print(f"   Instructions: {instructions_preview}")
            print("-" * 60)
        
        print()
        print(f"✅ Total assistants: {len(assistants.data)}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print()
        print("Common issues:")
        print("  1. Missing 'Cognitive Services OpenAI User' role")
        print("  2. Wrong endpoint URL")
        print("  3. Authentication failure")
        print()
        print("Run the permission setup script:")
        print("  bash scripts/setup-github-actions-permissions.sh")
        sys.exit(1)

if __name__ == "__main__":
    main()
