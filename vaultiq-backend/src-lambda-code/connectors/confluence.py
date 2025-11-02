"""
Confluence Connector Lambda
Fetches pages from Confluence and stores them in S3 Data Lake
"""
import json
import os
import boto3
from datetime import datetime
from atlassian import Confluence
from botocore.exceptions import ClientError

# Initialize AWS clients
s3_client = boto3.client('s3')
secrets_client = boto3.client('secretsmanager')

# Environment variables
DATA_LAKE_BUCKET = os.environ['DATA_LAKE_BUCKET']
SECRET_NAME = os.environ['SECRET_NAME']


def get_confluence_credentials():
    """Retrieve Confluence credentials from Secrets Manager"""
    try:
        response = secrets_client.get_secret_value(SecretId=SECRET_NAME)
        secret = json.loads(response['SecretString'])
        return secret
    except ClientError as e:
        print(f"Error retrieving secret: {e}")
        raise


def fetch_confluence_pages(confluence, space_key=None, limit=100):
    """
    Fetch pages from Confluence
    
    Args:
        confluence: Confluence client instance
        space_key: Optional space key to filter pages
        limit: Maximum number of pages to fetch
    
    Returns:
        List of page dictionaries
    """
    pages = []
    
    try:
        if space_key:
            # Fetch pages from specific space
            cql = f'type=page AND space="{space_key}"'
            results = confluence.cql(cql, limit=limit)
        else:
            # Fetch all accessible pages
            results = confluence.cql('type=page', limit=limit)
        
        if 'results' in results:
            for page in results['results']:
                page_id = page['content']['id']
                
                # Get full page content
                full_page = confluence.get_page_by_id(
                    page_id=page_id,
                    expand='body.storage,version,space,metadata.labels'
                )
                
                page_data = {
                    'id': full_page['id'],
                    'title': full_page['title'],
                    'space': full_page['space']['name'],
                    'space_key': full_page['space']['key'],
                    'url': confluence.url + full_page['_links']['webui'],
                    'content': full_page['body']['storage']['value'],
                    'version': full_page['version']['number'],
                    'created_date': full_page['version']['when'],
                    'modified_by': full_page['version'].get('by', {}).get('displayName', 'Unknown'),
                    'labels': [label['name'] for label in full_page.get('metadata', {}).get('labels', {}).get('results', [])],
                }
                
                pages.append(page_data)
                
        print(f"Fetched {len(pages)} pages from Confluence")
        return pages
        
    except Exception as e:
        print(f"Error fetching Confluence pages: {e}")
        raise


def save_to_s3(pages):
    """
    Save Confluence pages to S3 Data Lake
    
    Args:
        pages: List of page dictionaries
    """
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    
    for page in pages:
        try:
            # Create S3 key with hierarchical structure
            s3_key = f"confluence/{page['space_key']}/{page['id']}_{timestamp}.json"
            
            # Prepare page data
            page_json = json.dumps(page, indent=2, ensure_ascii=False)
            
            # Upload to S3
            s3_client.put_object(
                Bucket=DATA_LAKE_BUCKET,
                Key=s3_key,
                Body=page_json.encode('utf-8'),
                ContentType='application/json',
                Metadata={
                    'source': 'confluence',
                    'page_id': page['id'],
                    'space_key': page['space_key'],
                    'title': page['title'][:1024],  # S3 metadata has size limits
                }
            )
            
            print(f"Saved page '{page['title']}' to s3://{DATA_LAKE_BUCKET}/{s3_key}")
            
        except Exception as e:
            print(f"Error saving page {page['id']} to S3: {e}")
            # Continue with next page
            continue


def lambda_handler(event, context):
    """
    Lambda handler for Confluence connector
    
    Args:
        event: EventBridge scheduled event
        context: Lambda context
    
    Returns:
        Response dictionary
    """
    print("Starting Confluence connector...")
    
    try:
        # Get credentials
        credentials = get_confluence_credentials()
        
        # Initialize Confluence client
        confluence = Confluence(
            url=credentials['url'],
            username=credentials['username'],
            password=credentials['api_key']
        )
        
        # Test connection
        if not confluence.user():
            raise Exception("Failed to authenticate with Confluence")
        
        print("Successfully authenticated with Confluence")
        
        # Fetch pages (can be filtered by space_key if provided in event)
        space_key = event.get('space_key') if event else None
        limit = event.get('limit', 100) if event else 100
        
        pages = fetch_confluence_pages(confluence, space_key=space_key, limit=limit)
        
        if not pages:
            print("No pages found")
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'No pages found',
                    'pages_fetched': 0
                })
            }
        
        # Save to S3
        save_to_s3(pages)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Successfully fetched and saved Confluence pages',
                'pages_fetched': len(pages),
                'timestamp': datetime.utcnow().isoformat()
            })
        }
        
    except Exception as e:
        print(f"Error in Confluence connector: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'message': 'Failed to fetch Confluence pages'
            })
        }