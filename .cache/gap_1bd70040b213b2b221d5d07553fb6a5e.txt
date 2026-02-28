---
name: lucia-auth
description: >-
  Assists with building custom session-based authentication systems using Lucia. Use when
  implementing password auth, OAuth flows, two-factor authentication, or session management
  with full control over the auth logic in Next.js, SvelteKit, Express, or other Node.js
  frameworks. Trigger words: lucia, session auth, custom auth, password hashing, 2fa, totp.
license: Apache-2.0
compatibility: "Requires Node.js 18+"
metadata:
  author: terminal-skills
  version: "1.0.0"
  category: development
  tags: ["lucia", "authentication", "session", "oauth", "two-factor"]
---

# Lucia Auth

## Overview

Lucia is a lightweight, un-opinionated authentication library for Node.js that provides session management while giving developers full control over login, registration, and logout logic. It supports any database via adapters (Drizzle, Prisma, MongoDB) and any framework (Next.js, SvelteKit, Express, Astro), with built-in support for password hashing, OAuth via the Arctic library, and two-factor authentication.

## Instructions

- When setting up authentication, initialize Lucia with a database adapter and configure session cookie options (`httpOnly`, `secure`, `sameSite: "lax"`), then implement login and registration routes that create sessions via `lucia.createSession()`.
- When implementing password auth, use `Argon2id` (via `@node-rs/argon2`) for new projects or the built-in `Scrypt` for hashing, and validate password strength in your own code before hashing.
- When adding OAuth login, use the `arctic` library to generate authorization URLs, handle callbacks, create or link user accounts, and establish sessions.
- When implementing two-factor authentication, use `@oslojs/otp` for TOTP codes (Google Authenticator), generate and hash recovery codes on setup, and add a verification step between login and session creation.
- When managing sessions, validate with `lucia.validateSession(sessionId)` on every request, invalidate single sessions on logout, and invalidate all user sessions on password change or security events.
- When integrating with frameworks, validate sessions in Next.js Server Components via `cookies()`, in SvelteKit via `hooks.server.ts`, in Express via middleware, or in Astro via `Astro.locals`.

## Examples

### Example 1: Build email/password auth with session management

**User request:** "Add email and password login to my SvelteKit app using Lucia"

**Actions:**
1. Set up Lucia with Drizzle adapter and define user/session database schema
2. Create registration endpoint that hashes password with Argon2id and creates a session
3. Create login endpoint that verifies password and creates a session cookie
4. Add `hooks.server.ts` to validate sessions on every request and attach user to `event.locals`

**Output:** A SvelteKit app with secure email/password authentication and session-based access control.

### Example 2: Add TOTP two-factor authentication

**User request:** "Add Google Authenticator 2FA to the existing login flow"

**Actions:**
1. Add a TOTP secret field to the user model and a 2FA setup page that generates a QR code
2. Generate and hash recovery codes, store them in the database
3. Modify the login flow to check if 2FA is enabled and prompt for a TOTP code before creating a session
4. Add a recovery code fallback for users who lose access to their authenticator app

**Output:** A login flow with optional TOTP-based two-factor authentication and recovery codes.

## Guidelines

- Always hash session IDs with SHA-256 before storing in the database to prevent session theft from database leaks.
- Set `httpOnly`, `secure`, and `sameSite: "lax"` on session cookies to prevent XSS and CSRF attacks.
- Invalidate all user sessions on password change or any security-critical event.
- Use Argon2id for new projects over Scrypt for better side-channel resistance.
- Implement rate limiting on login endpoints: 5 attempts per 15 minutes per IP address.
- Store OAuth access tokens encrypted, not in plain text, since they grant API access to user accounts.
- Set session expiry to 30 days with sliding window renewal on each validated request.
