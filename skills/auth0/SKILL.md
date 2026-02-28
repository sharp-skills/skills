---
name: auth0
description: "Add authentication and authorization to apps using Auth0. Use when asked to: integrate Auth0 login, implement Auth0 with Next.js/React/Node, handle JWT tokens from Auth0, set up Auth0 rules or actions, configure social logins, protect API routes with Auth0, or implement Auth0 machine-to-machine auth."
license: Apache-2.0
compatibility:
  - node >= 18
metadata:
  author: SharpSkills
  version: 1.1.0
  category: development
  tags: [auth0, authentication, authorization, jwt, oauth2, oidc, security, nodejs]
trace_id: 7b1295ad24e5
generated_at: '2026-02-28T22:43:17'
generator: sharpskill-v1.0 (legacy)
---

# Auth0

Auth0 is an identity platform providing authentication and authorization as a service. Drop-in login for web, mobile, and APIs — supports social logins, MFA, SSO, and enterprise connections.

## Installation

```bash
# Next.js / React
npm install @auth0/nextjs-auth0

# Node.js API
npm install express-oauth2-jwt-bearer

# Node.js management (Admin API)
npm install auth0
```

## When to Use
- "Add login to my Next.js app with Auth0"
- "Protect Express API routes with Auth0 JWT"
- "Implement Google/GitHub login via Auth0"
- "Set up Auth0 machine-to-machine authentication"
- "Get user profile from Auth0"
- "Configure Auth0 roles and permissions"

## Core Patterns

### Pattern 1: Next.js — Auth0 Login Flow (App Router)

```typescript
// lib/auth0.ts
import { Auth0Client } from '@auth0/nextjs-auth0/server';

export const auth0 = new Auth0Client({
  domain: process.env.AUTH0_DOMAIN!,
  clientId: process.env.AUTH0_CLIENT_ID!,
  clientSecret: process.env.AUTH0_CLIENT_SECRET!,
  appBaseURL: process.env.APP_BASE_URL!,
  secret: process.env.AUTH0_SECRET!, // openssl rand -hex 32
  authorizationParameters: {
    scope: 'openid profile email',
  },
});
```

```typescript
// app/api/auth/[auth0]/route.ts
import { auth0 } from '@/lib/auth0';

export const GET = auth0.handler;
```

```typescript
// app/dashboard/page.tsx — protected page
import { auth0 } from '@/lib/auth0';
import { redirect } from 'next/navigation';

export default async function Dashboard() {
  const session = await auth0.getSession();

  if (!session) {
    redirect('/api/auth/login');
  }

  return (
    <div>
      <h1>Welcome, {session.user.name}</h1>
      <p>Email: {session.user.email}</p>
      <a href="/api/auth/logout">Logout</a>
    </div>
  );
}
```

```
# .env.local
AUTH0_DOMAIN=your-tenant.auth0.com
AUTH0_CLIENT_ID=your_client_id
AUTH0_CLIENT_SECRET=your_client_secret
APP_BASE_URL=http://localhost:3000
AUTH0_SECRET=long_random_secret_32_chars
```

### Pattern 2: Express — Protect API Routes with JWT

```typescript
import express from 'express';
import { auth } from 'express-oauth2-jwt-bearer';

const app = express();

// JWT middleware — validates Auth0 access tokens
const checkJwt = auth({
  audience: 'https://api.myapp.com',  // Your API audience in Auth0
  issuerBaseURL: `https://${process.env.AUTH0_DOMAIN}/`,
  tokenSigningAlg: 'RS256',
});

// Public route
app.get('/health', (req, res) => res.json({ status: 'ok' }));

// Protected route
app.get('/api/profile', checkJwt, (req, res) => {
  // req.auth.payload contains the decoded JWT claims
  const { sub, email } = req.auth!.payload as { sub: string; email: string };
  res.json({ userId: sub, email });
});

// Protected route with permission check
app.delete('/api/users/:id', checkJwt, (req, res) => {
  const permissions = (req.auth!.payload['permissions'] as string[]) || [];
  if (!permissions.includes('delete:users')) {
    return res.status(403).json({ error: 'Insufficient permissions' });
  }
  // proceed with deletion
  res.json({ deleted: req.params.id });
});

app.listen(3000);
```

### Pattern 3: Machine-to-Machine (M2M) Auth

```typescript
// Server-to-server calls — no user involved
// Used for cron jobs, microservices, background workers

