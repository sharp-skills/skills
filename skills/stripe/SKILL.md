---
name: stripe
description: "Integrates Stripe payment processing into applications using the official Stripe SDK (Python or Node.js). Use when asked to: accept credit card payments, set up subscriptions or recurring billing, handle Stripe webhooks, create Stripe Checkout sessions, manage customers and payment methods, issue refunds, set up Stripe Connect for marketplace payments, or retrieve invoices and payment history."
license: Apache-2.0
compatibility:
- node >= 16
metadata:
  author: SharpSkills
  version: 1.0.0
  category: development
  tags: [stripe, payments, billing, subscriptions, webhooks, checkout]
---

# Stripe Skill

## Quick Start

**Node.js**
```bash
npm install stripe
```

```typescript
import Stripe from 'stripe';

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!);

// Create a PaymentIntent
const paymentIntent = await stripe.paymentIntents.create({
  amount: 2000,          // $20.00 in cents
  currency: 'usd',
  automatic_payment_methods: { enabled: true },
});

console.log(paymentIntent.client_secret);
```

**Python**
```bash
pip install stripe
```

```python
import stripe

stripe.api_key = "sk_test_..."

payment_intent = stripe.PaymentIntent.create(
    amount=2000,
    currency="usd",
    automatic_payment_methods={"enabled": True},
)
print(payment_intent.client_secret)
```

## When to Use
Use this skill when asked to:
- "Accept credit card payments" or "integrate Stripe"
- "Set up subscriptions" or "recurring billing"
- "Handle Stripe webhooks" or "verify webhook signatures"
- "Create a Stripe Checkout session" or "hosted payment page"
- "Add a customer" or "save payment methods for later"
- "Issue a refund" or "cancel a payment"
- "Set up Stripe Connect" or "marketplace payments" or "split payments"
- "Retrieve invoices" or "list payment history"
- "Create a coupon" or "apply a discount"
- "Set up usage-based billing" or "metered subscriptions"

## Core Patterns

### Pattern 1: Stripe Checkout Session (Source: official)
Redirect users to a Stripe-hosted payment page — the fastest path to accepting payments with no PCI scope beyond redirect.

```typescript
import Stripe from 'stripe';

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!);

const session = await stripe.checkout.sessions.create({
  payment_method_types: ['card'],
  line_items: [
    {
      price_data: {
        currency: 'usd',
        product_data: { name: 'T-shirt' },
        unit_amount: 2000,
      },
      quantity: 1,
    },
  ],
  mode: 'payment',
  success_url: 'https://yoursite.com/success?session_id={CHECKOUT_SESSION_ID}',
  cancel_url: 'https://yoursite.com/cancel',
});

// Redirect user to session.url
console.log(session.url);
```

### Pattern 2: Subscription with Recurring Price (Source: official)
Create a customer and subscribe them to a product price for recurring billing.

```typescript
import Stripe from 'stripe';

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!);

// 1. Create a customer
const customer = await stripe.customers.create({
  email: 'user@example.com',
  payment_method: 'pm_card_visa', // attach after collecting via Elements
});

// 2. Set default payment method
await stripe.customers.update(customer.id, {
  invoice_settings: { default_payment_method: 'pm_card_visa' },
});

// 3. Create subscription (price ID from Stripe Dashboard)
const subscription = await stripe.subscriptions.create({
  customer: customer.id,
  items: [{ price: 'price_1234567890' }],
  expand: ['latest_invoice.payment_intent'],
});

console.log(subscription.status); // 'active' | 'incomplete' | ...
```

### Pattern 3: Webhook Signature Verification (Source: official)
Always verify webhook signatures before processing events to prevent spoofed requests.

```typescript
import Stripe from 'stripe';
import express from 'express';

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!);
const app = express();

// CRITICAL: use raw body — do NOT use express.json() before this route
app.post(
  '/webhook',
  express.raw({ type: 'application/json' }),
  (req, res) => {
    const sig = req.headers['stripe-signature'] as string;

    let event: Stripe.Event;
    try {
      event = stripe.webhooks.constructEvent(
        req.body,
        sig,
        process.env.STRIPE_WEBHOOK_SECRET!
      );
    } catch (err) {
      console.error('Webhook signature verification failed:', err);
      return res.status(400).send(`Webhook Error: ${(err as Error).message}`);
    }

    // Handle events
    switch (event.type) {
      case 'payment_intent.succeeded':
        const pi = event.data.object as Stripe.PaymentIntent;
        console.log('Payment succeeded:', pi.id);
        break;
      case 'customer.subscription.deleted':
        // Revoke access
        break;
      default:
        console.log(`Unhandled event type: ${event.type}`);
    }

    res.json({ received: true });
  }
);
```

