---
name: twilio-production
description: "Production-grade Twilio integration covering webhook signature validation, retry logic with exponential backoff, delivery failure handling, rate limiting, and throughput queue management. Use when asked to: validate Twilio webhook signatures, retry failed SMS or voice requests, handle undeliverable numbers, implement rate limiting for bulk messaging, manage message queues and throughput, authenticate incoming Twilio webhooks, handle 429 Too Many Requests errors from Twilio, or build reliable SMS delivery pipelines."
license: Apache-2.0
metadata:
  author: SharpSkills
  version: 1.0.0
  category: development
  tags: [twilio, sms, webhooks, rate-limiting, retry, authentication, messaging]
---

# Twilio Production Skill

## Quick Start

```bash
npm install twilio
# or
pip install twilio
```

```javascript
// Node.js — client with auto-retry enabled (official)
const client = require('twilio')(
  process.env.TWILIO_ACCOUNT_SID,
  process.env.TWILIO_AUTH_TOKEN,
  { autoRetry: true, maxRetries: 3 }
);

const message = await client.messages.create({
  body: 'Hello from production',
  to: '+15558675309',
  from: process.env.TWILIO_PHONE_NUMBER,
});
console.log(message.sid, message.status);
```

## When to Use

Use this skill when asked to:
- Validate or verify incoming Twilio webhook request signatures
- Retry failed Twilio API requests with exponential backoff
- Handle undeliverable numbers, failed deliveries, or error status callbacks
- Implement rate limiting or throttle bulk SMS sends
- Build a message queue to manage Twilio throughput limits
- Authenticate webhooks from Twilio to prevent spoofed requests
- Handle Twilio error 429 Too Many Requests gracefully
- Track message delivery status and parse status callbacks
- Send SMS at scale without hitting carrier or Twilio limits
- Build fault-tolerant messaging pipelines with dead-letter handling

## Core Patterns

### Pattern 1: Webhook Signature Validation (Source: official)

Twilio signs every webhook request with an HMAC-SHA1 of the request URL and POST parameters using your Auth Token. Validate before processing any payload — spoofed requests are the most common production security failure.

```javascript
// Express middleware — validates every incoming Twilio webhook
const twilio = require('twilio');
const express = require('express');
const app = express();

// Must use raw URL-encoded body for signature validation
app.use('/webhook', express.urlencoded({ extended: false }));

app.post('/webhook/sms', (req, res) => {
  const authToken = process.env.TWILIO_AUTH_TOKEN;

  // Use the full public URL Twilio called — scheme + host + path + query string
  const webhookUrl = `https://${req.hostname}${req.originalUrl}`;

  const isValid = twilio.validateRequest(
    authToken,
    req.headers['x-twilio-signature'],
    webhookUrl,
    req.body  // parsed urlencoded body (key-value pairs)
  );

  if (!isValid) {
    console.warn('Invalid Twilio signature — possible spoofed request');
    return res.status(403).send('Forbidden');
  }

  // Safe to process
  const from = req.body.From;
  const body = req.body.Body;
  console.log(`Validated message from ${from}: ${body}`);

  const twiml = new twilio.twiml.MessagingResponse();
  twiml.message('Got your message!');
  res.type('text/xml').send(twiml.toString());
});
```

```python
# Python / Flask equivalent — webhook signature validation
from flask import Flask, request, abort
from twilio.request_validator import RequestValidator
import os

app = Flask(__name__)

@app.route('/webhook/sms', methods=['POST'])
def sms_webhook():
    validator = RequestValidator(os.environ['TWILIO_AUTH_TOKEN'])

    # Reconstruct full URL exactly as Twilio called it
    url = request.url
    post_vars = request.form.to_dict()
    signature = request.headers.get('X-Twilio-Signature', '')

    if not validator.validate(url, post_vars, signature):
        abort(403)

    from_number = request.form.get('From')
    body = request.form.get('Body')
    print(f'Validated message from {from_number}: {body}')
    return '<Response><Message>Got it!</Message></Response>', 200, {'Content-Type': 'text/xml'}
```

> **Critical:** The URL used for validation must match byte-for-byte what Twilio called. Behind a proxy or load balancer, reconstruct from `X-Forwarded-Proto` and `X-Forwarded-Host` headers. Any mismatch causes every valid webhook to fail validation.

### Pattern 2: Retry Logic with Exponential Backoff (Source: official)

Twilio's SDK auto-retry handles 429s, but custom retry logic is needed for network failures, 5xx errors, and application-level retries on unconfirmed deliveries.

```javascript
// Auto-retry via SDK (official) — handles 429 only
const client = require('twilio')(
  process.env.TWILIO_ACCOUNT_SID,
  process.env.TWILIO_AUTH_TOKEN,
  { autoRetry: true, maxRetries: 4 }
);

