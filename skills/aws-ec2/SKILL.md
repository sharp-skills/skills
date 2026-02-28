---
name: aws-ec2
description: "Manages AWS EC2 instances with production-grade security and performance hardening. Use when asked to: launch or terminate EC2 instances, harden instance metadata service with IMDSv2, configure placement groups for low-latency workloads, set up Nitro hypervisor enhanced networking, recover from instance store or EBS failures, optimize EC2 networking with SR-IOV or ENA, automate instance lifecycle with AWS SDK, or debug instance connectivity and boot failures."
license: Apache-2.0
compatibility:
- any
metadata:
  author: SharpSkills
  version: 1.0.0
  category: devops
  tags: [aws-ec2, imdsv2, nitro, placement-groups, enhanced-networking, instance-store, ebs, cloud-infrastructure]
---

# AWS EC2 Skill

## Quick Start

```bash
# Install AWS CLI v2
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip && sudo ./aws/install

# Launch a Nitro-based instance with IMDSv2 enforced (no IMDSv1 fallback)
aws ec2 run-instances \
  --image-id ami-0c02fb55956c7d316 \
  --instance-type m6i.xlarge \
  --key-name my-key \
  --subnet-id subnet-0abc123 \
  --metadata-options "HttpTokens=required,HttpPutResponseHopLimit=1,HttpEndpoint=enabled" \
  --ebs-optimized \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=prod-node}]'
```

## When to Use

Use this skill when asked to:
- Launch, stop, or terminate EC2 instances via CLI or SDK
- Enforce IMDSv2 to block SSRF-based metadata credential theft
- Configure cluster or spread placement groups for HPC or fault isolation
- Enable Elastic Network Adapter (ENA) or SR-IOV for Nitro enhanced networking
- Recover data after instance store loss or EBS volume detachment
- Diagnose instance boot failures, networking drops, or kernel panics via console output
- Automate instance lifecycle (start/stop schedules, Auto Scaling integration)
- Tune EC2 for low-latency inter-node communication in distributed systems

## Core Patterns

### Pattern 1: IMDSv2 Hardening — Enforce Token-Based Metadata Access (Source: official)

IMDSv1 allows unauthenticated HTTP GET to `169.254.169.254`, making it exploitable via SSRF. IMDSv2 requires a session-oriented PUT token. Set `HttpTokens=required` at launch and retroactively on running instances. Keep hop limit at 1 to block container-to-host metadata leakage.

```bash
# Enforce IMDSv2 on an already-running instance
aws ec2 modify-instance-metadata-options \
  --instance-id i-0abc1234567890def \
  --http-tokens required \
  --http-put-response-hop-limit 1 \
  --http-endpoint enabled

# Retrieve metadata from within the instance using IMDSv2
TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" \
  -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")

# Use the token for all subsequent metadata calls
curl -s -H "X-aws-ec2-metadata-token: $TOKEN" \
  http://169.254.169.254/latest/meta-data/instance-id

curl -s -H "X-aws-ec2-metadata-token: $TOKEN" \
  http://169.254.169.254/latest/meta-data/iam/security-credentials/
```

```bash
# Audit account-wide: find instances still allowing IMDSv1
aws ec2 describe-instances \
  --query 'Reservations[].Instances[?MetadataOptions.HttpTokens!=`required`].[InstanceId,MetadataOptions.HttpTokens]' \
  --output table

# Enforce IMDSv2 as account default for all NEW instances
aws ec2 modify-instance-metadata-defaults \
  --http-tokens required \
  --http-put-response-hop-limit 2
```

### Pattern 2: Placement Groups — Cluster vs Spread vs Partition (Source: official)

Cluster placement groups co-locate instances in a single Availability Zone on high-bisection-bandwidth hardware, reducing inter-node latency to under 100µs. Spread placement groups place each instance on distinct underlying hardware, maximizing fault isolation. Partition placement groups spread instances across logical partitions (up to 7 per AZ) for large distributed systems like HDFS or Kafka.

```bash
# Create a cluster placement group for HPC / low-latency workloads
aws ec2 create-placement-group \
  --group-name hpc-cluster-pg \
  --strategy cluster

# Launch instances INTO the cluster group (must use same instance family)
aws ec2 run-instances \
  --image-id ami-0c02fb55956c7d316 \
  --instance-type c6gn.16xlarge \
  --count 4 \
  --placement "GroupName=hpc-cluster-pg,Tenancy=default" \
  --network-interfaces '[{"DeviceIndex":0,"InterfaceType":"efa","DeleteOnTermination":true}]'

# Create a spread placement group for fault isolation (max 7 instances per AZ)
aws ec2 create-placement-group \
  --group-name critical-spread-pg \
  --strategy spread \
  --spread-level host

# Create a partition placement group for distributed data systems
aws ec2 create-placement-group \
  --group-name kafka-partition-pg \
  --strategy partition \
  --partition-count 3

# Launch into a specific partition (useful for rack-aware Kafka broker placement)
aws ec2 run-instances \
  --image-id ami-0c02fb55956c7d316 \
  --instance-type r6i.2xlarge \
  --count 3 \
  --placement "GroupName=kafka-partition-pg,PartitionNumber=1"
```

