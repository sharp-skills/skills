---
I need to analyze the errors:

1. **YAML blocks #4 and #5**: `!Sub` and `!Ref` tags fail with standard YAML parsers. Need to quote them or use a plain string approach.
2. **TypeScript block #8**: `interface` is TypeScript syntax but being run as JavaScript. Need to convert to plain JS or restructure.
3. **npm:aws-cdk-lib/aws-iam** and **npm:aws-cdk-lib/aws-dynamodb**: Wrong package names — these are submodules of `aws-cdk-lib`, not separate npm packages. The imports are fine in code, but the skill metadata or package references need fixing. Looking at the errors, these seem to be package validation checks. The CDK block needs to show correct npm install.

For YAML issues with `!Sub` and `!Ref`: I need to use string literals instead of YAML tags. I'll replace them with the CloudFormation intrinsic function long form or use plain strings that won't break YAML parsers... Actually, the fix is to use `"Fn::Sub"` and `"Ref"` long-form syntax instead of `!Sub`/`!Ref` short tags.

For the TypeScript block #8 (capacity planning): The `interface` keyword fails as JS. I need to add a TypeScript code fence instead of typescript, or restructure. It's already marked as `typescript` — the test runner must be executing it as JS. I need to remove the `interface` and use JSDoc or just remove it.

For CDK packages: Change the CDK TypeScript block to not import from subpath packages, or add the correct npm install line. Actually `aws-cdk-lib/aws-iam` and `aws-cdk-lib/aws-dynamodb` are valid subpath imports from `aws-cdk-lib` package. The test checks `npm:aws-cdk-lib/aws-iam` as a package — I should change imports to use the main package differently, or wrap it so the package check passes. The simplest fix: change the CDK pattern to use `@aws-cdk/aws-iam` and `@aws-cdk/aws-dynamodb` — but those are v1. Better: keep `aws-cdk-lib` but ensure the npm package check finds it. The error says "wrong package name" — perhaps I need to reference `aws-cdk-lib` not the subpaths. I'll restructure the imports.

---
name: aws-dynamodb
description: "Production-grade AWS DynamoDB patterns with exponential backoff, capacity planning, VPC endpoints, and IAM least-privilege policies. Use when asked to: set up DynamoDB with retry logic, configure auto-scaling for DynamoDB tables, implement exponential backoff for throttled requests, create least-privilege IAM policies per DynamoDB table, configure VPC endpoints for private DynamoDB access, plan DynamoDB read/write capacity, handle ProvisionedThroughputExceededException, or implement production-ready DynamoDB clients."
license: Apache-2.0
metadata:
  author: SharpSkills
  version: 1.0.0
  category: database
  tags: [aws-dynamodb, dynamodb, aws, exponential-backoff, auto-scaling, vpc-endpoints, iam, capacity-planning]
---

# AWS DynamoDB Skill (Production Depth)

## Quick Start

```bash
npm install @aws-sdk/client-dynamodb @aws-sdk/lib-dynamodb @aws-sdk/util-dynamodb
```

```typescript
import { DynamoDBClient } from "@aws-sdk/client-dynamodb";
import { DynamoDBDocumentClient, GetCommand, PutCommand } from "@aws-sdk/lib-dynamodb";

const raw = new DynamoDBClient({ region: "us-east-1" });
const client = DynamoDBDocumentClient.from(raw, {
  marshallOptions: { removeUndefinedValues: true },
});

// Put item
await client.send(new PutCommand({ TableName: "orders", Item: { pk: "order#1", sk: "2024-01-01", total: 99.99 } }));

// Get item
const { Item } = await client.send(new GetCommand({ TableName: "orders", Key: { pk: "order#1", sk: "2024-01-01" } }));
```

## When to Use

Use this skill when asked to:
- Set up DynamoDB with production-grade retry and backoff logic
- Handle `ProvisionedThroughputExceededException` or `RequestLimitExceeded` errors
- Configure DynamoDB auto-scaling with target utilization policies
- Create per-table IAM least-privilege policies for DynamoDB access
- Set up VPC endpoints so Lambda/EC2 never traverses the public internet for DynamoDB
- Plan read/write capacity units (RCUs/WCUs) for a given traffic model
- Implement transactional writes or batch operations safely
- Debug throttling, hot partitions, or capacity exhaustion in production

## Core Patterns

### Pattern 1: Exponential Backoff with Jitter for Throttling (Source: official)

DynamoDB throttles requests that exceed provisioned capacity. AWS recommends full jitter backoff to spread retry storms. The AWS SDK v3 has built-in retry middleware but default settings are insufficient for burst throttling.

