# LLM-as-Judge Seam

The evaluator has two intentionally separate layers:

1. **Structural scoring** — deterministic, local, stdlib-only, CI-safe.
2. **Content judging** — optional model-based assessment of semantic quality.

Do not merge these numbers. A structurally valid output can be wrong, and a useful answer can be wrapped in a malformed event. Keeping the layers separate makes failures diagnosable.

## Bundled behavior

There are two ways to invoke the seam:

- **`--judge` with no command** calls the historical stub, which returns `None`. The script reports judge unavailability and continues to return the structural gate result. It never fabricates a content-quality score.
- **`--judge-cmd "<cli>"`** wires a real, provider-independent judge: the script sends the external CLI a **sanitized digest** (event shape and `meta` labels only — never raw outputs) as the last argument, expects a JSON verdict on stdout, and **fails soft** — a missing binary, a timeout, or non-JSON degrades to `None`, exactly like the stub. This is the same `--verifier-cmd` seam `cross-model-verification` uses, applied to content quality.

```bash
# provider-independent: any CLI that reads the prompt and prints a JSON verdict
python3 eval_run.py --latest --judge-cmd "my-judge-cli --json"
```

The verdict is **advisory and separate from the structural score** — it is printed under a `judge:` section and **never changes the structural exit code**. `examples/fake_judge.py` is a model-free stand-in used by the self-test to prove the seam wires end-to-end and stays advisory.

## Why the stub returns None

A real judge needs project-specific choices that should not be hidden inside a reusable skill:

- model/provider selection,
- credentials and secret handling,
- prompt and rubric calibration,
- sampling controls,
- privacy policy for sending trace-derived content to a model,
- storage format for judge decisions,
- retry and rate-limit behavior.

Until those are explicit, the safest behavior is no content score.

## Wiring a real judge

When a project is ready, add a local wrapper or forked script that preserves the structural report shape and appends a separate judge section.

Recommended contract:

```python
def llm_judge(events, rubric):
    """Return content-quality results or None when unavailable.

    Return shape:
    {
        "score": 0-100,
        "label": "pass|warn|fail",
        "findings": [
            {
                "event_index": 3,
                "agent": "writer",
                "severity": "low|medium|high",
                "reason": "short explanation",
                "evidence": "sanitized excerpt or field reference"
            }
        ],
        "model": "provider/model-id",
        "rubric_version": "project-local-id"
    }
    """
```

Keep this result under a field such as `judge`, not `structural_score`.

## Privacy rules

Before sending anything to an LLM judge:

- Prefer sanitized summaries and field-level references over raw outputs.
- Remove secrets, user identifiers, tokens, file paths with usernames, and private prompts.
- Decide whether trace metadata is allowed to leave the environment.
- Log model id and rubric version for reproducibility.

If privacy constraints prevent model access, keep using the structural score only.

## Calibration rules

Do not use a judge score as a release gate until it has been calibrated against human review. Start by logging judge results alongside structural scores, then compare:

- false positives: judge fails acceptable outputs,
- false negatives: judge passes bad outputs,
- instability: same input receives materially different scores,
- overlap: judge flags issues already caught structurally.

Only after calibration should a project decide whether judge results are advisory or blocking.

## Failure behavior

A judge integration should fail soft by default:

- credential missing → return `None`, emit `JUDGE_UNAVAILABLE`, keep structural result,
- provider timeout → return `None` or a separate judge error, keep structural result,
- malformed judge response → ignore judge result, keep structural result,
- structural parse failure → exit code 2 before judging.

This prevents external model outages from hiding deterministic structural regressions.