### Pattern 3: Nitro Enhanced Networking — ENA and SR-IOV Configuration (Source: official)

Nitro-based instances use the Elastic Network Adapter (ENA) to bypass the hypervisor for network I/O, delivering up to 100 Gbps throughput, consistent low latency, and lower CPU overhead. SR-IOV (via Intel VF driver `ixgbevf`) is the legacy path for older instance families. Always verify the driver is active before benchmarking.

```bash
# Verify ENA support on the AMI before launch
aws ec2 describe-images \
  --image-ids ami-0c02fb55956c7d316 \
  --query 'Images[0].EnaSupport'

# Enable ENA attribute on an existing AMI (must be stopped first)
aws ec2 stop-instances --instance-ids i-0abc1234567890def
aws ec2 modify-instance-attribute \
  --instance-id i-0abc1234567890def \
  --ena-support

# Verify ENA is active inside the instance (Amazon Linux 2)
modinfo ena | grep "^version"
ethtool -i eth0 | grep driver   # should show: driver: ena

# Check network interface queue depth and driver stats
ethtool -S eth0 | grep -E "queue_0_(tx|rx)_cnt"

# Enable SR-IOV (for older c3/i2/r3 instances not on Nitro)
aws ec2 modify-instance-attribute \
  --instance-id i-0abc1234567890def \
  --sriov-net-support simple

# Verify SR-IOV inside instance
modinfo ixgbevf
```

```bash
# Tune ENA for maximum throughput: increase ring buffer sizes
sudo ethtool -G eth0 rx 8192 tx 8192

# Pin IRQs to CPU cores matching NUMA topology (critical for >25 Gbps)
# Source: community
# Tested: SharpSkill
cat /proc/interrupts | grep eth0
sudo sh /usr/sbin/set_irq_affinity.sh eth0
```

### Pattern 4: Instance Store vs EBS — Failure Recovery Patterns (Source: official)

Instance store volumes are physically attached NVMe SSDs on Nitro instances. They provide the highest IOPS (up to 7.5M read IOPS on i4i.32xlarge) but data is lost on stop, termination, or host failure. EBS volumes persist independently. Production strategy: use instance store for ephemeral scratch space, write-ahead logs, or read caches; replicate durably to EBS or S3.

```bash
# List available instance store volumes after launch (NVMe on Nitro)
lsblk -d -o NAME,MODEL,SIZE | grep NVMe
ls -la /dev/nvme*

# Format and mount instance store (lost on stop — automate in user-data)
sudo mkfs.xfs -L ephemeral0 /dev/nvme1n1
sudo mkdir -p /mnt/ephemeral
sudo mount -t xfs -o noatime,nodiratime /dev/nvme1n1 /mnt/ephemeral

# Add to /etc/fstab with nofail to prevent boot hang if device absent
echo "LABEL=ephemeral0 /mnt/ephemeral xfs defaults,nofail,x-systemd.device-timeout=5 0 2" \
  | sudo tee -a /etc/fstab

# EBS: create and attach a high-performance gp3 volume
aws ec2 create-volume \
  --availability-zone us-east-1a \
  --volume-type gp3 \
  --size 500 \
  --iops 16000 \
  --throughput 1000 \
  --encrypted \
  --tag-specifications 'ResourceType=volume,Tags=[{Key=Name,Value=prod-data}]'

aws ec2 attach-volume \
  --volume-id vol-0abc1234567890def \
  --instance-id i-0abc1234567890def \
  --device /dev/sdf

# EBS recovery: detach from failed instance and re-attach to rescue instance
aws ec2 detach-volume --volume-id vol-0abc1234567890def --force
aws ec2 attach-volume \
  --volume-id vol-0abc1234567890def \
  --instance-id i-0rescue1234567890 \
  --device /dev/sdg
```

```bash
# Snapshot EBS for point-in-time recovery before risky operations
aws ec2 create-snapshot \
  --volume-id vol-0abc1234567890def \
  --description "pre-migration-$(date +%Y%m%d-%H%M%S)"

# Enable EBS fast snapshot restore in target AZ to eliminate snap-restore latency
aws ec2 enable-fast-snapshot-restores \
  --availability-zones us-east-1a \
  --source-snapshot-ids snap-0abc1234567890def
```

