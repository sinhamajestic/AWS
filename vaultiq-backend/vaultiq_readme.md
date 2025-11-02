# VaultIQ Backend - Complete Implementation Guide

## Overview

VaultIQ is an AI-Powered Unified Knowledge Hub for IT Management that uses Retrieval-Augmented Generation (RAG) to provide intelligent answers from multiple data sources including Confluence, Slack, Jira, and GitHub.

## Architecture

### Technology Stack
- **Infrastructure**: AWS CDK v2 (TypeScript)
- **Backend**: Python 3.11, FastAPI
- **AI/ML**: AWS Bedrock (Claude 3 Haiku, Amazon Titan Embeddings)
- **Vector Database**: Amazon OpenSearch Serverless
- **Compute**: AWS Lambda
- **Storage**: Amazon S3 (Data Lake), DynamoDB (Metadata)
- **API**: Amazon API Gateway
- **Scheduling**: Amazon EventBridge
- **Secrets**: AWS Secrets Manager

### Data Flow
1. **Ingestion**: EventBridge triggers connector Lambdas every 15 minutes
2. **Storage**: Connectors fetch data and store raw JSON in S3 Data Lake
3. **Processing**: S3 events trigger processing Lambda to create embeddings
4. **Indexing**: Embeddings stored in OpenSearch, metadata in DynamoDB
5. **Query**: Users query via API Gateway → FastAPI Lambda → RAG pipeline

## Project Structure

```
/vaultiq-backend
│
├── /aws-cdk-infra              # Infrastructure as Code
│   ├── /bin
│   │   └── vaultiq-infra.ts    # CDK app entry point
│   ├── /lib
│   │   └── vaultiq-stack.ts    # Main stack definition
│   ├── package.json
│   ├── cdk.json
│   └── tsconfig.json
│
└── /src-lambda-code            # Python Application Code
    ├── /connectors             # Data source connectors
    │   ├── conflu_connector.py
    │   ├── slack_connector.py
    │   ├── jira_connector.py
    │   ├── github_connector.py
    │   └── requirements.txt
    │
    ├── /processing             # RAG ingestion pipeline
    │   ├── handler.py
    │   └── requirements.txt
    │
    └── /api                    # FastAPI query endpoint
        ├── main.py
        └── requirements.txt
```

## Prerequisites

### AWS Configuration
- AWS Account with appropriate permissions
- AWS CLI configured with credentials
- AWS CDK v2 installed globally: `npm install -g aws-cdk`

### Required Services Access
- AWS Bedrock access enabled in your region
- Model access granted for:
  - `anthropic.claude-3-haiku-20240307-v1:0`
  - `amazon.titan-embed-text-v1`

### Development Tools
- Node.js 18+ and npm
- Python 3.11
- TypeScript

## Installation & Deployment

### Step 1: Install CDK Dependencies

```bash
cd aws-cdk-infra
npm install
```

### Step 2: Configure AWS Credentials

```bash
aws configure
# OR
export AWS_PROFILE=your-profile
export AWS_REGION=us-east-1
```

### Step 3: Bootstrap CDK (First Time Only)

```bash
cdk bootstrap aws://ACCOUNT-ID/REGION
```

### Step 4: Install Python Dependencies

For each Lambda function directory:

```bash
# Connectors
cd ../src-lambda-code/connectors
pip install -r requirements.txt -t .

# Processing
cd ../processing
pip install -r requirements.txt -t .

# API
cd ../api
pip install -r requirements.txt -t .
```

### Step 5: Deploy Infrastructure

```bash
cd ../../aws-cdk-infra
cdk deploy
```

The deployment will output:
- Data Lake S3 bucket name
- DynamoDB table name
- OpenSearch endpoint
- API Gateway URL

### Step 6: Configure Secrets

After deployment, add your API credentials to Secrets Manager:

#### Confluence
```bash
aws secretsmanager update-secret \
  --secret-id vaultiq/confluence \
  --secret-string '{
    "url": "https://your-domain.atlassian.net",
    "username": "your-email@company.com",
    "api_key": "your-api-token"
  }'
```

#### Slack
```bash
aws secretsmanager update-secret \
  --secret-id vaultiq/slack \
  --secret-string '{
    "bot_token": "xoxb-your-bot-token"
  }'
```

#### Jira
```bash
aws secretsmanager update-secret \
  --secret-id vaultiq/jira \
  --secret-string '{
    "server": "https://your-domain.atlassian.net",
    "username": "your-email@company.com",
    "api_token": "your-api-token"
  }'
```

