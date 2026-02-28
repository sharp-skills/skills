---
Looking at the errors:

1. **Blocks #6 and #7** (json): The JSON blocks have comments (`// ...`) which are invalid JSON
2. **Block #10** (typescript): The `msg.ReceiptHandle!` non-null assertion fails - the `Messages` variable and `msg` need proper typing, or the issue is that `queueUrl` is referenced but not defined in the quick start block

Let me trace the block numbers by counting code blocks:
1. bash (npm install)
2. typescript (quick start) ← block #10 is this one? Let me recount...

Blocks: #1=bash, #2=typescript(quickstart), #3=typescript(pattern1), #4=typescript(pattern2), #5=hcl, #6=json(queue policy), #7=json(iam policy), #8=typescript(long polling), #9=typescript(graceful shutdown), #10=typescript(quickstart)? 

The test framework counts from 1, so block #10 is likely 0-indexed block #9 (graceful shutdown) or the blocks are counted differently. Block #10 error shows `msg.ReceiptHandle!` - that's in the quickstart (block #2 by human count). The issue: `queueUrl` is used but not defined there. Also the non-null assertion `!` requires `strictNullChecks`.

For JSON blocks #6 and #7: remove comments from JSON.

---
name: aws-sqs
description: "Production-depth guidance for AWS SQS operations with emphasis on visibility timeout tuning, poison pill isolation, least-privilege IAM, and polling strategy. Use when asked to: configure SQS visibility timeout, extend message visibility during processing, detect and quarantine poison pill messages, set up dead-letter queues, configure long polling to reduce costs, grant cross-account SQS access with IAM, tune SQS consumer throughput, or troubleshoot messages reappearing after processing."
license: Apache-2.0
metadata:
  author: SharpSkills
  version: 1.0.0
  category: devops
  tags: [aws-sqs, message-queue, iam, dead-letter-queue, poison-pill, long-polling, visibility-timeout, cross-account]
---

# AWS SQS Skill

## Quick Start

```bash
npm install @aws-sdk/client-sqs
```

```typescript
import { SQSClient, ReceiveMessageCommand, DeleteMessageCommand } from "@aws-sdk/client-sqs";

const client = new SQSClient({ region: "us-east-1" });
const queueUrl = "https://sqs.us-east-1.amazonaws.com/123456789012/my-queue";

const { Messages } = await client.send(new ReceiveMessageCommand({
  QueueUrl: queueUrl,
  MaxNumberOfMessages: 10,
  WaitTimeSeconds: 20,
  VisibilityTimeout: 60,
  AttributeNames: ["ApproximateReceiveCount"],
}));

for (const msg of Messages ?? []) {
  await processMessage(msg);
  await client.send(new DeleteMessageCommand({
    QueueUrl: queueUrl,
    ReceiptHandle: msg.ReceiptHandle ?? "",
  }));
}
```

## When to Use

Use this skill when asked to:
- Configure or tune SQS visibility timeout for a consumer
- Extend message visibility while processing takes longer than expected
- Detect and quarantine poison pill / repeatedly failing messages
- Set up a dead-letter queue (DLQ) with a redrive policy
- Choose between long polling and short polling for SQS
- Grant least-privilege IAM access to SQS across AWS accounts
- Troubleshoot messages reappearing in the queue after deletion
- Reduce SQS API costs from excessive empty receive calls
- Set up cross-account SQS queue access without over-permissioning
- Debug consumers that starve under high message volume

---

## Core Patterns

### Pattern 1: Visibility Timeout Tuning and Mid-Flight Extension (Source: official)

The visibility timeout hides a message from other consumers while one consumer holds it. If processing exceeds the timeout, the message reappears and a second consumer picks it up — causing duplicate work or infinite loops.

**Rule:** Set `VisibilityTimeout` to at least 6× your expected processing time. Use `ChangeMessageVisibility` to heartbeat-extend when jobs are long.

```typescript
import {
  SQSClient,
  ChangeMessageVisibilityCommand,
  ReceiveMessageCommand,
  DeleteMessageCommand,
} from "@aws-sdk/client-sqs";

const client = new SQSClient({ region: "us-east-1" });
const QUEUE_URL = process.env.QUEUE_URL!;
const EXTENSION_SECONDS = 30;
const HEARTBEAT_INTERVAL_MS = 20_000;

async function processWithHeartbeat(msg: { ReceiptHandle?: string; Body?: string }) {
  const heartbeat = setInterval(async () => {
    try {
      await client.send(new ChangeMessageVisibilityCommand({
        QueueUrl: QUEUE_URL,
        ReceiptHandle: msg.ReceiptHandle ?? "",
        VisibilityTimeout: EXTENSION_SECONDS,
      }));
      console.log("Visibility extended");
    } catch (err) {
      console.error("Failed to extend visibility:", err);
      clearInterval(heartbeat);
    }
  }, HEARTBEAT_INTERVAL_MS);

  try {
    await doHeavyWork(msg.Body);
    await client.send(new DeleteMessageCommand({
      QueueUrl: QUEUE_URL,
      ReceiptHandle: msg.ReceiptHandle ?? "",
    }));
  } finally {
    clearInterval(heartbeat);
  }
}

async function doHeavyWork(body?: string) {
  await new Promise(r => setTimeout(r, 25_000));
}
```

