---
name: aws-sns
description: "Manages AWS Simple Notification Service for production-grade pub/sub messaging. Use when asked to: set up SNS topic with dead letter queue, configure message deduplication for FIFO topics, implement cross-account SNS topic access, set retry policies and backoff for failed deliveries, handle idempotent message processing, configure cross-region SNS subscriptions, implement SNS to SQS fanout with DLQ, or troubleshoot SNS delivery failures and message loss."
license: Apache-2.0
metadata:
  author: SharpSkills
  version: 1.0.0
  category: devops
  tags: [aws-sns, pub-sub, messaging, dead-letter-queue, fifo, cross-account, idempotency, fanout]
---

# AWS SNS Skill

## Quick Start

```bash
# Install AWS CLI v2
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip && sudo ./aws/install

# Install boto3
pip install boto3

# Create a standard topic and publish a message
aws sns create-topic --name my-production-topic
aws sns publish \
  --topic-arn arn:aws:sns:us-east-1:123456789012:my-production-topic \
  --message "Hello production" \
  --message-attributes '{"eventType":{"DataType":"String","StringValue":"order.created"}}'
```

## When to Use

Use this skill when asked to:
- Set up SNS topic with a dead letter queue (DLQ) for failed message handling
- Configure FIFO SNS topic with message deduplication IDs to prevent duplicates
- Grant cross-account access to an SNS topic via resource-based policy
- Subscribe an SQS queue in a different region to an SNS topic
- Tune SNS subscription delivery retry policy with exponential backoff
- Implement idempotent consumers using deduplication IDs and SQS FIFO
- Debug messages silently dropped by SNS (no delivery confirmation)
- Build SNS-to-SQS fanout with per-queue dead letter queues

## Core Patterns

### Pattern 1: FIFO Topic with Message Deduplication (Source: official)

FIFO topics guarantee ordering and exactly-once delivery within a 5-minute deduplication window. Supply a `MessageDeduplicationId` (content-based or explicit) and a `MessageGroupId` to control ordering per logical group.

```python
import boto3
import hashlib
import json

sns = boto3.client("sns", region_name="us-east-1")

# Create FIFO topic (name MUST end in .fifo)
response = sns.create_topic(
    Name="orders.fifo",
    Attributes={
        "FifoTopic": "true",
        "ContentBasedDeduplication": "false",  # explicit IDs give more control
    },
)
topic_arn = response["TopicArn"]

def publish_order_event(order_id: str, payload: dict) -> dict:
    """
    Publishes an order event with explicit deduplication.
    Re-publishing the same deduplication_id within 5 minutes is a no-op.
    """
    body = json.dumps(payload)
    # Deterministic ID: hash of order_id + event type prevents accidental dupes
    dedup_id = hashlib.sha256(f"order.created:{order_id}".encode()).hexdigest()

    return sns.publish(
        TopicArn=topic_arn,
        Message=body,
        MessageGroupId=f"order-{order_id}",          # ordering lane
        MessageDeduplicationId=dedup_id,              # idempotency key
        MessageAttributes={
            "eventType": {"DataType": "String", "StringValue": "order.created"},
            "orderId":   {"DataType": "String", "StringValue": order_id},
        },
    )

result = publish_order_event("ORD-9001", {"amount": 99.99, "currency": "USD"})
print("MessageId:", result["MessageId"])
# Calling again with same order_id within 5 min → same MessageId returned, not re-delivered
```

### Pattern 2: Dead Letter Queue for SNS Subscriptions (Source: official)

SNS does not natively support DLQs on topics — DLQs are configured **per subscription** using a `RedrivePolicy`. When SNS exhausts its retry attempts, the raw message is sent to the specified SQS queue.

