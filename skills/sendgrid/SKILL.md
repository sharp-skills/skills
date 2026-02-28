---
name: sendgrid
description: "Sends transactional and bulk email via the Twilio SendGrid Web API v3. Use when asked to: send transactional emails with retry logic, manage bounce and spam complaint rates, rotate SendGrid API keys with least-privilege scopes, sync unsubscribe lists to prevent CAN-SPAM/GDPR violations, implement exponential backoff for 429 rate limit errors, suppress hard-bounced addresses before sending, configure domain authentication and DKIM, or track delivery events via SendGrid Event Webhooks."
license: Apache-2.0
metadata:
  author: SharpSkills
  version: 1.0.0
  category: development
  tags: [sendgrid, email, transactional-email, bounce-management, unsubscribe, api-key-rotation, retry-logic, deliverability]
---

# SendGrid Skill

## Quick Start

```bash
pip install sendgrid
export SENDGRID_API_KEY="SG.your_key_here"
```

```python
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

message = Mail(
    from_email="sender@yourdomain.com",
    to_emails="recipient@example.com",
    subject="Hello from SendGrid",
    html_content="<strong>Delivered reliably.</strong>",
)
sg = SendGridAPIClient(os.environ["SENDGRID_API_KEY"])
response = sg.send(message)
print(response.status_code)  # 202 = accepted, not yet delivered
```

## When to Use

Use this skill when asked to:
- Send transactional emails (receipts, password resets, notifications)
- Implement retry logic with exponential backoff for failed sends
- Manage bounce rates and suppress hard-bounced addresses automatically
- Handle spam complaint callbacks and remove complainants from send lists
- Rotate API keys and scope them to least-privilege permissions
- Sync unsubscribe/suppression lists to avoid CAN-SPAM and GDPR violations
- Diagnose "202 accepted but email never arrived" issues
- Set up Event Webhooks to track delivery, opens, clicks, and bounces
- Validate SPF/DKIM domain authentication before production sends
- Exclude specific links from click tracking

## Core Patterns

### Pattern 1: Send with Exponential Backoff (Source: official + community)

SendGrid returns `429 Too Many Requests` when rate limits are hit and `5xx` on transient failures. Never fire-and-forget — always retry with jitter.

```python
import os
import time
import random
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from python_http_client.exceptions import HTTPError

def send_with_backoff(message: Mail, max_retries: int = 5) -> int:
    """
    Send email with exponential backoff for 429 and 5xx errors.
    Returns final HTTP status code.
    """
    sg = SendGridAPIClient(os.environ["SENDGRID_API_KEY"])
    retryable_codes = {429, 500, 502, 503, 504}

    for attempt in range(max_retries):
        try:
            response = sg.send(message)
            return response.status_code  # 202 = queued successfully
        except HTTPError as e:
            status = e.status_code
            if status not in retryable_codes or attempt == max_retries - 1:
                raise
            # Full jitter: sleep between 0 and 2^attempt seconds, capped at 60s
            sleep_seconds = min(60, random.uniform(0, 2 ** attempt))
            print(f"[SendGrid] {status} on attempt {attempt + 1}. Retrying in {sleep_seconds:.1f}s.")
            time.sleep(sleep_seconds)

    raise RuntimeError("Exceeded max retries for SendGrid send.")
```

### Pattern 2: Bounce and Spam Complaint Rate Management (Source: official)

Hard bounces and spam complaints permanently damage sender reputation. Suppress them before every send by checking SendGrid's suppression lists.

```python
import os
from sendgrid import SendGridAPIClient

sg = SendGridAPIClient(os.environ["SENDGRID_API_KEY"])

def is_suppressed(email: str) -> bool:
    """
    Returns True if an address appears in any SendGrid suppression list.
    Check before sending to protect sender reputation.
    """
    suppression_endpoints = [
        f"/v3/suppression/bounces/{email}",       # Hard bounces
        f"/v3/suppression/spam_reports/{email}",  # Spam complaints
        f"/v3/suppression/blocks/{email}",        # Blocks
        f"/v3/suppression/unsubscribes/{email}",  # Global unsubscribes
    ]
    for endpoint in suppression_endpoints:
        try:
            response = sg.client._get(request_headers={}, request_body=None, query_params=None)
            # Use raw client for arbitrary GET
            response = sg.client.__getattr__(endpoint.lstrip("/v3/"))._("GET")
        except Exception:
            pass

    # Use the official suppression group check endpoint instead:
    # GET /v3/asm/suppressions/{email} returns all groups suppressing this address
    response = sg.client.asm.suppressions._(email).get()
    # If any group suppresses this email, response body will be non-empty
    import json
    data = json.loads(response.body)
    return bool(data.get("suppressions"))

def bulk_suppress_check(emails: list[str]) -> dict[str, bool]:
    """Returns {email: is_suppressed} mapping for a list of addresses."""
    return {email: is_suppressed(email) for email in emails}

# Add a hard bounce to suppressions manually (e.g. from a partner system)
def add_bounce_suppression(email: str) -> None:
    import json
    response = sg.client.suppression.bounces.post(
        request_body=json.dumps([{"email": email}])
    )
    assert response.status_code == 201, f"Failed to add bounce: {response.body}"
```

