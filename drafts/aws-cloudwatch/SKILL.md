---
name: aws-cloudwatch
description: "Puts custom metrics into AWS CloudWatch using a simple wrapper around putMetricData. Use when user asks to: send custom metrics to CloudWatch, track application performance in AWS, publish metric data with dimensions, record aggregated statistics (min/max/sum/count), instrument Node.js apps with CloudWatch metrics, set up custom namespaces for monitoring, send dimensional metrics to AWS, or integrate app telemetry with CloudWatch dashboards."
license: Apache-2.0
metadata:
  author: SharpSkills
  version: 1.0.0
  category: devops
  tags: [aws-cloudwatch, aws, metrics, monitoring, cloudwatch, putMetricData, observability]
---

# AWS-CloudWatch Skill

## Quick Start

```bash
npm install aws-cloudwatch
```

```javascript
'use strict';

// config.json — create once, reuse everywhere
const config = {
  region: "us-east-1",
  namespace: "MyApp/Production",
  metrics: {
    requestDuration: { unit: "Milliseconds" },
    errorCount:      { unit: "Count" },
    throughput:      { unit: "Bytes/Second" }
  }
};

// app.js — initialize once at startup
require('aws-cloudwatch')(config);

// anywhere else in your app
const cloudWatch = require('aws-cloudwatch');

cloudWatch.put('requestDuration', 142)
  .then(data => console.log('Metric sent:', data))
  .catch(err => console.error('Failed:', err));
```

> **AWS credentials** must be available via environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`), an IAM role, or `~/.aws/credentials`. The IAM principal needs `cloudwatch:PutMetricData` permission.

---

## When to Use

Use this skill when asked to:

- Send a custom metric value to AWS CloudWatch
- Track request latency, error rates, or throughput from a Node.js service
- Publish metric data with one or more dimensions (e.g., per-region, per-environment)
- Record aggregated statistics (Maximum, Minimum, Sum, SampleCount) without sending raw data points
- Set up a custom CloudWatch namespace for an application
- Instrument an Express, Lambda, or background-worker app with CloudWatch telemetry
- Replace or supplement AWS X-Ray with lightweight metric publishing
- Build a CloudWatch dashboard backed by custom application metrics

---

## Core Patterns

### Pattern 1: Basic Metric — Scalar Value (Source: official)

Sends a single numeric value to a named metric. If no value is provided, `0` is sent by default.

```javascript
'use strict';
const cloudWatch = require('aws-cloudwatch');

// Send a specific value
cloudWatch.put('requestDuration', 142)
  .then(data  => console.log('OK', data))
  .catch(err  => console.error('ERR', err.message));

// Send default value (0) — useful for heartbeat metrics
cloudWatch.put('requestDuration')
  .then(data  => console.log('Heartbeat sent'))
  .catch(err  => console.error('ERR', err.message));
```

---

### Pattern 2: Metric with Dimensions (Source: official)

Dimensions slice a metric into sub-streams (e.g., per environment, per host). Pass an array of single-key objects.

```javascript
'use strict';
const cloudWatch = require('aws-cloudwatch');

// Single dimension
cloudWatch.put('errorCount', 3, [{ Environment: 'production' }])
  .then(data => console.log('Sent with dimension'))
  .catch(err => console.error(err));

// Multiple dimension values for the same metric name
cloudWatch.put('errorCount', 1, [{ Environment: 'staging' }]);
cloudWatch.put('errorCount', 0, [{ Environment: 'production' }]);

// Multiple dimensions on one data point
cloudWatch.put('throughput', 2048, [
  { Environment: 'production' },
  { Region: 'us-east-1' }
]);
```

---

### Pattern 3: Aggregated Statistics (Source: official)

Send pre-aggregated data instead of individual data points to reduce API calls and cost. The stats object must contain `Maximum`, `Minimum`, `Sum`, and `SampleCount`.

```javascript
'use strict';
const cloudWatch = require('aws-cloudwatch');

const stats = {
  Maximum:     420,
  Minimum:     10,
  SampleCount: 100,
  Sum:         18500
};

