# Recovery design notes

Background for `durable-sessions`: why the record has the shape it does, and what
the checker deliberately does not decide for you.

## Why replay rather than re-run

Resuming by re-running the session from the top is correct only if every action is
deterministic and free of side effects. Agent sessions are neither: they call models,
they read a changing world, and they act on it. Re-running is therefore not "slower
recovery" — it is a *different session*, which happens to share a starting prompt.

Replay makes the resumed session identical to the interrupted one up to the point of
failure, and only then continues. That is the whole reason for recording outcomes.

## What counts as non-deterministic

Anything whose result you cannot reproduce by asking again:

- **model calls** — same prompt, different day, different answer;
- **external reads** — prices, availability, search results;
- **clock and randomness** — including anything seeded from them;
- **human answers** — the strongest case, and the one most often missed because a
  question feels like input rather than an action.

Treat the human as an external system that is expensive to call and rude to call twice.

## Idempotency keys

The key exists so a repeated attempt is recognised as the same attempt. It must be:

- **derived from identity**, not from time — `session_id + action_id` works; a timestamp
  or a fresh UUID per attempt keys nothing;
- **stable across process restarts** — if it is computed in memory and lost on crash,
  it is not a key;
- **carried to the far side** — the downstream service has to honour it, or the key is
  documentation rather than protection. Where it will not, use `replay: skip` and accept
  that the effect is not repeated *and* not retried; that is a real trade-off, not a
  loophole.

## Where the cache boundary sits

The useful question is not "is this expensive?" but **"whose answer is it?"**

- Belongs to the world → shareable (a public search on a given day, a reference lookup).
- Belongs to this session → not shareable (anything generated for this user, anything
  the user said).

A shared cache of user-specific results is a correctness bug and, when the content is
personal, a disclosure bug. The checker enforces only the clearest case — a human answer
marked cacheable — because the rest depends on your domain.

## Retry caps and escalation

A cap is not a limit on patience; it is the point where the system admits the failure is
not transient. Reaching it should route somewhere, and "ask the user" is usually the right
destination: after several honest attempts, the missing thing is often information only
they have. Silent give-up and infinite retry are the two failure modes; both look like
"nothing happened" from the outside.

## What this checker does not do

- It does not verify that recovery **works** — only that the record could support it.
  Prove the rest by killing a live session on purpose and watching it resume.
- It does not decide your cache policy beyond the human-answer rule.
- It does not inspect the runtime, the orchestrator, or the model. It reads a log, so it
  is portable; the cost is that a log which lies to it will pass.
- It does not cover sandboxing agent-written code — a separate concern, covered by
  `agent-isolation` in this bundle.