**Limits (from AWS docs):**
- Minimum: 0 s | Maximum: 12 hours
- Each `ChangeMessageVisibility` call resets the clock from *now*, not from the original receive time
- You cannot extend beyond the 12-hour absolute maximum per receive attempt

---

### Pattern 2: Poison Pill Detection and Isolation to DLQ (Source: official)

A poison pill is a message that repeatedly fails processing and re-enters the queue. Without mitigation it saturates your consumer and starves healthy messages.

**Strategy:** Use `ApproximateReceiveCount` to detect messages that have been received more than N times, then manually move them to a dedicated poison-pill DLQ before the redrive policy would.

```typescript
import {
  SQSClient,
  ReceiveMessageCommand,
  SendMessageCommand,
  DeleteMessageCommand,
} from "@aws-sdk/client-sqs";

const client = new SQSClient({ region: "us-east-1" });
const MAIN_QUEUE = process.env.MAIN_QUEUE_URL!;
const POISON_QUEUE = process.env.POISON_QUEUE_URL!;
const POISON_THRESHOLD = 3;

async function consume() {
  const { Messages } = await client.send(new ReceiveMessageCommand({
    QueueUrl: MAIN_QUEUE,
    MaxNumberOfMessages: 10,
    WaitTimeSeconds: 20,
    AttributeNames: ["ApproximateReceiveCount"],
    MessageAttributeNames: ["All"],
  }));

  for (const msg of Messages ?? []) {
    const receiveCount = parseInt(
      msg.Attributes?.ApproximateReceiveCount ?? "1",
      10
    );

    if (receiveCount >= POISON_THRESHOLD) {
      await isolatePoisonPill(msg);
      continue;
    }

    try {
      await processMessage(msg);
      await client.send(new DeleteMessageCommand({
        QueueUrl: MAIN_QUEUE,
        ReceiptHandle: msg.ReceiptHandle ?? "",
      }));
    } catch (err) {
      console.error("Processing failed, will retry:", err);
    }
  }
}

async function isolatePoisonPill(msg: any) {
  console.warn(`Poison pill detected (MessageId: ${msg.MessageId}), isolating`);
  await client.send(new SendMessageCommand({
    QueueUrl: POISON_QUEUE,
    MessageBody: msg.Body,
    MessageAttributes: {
      OriginalMessageId: { DataType: "String", StringValue: msg.MessageId },
      OriginalReceiveCount: {
        DataType: "Number",
        StringValue: msg.Attributes?.ApproximateReceiveCount ?? "?",
      },
    },
  }));
  await client.send(new DeleteMessageCommand({
    QueueUrl: MAIN_QUEUE,
    ReceiptHandle: msg.ReceiptHandle ?? "",
  }));
}

async function processMessage(msg: any) {
  // throws on failure
}
```

**Complement with a redrive policy** (Terraform example) as a safety net:

```hcl
resource "aws_sqs_queue" "main" {
  name                       = "my-main-queue"
  visibility_timeout_seconds = 120
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = 5
  })
}

resource "aws_sqs_queue" "dlq" {
  name = "my-main-queue-dlq"
}
```

---

### Pattern 3: IAM Least-Privilege Cross-Account Queue Access (Source: official)

Granting another AWS account access to your SQS queue requires **both** an IAM identity policy in the consumer account **and** a resource-based queue policy in the producer/owner account. Missing either half silently denies access.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "CrossAccountConsumerAccess",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::ACCOUNT_B_ID:role/sqs-consumer-role"
      },
      "Action": [
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage",
        "sqs:ChangeMessageVisibility",
        "sqs:GetQueueAttributes"
      ],
      "Resource": "arn:aws:sqs:us-east-1:ACCOUNT_A_ID:my-queue",
      "Condition": {
        "StringEquals": {
          "aws:PrincipalOrgID": "o-xxxxxxxxxxxx"
        },
        "Bool": {
          "aws:SecureTransport": "true"
        }
      }
    }
  ]
}
```

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ConsumeFromAccountAQueue",
      "Effect": "Allow",
      "Action": [
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage",
        "sqs:ChangeMessageVisibility",
        "sqs:GetQueueAttributes"
      ],
      "Resource": "arn:aws:sqs:us-east-1:ACCOUNT_A_ID:my-queue"
    }
  ]
}
```

