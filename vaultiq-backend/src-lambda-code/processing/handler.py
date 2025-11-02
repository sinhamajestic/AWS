"""
Processing Lambda - RAG Ingestion Pipeline
Triggered by S3 events to process documents, create embeddings, and store in OpenSearch
"""
import json
import os
import boto3
from datetime import datetime
from urllib.parse import unquote_plus
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import hashlib

# LangChain imports
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document as LangChainDocument

# Bedrock imports
from langchain_aws import BedrockEmbeddings

# Initialize AWS clients
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
bedrock_runtime = boto3.client('bedrock-runtime', region_name=os.environ.get('AWS_REGION', 'us-east-1'))

# Environment variables
METADATA_TABLE = os.environ['METADATA_TABLE']
OPENSEARCH_ENDPOINT = os.environ['OPENSEARCH_ENDPOINT']
OPENSEARCH_INDEX = os.environ['OPENSEARCH_INDEX']

# Initialize DynamoDB table
metadata_table = dynamodb.Table(METADATA_TABLE)

# Initialize text splitter
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    length_function=len,
    separators=["\n\n", "\n", ". ", " ", ""]
)


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
    
    # Extract host from endpoint (remove https://)
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


def create_index_if_not_exists(os_client):
    """
    Create OpenSearch index with vector field if it doesn't exist
    
    Args:
        os_client: OpenSearch client instance
    """
    try:
        if not os_client.indices.exists(index=OPENSEARCH_INDEX):
            index_body = {
                "settings": {
                    "index.knn": True
                },
                "mappings": {
                    "properties": {
                        "embedding": {
                            "type": "knn_vector",
                            "dimension": 1536,  # Amazon Titan embeddings dimension
                            "method": {
                                "name": "hnsw",
                                "engine": "nmslib",
                                "parameters": {
                                    "ef_construction": 512,
                                    "m": 16
                                }
                            }
                        },
                        "text": {"type": "text"},
                        "document_id": {"type": "keyword"},
                        "chunk_id": {"type": "keyword"},
                        "source": {"type": "keyword"},
                        "source_url": {"type": "keyword"},
                        "title": {"type": "text"},
                        "metadata": {"type": "object"},
                        "timestamp": {"type": "date"}
                    }
                }
            }
            
            os_client.indices.create(index=OPENSEARCH_INDEX, body=index_body)
            print(f"Created index: {OPENSEARCH_INDEX}")
        else:
            print(f"Index already exists: {OPENSEARCH_INDEX}")
            
    except Exception as e:
        print(f"Error creating index: {e}")
        # Index might already exist, continue


def load_document_from_s3(bucket, key):
    """
    Load document from S3
    
    Args:
        bucket: S3 bucket name
        key: S3 object key
    
    Returns:
        Tuple of (document text, metadata)
    """
    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        content = response['Body'].read().decode('utf-8')
        
        # Parse JSON content
        data = json.loads(content)
        
        # Extract text based on source type
        source_type = key.split('/')[0]  # confluence, slack, jira, github
        
        text = ''
        metadata = {
            'source': source_type,
            's3_bucket': bucket,
            's3_key': key,
        }
        
        if source_type == 'confluence':
            text = f"Title: {data.get('title', '')}\n\n{data.get('content', '')}"
            metadata.update({
                'title': data.get('title', ''),
                'source_url': data.get('url', ''),
                'space': data.get('space', ''),
                'page_id': data.get('id', ''),
            })
            
        elif source_type == 'slack':
            messages = data.get('messages', [])
            text = '\n\n'.join([
                f"User: {msg.get('user', 'Unknown')}\n{msg.get('text', '')}"
                for msg in messages
            ])
            metadata.update({
                'title': f"Slack Channel: {data.get('channel', '')}",
                'channel': data.get('channel', ''),
                'message_count': len(messages),
            })
            
        elif source_type == 'jira':
            text = f"Issue: {data.get('key', '')} - {data.get('summary', '')}\n\n"
            text += f"Description:\n{data.get('description', '')}\n\n"
            
            # Add comments
            comments = data.get('comments', [])
            if comments:
                text += "Comments:\n"
                for comment in comments:
                    text += f"{comment.get('author', 'Unknown')}: {comment.get('body', '')}\n\n"
            
            metadata.update({
                'title': f"{data.get('key', '')}: {data.get('summary', '')}",
                'source_url': data.get('url', ''),
                'issue_key': data.get('key', ''),
                'status': data.get('status', ''),
                'issue_type': data.get('issue_type', ''),
            })
            
        elif source_type == 'github':
            text = f"Repository: {data.get('full_name', '')}\n\n"
            text += f"Description: {data.get('description', '')}\n\n"
            text += f"README:\n{data.get('readme', '')}\n\n"
            
            # Add issues
            issues = data.get('issues', [])
            if issues:
                text += "Recent Issues:\n"
                for issue in issues[:10]:  # Limit to 10 issues
                    text += f"#{issue.get('number', '')}: {issue.get('title', '')}\n"
                    text += f"{issue.get('body', '')}\n\n"
            
            # Add pull requests
            prs = data.get('pull_requests', [])
            if prs:
                text += "Recent Pull Requests:\n"
                for pr in prs[:10]:  # Limit to 10 PRs
                    text += f"#{pr.get('number', '')}: {pr.get('title', '')}\n"
                    text += f"{pr.get('body', '')}\n\n"
            
            metadata.update({
                'title': data.get('full_name', ''),
                'source_url': data.get('url', ''),
                'repository': data.get('full_name', ''),
                'language': data.get('language', ''),
            })
        
        return text, metadata
        
    except Exception as e:
        print(f"Error loading document from S3: {e}")
        raise


