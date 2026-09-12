# Structural Rubric

This rubric scores whether recorded multi-agent outputs are well-formed and in contract. It is deliberately generic: projects can configure required fields, thresholds, schema hints, and blocking flags without importing any private pipeline vocabulary.

Structural score answers: "Can this output be trusted as a comparable, machine-checkable artifact?" It does not answer: "Is the output true, insightful, or useful?"

## Inputs

The evaluator reads observability-tracing JSONL:

```text
.context/traces/<trace_id>.jsonl
```

Each line is one event. The base trace schema defines fields such as `trace_id`, `span`, `step`, `kind`, `ts`, `agent`, `status`, token counts, `parent`, `error`, and optional `meta`.

Agent-specific contract signals should live in `meta` as sanitized structure, not private content. Prefer booleans, counts, enum labels, and field names over full outputs.

## Generic event example

```json
{
  "trace_id": "run-20260115-a3f2",
  "span": "draft-1",
  "step": 1,
  "kind": "step_complete",
  "ts": "2026-01-15T10:00:01.234Z",
  "agent": "writer",
  "tool": null,
  "status": "ok",
  "input_tokens": 512,
  "output_tokens": 256,
  "parent": "root",
  "error": null,
  "meta": {
    "output_fields": ["summary", "risks", "next_actions"],
    "confidence": 0.86,
    "schema_valid": true,
    "alerts": []
  }
}
```

This example logs the existence of fields and validation signals. It does not log private output text.

## Default scoring model

The bundled script computes an event score from four weighted components:

| Component | Default weight | What it checks |
|---|---:|---|
| Trace shape | 40 | Required trace fields exist and have basic types. |
| Contract fields | 25 | Configured output/metadata fields are present when applicable. |
| Confidence | 15 | A confidence-like numeric value, if configured/present, meets threshold. |
| Schema hints | 10 | Optional schema-valid indicators do not report failure. |
| Status and alerts | 10 | Error statuses, error text, or configured alert labels are absent. |

The score is clamped to 0-100. Missing optional signals do not always fail by default; configure stricter behavior when your pipeline emits those signals reliably.

Overall score is the arithmetic mean of scored agent events. By default, lifecycle events such as `trace_start`, `trace_end`, `tool_call`, and `tool_result` are parsed for blocking errors but are not counted as agent output quality events unless configured.

## Flags

Flags are stable strings intended for CI logs and dashboards. The default evaluator may emit flags such as:

- `MISSING_REQUIRED_FIELD:<event-index>:<field>` — a trace-level field is absent.
- `INVALID_TYPE:<event-index>:<field>` — a field exists but has the wrong basic type.
- `MISSING_CONTRACT_FIELD:<event-index>:<field>` — a configured contract field was not present.
- `LOW_CONFIDENCE:<event-index>:<value>` — confidence was below the configured threshold.
- `SCHEMA_INVALID:<event-index>` — schema hint reported failure.
- `EVENT_STATUS_ERROR:<event-index>:<status>` — event status indicates failure.
- `EVENT_ERROR_PRESENT:<event-index>` — an error field contains text.
- `ALERT_PRESENT:<event-index>:<label>` — alert-like metadata contains a configured or generic alert label.
- `NO_SCORABLE_EVENTS` — no events matched the configured output event kinds.
- `JUDGE_UNAVAILABLE` — `--judge` was requested but the stub is not connected.

Blocking flags cause exit code 1 even when the numeric score is above threshold. Parse/config errors use exit code 2 instead.

## Configuration

The script works without configuration. For stricter project contracts, pass a JSON file with `--rubric`.

Example:

```json
{
  "min_score": 85,
  "scored_kinds": ["step_complete"],
  "required_event_fields": {
    "trace_id": "str",
    "span": "str",
    "step": "int",
    "kind": "str",
    "ts": "str",
    "agent": "str",
    "status": "str",
    "input_tokens": "int",
    "output_tokens": "int",
    "parent": "any"
  },
  "required_meta_fields": ["output_fields"],
  "required_output_fields": ["summary", "risks", "next_actions"],
  "output_fields_meta_key": "output_fields",
  "confidence": {
    "meta_key": "confidence",
    "threshold": 0.75,
    "required": false,
    "blocking": true
  },
  "schema": {
    "meta_key": "schema_valid",
    "required": false
  },
  "alerts": {
    "meta_keys": ["alerts", "flags"],
    "blocking_labels": ["error", "blocked", "policy_violation"]
  },
  "blocking_statuses": ["error"],
  "weights": {
    "shape": 40,
    "contract": 25,
    "confidence": 15,
    "schema": 10,
    "status_alerts": 10
  }
}
```

All five weight values must sum to 100. Partial overrides are merged with defaults, so any override that changes the total is rejected as a configuration error instead of silently shifting the maximum achievable score.

### Required event fields

`required_event_fields` validates the trace envelope. Supported type labels are:

- `str`
- `int`
- `number`
- `bool`
- `list`
- `dict`
- `any`

Keep these aligned with observability-tracing unless you intentionally extend your local trace format.

### Required meta fields and output fields

Use `required_meta_fields` for metadata keys that must exist directly in `meta`.

Use `required_output_fields` with `output_fields_meta_key` when an event records which output fields were produced. The value may be a list of field names or an object whose keys are field names.

This pattern checks "the output contract was represented" without logging the output itself.

### Confidence

The confidence block is generic. Choose any metadata key that your pipeline emits, such as `confidence`, `quality_confidence`, or `contract_confidence`.

- If `required` is `false`, missing confidence is flagged as informational and the confidence component receives partial credit.
- If `required` is `true`, missing confidence receives no confidence credit and emits a blocking contract flag.
- If `blocking` is `true`, below-threshold confidence emits a blocking `LOW_CONFIDENCE` flag. If `false`, it emits `LOW_CONFIDENCE_INFO` and only affects the numeric score.
- Thresholds should be calibrated on real traces; do not copy another project's value blindly.

### Opportunistic schema validation

The evaluator does not implement a full JSON Schema engine because it is stdlib-only. Instead it supports opportunistic hints:

- `meta.schema_valid: true` — full schema credit.
- `meta.schema_valid: false` — schema component fails and emits `SCHEMA_INVALID`.
- missing schema hint — partial credit unless `schema.required` is true.

If a project needs full schema validation, run that separately in the pipeline and log a sanitized boolean result in `meta`.

### Error and alert flags

Structural evaluation should surface both explicit failures and warning labels:

- `status` in `blocking_statuses` is blocking.
- non-empty `error` is blocking.
- alert-like metadata in configured `meta_keys` is blocking when it matches a configured label, and flagged generically when it is non-empty.

Keep alert labels generic to your project and avoid names that encode private process details.

## CI gating

Recommended CI command:

```bash
python3 multi-agent-engineering/eval-harness/scripts/eval_run.py --latest --min-score 85
```

Use exit codes as the integration contract:

- `0` — evaluation completed and passed.
- `1` — evaluation completed but failed threshold or blocking flags.
- `2` — evaluator could not run because of usage, missing input, parse, or config errors.

## Keep this rubric out of the scored agent's context

Everything defined above — the weights, the components, the flag strings, the thresholds — is an input to a human review or a CI gate. **Do not place it in the prompt, retry loop, reward signal, or memory of the agent whose events are being scored.**

A rubric the scored agent can read is a specification it will satisfy directly, and the components above are unusually easy to satisfy directly: emit the field name, emit a confidence number above the threshold, avoid the alert label. Every weighted component then reports success while the underlying outputs are unchanged, and the score silently stops measuring anything.

If an agent must correct itself, give it the named defect ("the `risks` field was absent from the output"), not the flag string, not the component score, and not the delta against baseline. See *Who the score is for* in the skill.

## Calibration workflow

1. Collect several representative traces.
2. Run the default evaluator and inspect flags.
3. Add a project-local rubric JSON only for signals your trace reliably emits.
4. Set `min_score` low enough to avoid noise, then tighten after a few real runs.
5. Keep structural and judge metrics in separate report fields.
6. Confirm the resulting scores and flags reach humans and CI only — calibrating a rubric that the scored agent can also read calibrates nothing.
