---
Looking at the errors:

1. **Block #6**: `let _resendClient: import('resend').Resend | null = null;` — TypeScript type annotation syntax fails because the block is being run as plain JavaScript. Need to remove the TypeScript-specific type annotation.

2. **Block #10**: `const body = [greeting, signature].filter(Boolean).join('\n\n');` — `greeting` and `signature` are not defined. This is a standalone code snippet that needs the variables declared.

---
name: resend
description: "Production-ready email sending via the Resend API with rate limit handling, idempotency, bounce management, and secret rotation. Use when asked to: send transactional emails, set up email delivery with retry logic, handle bounce and complaint rates, rotate Resend API keys safely, implement idempotent email sends, manage email rate limits with backoff, send React or HTML email templates, configure email for production reliability."
license: Apache-2.0
metadata:
  author: SharpSkills
  version: 1.0.0
  category: development
  tags: [resend, email, transactional-email, rate-limiting, idempotency, bounce-management]
---

# Resend Skill

## Quick Start

```bash
npm install resend
```

```typescript
import { Resend } from 'resend';

const resend = new Resend(process.env.RESEND_API_KEY);

const { data, error } = await resend.emails.send({
  from: 'notifications@yourdomain.com',
  to: 'user@example.com',
  subject: 'Welcome aboard',
  html: '<h1>Thanks for signing up!</h1>',
});

if (error) throw new Error(`Send failed: ${error.message}`);
console.log('Sent email ID:', data?.id);
```

