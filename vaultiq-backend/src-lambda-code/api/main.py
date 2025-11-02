"""
FastAPI Application for VaultIQ RAG Query Pipeline
Handles natural language queries using Retrieval-Augmented Generation
"""
import json
import os
import boto3
from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from mangum import Mangum

from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

# Bedrock imports
from langchain_aws import BedrockEmbeddings, ChatBedrock

# Initialize AWS clients
bedrock_runtime = boto3.client('bedrock-runtime', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
dynamodb = boto3.resource('dynamodb')

# Environment variables
METADATA_TABLE = os.environ['METADATA_TABLE']
OPENSEARCH_ENDPOINT = os.environ['OPENSEARCH_ENDPOINT']
OPENSEARCH_INDEX = os.environ['OPENSEARCH_INDEX']

# Initialize DynamoDB table
metadata_table = dynamodb.Table(METADATA_TABLE)

# Initialize FastAPI app
app = FastAPI(
    title="VaultIQ API",
    description="AI-Powered Unified Knowledge Hub",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models
class QueryRequest(BaseModel):
    """Request model for query endpoint"""
    query: str
    top_k: Optional[int] = 5
    source_filter: Optional[List[str]] = None


class Source(BaseModel):
    """Source document model"""
    title: str
    url: str
    source_type: str
    relevance_score: float
    snippet: str


class QueryResponse(BaseModel):
    """Response model for query endpoint"""
    answer: str
    sources: List[Source]
    query: str
    timestamp: str


def get_opensearch_client():
    """
    Initialize OpenSearch Serverless client with AWS authentication
    
    Returns:
        OpenSearch client instance
    """
    region = os.environ.get('AWS_REGION', 'us-east-1')
    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(
        credentials.access_key,
        credentials.secret_key,
        region,
        'aoss',
        session_token=credentials.token
    )
    
    # Extract host from endpoint
    host = OPENSEARCH_ENDPOINT.replace('https://', '')
    
    client = OpenSearch(
        hosts=[{'host': host, 'port': 443}],
        http_auth=awsauth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
        timeout=300
    )
    
    return client


def create_query_embedding(query: str) -> List[float]:
    """
    Create embedding for user query using Amazon Titan
    
    Args:
        query: User's natural language query
    
    Returns:
        Embedding vector
    """
    try:
        embeddings = BedrockEmbeddings(
            client=bedrock_runtime,
            model_id="amazon.titan-embed-text-v1"
        )
        
        # Embed single query
        vector = embeddings.embed_query(query)
        
        return vector
        
    except Exception as e:
        print(f"Error creating query embedding: {e}")
        raise


def search_similar_documents(
    os_client: OpenSearch,
    query_embedding: List[float],
    top_k: int = 5,
    source_filter: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Search for similar documents in OpenSearch using vector similarity
    
    Args:
        os_client: OpenSearch client instance
        query_embedding: Query embedding vector
        top_k: Number of results to return
        source_filter: Optional list of source types to filter
    
    Returns:
        List of matching documents with scores
    """
    try:
        # Build KNN query
        knn_query = {
            "size": top_k,
            "query": {
                "knn": {
                    "embedding": {
                        "vector": query_embedding,
                        "k": top_k
                    }
                }
            },
            "_source": ["text", "title", "source", "source_url", "metadata", "document_id"]
        }
        
        # Add source filter if provided
        if source_filter:
            knn_query["query"] = {
                "bool": {
                    "must": [
                        {"knn": {"embedding": {"vector": query_embedding, "k": top_k}}}
                    ],
                    "filter": [
                        {"terms": {"source": source_filter}}
                    ]
                }
            }
        
        # Execute search
        response = os_client.search(
            index=OPENSEARCH_INDEX,
            body=knn_query
        )
        
        # Extract results
        results = []
        for hit in response['hits']['hits']:
            results.append({
                'text': hit['_source']['text'],
                'title': hit['_source'].get('title', 'Untitled'),
                'source': hit['_source'].get('source', 'unknown'),
                'source_url': hit['_source'].get('source_url', ''),
                'metadata': hit['_source'].get('metadata', {}),
                'score': hit['_score'],
                'document_id': hit['_source'].get('document_id', '')
            })
        
        print(f"Found {len(results)} similar documents")
        return results
        
    except Exception as e:
        print(f"Error searching documents: {e}")
        raise


def generate_answer_with_claude(query: str, context_docs: List[Dict[str, Any]]) -> str:
    """
    Generate answer using Claude 3 Haiku with retrieved context
    
    Args:
        query: User's original query
        context_docs: List of retrieved document chunks
    
    Returns:
        Generated answer string
    """
    try:
        # Initialize Claude 3 Haiku
        llm = ChatBedrock(
            client=bedrock_runtime,
            model_id="anthropic.claude-3-haiku-20240307-v1:0",
            model_kwargs={
                "temperature": 0.7,
                "max_tokens": 1000
            }
        )
        
        # Build context from retrieved documents
        context_text = "\n\n".join([
            f"Source: {doc['title']} ({doc['source']})\n{doc['text']}"
            for doc in context_docs
        ])
        
        # Construct prompt
        prompt = f"""You are VaultIQ, an AI assistant that helps answer questions about IT management, documentation, and organizational knowledge.

Based on the following context from various sources (Confluence, Slack, Jira, GitHub), please answer the user's question accurately and comprehensively.

Context:
{context_text}

User Question: {query}

Instructions:
- Provide a clear, accurate answer based on the context provided
- If the context doesn't contain enough information, acknowledge this and provide the best answer you can
- Cite sources when making specific claims
- Be concise but thorough
- If there are conflicting pieces of information, acknowledge this

Answer:"""
        
        # Generate response
        response = llm.invoke(prompt)
        answer = response.content
        
        print(f"Generated answer with Claude 3 Haiku")
        return answer
        
    except Exception as e:
        print(f"Error generating answer: {e}")
        raise


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "VaultIQ API",
        "version": "1.0.0",
        "status": "active"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/api/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """
    Main RAG query endpoint
    
    Args:
        request: QueryRequest with user's query
    
    Returns:
        QueryResponse with answer and sources
    """
    try:
        print(f"Received query: {request.query}")
        
        # Step 1: Create embedding for the query
        query_embedding = create_query_embedding(request.query)
        
        # Step 2: Search for similar documents in OpenSearch
        os_client = get_opensearch_client()
        similar_docs = search_similar_documents(
            os_client,
            query_embedding,
            top_k=request.top_k,
            source_filter=request.source_filter
        )
        
        if not similar_docs:
            return QueryResponse(
                answer="I couldn't find any relevant information to answer your question. Please try rephrasing or asking about a different topic.",
                sources=[],
                query=request.query,
                timestamp=datetime.utcnow().isoformat()
            )
        
        # Step 3: Generate answer using Claude 3 Haiku with context
        answer = generate_answer_with_claude(request.query, similar_docs)
        
        # Step 4: Format sources
        sources = []
        for doc in similar_docs:
            # Truncate snippet to 200 characters
            snippet = doc['text'][:200] + "..." if len(doc['text']) > 200 else doc['text']
            
            sources.append(Source(
                title=doc['title'],
                url=doc['source_url'] or f"Document from {doc['source']}",
                source_type=doc['source'],
                relevance_score=float(doc['score']),
                snippet=snippet
            ))
        
        # Step 5: Return response
        return QueryResponse(
            answer=answer,
            sources=sources,
            query=request.query,
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        print(f"Error processing query: {str(e)}")
        import traceback
        traceback.print_exc()
        
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )


@app.get("/api/sources")
async def list_sources():
    """
    List available sources and document counts
    
    Returns:
        Dictionary with source statistics
    """
    try:
        os_client = get_opensearch_client()
        
        # Aggregate by source
        agg_query = {
            "size": 0,
            "aggs": {
                "sources": {
                    "terms": {
                        "field": "source",
                        "size": 10
                    }
                }
            }
        }
        
        response = os_client.search(
            index=OPENSEARCH_INDEX,
            body=agg_query
        )
        
        sources = {}
        for bucket in response['aggregations']['sources']['buckets']:
            sources[bucket['key']] = bucket['doc_count']
        
        return {
            "sources": sources,
            "total_documents": response['hits']['total']['value'],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        print(f"Error listing sources: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error listing sources: {str(e)}"
        )


# Mangum handler for AWS Lambda
handler = Mangum(app)