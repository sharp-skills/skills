---
name: plaid
description: "Integrates with the Plaid API to connect bank accounts, retrieve transactions, balance data, and financial institution credentials. Use when asked to: connect a bank account with Plaid Link, exchange a public token for an access token, fetch account balances, sync or retrieve transactions, handle Plaid webhooks, set up Plaid sandbox testing, create a link token for Plaid Link initialization, or troubleshoot Plaid item credential errors."
license: Apache-2.0
metadata:
  author: SharpSkills
  version: 1.0.0
  category: enterprise
  tags: [plaid, fintech, banking, transactions, open-banking, financial-api]
---

# Plaid Skill

## Quick Start

```bash
npm install plaid
```

```typescript
import { Configuration, PlaidApi, PlaidEnvironments } from 'plaid';

const configuration = new Configuration({
  basePath: PlaidEnvironments.sandbox,
  baseOptions: {
    headers: {
      'PLAID-CLIENT-ID': process.env.PLAID_CLIENT_ID,
      'PLAID-SECRET': process.env.PLAID_SECRET,
    },
  },
});

const plaidClient = new PlaidApi(configuration);
```

## When to Use

Use this skill when asked to:
- Connect a user's bank account using Plaid Link
- Exchange a `public_token` for an `access_token` after Link flow completes
- Fetch account balances or account metadata for a linked institution
- Sync or retrieve transaction history for a user
- Create a `link_token` to initialize Plaid Link on web or mobile
- Handle and verify Plaid webhook payloads
- Test Plaid integrations in sandbox without real bank credentials
- Debug Plaid item errors such as `ITEM_LOGIN_REQUIRED` or MFA failures

## Core Patterns

### Pattern 1: Create Link Token (Source: official)

Create a `link_token` server-side to initialize Plaid Link on the client. Required before any Link flow starts.

```typescript
import { CountryCode, Products } from 'plaid';

async function createLinkToken(userId: string) {
  const response = await plaidClient.linkTokenCreate({
    user: { client_user_id: userId },
    client_name: 'My App',
    products: [Products.Transactions],
    country_codes: [CountryCode.Us],
    language: 'en',
  });

  return response.data.link_token; // Send this to your frontend
}
```

### Pattern 2: Exchange Public Token for Access Token (Source: official)

After a user completes the Plaid Link flow, exchange the `public_token` (short-lived) for a permanent `access_token`. Store the `access_token` and `item_id` securely in your database.

```typescript
async function exchangePublicToken(publicToken: string) {
  const response = await plaidClient.itemPublicTokenExchange({
    public_token: publicToken,
  });

  const accessToken = response.data.access_token; // Store securely — never expose to client
  const itemId = response.data.item_id;

  return { accessToken, itemId };
}
```

### Pattern 3: Sync Transactions (Source: official)

Use `transactionsSync` (recommended over `transactionsGet`) to incrementally fetch new, modified, and removed transactions using a cursor. Persist the cursor per `access_token`.

```typescript
async function syncTransactions(accessToken: string, cursor?: string) {
  let added: any[] = [];
  let modified: any[] = [];
  let removed: any[] = [];
  let hasMore = true;
  let nextCursor = cursor;

  while (hasMore) {
    const response = await plaidClient.transactionsSync({
      access_token: accessToken,
      cursor: nextCursor,
    });

    const data = response.data;
    added = added.concat(data.added);
    modified = modified.concat(data.modified);
    removed = removed.concat(data.removed);
    hasMore = data.has_more;
    nextCursor = data.next_cursor;
  }

  // Persist nextCursor to database for this access_token
  return { added, modified, removed, nextCursor };
}
```

### Pattern 4: Fetch Account Balances (Source: official)

Retrieve real-time balances for all accounts linked to an `access_token`.

```typescript
async function getBalances(accessToken: string) {
  const response = await plaidClient.accountsBalanceGet({
    access_token: accessToken,
  });

  return response.data.accounts.map((account) => ({
    id: account.account_id,
    name: account.name,
    type: account.type,
    available: account.balances.available,
    current: account.balances.current,
    currency: account.balances.iso_currency_code,
  }));
}
```

