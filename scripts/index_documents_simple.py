#!/usr/bin/env python3
"""
Simple Azure AI Search indexer for document indexing without vectorization.
This script creates a basic indexer that processes PDFs and makes them searchable
using traditional keyword search without requiring embedding models.
"""

import os
from pathlib import Path
from typing import Dict, List
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
from azure.search.documents.indexes import SearchIndexClient, SearchIndexerClient
from azure.search.documents.indexes.models import (
    SearchIndex, SearchField, SearchFieldDataType, SearchIndexer,
    SearchIndexerDataSourceConnection, SearchIndexerDataContainer,
    IndexingSchedule, FieldMapping
)


class SimpleDocumentIndexer:
    """
    Simple document indexer for Azure AI Search using keyword search only.
    No embedding skills or vectorization - just basic text extraction and indexing.
    """
    
    def __init__(self):
        """Initialize the simple indexer with required configurations."""
        # Azure AI Search configuration
        self.search_service_name = os.getenv("AZURE_SEARCH_SERVICE_NAME", "aif-search-dev-mf77j5")
        self.search_endpoint = f"https://{self.search_service_name}.search.windows.net"
        
        # Storage configuration
        self.storage_account_name = os.getenv("AZURE_STORAGE_ACCOUNT_NAME", "aifstdevmf77j5")
        self.storage_endpoint = f"https://{self.storage_account_name}.blob.core.windows.net"
        self.container_name = "knowledge-documents"
        
        # Simple indexer names (without vectorization)
        self.index_name = "knowledge-simple-index"
        self.data_source_name = "knowledge-simple-data-source"
        self.indexer_name = "knowledge-simple-indexer"
        
        # Initialize Azure clients
        self.credential = DefaultAzureCredential()
        self.search_index_client = SearchIndexClient(
            endpoint=self.search_endpoint,
            credential=self.credential
        )
        self.search_indexer_client = SearchIndexerClient(
            endpoint=self.search_endpoint,
            credential=self.credential
        )
        self.blob_service_client = BlobServiceClient(
            account_url=self.storage_endpoint,
            credential=self.credential
        )
    
    def setup_storage_container(self) -> None:
        """Create blob storage container if it doesn't exist."""
        try:
            container_client = self.blob_service_client.get_container_client(self.container_name)
            
            # Check if container exists, create if not
            if not container_client.exists():
                container_client.create_container()
                print(f"Created blob container: {self.container_name}")
            else:
                print(f"Blob container already exists: {self.container_name}")
                
        except Exception as e:
            print(f"Error setting up storage container: {e}")
    
    def upload_documents(self, data_dir: Path) -> List[str]:
        """Upload PDF documents to blob storage."""
        uploaded_files = []
        
        try:
            container_client = self.blob_service_client.get_container_client(self.container_name)
            
            # Upload weather PDFs
            weather_dir = data_dir / "weather_pdfs"
            if weather_dir.exists():
                for pdf_file in weather_dir.glob("*.pdf"):
                    blob_name = f"weather/{pdf_file.name}"
                    blob_client = container_client.get_blob_client(blob_name)
                    
                    with open(pdf_file, "rb") as data:
                        blob_client.upload_blob(data, overwrite=True)
                    
                    uploaded_files.append(blob_name)
                    print(f"Uploaded: {blob_name}")
            
            # Upload news PDFs
            news_dir = data_dir / "news_pdfs"
            if news_dir.exists():
                for pdf_file in news_dir.glob("*.pdf"):
                    blob_name = f"news/{pdf_file.name}"
                    blob_client = container_client.get_blob_client(blob_name)
                    
                    with open(pdf_file, "rb") as data:
                        blob_client.upload_blob(data, overwrite=True)
                    
                    uploaded_files.append(blob_name)
                    print(f"Uploaded: {blob_name}")
            
            print(f"Uploaded {len(uploaded_files)} documents to blob storage")
            return uploaded_files
            
        except Exception as e:
            print(f"Error uploading documents: {e}")
            return []
    
    def create_simple_index(self) -> None:
        """Create a simple search index for keyword search."""
        fields = [
            SearchField(name="id", type=SearchFieldDataType.String, key=True, retrievable=True),
            SearchField(name="title", type=SearchFieldDataType.String, searchable=True, retrievable=True, filterable=True),
            SearchField(name="content", type=SearchFieldDataType.String, searchable=True, retrievable=True),
            SearchField(name="category", type=SearchFieldDataType.String, filterable=True, retrievable=True),
            SearchField(name="source_type", type=SearchFieldDataType.String, filterable=True, retrievable=True),
            SearchField(name="file_path", type=SearchFieldDataType.String, retrievable=True),
            SearchField(name="last_modified", type=SearchFieldDataType.DateTimeOffset, retrievable=True, sortable=True),
        ]
        
        index = SearchIndex(name=self.index_name, fields=fields)
        
        try:
            result = self.search_index_client.create_index(index)
            print(f"Created simple search index: {result.name}")
        except Exception as e:
            if "already exists" in str(e).lower():
                print(f"Index already exists: {self.index_name}")
            else:
                print(f"Error creating index: {e}")
    
    def create_data_source(self) -> None:
        """Create a data source connection to blob storage."""
        data_source = SearchIndexerDataSourceConnection(
            name=self.data_source_name,
            type="azureblob",
            connection_string=f"ResourceId=/subscriptions/{os.getenv('AZURE_SUBSCRIPTION_ID')}/resourceGroups/{os.getenv('AZURE_RESOURCE_GROUP')}/providers/Microsoft.Storage/storageAccounts/{self.storage_account_name};",
            container=SearchIndexerDataContainer(name=self.container_name)
        )
        
        try:
            result = self.search_indexer_client.create_data_source_connection(data_source)
            print(f"Created data source: {result.name}")
        except Exception as e:
            if "already exists" in str(e).lower():
                print(f"Data source already exists: {self.data_source_name}")
            else:
                print(f"Error creating data source: {e}")
    
    def create_simple_indexer(self) -> None:
        """Create a simple indexer without skillsets."""
        # Field mappings from blob storage to index
        field_mappings = [
            FieldMapping(source_field_name="metadata_storage_name", target_field_name="title"),
            FieldMapping(source_field_name="content", target_field_name="content"),
            FieldMapping(source_field_name="metadata_storage_path", target_field_name="file_path"),
            FieldMapping(source_field_name="metadata_storage_last_modified", target_field_name="last_modified")
        ]
        
        # Create simple indexer without skillset
        indexer = SearchIndexer(
            name=self.indexer_name,
            description="Simple indexer for document keyword search",
            data_source_name=self.data_source_name,
            target_index_name=self.index_name,
            schedule=IndexingSchedule(interval="PT2H"),  # Run every 2 hours
            field_mappings=field_mappings,
            parameters={
                "batchSize": 10,
                "maxFailedItems": 5,
                "maxFailedItemsPerBatch": 2,
                "configuration": {
                    "dataToExtract": "contentAndMetadata",
                    "parsingMode": "default",
                    "imageAction": "none"
                }
            }
        )
        
        try:
            result = self.search_indexer_client.create_indexer(indexer)
            print(f"Created simple indexer: {result.name}")
        except Exception as e:
            if "already exists" in str(e).lower():
                print(f"Indexer already exists: {self.indexer_name}")
            else:
                print(f"Error creating indexer: {e}")
    
    def run_indexer(self) -> None:
        """Run the simple indexer to process documents."""
        try:
            self.search_indexer_client.run_indexer(self.indexer_name)
            print(f"Started simple indexer run: {self.indexer_name}")
        except Exception as e:
            print(f"Error running indexer: {e}")
    
    def get_indexer_status(self) -> Dict:
        """Get the status of the simple indexer."""
        try:
            status = self.search_indexer_client.get_indexer_status(self.indexer_name)
            return {
                "status": status.status,
                "last_result": {
                    "status": status.last_result.status if status.last_result else None,
                    "item_count": status.last_result.item_count if status.last_result else 0,
                    "failed_item_count": status.last_result.failed_item_count if status.last_result else 0,
                    "start_time": status.last_result.start_time if status.last_result else None,
                    "end_time": status.last_result.end_time if status.last_result else None
                }
            }
        except Exception as e:
            print(f"Error getting indexer status: {e}")
            return {"error": str(e)}
    
    def setup_simple_pipeline(self, data_dir: Path) -> Dict:
        """Set up the complete simple indexing pipeline."""
        try:
            print("Setting up Azure AI Search simple indexing pipeline...")
            
            # 1. Setup storage and upload documents
            print("\n1. Setting up blob storage...")
            self.setup_storage_container()
            uploaded_files = self.upload_documents(data_dir)
            
            # 2. Create simple search index
            print("\n2. Creating simple search index...")
            self.create_simple_index()
            
            # 3. Create data source
            print("\n3. Creating data source...")
            self.create_data_source()
            
            # 4. Create simple indexer (no skillset needed)
            print("\n4. Creating simple indexer...")
            self.create_simple_indexer()
            
            # 5. Run indexer
            print("\n5. Running simple indexer...")
            self.run_indexer()
            
            print("\n✅ Simple pipeline setup complete!")
            print("\nNext steps:")
            print(f"- Monitor indexer status with: get_indexer_status()")
            print(f"- Index name: {self.index_name}")
            print(f"- Uploaded {len(uploaded_files)} documents")
            print(f"- Search capability: Keyword search only")
            
            return {
                "success": True,
                "index_name": self.index_name,
                "uploaded_files": len(uploaded_files),
                "search_type": "keyword"
            }
            
        except Exception as e:
            print(f"Error setting up simple pipeline: {e}")
            return {"error": str(e)}
    
    def cleanup_resources(self) -> None:
        """Clean up Azure resources."""
        pass  # No async cleanup needed for sync version


def main():
    """Main function to set up the simple document indexing pipeline."""
    indexer = SimpleDocumentIndexer()
    
    # Check if data directory exists
    data_dir = Path("data")
    if not data_dir.exists():
        print("Data directory not found: data")
        print("Please run the document generation scripts first:")
        print("- python scripts/generate_weather_data.py")
        print("- python scripts/generate_news_data.py")
        return
    
    try:
        # Set up the simple indexing pipeline
        result = indexer.setup_simple_pipeline(data_dir)
        
        if result.get("success"):
            print(f"\n🎉 Successfully set up simple indexing!")
            print(f"   Index: {result['index_name']}")
            print(f"   Documents: {result['uploaded_files']}")
            print(f"   Search Type: {result['search_type']}")
            
            # Wait a moment and check indexer status
            print(f"\n📊 Initial indexer status:")
            import time
            time.sleep(5)
            status = indexer.get_indexer_status()
            print(status)
        else:
            print(f"❌ Setup failed: {result.get('error', 'Unknown error')}")
    
    finally:
        # Clean up resources
        indexer.cleanup_resources()


if __name__ == "__main__":
    main()