# Gate design notes

## Placement

The gate belongs at the single point where an output becomes a routing
decision — the dispatcher/orchestrator that reads `status` and publishes it
as an event. Not in each agent (N copies drift), not in the schema layer
(schemas can't stop a runtime disobedience, and an enum that duplicates the
registry is a second copy of truth — see `prompt-contracts`).

```
agent output ──> [ status gate ] ──ok──> publish status as event ──> subscribers
                      │
                   reject
                      ▼
        teaching message + retry (capped) ──cap──> PIPELINE_FAILED + history
```

## The reject path, precisely

1. Gate rejects → the agent gets the teaching message (allowed vocabulary,
   instruction to re-emit, instruction not to invent).
2. Dispatcher increments `rejects[agent]` for this run.
3. `rejects[agent] < CAP` (2–3): re-invoke the agent with the message
   appended to its context.
4. `rejects[agent] >= CAP`: stop retrying. Emit the shared failure terminal
   with the rejection history in the payload, so the failure is routable
   (watchdogs and humans see it) instead of a stuck loop.

The cap exists because the first production version of this gate lacked it:
a schema taught a forbidden status, the gate correctly rejected it, the
runtime automatically retried, and the pipeline burned quota in a perfect
reject-retry loop until a human intervened. Correct gate + missing cap =
denial of service against yourself.

## Message design

Measured effect in production: bare rejections ("invalid status") made the
model retry synonyms of the same invention (`SUCCESS` → `DONE` → `OK`).
Including the full allowed list plus the negative instruction ("do not
invent new ones") converged in one retry. The message is part of the
mechanism, not logging — write it for the model.

## Warn → enforce rollout

Order matters and each step has a reason:

1. **Static alignment first** (`prompt-contracts` checker green). Enforcing
   against prompts that teach forbidden statuses converts every run into a
   reject storm — the gate will be blamed and disabled.
2. **Warn mode**: log would-be rejections without blocking for several runs.
   Triage each warning: model disobedience (gate is right, keep it) vs
   contract drift the static pass missed (fix files, re-run static check).
3. **Enforce** with the cap wired.
4. **Delete rollout shims.** Any "temporarily also allow X" added during
   the flip must die with the rollout ticket. A relaxed gate that outlives
   its incident is the next incident.

## Statuses vs events: the two legitimate exceptions

- **Skip forms** (`*_SKIPPED`): a conditional agent declaring "not needed
  this run". Downstream treats it as a no-op event; allowing the suffix
  class avoids registering N boilerplate events.
- **Shared failure terminal** (`PIPELINE_FAILED`): every agent may fail;
  requiring each to register a personal failure event duplicates the
  registry for no routing benefit.

Both are *config*, not code — if your system uses different conventions,
change the config, and keep it identical to the `prompt-contracts` config so
the static and runtime halves enforce the same contract.
