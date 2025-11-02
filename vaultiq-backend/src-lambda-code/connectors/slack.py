"""
Slack Connector Lambda
Fetches messages from Slack channels and stores them in S3 Data Lake
"""
import json
import os
import boto3
from datetime import datetime, timedelta
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from botocore.exceptions import ClientError

# Initialize AWS clients
s3_client = boto3.client('s3')
secrets_client = boto3.client('secretsmanager')

# Environment variables
DATA_LAKE_BUCKET = os.environ['DATA_LAKE_BUCKET']
SECRET_NAME = os.environ['SECRET_NAME']


def get_slack_credentials():
    """Retrieve Slack credentials from Secrets Manager"""
    try:
        response = secrets_client.get_secret_value(SecretId=SECRET_NAME)
        secret = json.loads(response['SecretString'])
        return secret
    except ClientError as e:
        print(f"Error retrieving secret: {e}")
        raise


def fetch_slack_channels(client):
    """
    Fetch list of public channels
    
    Args:
        client: Slack WebClient instance
    
    Returns:
        List of channel dictionaries
    """
    try:
        channels = []
        cursor = None
        
        while True:
            response = client.conversations_list(
                types='public_channel',
                cursor=cursor,
                limit=100
            )
            
            channels.extend(response['channels'])
            
            cursor = response.get('response_metadata', {}).get('next_cursor')
            if not cursor:
                break
        
        print(f"Found {len(channels)} public channels")
        return channels
        
    except SlackApiError as e:
        print(f"Error fetching channels: {e}")
        raise


def fetch_channel_messages(client, channel_id, channel_name, days_back=7):
    """
    Fetch messages from a Slack channel
    
    Args:
        client: Slack WebClient instance
        channel_id: Channel ID
        channel_name: Channel name
        days_back: Number of days to look back for messages
    
    Returns:
        List of message dictionaries
    """
    try:
        # Calculate timestamp for messages (last N days)
        oldest_timestamp = (datetime.utcnow() - timedelta(days=days_back)).timestamp()
        
        messages = []
        cursor = None
        
        while True:
            response = client.conversations_history(
                channel=channel_id,
                oldest=str(oldest_timestamp),
                cursor=cursor,
                limit=100
            )
            
            for msg in response['messages']:
                # Skip messages without text or from bots (optional)
                if 'text' not in msg or not msg['text'].strip():
                    continue
                
                # Get user info if available
                user_name = 'Unknown'
                if 'user' in msg:
                    try:
                        user_info = client.users_info(user=msg['user'])
                        user_name = user_info['user']['real_name'] or user_info['user']['name']
                    except:
                        user_name = msg['user']
                
                message_data = {
                    'channel_id': channel_id,
                    'channel_name': channel_name,
                    'message_id': msg['ts'],
                    'text': msg['text'],
                    'user': user_name,
                    'timestamp': msg['ts'],
                    'datetime': datetime.fromtimestamp(float(msg['ts'])).isoformat(),
                    'thread_ts': msg.get('thread_ts'),
                    'reply_count': msg.get('reply_count', 0),
                    'reactions': msg.get('reactions', []),
                }
                
                # Fetch thread replies if this is a parent message
                if msg.get('reply_count', 0) > 0:
                    try:
                        thread_response = client.conversations_replies(
                            channel=channel_id,
                            ts=msg['ts']
                        )
                        message_data['replies'] = [
                            {
                                'text': reply['text'],
                                'user': reply.get('user', 'Unknown'),
                                'timestamp': reply['ts']
                            }
                            for reply in thread_response['messages'][1:]  # Skip parent
                        ]
                    except:
                        pass
                
                messages.append(message_data)
            
            cursor = response.get('response_metadata', {}).get('next_cursor')
            if not cursor:
                break
        
        print(f"Fetched {len(messages)} messages from #{channel_name}")
        return messages
        
    except SlackApiError as e:
        print(f"Error fetching messages from #{channel_name}: {e}")
        return []


def save_to_s3(channel_messages):
    """
    Save Slack messages to S3 Data Lake
    
    Args:
        channel_messages: Dictionary mapping channel names to message lists
    """
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    
    for channel_name, messages in channel_messages.items():
        if not messages:
            continue
        
        try:
            # Create S3 key with hierarchical structure
            s3_key = f"slack/{channel_name}/{timestamp}.json"
            
            # Prepare channel data
            channel_data = {
                'channel': channel_name,
                'fetch_timestamp': timestamp,
                'message_count': len(messages),
                'messages': messages
            }
            
            channel_json = json.dumps(channel_data, indent=2, ensure_ascii=False)
            
            # Upload to S3
            s3_client.put_object(
                Bucket=DATA_LAKE_BUCKET,
                Key=s3_key,
                Body=channel_json.encode('utf-8'),
                ContentType='application/json',
                Metadata={
                    'source': 'slack',
                    'channel': channel_name,
                    'message_count': str(len(messages)),
                }
            )
            
            print(f"Saved {len(messages)} messages from #{channel_name} to s3://{DATA_LAKE_BUCKET}/{s3_key}")
            
        except Exception as e:
            print(f"Error saving messages from #{channel_name} to S3: {e}")
            continue


def lambda_handler(event, context):
    """
    Lambda handler for Slack connector
    
    Args:
        event: EventBridge scheduled event
        context: Lambda context
    
    Returns:
        Response dictionary
    """
    print("Starting Slack connector...")
    
    try:
        # Get credentials
        credentials = get_slack_credentials()
        
        # Initialize Slack client
        client = WebClient(token=credentials['bot_token'])
        
        # Test connection
        auth_response = client.auth_test()
        print(f"Successfully authenticated as {auth_response['user']}")
        
        # Get channels to monitor (from event or fetch all)
        channel_filter = event.get('channels', []) if event else []
        days_back = event.get('days_back', 7) if event else 7
        
        # Fetch channels
        all_channels = fetch_slack_channels(client)
        
        # Filter channels if specified
        if channel_filter:
            channels = [ch for ch in all_channels if ch['name'] in channel_filter]
        else:
            channels = all_channels[:10]  # Limit to first 10 channels by default
        
        print(f"Processing {len(channels)} channels")
        
        # Fetch messages from each channel
        channel_messages = {}
        total_messages = 0
        
        for channel in channels:
            messages = fetch_channel_messages(
                client,
                channel['id'],
                channel['name'],
                days_back=days_back
            )
            
            if messages:
                channel_messages[channel['name']] = messages
                total_messages += len(messages)
        
        if total_messages == 0:
            print("No messages found")
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'No messages found',
                    'channels_processed': len(channels),
                    'messages_fetched': 0
                })
            }
        
        # Save to S3
        save_to_s3(channel_messages)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Successfully fetched and saved Slack messages',
                'channels_processed': len(channels),
                'messages_fetched': total_messages,
                'timestamp': datetime.utcnow().isoformat()
            })
        }
        
    except Exception as e:
        print(f"Error in Slack connector: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'message': 'Failed to fetch Slack messages'
            })
        }