---
name: durable-sessions
description: Make a long-running agent session survive being interrupted — log every action so recovery replays recorded outcomes instead of re-running them, key side effects so they cannot fire twice, bound every retry, and scope caches so one user's answer never becomes another's. Use when a session lives longer than the process running it (hours, days, weeks), when a crash or restart forces users to start over or answer the same question again, when a retry loop burns budget without ever escalating, or when you need the production-failure axis rather than the output-quality one.
license: Apache-2.0
---

# Durable sessions

Most agent engineering effort goes into semantic quality — getting the right output.
That work happens on a laptop, in minutes-long runs. Production breaks on a different
axis entirely: the process dies, the machine is reclaimed, an upstream throttles, the
session has been open for nine days. **These failures have nothing to do with how good
the answers are, and no amount of prompt work prevents them.**

So do not design a session that never fails. Design one where failure is cheap.

## Two axes of failure — do not conflate them

| Axis | Examples | Where it shows up | Who owns it |
|---|---|---|---|
| **Semantic** | wrong tool chosen, malformed output, hallucinated citation | during development | your prompts, contracts, evals |
| **Operational** | crash, OOM, machine reclaimed, throttling, dropped connection | only in production | your session log and recovery policy |

This skill is entirely about the second. A team that has polished the first and skipped
the second ships an agent that is right and unusable.

## The rule: recovery replays the log, it does not re-run it

After an interruption the session resumes from a recorded log of what already happened.
Two categories of action make that dangerous if the log is sloppy:

**Non-deterministic actions** — a model call, a web read, a clock read, and above all a
**question you asked the human**. Running them again produces a different answer, so the
resumed session silently diverges from the one the user was in. Record the outcome; on
replay, return the record.

> Re-asking a person something they already told you is the sharpest form of this bug.
> It is also the one users notice immediately: it reads as the agent having forgotten them.

**Side-effecting actions** — a payment, an email, a write, a deploy. Replaying these
repeats the effect in the real world. Each needs an **idempotency key** (so the second
attempt is recognised and collapsed) or an explicit **`replay: skip`** (so recovery steps
over it). There is no safe third option.

## Bound every retry, then escalate to a human

An action marked retryable without a finite cap is an unbounded loop. It burns budget,
it never surfaces, and it never asks. Declare `max_attempts`; when the cap is reached,
the correct move is usually not another attempt but **a question**: the task may be
impossible, or it may need input only the user has.

A failed action that is *not* retryable needs an instruction — ask the user, abort,
or compensate — otherwise recovery has to guess. `--strict` enforces this.

## Cache by call type, not by habit

Sharing results across sessions is a large, cheap win, but only for the right calls.

| Cache | Do not cache |
|---|---|
| The same web search on the same day | Anything generated *for* this user (a report, a reply) |
| A stable reference lookup | **Anything a human told you** — that answer belongs to one session |

Every cache entry needs a key *and* a lifetime. An entry that never expires is a stale
answer waiting to be served.

## Declare the resources in the code that uses them

Code that does not know it asked for 32 GB cannot react when 32 GB runs out. When the
resource request lives beside the logic, an out-of-memory or a reclaimed machine becomes
an actionable event — retry elsewhere, retry larger, or degrade — instead of an opaque death.
The corollary: prefer a runtime where you write ordinary code rather than a constrained
mini-language, or the recovery logic you need will be the thing you cannot express.

## Run the checker

```sh
python3 scripts/replay_check.py --actions session.jsonl          # 0 safe / 1 violations / 2 unreadable
python3 scripts/replay_check.py --actions session.jsonl --strict  # also demand on_failure on dead ends
sh examples/selftest.sh                                           # 13 assertions over both fixtures
```

One JSON object per action; `session_id`, `action_id`, `kind`, `status` are required.
The checker reads the record, not the runtime, so any orchestrator that can emit a line
per action is supported. See `examples/actions.good.jsonl` for the shape and
`examples/actions.bad.jsonl` for a plausible-but-unrecoverable log (each line carries
`_fails_because`).

## Common pitfalls

- **Logging only the prompt, not the answer.** The most common shape of an unrecoverable
  log: every question is recorded, no result is. Replay then re-asks everything.
- **Treating `result: null` as "not recorded".** An action can legitimately return nothing.
  What matters is that the key is present — absence means nobody wrote it down.
- **Idempotency keys derived from a timestamp.** They differ on replay, so they key nothing.
  Derive them from the session and action identity.
- **One giant retry policy for the whole agent.** Throttling wants a long backoff; a
  reclaimed machine wants an immediate move; a semantic failure wants a human. Set caps
  per action kind.
- **Assuming a durable log means a durable agent.** The log makes recovery *possible*;
  something must still decide to resume, and that path needs exercising — kill the process
  mid-session on purpose and confirm it comes back where it was.

## Verification checklist

- [ ] Every non-deterministic action that succeeded carries its result.
- [ ] Every side-effecting action carries an idempotency key or `replay: skip`.
- [ ] Every retryable action has a finite cap, and the cap escalates rather than loops.
- [ ] Cached entries have a key and a lifetime; nothing a human said is cached.
- [ ] Action IDs are unique within a session.
- [ ] A deliberately killed session resumes without re-asking or re-charging.

## Related skills in this bundle

- **event-envelope** — the wire contract that lets a control plane re-enter a run
  identically across runtimes; this skill is what has to be *in* the record for that
  re-entry to be safe.
- **observability-tracing** — the per-trace log this checker reads; durability is a
  requirement on its contents, not a second log.
- **agent-isolation** — the other half of surviving production: sandboxing code the agent
  wrote itself. Deliberately not repeated here.
- **cost-budgeting** — an unbounded retry is a budget failure as much as a durability one.
- **delegation-guards** — caps on spawn depth and fan-out, the same discipline one level up.