**Python equivalent:**
```python
import stripe
import flask

app = flask.Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    payload = flask.request.get_data(as_text=True)
    sig_header = flask.request.headers.get('Stripe-Signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, "whsec_..."
        )
    except stripe.error.SignatureVerificationError as e:
        return flask.jsonify(error=str(e)), 400

    if event['type'] == 'payment_intent.succeeded':
        print('Payment succeeded:', event['data']['object']['id'])

    return flask.jsonify(success=True)
```

### Pattern 4: Refund a Payment (Source: official)

```typescript
import Stripe from 'stripe';

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!);

// Full refund
const refund = await stripe.refunds.create({
  payment_intent: 'pi_1234567890',
});

// Partial refund ($5.00 of original charge)
const partialRefund = await stripe.refunds.create({
  payment_intent: 'pi_1234567890',
  amount: 500,
});

console.log(refund.status); // 'succeeded'
```

### Pattern 5: Error Handling (Source: community)
Stripe throws typed errors — catch them specifically to give users actionable feedback rather than generic 500s.

```typescript
import Stripe from 'stripe';

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!);

async function chargeCustomer(customerId: string, amount: number) {
  try {
    const paymentIntent = await stripe.paymentIntents.create({
      amount,
      currency: 'usd',
      customer: customerId,
      confirm: true,
      payment_method: 'pm_card_visa',
    });
    return { success: true, paymentIntent };
  } catch (err) {
    if (err instanceof Stripe.errors.StripeCardError) {
      // Card declined — show user-facing message
      return { success: false, message: err.message, code: err.code };
    } else if (err instanceof Stripe.errors.StripeInvalidRequestError) {
      // Bad parameters — log for debugging
      console.error('Invalid request:', err.message);
      return { success: false, message: 'Invalid payment parameters.' };
    } else if (err instanceof Stripe.errors.StripeAuthenticationError) {
      // Wrong API key
      console.error('Authentication failed — check STRIPE_SECRET_KEY');
      return { success: false, message: 'Payment service unavailable.' };
    } else if (err instanceof Stripe.errors.StripeRateLimitError) {
      // Back off and retry
      console.warn('Rate limited by Stripe — retry with backoff');
      return { success: false, message: 'Payment service busy, try again.' };
    } else {
      throw err; // Unknown — rethrow
    }
  }
}
```

### Pattern 6: Stripe Connect — Create an Account Link (Source: official)
For marketplaces: create a connected account and generate an onboarding link.

```typescript
import Stripe from 'stripe';

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!);

// Create a connected account
const account = await stripe.accounts.create({
  type: 'express',
  country: 'US',
  email: 'seller@example.com',
  capabilities: {
    card_payments: { requested: true },
    transfers: { requested: true },
  },
});

// Generate onboarding link
const accountLink = await stripe.accountLinks.create({
  account: account.id,
  refresh_url: 'https://yoursite.com/reauth',
  return_url: 'https://yoursite.com/onboard-complete',
  type: 'account_onboarding',
});

// Redirect seller to accountLink.url
console.log(accountLink.url);
```

## Production Notes

1. **Raw body required for webhooks** — If you parse the request body with `express.json()` or any body parser before the webhook route, `stripe.webhooks.constructEvent()` will throw a signature mismatch. Mount `express.raw({ type: 'application/json' })` as middleware on the webhook route specifically, before any global body parsers. Source: Stripe official docs + recurring community reports.

2. **Use `STRIPE_WEBHOOK_SECRET` from the CLI or Dashboard, not your API key** — The webhook secret starts with `whsec_` and is distinct from your `sk_` secret key. Using the wrong value produces a persistent 400. For local development use `stripe listen --forward-to localhost:3000/webhook` which prints the correct `whsec_` to stdout. Source: Stripe CLI docs.

3. **Always store amounts in the currency's smallest unit** — USD uses cents (`2000` = $20.00), JPY uses whole yen (`500` = ¥500). Passing `20.00` instead of `2000` for USD produces an `StripeInvalidRequestError`. Source: Stripe API docs / common Stack Overflow issue.