def create_embeddings(texts):
    """
    Create embeddings using Amazon Bedrock Titan
    
    Args:
        texts: List of text strings
    
    Returns:
        List of embedding vectors
    """
    try:
        # Initialize Bedrock embeddings
        embeddings = BedrockEmbeddings(
            client=bedrock_runtime,
            model_id="amazon.titan-embed-text-v1"
        )
        
        # Create embeddings
        vectors = embeddings.embed_documents(texts)
        
        print(f"Created {len(vectors)} embeddings")
        return vectors
        
    except Exception as e:
        print(f"Error creating embeddings: {e}")
        raise


def store_in_opensearch(os_client, chunks_with_embeddings, document_id, metadata):
    """
    Store document chunks and embeddings in OpenSearch
    
    Args:
        os_client: OpenSearch client instance
        chunks_with_embeddings: List of (chunk_text, embedding) tuples
        document_id: Document identifier
        metadata: Document metadata
    """
    try:
        for idx, (chunk_text, embedding) in enumerate(chunks_with_embeddings):
            chunk_id = f"{document_id}_chunk_{idx}"
            
            doc = {
                'embedding': embedding,
                'text': chunk_text,
                'document_id': document_id,
                'chunk_id': chunk_id,
                'chunk_index': idx,
                'source': metadata.get('source', ''),
                'source_url': metadata.get('source_url', ''),
                'title': metadata.get('title', ''),
                'metadata': metadata,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            os_client.index(
                index=OPENSEARCH_INDEX,
                id=chunk_id,
                body=doc,
                refresh=True
            )
        
        print(f"Stored {len(chunks_with_embeddings)} chunks in OpenSearch")
        
    except Exception as e:
        print(f"Error storing in OpenSearch: {e}")
        raise


def store_metadata_in_dynamodb(document_id, chunks_count, metadata):
    """
    Store document metadata in DynamoDB
    
    Args:
        document_id: Document identifier
        chunks_count: Number of chunks created
        metadata: Document metadata
    """
    try:
        for idx in range(chunks_count):
            chunk_id = f"{document_id}_chunk_{idx}"
            
            item = {
                'document_id': document_id,
                'chunk_id': chunk_id,
                'chunk_index': idx,
                'total_chunks': chunks_count,
                'source': metadata.get('source', ''),
                'source_url': metadata.get('source_url', ''),
                'title': metadata.get('title', ''),
                's3_bucket': metadata.get('s3_bucket', ''),
                's3_key': metadata.get('s3_key', ''),
                'processed_at': datetime.utcnow().isoformat(),
                'metadata': json.dumps(metadata)
            }
            
            metadata_table.put_item(Item=item)
        
        print(f"Stored metadata for {chunks_count} chunks in DynamoDB")
        
    except Exception as e:
        print(f"Error storing metadata in DynamoDB: {e}")
        raise


def lambda_handler(event, context):
    """
    Lambda handler for processing S3 events
    
    Args:
        event: S3 event notification
        context: Lambda context
    
    Returns:
        Response dictionary
    """
    print("Starting document processing...")
    
    try:
        # Parse S3 event
        for record in event['Records']:
            bucket = record['s3']['bucket']['name']
            key = unquote_plus(record['s3']['object']['key'])
            
            print(f"Processing: s3://{bucket}/{key}")
            
            # Generate document ID
            document_id = hashlib.md5(f"{bucket}/{key}".encode()).hexdigest()
            
            # Load document from S3
            text, metadata = load_document_from_s3(bucket, key)
            
            if not text or len(text.strip()) < 10:
                print("Document text is empty or too short, skipping")
                continue
            
            # Split document into chunks
            langchain_doc = LangChainDocument(page_content=text, metadata=metadata)
            chunks = text_splitter.split_documents([langchain_doc])
            
            chunk_texts = [chunk.page_content for chunk in chunks]
            print(f"Split document into {len(chunk_texts)} chunks")
            
            # Create embeddings
            embeddings = create_embeddings(chunk_texts)
            
            # Combine chunks with embeddings
            chunks_with_embeddings = list(zip(chunk_texts, embeddings))
            
            # Initialize OpenSearch client
            os_client = get_opensearch_client()
            
            # Create index if needed
            create_index_if_not_exists(os_client)
            
            # Store in OpenSearch
            store_in_opensearch(os_client, chunks_with_embeddings, document_id, metadata)
            
            # Store metadata in DynamoDB
            store_metadata_in_dynamodb(document_id, len(chunks), metadata)
            
            print(f"Successfully processed document: {document_id}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Successfully processed documents',
                'timestamp': datetime.utcnow().isoformat()
            })
        }
        
    except Exception as e:
        print(f"Error processing document: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'message': 'Failed to process document'
            })
        }