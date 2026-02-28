---
name: aws-s3
description: "Production-depth AWS S3 skill covering request rate limits and prefix partitioning, multipart upload failure recovery and cleanup, VPC endpoints for private S3 access, and account-level Block Public Access enforcement. Use when asked to: upload large files to S3 with retry logic, fix S3 503 SlowDown errors under high request rates, configure S3 VPC gateway or interface endpoints, enforce S3 Block Public Access at the account level, recover or clean up stuck multipart uploads, partition S3 key prefixes for throughput scaling, restrict S3 access to a specific VPC, or audit and abort incomplete multipart uploads to reduce storage costs."
license: Apache-2.0
compatibility:
- any
metadata:
  author: SharpSkills
  version: 1.0.0
  category: devops
  tags: [aws-s3, multipart-upload, vpc-endpoint, block-public-access, prefix-partitioning, boto3, s3-throughput]
---

# AWS S3 Skill

## Quick Start

```bash
pip install boto3
```

```python
import boto3

s3 = boto3.client("s3", region_name="us-east-1")

# Basic upload
s3.upload_file("local_file.txt", "my-bucket", "prefix/local_file.txt")

# Basic download
s3.download_file("my-bucket", "prefix/local_file.txt", "downloaded.txt")

# List objects under a prefix
response = s3.list_objects_v2(Bucket="my-bucket", Prefix="prefix/")
for obj in response.get("Contents", []):
    print(obj["Key"])
```

## When to Use

Use this skill when asked to:
- Upload large files (>100 MB) to S3 with multipart upload and retry logic
- Fix `503 SlowDown` or `503 Service Unavailable` errors under high S3 request rates
- Configure a VPC gateway or interface endpoint for private S3 access without NAT
- Enforce S3 Block Public Access at the AWS account level or per-bucket
- Recover from failed multipart uploads and clean up orphaned parts
- Partition S3 key prefixes to scale beyond 3,500 PUT or 5,500 GET requests per second per prefix
- Abort and audit incomplete multipart uploads to eliminate hidden storage charges
- Restrict S3 bucket access so only traffic originating from a specific VPC is allowed

## Core Patterns

### Pattern 1: Prefix Partitioning for High-Throughput Workloads (Source: official)

S3 scales to 3,500 PUT/COPY/POST/DELETE and 5,500 GET/HEAD requests **per second per prefix**. A prefix is everything in the key up to the final `/`. When all keys share the same prefix (e.g. `logs/2024/`), a single partition absorbs all traffic and throttles at those limits. Distribute load by hashing or sharding the leading path segment.

```python
import hashlib
import boto3

s3 = boto3.client("s3", region_name="us-east-1")
BUCKET = "my-high-throughput-bucket"

def sharded_key(logical_key: str, shard_count: int = 16) -> str:
    """
    Prepend a 2-hex-char shard prefix derived from the key hash.
    Results in up to 16 independent S3 prefixes, each with its own
    3,500 PUT / 5,500 GET per-second limit.
    e.g. "logs/event.json" -> "0a/logs/event.json"
    """
    shard = hashlib.md5(logical_key.encode()).hexdigest()[:2]
    # Clamp to shard_count buckets so prefix space stays predictable
    index = int(shard, 16) % shard_count
    return f"{index:02x}/{logical_key}"

# Write
key = sharded_key("logs/2024-01-15/event-9923.json")
s3.put_object(Bucket=BUCKET, Key=key, Body=b'{"event":"click"}')

# Read — must reconstruct the same sharded key
key = sharded_key("logs/2024-01-15/event-9923.json")
obj = s3.get_object(Bucket=BUCKET, Key=key)
print(obj["Body"].read())
```

> **Note:** S3 auto-partitions prefixes under sustained load, but it takes 15–30 minutes. Pre-shard before a traffic spike; do not rely on auto-partition during burst events.
> Source: https://docs.aws.amazon.com/AmazonS3/latest/userguide/optimizing-performance.html

---

### Pattern 2: Multipart Upload with Failure Recovery and Orphan Cleanup (Source: official)

Multipart upload is required for objects >5 GB and recommended above 100 MB. A crash mid-upload leaves parts in the bucket — billable storage with no visible object. The pattern below: (a) initiates multipart upload, (b) uploads parts with per-part retry, (c) completes or aborts on failure.