// Custom exponential backoff for broader failure types
async function sendWithRetry(to, body, maxAttempts = 5) {
  const baseDelayMs = 500;

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      const message = await client.messages.create({
        body,
        to,
        from: process.env.TWILIO_PHONE_NUMBER,
      });

      console.log(`Sent on attempt ${attempt}: ${message.sid}`);
      return message;

    } catch (err) {
      const isRetryable =
        err.status === 429 ||          // Rate limited
        err.status >= 500 ||           // Twilio server error
        err.code === 'ECONNRESET' ||   // Network reset
        err.code === 'ETIMEDOUT';      // Network timeout

      const isTerminal =
        err.code === 21211 ||   // Invalid 'To' number
        err.code === 21610 ||   // Recipient opted out (STOP)
        err.code === 21408 ||   // Region permission not enabled
        err.code === 21614;     // 'To' number not SMS-capable

      if (isTerminal) {
        console.error(`Terminal error for ${to} — code ${err.code}: ${err.message}`);
        throw err; // Do not retry — escalate to dead-letter queue
      }

      if (!isRetryable || attempt === maxAttempts) {
        console.error(`Failed after ${attempt} attempts:`, err.message);
        throw err;
      }

      // Exponential backoff with full jitter
      const delay = Math.min(
        baseDelayMs * Math.pow(2, attempt - 1) + Math.random() * 200,
        30000 // cap at 30 seconds
      );
      console.warn(`Attempt ${attempt} failed (${err.status || err.code}). Retrying in ${Math.round(delay)}ms…`);
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
}
```

### Pattern 3: Rate Limiting and Throughput Queue (Source: official + community)

Twilio enforces per-number throughput: long codes send ~1 SMS/second, Alphanumeric Sender IDs vary by country, and short codes handle ~100/second. Exceeding limits triggers 429 errors and carrier filtering.

```javascript
// Token-bucket queue for bulk sends — respects per-number throughput
class TwilioMessageQueue {
  constructor({ messagesPerSecond = 1, client, from }) {
    this.rateMs = 1000 / messagesPerSecond; // ms between sends
    this.client = client;
    this.from = from;
    this.queue = [];
    this.processing = false;
  }

  enqueue(to, body) {
    return new Promise((resolve, reject) => {
      this.queue.push({ to, body, resolve, reject });
      if (!this.processing) this._processQueue();
    });
  }

  async _processQueue() {
    this.processing = true;

    while (this.queue.length > 0) {
      const { to, body, resolve, reject } = this.queue.shift();

      try {
        const message = await this.client.messages.create({
          body,
          to,
          from: this.from,
        });
        resolve(message);
      } catch (err) {
        reject(err);
      }

      // Enforce rate limit between sends
      if (this.queue.length > 0) {
        await new Promise(resolve => setTimeout(resolve, this.rateMs));
      }
    }

    this.processing = false;
  }
}

// Usage
const queue = new TwilioMessageQueue({
  messagesPerSecond: 1,  // long code: 1/sec; short code: up to 100/sec
  client,
  from: process.env.TWILIO_PHONE_NUMBER,
});

const recipients = ['+15550001111', '+15550002222', '+15550003333'];
const results = await Promise.allSettled(
  recipients.map(to => queue.enqueue(to, 'Your notification here'))
);

results.forEach((result, i) => {
  if (result.status === 'rejected') {
    console.error(`Failed for ${recipients[i]}:`, result.reason.message);
  }
});
```

### Pattern 4: Delivery Failure Handling via Status Callback (Source: official)

Message status updates arrive asynchronously. Poll or use status callbacks to detect `failed` and `undelivered` states and route to dead-letter handling.

```javascript
// Send with status callback URL
const message = await client.messages.create({
  body: 'Important notification',
  to: '+15558675309',
  from: process.env.TWILIO_PHONE_NUMBER,
  statusCallback: 'https://yourapp.com/webhook/status',
});

