#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { VaultiqStack } from '../lib/vaultiq-stack';

const app = new cdk.App();

new VaultiqStack(app, 'VaultiqStack', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION || 'us-east-1',
  },
  description: 'VaultIQ - AI-Powered Unified Knowledge Hub Infrastructure',
});

app.synth();