#!/usr/bin/env python3
"""
Post-deployment script to set up Azure AI Search knowledge base.
This runs after infrastructure deployment to populate the search service with data.
"""

import os
import sys
import asyncio
import json
from pathlib import Path
from typing import Dict, Any

# Add project root to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Import our scripts
from scripts.generate_weather_data import main as generate_weather_data
from scripts.generate_news_data import main as generate_news_data

def setup_environment_from_deployment(deployment_outputs: Dict[str, Any]) -> None:
    """Set up environment variables from deployment outputs."""
    
    # Extract values from deployment outputs
    search_service_name = deployment_outputs.get('searchServiceName', {}).get('value')
    storage_account_name = deployment_outputs.get('storageAccountName', {}).get('value')
    ai_foundry_name = deployment_outputs.get('aiFoundryName', {}).get('value')  # This is the OpenAI service
    resource_group = deployment_outputs.get('resourceGroupName', {}).get('value')
    location = deployment_outputs.get('location', {}).get('value', 'eastus')
    subscription_id = os.getenv('AZURE_SUBSCRIPTION_ID')
    
    if not all([search_service_name, storage_account_name, ai_foundry_name]):
        print("❌ Missing required deployment outputs")
        print(f"Search Service: {search_service_name}")
        print(f"Storage Account: {storage_account_name}")
        print(f"AI Foundry Service: {ai_foundry_name}")
        sys.exit(1)
    
    # Set environment variables for our scripts
    os.environ['AZURE_SEARCH_ENDPOINT'] = f"https://{search_service_name}.search.windows.net"
    os.environ['AZURE_STORAGE_ACCOUNT_NAME'] = storage_account_name
    os.environ['AZURE_OPENAI_ENDPOINT'] = f"https://{ai_foundry_name}.cognitiveservices.azure.com/"
    os.environ['AZURE_OPENAI_EMBEDDING_DEPLOYMENT'] = "text-embedding-3-small"
    os.environ['AZURE_OPENAI_EMBEDDING_MODEL'] = "text-embedding-3-small"
    
    # Get storage connection string
    print("🔑 Getting storage connection string...")
    import subprocess
    try:
        result = subprocess.run([
            'az', 'storage', 'account', 'show-connection-string',
            '--name', storage_account_name,
            '--resource-group', resource_group,
            '--query', 'connectionString',
            '--output', 'tsv'
        ], capture_output=True, text=True, check=True)
        
        connection_string = result.stdout.strip()
        os.environ['AZURE_STORAGE_CONNECTION_STRING'] = connection_string
        print("✅ Storage connection string configured")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to get storage connection string: {e}")
        sys.exit(1)
    
    print(f"✅ Environment configured for:")
    print(f"   - Search Service: {search_service_name}")
    print(f"   - Storage Account: {storage_account_name}")
    print(f"   - AI Foundry Service: {ai_foundry_name}")

def install_required_packages() -> None:
    """Install required Python packages for the knowledge base setup."""
    print("📦 Installing required packages...")
    
    packages = [
        "azure-identity>=1.15.0",
        "azure-search-documents>=11.5.0",
        "azure-storage-blob>=12.19.0",
        "openai>=1.0.0",
        "reportlab>=4.0.0"
    ]
    
    import subprocess
    
    for package in packages:
        try:
            print(f"Installing {package}...")
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", package
            ], capture_output=True, text=True, check=True)
            print(f"✅ {package} installed")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {package}: {e.stderr}")
            # Don't exit - try to continue with other packages

def generate_knowledge_data() -> bool:
    """Generate weather and news PDF data."""
    print("📄 Generating knowledge base data...")
    
    try:
        # Create data directory
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        
        # Generate weather data
        print("🌤️ Generating weather data PDFs...")
        generate_weather_data()
        
        # Generate news data
        print("📰 Generating news data PDFs...")
        generate_news_data()
        
        # Verify files were created
        weather_dir = data_dir / "weather_pdfs"
        news_dir = data_dir / "news_pdfs"
        
        weather_count = len(list(weather_dir.glob("*.pdf"))) if weather_dir.exists() else 0
        news_count = len(list(news_dir.glob("*.pdf"))) if news_dir.exists() else 0
        
        print(f"✅ Generated {weather_count} weather PDFs and {news_count} news PDFs")
        
        if weather_count == 0 and news_count == 0:
            print("❌ No PDF files were generated")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error generating data: {e}")
        return False

async def setup_integrated_vectorization() -> bool:
    """Set up the Azure AI Search integrated vectorization pipeline."""
    print("🔍 Setting up Azure AI Search integrated vectorization...")
    
    try:
        # Import the indexer class
        from scripts.index_documents_integrated import IntegratedVectorizationIndexer
        
        # Initialize the indexer
        indexer = IntegratedVectorizationIndexer()
        
        # Set up the complete pipeline
        data_dir = Path("data")
        result = await indexer.setup_complete_pipeline(data_dir)
        
        if result["success"]:
            print(f"✅ Successfully set up integrated vectorization!")
            print(f"   Index: {result['index_name']}")
            print(f"   Documents: {result['uploaded_files']}")
            
            # Wait a bit for indexing to start
            print("⏳ Waiting for initial indexing to begin...")
            await asyncio.sleep(30)
            
            # Check indexer status
            status = indexer.get_indexer_status()
            print("📊 Indexer status:")
            print(json.dumps(status, indent=2, default=str))
            
            return True
        else:
            print(f"❌ Failed to set up vectorization: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error setting up vectorization: {e}")
        return False

