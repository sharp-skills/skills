---
name: aws-dynamodb
description: "Production-grade AWS DynamoDB patterns with exponential backoff, VPC endpoints, IAM least-privilege access, and Global Tables conflict resolution. Use when asked to: set up DynamoDB with retry logic, implement exponential backoff for throttling, configure private DynamoDB via VPC endpoints, create attribute-level IAM policies, resolve Global Tables replication conflicts, handle ProvisionedThroughputExceededException, design multi-region DynamoDB with conflict resolution, or monitor replication lag across DynamoDB regions."
license: Apache-2.0
compatibility:
- any
metadata:
  author: SharpSkills
  version: 1.0.0
  category: database
  tags: [aws-dynamodb, dynamodb, aws, global-tables, vpc-endpoints, iam, backoff, replication]
---

# AWS DynamoDB Skill

## Quick Start

```bash
npm install @aws-sdk/client-dynamodb @aws-sdk/lib-dynamodb
```

```javascript
import { DynamoDBClient } from "@aws-sdk/client-dynamodb";
import { DynamoDBDocumentClient, GetCommand, PutCommand } from "@aws-sdk/lib-dynamodb";

const client = new DynamoDBClient({ region: "us-east-1" });
const docClient = DynamoDBDocumentClient.from(client);

// Put item
await docClient.send(new PutCommand({
  TableName: "Orders",
  Item: { orderId: "ord-001", status: "pending", amount: 99.99 }
}));

// Get item
const { Item } = await docClient.send(new GetCommand({
  TableName: "Orders",
  Key: { orderId: "ord-001" }
}));
```

## When to Use

Use this skill when asked to:
- Handle `ProvisionedThroughputExceededException` or DynamoDB throttling errors
- Implement exponential backoff with jitter for DynamoDB retries
- Connect to DynamoDB privately through a VPC endpoint (no internet traversal)
- Write IAM policies restricting access to specific DynamoDB attributes or conditions
- Set up DynamoDB Global Tables for multi-region active-active replication
- Detect or resolve write conflicts and monitor replication lag in Global Tables
- Enforce least-privilege access at the item or attribute level using IAM conditions
- Migrate from deprecated `aws-dynamodb` npm package to `@awspilot/dynamodb` or AWS SDK v3

## Core Patterns

### Pattern 1: Exponential Backoff with Full Jitter for Throttling (Source: official)

The AWS SDK v3 retries automatically, but tuning `maxAttempts` and using full jitter prevents thundering-herd storms when capacity is exhausted. Full jitter (`Math.random() * cap`) is recommended over equal jitter for high-concurrency workloads.

```javascript
import { DynamoDBClient } from "@aws-sdk/client-dynamodb";
import { DynamoDBDocumentClient, PutCommand } from "@aws-sdk/lib-dynamodb";
import { ConfiguredRetryStrategy } from "@aws-sdk/util-retry";

// Full-jitter exponential backoff: sleep = random(0, min(cap, base * 2^attempt))
function fullJitterDelay(attempt, baseMs = 100, capMs = 20000) {
  const exponential = Math.min(capMs, baseMs * Math.pow(2, attempt));
  return Math.floor(Math.random() * exponential);
}

async function putWithBackoff(docClient, params, maxAttempts = 8) {
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    try {
      return await docClient.send(new PutCommand(params));
    } catch (err) {
      const throttled =
        err.name === "ProvisionedThroughputExceededException" ||
        err.name === "RequestLimitExceeded" ||
        err.name === "ThrottlingException";

      if (!throttled || attempt === maxAttempts - 1) throw err;

      const delay = fullJitterDelay(attempt);
      console.warn(`Throttled (attempt ${attempt + 1}), retrying in ${delay}ms`);
      await new Promise((r) => setTimeout(r, delay));
    }
  }
}

// SDK-level retry configuration (complements manual backoff for transient errors)
const client = new DynamoDBClient({
  region: "us-east-1",
  retryStrategy: new ConfiguredRetryStrategy(
    8,                          // maxAttempts
    (attempt) => fullJitterDelay(attempt)
  ),
});
const docClient = DynamoDBDocumentClient.from(client);

// Usage
await putWithBackoff(docClient, {
  TableName: "Orders",
  Item: { orderId: "ord-002", status: "new" },
});
```

### Pattern 2: VPC Endpoint for Private DynamoDB Access (Source: official)

Gateway VPC endpoints for DynamoDB route traffic entirely within the AWS network — no NAT Gateway, no internet. Required for compliance workloads (HIPAA, PCI-DSS) or when Lambda/EC2 runs in a private subnet.