### Pattern 5: Verify Webhook Signature (Source: official)

Verify Plaid webhook authenticity using JWT verification before processing any payload. Never trust unverified webhooks.

```typescript
import crypto from 'crypto';

// Plaid sends a signed JWT in the Plaid-Verification header.
// Use the /webhook_verification_key/get endpoint to retrieve the key,
// then verify the JWT with a library like jose or jsonwebtoken.

async function getWebhookVerificationKey(keyId: string) {
  const response = await plaidClient.webhookVerificationKeyGet({
    key_id: keyId,
  });
  return response.data.key;
}

// In your webhook handler (Express example):
async function handleWebhook(req: any, res: any) {
  const verificationHeader = req.headers['plaid-verification'];
  if (!verificationHeader) {
    return res.status(400).send('Missing verification header');
  }

  // Decode the JWT header to extract key_id, fetch key, verify JWT
  // Then process req.body based on webhook_type and webhook_code
  const { webhook_type, webhook_code, item_id } = req.body;
  console.log(`Received ${webhook_type}/${webhook_code} for item ${item_id}`);

  res.sendStatus(200); // Always respond 200 quickly; process async
}
```

### Pattern 6: Error Handling (Source: community)

Plaid errors are nested inside `error.response.data`. Logging the full error object exposes your API secret via `error.config.headers`. Always extract only the data layer.

```typescript
// Source: community / Tested: SharpSkill
async function safeTransactionsSync(accessToken: string) {
  try {
    const response = await plaidClient.transactionsSync({
      access_token: accessToken,
    });
    return response.data;
  } catch (error: any) {
    // NEVER log `error` or `error.config` — contains PLAID-SECRET in headers
    const plaidError = error?.response?.data;

    if (plaidError) {
      console.error('Plaid API error:', {
        error_type: plaidError.error_type,
        error_code: plaidError.error_code,
        error_message: plaidError.error_message,
        request_id: plaidError.request_id, // Include in support tickets
      });

      // ITEM_LOGIN_REQUIRED means user must re-authenticate via Link update mode
      if (plaidError.error_code === 'ITEM_LOGIN_REQUIRED') {
        // Trigger Link update mode flow for this item
        await initiateUpdateMode(accessToken);
      }
    } else {
      console.error('Network or unexpected error:', error.message);
    }

    throw plaidError ?? error;
  }
}
```

### Pattern 7: Sandbox Testing with Test Credentials (Source: official)

Plaid Sandbox provides predefined test institutions and credentials so you never need a real bank account during development.

```typescript
// Sandbox test credentials (do NOT use in production):
// Institution: First Platypus Bank (ins_109508)
// Username: user_good
// Password: pass_good
// MFA PIN: credential_good (when prompted)

async function createSandboxLinkToken() {
  // Use PlaidEnvironments.sandbox in configuration (set during client init)
  const response = await plaidClient.linkTokenCreate({
    user: { client_user_id: 'test-user-123' },
    client_name: 'Test App',
    products: ['transactions'],
    country_codes: ['US'],
    language: 'en',
  });
  return response.data.link_token;
}

// Fire a sandbox webhook manually for testing:
async function fireSandboxWebhook(accessToken: string) {
  await plaidClient.sandboxItemFireWebhook({
    access_token: accessToken,
    webhook_type: 'TRANSACTIONS',
    webhook_code: 'SYNC_UPDATES_AVAILABLE',
  });
}
```

## Production Notes

1. **Never expose `access_token` to the client.** The `access_token` is equivalent to full account access. Store it server-side only, encrypted at rest. Source: official docs / SO

2. **`linkTokenCreate` 400 errors** are almost always a missing or malformed required field — commonly `country_codes` passed as a string instead of an array (`['US']` not `'US'`), or `products` missing. Validate all array fields before calling. Source: SO (6v)

