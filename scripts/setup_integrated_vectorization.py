#!/usr/bin/env python3
"""
Setup script for Azure AI Search integrated vectorization.
Installs required packages and provides setup instructions.
"""

import subprocess
import sys
import os
from pathlib import Path

def install_packages():
    """Install required Python packages."""
    packages = [
        "azure-identity",
        "azure-search-documents>=11.5.0",  # Need latest version for integrated vectorization
        "azure-storage-blob",
        "openai>=1.0.0",
        "python-dotenv"
    ]
    
    print("📦 Installing required packages...")
    for package in packages:
        try:
            print(f"Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ {package} installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {package}: {e}")
            return False
    
    print("✅ All packages installed successfully!")
    return True

def create_env_template():
    """Create a .env template file with required variables."""
    env_template = """# Azure AI Search Configuration
AZURE_SEARCH_ENDPOINT=https://your-search-service.search.windows.net
# AZURE_SEARCH_KEY=your-search-admin-key  # Optional: use if not using Azure CLI/DefaultAzureCredential

# Azure Storage Configuration
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=your-storage;AccountKey=your-key;EndpointSuffix=core.windows.net

# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://your-openai-service.openai.azure.com/
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-small
AZURE_OPENAI_EMBEDDING_MODEL=text-embedding-3-small
# AZURE_OPENAI_KEY=your-openai-key  # Optional: use if not using Azure CLI/DefaultAzureCredential
"""
    
    env_file = Path(".env")
    if not env_file.exists():
        with open(env_file, "w") as f:
            f.write(env_template)
        print(f"📄 Created .env template file: {env_file}")
        print("Please update it with your actual Azure resource endpoints and keys.")
    else:
        print("📄 .env file already exists")

def show_setup_instructions():
    """Display setup and usage instructions."""
    instructions = """
🚀 Azure AI Search Integrated Vectorization Setup Complete!

📋 Next Steps:

1️⃣ Configure Azure Resources:
   - Update the .env file with your actual Azure endpoints and keys
   - Ensure your Azure AI Search service is deployed (Basic tier or higher)
   - Ensure your Azure OpenAI service has text-embedding-3-small deployed
   - Ensure your Azure Storage account is accessible

2️⃣ Authentication Setup:
   Option A: Use Azure CLI (Recommended)
     az login
     az account set --subscription "your-subscription-id"
   
   Option B: Use Service Principal
     Set AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID
   
   Option C: Use Access Keys
     Set AZURE_SEARCH_KEY and AZURE_OPENAI_KEY in .env

3️⃣ Run the Pipeline:
   # Generate test data (if not already done)
   python scripts/generate_weather_data.py
   python scripts/generate_news_data.py
   
   # Set up integrated vectorization pipeline
   python scripts/index_documents_integrated.py
   
   # Test the search capabilities
   python scripts/test_search.py

🔧 What the Integrated Vectorization Does:

✨ Automatic PDF Processing:
   - Azure AI Search natively reads PDF files from blob storage
   - No need for custom PDF parsing code
   
✨ Smart Chunking:
   - Text Split skill automatically chunks documents
   - Configurable chunk size (2000 chars) and overlap (500 chars)
   - Preserves document structure and context
   
✨ Automatic Vectorization:
   - Azure OpenAI Embedding skill generates vectors for each chunk
   - No need to manually call embedding APIs
   - Vectors are automatically indexed for search
   
✨ End-to-End Pipeline:
   - Indexer runs automatically when new documents are added
   - Can be scheduled to run periodically (every 2 hours)
   - Handles errors and retries automatically

🎯 Benefits Over Custom Implementation:

✅ No Code Maintenance: Azure handles PDF parsing, chunking, and embedding
✅ Automatic Scaling: Azure scales the processing based on workload
✅ Error Handling: Built-in retry logic and error reporting
✅ Monitoring: Indexer status and metrics available in Azure portal
✅ Performance: Optimized for large document sets
✅ Security: Uses Azure RBAC and managed identities

📊 Search Capabilities:

🔍 Vector Search: Semantic similarity using embeddings
🔍 Keyword Search: Traditional text search with BM25 scoring
🔍 Hybrid Search: Combines vector and keyword search
🔍 Filtered Search: Search within specific categories or document types
🔍 Faceted Search: Browse by category, source type, date, etc.

🔗 Integration with Agent:

After indexing is complete, your agent can use the search index for RAG:
- Query the index for relevant context
- Combine search results with user questions
- Generate informed responses based on your knowledge base

Next: Update your agent to use the search index for knowledge retrieval!
"""
    
    print(instructions)

def main():
    """Main setup function."""
    print("🚀 Azure AI Search Integrated Vectorization Setup")
    print("=" * 60)
    
    # Install required packages
    if not install_packages():
        print("❌ Package installation failed. Please check your Python environment.")
        return
    
    # Create .env template
    create_env_template()
    
    # Show setup instructions
    show_setup_instructions()
    
    print("\n✅ Setup complete! Follow the instructions above to configure and run the pipeline.")

if __name__ == "__main__":
    main()