```python
import boto3
import math
import os
from botocore.exceptions import ClientError

s3 = boto3.client("s3", region_name="us-east-1")
BUCKET = "my-bucket"
PART_SIZE = 64 * 1024 * 1024  # 64 MiB — minimum 5 MiB except last part

def upload_large_file(local_path: str, s3_key: str, max_retries: int = 3) -> str:
    file_size = os.path.getsize(local_path)
    part_count = math.ceil(file_size / PART_SIZE)

    # Initiate
    mpu = s3.create_multipart_upload(Bucket=BUCKET, Key=s3_key)
    upload_id = mpu["UploadId"]
    print(f"Started multipart upload: {upload_id}")

    parts = []
    try:
        with open(local_path, "rb") as f:
            for part_num in range(1, part_count + 1):
                data = f.read(PART_SIZE)
                for attempt in range(1, max_retries + 1):
                    try:
                        resp = s3.upload_part(
                            Bucket=BUCKET,
                            Key=s3_key,
                            PartNumber=part_num,
                            UploadId=upload_id,
                            Body=data,
                        )
                        parts.append({"PartNumber": part_num, "ETag": resp["ETag"]})
                        print(f"  Part {part_num}/{part_count} OK")
                        break
                    except ClientError as e:
                        print(f"  Part {part_num} attempt {attempt} failed: {e}")
                        if attempt == max_retries:
                            raise  # triggers abort in outer except

        # Complete
        result = s3.complete_multipart_upload(
            Bucket=BUCKET,
            Key=s3_key,
            MultipartUpload={"Parts": parts},
            UploadId=upload_id,
        )
        return result["Location"]

    except Exception as exc:
        # Always abort — prevents orphaned parts from accumulating
        print(f"Upload failed, aborting {upload_id}: {exc}")
        s3.abort_multipart_upload(Bucket=BUCKET, Key=s3_key, UploadId=upload_id)
        raise


def abort_all_incomplete_uploads(bucket: str) -> int:
    """
    Safety net: find and abort every incomplete multipart upload in a bucket.
    Run as a scheduled job or before enabling lifecycle rules.
    Returns count of uploads aborted.
    """
    paginator = s3.get_paginator("list_multipart_uploads")
    aborted = 0
    for page in paginator.paginate(Bucket=bucket):
        for upload in page.get("Uploads", []):
            s3.abort_multipart_upload(
                Bucket=bucket,
                Key=upload["Key"],
                UploadId=upload["UploadId"],
            )
            print(f"Aborted: {upload['Key']} / {upload['UploadId']}")
            aborted += 1
    return aborted
```

**Lifecycle rule (preferred for automation)** — aborts any upload not completed within 7 days:

```python
s3.put_bucket_lifecycle_configuration(
    Bucket=BUCKET,
    LifecycleConfiguration={
        "Rules": [
            {
                "ID": "abort-incomplete-mpu",
                "Status": "Enabled",
                "Filter": {"Prefix": ""},          # all keys
                "AbortIncompleteMultipartUpload": {"DaysAfterInitiation": 7},
            }
        ]
    },
)
```

> Source: https://docs.aws.amazon.com/AmazonS3/latest/userguide/mpuoverview.html

---

### Pattern 3: VPC Endpoints for Private S3 Access (Source: official)

A **Gateway endpoint** (free, route-table based) is the standard choice for EC2/Lambda in a VPC. An **Interface endpoint** (hourly + data-processing charge, DNS-based) is required for on-premises traffic over Direct Connect/VPN.

```python
import boto3

ec2 = boto3.client("ec2", region_name="us-east-1")

# --- Gateway endpoint (no per-hour cost) ---
response = ec2.create_vpc_endpoint(
    VpcEndpointType="Gateway",
    VpcId="vpc-0abc12345def67890",
    ServiceName="com.amazonaws.us-east-1.s3",
    RouteTableIds=["rtb-0123456789abcdef0"],  # private subnets' route tables
    PolicyDocument="""{
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": "*",
            "Action": ["s3:GetObject", "s3:PutObject", "s3:ListBucket"],
            "Resource": [
                "arn:aws:s3:::my-bucket",
                "arn:aws:s3:::my-bucket/*"
            ]
        }]
    }""",
)
endpoint_id = response["VpcEndpoint"]["VpcEndpointId"]
print(f"Gateway endpoint created: {endpoint_id}")
```

**Bucket policy — enforce VPC-only access** (deny all non-VPC traffic):

