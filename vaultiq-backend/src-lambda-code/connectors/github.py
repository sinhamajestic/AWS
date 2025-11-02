"""
GitHub Connector Lambda
Fetches repositories, issues, and pull requests from GitHub and stores them in S3 Data Lake
"""
import json
import os
import boto3
from datetime import datetime, timedelta
from github import Github
from botocore.exceptions import ClientError

# Initialize AWS clients
s3_client = boto3.client('s3')
secrets_client = boto3.client('secretsmanager')

# Environment variables
DATA_LAKE_BUCKET = os.environ['DATA_LAKE_BUCKET']
SECRET_NAME = os.environ['SECRET_NAME']


def get_github_credentials():
    """Retrieve GitHub credentials from Secrets Manager"""
    try:
        response = secrets_client.get_secret_value(SecretId=SECRET_NAME)
        secret = json.loads(response['SecretString'])
        return secret
    except ClientError as e:
        print(f"Error retrieving secret: {e}")
        raise


def fetch_repositories(github_client, org_name=None, user_name=None):
    """
    Fetch repositories from GitHub
    
    Args:
        github_client: Github client instance
        org_name: Organization name (optional)
        user_name: User name (optional)
    
    Returns:
        List of repository objects
    """
    try:
        repos = []
        
        if org_name:
            # Fetch organization repositories
            org = github_client.get_organization(org_name)
            repos = list(org.get_repos())
            print(f"Found {len(repos)} repositories in organization '{org_name}'")
        elif user_name:
            # Fetch user repositories
            user = github_client.get_user(user_name)
            repos = list(user.get_repos())
            print(f"Found {len(repos)} repositories for user '{user_name}'")
        else:
            # Fetch authenticated user's repositories
            user = github_client.get_user()
            repos = list(user.get_repos())
            print(f"Found {len(repos)} repositories for authenticated user")
        
        return repos
        
    except Exception as e:
        print(f"Error fetching repositories: {e}")
        raise


def fetch_repository_data(repo, days_back=30):
    """
    Fetch detailed data from a repository
    
    Args:
        repo: Repository object
        days_back: Number of days to look back for issues/PRs
    
    Returns:
        Dictionary with repository data
    """
    try:
        since_date = datetime.utcnow() - timedelta(days=days_back)
        
        repo_data = {
            'id': repo.id,
            'name': repo.name,
            'full_name': repo.full_name,
            'url': repo.html_url,
            'description': repo.description or '',
            'language': repo.language,
            'default_branch': repo.default_branch,
            'created_at': repo.created_at.isoformat(),
            'updated_at': repo.updated_at.isoformat(),
            'stars': repo.stargazers_count,
            'forks': repo.forks_count,
            'open_issues': repo.open_issues_count,
            'topics': repo.get_topics(),
        }
        
        # Fetch README
        try:
            readme = repo.get_readme()
            repo_data['readme'] = readme.decoded_content.decode('utf-8')
        except:
            repo_data['readme'] = ''
        
        # Fetch recent issues
        issues_data = []
        try:
            issues = repo.get_issues(state='all', since=since_date)
            for issue in issues[:50]:  # Limit to 50 most recent
                if issue.pull_request:  # Skip pull requests in issues
                    continue
                
                issue_data = {
                    'number': issue.number,
                    'title': issue.title,
                    'body': issue.body or '',
                    'state': issue.state,
                    'url': issue.html_url,
                    'created_at': issue.created_at.isoformat(),
                    'updated_at': issue.updated_at.isoformat(),
                    'user': issue.user.login,
                    'labels': [label.name for label in issue.labels],
                    'comments_count': issue.comments,
                }
                
                # Fetch comments
                try:
                    comments = issue.get_comments()
                    issue_data['comments'] = [
                        {
                            'user': comment.user.login,
                            'body': comment.body,
                            'created_at': comment.created_at.isoformat(),
                        }
                        for comment in comments
                    ]
                except:
                    issue_data['comments'] = []
                
                issues_data.append(issue_data)
        except Exception as e:
            print(f"Error fetching issues for {repo.name}: {e}")
        
        repo_data['issues'] = issues_data
        
        # Fetch recent pull requests
        prs_data = []
        try:
            pulls = repo.get_pulls(state='all', sort='updated', direction='desc')
            for pr in pulls[:50]:  # Limit to 50 most recent
                if pr.updated_at < since_date:
                    break
                
                pr_data = {
                    'number': pr.number,
                    'title': pr.title,
                    'body': pr.body or '',
                    'state': pr.state,
                    'url': pr.html_url,
                    'created_at': pr.created_at.isoformat(),
                    'updated_at': pr.updated_at.isoformat(),
                    'merged': pr.merged,
                    'user': pr.user.login,
                    'base_branch': pr.base.ref,
                    'head_branch': pr.head.ref,
                    'comments_count': pr.comments,
                    'commits_count': pr.commits,
                    'changed_files': pr.changed_files,
                    'additions': pr.additions,
                    'deletions': pr.deletions,
                }
                
                # Fetch review comments
                try:
                    comments = pr.get_comments()
                    pr_data['comments'] = [
                        {
                            'user': comment.user.login,
                            'body': comment.body,
                            'created_at': comment.created_at.isoformat(),
                        }
                        for comment in comments[:20]  # Limit comments
                    ]
                except:
                    pr_data['comments'] = []
                
                prs_data.append(pr_data)
        except Exception as e:
            print(f"Error fetching pull requests for {repo.name}: {e}")
        
        repo_data['pull_requests'] = prs_data
        
        print(f"Fetched data for repository {repo.name}: {len(issues_data)} issues, {len(prs_data)} PRs")
        return repo_data
        
    except Exception as e:
        print(f"Error fetching data for repository {repo.name}: {e}")
        raise


