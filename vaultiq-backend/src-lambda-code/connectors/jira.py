"""
Jira Connector Lambda
Fetches issues and comments from Jira and stores them in S3 Data Lake
"""
import json
import os
import boto3
from datetime import datetime, timedelta
from jira import JIRA
from botocore.exceptions import ClientError

# Initialize AWS clients
s3_client = boto3.client('s3')
secrets_client = boto3.client('secretsmanager')

# Environment variables
DATA_LAKE_BUCKET = os.environ['DATA_LAKE_BUCKET']
SECRET_NAME = os.environ['SECRET_NAME']


def get_jira_credentials():
    """Retrieve Jira credentials from Secrets Manager"""
    try:
        response = secrets_client.get_secret_value(SecretId=SECRET_NAME)
        secret = json.loads(response['SecretString'])
        return secret
    except ClientError as e:
        print(f"Error retrieving secret: {e}")
        raise


def fetch_jira_issues(jira_client, jql_query=None, max_results=100):
    """
    Fetch issues from Jira using JQL query
    
    Args:
        jira_client: JIRA client instance
        jql_query: JQL query string (optional)
        max_results: Maximum number of issues to fetch
    
    Returns:
        List of issue dictionaries
    """
    try:
        # Default query: recently updated issues
        if not jql_query:
            # Get issues updated in last 30 days
            date_30_days_ago = (datetime.utcnow() - timedelta(days=30)).strftime('%Y-%m-%d')
            jql_query = f'updated >= {date_30_days_ago} ORDER BY updated DESC'
        
        print(f"Executing JQL query: {jql_query}")
        
        issues = []
        start_at = 0
        
        while len(issues) < max_results:
            # Fetch issues in batches
            batch = jira_client.search_issues(
                jql_query,
                startAt=start_at,
                maxResults=min(50, max_results - len(issues)),
                fields='*all'
            )
            
            if not batch:
                break
            
            for issue in batch:
                # Extract issue data
                issue_data = {
                    'id': issue.id,
                    'key': issue.key,
                    'url': f"{jira_client.server_url}/browse/{issue.key}",
                    'summary': issue.fields.summary,
                    'description': issue.fields.description or '',
                    'status': issue.fields.status.name,
                    'priority': issue.fields.priority.name if issue.fields.priority else 'None',
                    'issue_type': issue.fields.issuetype.name,
                    'project': {
                        'key': issue.fields.project.key,
                        'name': issue.fields.project.name
                    },
                    'created': issue.fields.created,
                    'updated': issue.fields.updated,
                    'reporter': issue.fields.reporter.displayName if issue.fields.reporter else 'Unknown',
                    'assignee': issue.fields.assignee.displayName if issue.fields.assignee else 'Unassigned',
                    'labels': issue.fields.labels,
                    'components': [comp.name for comp in issue.fields.components],
                }
                
                # Fetch comments
                try:
                    comments = jira_client.comments(issue.key)
                    issue_data['comments'] = [
                        {
                            'id': comment.id,
                            'author': comment.author.displayName,
                            'body': comment.body,
                            'created': comment.created,
                        }
                        for comment in comments
                    ]
                except Exception as e:
                    print(f"Error fetching comments for {issue.key}: {e}")
                    issue_data['comments'] = []
                
                # Fetch attachments metadata (not downloading files)
                try:
                    if hasattr(issue.fields, 'attachment') and issue.fields.attachment:
                        issue_data['attachments'] = [
                            {
                                'id': attach.id,
                                'filename': attach.filename,
                                'size': attach.size,
                                'created': attach.created,
                                'author': attach.author.displayName if attach.author else 'Unknown',
                            }
                            for attach in issue.fields.attachment
                        ]
                    else:
                        issue_data['attachments'] = []
                except Exception as e:
                    print(f"Error fetching attachments for {issue.key}: {e}")
                    issue_data['attachments'] = []
                
                issues.append(issue_data)
            
            start_at += len(batch)
            
            # Break if we've fetched all available issues
            if len(batch) < 50:
                break
        
        print(f"Fetched {len(issues)} issues from Jira")
        return issues
        
    except Exception as e:
        print(f"Error fetching Jira issues: {e}")
        raise


def save_to_s3(issues):
    """
    Save Jira issues to S3 Data Lake
    
    Args:
        issues: List of issue dictionaries
    """
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    
    for issue in issues:
        try:
            # Create S3 key with hierarchical structure
            s3_key = f"jira/{issue['project']['key']}/{issue['key']}_{timestamp}.json"
            
            # Prepare issue data
            issue_json = json.dumps(issue, indent=2, ensure_ascii=False)
            
            # Upload to S3
            s3_client.put_object(
                Bucket=DATA_LAKE_BUCKET,
                Key=s3_key,
                Body=issue_json.encode('utf-8'),
                ContentType='application/json',
                Metadata={
                    'source': 'jira',
                    'issue_key': issue['key'],
                    'project_key': issue['project']['key'],
                    'status': issue['status'],
                    'issue_type': issue['issue_type'],
                }
            )
            
            print(f"Saved issue {issue['key']} to s3://{DATA_LAKE_BUCKET}/{s3_key}")
            
        except Exception as e:
            print(f"Error saving issue {issue['key']} to S3: {e}")
            continue


def lambda_handler(event, context):
    """
    Lambda handler for Jira connector
    
    Args:
        event: EventBridge scheduled event
        context: Lambda context
    
    Returns:
        Response dictionary
    """
    print("Starting Jira connector...")
    
    try:
        # Get credentials
        credentials = get_jira_credentials()
        
        # Initialize Jira client
        jira_client = JIRA(
            server=credentials['server'],
            basic_auth=(credentials['username'], credentials['api_token'])
        )
        
        # Test connection
        server_info = jira_client.server_info()
        print(f"Successfully connected to Jira: {server_info['serverTitle']}")
        
        # Get JQL query from event or use default
        jql_query = event.get('jql_query') if event else None
        max_results = event.get('max_results', 100) if event else 100
        
        # Fetch issues
        issues = fetch_jira_issues(jira_client, jql_query=jql_query, max_results=max_results)
        
        if not issues:
            print("No issues found")
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'No issues found',
                    'issues_fetched': 0
                })
            }
        
        # Save to S3
        save_to_s3(issues)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Successfully fetched and saved Jira issues',
                'issues_fetched': len(issues),
                'timestamp': datetime.utcnow().isoformat()
            })
        }
        
    except Exception as e:
        print(f"Error in Jira connector: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'message': 'Failed to fetch Jira issues'
            })
        }