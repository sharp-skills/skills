# Cross-model verification design notes

## The self-review evidence

Two data points from the source system drove this skill:

1. An agent invoked outside the instrumented pipeline **self-assessed at
   88** where the objective evaluation of equivalent work through the
   pipeline scored **84.2**. Self-review flatters — not by lying, but by
   sharing the author's assumptions about what "done" means.
2. The dominant rework loop (re-implementation requests from QA back to
   engineering) traced repeatedly to hand-offs that were *incomplete* —
   a blueprint requirement with no corresponding file, criterion, or
   constraint in the execution prompt. Same-family review had read those
   hand-offs and passed them.

Hence the architecture: keep authoring in the family that authors best;
buy independence exactly at the hand-off, from a different family, for a
task (completeness/consistency) where "different" matters more than
"stronger".

## Verifier prompt design

- **Role framing**: "independent auditor, NOT the author" — measurably
  reduces the verifier's tendency to improve rather than judge.
- **Field enumeration**: name every field to check. Without it the model
  audits what it read most recently (recency bias) and waves earlier
  sections through.
- **Negative instructions**: "do not rewrite, do not judge code quality" —
  the two failure modes of verifier drift.
- **Closed output**: "ONLY JSON {gaps, contradictions}" — anything else is
  unparseable and (by the fail-soft rule) discarded, so the format
  instruction protects the check's own reliability.

## The control-arm rollout

The check ships **unable to block**: absent, dead, or malformed verifier
output degrades to PASS-with-note. This is not caution theater — it's the
experiment design:

1. Run with the verifier logging verdicts but not gating (weeks).
2. Measure: of the hand-offs the verifier flagged, how many actually caused
   downstream rework? Of those it passed, how many did?
3. Only a verifier whose flags predict real rework earns gating power —
   and then gate on the specific finding types that predicted, not on
   everything it says.

An unmeasured advisory layer promoted straight to a gate has only one
possible first impression: a false block, followed by deletion.

## Seam coupling

The verifier is reached through a transport/command seam, not through the
routing registry. Reasons: the registry is a no-touch source of truth
(see `governance-hooks`), experiments must be attachable/detachable without
touching it; tests inject a fake transport; CI runs with no verifier at all
and the check still passes (control arm). The general rule: **experimental
layers couple to seams, never to sources of truth.**

## Where cross-model pays (and where it doesn't)

| Task | Cross-model worth it? | Why |
|---|---|---|
| Hand-off completeness/consistency | **Yes** | Objective, enumerable, blind-spot-sensitive |
| Code/tests verification vs spec | **Yes** | Different training catches different bug classes |
| Design taste, strategy, tone | No | You get a second opinion, not verification |
| Mechanical field presence | No — code does it | See the deterministic floor; models cost money |
