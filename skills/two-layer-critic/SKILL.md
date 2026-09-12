---
name: two-layer-critic
description: Structure adversarial review in a multi-agent pipeline as two tiers — a cheap model reviewing broadly on routine runs, a premium model reserved for high-stakes runs — with findings capped and structured so review output stays actionable instead of becoming noise. Use this when review costs rival production costs, when the strongest model reviews trivia while its quota starves real gates, when review output is a wall of prose nobody acts on, or when the reviewer's findings never feed back into agent improvement.
license: Apache-2.0
---

# Two-Layer Adversarial Critic

Review is the easiest place to overspend and the easiest place to under-deliver — often simultaneously. The failure pattern: the strongest available model reviews everything (burning its quota on routine runs), produces ten-paragraph essays per artifact (which downstream agents skim and ignore), and its insights evaporate at session end. The fix is economic and structural at once: **two tiers by stakes, findings capped and structured, and a feedback loop into agent experience.**

In the source system the critic reviews design-stage outputs with a cheap-tier model on routine runs; the premium tier engages only when the run is declared high-stakes. Findings are capped at three, each structured; the verdict is pass/fail. Review cost stopped competing with production cost, and — the surprising part — capped review got *more* actionable, not less.

## Use this when

- Review spend rivals or exceeds production spend (see `cost-budgeting`'s tier table).
- The premium model's quota disappears into routine reviews while genuinely high-stakes runs queue.
- Review output is prose walls; authors respond to none of it and resent all of it.
- The same finding recurs across reviews because nothing retains it.

Do not confuse this with cross-model verification (`cross-model-verification`): the critic is *adversarial judgment within the family* ("attack this design"); cross-model is *independent mechanical verification* ("is this complete?"). A mature pipeline runs both — they catch disjoint failure classes.

## The four rules

1. **Tier by declared stakes, not by artifact.** The run's mode (routine / standard / high-stakes) is set once, upstream, by the orchestrating authority — and the critic's tier follows it. Deciding tier per-artifact re-litigates the question every time and always drifts expensive. On explicitly fast-tracked runs the critic doesn't run at all: a fast track with mandatory review is not a fast track.
2. **Cap findings — three is the number.** An adversarial reviewer told "find everything" pads with trivia to look thorough. Told "you get three findings", it spends them on what matters. The cap converts review from coverage theater into forced prioritization. (Empirically: authors act on three findings; they skim ten.)
3. **Findings are structured or they didn't happen.** Each finding: severity, location, claim, and what-would-fix-it. The verdict: pass or fail, nothing in between. Structured findings can be counted, routed, and retired; prose can only be read once.
4. **Findings feed the loop.** Review findings are the highest-grade learning input the system produces — a domain expert already prioritized them. Recurring finding categories per agent flow into that agent's experience record (see `experience-loop`) and eventually graduate into prompt/contract fixes. A critic without this loop re-discovers the same defect monthly, at premium rates.

## Run vs read

| Resource | Action | Why |
|---|---|---|
| `scripts/critic_policy.py` | **RUN** | Enforces the policy: routes run-mode → tier (or skip), validates review output (cap, structure, verdict). |
| `references/policy-design.md` | **READ** | Why caps work, tier-routing rationale, the review→learning pipeline, escalation between layers. |
| `examples/selftest.sh` | **RUN** | Proves routing and output validation on shipped fixtures. |

```bash
# which tier reviews this run?
python3 .../critic_policy.py route --mode STANDARD --policy critic-policy.json

# does this review output satisfy the policy?
python3 .../critic_policy.py validate review-output.json --policy critic-policy.json
```

## Common pitfalls

- **Premium as the review default.** The premium tier is a budget line, not a quality baseline; rule 1 exists because "just this once" compounds into the default.
- **Uncapped findings.** Ten findings = zero priorities. The cap is the feature.
- **Score creep.** A critic that emits 0–100 scores invites negotiation; pass/fail with three named reasons invites fixes.
- **Reviewing on the fast track.** If the org declared the run urgent, mandatory review contradicts the declaration — remove the review or the declaration.
- **Findings that die in the review.** Rule 4; without the loop you are renting the same insight repeatedly.
- **Letting the critic edit.** Same boundary as verification: the critic names defects; the author fixes them. A critic that rewrites is a second author with veto power.

## Verification checklist

- [ ] `sh examples/selftest.sh` passes (routing per mode, cap enforced, structure enforced, verdict enforced).
- [ ] Premium-tier reviews appear only on runs declared high-stakes (auditable from traces).
- [ ] Review outputs in production validate against the policy (wire `validate` into the pipeline).
- [ ] At least one prompt/contract change traces back to a recurring finding category.
- [ ] The fast track demonstrably skips the critic.

## Related skills in this bundle

- `cross-model-verification` — the independent-verification sibling; run both, they catch disjoint classes.
- `experience-loop` — where findings go to compound; the critic is its richest feeder.
- `cost-budgeting` — the tier table this policy implements for the review column.
- `eval-harness` — structural scoring downstream of review; a failed review should correlate with eval flags, and disagreement between them is a calibration finding.