def create_summary_report(success: bool) -> None:
    """Create a summary report of the knowledge base setup."""
    
    summary_file = Path("knowledge-base-setup-summary.md")
    
    with open(summary_file, "w") as f:
        f.write("# 📚 Knowledge Base Setup Summary\n\n")
        
        if success:
            f.write("## ✅ Setup Completed Successfully!\n\n")
            f.write("Your Azure AI Search knowledge base has been configured with:\n\n")
            f.write("### 📄 Generated Data\n")
            f.write("- **Weather Data**: Historical weather information for multiple cities\n")
            f.write("- **News Articles**: Climate and weather-related news content\n\n")
            f.write("### 🔍 Azure AI Search Configuration\n")
            f.write("- **Index Name**: `knowledge-vector-index`\n")
            f.write("- **Vector Dimensions**: 1536 (text-embedding-3-small)\n")
            f.write("- **Search Capabilities**:\n")
            f.write("  - Vector search (semantic similarity)\n")
            f.write("  - Keyword search (traditional text matching)\n")
            f.write("  - Hybrid search (combines both approaches)\n")
            f.write("  - Filtered search (by category, source type, etc.)\n\n")
            f.write("### 🛠️ Integrated Vectorization Pipeline\n")
            f.write("- **Data Source**: Blob storage container (`knowledge-documents`)\n")
            f.write("- **Skillset**: Text splitting + Azure OpenAI embedding\n")
            f.write("- **Indexer**: Automated processing every 2 hours\n")
            f.write("- **Document Processing**: Native PDF parsing and chunking\n\n")
            f.write("## 🚀 Next Steps\n\n")
            f.write("1. **Deploy your language model** using the model deployment workflow\n")
            f.write("2. **Update your agent** to use the knowledge base for RAG\n")
            f.write("3. **Test search capabilities** using the provided test scripts\n")
            f.write("4. **Run evaluations** to measure RAG performance\n\n")
            f.write("## 🔗 Resources\n\n")
            f.write("- [Azure AI Search Documentation](https://docs.microsoft.com/en-us/azure/search/)\n")
            f.write("- [Integrated Vectorization Guide](docs/INTEGRATED_VECTORIZATION_GUIDE.md)\n")
            f.write("- [Search Index Portal](https://portal.azure.com/#blade/HubsExtension/BrowseResource/resourceType/Microsoft.Search%2FsearchServices)\n\n")
        else:
            f.write("## ❌ Setup Failed\n\n")
            f.write("The knowledge base setup encountered errors. Check the logs above for details.\n\n")
            f.write("### 🛠️ Troubleshooting\n\n")
            f.write("1. **Check Azure permissions**: Ensure the service principal has required roles\n")
            f.write("2. **Verify resource deployment**: Confirm all Azure services are properly deployed\n")
            f.write("3. **Check environment variables**: Ensure all required variables are set\n")
            f.write("4. **Review logs**: Look for specific error messages in the deployment logs\n\n")
            f.write("### 🔧 Manual Setup\n\n")
            f.write("If automated setup failed, you can run the scripts manually:\n\n")
            f.write("```bash\n")
            f.write("# Generate data\n")
            f.write("python scripts/generate_weather_data.py\n")
            f.write("python scripts/generate_news_data.py\n\n")
            f.write("# Set up indexing\n")
            f.write("python scripts/index_documents_integrated.py\n")
            f.write("```\n\n")
    
    print(f"📄 Summary report created: {summary_file}")

async def main():
    """Main function to set up the knowledge base after infrastructure deployment."""
    print("🚀 Azure AI Search Knowledge Base Setup")
    print("=" * 60)
    
    success = False
    
    try:
        # Check if we have deployment outputs
        deployment_outputs_file = os.getenv('DEPLOYMENT_OUTPUTS_FILE', 'deployment-outputs.json')
        
        if os.path.exists(deployment_outputs_file):
            print(f"📋 Loading deployment outputs from {deployment_outputs_file}")
            with open(deployment_outputs_file, 'r') as f:
                deployment_outputs = json.load(f)
            
            # Set up environment
            setup_environment_from_deployment(deployment_outputs)
        else:
            print(f"⚠️ Deployment outputs file not found: {deployment_outputs_file}")
            print("Using environment variables directly...")
        
        # Install required packages
        install_required_packages()
        
        # Generate knowledge data
        if not generate_knowledge_data():
            print("❌ Failed to generate knowledge data")
            return
        
        # Set up integrated vectorization
        if await setup_integrated_vectorization():
            print("✅ Knowledge base setup completed successfully!")
            success = True
        else:
            print("❌ Failed to set up integrated vectorization")
    
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Create summary report
        create_summary_report(success)
        
        if success:
            print("\n🎉 Knowledge Base is Ready!")
            print("Your Azure AI Search service is now populated with weather and news data.")
            print("The agent can now use this knowledge base for RAG operations.")
        else:
            print("\n💥 Setup Failed")
            print("Check the logs above and the summary report for troubleshooting steps.")

if __name__ == "__main__":
    asyncio.run(main())