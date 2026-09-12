# Experience loop design notes

## The capture-point bug

The source system originally recorded experience at the final approval gate.
Consequence: every agent scheduled *after* that gate — deployment, legal
clearance, analytics, growth — accumulated nothing. No error, no gap in the
file, just a set of agents whose experience silently stayed at bootstrap
values for weeks. Found during an audit, not by a failure.

Fix: hook the recorder to actual run **completion** (the last event of the
trace), and audit per-agent write recency, not just file recency. The
general form of the bug: *your capture point defines who gets to learn* —
choose it by looking at who runs last, not who matters most.

## Why EMA and not an average

- A plain average over all history makes month-old behavior forever equal
  to yesterday's; after a prompt rewrite the number describes an agent that
  no longer exists.
- A "last value" is the opposite failure: one bad run erases a year.
- EMA (`α ≈ 0.3`) is the standard compromise: roughly, the last five runs
  carry ~80% of the weight, everything older fades smoothly. One outlier
  moves the number visibly but not decisively.
- Bootstrap new agents at a typical floor (70), not zero — a zero start
  makes every new agent look catastrophic for its first ten runs.
- After structural changes (new prompt, new model), re-bootstrap the agent
  deliberately and note why: continuity of the number would be a lie.

## The distillation discipline (where the ROI lives)

Recording is inventory; distillation is income. The working cadence:

1. Periodically (weekly, or at N new entries) group active learnings by
   `category` and count.
2. A category that recurs ≥3 times is a graduation candidate: the fix
   belongs in a **prompt rule, schema/contract tightening** (see
   `prompt-contracts`), **a governance zone** (see `governance-hooks`),
   or a new bundle skill — somewhere structural, where it acts without
   being remembered.
3. After graduating, mark the entries `retired: true` (never delete — the
   trail of *why a prompt changed* is provenance).
4. If a category recurs but resists graduation, that is a finding about the
   system, not the buffer: usually the insight is real but the fix owner is
   ambiguous. Assign one.

The anti-pattern this prevents: a learnings file that grows for months while
the prompts never change. That file is a diary. The loop closes only when a
recorded lesson stops needing to be remembered because the system enforces
it.

## What to load at session start

Not the archive. Per agent: the EMA, the session count, and the *distilled
top categories* (three lines). Context is a budget (`cost-budgeting`), and
raw learnings are exactly the kind of well-intentioned ballast that crowds
out the task. The archive stays on disk for audits and distillation runs.