```typescript
import { DynamoDBClient } from "@aws-sdk/client-dynamodb";
import { DynamoDBDocumentClient, GetCommand } from "@aws-sdk/lib-dynamodb";
import { ConfiguredRetryStrategy } from "@aws-sdk/util-retry";

// Source: official AWS SDK v3 retry configuration
// Docs: https://docs.aws.amazon.com/sdk-for-javascript/v3/developer-guide/middleware-stack.html
const raw = new DynamoDBClient({
  region: process.env.AWS_REGION ?? "us-east-1",
  retryStrategy: new ConfiguredRetryStrategy(
    8, // max attempts (1 initial + 7 retries)
    (attempt: number) => {
      // Full jitter: random(0, min(cap, base * 2^attempt))
      const cap = 30_000;       // 30 s ceiling
      const base = 100;         // 100 ms base
      const expDelay = Math.min(cap, base * Math.pow(2, attempt));
      return Math.floor(Math.random() * expDelay);
    }
  ),
});

const client = DynamoDBDocumentClient.from(raw, {
  marshallOptions: { removeUndefinedValues: true, convertClassInstanceToMap: true },
  unmarshallOptions: { wrapNumbers: false },
});

// Wrapper that surfaces remaining capacity info on throttle
async function safeGet(tableName: string, key: Record<string, unknown>) {
  try {
    return await client.send(new GetCommand({ TableName: tableName, Key: key }));
  } catch (err: any) {
    if (err.name === "ProvisionedThroughputExceededException") {
      console.error("[DynamoDB] Throttled after all retries — check capacity alarms", {
        table: tableName,
        key,
        retryableReason: err.message,
      });
    }
    throw err;
  }
}
```

### Pattern 2: Auto-Scaling Configuration via CloudFormation / CDK (Source: official)

Provision both a table and its auto-scaling policy together. Target 70 % utilization — low enough to absorb sudden traffic spikes before throttling begins.

```yaml
# CloudFormation — production auto-scaling for DynamoDB
# Docs: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/AutoScaling.html
Resources:
  OrdersTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: orders
      BillingMode: PROVISIONED
      ProvisionedThroughput:
        ReadCapacityUnits: 10
        WriteCapacityUnits: 10
      KeySchema:
        - AttributeName: pk
          KeyType: HASH
        - AttributeName: sk
          KeyType: RANGE
      AttributeDefinitions:
        - AttributeName: pk
          AttributeType: S
        - AttributeName: sk
          AttributeType: S
      PointInTimeRecoverySpecification:
        PointInTimeRecoveryEnabled: true
      SSESpecification:
        SSEEnabled: true        # AWS-managed KMS at rest

  # Read auto-scaling
  OrdersReadScalableTarget:
    Type: AWS::ApplicationAutoScaling::ScalableTarget
    Properties:
      MaxCapacity: 1000
      MinCapacity: 10
      ResourceId:
        "Fn::Sub": "table/${OrdersTable}"
      ScalableDimension: dynamodb:table:ReadCapacityUnits
      ServiceNamespace: dynamodb
      RoleARN:
        "Fn::Sub": "arn:aws:iam::${AWS::AccountId}:role/aws-service-role/dynamodb.application-autoscaling.amazonaws.com/AWSServiceRoleForApplicationAutoScaling_DynamoDBTable"

  OrdersReadScalingPolicy:
    Type: AWS::ApplicationAutoScaling::ScalingPolicy
    Properties:
      PolicyName: OrdersReadAutoScaling
      PolicyType: TargetTrackingScaling
      ScalingTargetId:
        "Ref": OrdersReadScalableTarget
      TargetTrackingScalingPolicyConfiguration:
        TargetValue: 70.0          # % utilization target
        ScaleInCooldown: 300       # seconds — prevent flapping
        ScaleOutCooldown: 60
        PredefinedMetricSpecification:
          PredefinedMetricType: DynamoDBReadCapacityUtilization

  # Write auto-scaling (mirror pattern)
  OrdersWriteScalableTarget:
    Type: AWS::ApplicationAutoScaling::ScalableTarget
    Properties:
      MaxCapacity: 500
      MinCapacity: 10
      ResourceId:
        "Fn::Sub": "table/${OrdersTable}"
      ScalableDimension: dynamodb:table:WriteCapacityUnits
      ServiceNamespace: dynamodb
      RoleARN:
        "Fn::Sub": "arn:aws:iam::${AWS::AccountId}:role/aws-service-role/dynamodb.application-autoscaling.amazonaws.com/AWSServiceRoleForApplicationAutoScaling_DynamoDBTable"

  OrdersWriteScalingPolicy:
    Type: AWS::ApplicationAutoScaling::ScalingPolicy
    Properties:
      PolicyName: OrdersWriteAutoScaling
      PolicyType: TargetTrackingScaling
      ScalingTargetId:
        "Ref": OrdersWriteScalableTarget
      TargetTrackingScalingPolicyConfiguration:
        TargetValue: 70.0
        ScaleInCooldown: 300
        ScaleOutCooldown: 60
        PredefinedMetricSpecification:
          PredefinedMetricType: DynamoDBWriteCapacityUtilization
```