```python
import boto3
import json

sns = boto3.client("sns", region_name="us-east-1")
sqs = boto3.client("sqs", region_name="us-east-1")

# 1. Create the primary SQS queue and the DLQ
primary_queue = sqs.create_queue(QueueName="orders-processor")
dlq = sqs.create_queue(QueueName="orders-processor-dlq")

primary_url = primary_queue["QueueUrl"]
dlq_url = dlq["QueueUrl"]

primary_attrs = sqs.get_queue_attributes(QueueUrl=primary_url, AttributeNames=["QueueArn"])
dlq_attrs = sqs.get_queue_attributes(QueueUrl=dlq_url, AttributeNames=["QueueArn"])

primary_arn = primary_attrs["Attributes"]["QueueArn"]
dlq_arn = dlq_attrs["Attributes"]["QueueArn"]

# 2. Subscribe primary SQS to the SNS topic with a RedrivePolicy (DLQ per subscription)
topic_arn = "arn:aws:sns:us-east-1:123456789012:orders.fifo"

subscription = sns.subscribe(
    TopicArn=topic_arn,
    Protocol="sqs",
    Endpoint=primary_arn,
    Attributes={
        # SNS will route to DLQ after exhausting retries
        "RedrivePolicy": json.dumps({"deadLetterTargetArn": dlq_arn}),
        # Raw delivery avoids double-JSON-encoding; consumer sees SNS envelope otherwise
        "RawMessageDelivery": "true",
    },
)
subscription_arn = subscription["SubscriptionArn"]
print("Subscription ARN:", subscription_arn)

# 3. Grant SNS permission to write to both queues
def allow_sns_on_queue(queue_url: str, queue_arn: str, topic_arn: str):
    policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "sns.amazonaws.com"},
            "Action": "sqs:SendMessage",
            "Resource": queue_arn,
            "Condition": {"ArnEquals": {"aws:SourceArn": topic_arn}},
        }],
    }
    sqs.set_queue_attributes(
        QueueUrl=queue_url,
        Attributes={"Policy": json.dumps(policy)},
    )

allow_sns_on_queue(primary_url, primary_arn, topic_arn)
allow_sns_on_queue(dlq_url, dlq_arn, topic_arn)
print("DLQ redrive policy attached to subscription.")
```

### Pattern 3: Custom Delivery Retry Policy with Exponential Backoff (Source: official)

SNS retry policies are set on the **topic** (HTTP/HTTPS endpoints) or on subscriptions. The `DeliveryPolicy` controls phase durations and backoff functions. SQS subscribers inherit their own redrive; this pattern targets HTTP endpoints.

```python
import boto3
import json

sns = boto3.client("sns", region_name="us-east-1")

delivery_policy = {
    "healthyRetryPolicy": {
        "numRetries": 20,                 # total attempts after initial failure
        "numNoDelayRetries": 0,           # immediate retries before backoff starts
        "minDelayTarget": 20,             # seconds — minimum backoff
        "maxDelayTarget": 600,            # seconds — maximum backoff (10 min)
        "numMinDelayRetries": 3,          # retries at minDelayTarget
        "numMaxDelayRetries": 5,          # retries at maxDelayTarget
        "backoffFunction": "exponential", # linear | arithmetic | geometric | exponential
    },
    "throttlePolicy": {
        "maxReceivesPerSecond": 10,       # rate-limit delivery to endpoint
    },
    "requestPolicy": {
        "headerContentType": "application/json",
    },
}

# Apply at topic level (affects all HTTP/S subscriptions on this topic)
topic_arn = "arn:aws:sns:us-east-1:123456789012:my-production-topic"
sns.set_topic_attributes(
    TopicArn=topic_arn,
    AttributeName="DeliveryPolicy",
    AttributeValue=json.dumps(delivery_policy),
)

# Or override per-subscription (HTTP/S only)
subscription_arn = "arn:aws:sns:us-east-1:123456789012:my-production-topic:abc-123"
sns.set_subscription_attributes(
    SubscriptionArn=subscription_arn,
    AttributeName="DeliveryPolicy",
    AttributeValue=json.dumps({"healthyRetryPolicy": {"numRetries": 10, "backoffFunction": "exponential"}}),
)
print("Delivery retry policy configured.")
```

### Pattern 4: Cross-Account SNS Topic Access (Source: official)

Cross-account access is granted via an SNS resource-based policy. The subscribing account needs `sns:Subscribe`; the publishing account needs `sns:Publish`. No role assumption is required for the topic owner — only policy attachment.

```python
import boto3
import json

sns = boto3.client("sns", region_name="us-east-1")

TOPIC_ARN          = "arn:aws:sns:us-east-1:111111111111:shared-events"
SUBSCRIBER_ACCOUNT = "222222222222"   # account that will subscribe
PUBLISHER_ACCOUNT  = "333333333333"   # account that will publish

cross_account_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowCrossAccountSubscribe",
            "Effect": "Allow",
            "Principal": {"AWS": f"arn:aws:iam::{SUBSCRIBER_ACCOUNT}:root"},
            "Action": ["sns:Subscribe", "sns:Receive"],
            "Resource": TOPIC_ARN,
            # Restrict to SQS to prevent HTTP endpoint abuse
            "Condition": {"StringEquals": {"sns:Protocol": "sqs"}},
        },
        {
            "Sid": "AllowCrossAccountPublish",
            "Effect": "Allow",
            "Principal": {"AWS": f"arn:aws:iam::{PUBLISHER_ACCOUNT}:root"},
            "Action": "sns:Publish",
            "Resource": TOPIC_ARN,
        },
    ],
}

sns.set_topic_attributes(
    TopicArn=TOPIC_ARN,
    AttributeName="Policy",
    AttributeValue=json.dumps(cross_account_policy),
)
print("Cross-account policy applied.")

# --- In the subscriber account (222222222222) ---
# sns_subscriber = boto3.client("sns", region_name="us-east-1")
# sns_subscriber.subscribe(
#     TopicArn=TOPIC_ARN,
#     Protocol="sqs",
#     Endpoint="arn:aws:sqs:us-east-1:222222222222:cross-account-queue",
# )
```