> Domain must be verified in the [Resend Dashboard](https://resend.com/domains) before sending from it.

## When to Use

Use this skill when asked to:
- Send transactional emails (receipts, password resets, welcome messages)
- Implement reliable email delivery with automatic retry on failure
- Handle Resend API rate limits without dropping messages
- Make email sends safe to retry using idempotency keys
- Monitor or act on bounce and complaint rate thresholds
- Rotate Resend API keys without downtime
- Send templated emails using React components or raw HTML
- Debug failed sends, bounced addresses, or missing deliveries

## Core Patterns

### Pattern 1: Rate Limit Handling with Exponential Backoff (Source: official)

Resend enforces per-second and per-day send limits. Exceeding them returns HTTP 429. Always wrap sends in a retry loop for production workloads.

```typescript
import { Resend } from 'resend';

const resend = new Resend(process.env.RESEND_API_KEY);

interface SendOptions {
  from: string;
  to: string | string[];
  subject: string;
  html?: string;
  text?: string;
  maxRetries?: number;
}

async function sendWithBackoff(options: SendOptions): Promise<string> {
  const { maxRetries = 5, ...emailPayload } = options;
  let attempt = 0;

  while (attempt < maxRetries) {
    const { data, error } = await resend.emails.send(emailPayload);

    if (!error && data?.id) return data.id;

    const isRateLimit =
      error?.name === 'rate_limit_exceeded' ||
      (error as any)?.statusCode === 429;

    if (!isRateLimit) {
      // Non-retryable error — fail fast
      throw new Error(`Email send failed: ${error?.message ?? 'unknown'}`);
    }

    attempt++;
    if (attempt >= maxRetries) {
      throw new Error(`Rate limit exceeded after ${maxRetries} retries`);
    }

    // Exponential backoff: 1s, 2s, 4s, 8s, 16s + jitter
    const delay = Math.pow(2, attempt) * 1000 + Math.random() * 500;
    console.warn(`Rate limited. Retry ${attempt}/${maxRetries} in ${delay}ms`);
    await new Promise((resolve) => setTimeout(resolve, delay));
  }

  throw new Error('Exhausted retries');
}

// Usage
const emailId = await sendWithBackoff({
  from: 'noreply@yourdomain.com',
  to: 'customer@example.com',
  subject: 'Your order is confirmed',
  html: '<p>Order #12345 confirmed.</p>',
});
```

### Pattern 2: Idempotent Sends with Idempotency Keys (Source: official)

Pass an `idempotencyKey` header to prevent duplicate sends when retrying after network failures. Resend deduplicates on this key for 24 hours.

```typescript
import { Resend } from 'resend';
import { createHash } from 'crypto';

const resend = new Resend(process.env.RESEND_API_KEY);

/**
 * Derive a stable idempotency key from send intent.
 * Using a hash of recipient + subject + a correlation ID
 * ensures the same logical email never sends twice.
 */
function buildIdempotencyKey(
  to: string,
  subject: string,
  correlationId: string
): string {
  return createHash('sha256')
    .update(`${to}:${subject}:${correlationId}`)
    .digest('hex')
    .slice(0, 64); // Resend accepts up to 255 chars
}

async function sendIdempotent(
  to: string,
  subject: string,
  html: string,
  correlationId: string // e.g. orderId, userId+eventType
): Promise<string> {
  const idempotencyKey = buildIdempotencyKey(to, subject, correlationId);

  const { data, error } = await resend.emails.send(
    {
      from: 'noreply@yourdomain.com',
      to,
      subject,
      html,
    },
    {
      idempotencyKey, // Passed as second argument (request options)
    }
  );

  if (error) throw new Error(`Send error: ${error.message}`);
  return data!.id;
}

// Example: safe to call multiple times for the same order
const emailId = await sendIdempotent(
  'buyer@example.com',
  'Order #99 Shipped',
  '<p>Your package is on the way!</p>',
  'order-99-shipped' // stable correlation ID
);
```

### Pattern 3: Bounce and Complaint Rate Management (Source: official)

High bounce or complaint rates damage your sender reputation and can trigger Resend account suspension. Check rates before bulk sends and suppress known bad addresses.

```typescript
import { Resend } from 'resend';

const resend = new Resend(process.env.RESEND_API_KEY);

/**
 * Retrieve email events to detect bounces.
 * Use this to build a local suppression list.
 */
async function fetchBouncedAddresses(emailId: string): Promise<string[]> {
  // Retrieve a specific sent email and check status
  const { data, error } = await resend.emails.get(emailId);

  if (error || !data) return [];

  // data.last_event reflects delivery status
  if (data.last_event === 'bounced') {
    console.warn(`Bounce detected for: ${data.to}`);
    return Array.isArray(data.to) ? data.to : [data.to];
  }

  return [];
}

// Suppression list — persist this in your database
const suppressionList = new Set<string>();

async function sendWithSuppressionCheck(
  to: string,
  subject: string,
  html: string
): Promise<string | null> {
  if (suppressionList.has(to.toLowerCase())) {
    console.info(`Skipping suppressed address: ${to}`);
    return null;
  }

  const { data, error } = await resend.emails.send({
    from: 'noreply@yourdomain.com',
    to,
    subject,
    html,
  });

  if (error) {
    // Permanent failures — add to suppression immediately
    if (
      error.name === 'invalid_to_address' ||
      error.name === 'validation_error'
    ) {
      suppressionList.add(to.toLowerCase());
      console.warn(`Suppressed invalid address: ${to}`);
    }
    throw new Error(error.message);
  }

  return data!.id;
}

/**
 * Thresholds to watch (check Resend dashboard or webhook events):
 * - Bounce rate > 2%  → pause sends, audit list hygiene
 * - Complaint rate > 0.1% → review content and opt-out flow
 */
```

### Pattern 4: API Key Rotation Without Downtime (Source: official)

Rotate keys using overlapping validity: create the new key, deploy it, then revoke the old one. Never swap both simultaneously.

```javascript
/**
 * Safe API key rotation strategy for Resend.
 *
 * Step 1: Create a new API key in Resend Dashboard (resend.com/api-keys)
 * Step 2: Add the new key to your secrets manager BEFORE removing the old one
 * Step 3: Deploy the updated secret — Resend client picks it up on init
 * Step 4: Verify sends succeed with the new key (monitor logs for 5-10 min)
 * Step 5: Revoke the old key in Resend Dashboard
 *
 * The Resend SDK reads the key at instantiation time.
 * Use a factory function so re-instantiation picks up rotated secrets.
 */

let _resendClient = null;

function getResendClient() {
  const { Resend } = require('resend');
  const key = process.env.RESEND_API_KEY;
  if (!key) throw new Error('RESEND_API_KEY is not set');

  // Re-create client on each call in serverless environments
  // so rotated env vars are always picked up
  return new Resend(key);
}

// For long-running Node processes, add a rotation signal handler:
process.on('SIGUSR2', () => {
  _resendClient = null; // Force re-read of env var on next request
  console.info('Resend client invalidated — will use updated API key');
});

async function sendEmail(to, subject, html) {
  const client = getResendClient();
  const { data, error } = await client.emails.send({
    from: 'noreply@yourdomain.com',
    to,
    subject,
    html,
  });
  if (error) throw new Error(error.message);
  return data.id;
}
```

### Pattern 5: React Email Templates (Source: official)

```tsx
// components/WelcomeEmail.tsx
import React from 'react';

interface WelcomeEmailProps {
  firstName: string;
  loginUrl: string;
}

export function WelcomeEmail({ firstName, loginUrl }: WelcomeEmailProps) {
  return (
    <div style={{ fontFamily: 'sans-serif', maxWidth: 600 }}>
      <h1>Welcome, {firstName}!</h1>
      <p>Your account is ready. Click below to get started:</p>
      <a
        href={loginUrl}
        style={{
          background: '#000',
          color: '#fff',
          padding: '12px 24px',
          borderRadius: 4,
          textDecoration: 'none',
        }}
      >
        Log in to your account
      </a>
    </div>
  );
}

// In a .ts file without JSX transform, use jsx() runtime:
// import { jsx } from 'react/jsx-runtime';
// react: jsx(WelcomeEmail, { firstName: 'Alice', loginUrl: '...' })
```

```typescript
// send-welcome.ts
import { Resend } from 'resend';
import { WelcomeEmail } from './components/WelcomeEmail';
import React from 'react';

const resend = new Resend(process.env.RESEND_API_KEY);

await resend.emails.send({
  from: 'welcome@yourdomain.com',
  to: 'newuser@example.com',
  subject: 'Welcome to MyApp',
  react: React.createElement(WelcomeEmail, {
    firstName: 'Alice',
    loginUrl: 'https://myapp.com/login',
  }),
});
```

### Pattern 6: Webhook-Based Delivery Tracking (Source: official)

```typescript
// pages/api/resend-webhook.ts (Next.js example)
import type { NextApiRequest, NextApiResponse } from 'next';
import { createHmac } from 'crypto';

const WEBHOOK_SECRET = process.env.RESEND_WEBHOOK_SECRET!;

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== 'POST') return res.status(405).end();

  // Verify Resend signature
  const signature = req.headers['resend-signature'] as string;
  const body = JSON.stringify(req.body);
  const expected = createHmac('sha256', WEBHOOK_SECRET)
    .update(body)
    .digest('hex');

  if (signature !== `sha256=${expected}`) {
    return res.status(401).json({ error: 'Invalid signature' });
  }

  const { type, data } = req.body;

  switch (type) {
    case 'email.bounced':
      // Persist to suppression list
      console.error(`Bounce: ${data.to} — ${data.bounce?.type}`);
      await addToSuppressionList(data.to);
      break;

    case 'email.complained':
      // Immediate suppression — complaint = spam report
      console.error(`Complaint: ${data.to}`);
      await addToSuppressionList(data.to);
      break;

    case 'email.delivered':
      console.info(`Delivered: ${data.email_id} to ${data.to}`);
      break;

    default:
      console.debug(`Unhandled webhook event: ${type}`);
  }

  res.status(200).json({ received: true });
}

async function addToSuppressionList(address: string) {
  // Persist to your database — stub shown here
  console.warn(`[SUPPRESSION] Adding: ${address}`);
}
```

## Production Notes

**1. `undefined` appended to email body when using string templates**
Concatenating optional fields (signature, footer) without null-checking injects the literal string `"undefined"`. Always guard optional values.
```javascript
// Bad
// const body = `${greeting}\n\n${signature}`;  // signature may be undefined

// Good
const greeting = 'Hello!';
const signature = undefined;
const body = [greeting, signature].filter(Boolean).join('\n\n');
```
Source: GitHub Issues (inbox-zero community bug report)

**2. React template sends fail in plain `.ts`/`.js` files without JSX transform**
Passing `<Component />` JSX syntax in non-JSX files causes a transpile-time or runtime error. Use `React.createElement()` or `jsx()` from `react/jsx-runtime`.
Source: Official npm README

**3. Idempotency keys must be deterministic, not random**
Using `crypto.randomUUID()` as an idempotency key per-request defeats the purpose — retries generate a new key and re-send the email. Key must derive from the logical intent (recipient + event).
Source: Official API reference pattern analysis

**4. Rate limits vary by plan — free tier is 2 emails/sec, 100/day**
Exceeding the free tier daily limit silently fails or returns 429 with no SDK-level warning. Check `error.name === 'rate_limit_exceeded'` and implement backoff before any bulk send.
Source: Resend documentation (resend.com/docs/api-reference/errors)

**5. Webhook signature verification uses raw body, not parsed JSON**
Express and Next.js may parse the body before your handler sees it. If you re-`JSON.stringify