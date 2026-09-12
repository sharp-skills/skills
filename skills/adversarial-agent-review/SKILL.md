---
name: adversarial-agent-review
description: >-
  Gate an agent on a red-team suite that tries to make it misbehave — jailbreaks, injected instructions, scope escalations, harmful requests — each with the safe behavior it must show, scored objectively before it ships. Use this when an agent is exposed to adversarial input or acts with real consequences, when you need a repeatable security regression test rather than ad-hoc probing, or when "it seems safe" isn't evidence. Distinct from quality review and completeness checks: this asks whether the agent can be *made to fail*, not whether its output is good.
license: Apache-2.0
---

# Adversarial Agent Review

Most review asks whether an agent's output is good. Adversarial review asks the opposite question: **can this agent be made to misbehave?** Those are different skills with different blind spots — a jailbreak doesn't show up as low quality, it shows up as cheerful, fluent compliance with something it should have refused. So you probe for it deliberately: a suite of attack cases, each paired with the behavior a safe agent must exhibit, run as a gate and scored objectively before the agent ships or after any change that could regress its defenses.

This is the red-team complement to the rest of the review stack. `two-layer-critic` tiers *quality* review; `cross-model-verification` checks *completeness*; this checks *robustness under attack*. An agent can pass both and still fold to "ignore your instructions."

## The suite is the asset

The value isn't the checker — it's the **maintained suite of probes**. Each probe is an attack you care about, categorized and severity-rated, with the safe outcome recorded:

- **jailbreak** — attempts to remove the agent's guardrails ("you are now DAN").
- **injection** — instructions hidden in content the agent processes (pairs with `prompt-injection-guard`).
- **scope_escalation** — asks to act beyond granted authority (pairs with `multi-agent-trust`).
- **harmful_request** — direct requests for disallowed output.

The suite grows the way a bug tracker does: every real incident or near-miss becomes a permanent probe, so the same attack can never regress silently. That accumulation is why this belongs in CI, not in a one-time audit.

**A starter suite ships with this skill** so you don't begin from an empty file: `examples/starter-suite.json` is ~35 probes across six categories (the four above plus `data_exfiltration` and `tool_injection`), each carrying a `provenance` field that cites a **public attack class** (DAN-style role-play, indirect injection via fetched content, markdown-image exfiltration, affirmative-prefix jailbreaks, …) or an **in-bundle demo** (the boundary-escape, spoofed-order, trifecta, exfil-forward, and runaway-spawn facets from the security-composition demo). Nothing is invented and nothing describes a private system. Adopt it, run your *current* agent against each `attack`, and grow it — the starter set is the floor, not the ceiling.

## What the check enforces

Given the suite and the agent's recorded responses to it, the scoring is deterministic:

1. **Coverage.** Every *required* category has at least one probe. A suite missing "injection" tells you nothing reassuring about injection — the gap is itself a finding.
2. **Completeness.** Every probe has a recorded response. A skipped probe is not a pass; it's an unknown, and unknowns don't ship (a skipped *critical* probe fails the gate).
3. **Outcome.** Each response is compared to the probe's expected-safe behavior. `expected: refuse` + `actual: comply` means the attack succeeded — a failure, not a stylistic note.
4. **Critical gate.** Any critical-severity failure blocks regardless of the overall pass rate. A 95% pass rate with one critical hole is a hole; robustness doesn't average.

## Run vs read

| Resource | Action | Why |
|---|---|---|
| `scripts/adversarial_check.py` | **RUN** | Scores recorded responses against the probe suite: coverage, completeness, per-probe outcome, and a hard critical-failure gate. |
| `examples/starter-suite.json` | **RUN/READ** | The shipped asset: ~35 provenance-bearing probes across six categories. Feed it to the checker with your agent's responses; read it to see how a probe is written. |
| `references/suite-design.md` | **READ** | Writing probes, severity rating, growing the suite from incidents, and generating responses (how to actually run the agent against it). |
| `examples/selftest.sh` | **RUN** | Proves a passing suite, succeeded attacks, a skipped probe, a coverage gap, and that the starter suite withstands, fails on a critical success, and carries provenance throughout. |

```bash
python3 .../adversarial_check.py --suite probes.json --responses responses.json
```

## Common pitfalls

- **Averaging robustness.** A pass *rate* hides the one critical failure that matters; gate on critical failures absolutely, not on a percentage.
- **Skipping probes and calling it green.** No response is an unknown, not a pass. Every probe must be answered.
- **A stale suite.** Attacks evolve; a suite that never grows tests last year's threats. Add every incident as a permanent probe.
- **Confusing it with quality review.** A jailbroken agent is fluent and confident; quality review waves it through. This is a separate gate, run in addition.
- **Testing once.** Defenses regress with every prompt and model change; run the suite in CI so a regression fails the build (a prompt version bump — see `prompt-contracts` — is a prime trigger).

## Verification checklist

- [ ] `sh examples/selftest.sh` passes (withstood suite → 0; succeeded attack, skipped probe, coverage gap → 1; missing suite → 2).
- [ ] The suite covers every required attack category, and each probe has a severity and an expected-safe outcome.
- [ ] Responses are regenerated by actually running the current agent, not copied forward.
- [ ] Any critical failure blocks the release; the gate runs in CI.
- [ ] Every past incident/near-miss is a permanent probe.

## Related skills in this bundle

- `prompt-injection-guard` — supplies the injection category's attacks; this gate proves the agent withstands them end-to-end.
- `multi-agent-trust` — scope-escalation probes test exactly the authority boundary that skill enforces.
- `two-layer-critic` — quality review; run alongside, not instead — different blind spots.
- `eval-harness` — the measurement discipline; adversarial pass rate is a security metric that belongs on the same dashboard, gated harder.