```javascript
// --- Infrastructure: Terraform snippet ---
// resource "aws_vpc_endpoint" "dynamodb" {
//   vpc_id            = aws_vpc.main.id
//   service_name      = "com.amazonaws.us-east-1.dynamodb"
//   vpc_endpoint_type = "Gateway"
//   route_table_ids   = [aws_route_table.private.id]
// }

// --- Application: client auto-uses VPC endpoint via route table; no SDK change needed ---
import { DynamoDBClient } from "@aws-sdk/client-dynamodb";
import { DynamoDBDocumentClient, QueryCommand } from "@aws-sdk/lib-dynamodb";

// When running inside a VPC with Gateway endpoint configured, traffic stays private.
// Optionally force endpoint URL for interface endpoints (PrivateLink):
const client = new DynamoDBClient({
  region: "us-east-1",
  // Uncomment for Interface endpoint (PrivateLink), not needed for Gateway endpoints:
  // endpoint: "https://vpce-<id>.dynamodb.us-east-1.vpce.amazonaws.com",
});
const docClient = DynamoDBDocumentClient.from(client);

// Validate private connectivity — no public IP should be reachable
async function queryPrivate(userId) {
  const result = await docClient.send(new QueryCommand({
    TableName: "UserEvents",
    KeyConditionExpression: "userId = :uid",
    ExpressionAttributeValues: { ":uid": userId },
  }));
  return result.Items;
}
```

**VPC Endpoint Policy (least-privilege — attach to the endpoint itself):**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": { "AWS": "arn:aws:iam::123456789012:role/AppRole" },
      "Action": ["dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:Query"],
      "Resource": "arn:aws:dynamodb:us-east-1:123456789012:table/UserEvents"
    }
  ]
}
```

### Pattern 3: IAM Least-Privilege — Attribute-Level Access Control (Source: official)

DynamoDB IAM conditions support `dynamodb:Attributes`, `dynamodb:LeadingKeys`, and `dynamodb:Select` to restrict access at the attribute and item level — critical for multi-tenant tables.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowReadOwnItems",
      "Effect": "Allow",
      "Action": ["dynamodb:GetItem", "dynamodb:Query"],
      "Resource": "arn:aws:dynamodb:us-east-1:123456789012:table/UserData",
      "Condition": {
        "ForAllValues:StringEquals": {
          "dynamodb:LeadingKeys": ["${aws:PrincipalTag/userId}"],
          "dynamodb:Attributes": ["userId", "email", "preferences", "createdAt"]
        },
        "StringEqualsIfExists": {
          "dynamodb:Select": "SPECIFIC_ATTRIBUTES"
        }
      }
    },
    {
      "Sid": "DenyPIIAttributes",
      "Effect": "Deny",
      "Action": ["dynamodb:GetItem", "dynamodb:Query", "dynamodb:Scan"],
      "Resource": "arn:aws:dynamodb:us-east-1:123456789012:table/UserData",
      "Condition": {
        "ForAnyValue:StringEquals": {
          "dynamodb:Attributes": ["ssn", "creditCard", "rawPassword"]
        }
      }
    }
  ]
}
```

```javascript
// Application: request only allowed attributes to satisfy IAM condition
import { DynamoDBDocumentClient, GetCommand } from "@aws-sdk/lib-dynamodb";

async function getUserPreferences(docClient, userId) {
  const { Item } = await docClient.send(new GetCommand({
    TableName: "UserData",
    Key: { userId },
    // Must match dynamodb:Attributes condition exactly
    ProjectionExpression: "userId, email, preferences, createdAt",
  }));
  return Item;
}
```

### Pattern 4: Global Tables — Conflict Resolution and Replication Lag (Source: official)

DynamoDB Global Tables use **last-writer-wins (LWW)** based on wall-clock time. Concurrent writes to different regions that arrive within the replication window (~1 second typical, up to seconds under load) will silently overwrite each other. Detecting and mitigating conflicts requires application-level version attributes.

```javascript
import { DynamoDBDocumentClient, UpdateCommand, GetCommand } from "@aws-sdk/lib-dynamodb";

// Optimistic locking with version counter to detect lost updates across regions
async function updateWithVersionCheck(docClient, tableName, key, updates, expectedVersion) {
  try {
    const result = await docClient.send(new UpdateCommand({
      TableName: tableName,
      Key: key,
      // Increment version; reject if someone else already wrote a newer version
      UpdateExpression: "SET #v = :newVersion, #ts = :timestamp, #data = :data",
      ConditionExpression: "#v = :expectedVersion",
      ExpressionAttributeNames: {
        "#v": "version",
        "#ts": "lastUpdatedAt",
        "#data": "payload",
      },
      ExpressionAttributeValues: {
        ":newVersion": expectedVersion + 1,
        ":expectedVersion": expectedVersion,
        ":timestamp": Date.now(),
        ":data": updates,
      },
      ReturnValues: "ALL_NEW",
    }));
    return { success: true, item: result.Attributes };
  } catch (err) {
    if (err.name === "ConditionalCheckFailedException") {
      // Another region wrote first — fetch current state and signal conflict
      const { Item } = await docClient.send(new GetCommand({
        TableName: tableName,
        Key: key,
        ConsistentRead: true, // Only valid in the table's home region
      }));
      return { success: false, conflict: true, currentItem: Item };
    }
    throw err;
  }
}

// Monitor replication lag via CloudWatch (metric: ReplicationLatency per region)
// aws cloudwatch get-metric-statistics \
//   --namespace AWS/DynamoDB \
//   --metric-name ReplicationLatency \
//   --dimensions Name=TableName,Value=GlobalOrders Name=ReceivingRegion,Value=eu-west-1 \
//   --start-time 2024-01-01T00:00:00Z --end-time 2024-01-01T01:00:00Z \
//   --period 60 --statistics Maximum

// Alert threshold: ReplicationLatency > 5000ms indicates replication pressure
```

