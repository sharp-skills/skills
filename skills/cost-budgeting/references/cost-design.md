# Cost design notes

## The timeout incident, in full

A production pipeline task was packed into one oversized agent call. The
call hit the runtime's fixed per-call timeout (600s) and died — after
consuming the full context it had been given. The failure was misdiagnosed
three times in sequence: first as a model availability problem, then as a
quota problem, then as a platform bug. The actual cause: **the call was
larger than any reasonable timeout should be asked to cover**.

What didn't work: raising the timeout. Each raise moved the failure to the
next larger task.

What worked, permanently:

1. **Decompose** — the oversized call became two calls with a hand-off.
2. **Bounded generosity** — each call got a generous but explicit timeout
   (1200s), so the limit documents intent instead of encoding hope.
3. **Capped turns** — an explicit max-turns per call (8–10), because an
   agent that hasn't converged by then is looping, not thinking.
4. **Declared budgets** — per-agent token ceilings that flag an oversized
   call *before* it runs out a clock.

The rule that generalizes: **a call approaching its budget is a
decomposition candidate**. Timeouts and budgets are smoke detectors;
decomposition is the fire exit.

## Deriving budgets from traces

Budgets set by intuition either never fire or always fire. Derivation:

1. Collect healthy runs (flight recorder, `observability-tracing`).
2. Per agent, take the median input/output tokens across those runs.
3. Budget = median × 1.5 (headroom for legitimate variance).
4. Record the derivation in budgets.json (`derived_from`) — a budget whose
   origin is unknown cannot be legitimately tightened or loosened later.
5. Re-derive after structural changes (new prompt sizes, new models,
   triage enabled) — stale budgets fail in both directions.

## The model-tier table

Cost policy's second half: which model serves which stage. The pattern that
held in the source system:

| Tier | Serves | Rationale |
|---|---|---|
| Premium | Architecture review, final gates, high-stakes legal/security analysis | Dense reasoning; being wrong is expensive |
| Standard | Most pipeline specialists | Judgment present, stakes bounded |
| Cheap | Classification, triage, extraction, bookkeeping | No judgment authority (see `task-triage`: the classifier proposes, rules dispose) |
| Code (no model) | Rule-defined work | See `mechanize-agents` — the cheapest call is no call |

Two disciplines make the table real: premium is **never the default** (each
premium assignment is a listed, justified exception), and review-type agents
escalate tier by *mode* (cheap review on routine runs, premium only on
high-stakes runs) rather than always paying for the strongest reviewer.

## Retry economics

Every retry path multiplies spend by its cap — and by infinity without one.
The reject-retry loop that motivated the status gate's cap (see
`status-gates`) was simultaneously a billing incident: identical tokens
re-spent on an identical guaranteed failure until a human noticed. When
pricing a pipeline, multiply each stage's cost by its worst-case retries;
if that number alarms you, the cap is too high or the failure it retries is
fixable upstream (usually via `prompt-contracts`).
