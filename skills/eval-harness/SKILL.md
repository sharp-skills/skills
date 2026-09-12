---
name: eval-harness
description: Measure recorded multi-agent run outputs with two deterministic offline checkers plus a judge seam. Structural eval scores observability-tracing JSONL on a 0-100 rubric with flags and a regression baseline. Grounding audit holds claim-with-citation outputs to their sources — every claim must cite a source that exists and substantiates it — catching uncited, mis-cited, and fabricated references. An LLM-judge seam is documented for content quality. Scores, flags and deltas are for humans and CI only — never for the agent being scored. Use when a pipeline is unmeasured, when you need a regression baseline, when a RAG/research agent must be held to its sources, or when a quality metric is being fed back to the agent it measures.
license: Apache-2.0
---

# Eval Harness for Multi-Agent Runs

A multi-agent pipeline can be observable and still have no quality baseline. This skill adds the next layer: read a recorded trace and score whether the emitted outputs are well-formed, in contract, and safe to compare across runs.

The input is the same per-trace JSONL format used by `multi-agent-engineering/observability-tracing`: one run per `.context/traces/<trace_id>.jsonl` file, one event per line. Use the trace viewer to understand what happened; use this evaluator to measure whether the recorded outputs meet the structural contract.

## Use this when

- A pipeline is designed, traced, or demoed, but nobody has measured the outputs.
- You need a deterministic regression baseline for output quality across runs.
- CI should fail on malformed events, missing required fields, low confidence indicators, schema drift, or error/alert flags.
- You want to add content-quality judging later without mixing it into deterministic structural scoring.

Do not use this as proof that an answer is semantically correct. The default score measures structure and contract compliance, not truth, usefulness, or reasoning quality.

## Two layers, kept separate

1. **Structural evaluation — run now.** `scripts/eval_run.py` is stdlib-only, deterministic, and safe for CI. It reads a trace, applies a configurable rubric, prints per-agent scores, an overall 0-100 score, and flags. This layer costs $0 and should be stable enough for regression gates.
2. **Content quality — seam only.** `references/judge.md` documents the `llm_judge()` extension point. The bundled implementation returns `None` until a project deliberately connects a model and credentials. Keep judge results separate from structural scores.

## Who the score is for — never the agent being scored

A measurement becomes a target the moment the thing being measured can read it. **Every score, flag and delta this harness emits is for humans and for CI.** None of it belongs in the prompt, retry message, reward signal, memory, or context of the agent whose output is being scored.

The failure is quiet and it looks exactly like success. Show a writer agent `MISSING_CONTRACT_FIELD:…:risks` and it learns to emit a `risks` field; show it `LOW_CONFIDENCE:…:0.61` and it learns to emit a higher number. Flags go green, the overall score climbs, the baseline gate passes — and nothing about the answers changed. Structural signals are *especially* exposed to this, because the property that makes them good CI gates (mechanically checkable) is the same property that makes them cheap to satisfy directly.

| Class | Who may see it | Why |
|---|---|---|
| **Gate** — overall score, per-agent scores, flags, baseline deltas | humans, CI | Stays comparable only while nothing is steering by it |
| **Feedback** — one specific factual defect ("the `risks` field was absent") | the agent, on the next attempt | Names the defect, not the number; not aggregatable, so there is no curve to climb |

Feedback is legitimate and useful. **A score is not feedback.** If an agent needs to correct itself, hand it the concrete defect and withhold the arithmetic.

**Never expose a proxy for a qualitative property.** Teams that have tried report the same outcome each time, with different proxies: test-coverage percentage, cyclomatic complexity, lines of code, PR counts, token volume. Each is a truthful measurement of *something*; none of them is quality; and each one moves on demand without quality following. The structural score in this skill is a member of that family — it is a proxy for "well-formed" — which is why the limits are stated up front and why the number stays on the human side of the line.

**Match the unit of measure to the unit of value.** Cost per *completed task*, not per token — a model that is cheaper per token can take more turns and cost more per task. Behaviour that *changed*, not a score that *moved*. A truthful measurement in the wrong unit still yields a false conclusion.

## Grounding audit — the content-truth check that *is* deterministic

Structural eval can't tell a fluent lie from a fact, and the judge seam needs a model. But one slice of content-truth is checkable offline: **is a claim grounded in the sources the agent was given?** A hallucination looks perfect — fluent, confident, well-fitted — so you can't catch it by reading for wrongness; the signal is the *absence of support* behind it. `scripts/grounding_check.py` makes that absence measurable by putting every factual claim through three gates:

1. **Cited.** The claim points at one or more source ids. An uncited factual claim is ungrounded by definition — "trust me" is not grounding.
2. **Resolves.** Every cited id exists in the context the agent was actually given. A citation to a source that isn't there is a *fabricated reference* — one of the most convincing hallucination shapes, because "as shown in [4]" lends authority when [4] doesn't exist.
3. **Supported.** The claim's salient terms actually appear in the cited source. Citing a real-but-irrelevant source fails here. This gate is a **lexical-overlap heuristic**: it reliably catches the gross mis-cite, and it does **not** claim to verify entailment — a source can mention the terms and still not support the specific assertion. It's a floor, not a proof.

Built for the pipelines where this matters most — retrieval-augmented generation, summarization, research agents — whose whole value is "grounded in *these* documents." The design ask is that the agent emit **claims-with-citations** (`{claim, sources}`), not just prose: an unstructured paragraph isn't auditable. For the last mile (a source that's cited, resolves, and mentions the terms but still doesn't entail the claim), layer a model-based entailment check on top — `cross-model-verification` is that pattern — but only *after* these structural gates remove the cheap, common failures.

## Run vs read

| Resource | Action | Why |
|---|---|---|
| `scripts/eval_run.py` | **RUN** | Structural: evaluates a trace and exits with CI-friendly status codes. |
| `scripts/grounding_check.py` | **RUN** | Grounding: audits a `{claim, sources}` output against provided context — cited, resolves, terms covered (`--min-support`). |
| `references/rubric.md` | **READ** | Explains the default structural rubric, score math, flags, and JSON config shape. |
| `references/judge.md` | **READ** | Explains how to add an LLM-as-judge integration without contaminating deterministic scores. |
| `references/grounding-design.md` | **READ** | Structuring output as claims, the overlap heuristic's limits, adding an entailment layer, tuning the threshold. |
| `examples/fake_judge.py` / `examples/fake_entailer.py` | **RUN** | Model-free stand-ins the self-test uses to prove the `--judge-cmd` and `--entailment-cmd` seams wire end-to-end and stay advisory. Replace with a real model CLI. |
| `examples/selftest.sh` | **RUN** | Proves structural eval on healthy/weak/malformed traces, grounding on grounded/hallucinated fixtures, AND both model seams (advisory, fail-soft, exit unchanged). |

Start with help:

```bash
python3 multi-agent-engineering/eval-harness/scripts/eval_run.py --help
```

Evaluate the latest trace in the default location:

```bash
python3 multi-agent-engineering/eval-harness/scripts/eval_run.py --latest
```

Evaluate a specific trace and fail CI below a threshold:

```bash
python3 multi-agent-engineering/eval-harness/scripts/eval_run.py run-20260115-a3f2 --min-score 85
```

Try a custom rubric:

```bash
python3 multi-agent-engineering/eval-harness/scripts/eval_run.py run-20260115-a3f2 --rubric eval-rubric.json
```

Enable the judge seam without wiring a real model (reports unavailable rather than inventing a score):

```bash
python3 multi-agent-engineering/eval-harness/scripts/eval_run.py --latest --judge
```

Wire a real, provider-independent judge — any CLI that reads the prompt and prints a JSON verdict; it fails soft and stays advisory (never gates the structural score):

```bash
python3 .../eval_run.py --latest --judge-cmd "my-judge-cli --json"
```

Audit an agent's grounded claims against the sources it was given:

```bash
python3 .../grounding_check.py --output claims.json --context sources.json --min-support 0.5
```

Grounded output exits 0; an uncited, mis-cited, or fabricated-reference claim exits 1. For the last mile the lexical floor can't reach — does the source actually *entail* the claim — add a provider-independent verifier that runs only on survivors, fails soft, and stays advisory:

```bash
python3 .../grounding_check.py --output claims.json --context sources.json \
    --entailment-cmd "my-verifier-cli --json"
```

## Regression baseline

Scores that aren't compared are opinions. Save a known-good run as the baseline, then gate every later run against it:

```bash
# once, on a run you trust:
python3 .../eval_run.py run-20260115-a3f2 --save-baseline eval-baseline.json

# on every later run (CI):
python3 .../eval_run.py --latest --baseline eval-baseline.json
```

The comparison reports overall and per-agent deltas, agents that disappeared, and flags that are new relative to the baseline. Exit 1 on: overall or per-agent score dropping more than `--max-drop` (default 0), a missing agent, or any new blocking flag. Refresh the baseline deliberately (re-run `--save-baseline` after a reviewed improvement), never automatically — an auto-updating baseline is a gate that agrees with everything.