// Status callback endpoint — receives delivery receipts
app.post('/webhook/status', express.urlencoded({ extended: false }), async (req, res) => {
  // Always validate signature on status callbacks too
  const isValid = twilio.validateRequest(
    process.env.TWILIO_AUTH_TOKEN,
    req.headers['x-twilio-signature'],
    `https://${req.hostname}${req.originalUrl}`,
    req.body
  );
  if (!isValid) return res.status(403).send('Forbidden');

  const { MessageSid, MessageStatus, ErrorCode, To } = req.body;

  // Terminal failure states — do not retry
  const terminalFailures = ['failed', 'undelivered'];

  if (terminalFailures.includes(MessageStatus)) {
    console.error(`Delivery failure — SID: ${MessageSid}, To: ${To}, ErrorCode: ${ErrorCode}`);

    // Route to dead-letter handling
    await handleDeliveryFailure({
      sid: MessageSid,
      to: To,
      errorCode: ErrorCode,
      // ErrorCode 30003 = unreachable, 30004 = blocked, 30005 = unknown destination
      // ErrorCode 30006 = landline/non-SMS capable, 30007 = carrier violation
      // ErrorCode 21610 = opt-out (STOP) — do not re-attempt ever
    });
  }

  res.sendStatus(204);
});

async function handleDeliveryFailure({ sid, to, errorCode }) {
  const optOutCodes = [21610, 21611, 21612]; // Opt-out errors — never retry
  const badNumberCodes = [30003, 30006, 21211]; // Invalid or non-SMS numbers

  if (optOutCodes.includes(Number(errorCode))) {
    // Remove from all future send lists — TCPA compliance
    await markNumberOptedOut(to);
  } else if (badNumberCodes.includes(Number(errorCode))) {
    await markNumberUndeliverable(to);
  } else {
    // Log for manual review or conditional retry
    await logFailureForReview({ sid, to, errorCode });
  }
}
```

### Pattern 5: Error Handling for Regional Permission Errors (Source: community)

A common production issue is sending to numbers in regions not enabled in your Twilio console. Error 21408 ("Permission to send an SMS has not been enabled for the region indicated by the 'To' number") requires console action, not code changes.

```javascript
// Source: community / # Tested: SharpSkill
// Handles region permission errors with actionable logging
async function sendSMSSafe(to, body) {
  try {
    return await client.messages.create({ body, to, from: process.env.TWILIO_PHONE_NUMBER });
  } catch (err) {
    switch (err.code) {
      case 21408:
        // Geographic permission not enabled — must enable in Twilio console:
        // Console > Messaging > Settings > Geo Permissions
        console.error(`Region not enabled for ${to}. Enable at: https://console.twilio.com/us1/develop/sms/settings/geo-permissions`);
        break;
      case 21211:
        console.error(`Invalid phone number format: ${to}. Use E.164 format (+15551234567)`);
        break;
      case 21610:
        console.error(`${to} has opted out (STOP). Remove from your list — TCPA violation risk if resent.`);
        break;
      case 21614:
        console.error(`${to} is not SMS-capable (likely a landline). Mark as undeliverable.`);
        break;
      case 20003:
        console.error('Authentication failed. Check TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN env vars.');
        break;
      default:
        console.error(`Twilio error ${err.code}: ${err.message}`);
    }
    throw err;
  }
}
```

## Production Notes

**1. Webhook URL must match exactly for signature validation**
The most common production failure: signature validation fails on every request. Root cause is usually an HTTP vs HTTPS mismatch, a missing or extra trailing slash, query string differences, or a reverse proxy stripping/modifying headers. Reconstruct the URL from `X-Forwarded-Proto` and `X-Forwarded-Host` if behind a proxy. Never use `req.url` — always use the full public URL. Source: SO (25+ votes, multiple reports)

**2. Opt-out compliance is not optional**
Error code 21610 means the recipient sent STOP. Under TCPA, resending to opted-out numbers is a legal violation. Maintain a persistent opt-out list and check it before every send. Never auto-retry on 21610. Source: GitHub Issues / community compliance discussions

**3. Trial accounts block non-verified numbers**
Error "permission to send to region" on trial accounts often means the destination number is not verified in the Twilio console, not a geo-permission issue. Upgrade or verify the destination number. Source: SO (110 votes)

**4. Long code throughput limits cause silent carrier filtering**
Sending faster than 1 SMS/second per long code number doesn't always produce a 429 — carriers silently drop messages. Use a queue (Pattern 3) and monitor delivery rates, not just send success rates. Source: community messaging best-practices

**5. Status callbacks require their own signature validation**
Many teams validate inbound SMS webhooks but skip validation on `/webhook/status` endpoints. Spoofed status callbacks can mark messages as delivered when they're not, corrupting delivery analytics. Apply the same validation middleware to all Twilio-originated endpoints. Source: SharpSkill analysis of common implementations

## Failure Modes

| Symptom | Root Cause | Fix |
|---------|-----------|-----|
| 403 on all incoming webhooks | Signature validation URL mismatch (HTTP vs HTTPS, trailing slash, proxy stripping headers) | Reconstruct full public URL from forwarded headers; log `webhookUrl` and compare with Twilio console URL |
| Error 21408: