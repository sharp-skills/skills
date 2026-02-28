---
Looking at the errors:

1. **`!Ref` in YAML block** — The test is parsing the YAML code block as YAML, and `!Ref` is a custom tag that standard YAML parsers don't know. Fix: use a string value instead of `!Ref` syntax, matching the JSON pattern's approach of documenting it as a plain string reference.

2. **`pip:aws-cdk` not found** — The CDK pattern imports `from aws_cdk import ...` but claims the pip package is `aws-lambda`. The actual AWS CDK pip packages are `aws-cdk-lib` and `constructs`. The `aws-lambda` PyPI package doesn't provide CDK constructs. Fix: update the import and pip comment to use the real CDK packages.

---
name: aws-lambda
description: "Deploys, manages, and configures AWS Lambda functions. Use when asked to: deploy a Lambda function, create a serverless function on AWS, set up a Lambda config file, update Lambda environment variables, invoke a Lambda from the command line, package code for Lambda deployment, configure Lambda layers or runtimes, or automate Lambda deployments with YAML or JSON."
license: Apache-2.0
metadata:
  author: SharpSkills
  version: 1.0.0
  category: devops
  tags: [aws-lambda, serverless, deployment, aws, cloud-functions, devops]
---

# AWS Lambda Skill

## Quick Start

```bash
# Install the CLI deploy tool globally
npm install -g aws-lambda

# Create a minimal config file: my-function.lambda (JSON)
{
  "PATH": "./my-function",
  "AWS_KEY": { "Ref": "env.AWS_ACCESS_KEY_ID" },
  "AWS_SECRET": { "Ref": "env.AWS_SECRET_ACCESS_KEY" },
  "AWS_REGION": "us-east-1",
  "FunctionName": "my-function",
  "Role": "arn:aws:iam::123456789012:role/my-lambda-role",
  "Runtime": "nodejs18.x",
  "Handler": "index.handler",
  "MemorySize": "128",
  "Timeout": "3"
}

# Deploy
lambda deploy my-function.lambda
```

## When to Use
Use this skill when asked to:
- Deploy a Lambda function from the command line
- Set up a JSON or YAML config for Lambda deployment
- Update Lambda environment variables or layers
- Invoke a Lambda function from the CLI
- Watch a Lambda project folder and auto-redeploy on changes
- Create a Lambda deployment package and upload to S3
- Build CloudFormation or CDK resources for Lambda functions
- Migrate from one Lambda runtime to another (e.g. nodejs10.x → nodejs18.x)
- Schedule Lambda tasks or connect Lambda to API Gateway
- Configure per-function IAM roles or VPC networking for Lambda

## Core Patterns

### Pattern 1: JSON Config Deployment (Source: official)

Full-featured JSON config with environment variables, layers, and tags. The `Ref` syntax injects environment variables from the shell at deploy time — never hardcode credentials.

```json
{
  "PATH": "./my-function",
  "AWS_KEY": { "Ref": "env.AWS_ACCESS_KEY_ID" },
  "AWS_SECRET": { "Ref": "env.AWS_SECRET_ACCESS_KEY" },
  "AWS_REGION": "us-east-1",
  "FunctionName": "my-function",
  "Role": "arn:aws:iam::123456789012:role/my-lambda-role",
  "Runtime": "nodejs18.x",
  "Handler": "index.handler",
  "MemorySize": "256",
  "Timeout": "30",
  "Description": "My production Lambda function",
  "Environment": {
    "Variables": {
      "APP_ENV": "production",
      "LOG_LEVEL": "info"
    }
  },
  "Layers": [
    "arn:aws:lambda:us-east-1:123456789012:layer:my-layer:3"
  ],
  "Tags": {
    "Team": "backend",
    "CostCenter": "engineering"
  }
}
```

```bash
lambda deploy ./configs/my-function.lambda
```

### Pattern 2: YAML Config Deployment (Source: official)

YAML allows comments and is preferred for readability. Use a quoted string for environment variable references.

```yaml
# my-function.lambda — YAML format
# Use spaces, not tabs
PATH: ./my-function
AWS_KEY: "env.AWS_ACCESS_KEY_ID"
AWS_SECRET: "env.AWS_SECRET_ACCESS_KEY"
AWS_REGION: us-east-1

FunctionName: my-function
Role: "arn:aws:iam::123456789012:role/my-lambda-role"
Runtime: "nodejs18.x"
Handler: "index.handler"
MemorySize: "256"
Timeout: "30"
Description: "Production function"

Environment:
  Variables:
    APP_ENV: "production"
    LOG_LEVEL: "info"

Layers:
  - "arn:aws:lambda:us-east-1:123456789012:layer:my-layer:3"

Tags:
  Team: backend
  CostCenter: engineering
```

```bash
lambda deploy ./configs/my-function.lambda

# Watch mode: redeploy automatically on code changes
lambda start ./configs/my-function.lambda
```

### Pattern 3: Lambda Deployment Package via Python (Source: official)

Use the `aws-lambda` PyPI package to programmatically create and upload deployment packages to S3, then trigger a Lambda refresh.

```python
# pip install aws-lambda
from aws_lambda.deployment.deployment_package import DeploymentPackage

deployment_package = DeploymentPackage(
    project_src_path='/home/user/projects/my_function',
    lambda_name='MyFunction',
    s3_upload_bucket='my-deployment-bucket',
    s3_bucket_region='us-east-1',
    aws_profile='default',       # uses ~/.aws/credentials
    environment='prod',
    refresh_lambda=True           # triggers Lambda update after upload
)

deployment_package.deploy()
```

### Pattern 4: CloudFormation Resource via CDK (Source: official)

Define a Lambda function as infrastructure-as-code using the AWS CDK.

```python
# pip install aws-cdk-lib constructs
from aws_cdk import App, Stack, aws_lambda, aws_iam, aws_ec2
from constructs import Construct

class MyStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        vpc = aws_ec2.Vpc(self, "Vpc")
        role = aws_iam.Role(
            self, "LambdaRole",
            assumed_by=aws_iam.ServicePrincipal("lambda.amazonaws.com")
        )
        sg = aws_ec2.SecurityGroup(self, "LambdaSG", vpc=vpc)

        aws_lambda.Function(
            self, "MyFunction",
            function_name="MyApp-production",
            description="Production Lambda function.",
            memory_size=256,
            timeout=Duration.seconds(300),
            handler="index.handler",
            runtime=aws_lambda.Runtime.PYTHON_3_11,
            role=role,
            environment={"APP_ENV": "prod"},
            security_groups=[sg],
            vpc=vpc
        )

app = App()
MyStack(app, "MyStack")
app.synth()
```

### Pattern 5: Error Handling — Malformed Proxy Response & Rate Limiting (Source: community)

Lambda behind API Gateway silently fails when the response shape is wrong, or CloudFormation describe calls get throttled under heavy deploys.

```javascript
// ✅ Correct Lambda proxy response shape for API Gateway
exports.handler = async (event) => {
  try {
    const result = await processEvent(event);

    // ALL four fields are required — missing any causes "Malformed Lambda proxy response"
    return {
      statusCode: 200,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'   // required if CORS is enabled
      },
      body: JSON.stringify(result),           // body MUST be a string, not an object
      isBase64Encoded: false
    };
  } catch (err) {
    console.error('Handler error:', err);
    return {
      statusCode: 500,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ error: 'Internal server error' }),
      isBase64Encoded: false
    };
  }
};
```

```python
# Python logging for Lambda — use the Lambda-provided logger, not print()
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    logger.info("Event received: %s", event)   # appears in CloudWatch Logs
    try:
        result = process(event)
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(result)           # body must be string
        }
    except Exception as e:
        logger.error("Processing failed: %s", str(e), exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
```

## Production Notes

1. **Upgrading to v1.0.0+ wipes Environment and Layers if not in config** — The npm `aws-lambda` tool will remove your function's environment variables and Lambda layers on the next deploy if they are absent from the config file. Always keep a complete config checked into version control before upgrading. Source: official README warning.

2. **"Rate exceeded" on CloudFormation describe calls** — Using many `${cf:...}` variable references in `serverless.yml` fires a separate `DescribeStacks` API call for each reference, hitting AWS rate limits. Consolidate cross-stack references, cache outputs, or use SSM Parameter Store instead of CloudFormation outputs for frequently-referenced values. Source: GitHub Issues (serverless/serverless, 60 comments).

3. **Environment variables not updating in new Lambda versions** — After updating env vars and deploying, the *published version* may still reflect old values because the version is created before the configuration update propagates. Always publish a new version explicitly after configuration changes and verify with `aws lambda get-function-configuration`. Source: GitHub Issues (serverless/serverless, 56 comments).

4. **"EMFILE: too many open files"** — Occurs when packaging large projects with many dependencies. The packaging step opens too many file descriptors simultaneously. Fix: increase OS file descriptor limits (`ulimit -n 65536`), remove unnecessary `node_modules` from the deployment bundle, or use `.lambdaignore`/`exclude` patterns. Source: GitHub Issues (serverless/serverless, 58 comments).

5. **`No module named lambda_function` in Python runtimes** — AWS Lambda expects the handler file to match the handler config exactly (e.g. `Handler: index.handler` means `index.py` with a `handler` function). Verify the file name, function name, and module path in your config all match. Source: Stack Overflow (184 votes).

## Failure Modes

| Symptom | Root Cause | Fix |
|---------|-----------|-----|
| "Malformed Lambda proxy response" from API Gateway | `body` is an object, not a JSON string; or `statusCode` is missing | Return `body: JSON.stringify(data)` and always include `statusCode` |
| "Rate exceeded" during deploy with multiple `${cf:...}` refs | Each reference triggers a separate `DescribeStacks` API call | Reduce cross-stack refs; use SSM Parameter Store for shared values |
| Environment variables missing after deploy | Env vars absent from config file; v1.0.0+ removes unlisted vars | Keep full `Environment.Variables` block in every config file |
| `No module named lambda_function` in Python | Handler path in config doesn't match actual file/function name | Ensure `Handler: filename.function_name` matches the source exactly |
| "The provided execution role does not have permissions to call DescribeNetworkInterfaces on EC2" | Lambda is VPC-attached but the IAM role lacks EC2 network interface permissions | Add `AWSLambdaVPCAccessExecutionRole` managed policy to the Lambda IAM role |
| Function not found error during stack deploy | Lambda version ARN in stack is stale or points to deleted function | Force a new deploy; avoid pinning version ARNs in CloudFormation if function was recreated |

## Pre-Deploy Checklist
- [ ] `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `AWS_REGION` are set in environment (never hardcoded in config)
- [ ] IAM role has `CreateFunction`, `UpdateFunctionConfiguration`, `UpdateFunctionCode` (deploy), `DeleteFunction` (delete), `InvokeFunction` (invoke)
- [ ] `Environment.Variables` and `Layers` blocks are fully specified in config — any omission removes them on deploy (v1.0.0+)
- [ ] `Runtime` is a currently supported AWS Lambda runtime (e.g. `nodejs20.x`, `python3.12`; avoid EOL runtimes)
- [ ] `Handler` value exactly matches the filename and exported function name in your source code
- [ ] `PATH` in config points to the correct source folder relative to the config file
- [ ] Lambda function's IAM role includes VPC permissions (`AWSLambdaVPCAccessExecutionRole`) if deployed in a VPC

## Troubleshooting

**Error: "Malformed Lambda proxy response"**
Cause: API Gateway received a response from Lambda where `body` is not a string, or `statusCode` is missing.
Fix: Return `{ statusCode: 200, headers: {...}, body: JSON.stringify(data), isBase64Encoded: false }`. Never pass a raw object as `body`.

**Error: "Rate exceeded"**
Cause: Too many CloudFormation `DescribeStacks` API calls fired simultaneously by multiple `${cf:...}` variable references.
Fix: Deduplicate references, batch lookups, or move shared values to SSM Parameter Store.

**Error: "No module named lambda_function"**
Cause: AWS Lambda cannot find the Python module specified in the `Handler` config field.
Fix: Confirm `Handler` is `filename.function_name` (e.g. `index.handler` → file `index.py`, function `handler`). Check for typos and ensure the file is included in the deployment package.

**Error: "The provided execution role does not have permissions to call DescribeNetworkInterfaces on EC2"**
Cause: Lambda is configured in a VPC but the execution role lacks the required EC2 permissions.
Fix: Attach the AWS managed policy `AWSLambdaVPCAccessExecutionRole` to the Lambda's IAM role.

**Error: "Function not found: arn:aws:lambda:..."**
Cause: A CloudFormation stack references a Lambda version or ARN that no longer exists (function was deleted and recreated).
Fix: Redeploy the full stack to regenerate version ARNs; avoid hardcoding version ARNs in dependent stacks.

## Resources
- Docs (npm cli tool): https://www.npmjs.com/package/aws-lambda
- Docs (PyPI package): https://pypi.org/project/aws-lambda/
- AWS Lambda Official Docs: https://docs.aws.amazon.com/lambda/latest/dg/welcome.html
- GitHub (cli-lambda-deploy): https://github.com/awspilot/cli-lambda-deploy
- GitHub (Serverless Framework): https://github.com/serverless/serverless
- AWS Lambda Runtimes Reference: https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html