⚠️ **A small delta is weak evidence.** This gate is sound for catching a *collapse*: an agent that stopped emitting, a new blocking flag, a large drop. A few points in either direction says almost nothing. In particular it is the wrong instrument when something structural changes underneath the pipeline — a swapped model version, a rewritten prompt, a new runtime. Practitioners running exactly this comparison report scores holding steady while behaviour shifted enough that users noticed. When the substrate changes, put the recorded runs side by side and read what the agent actually *did*, step by step; the score tells you the contract still holds, not that the behaviour is unchanged.

## CI wiring

```yaml
- name: Structural eval gate
  run: |
    python3 skills/eval-harness/scripts/eval_run.py --latest \
      --traces-dir .context/traces \
      --baseline eval-baseline.json --max-drop 2
```

Commit `eval-baseline.json` to the repo so the gate has a fixed reference; treat baseline refreshes as reviewed changes (they show up in diffs).

## Integration pattern

1. Instrument the pipeline with `observability-tracing` and write one JSONL file per run.
2. Make agent completion events carry generic contract metadata in `meta`, such as required output field names, confidence indicators, schema check results, or alert labels. Keep payloads sanitized; do not log prompts, secrets, or full private responses.
3. Run `eval_run.py` locally while developing.
4. Add the same command to CI once the default or custom threshold is stable.
5. Treat structural regressions as release blockers; treat content-judge results as advisory until you have calibrated them separately.

## What the default rubric expects

The default rubric is intentionally generic. It checks trace event shape, required trace fields, status/error indicators, numeric confidence-like values when present, optional schema validity hints, and alert-like metadata. It does not require domain-specific field names.

Read `references/rubric.md` before changing weights or adding a project-specific rubric file.

## Common pitfalls

- **Routing the score or flags back into the scored agent.** The single failure that invalidates every other number in this skill: the agent starts satisfying the rubric instead of the task, and the harness reports the improvement. Hand over the named defect, never the score. See *Who the score is for*.
- **Scoring content with structural signals.** A perfectly structured event can still be a bad answer. Use the judge seam for content quality.
- **Logging private outputs to make evaluation easier.** Prefer counts, booleans, enum labels, and sanitized field names in `meta`; do not log secrets or user content.
- **Hard-coding one pipeline's contract.** Keep rubric config generic and project-local.
- **Failing on judge unavailability.** The judge seam is optional by design; structural CI should not require model credentials.
- **Auto-refreshing the baseline.** If the baseline updates itself on every run, the regression gate can never fire. Refresh is a reviewed action.

## Known limits (by design, stated openly)

- **The judge still needs a model you bring.** The plumbing is done — `--judge-cmd` wires any model CLI, fails soft, stays advisory — but no model ships with this skill, so out of the box the structural score still won't detect a fluent wrong answer. The seam removes the integration work, not the need for a judge.
- **The default rubric weights are engineering judgment, not validated coefficients.** They encode which structural failures preceded real incidents in the source system, but no cross-project calibration data ships with this skill. Tune weights against your own incident history.
- **Grounding's support gate is lexical overlap, not entailment.** Term overlap catches the gross mis-cite and the fabricated reference cheaply; it cannot tell you a cited source is itself wrong or that a claim subtly misreads a source that mentions the right words. The `--entailment-cmd` seam adds that last mile with a model you bring — but it is advisory by default and off unless you wire it, so a bare lexical pass still isn't "verified true."

## Verification checklist

- [ ] `sh examples/selftest.sh` passes: structural (healthy → 0, weak → 1, malformed → 2) AND grounding (grounded → 0, uncited/mis-cited/fabricated-ref → 1, missing context → 2).
- [ ] Trace input is `.context/traces/<trace_id>.jsonl` in observability-tracing format.
- [ ] Grounding input is `{claim, sources}` structured output plus the context the agent was given; prose is not auditable.
- [ ] `python3 .../eval_run.py --help` works.
- [ ] A valid trace prints per-agent scores, overall score, and flags.
- [ ] Low scores or blocking flags return exit code 1.
- [ ] Bad input, missing trace, or invalid JSON returns exit code 2.
- [ ] `--judge` reports the disabled stub instead of fabricating content scores.
- [ ] No score, flag, or baseline delta is routed into the prompt, retry loop, reward, or memory of the agent being scored — only named defects are.

## Related skills in this bundle

- `observability-tracing` — produces the JSONL traces this skill consumes; the shipped demo trace is shared between the two.
- `prompt-contracts` — the static complement: it keeps schemas/prompts aligned to the registry *before* runs; this skill measures what runs actually emitted.
- `registry-ssot` — the vocabulary both contracts are anchored to.
