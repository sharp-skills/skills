---
name: cross-model-verification
description: Verify one model's hand-off artifact with a different model family before downstream agents execute it — same-model authoring, cross-model verification — catching gaps and contradictions that same-family review shares blind spots with. Use this when rework loops trace back to incomplete hand-offs (execution prompts, blueprints, specs), when self-review keeps grading its own work too kindly, when you want a second opinion that can never block the pipeline while it's being evaluated, or when wiring an external verifier that must fail soft.
license: Apache-2.0
---

# Cross-Model Verification of Hand-offs

A model reviewing its own family's output shares its blind spots: what one instance under-specified, a sibling tends not to notice. Measured in the source system: an agent's self-assessment scored 88 where the objective pipeline evaluation said 84.2 — self-review flatters. The cheapest place to buy an *independent* pair of eyes is the hand-off artifact: the execution prompt, spec, or blueprint that downstream agents will spend real tokens executing. Catch a gap there and you save the whole rework loop it would have caused.

The design that worked: **same-model authoring, cross-model verification.** The original model family keeps authoring (that's where its strength is); a different family verifies completeness and consistency — a task that plays to strict-instruction-adherence strengths and requires no creativity. Concretely, this is a Claude agent authoring and an OpenAI (Codex / GPT) or Gemini agent verifying, or any pairing where the verifier is a *different family* than the author — the point is the blind spots don't overlap. The verifier does not rewrite, does not improve, does not co-author. It answers one question: *is this hand-off complete and internally consistent against its upstream source?*

## Use this when

- Rework loops (re-implementation, re-architecture) trace back to hand-offs that were missing a requirement or contradicted themselves.
- Review exists but is same-family, and its findings correlate suspiciously with what the author already believed.
- You want to trial an external verifier without making the pipeline depend on it.
- A hand-off has enumerable required parts (objectives, file lists, no-touch zones, acceptance criteria) — i.e., completeness is checkable at all.

Do not use this for taste. Cross-model verification earns its cost on *completeness and consistency* — objective properties with yes/no answers. "Is this design good?" sent to a second model produces a second opinion, not verification.

## The five design rules

1. **Author ≠ verifier ≠ editor.** The verifier returns a verdict (gaps, contradictions) — never a rewrite. The moment the verifier edits, you have two authors and zero verification.
2. **Enumerate what to check.** The verifier receives the explicit field list (objective, files, no-touch zones, acceptance criteria, constraints) and must pronounce on each. Open-ended "review this" invites recency bias — the model checks what it read last and waves the rest through.
3. **Never block while unproven.** A failed, absent, or malformed verifier response degrades to PASS with a note — the pipeline runs exactly as it would without the check (the control arm). Only after measured value does the verdict earn gating power. An advisory layer that can wedge the pipeline gets deleted the first week.
4. **Deterministic floor under the model.** Field presence and mechanical contradictions (a path in both `no_touch_zones` and `files_to_modify`) are checked by code before any model is called. The cross-model layer spends its attention only on what code can't see: semantic gaps against the upstream source.
5. **Couple via a seam, not the registry.** The verifier is a transport/command the check calls — swappable, fakeable in tests, absent in CI without breakage. Wiring it into the routing registry couples an experiment to the system's source of truth.

## Run vs read

| Resource | Action | Why |
|---|---|---|
| `scripts/verify_handoff.py` | **RUN** | Deterministic completeness/contradiction check + optional `--verifier-cmd` cross-model layer that fails soft. |
| `references/design.md` | **READ** | The self-review bias evidence, verifier prompt design, control-arm rollout, what to measure before letting it gate. |
| `examples/selftest.sh` | **RUN** | Proves gap/contradiction detection, verifier wiring, and fail-soft on shipped fixtures. |

```bash
# deterministic floor only
python3 .../verify_handoff.py handoff.json --spec handoff-spec.json

# with a cross-model verifier (any CLI; prompt as last arg; JSON verdict on stdout)
python3 .../verify_handoff.py handoff.json --spec handoff-spec.json \
    --upstream blueprint.json --verifier-cmd "some-model-cli --json"
```

## Common pitfalls

- **Letting the verifier rewrite.** Rule 1. The output is a verdict; anything more erases authorship boundaries and audit trails.
- **Gating on day one.** Rule 3 exists because an unmeasured gate is pure downside: it can only cause false blocks until proven.
- **Open-ended review prompts.** Enumerate fields or accept recency bias.
- **Paying a premium model for the floor.** Field presence and path conflicts are code (`$0`); spend model tokens only above the floor (see `cost-budgeting`).
- **Verifying everything.** The hand-off between authoring and execution is the leverage point; verifying every intermediate output turns a check into a tax.
- **Same-family "cross" verification.** A sibling model shares training blind spots; the independence premium comes from a genuinely different family.

## Verification checklist

- [ ] `sh examples/selftest.sh` passes (complete hand-off → 0, gaps/contradictions → 1, dead verifier fails soft → 0 with note).
- [ ] The deterministic floor catches a path listed in both no-touch and modify lists.
- [ ] The verifier command is absent in CI and the check still passes (control arm).
- [ ] Verifier verdicts are logged with the hand-off id (you are accumulating the evidence that decides gating).
- [ ] The verifier prompt enumerates every required field by name.

## Related skills in this bundle

- `prompt-contracts` — verifies the *contract vocabulary* statically; this skill verifies the *content* of one hand-off against its upstream source. Different axes, both pre-execution.
- `two-layer-critic` — the review economics sibling: cheap broad review always, expensive review reserved; cross-model verification is the third, independent tier.
- `experience-loop` — verifier findings are premium learning entries; recurring gap categories graduate into authoring-prompt fixes.
- `cost-budgeting` — the rework loop this check prevents is usually the most expensive path in the pipeline; that's the ROI calculation.