### Pattern 5: Error Handling — ProvisionedThroughputExceededException (Source: community)

Real-world scenario: Lambda functions burst simultaneously during a traffic spike, exhausting table RCU/WCU, causing cascading failures because errors propagate without retry.

```javascript
// Source: community / Tested: SharpSkill
import { DynamoDBDocumentClient, BatchWriteCommand } from "@aws-sdk/lib-dynamodb";

// BatchWrite returns UnprocessedItems instead of throwing — must handle explicitly
async function batchWriteWithRetry(docClient, tableName, items, maxAttempts = 5) {
  let unprocessed = items.map((item) => ({ PutRequest: { Item: item } }));

  for (let attempt = 0; attempt < maxAttempts && unprocessed.length > 0; attempt++) {
    if (attempt > 0) {
      // Full jitter backoff between batch retry attempts
      const delay = Math.floor(Math.random() * Math.min(20000, 200 * Math.pow(2, attempt)));
      await new Promise((r) => setTimeout(r, delay));
    }

    const result = await docClient.send(new BatchWriteCommand({
      RequestItems: { [tableName]: unprocessed },
    }));

    // CRITICAL: SDK does NOT throw for unprocessed items — always check this field
    unprocessed = result.UnprocessedItems?.[tableName] ?? [];

    if (unprocessed.length > 0) {
      console.warn(`Attempt ${attempt + 1}: ${unprocessed.length} unprocessed items remain`);
    }
  }

  if (unprocessed.length > 0) {
    throw new Error(`BatchWrite failed: ${unprocessed.length} items unprocessed after ${maxAttempts} attempts`);
  }
}
```

## Production Notes

**1. BatchWriteItem silently drops unprocessed items**
The `BatchWriteCommand` response includes an `UnprocessedItems` map when throttled. The SDK does **not** throw an exception — callers that ignore this field silently lose data. Always loop on `UnprocessedItems` with backoff.
Source: AWS DynamoDB Developer Guide — BatchWriteItem

**2. ConsistentRead is region-local in Global Tables**
`ConsistentRead: true` only guarantees consistency within the region where the read is issued. Reads from a replica region may still return stale data even with consistent reads enabled. For cross-region consistency, route reads to the write region or accept eventual consistency by design.
Source: AWS Global Tables documentation

**3. VPC Gateway Endpoints do not support all DynamoDB APIs**
Streams (DynamoDB Streams / Kinesis Data Streams for DynamoDB) use a separate endpoint (`streams.dynamodb.<region>.amazonaws.com`). A Gateway VPC endpoint for DynamoDB does **not** cover Streams traffic. Add a separate Interface endpoint for Streams or allow outbound HTTPS for `streams.dynamodb.*`.
Source: AWS VPC Endpoints documentation

**4. IAM `dynamodb:LeadingKeys` condition does not block Scan operations**
Attribute-level and leading-key conditions in IAM apply to `GetItem`, `Query`, and `UpdateItem`, but `Scan` with a filter expression bypasses `LeadingKeys` enforcement. Explicitly Deny `dynamodb:Scan` on multi-tenant tables where row isolation is required.
Source: AWS IAM Condition Keys for DynamoDB documentation

**5. Global Tables LWW conflict window is not zero**
Even with version-check optimistic locking, a write to region A and a simultaneous write to region B can both pass their local `ConditionExpression` checks before replication propagates. The replication window (typically <1s, but variable under load) means both writes succeed locally, and one is silently discarded. Design for idempotency and use `ReplicationLatency` CloudWatch alarms.
Source: AWS DynamoDB Global Tables — Conflict Resolution documentation / Reddit r/devops

## Failure Modes

| Symptom | Root Cause | Fix |
|---------|-----------|-----|
| `ProvisionedThroughputExceededException` on spiky traffic | Hot partition key or insufficient WCU/RCU for burst | Use on-demand capacity mode, redesign partition key for even distribution, implement exponential backoff with full jitter |
| Silent data loss in `BatchWriteItem` | `UnprocessedItems` not checked after SDK call | Always iterate on `UnprocessedItems` with back