**Note:** `sqs:SendMessage` should be granted separately and only to producer roles — never bundle send + receive + delete into one policy.

---

### Pattern 4: Long Polling vs Short Polling Decision (Source: official)

```
Short polling (WaitTimeSeconds = 0):
  ┌──────────┐   empty response    ┌──────────┐
  │ Consumer │ ────────────────>   │ SQS      │
  │          │ <────────────────   │ (subset  │
  └──────────┘   (only queries     │  of nodes│
                  a subset of      │  sampled)│
                  servers)         └──────────┘
  Cost: high — many empty API calls billed at $0.40/million

Long polling (WaitTimeSeconds = 1–20):
  ┌──────────┐   waits up to 20s   ┌──────────┐
  │ Consumer │ ────────────────>   │ SQS      │
  │          │ <────────────────   │ (all     │
  └──────────┘   (all servers      │  servers │
                  sampled, returns  │  sampled)│
                  on first message) └──────────┘
  Cost: low — far fewer API calls, 0 empty responses when idle
```

```typescript
const params = {
  QueueUrl: QUEUE_URL,
  WaitTimeSeconds: 20,
  MaxNumberOfMessages: 10,
};

await client.send(new SetQueueAttributesCommand({
  QueueUrl: QUEUE_URL,
  Attributes: { ReceiveMessageWaitTimeSeconds: "20" },
}));
```

**When short polling is acceptable:**
- Batch jobs that need to drain a queue as fast as possible with many parallel consumers
- Lambda triggers (AWS manages polling internally with long polling anyway)

---

### Pattern 5: Graceful Consumer Shutdown (Source: community)

Abruptly killing a consumer mid-processing causes messages to remain invisible until the visibility timeout expires, delaying reprocessing.

```typescript
let isShuttingDown = false;
let inFlight = 0;

process.on("SIGTERM", async () => {
  console.log("SIGTERM received, draining in-flight messages...");
  isShuttingDown = true;
  while (inFlight > 0) {
    await new Promise(r => setTimeout(r, 500));
  }
  console.log("All in-flight messages complete. Exiting.");
  process.exit(0);
});

async function pollLoop() {
  while (!isShuttingDown) {
    const { Messages } = await client.send(new ReceiveMessageCommand({
      QueueUrl: QUEUE_URL,
      WaitTimeSeconds: 20,
      MaxNumberOfMessages: 10,
    }));

    const tasks = (Messages ?? []).map(async (msg) => {
      inFlight++;
      try {
        await processMessage(msg);
        await client.send(new DeleteMessageCommand({
          QueueUrl: QUEUE_URL,
          ReceiptHandle: msg.ReceiptHandle ?? "",
        }));
      } catch (err) {
        console.error("Message failed, will re-enqueue:", err);
      } finally {
        inFlight--;
      }
    });

    await Promise.all(tasks);
  }
}
```

---

## Production Notes

**1. Deleting before processing causes silent message loss**
Deleting a message immediately on receive (before confirming successful processing) permanently loses the message if your process crashes. Always delete *after* your work is durably committed.
Source: AWS SQS Best Practices docs

**2. Visibility timeout shorter than processing time causes duplicates**
If `VisibilityTimeout` is shorter than actual processing duration, SQS re-enqueues the message while the first consumer is still working. Use the heartbeat pattern (Pattern 1) or set timeout to 6× your P99 processing time.
Source: AWS SQS Developer Guide — Visibility Timeout

**3. `ApproximateReceiveCount` is eventually consistent**
Under high-throughput or rapid re-enqueue scenarios, `ApproximateReceiveCount` can lag by 1–2 counts. Set your poison-pill threshold at least 1 higher than your DLQ `maxReceiveCount` to avoid a race where SQS routes to DLQ before your code can isolate and audit the message.
Source: GitHub Issues — community reports on DLQ timing races

**4. Cross-account: missing queue policy causes opaque `AccessDenied`**
When an IAM policy in Account B explicitly allows SQS actions but the queue in Account A has no resource policy, the request is denied with a generic `AccessDenied`. Both sides must allow. Check CloudTrail — the denial event appears in Account A's trail, not B's.
Source: AWS IAM documentation — Cross-account resource policies

**5. Short polling with Lambda triggers wastes nothing — but custom consumers pay**
Lambda SQS event source mappings use long polling internally and are not billed per-poll. Custom EC2/ECS consumers using `WaitTimeSeconds: 0` are billed per API call including empty responses. At 1 req/s that's ~2.6M calls/month, ~$1.04 extra —