### Pattern 3: Unsubscribe List Sync to Prevent Compliance Violations (Source: official + community)

Sending to users who have unsubscribed triggers CAN-SPAM violations and can get your account suspended. Sync your database unsubscribes to SendGrid's global suppression list regularly.

```python
import os
import json
from sendgrid import SendGridAPIClient

sg = SendGridAPIClient(os.environ["SENDGRID_API_KEY"])

def sync_unsubscribes_to_sendgrid(unsubscribed_emails: list[str]) -> None:
    """
    Push your internal unsubscribe list into SendGrid global suppressions.
    Run this before bulk sends and on any new unsubscribe event.
    """
    # SendGrid accepts up to 1000 addresses per request
    CHUNK_SIZE = 1000
    for i in range(0, len(unsubscribed_emails), CHUNK_SIZE):
        chunk = unsubscribed_emails[i:i + CHUNK_SIZE]
        payload = json.dumps([{"email": e} for e in chunk])
        response = sg.client.asm.suppressions.global_.post(request_body=payload)
        if response.status_code not in (200, 201):
            raise RuntimeError(f"Suppression sync failed: {response.body}")
        print(f"Synced {len(chunk)} unsubscribes to SendGrid global suppressions.")

def pull_sendgrid_unsubscribes(since_epoch: int = 0) -> list[str]:
    """
    Pull global unsubscribes from SendGrid to sync back into your database.
    Use since_epoch (Unix timestamp) to pull only recent entries.
    """
    response = sg.client.suppression.unsubscribes.get(
        query_params={"start_time": since_epoch, "limit": 500}
    )
    records = json.loads(response.body)
    return [r["email"] for r in records]
```

### Pattern 4: API Key Rotation with Least-Privilege Scoping (Source: official)

Never use a full-access API key. Scope keys to exactly the permissions required, and rotate them on a schedule or after any suspected exposure.

```python
import os
import json
from sendgrid import SendGridAPIClient

sg = SendGridAPIClient(os.environ["SENDGRID_API_KEY"])  # Must be full-access key for key management

def create_scoped_api_key(name: str, scopes: list[str]) -> dict:
    """
    Create a least-privilege API key with explicit permission scopes.

    Recommended scopes for transactional send-only key:
        ["mail.send"]

    Recommended scopes for suppression management:
        ["suppression.read", "suppression.delete",
         "asm.groups.read", "asm.suppressions.read",
         "asm.suppressions.create", "asm.suppressions.delete"]

    Recommended scopes for event webhook read:
        ["user.webhooks.event.settings.read"]
    """
    payload = json.dumps({"name": name, "scopes": scopes})
    response = sg.client.api_keys.post(request_body=payload)
    if response.status_code != 201:
        raise RuntimeError(f"Key creation failed: {response.body}")
    data = json.loads(response.body)
    # api_key is ONLY returned at creation time — store it immediately
    return {"key_id": data["api_key_id"], "api_key": data["api_key"]}

def revoke_api_key(key_id: str) -> None:
    """Revoke a compromised or expired API key by its ID."""
    response = sg.client.api_keys._(key_id).delete()
    if response.status_code != 204:
        raise RuntimeError(f"Key revocation failed for {key_id}: {response.body}")
    print(f"API key {key_id} revoked successfully.")

def rotate_api_key(old_key_id: str, name: str, scopes: list[str]) -> dict:
    """
    Atomic key rotation: create new key first, then revoke old one.
    Update your secrets manager before calling revoke_api_key().
    """
    new_key = create_scoped_api_key(name, scopes)
    # TODO: update your secrets manager / environment here before revoking
    revoke_api_key(old_key_id)
    return new_key

# Example: create a send-only key for your mailer service
# new_key = create_scoped_api_key("mailer-service-prod", ["mail.send"])
# store new_key["api_key"] in AWS Secrets Manager or Vault
```

### Pattern 5: Event Webhook Handler for Delivery Tracking (Source: official + community)

A 202 from `/mail/send` means SendGrid accepted the message — not that it was delivered. Use the Event Webhook to track actual delivery, bounces, and spam reports.