### Pattern 5: Cross-Region SNS-to-SQS Fanout (Source: official)

SNS can deliver to SQS queues in a different region by specifying the full cross-region queue ARN. The SQS queue policy must explicitly allow the SNS topic from the source region.

```python
import boto3
import json

# SNS topic in us-east-1, SQS queue in eu-west-1
SNS_REGION   = "us-east-1"
SQS_REGION   = "eu-west-1"
ACCOUNT_ID   = "123456789012"
TOPIC_ARN    = f"arn:aws:sns:{SNS_REGION}:{ACCOUNT_ID}:global-events"
QUEUE_ARN    = f"arn:aws:sqs:{SQS_REGION}:{ACCOUNT_ID}:eu-processor"
QUEUE_URL    = f"https://sqs.{SQS_REGION}.amazonaws.com/{ACCOUNT_ID}/eu-processor"

# 1. Update SQS queue policy in eu-west-1 to trust the SNS topic
sqs_eu = boto3.client("sqs", region_name=SQS_REGION)
queue_policy = {
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Principal": {"Service": "sns.amazonaws.com"},
        "Action": "sqs:SendMessage",
        "Resource": QUEUE_ARN,
        "Condition": {"ArnEquals": {"aws:SourceArn": TOPIC_ARN}},
    }],
}
sqs_eu.set_queue_attributes(
    QueueUrl=QUEUE_URL,
    Attributes={"Policy": json.dumps(queue_policy)},
)

# 2. Subscribe the EU queue to the us-east-1 topic
sns_us = boto3.client("sns", region_name=SNS_REGION)
response = sns_us.subscribe(
    TopicArn=TOPIC_ARN,
    Protocol="sqs",
    Endpoint=QUEUE_ARN,          # cross-region ARN works; URL does NOT
    Attributes={"RawMessageDelivery": "true"},
)
print("Cross-region subscription ARN:", response["SubscriptionArn"])
```

### Pattern 6: Idempotent SQS Consumer with Deduplication Tracking (Source: community)

Even with FIFO deduplication, at-least-once delivery means consumers must guard against duplicates outside the 5-minute window or from standard topics.

```python
# Source: community
# Tested: SharpSkill
import boto3
import json
import hashlib
import time

dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
sqs = boto3.client("sqs", region_name="us-east-1")

QUEUE_URL    = "https://sqs.us-east-1.amazonaws.com/123456789012/orders-processor"
DEDUP_TABLE  = "sns-message-dedup"   # TTL-based DynamoDB table; sort key: message_id

table = dynamodb.Table(DEDUP_TABLE)

def is_duplicate(message_id: str) -> bool:
    resp = table.get_item(Key={"message_id": message_id})
    return "Item" in resp

def mark_processed(message_id: str, ttl_seconds: int = 86400):
    table.put_item(Item={
        "message_id": message_id,
        "processed_at": int(time.time()),
        "ttl": int(time.time()) + ttl_seconds,   # DynamoDB TTL auto-deletes old records
    })

def process_message(body: dict):
    print("Processing:", body)

def poll_and_process():
    messages = sqs.receive_message(
        QueueUrl=QUEUE_URL,
        MaxNumberOfMessages=10,
        WaitTimeSeconds=20,          # long polling — avoids empty receive charges
        AttributeNames=["MessageDeduplicationId"],
    ).get("Messages", [])

    for msg in messages:
        message_id = msg["MessageId"]

        if is_duplicate(message_id):
            print(f"Duplicate skipped: {message_id}")
            # Still delete from SQS — already processed
        else:
            body = json.loads(msg["Body"])
            process_message(body)
            mark_processed(message_id)

        sqs.delete_message(QueueUrl=QUEUE_URL, ReceiptHandle=msg["ReceiptHandle"])

poll_and_process()
```

### Pattern 7: Error Handling