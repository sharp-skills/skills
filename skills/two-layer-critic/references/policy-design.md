# Critic policy design notes

## Why the cap works (three findings)

An adversarial reviewer with unlimited findings optimizes for looking
thorough: ten findings, seven of them trivia, severity inflation to justify
the count. Authors respond by skimming — the review is technically complete
and practically ignored.

A cap inverts the reviewer's incentive: three slots force ranking, and
ranking is the actual expertise. Observed effect in the source system:
capped reviews got *acted on* — every finding either fixed or explicitly
rebutted, because three items is a to-do list and ten is a document.

Cap discipline: the cap is per-review, not per-artifact-forever. If a FAIL's
three findings are fixed and the re-review finds three more, that's the
process working — not a reason to raise the cap.

## Why pass/fail, not scores

A 0–100 review score invites negotiation ("74 is basically passing") and
drifts upward under social pressure. Pass/fail with named reasons has no
negotiable middle: either the named defects block, or they don't. Numeric
quality measurement belongs to the deterministic evaluator (`eval-harness`),
where no one can argue with the rubric mid-review.

## Tier routing rationale

The run's stakes are declared once, upstream, by the orchestrating
authority (the same declaration that sets pipeline depth — see the mode
concept in `task-triage` and `status-gates`). The critic inherits that
declaration:

| Run mode | Critic tier | Why |
|---|---|---|
| Fast track | **none** | The org declared urgency; mandatory review contradicts it. Risk was accepted at declaration time. |
| Standard | cheap | Broad sanity at commodity cost on every routine run. |
| High-stakes | premium | Dense adversarial reasoning where being wrong is expensive — the quota exists for exactly these runs. |

Escalation between layers: the cheap tier may recommend escalation
("finding exceeds my confidence — premium review advised") but may not
invoke the premium tier itself; tier changes are the orchestrator's
decision, or the budget dies by a thousand justified exceptions.

## The review → learning pipeline

Findings are structured (`severity, location, claim, fix_direction`)
precisely so they can flow into the experience loop (`experience-loop`):

1. Each finding lands in the *reviewed agent's* learning record under a
   category derived from the claim.
2. Distillation counts categories per agent; a category recurring across
   reviews graduates into that agent's prompt or an output contract
   (`prompt-contracts`).
3. The finding entries are then retired — the defect class is now enforced
   structurally, and the critic stops paying to rediscover it.

This loop is what makes review an investment instead of a recurring fee.
The bidirectional variant (the critic also learns which of its findings
authors rebutted successfully) tunes the critic's own aim over time.

## Boundary with cross-model verification

| | two-layer-critic | cross-model-verification |
|---|---|---|
| Question | "attack this design" | "is this hand-off complete?" |
| Judgment | adversarial, subjective | mechanical, objective |
| Model family | same family, tiered by cost | deliberately different family |
| Output | ≤3 structured findings + verdict | gaps/contradictions list |
| May block? | yes (it's a gate) | not until measured (control arm) |

Run both; they catch disjoint classes. Merging them loses either the
independence (if merged into the critic) or the judgment (if merged into
the verifier).