### Pattern 5: Error Handling — Instance Launch Failures (Source: community)
# Tested: SharpSkill

The most common unhandled failure is `InsufficientInstanceCapacity` in a single AZ. Applications that hardcode a single AZ will fail silently or retry indefinitely. The fix is multi-AZ retry logic with exponential backoff.

```python
import boto3
import time
from botocore.exceptions import ClientError

ec2 = boto3.client('ec2', region_name='us-east-1')

SUBNETS_BY_AZ = {
    'us-east-1a': 'subnet-aaa111',
    'us-east-1b': 'subnet-bbb222',
    'us-east-1c': 'subnet-ccc333',
}

RETRYABLE_ERRORS = {
    'InsufficientInstanceCapacity',
    'InsufficientHostCapacity',
    'Unsupported',          # instance type not available in AZ
    'RequestLimitExceeded',
}

def launch_with_az_fallback(image_id, instance_type, key_name, sg_id):
    """
    Attempt launch across AZs with exponential backoff on capacity errors.
    # Source: community / # Tested: SharpSkill
    """
    for attempt, (az, subnet_id) in enumerate(SUBNETS_BY_AZ.items()):
        try:
            print(f"Attempting launch in {az} (attempt {attempt + 1})")
            response = ec2.run_instances(
                ImageId=image_id,
                InstanceType=instance_type,
                MinCount=1,
                MaxCount=1,
                KeyName=key_name,
                SubnetId=subnet_id,
                SecurityGroupIds=[sg_id],
                MetadataOptions={
                    'HttpTokens': 'required',
                    'HttpPutResponseHopLimit': 1,
                    'HttpEndpoint': 'enabled',
                },
                EbsOptimized=True,
                TagSpecifications=[{
                    'ResourceType': 'instance',
                    'Tags': [{'Key': 'Name', 'Value': f'prod-{az}'}]
                }]
            )
            instance_id = response['Instances'][0]['InstanceId']
            print(f"Launched {instance_id} in {az}")
            return instance_id

        except ClientError as e:
            code = e.response['Error']['Code']
            if code in RETRYABLE_ERRORS:
                wait = 2 ** attempt
                print(f"[{code}] in {az}, retrying next AZ in {wait}s...")
                time.sleep(wait)
                continue
            raise  # non-retryable: propagate immediately

    raise RuntimeError("All AZs exhausted: InsufficientInstanceCapacity in all zones")


# Wait for instance to reach 'running' state with status check polling
def wait_for_running(instance_id, timeout=300):
    waiter = ec2.get_waiter('instance_running')
    waiter.wait(
        InstanceIds=[instance_id],
        WaiterConfig={'Delay': 10, 'MaxAttempts': timeout // 10}
    )
    # Also confirm system and instance status checks pass
    waiter2 = ec2.get_waiter('instance_status_ok')
    waiter2.wait(InstanceIds=[instance_id])
    print(f"{instance_id} is running and status checks passed")
```

## Production Notes

**1. IMDSv1 left enabled exposes IAM credentials via SSRF**
Any web application vulnerable to SSRF can request `http://169.254.169.254/latest/meta-data/iam/security-credentials/` and exfiltrate temporary IAM credentials. Setting `HttpTokens=required` at account defaults prevents new instances from being vulnerable, but existing instances must be patched individually. Run the describe-instances audit query weekly in CI.
Source: AWS Security Blog / IMDS documentation

**2. Cluster placement group failures: `InsufficientInstanceCapacity` on large counts**
AWS cannot always place 16+ same-family instances into a single cluster PG simultaneously. The fix is to launch in smaller batches (4–8 at a time) and allow AWS to pack them before requesting more. Alternatively, use a pre-warmed reservation with EC2 Capacity Reservations targeting the PG.
Source: Reddit r/devops, AWS re:Post community threads

**3. ENA driver version mismatch causes silent packet drops above 10 Gbps**
Older Amazon Linux 2 AMIs ship with ENA driver 2.2.x. On m6i/c6i instances the driver should be ≥2.8.x to avoid TX queue stalls under heavy load. Symptom: `ethtool -S eth0 | grep tx_timeout` increments during load tests. Fix: update kernel or install latest ENA driver from the AWS ENA GitHub repository.
Source: GitHub aws/amzn-drivers issues

**4. Instance store data loss on host maintenance events**
AWS scheduled maintenance (host retirement) stops and restarts instances, which wipes instance store volumes. Applications that write to instance store without replication (e.g