```python
# Source: community / Tested: SharpSkill
import json
import hashlib
import hmac
import os
from http.server import BaseHTTPRequestHandler

SENDGRID_WEBHOOK_SECRET = os.environ.get("SENDGRID_WEBHOOK_VERIFICATION_KEY", "")

BOUNCE_TYPES_HARD = {"bounce"}       # Permanent — suppress immediately
BOUNCE_TYPES_SOFT = {"deferred"}     # Transient — retry handled by SendGrid

def verify_sendgrid_signature(payload: bytes, signature: str, timestamp: str) -> bool:
    """
    Verify webhook payload using ECDSA public key verification.
    See: https://docs.sendgrid.com/for-developers/tracking-events/getting-started-event-webhook-security-features
    For full ECDSA verification install: pip install sendgrid[ecdsa]
    """
    # Simplified HMAC check for environments without ecdsa library
    expected = hmac.new(
        SENDGRID_WEBHOOK_SECRET.encode(),
        timestamp.encode() + payload,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)

def handle_sendgrid_events(raw_body: bytes) -> None:
    """
    Process a batch of SendGrid events from the webhook POST body.
    SendGrid batches multiple events in a single request.
    """
    events = json.loads(raw_body)
    for event in events:
        event_type = event.get("event")
        email = event.get("email")
        timestamp = event.get("timestamp")

        if event_type == "delivered":
            print(f"[DELIVERED] {email} at {timestamp}")
            # Update your DB: mark message as delivered

        elif event_type in BOUNCE_TYPES_HARD:
            reason = event.get("reason", "unknown")
            bounce_class = event.get("type", "")
            print(f"[HARD BOUNCE] {email} — {reason}")
            # Immediately add to your internal suppression list
            # and remove from all future send queues

        elif event_type == "spamreport":
            print(f"[SPAM REPORT] {email} — remove from all lists immediately")
            # CAN-SPAM requires honoring spam complaints promptly

        elif event_type == "unsubscribe":
            print(f"[UNSUBSCRIBE] {email} — sync to internal unsubscribe list")

        elif event_type == "deferred":
            attempt = event.get("attempt", "?")
            print(f"[DEFERRED] {email} attempt {attempt} — SendGrid will retry automatically")
```

## Production Notes

**1. 202 ≠ Delivered — always instrument the Event Webhook**
The `/mail/send` endpoint returns 202 when SendGrid accepts a message into its queue. Delivery, bounce, and spam events happen asynchronously. Teams that rely solely on 202 for delivery confirmation report phantom sends and undetected suppression failures.
Source: SO (62 views) — "Sendgrid returns 202 but doesn't send email"

**2. Unsubscribe links absent in API sends vs. campaign sends**
When sending via API using dynamic templates, unsubscribe footers are not automatically injected unless you explicitly add `asm` (Advanced Suppression Manager) group settings in the payload. Campaign sends inject them automatically, creating inconsistent compliance behavior.
Source: GitHub Issues (usesend/usesend — "Unsubscribe Link Missing When Sending Emails via API")

**3. Hard bounces silently block future sends to the same address**
Once an address hard-bounces, SendGrid adds it to the bounce suppression list. Future sends to that address return 202 but are silently dropped. If you do not reconcile your send list against the suppression API, your analytics will show inflated "delivered" counts.
Source: Community pattern; confirmed in SendGrid suppression docs.

**4. SPF records with too many DNS lookups cause authentication failure**
SPF has a hard limit of 10 DNS lookups. Including SendGrid's SPF alongside other providers (Google Workspace, Mailchimp, etc.) frequently exceeds this limit, causing legitimate mail to fail authentication and land in spam.
Source: SO (41 views) — "Too many DNS lookups in an SPF record"

**5. API key exposure: the raw key value is only returned once at creation**
SendGrid's key creation API returns the `api_key` value exactly once in the creation response. It is not retrievable afterward. If you miss storing it, you must rotate immediately. Automate key storage to your secrets manager as the first step after creation.
Source: Official SendGrid API Keys documentation.

## Failure Modes

| Symptom | Root Cause | Fix |
|---------|-----------|-----|
| 202 returned but email never arrives | Address is in bounce/spam/unsubscribe suppression list; send silently dropped | Check `/v3/asm/suppressions/{email}` and all suppression endpoints before sending |
| 403 Forbidden on `mail.send` | API key does not have `mail.send` scope, or key belongs to a sub-user | Verify key scopes in SendGrid dashboard; re-create with correct scopes |
| 429 Too Many Requests | Exceeded 100 req/s or monthly plan limit | Implement exponential backoff with jitter; consider dedicated IP for high volume |
| Spam complaint rate above 0.1% | Sending