```python
import json

bucket_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "DenyNonVPCAccess",
            "Effect": "Deny",
            "Principal": "*",
            "Action": "s3:*",
            "Resource": [
                "arn:aws:s3:::my-bucket",
                "arn:aws:s3:::my-bucket/*",
            ],
            "Condition": {
                "StringNotEquals": {
                    "aws:SourceVpce": "vpce-0abc12345def67890"
                }
            },
        }
    ],
}

s3 = boto3.client("s3", region_name="us-east-1")
s3.put_bucket_policy(Bucket="my-bucket", Body=json.dumps(bucket_policy))
print("VPC-only bucket policy applied.")
```

> **Important:** The `DenyNonVPCAccess` statement also blocks the AWS Console and CLI running outside the VPC. Add an explicit `Allow` for admin IAM roles when needed.
> Source: https://docs.aws.amazon.com/AmazonS3/latest/userguide/privatelink-interface-endpoints.html

---

### Pattern 4: S3 Block Public Access — Account-Level Enforcement (Source: official)

Block Public Access (BPA) is the primary control against accidental public exposure. Account-level BPA overrides any bucket policy or ACL that attempts to grant public access.

```python
import boto3

# Account-level BPA — applies to ALL buckets in the account
s3control = boto3.client("s3control", region_name="us-east-1")
account_id = boto3.client("sts").get_caller_identity()["Account"]

s3control.put_public_access_block(
    AccountId=account_id,
    PublicAccessBlockConfiguration={
        "BlockPublicAcls": True,        # Ignore PUT requests that grant public ACLs
        "IgnorePublicAcls": True,       # Ignore existing public ACLs on objects/buckets
        "BlockPublicPolicy": True,      # Reject bucket policies that grant public access
        "RestrictPublicBuckets": True,  # Restrict access to buckets with public policies
    },
)
print(f"Account-level Block Public Access enabled for account {account_id}")

# Verify
response = s3control.get_public_access_block(AccountId=account_id)
print(response["PublicAccessBlockConfiguration"])
```

**Per-bucket BPA** (when account-level is not feasible):

```python
s3 = boto3.client("s3", region_name="us-east-1")
s3.put_public_access_block(
    Bucket="my-bucket",
    PublicAccessBlockConfiguration={
        "BlockPublicAcls": True,
        "IgnorePublicAcls": True,
        "BlockPublicPolicy": True,
        "RestrictPublicBuckets": True,
    },
)
```

**AWS Config rule to audit compliance** (detect any bucket with BPA disabled):

```python
# Deploy via AWS Config — managed rule, no Lambda required
config = boto3.client("config", region_name="us-east-1")
config.put_config_rule(
    ConfigRule={
        "ConfigRuleName": "s3-account-level-public-access-blocks",
        "Source": {
            "Owner": "AWS",
            "SourceIdentifier": "S3_ACCOUNT_LEVEL_PUBLIC_ACCESS_BLOCKS_PERIODIC",
        },
        "MaximumExecutionFrequency": "TwentyFour_Hours",
    }
)
```

> Source: https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-control-block-public-access.html

---

### Pattern 5: 503 SlowDown Retry with Exponential Backoff (Source: community)

S3 returns `503 SlowDown` when request rate to a prefix exceeds the per-partition limit. The AWS SDK retries by default, but default settings are often too aggressive for burst workloads.

```python
# Source: community
# Tested: SharpSkill

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
import time
import random

# Increase retry attempts and switch to adaptive retry mode,
# which tracks throttling signals and slows the request rate automatically.
s3 = boto3.client(
    "s3",
    region_name="us-east-1",
    config=Config(
        retries={
            "max_attempts": 10,
            "mode": "adaptive",   # "adaptive" > "standard" for throttling workloads
        }
    ),
)

def get_with_backoff(bucket: str, key: str, max_retries: int = 8):
    """Manual exponential backoff for cases where SDK retry is exhausted."""
    for attempt in range(max_retries):
        try:
            return s3.get_object(Bucket=bucket, Key=key)
        except ClientError as e:
            code = e.response["Error"]["Code"]
            if code in ("503", "SlowDown", "ServiceUnavailable"):
                wait = (2 ** attempt) + random.uniform(0, 1)
                print(f"SlowDown on attempt {attempt + 1}, waiting {wait:.2f}s")
                time.sleep(wait)
            else:
                raise  # non-throttling errors propagate immediately
    raise RuntimeError(f"Exceeded {max_retries} retries for s3://{bucket}/{key}")
```

## Production Notes

**1. Orphaned multipart parts are billed silently**
Parts uploaded before a `create_multipart_upload` is either completed or aborted remain in the bucket and incur standard storage charges —