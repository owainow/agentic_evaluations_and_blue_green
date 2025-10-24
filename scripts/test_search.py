#!/usr/bin/env python3
"""
Test script for searching the indexed knowledge base using Azure AI Search.
Demonstrates vector search, hybrid search, and semantic ranking capabilities.
"""

import os
import asyncio
from typing import List, Dict, Optional
from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery, VectorQuery
from azure.core.credentials import AzureKeyCredential

class KnowledgeSearcher:
    """
    Handles searching the indexed knowledge base using various Azure AI Search capabilities.
    """
    
    def __init__(self):
        """Initialize the search client."""
        self.search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
        self.search_key = os.getenv("AZURE_SEARCH_KEY")
        self.aoai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.aoai_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
        
        # Use either key-based or credential-based authentication
        if self.search_key:
            credential = AzureKeyCredential(self.search_key)
        else:
            credential = DefaultAzureCredential()
        
        self.search_client = SearchClient(
            endpoint=self.search_endpoint,
            index_name="knowledge-vector-index",
            credential=credential
        )
        
        # For generating query embeddings
        if self.aoai_endpoint and self.aoai_deployment:
            from openai import AzureOpenAI
            self.openai_client = AzureOpenAI(
                api_key=os.getenv("AZURE_OPENAI_KEY"),
                api_version="2024-02-01",
                azure_endpoint=self.aoai_endpoint
            )
    
    async def generate_query_embedding(self, query: str) -> List[float]:
        """Generate embedding for a search query."""
        try:
            response = await asyncio.to_thread(
                self.openai_client.embeddings.create,
                input=query,
                model=self.aoai_deployment
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error generating query embedding: {e}")
            return None
    
    def keyword_search(self, query: str, top: int = 5) -> Dict:
        """Perform traditional keyword search."""
        try:
            results = self.search_client.search(
                search_text=query,
                top=top,
                select=["title", "chunk_text", "category", "source_type", "file_path"],
                highlight_fields=["chunk_text"]
            )
            
            search_results = []
            for result in results:
                search_results.append({
                    "score": result["@search.score"],
                    "title": result.get("title", ""),
                    "chunk_text": result.get("chunk_text", "")[:500] + "...",
                    "category": result.get("category", ""),
                    "source_type": result.get("source_type", ""),
                    "file_path": result.get("file_path", ""),
                    "highlights": result.get("@search.highlights", {})
                })
            
            return {
                "query": query,
                "search_type": "keyword",
                "results": search_results
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def vector_search(self, query: str, top: int = 5) -> Dict:
        """Perform vector similarity search."""
        try:
            # Generate embedding for the query
            query_embedding = await self.generate_query_embedding(query)
            if not query_embedding:
                return {"error": "Failed to generate query embedding"}
            
            # Create vector query
            vector_query = VectorizedQuery(
                vector=query_embedding,
                k_nearest_neighbors=top,
                fields="chunk_vector"
            )
            
            results = self.search_client.search(
                search_text=None,
                vector_queries=[vector_query],
                select=["title", "chunk_text", "category", "source_type", "file_path"],
                top=top
            )
            
            search_results = []
            for result in results:
                search_results.append({
                    "score": result["@search.score"],
                    "title": result.get("title", ""),
                    "chunk_text": result.get("chunk_text", "")[:500] + "...",
                    "category": result.get("category", ""),
                    "source_type": result.get("source_type", ""),
                    "file_path": result.get("file_path", "")
                })
            
            return {
                "query": query,
                "search_type": "vector",
                "results": search_results
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def hybrid_search(self, query: str, top: int = 5) -> Dict:
        """Perform hybrid search combining keyword and vector search."""
        try:
            # Generate embedding for the query
            query_embedding = await self.generate_query_embedding(query)
            if not query_embedding:
                return {"error": "Failed to generate query embedding"}
            
            # Create vector query
            vector_query = VectorizedQuery(
                vector=query_embedding,
                k_nearest_neighbors=top,
                fields="chunk_vector"
            )
            
            results = self.search_client.search(
                search_text=query,
                vector_queries=[vector_query],
                select=["title", "chunk_text", "category", "source_type", "file_path"],
                highlight_fields=["chunk_text"],
                top=top
            )
            
            search_results = []
            for result in results:
                search_results.append({
                    "score": result["@search.score"],
                    "title": result.get("title", ""),
                    "chunk_text": result.get("chunk_text", "")[:500] + "...",
                    "category": result.get("category", ""),
                    "source_type": result.get("source_type", ""),
                    "file_path": result.get("file_path", ""),
                    "highlights": result.get("@search.highlights", {})
                })
            
            return {
                "query": query,
                "search_type": "hybrid",
                "results": search_results
            }
        except Exception as e:
            return {"error": str(e)}
    
    def filtered_search(self, query: str, category: str = None, source_type: str = None, top: int = 5) -> Dict:
        """Perform search with category or source type filters."""
        try:
            # Build filter expression
            filters = []
            if category:
                filters.append(f"category eq '{category}'")
            if source_type:
                filters.append(f"source_type eq '{source_type}'")
            
            filter_expression = " and ".join(filters) if filters else None
            
            results = self.search_client.search(
                search_text=query,
                filter=filter_expression,
                select=["title", "chunk_text", "category", "source_type", "file_path"],
                highlight_fields=["chunk_text"],
                top=top
            )
            
            search_results = []
            for result in results:
                search_results.append({
                    "score": result["@search.score"],
                    "title": result.get("title", ""),
                    "chunk_text": result.get("chunk_text", "")[:500] + "...",
                    "category": result.get("category", ""),
                    "source_type": result.get("source_type", ""),
                    "file_path": result.get("file_path", ""),
                    "highlights": result.get("@search.highlights", {})
                })
            
            return {
                "query": query,
                "search_type": "filtered",
                "filters": {"category": category, "source_type": source_type},
                "results": search_results
            }
        except Exception as e:
            return {"error": str(e)}

def print_search_results(results: Dict) -> None:
    """Pretty print search results."""
    if "error" in results:
        print(f"❌ Search error: {results['error']}")
        return
    
    print(f"\n🔍 {results['search_type'].title()} Search Results for: '{results['query']}'")
    print("=" * 80)
    
    if "filters" in results and any(results["filters"].values()):
        print(f"Filters: {results['filters']}")
        print("-" * 40)
    
    if not results["results"]:
        print("No results found.")
        return
    
    for i, result in enumerate(results["results"], 1):
        print(f"\n📄 Result {i} (Score: {result['score']:.4f})")
        print(f"Title: {result['title']}")
        print(f"Category: {result['category']} | Source: {result['source_type']}")
        print(f"File: {result['file_path']}")
        print(f"Content: {result['chunk_text']}")
        
        if "highlights" in result and result["highlights"]:
            print("Highlights:")
            for field, highlights in result["highlights"].items():
                for highlight in highlights:
                    print(f"  - {highlight}")
        
        print("-" * 40)

async def run_search_tests():
    """Run various search tests to demonstrate capabilities."""
    searcher = KnowledgeSearcher()
    
    # Test queries
    test_queries = [
        "What was the temperature in New York during winter 2023?",
        "climate change effects on weather patterns",
        "precipitation data Chicago",
        "extreme weather events news",
        "seasonal temperature variations"
    ]
    
    print("🚀 Testing Azure AI Search Knowledge Base")
    print("=" * 60)
    
    for query in test_queries:
        print(f"\n\n🔍 Testing query: '{query}'")
        print("=" * 60)
        
        # Keyword search
        print("\n1️⃣ Keyword Search:")
        keyword_results = searcher.keyword_search(query, top=3)
        print_search_results(keyword_results)
        
        # Vector search
        print("\n2️⃣ Vector Search:")
        vector_results = await searcher.vector_search(query, top=3)
        print_search_results(vector_results)
        
        # Hybrid search
        print("\n3️⃣ Hybrid Search:")
        hybrid_results = await searcher.hybrid_search(query, top=3)
        print_search_results(hybrid_results)
        
        # Filtered search example
        if "weather" in query.lower():
            print("\n4️⃣ Filtered Search (Weather category only):")
            filtered_results = searcher.filtered_search(query, category="weather", top=3)
            print_search_results(filtered_results)
        
        print("\n" + "="*80)
        
        # Wait between queries to avoid rate limiting
        await asyncio.sleep(1)

def main():
    """Main function to run search tests."""
    print("📚 Azure AI Search Knowledge Base Tester")
    print("=" * 50)
    
    # Check required environment variables
    required_vars = ["AZURE_SEARCH_ENDPOINT"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {missing_vars}")
        return
    
    # Run search tests
    asyncio.run(run_search_tests())

if __name__ == "__main__":
    main()