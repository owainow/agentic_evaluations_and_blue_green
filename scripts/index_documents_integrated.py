#!/usr/bin/env python3
"""
Document indexing script using Azure AI Search integrated vectorization.
Uses Azure AI Search's built-in skills for document processing, chunking, and vectorization.
"""

import os
import json
import asyncio
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

# Azure libraries
from azure.identity import DefaultAzureCredential
from azure.search.documents.indexes import SearchIndexClient, SearchIndexerClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchField,
    SearchFieldDataType,
    VectorSearch,
    VectorSearchProfile,
    HnswAlgorithmConfiguration,
    VectorSearchAlgorithmMetric,
    AzureOpenAIVectorizer,
    AzureOpenAIVectorizerParameters,
    SearchIndexer,
    SearchIndexerDataSourceConnection,
    SearchIndexerSkillset,
    SplitSkill,
    AzureOpenAIEmbeddingSkill,
    InputFieldMappingEntry,
    OutputFieldMappingEntry,
    SearchIndexerDataContainer,
    IndexingSchedule
)
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError

class IntegratedVectorizationIndexer:
    """
    Manages document indexing using Azure AI Search's integrated vectorization capabilities.
    This approach leverages Azure AI Search's built-in skills for document processing.
    """
    
    def __init__(self):
        """Initialize the indexer with Azure credentials and endpoints."""
        self.credential = DefaultAzureCredential()
        
        # Configuration from environment variables
        self.search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
        self.search_service_name = self._extract_service_name(self.search_endpoint)
        self.storage_account_name = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
        self.storage_connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")  # Optional
        self.aoai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.aoai_deployment_name = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-small")
        self.aoai_model_name = os.getenv("AZURE_OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        
        # Initialize clients
        self.search_index_client = SearchIndexClient(
            endpoint=self.search_endpoint,
            credential=self.credential
        )
        
        self.search_indexer_client = SearchIndexerClient(
            endpoint=self.search_endpoint,
            credential=self.credential
        )
        
        # Use identity-based authentication for storage
        if self.storage_connection_string:
            try:
                self.blob_service_client = BlobServiceClient.from_connection_string(
                    self.storage_connection_string
                )
            except Exception:
                # Fallback to identity-based auth if connection string fails
                if self.storage_account_name:
                    account_url = f"https://{self.storage_account_name}.blob.core.windows.net"
                    self.blob_service_client = BlobServiceClient(
                        account_url=account_url,
                        credential=self.credential
                    )
                else:
                    raise ValueError("Neither connection string nor storage account name available")
        else:
            # Use identity-based authentication
            if not self.storage_account_name:
                raise ValueError("AZURE_STORAGE_ACCOUNT_NAME environment variable is required")
            account_url = f"https://{self.storage_account_name}.blob.core.windows.net"
            self.blob_service_client = BlobServiceClient(
                account_url=account_url,
                credential=self.credential
            )
        
        # Container for documents
        self.container_name = "knowledge-documents"
        
        # Index configuration
        self.index_name = "knowledge-vector-index"
        self.data_source_name = "knowledge-data-source"
        self.skillset_name = "knowledge-skillset"
        self.indexer_name = "knowledge-indexer"
    
    def _extract_service_name(self, endpoint: str) -> str:
        """Extract service name from search endpoint."""
        if not endpoint:
            raise ValueError("AZURE_SEARCH_ENDPOINT environment variable is required")
        # Extract from https://servicename.search.windows.net
        return endpoint.split("//")[1].split(".")[0]
    
    async def setup_storage_container(self) -> None:
        """Create blob storage container if it doesn't exist."""
        try:
            container_client = self.blob_service_client.get_container_client(self.container_name)
            container_client.create_container()
            print(f"Created blob container: {self.container_name}")
        except ResourceExistsError:
            print(f"Blob container already exists: {self.container_name}")
    
    async def upload_documents(self, data_dir: Path) -> List[str]:
        """Upload PDF documents to blob storage."""
        uploaded_files = []
        container_client = self.blob_service_client.get_container_client(self.container_name)
        
        # Upload weather PDFs
        weather_dir = data_dir / "weather_pdfs"
        if weather_dir.exists():
            for pdf_file in weather_dir.glob("*.pdf"):
                blob_name = f"weather/{pdf_file.name}"
                try:
                    with open(pdf_file, "rb") as data:
                        container_client.upload_blob(
                            name=blob_name,
                            data=data,
                            overwrite=True,
                            metadata={
                                "category": "weather_data",
                                "source_type": "historical_weather",
                                "upload_date": datetime.now().isoformat()
                            }
                        )
                    uploaded_files.append(blob_name)
                    print(f"Uploaded: {blob_name}")
                except Exception as e:
                    print(f"Error uploading {pdf_file}: {e}")
        
        # Upload news PDFs
        news_dir = data_dir / "news_pdfs"
        if news_dir.exists():
            for pdf_file in news_dir.glob("*.pdf"):
                blob_name = f"news/{pdf_file.name}"
                try:
                    with open(pdf_file, "rb") as data:
                        container_client.upload_blob(
                            name=blob_name,
                            data=data,
                            overwrite=True,
                            metadata={
                                "category": "news_articles",
                                "source_type": "weather_climate_news",
                                "upload_date": datetime.now().isoformat()
                            }
                        )
                    uploaded_files.append(blob_name)
                    print(f"Uploaded: {blob_name}")
                except Exception as e:
                    print(f"Error uploading {pdf_file}: {e}")
        
        print(f"Uploaded {len(uploaded_files)} documents to blob storage")
        return uploaded_files
    
    def create_vector_index(self) -> None:
        """Create a vector search index with integrated vectorization support."""
        # Vector search configuration
        vector_search = VectorSearch(
            algorithms=[
                HnswAlgorithmConfiguration(
                    name="hnsw-algorithm",
                    parameters={
                        "m": 4,
                        "efConstruction": 400,
                        "efSearch": 100,
                        "metric": VectorSearchAlgorithmMetric.COSINE
                    }
                )
            ],
            profiles=[
                VectorSearchProfile(
                    name="vector-profile-hnsw",
                    algorithm_configuration_name="hnsw-algorithm",
                    vectorizer_name="openai-vectorizer"
                )
            ],
            vectorizers=[
                AzureOpenAIVectorizer(
                    vectorizer_name="openai-vectorizer",
                    parameters=AzureOpenAIVectorizerParameters(
                        resource_url=self.aoai_endpoint,
                        deployment_name=self.aoai_deployment_name,
                        model_name=self.aoai_model_name
                    )
                )
            ]
        )
        
        # Index fields
        fields = [
            SearchField(
                name="id",
                type=SearchFieldDataType.String,
                key=True,
                filterable=True,
                searchable=False
            ),
            SearchField(
                name="title",
                type=SearchFieldDataType.String,
                searchable=True,
                filterable=True,
                sortable=True
            ),
            SearchField(
                name="content",
                type=SearchFieldDataType.String,
                searchable=True
            ),
            SearchField(
                name="chunk_text",
                type=SearchFieldDataType.String,
                searchable=True
            ),
            SearchField(
                name="chunk_vector",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                stored=True,
                vector_search_dimensions=1536,  # text-embedding-3-small dimensions
                vector_search_profile_name="vector-profile-hnsw"
            ),
            SearchField(
                name="category",
                type=SearchFieldDataType.String,
                filterable=True,
                facetable=True
            ),
            SearchField(
                name="source_type",
                type=SearchFieldDataType.String,
                filterable=True,
                facetable=True
            ),
            SearchField(
                name="file_path",
                type=SearchFieldDataType.String,
                filterable=True
            ),
            SearchField(
                name="last_modified",
                type=SearchFieldDataType.DateTimeOffset,
                filterable=True,
                sortable=True
            )
        ]
        
        # Create the index
        index = SearchIndex(
            name=self.index_name,
            fields=fields,
            vector_search=vector_search
        )
        
        try:
            result = self.search_index_client.create_index(index)
            print(f"Created vector index: {result.name}")
        except ResourceExistsError:
            print(f"Vector index already exists: {self.index_name}")
        except Exception as e:
            print(f"Error creating index: {e}")
    
    def create_data_source(self) -> None:
        """Create a data source connection to blob storage using identity-based authentication."""
        # Use identity-based authentication instead of connection string
        storage_account_name = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
        resource_group_name = os.getenv("AZURE_RESOURCE_GROUP_NAME")
        subscription_id = "269eee56-58bc-45eb-9dca-4d22421c45fa"  # Your subscription ID
        
        if not storage_account_name:
            raise ValueError("AZURE_STORAGE_ACCOUNT_NAME environment variable is required")
        if not resource_group_name:
            raise ValueError("AZURE_RESOURCE_GROUP_NAME environment variable is required")
        
        # Use ResourceId format for identity-based authentication
        resource_id = f"/subscriptions/{subscription_id}/resourceGroups/{resource_group_name}/providers/Microsoft.Storage/storageAccounts/{storage_account_name}"
        
        data_source = SearchIndexerDataSourceConnection(
            name=self.data_source_name,
            type="azureblob",
            connection_string=f"ResourceId={resource_id};",
            container=SearchIndexerDataContainer(name=self.container_name)
        )
        
        try:
            result = self.search_indexer_client.create_data_source_connection(data_source)
            print(f"Created data source: {result.name}")
        except ResourceExistsError:
            print(f"Data source already exists: {self.data_source_name}")
        except Exception as e:
            print(f"Error creating data source: {e}")
    
    def create_skillset(self) -> None:
        """Create a skillset with Text Split and Azure OpenAI Embedding skills."""
        # Text Split skill for chunking
        text_split_skill = SplitSkill(
            name="text-split-skill",
            context="/document",
            text_split_mode="pages",
            maximum_page_length=2000,
            page_overlap_length=500,
            maximum_pages_to_take=0,
            default_language_code="en",
            inputs=[
                InputFieldMappingEntry(
                    name="text",
                    source="/document/content"
                )
            ],
            outputs=[
                OutputFieldMappingEntry(
                    name="textItems",
                    target_name="chunks"
                )
            ]
        )
        
        # Azure OpenAI Embedding skill for vectorization
        embedding_skill = AzureOpenAIEmbeddingSkill(
            name="embedding-skill",
            context="/document/chunks/*",
            resource_url=self.aoai_endpoint,
            deployment_name=self.aoai_deployment_name,
            model_name=self.aoai_model_name,
            dimensions=1536,
            inputs=[
                InputFieldMappingEntry(
                    name="text",
                    source="/document/chunks/*"
                )
            ],
            outputs=[
                OutputFieldMappingEntry(
                    name="embedding",
                    target_name="chunk_vector"
                )
            ]
        )
        
        # Create skillset
        skillset = SearchIndexerSkillset(
            name=self.skillset_name,
            skills=[text_split_skill, embedding_skill],
            description="Skillset for chunking and vectorizing documents"
        )
        
        try:
            result = self.search_indexer_client.create_skillset(skillset)
            print(f"Created skillset: {result.name}")
        except ResourceExistsError:
            print(f"Skillset already exists: {self.skillset_name}")
        except Exception as e:
            print(f"Error creating skillset: {e}")
    
    def create_indexer(self) -> None:
        """Create an indexer to execute the vectorization pipeline."""
        # Field mappings from data source to index
        field_mappings = [
            {
                "sourceFieldName": "metadata_storage_name",
                "targetFieldName": "title"
            },
            {
                "sourceFieldName": "content",
                "targetFieldName": "content"
            },
            {
                "sourceFieldName": "metadata_storage_path",
                "targetFieldName": "file_path"
            },
            {
                "sourceFieldName": "metadata_storage_last_modified",
                "targetFieldName": "last_modified"
            }
        ]
        
        # Output field mappings from skillset to index - REMOVE THIS FOR INDEX PROJECTIONS
        # output_field_mappings = []
        
        # Create indexer with schedule - NO OUTPUT FIELD MAPPINGS
        indexer = SearchIndexer(
            name=self.indexer_name,
            description="Indexer to process documents and generate embeddings",
            data_source_name=self.data_source_name,
            target_index_name=self.index_name,
            skillset_name=self.skillset_name,
            schedule=IndexingSchedule(interval="PT2H"),  # Run every 2 hours
            field_mappings=field_mappings,
            # output_field_mappings=output_field_mappings,  # REMOVE FOR INDEX PROJECTIONS
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
            print(f"Created indexer: {result.name}")
        except ResourceExistsError:
            print(f"Indexer already exists: {self.indexer_name}")
        except Exception as e:
            print(f"Error creating indexer: {e}")
            # Print more detailed error information
            if hasattr(e, 'error') and hasattr(e.error, 'message'):
                print(f"Detailed error message: {e.error.message}")
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                print(f"Response text: {e.response.text()}")
            import traceback
            print(f"Full traceback: {traceback.format_exc()}")
    
    def run_indexer(self) -> None:
        """Run the indexer to process documents."""
        try:
            self.search_indexer_client.run_indexer(self.indexer_name)
            print(f"Started indexer run: {self.indexer_name}")
        except Exception as e:
            print(f"Error running indexer: {e}")
    
    def get_indexer_status(self) -> Dict:
        """Get the status of the indexer."""
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
    
    async def setup_complete_pipeline(self, data_dir: Path) -> Dict:
        """Set up the complete integrated vectorization pipeline."""
        try:
            print("Setting up Azure AI Search integrated vectorization pipeline...")
            
            # 1. Setup storage and upload documents
            print("\n1. Setting up blob storage...")
            await self.setup_storage_container()
            uploaded_files = await self.upload_documents(data_dir)
            
            # 2. Create search index
            print("\n2. Creating vector search index...")
            self.create_vector_index()
            
            # 3. Create data source
            print("\n3. Creating data source...")
            self.create_data_source()
            
            # 4. Create skillset
            print("\n4. Creating skillset...")
            self.create_skillset()
            
            # 5. Create indexer
            print("\n5. Creating indexer...")
            self.create_indexer()
            
            # 6. Run indexer
            print("\n6. Running indexer...")
            self.run_indexer()
            
            print("\n✅ Pipeline setup complete!")
            print("\nNext steps:")
            print(f"- Monitor indexer status with: get_indexer_status()")
            print(f"- Index name: {self.index_name}")
            print(f"- Uploaded {len(uploaded_files)} documents")
            
            return {
                "success": True,
                "index_name": self.index_name,
                "uploaded_files": len(uploaded_files),
                "indexer_name": self.indexer_name
            }
            
        except Exception as e:
            print(f"Error setting up pipeline: {e}")
            return {"success": False, "error": str(e)}

def main():
    """Main function to run the integrated vectorization setup."""
    # Check environment variables
    required_env_vars = [
        "AZURE_SEARCH_ENDPOINT",
        "AZURE_STORAGE_ACCOUNT_NAME",  # Changed from connection string to account name
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_EMBEDDING_DEPLOYMENT"
    ]
    
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        print(f"Missing required environment variables: {missing_vars}")
        print("Please set these in your .env file or environment")
        return
    
    # Initialize indexer
    indexer = IntegratedVectorizationIndexer()
    
    # Set up the pipeline
    data_dir = Path("data")
    if not data_dir.exists():
        print(f"Data directory not found: {data_dir}")
        print("Please run the document generation scripts first:")
        print("- python scripts/generate_weather_data.py")
        print("- python scripts/generate_news_data.py")
        return
    
    # Run async setup
    result = asyncio.run(indexer.setup_complete_pipeline(data_dir))
    
    if result["success"]:
        print(f"\n🎉 Successfully set up integrated vectorization!")
        print(f"   Index: {result['index_name']}")
        print(f"   Documents: {result['uploaded_files']}")
        
        # Check initial status
        print("\n📊 Initial indexer status:")
        status = indexer.get_indexer_status()
        print(json.dumps(status, indent=2, default=str))
    else:
        print(f"\n❌ Setup failed: {result.get('error')}")

if __name__ == "__main__":
    main()