// No dimension — namespace-level aggregate
cloudWatch.put('requestDuration', stats)
  .then(data => console.log('Aggregated stats sent', data));

// With dimension — aggregate per service
cloudWatch.put('requestDuration', stats, [{ Service: 'auth-service' }])
  .then(data => console.log('Per-service aggregate sent'));
```

---

### Pattern 4: Initialization & Config File (Source: official)

Centralize config in a JSON file and initialize the module once at process startup.

```json
// cloudwatch-config.json
{
  "region": "eu-west-1",
  "namespace": "MyApp/API",
  "metrics": {
    "requestDuration": { "unit": "Milliseconds" },
    "errorCount":      { "unit": "Count" },
    "payloadSize":     { "unit": "Bytes" },
    "cacheHitRate":    { "unit": "Percent" }
  }
}
```

```javascript
// app.js — run once before any require('aws-cloudwatch') calls
'use strict';
const config = require('./cloudwatch-config.json');
require('aws-cloudwatch')(config); // initializes singleton with credentials + namespace
```

**Available units:**
`Seconds | Microseconds | Milliseconds | Bytes | Kilobytes | Megabytes | Gigabytes | Terabytes | Bits | Kilobits | Megabits | Gigabits | Terabits | Percent | Count | Bytes/Second | Kilobytes/Second | Megabytes/Second | Gigabytes/Second | Terabytes/Second | Bits/Second | Kilobits/Second | Megabits/Second | Gigabits/Second | Terabits/Second | Count/Second | None`

---

### Pattern 5: Error Handling — Missing or Invalid Metric (Source: official)

`cloudWatch.put()` throws **synchronously** if the metric name is absent or not declared in config. Wrap in try/catch before the `.then()` chain.

```javascript
'use strict';
const cloudWatch = require('aws-cloudwatch');

// Source: community / # Tested: SharpSkill
function safeput(metricName, value, dimensions) {
  try {
    return cloudWatch.put(metricName, value, dimensions);
  } catch (err) {
    // Thrown synchronously — .catch() on the promise won't catch these
    console.error(`[CloudWatch] Metric error: ${err.message}`);
    return Promise.reject(err);
  }
}

// Will throw: no metricName
safeput();                        // → "metricName is required"

// Will throw: metric not in config
safeput('undeclaredMetric', 99);  // → "undeclaredMetric is not a valid metric"

// Will resolve: metric is declared in config
safeput('errorCount', 5, [{ Env: 'prod' }])
  .then(data => console.log('Sent'))
  .catch(err => console.error('AWS error:', err.stack));