### Pattern 3: VPC Endpoint for Private DynamoDB Access (Source: official)

Without a VPC endpoint, traffic between Lambda/EC2 inside a VPC and DynamoDB traverses the public internet. A Gateway endpoint is free and routes traffic privately.

```yaml
# CloudFormation — DynamoDB VPC Gateway Endpoint
# Docs: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/vpc-endpoints-dynamodb.html
Resources:
  DynamoDBVPCEndpoint:
    Type: AWS::EC2::VPCEndpoint
    Properties:
      VpcId:
        "Ref": AppVPC
      ServiceName:
        "Fn::Sub": "com.amazonaws.${AWS::Region}.dynamodb"
      VpcEndpointType: Gateway
      RouteTableIds:
        - "Ref": PrivateRouteTable1
        - "Ref": PrivateRouteTable2
      PolicyDocument:
        Version: "2012-10-17"
        Statement:
          - Effect: Allow
            Principal: "*"
            Action:
              - "dynamodb:GetItem"
              - "dynamodb:PutItem"
              - "dynamodb:UpdateItem"
              - "dynamodb:DeleteItem"
              - "dynamodb:Query"
              - "dynamodb:Scan"
              - "dynamodb:BatchGetItem"
              - "dynamodb:BatchWriteItem"
              - "dynamodb:TransactGetItems"
              - "dynamodb:TransactWriteItems"
            Resource:
              - "Fn::Sub": "arn:aws:dynamodb:${AWS::Region}:${AWS::AccountId}:table/orders"
              - "Fn::Sub": "arn:aws:dynamodb:${AWS::Region}:${AWS::AccountId}:table/orders/*"
```

### Pattern 4: IAM Least-Privilege Policy Per Table (Source: official)

Never grant `dynamodb:*` or wildcard resources. Scope each role to the exact actions and table ARN it needs, including GSI sub-resources.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "OrdersTableReadWrite",
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem",
        "dynamodb:Query",
        "dynamodb:ConditionCheckItem"
      ],
      "Resource": [
        "arn:aws:dynamodb:us-east-1:123456789012:table/orders",
        "arn:aws:dynamodb:us-east-1:123456789012:table/orders/index/*"
      ],
      "Condition": {
        "StringEquals": {
          "aws:RequestedRegion": "us-east-1"
        }
      }
    },
    {
      "Sid": "DenyTableDeletion",
      "Effect": "Deny",
      "Action": [
        "dynamodb:DeleteTable",
        "dynamodb:UpdateTable"
      ],
      "Resource": "*"
    }
  ]
}
```

```typescript
// Inline CDK equivalent
// npm install aws-cdk-lib constructs
import { aws_iam as iam, aws_dynamodb as dynamodb } from "aws-cdk-lib";

declare const table: dynamodb.Table;
declare const lambdaRole: iam.Role;

// CDK convenience — generates least-privilege policy automatically
table.grantReadWriteData(lambdaRole);

// For read-only consumers (e.g., reporting Lambda)
table.grantReadData(lambdaRole);

// Explicit deny for destructive ops — always add this
lambdaRole.addToPolicy(new iam.PolicyStatement({
  effect: iam.Effect.DENY,
  actions: ["dynamodb:DeleteTable", "dynamodb:UpdateTable"],
  resources: ["*"],
}));
```

### Pattern 5: Capacity Planning Formula (Source: official)

```typescript
// RCU / WCU estimation helpers
// Docs: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/ProvisionedThroughput.html

type ConsistencyModel = "eventual" | "strong" | "transactional";

interface CapacityEstimate {
  rcu: number;
  wcu: number;
}

/**
 * Eventually consistent reads cost 0.5 RCU per 4 KB item.
 * Strongly consistent reads cost 1 RCU per 4 KB item.
 * Transactional reads cost 2 RCU per 4 KB item.
 */
function estimateRCU(params: {
  readsPerSecond: number;
  avgItemSizeKB: number;
  consistencyModel: ConsistencyModel;
}): number {
  const blocks = Math.ceil(params.avgItemSizeKB / 4);
  const multiplier = params.consistencyModel === "eventual" ? 0.5
    : params.consistencyModel === "transactional" ? 2 : 1;
  return Math.ceil(params.readsPerSecond * blocks * multiplier);
}

/**
 * Standard writes cost 1 WCU per 1 KB item.
 * Transactional writes cost 2 WCU per 1 KB item.