4. **Idempotency keys prevent duplicate charges on retry** — Network failures can leave a charge in an ambiguous state. Pass `idempotencyKey` (Node) or `idempotency_key` (Python) set to a stable ID (e.g., your order UUID) so retried requests return the original object rather than creating a second charge. Source: Stripe official best practices.

5. **Test mode and live mode use different keys and webhook secrets** — `sk_test_` / `pk_test_` keys only work with test card numbers (e.g., `4242 4242 4242 4242`). Accidentally using a test webhook secret against a live webhook (or vice versa) causes all events to fail signature verification silently. Source: community GitHub issues.

## Failure Modes

| Symptom | Root Cause | Fix |
|---|---|---|
| `No signatures found matching the expected signature` on webhook | Body was parsed (JSON/URL-encoded) before reaching `constructEvent` | Apply `express.raw()` to the webhook route before any global `express.json()` middleware |
| `StripeInvalidRequestError: Amount must be a positive integer` | Passing a float (`19.99`) instead of smallest-unit integer (`1999`) | Always multiply by 100 for USD and round: `Math.round(amount * 100)` |
| Webhook events arrive but subscription state is stale | Relying on API polling instead of webhook events for state sync | Listen to `customer.subscription.updated` and `customer.subscription.deleted` events to update your DB |
| `StripeAuthenticationError: No API key provided` | `STRIPE_SECRET_KEY` env var missing at runtime (common in serverless cold starts) | Confirm env var is set in deployment config; throw a startup error if `!process.env.STRIPE_SECRET_KEY` |
| Duplicate charges on network retry | Missing idempotency key on `paymentIntents.create` or `charges.create` | Pass `{ idempotencyKey: orderId }` as the second argument to prevent duplicate processing |
| `StripeRateLimitError` under load | Exceeding Stripe's API rate limits in burst traffic | Implement exponential backoff; cache customer/price lookups; avoid per-request price creation |

## Pre-Deploy Checklist
- [ ] `STRIPE_SECRET_KEY` is set to a **live** `sk_live_` key in production (not `sk_test_`)
- [ ] `STRIPE_PUBLISHABLE_KEY` is `pk_live_` in the frontend bundle for production
- [ ] `STRIPE_WEBHOOK_SECRET` matches the live webhook endpoint secret from the Stripe Dashboard (not the CLI `whsec_`)
- [ ] Webhook route receives the **raw** (unparsed) request body
- [ ] All payment amounts are in the currency's **smallest unit** (cents for USD)
- [ ] Idempotency keys are set on all charge/payment-intent creation calls
- [ ] Error handling distinguishes `StripeCardError` (user-facing) from `StripeAuthenticationError` (ops alert)
- [ ] Webhook handler returns `200` quickly and processes heavy work asynchronously to avoid Stripe retry storms

## Troubleshooting

**Error: `No signatures found matching the expected signature for payload`**
Cause: The request body was JSON-parsed before `constructEvent` received it, corrupting the raw bytes Stripe signs.
Fix: On the webhook route, use `express.raw({ type: 'application/json' })` **instead of** `express.json()`. In Next.js API routes, add `export const config = { api: { bodyParser: false } }`.

**Error: `StripeInvalidRequestError: Amount must be a positive integer`**
Cause: Passing a decimal dollar amount (e.g., `9.99`) instead of the integer cent amount (`999`).
Fix: Convert before sending: `const amountInCents = Math.round(dollarAmount * 100)`.

**Error: `StripeAuthenticationError: Invalid API Key provided`**
Cause: Mismatched key environment (test key in production, or live key in test), or a truncated/copied key with whitespace.
Fix: Log `process.env.STRIPE_SECRET_KEY?.slice(0, 8)` to verify the prefix (`sk_test_` vs `sk_live_`). Trim whitespace when setting the env var.

**Webhooks not received locally**
Cause: Stripe cannot reach `localhost`.
Fix: Install the Stripe CLI and run `stripe listen --forward-to localhost:3000/webhook`. Copy the printed `whsec_` value to your local `.env` as `STRIPE_WEBHOOK_SECRET`.

## Resources
- Docs: https://stripe.com/docs/api
- Python SDK: https://github.com/stripe/stripe-python
- Node SDK: https://github.com/stripe/stripe-node
- Stripe CLI: https://stripe.com/docs/stripe-cli
- Webhook testing: https://stripe.com/docs/webhooks/test
- Error handling reference: https://stripe.com/docs/api/errors/handling
- Test card numbers: https://stripe.com/docs/testing#cards