```

---

## Production Notes

1. **Initialize exactly once, before any `require` calls downstream.**  
   The module is a singleton. Calling `require('aws-cloudwatch')(config)` a second time overwrites the namespace and credentials. Initialize in `app.js` or your process entry point before any worker modules load.  
   Source: README (official)

2. **`put()` throws synchronously for config errors — `.catch()` will not intercept them.**  
   Invalid metric names and missing arguments throw at call time, not as rejected promises. Always wrap `put()` calls in `try/catch` in production code.  
   Source: README (official sample), GitHub Issues (community pattern)

3. **IAM policy must include `cloudwatch:PutMetricData` for the target namespace.**  
   Overly restrictive IAM roles will cause silent 403 failures returned as rejected promises. Scope the resource to `arn:aws:cloudwatch:REGION:ACCOUNT:*` or restrict to specific namespaces using condition keys.  
   Source: AWS IAM docs (official)

4. **High-frequency metrics incur CloudWatch API costs.**  
   Each `put()` call invokes `PutMetricData`. At scale, batch using the aggregated-statistics pattern (Pattern 3) or buffer values locally and flush on an interval to reduce API calls and cost.  
   Source: Reddit r/devops (community), AWS CloudWatch pricing docs

5. **Dimension cardinality explosion degrades CloudWatch performance.**  
   Using high-cardinality values (e.g., user IDs, request IDs) as dimension values creates an unbounded number of metric streams, making dashboards unusable and dramatically increasing cost. Use low-cardinality values only (environment, region, service name).  
   Source: AWS CloudWatch best practices (official), r/devops community

---

## Failure Modes

| Symptom | Root Cause | Fix |
|---------|------------|-----|
| `Error: [metricName] is not a valid metric` thrown synchronously | Metric name not declared in the `metrics` block of config | Add the metric to your config JSON with a valid `unit` before calling `put()` |
| `put()` silently sends to wrong namespace | `require('aws-cloudwatch')(config)` called multiple times with different configs | Call initializer once only; store config reference outside module if needed |
| `AccessDeniedException` from AWS SDK | IAM role/user missing `cloudwatch:PutMetricData` permission | Attach a policy granting `cloudwatch:PutMetricData` on the target namespace |
| Metrics appear in CloudWatch but dashboard shows no data | Dimension mismatch — metric sent with dimension, queried without (or vice versa) | Ensure dashboard filter dimensions exactly match those sent via `put()` |
| `TypeError` or unhandled rejection in production | Synchronous throw from `put()` not caught — `.catch()` only handles promise rejections | Wrap all `put()` calls in `try/catch`; re-throw or log as appropriate |
| High AWS bill from CloudWatch | Too many `PutMetricData` calls at high frequency | Switch to aggregated stats pattern; batch with local accumulator + interval flush |

---

## Pre-Deploy Checklist

- [ ] `require('aws-cloudwatch')(config)` called once and only once at process entry point
- [ ] All metric names used in `put()` calls are declared in the config `metrics` block
- [ ] AWS credentials available via environment variables, IAM role, or `~/.aws/credentials`
- [ ] IAM principal has `cloudwatch:PutMetricData` permission scoped to the correct namespace/region
- [ ] All `put()` calls wrapped in `try/catch` to catch synchronous config errors
- [ ] Dimension values are low-cardinality (environment, region, service — not user IDs or request IDs)
- [ ] High-frequency paths use aggregated statistics (`{Maximum, Minimum, Sum, SampleCount}`) not scalar `put()` per event

---

## Troubleshooting

**Error: `TypeError: cloudWatch.put is not a function`**  
Cause: Module required before initialization — `require('aws-cloudwatch')` returns the uninitialized function, not the instance.  
Fix: Ensure `require('aws-cloudwatch')(config)` runs in your entry file before any downstream module calls `require('aws-cloudwatch')`.

---

**Error: `[metricName] is not a valid metric` (synchronous throw)**  
Cause: The metric name passed to `put()` is not listed in the `metrics` key of the config object used during initialization.  
Fix: Add the metric to your config JSON:
```json
"metrics": {
  "yourMetricName": { "unit": "Count" }
}
```

---

**Error: `AccessDeniedException` / `AuthorizationError` in rejected promise**  
Cause: The AWS principal lacks `cloudwatch:PutMetricData` permission.  
Fix: Attach this IAM policy to the role or user:
```json
{
  "Effect": "Allow",
  "Action": "cloudwatch:PutMetricData",
  "Resource": "*"
}
```
Optionally restrict by namespace using a `Condition` block with `cloudwatch:namespace`.

---

**Metrics sent but not visible in CloudWatch console**  
Cause 1: Wrong region — config `region` does not match the console region selector.  
Fix: Switch the console region to match the `region` in config.  
Cause 2: Dimension mismatch — metric sent with dimensions but queried without (or vice versa).  
Fix: In the CloudWatch console, add the exact dimension name/value used in `put()` to the metric filter.

---

## Resources

- Docs: https://docs.aws.amazon.com/AmazonCloudWatch/latest/APIReference/API_PutMetricData.html
- npm: https://www.npmjs.com/package/aws-cloudwatch
- GitHub: https://github.com/arlyon/aws-cloudwatch
- AWS IAM for CloudWatch: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/auth-and-access-control-cw.html
- CloudWatch Pricing: https://aws.amazon.com/cloudwatch/pricing/