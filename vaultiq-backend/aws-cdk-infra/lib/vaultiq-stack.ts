import * as cdk from 'aws-cdk-lib';
import * as iam from 'aws-cdk-lib/aws-iam';
import { Construct } from 'constructs';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as events from 'aws-cdk-lib/aws-events';
import * as targets from 'aws-cdk-lib/aws-events-targets';
import * as s3n from 'aws-cdk-lib/aws-s3-notifications';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import * as opensearchserverless from 'aws-cdk-lib/aws-opensearchserverless';

export class VaultiqStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // ========================================
    // S3 Data Lake Bucket
    // ========================================
    const dataLakeBucket = new s3.Bucket(this, 'VaultIQDataLake', {
      bucketName: `vaultiq-datalake-${this.account}`,
      versioned: true,
      encryption: s3.BucketEncryption.S3_MANAGED,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      removalPolicy: cdk.RemovalPolicy.RETAIN,
    });

    // ========================================
    // DynamoDB Metadata Table
    // ========================================
    const metadataTable = new dynamodb.Table(this, 'VaultIQMetadata', {
      tableName: 'vaultiq-metadata',
      partitionKey: { name: 'document_id', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'chunk_id', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: cdk.RemovalPolicy.RETAIN,
      pointInTimeRecovery: true,
    });

    // ========================================
    // Secrets Manager - Placeholder Secrets
    // ========================================
    const confluenceSecret = new secretsmanager.Secret(this, 'ConfluenceSecret', {
      secretName: 'vaultiq/confluence',
      description: 'Confluence API credentials',
      generateSecretString: {
        secretStringTemplate: JSON.stringify({ url: '', username: '' }),
        generateStringKey: 'api_key',
      },
    });

    const slackSecret = new secretsmanager.Secret(this, 'SlackSecret', {
      secretName: 'vaultiq/slack',
      description: 'Slack Bot Token',
      generateSecretString: {
        secretStringTemplate: JSON.stringify({}),
        generateStringKey: 'bot_token',
      },
    });

    const jiraSecret = new secretsmanager.Secret(this, 'JiraSecret', {
      secretName: 'vaultiq/jira',
      description: 'Jira API credentials',
      generateSecretString: {
        secretStringTemplate: JSON.stringify({ server: '', username: '' }),
        generateStringKey: 'api_token',
      },
    });

    const githubSecret = new secretsmanager.Secret(this, 'GitHubSecret', {
      secretName: 'vaultiq/github',
      description: 'GitHub Personal Access Token',
      generateSecretString: {
        secretStringTemplate: JSON.stringify({}),
        generateStringKey: 'token',
      },
    });

    // ========================================
    // OpenSearch Serverless Collection
    // ========================================
    const opensearchCollection = new opensearchserverless.CfnCollection(this, 'VaultIQVectorCollection', {
      name: 'vaultiq-vectors',
      type: 'VECTORSEARCH',
      description: 'Vector search collection for VaultIQ embeddings',
    });

    // OpenSearch Serverless Encryption Policy
    const encryptionPolicy = new opensearchserverless.CfnSecurityPolicy(this, 'VaultIQEncryptionPolicy', {
      name: 'vaultiq-encryption-policy',
      type: 'encryption',
      policy: JSON.stringify({
        Rules: [
          {
            ResourceType: 'collection',
            Resource: [`collection/${opensearchCollection.name}`],
          },
        ],
        AWSOwnedKey: true,
      }),
    });

    // OpenSearch Serverless Network Policy
    const networkPolicy = new opensearchserverless.CfnSecurityPolicy(this, 'VaultIQNetworkPolicy', {
      name: 'vaultiq-network-policy',
      type: 'network',
      policy: JSON.stringify([
        {
          Rules: [
            {
              ResourceType: 'collection',
              Resource: [`collection/${opensearchCollection.name}`],
            },
          ],
          AllowFromPublic: true,
        },
      ]),
    });

    opensearchCollection.addDependency(encryptionPolicy);
    opensearchCollection.addDependency(networkPolicy);

    // ========================================
    // IAM Roles for Lambda Functions
    // ========================================
    
    // Connector Lambda Role
    const connectorRole = new iam.Role(this, 'ConnectorLambdaRole', {
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'),
      ],
    });

    dataLakeBucket.grantWrite(connectorRole);
    confluenceSecret.grantRead(connectorRole);
    slackSecret.grantRead(connectorRole);
    jiraSecret.grantRead(connectorRole);
    githubSecret.grantRead(connectorRole);

    // Processing Lambda Role
    const processingRole = new iam.Role(this, 'ProcessingLambdaRole', {
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'),
      ],
    });

    dataLakeBucket.grantRead(processingRole);
    metadataTable.grantWriteData(processingRole);
    
    processingRole.addToPolicy(new iam.PolicyStatement({
      actions: ['bedrock:InvokeModel'],
      resources: ['*'],
    }));

    processingRole.addToPolicy(new iam.PolicyStatement({
      actions: ['aoss:APIAccessAll'],
      resources: [opensearchCollection.attrArn],
    }));

    // API Lambda Role
    const apiRole = new iam.Role(this, 'ApiLambdaRole', {
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'),
      ],
    });

    metadataTable.grantReadData(apiRole);
    
    apiRole.addToPolicy(new iam.PolicyStatement({
      actions: ['bedrock:InvokeModel'],
      resources: ['*'],
    }));

    apiRole.addToPolicy(new iam.PolicyStatement({
      actions: ['aoss:APIAccessAll'],
      resources: [opensearchCollection.attrArn],
    }));

    // ========================================
    // Lambda Functions - Connectors
    // ========================================
    const confluenceConnector = new lambda.Function(this, 'ConfluenceConnectorLambda', {
      functionName: 'vaultiq-confluence-connector',
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'conflu_connector.lambda_handler',
      code: lambda.Code.fromAsset('../src-lambda-code/connectors'),
      timeout: cdk.Duration.minutes(5),
      memorySize: 512,
      role: connectorRole,
      environment: {
        DATA_LAKE_BUCKET: dataLakeBucket.bucketName,
        SECRET_NAME: confluenceSecret.secretName,
      },
    });

    const slackConnector = new lambda.Function(this, 'SlackConnectorLambda', {
      functionName: 'vaultiq-slack-connector',
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'slack_connector.lambda_handler',
      code: lambda.Code.fromAsset('../src-lambda-code/connectors'),
      timeout: cdk.Duration.minutes(5),
      memorySize: 512,
      role: connectorRole,
      environment: {
        DATA_LAKE_BUCKET: dataLakeBucket.bucketName,
        SECRET_NAME: slackSecret.secretName,
      },
    });

    const jiraConnector = new lambda.Function(this, 'JiraConnectorLambda', {
      functionName: 'vaultiq-jira-connector',
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'jira_connector.lambda_handler',
      code: lambda.Code.fromAsset('../src-lambda-code/connectors'),
      timeout: cdk.Duration.minutes(5),
      memorySize: 512,
      role: connectorRole,
      environment: {
        DATA_LAKE_BUCKET: dataLakeBucket.bucketName,
        SECRET_NAME: jiraSecret.secretName,
      },
    });

    const githubConnector = new lambda.Function(this, 'GitHubConnectorLambda', {
      functionName: 'vaultiq-github-connector',
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'github_connector.lambda_handler',
      code: lambda.Code.fromAsset('../src-lambda-code/connectors'),
      timeout: cdk.Duration.minutes(5),
      memorySize: 512,
      role: connectorRole,
      environment: {
        DATA_LAKE_BUCKET: dataLakeBucket.bucketName,
        SECRET_NAME: githubSecret.secretName,
      },
    });

    // ========================================
    // Lambda Function - Processing
    // ========================================
    const processingLambda = new lambda.Function(this, 'ProcessingLambda', {
      functionName: 'vaultiq-processing',
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'handler.lambda_handler',
      code: lambda.Code.fromAsset('../src-lambda-code/processing'),
      timeout: cdk.Duration.minutes(15),
      memorySize: 2048,
      role: processingRole,
      environment: {
        METADATA_TABLE: metadataTable.tableName,
        OPENSEARCH_ENDPOINT: opensearchCollection.attrCollectionEndpoint,
        OPENSEARCH_INDEX: 'vaultiq-vectors',
      },
    });

    // S3 Event Trigger for Processing Lambda
    dataLakeBucket.addEventNotification(
      s3.EventType.OBJECT_CREATED,
      new s3n.LambdaDestination(processingLambda)
    );

    // ========================================
    // Lambda Function - API
    // ========================================
    const apiLambda = new lambda.Function(this, 'ApiLambda', {
      functionName: 'vaultiq-api',
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'main.handler',
      code: lambda.Code.fromAsset('../src-lambda-code/api'),
      timeout: cdk.Duration.seconds(30),
      memorySize: 1024,
      role: apiRole,
      environment: {
        METADATA_TABLE: metadataTable.tableName,
        OPENSEARCH_ENDPOINT: opensearchCollection.attrCollectionEndpoint,
        OPENSEARCH_INDEX: 'vaultiq-vectors',
      },
    });

    // ========================================
    // API Gateway
    // ========================================
    const api = new apigateway.RestApi(this, 'VaultIQApi', {
      restApiName: 'VaultIQ API',
      description: 'API Gateway for VaultIQ RAG queries',
      deployOptions: {
        stageName: 'prod',
      },
      defaultCorsPreflightOptions: {
        allowOrigins: apigateway.Cors.ALL_ORIGINS,
        allowMethods: apigateway.Cors.ALL_METHODS,
        allowHeaders: ['Content-Type'],
      },
    });

    const apiIntegration = new apigateway.LambdaIntegration(apiLambda);
    api.root.addProxy({
      defaultIntegration: apiIntegration,
      anyMethod: true,
    });

    // ========================================
    // EventBridge Rules - Scheduled Ingestion
    // ========================================
    const scheduleRule = new events.Rule(this, 'ConnectorScheduleRule', {
      schedule: events.Schedule.rate(cdk.Duration.minutes(15)),
      description: 'Trigger VaultIQ connectors every 15 minutes',
    });

    scheduleRule.addTarget(new targets.LambdaFunction(confluenceConnector));
    scheduleRule.addTarget(new targets.LambdaFunction(slackConnector));
    scheduleRule.addTarget(new targets.LambdaFunction(jiraConnector));
    scheduleRule.addTarget(new targets.LambdaFunction(githubConnector));

    // ========================================
    // Data Access Policy for OpenSearch
    // ========================================
    const dataAccessPolicy = new opensearchserverless.CfnAccessPolicy(this, 'VaultIQDataAccessPolicy', {
      name: 'vaultiq-data-access',
      type: 'data',
      policy: JSON.stringify([
        {
          Rules: [
            {
              ResourceType: 'collection',
              Resource: [`collection/${opensearchCollection.name}`],
              Permission: ['aoss:*'],
            },
            {
              ResourceType: 'index',
              Resource: [`index/${opensearchCollection.name}/*`],
              Permission: ['aoss:*'],
            },
          ],
          Principal: [
            processingRole.roleArn,
            apiRole.roleArn,
          ],
        },
      ]),
    });

    // ========================================
    // Outputs
    // ========================================
    new cdk.CfnOutput(this, 'DataLakeBucketName', {
      value: dataLakeBucket.bucketName,
      description: 'S3 Data Lake Bucket Name',
    });

    new cdk.CfnOutput(this, 'MetadataTableName', {
      value: metadataTable.tableName,
      description: 'DynamoDB Metadata Table Name',
    });

    new cdk.CfnOutput(this, 'OpenSearchEndpoint', {
      value: opensearchCollection.attrCollectionEndpoint,
      description: 'OpenSearch Serverless Collection Endpoint',
    });

    new cdk.CfnOutput(this, 'ApiEndpoint', {
      value: api.url,
      description: 'API Gateway Endpoint URL',
    });
  }
}