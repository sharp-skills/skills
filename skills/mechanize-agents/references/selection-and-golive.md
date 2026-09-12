# Selecting what to mechanize, and how to go live

## The selection test

Write the complete input→output specification for the agent. Three outcomes:

| You can write… | Verdict | Example from the source system |
|---|---|---|
| The whole spec | **Mechanize** | Git/PR operations: payload → exact command → canonical event |
| The spec except named edge cases | **Hybrid** | Financial gate: ROI formula is code; missing/contradictory inputs defer to the analyst |
| Not really a spec | **Keep the LLM** | Anything where informed people could disagree (analysis, design, review) |

Priority order among candidates: highest call frequency × highest blast
radius of a hallucination. Session bookkeeping (every run) and git operations
(irreversible side effects) rank far above occasional formatting steps.

## Payload validation patterns

The handler's input was authored by a model. Treat it as hostile:

- **Flag-shaped values**: reject any positional value starting with `-` —
  the classic escalation is a branch name of `--force`.
- **Format allowlists**: repository as strict `owner/name` regex; identifiers
  as `[A-Za-z0-9._-]+`; nothing that can traverse paths.
- **Directory confinement**: filesystem/git operations run only inside
  explicitly declared directories (an env-var allowlist). A rollback handler
  must be *unable* to run in an arbitrary checkout, not merely instructed
  not to.
- **Known-operation dispatch**: the payload selects from a fixed table of
  operations; unknown operation = reject, not best-effort.

## Go-live runbook (deployment ≠ activation)

1. **Land dark.** The handler ships with side effects disabled: it builds
   commands and returns events, executing nothing. Merging is now safe by
   construction.
2. **Shadow on traces.** Run real payloads through the dry handler; diff its
   would-be commands/events against what the LLM agent actually did (the
   flight recorder from `observability-tracing` makes this a file diff).
3. **Flip the registry** (`runtime: "code"`) — routing now fans out to the
   handler, still dry where side effects exist.
4. **Enable execution** with the explicit env flag, lowest-risk operation
   first (issue creation before PR merge before rollback).
5. **Keep the prompt.** The LLM version remains in the repo as fallback and
   as the intent spec; flip-back is one registry edit.

## Hybrid defer: the contract, precisely

- The defer status is a reserved string (e.g. `ANALYST_REQUIRED`) returned
  by the code path with `defer_reason` attached.
- It is **not** in any agent's `publishes` — the audit script enforces this.
  The orchestrator intercepts it and re-invokes the LLM analyst with the
  reason as context; the bus never sees it.
- Every defer is logged. The accumulated defer reasons are the backlog for
  mechanizing the next slice: when one reason dominates, its handling has
  usually become spec-able.

## Measured effect in the source system

Three agents flipped (git automation, session manager, financial gate):
zero changes to schemas, routing, or downstream consumers; identical event
sequences on identical inputs; LLM calls removed from the hottest
bookkeeping path. The financial gate runs as hybrid — deterministic verdict
when inputs are complete, defer to the analyst otherwise — with no new bus
events.
