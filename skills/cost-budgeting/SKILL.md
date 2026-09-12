---
name: cost-budgeting
description: Declare per-agent and per-run token/step budgets for a multi-agent pipeline and check recorded runs against them, so cost failures surface as named overruns instead of surprise bills and mid-run timeouts. Use this when one oversized agent call dies at a wrapper timeout after burning its whole context, when premium-model calls appear on routine steps, when a retry loop quietly multiplies spend, or when nobody can say which agent consumes the budget.
license: Apache-2.0
---

# Cost & Token Budgeting for Multi-Agent Runs

Multi-agent cost failures are structural, not gradual. The bill doesn't creep — it spikes, and always through one of three shapes: an **oversized single call** that hits a wrapper timeout and burns everything it consumed before dying; a **premium model on a mechanical step**, multiplied by every run; or a **retry loop** re-spending the same tokens on the same failure. Budgets turn all three from surprises into named, checkable overruns.

This skill exists because of a production incident: a task packed into one oversized agent call died at a fixed per-call timeout — after consuming the full context it had been given. The diagnosis was mis-read three times (model quota? platform bug?) before the real cause surfaced: the *call was bigger than any timeout should be asked to cover*. The durable fix was not a bigger timeout — it was decomposition plus declared budgets that make an oversized call visible **before** it runs out the clock.

## Use this when

- An agent call times out mid-run and the tokens it consumed are simply gone.
- The monthly bill moved and nobody can name the agent responsible.
- Premium-tier models serve steps that a cheap tier handles identically.
- Retries exist anywhere without a cap (see `status-gates` — a reject loop is also a billing loop).

## The three budget rules

1. **Decompose over extend.** A call that approaches its time or token budget is a *decomposition candidate*, not a timeout-increase request. Raising the limit hides the problem exactly until the next size step, where it fails worse. In the source incident, splitting one oversized call into two, each with a bounded generous timeout and a capped turn count, fixed what three rounds of limit-raising had not.
2. **Budgets are declared per agent, not felt per month.** Each agent gets explicit input/output token ceilings (and optionally a step count); the run gets a total. The numbers come from your own traces — set them at ~1.5× the observed healthy median, then tighten. A budget nobody derived from data will either never fire or always fire.
3. **Tier models by judgment density, not by habit.** Premium models go where being wrong is expensive and reasoning is dense (architecture review, final gates); the cheap tier does classification, extraction, bookkeeping. Write the tier table down next to the budgets — both are cost policy, and both drift when they live in nobody's file.

## Run vs read

| Resource | Action | Why |
|---|---|---|
| `scripts/budget_check.py` | **RUN** | Checks a recorded trace (observability-tracing JSONL) against budgets.json; per-agent and per-run overruns; CI exit codes. |
| `references/cost-design.md` | **READ** | The timeout incident in full, deriving budgets from traces, the model-tier table pattern, retry-loop economics. |
| `examples/selftest.sh` | **RUN** | Proves overrun detection on shipped healthy and over-budget traces. |

```bash
python3 .../budget_check.py --traces-dir .context/traces --latest --budgets budgets.json
python3 .../budget_check.py my-run-id --budgets budgets.json     # specific run, CI-friendly
```

The input is the same per-trace JSONL the bundle's flight recorder writes — record with `observability-tracing`, budget-check here, score with `eval-harness`.

## Common pitfalls

- **Raising the timeout again.** The wrapper timeout is a smoke detector; a bigger battery does not put out the fire. Decompose.
- **One global budget.** A run total without per-agent ceilings tells you *that* you overspent, never *who* — which is the question.
- **Budgets set by intuition.** Derive from trace history or the check is noise (fires always or never).
- **Uncapped retries anywhere.** Every retry path is a spend multiplier; caps belong to cost policy, not just correctness (see `status-gates`).
- **Premium model as default.** Defaults are multiplied by every call; tier tables exist to make each premium call a decision, not an inheritance.
- **Budgeting the model but not the tools.** Tool calls carry token costs too (results re-enter the context); the check counts every event's tokens, not only completions.

## Verification checklist

- [ ] `sh examples/selftest.sh` passes (healthy trace → 0, per-agent and per-run overruns → 1, malformed input → 2).
- [ ] Every pipeline agent has an entry in budgets.json (the check reports uncovered agents).
- [ ] Budgets trace back to observed medians (a comment/field in budgets.json says from which period).
- [ ] The model-tier table exists and premium exceptions are individually justified.
- [ ] Budget check runs in CI against the latest recorded run.

## Related skills in this bundle

- `observability-tracing` — produces the token-per-event records this skill consumes; without the flight recorder there is nothing to budget against.
- `eval-harness` — quality regression and cost regression are siblings; run both against the same trace, baseline both.
- `status-gates` — its retry cap is the enforcement half of rule 3's economics.
- `task-triage` — the largest cost lever of all: the cheapest agent call is the one that never runs.