async function getM2MToken(): Promise<string> {
  const response = await fetch(`https://${process.env.AUTH0_DOMAIN}/oauth/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      client_id: process.env.AUTH0_M2M_CLIENT_ID,
      client_secret: process.env.AUTH0_M2M_CLIENT_SECRET,
      audience: 'https://api.myapp.com',
      grant_type: 'client_credentials',
    }),
  });

  const { access_token, expires_in } = await response.json();
  return access_token;
}

// Cache the token — don't fetch on every request
let cachedToken: { token: string; expiresAt: number } | null = null;

async function getCachedToken(): Promise<string> {
  if (cachedToken && Date.now() < cachedToken.expiresAt - 30_000) {
    return cachedToken.token;
  }
  const token = await getM2MToken();
  cachedToken = { token, expiresAt: Date.now() + 86400_000 }; // 24h
  return token;
}

// Call protected internal API
async function callInternalApi(endpoint: string) {
  const token = await getCachedToken();
  return fetch(`https://api.myapp.com${endpoint}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
}
```

### Pattern 4: Auth0 Management API — Manage Users

```typescript
import { ManagementClient } from 'auth0';

const management = new ManagementClient({
  domain: process.env.AUTH0_DOMAIN!,
  clientId: process.env.AUTH0_MGMT_CLIENT_ID!,
  clientSecret: process.env.AUTH0_MGMT_CLIENT_SECRET!,
});

// Get user by ID
const user = await management.users.get({ id: 'auth0|64abc123' });
console.log(user.data.email);

// Update user metadata
await management.users.update(
  { id: 'auth0|64abc123' },
  { user_metadata: { plan: 'pro', onboarded: true } }
);

// Assign role to user
await management.users.assignRoles(
  { id: 'auth0|64abc123' },
  { roles: ['rol_abc123'] }
);

// Search users
const users = await management.users.getAll({
  q: 'email:john@example.com',
  search_engine: 'v3',
});
```

## Production Notes

1. **Cache M2M tokens** — Auth0 rate-limits `/oauth/token`. Cache the access token (it's valid for 24h by default) and refresh only when within 30s of expiry.
2. **API audience must match exactly** — The `audience` in your JWT middleware must match the API identifier in the Auth0 dashboard. Even a trailing slash difference causes 401s.
3. **`AUTH0_SECRET` must be 32+ chars** — Next.js SDK uses this to encrypt session cookies. Short secrets cause startup errors in production.
4. **RBAC requires enabling in API settings** — Go to Auth0 Dashboard → APIs → your API → Settings → Enable RBAC and "Add Permissions in the Access Token" to have roles/permissions in JWT claims.

## Failure Modes

| Symptom | Root Cause | Fix |
|---------|-----------|-----|
| `401 Unauthorized` on protected route | Wrong `audience` in JWT middleware | Match exact API Identifier from Auth0 Dashboard (no trailing slash) |
| Infinite redirect loop on login | `AUTH0_BASE_URL` / `APP_BASE_URL` mismatch | Set to exact origin of your app (e.g. `https://myapp.com`) |
| `permissions` claim missing from token | RBAC not enabled on API | Enable RBAC in Auth0 Dashboard → APIs → your API → Settings |
| `invalid_client` on M2M token request | Wrong client credentials | Use M2M application credentials, not Regular Web App |
| Session lost after deployment | `AUTH0_SECRET` changed between deploys | Use a stable secret stored in environment variable manager |
| `Too many requests` on token endpoint | Fetching M2M token on every request | Cache token in-memory; only refresh near expiry |

## Pre-Deploy Checklist
- [ ] Auth0 application callback URLs include production domain
- [ ] Auth0 application logout URLs include production domain
- [ ] `AUTH0_SECRET` is 32+ random characters stored in secrets manager
- [ ] API Identifier matches `audience` in JWT middleware exactly
- [ ] RBAC enabled if using roles/permissions in tokens
- [ ] M2M token caching implemented (not fetched on every request)
- [ ] Error boundary handles Auth0 session errors gracefully

## Resources
- Docs: https://auth0.com/docs
- Next.js SDK: https://github.com/auth0/nextjs-auth0
- Express middleware: https://github.com/auth0/node-oauth2-jwt-bearer
- Management SDK: https://github.com/auth0/node-auth0