#### GitHub
```bash
aws secretsmanager update-secret \
  --secret-id vaultiq/github \
  --secret-string '{
    "token": "ghp_your-personal-access-token"
  }'
```

## API Usage

### Query Endpoint

**POST** `/api/query`

Request:
```json
{
  "query": "How do I deploy to production?",
  "top_k": 5,
  "source_filter": ["confluence", "github"]
}
```

Response:
```json
{
  "answer": "Based on the documentation...",
  "sources": [
    {
      "title": "Deployment Guide",
      "url": "https://...",
      "source_type": "confluence",
      "relevance_score": 0.92,
      "snippet": "To deploy to production..."
    }
  ],
  "query": "How do I deploy to production?",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### List Sources Endpoint

**GET** `/api/sources`

Response:
```json
{
  "sources": {
    "confluence": 150,
    "slack": 500,
    "jira": 200,
    "github": 100
  },
  "total_documents": 950,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Health Check

**GET** `/health`

Response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Testing

### Test Connector Lambdas

```bash
# Manually invoke a connector
aws lambda invoke \
  --function-name vaultiq-confluence-connector \
  --payload '{"space_key": "ENG", "limit": 10}' \
  response.json
```

### Test Processing Lambda

Upload a test file to S3:
```bash
aws s3 cp test-document.json s3://your-datalake-bucket/test/
```

The processing Lambda will automatically trigger.

### Test API

```bash
curl -X POST https://your-api-gateway-url/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the latest project status?"
  }'
```

## Monitoring & Troubleshooting

### CloudWatch Logs

Each Lambda function has its own log group:
- `/aws/lambda/vaultiq-confluence-connector`
- `/aws/lambda/vaultiq-slack-connector`
- `/aws/lambda/vaultiq-jira-connector`
- `/aws/lambda/vaultiq-github-connector`
- `/aws/lambda/vaultiq-processing`
- `/aws/lambda/vaultiq-api`

### Common Issues

#### 1. Bedrock Access Denied
- Ensure Bedrock is enabled in your region
- Grant model access in AWS Console → Bedrock → Model access

#### 2. OpenSearch Connection Failed
- Verify IAM roles have `aoss:APIAccessAll` permission
- Check data access policy includes Lambda role ARNs

#### 3. Connector Authentication Failed
- Verify secrets are correctly formatted in Secrets Manager
- Test API tokens independently

#### 4. No Search Results
- Wait for processing Lambda to complete
- Check OpenSearch index exists: `vaultiq-vectors`
- Verify embeddings were created

## Cost Optimization

### Estimated Monthly Costs (Low-Medium Usage)
- Lambda: $10-50
- S3: $5-20
- OpenSearch Serverless: $50-100
- DynamoDB: $5-10
- Bedrock API: $20-100 (depends on query volume)

### Optimization Tips
1. Adjust EventBridge schedule (currently 15 min)
2. Implement result caching for common queries
3. Use S3 lifecycle policies for old data
4. Monitor and adjust Lambda memory/timeout

## Security Best Practices

1. **Secrets Management**: Never hardcode credentials
2. **IAM Roles**: Use least-privilege access
3. **VPC**: Consider deploying Lambda in VPC for production
4. **Encryption**: Enable encryption at rest (already configured)
5. **API Authentication**: Add API Gateway authentication for production
6. **Network Policies**: Restrict OpenSearch access to Lambda roles only

## Maintenance

### Update Dependencies

```bash
# Update CDK
cd aws-cdk-infra
npm update

# Update Python packages
cd ../src-lambda-code/connectors
pip install -r requirements.txt --upgrade -t .
```

### Scale Considerations

- **Increase chunk size**: Modify `RecursiveCharacterTextSplitter` chunk_size
- **Add more sources**: Create new connector Lambdas
- **Improve retrieval**: Adjust OpenSearch k-NN parameters
- **Better answers**: Use Claude 3 Sonnet instead of Haiku

## Development Workflow

### Local Testing

1. Use AWS SAM for local Lambda testing
2. Mock Bedrock API for development
3. Use LocalStack for OpenSearch testing

### CI/CD Integration

```yaml
# Example GitHub Actions workflow
name: Deploy VaultIQ
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-node@v2
      - name: Deploy CDK
        run: |
          cd aws-cdk-infra
          npm install
          cdk deploy --require-approval never
```

## Support & Contributions

For issues, feature requests, or contributions, please refer to the project documentation.

## License

[Your License Here]

---

**Built with ❤️ using AWS CDK, Python, and AWS Bedrock**