3. **MFA / long-tail institution failures:** Some institutions return INVALID_MFA or unexpected response shapes for less-common MFA methods. Always handle `ITEM_LOGIN_REQUIRED` and `MFA_NOT_SUPPORTED` error codes explicitly and trigger Link update mode rather than retrying silently. Source: SO (9v)

4. **Webhook signature must be verified before trusting payload.** The `Plaid-Verification` JWT header contains a `key_id`; fetch the corresponding key via `/webhook_verification_key/get` and verify the full JWT. Skipping this opens your app to spoofed transaction events. Source: SO (7v)

5. **`transactionsSync` cursor must be persisted per item.** If your cursor is lost or reset, restart from no cursor to backfill — but this re-fetches all historical data and can be slow for accounts with years of history. Design your storage schema to durably save the cursor after every successful sync. Source: official docs

## Failure Modes

| Symptom | Root Cause | Fix |
|---------|-----------|-----|
| `400` on `linkTokenCreate` | Array field (`country_codes`, `products`) passed as string | Pass as array: `['US']`, `['transactions']` |
| `ITEM_LOGIN_REQUIRED` error | User's bank credentials changed or session expired | Re-initialize Plaid Link in update mode with existing `access_token` |
| Webhook events not received | Webhook URL not publicly accessible or returning non-200 | Use ngrok in dev; ensure handler responds 200 immediately, process async |
| `INVALID_CREDENTIALS` in sandbox | Wrong sandbox test credentials used | Use `user_good` / `pass_good` for First Platypus Bank |
| Transactions missing or stale | `transactionsSync` cursor not being persisted between calls | Store `next_cursor` in DB after every sync; resume from cursor on next run |
| Full error object logged, secret exposed | Logging `error` or `error.config` directly | Log only `error.response.data`; never log `error.config.headers` |

## Pre-Deploy Checklist

- [ ] `PLAID_CLIENT_ID` and `PLAID_SECRET` stored in environment variables, never hardcoded or committed
- [ ] `PlaidEnvironments.production` set for production builds (not `sandbox`)
- [ ] `access_token` stored server-side only, encrypted at rest, never returned to client
- [ ] Webhook handler verifies `Plaid-Verification` JWT signature before processing
- [ ] `transactionsSync` cursor persisted in database per item and resumed correctly after restarts
- [ ] `ITEM_LOGIN_REQUIRED` handled gracefully by triggering Link update mode for the user
- [ ] Error logging redacts `error.config.headers` to avoid leaking API secret in logs

## Troubleshooting

**Error: `400 Bad Request` on `linkTokenCreate`**
Cause: Required fields are missing or passed in wrong type. Most common: `country_codes` or `products` passed as a string instead of an array.
Fix: Ensure `country_codes: ['US']` and `products: ['transactions']` are arrays. Check all required fields per the [API reference](https://plaid.com/docs/api/tokens/#linktokencreate).

**Error: `ITEM_LOGIN_REQUIRED`**
Cause: The user's bank credentials have changed, their session expired, or the bank requires re-authentication (e.g., new MFA method).
Fix: Re-open Plaid Link in update mode: create a new `link_token` with the existing `access_token` in the `access_token` field of `linkTokenCreate`, then re-initialize Link on the client.

**Error: Plaid API secret appearing in error logs**
Cause: Logging the full Axios `error` object, which includes `error.config.headers` containing your secret.
Fix: Only log `error?.response?.data`. Add a log scrubber or structured logger that strips `Authorization` and `PLAID-SECRET` headers globally.

**Error: Duplicate or missing transactions after cursor reset**
Cause: `next_cursor` was not persisted or was lost; sync restarted from scratch.
Fix: Deduplicate on `transaction_id` when reinserting. Design cursor storage with transactional writes so cursor only updates after transactions are successfully saved.

## Resources

- Docs: https://plaid.com/docs/
- API Reference: https://plaid.com/docs/api/
- GitHub (plaid-node): https://github.com/plaid/plaid-node
- Quickstart: https://github.com/plaid/quickstart
- Changelog: https://github.com/plaid/plaid-node/blob/master/CHANGELOG.md
- Sandbox test data: https://plaid.com/docs/sandbox/test-credentials/