def save_to_s3(repositories_data):
    """
    Save GitHub repository data to S3 Data Lake
    
    Args:
        repositories_data: List of repository data dictionaries
    """
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    
    for repo_data in repositories_data:
        try:
            # Create S3 key with hierarchical structure
            s3_key = f"github/{repo_data['full_name']}/{timestamp}.json"
            
            # Prepare repo data
            repo_json = json.dumps(repo_data, indent=2, ensure_ascii=False)
            
            # Upload to S3
            s3_client.put_object(
                Bucket=DATA_LAKE_BUCKET,
                Key=s3_key,
                Body=repo_json.encode('utf-8'),
                ContentType='application/json',
                Metadata={
                    'source': 'github',
                    'repository': repo_data['full_name'],
                    'language': repo_data['language'] or 'none',
                }
            )
            
            print(f"Saved repository {repo_data['full_name']} to s3://{DATA_LAKE_BUCKET}/{s3_key}")
            
        except Exception as e:
            print(f"Error saving repository {repo_data['full_name']} to S3: {e}")
            continue


def lambda_handler(event, context):
    """
    Lambda handler for GitHub connector
    
    Args:
        event: EventBridge scheduled event
        context: Lambda context
    
    Returns:
        Response dictionary
    """
    print("Starting GitHub connector...")
    
    try:
        # Get credentials
        credentials = get_github_credentials()
        
        # Initialize GitHub client
        github_client = Github(credentials['token'])
        
        # Test connection
        user = github_client.get_user()
        print(f"Successfully authenticated as {user.login}")
        
        # Get parameters from event
        org_name = event.get('org_name') if event else None
        user_name = event.get('user_name') if event else None
        days_back = event.get('days_back', 30) if event else 30
        max_repos = event.get('max_repos', 10) if event else 10
        
        # Fetch repositories
        repos = fetch_repositories(github_client, org_name=org_name, user_name=user_name)
        
        if not repos:
            print("No repositories found")
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'No repositories found',
                    'repositories_fetched': 0
                })
            }
        
        # Limit number of repositories to process
        repos = repos[:max_repos]
        
        # Fetch detailed data for each repository
        repositories_data = []
        for repo in repos:
            try:
                repo_data = fetch_repository_data(repo, days_back=days_back)
                repositories_data.append(repo_data)
            except Exception as e:
                print(f"Error processing repository {repo.name}: {e}")
                continue
        
        if not repositories_data:
            print("No repository data collected")
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'No repository data collected',
                    'repositories_fetched': 0
                })
            }
        
        # Save to S3
        save_to_s3(repositories_data)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Successfully fetched and saved GitHub data',
                'repositories_fetched': len(repositories_data),
                'timestamp': datetime.utcnow().isoformat()
            })
        }
        
    except Exception as e:
        print(f"Error in GitHub connector: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'message': 'Failed to fetch GitHub data'
            })
        }