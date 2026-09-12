---
name: observability-tracing
description: >-
  Instrument a multi-agent pipeline with structured per-trace JSONL logs and render them as a human-readable timeline, token summary, and error report — without ever breaking the pipeline. Use this skill when you need to see what a multi-step or multi-agent run actually did, debug why a pipeline stalled or produced wrong output, audit token spend across agents and tools, or produce a durable audit trail that survives fan-out across runtimes. Trigger on any of: add observability, tracing, pipeline logging, debug agents, audit trail, trace viewer, why did the agent do X.
license: Apache-2.0
---

# Observability & Tracing for Multi-Agent Systems

One trace = one run. One JSONL line = one event. Log once; view many times without re-running.

## Data model

- **Trace** — the complete record of one pipeline run, keyed by `trace_id`.
- **Span** — a logical unit of work within a trace (agent turn, tool call, sub-task). Spans nest via `parent`.
- **Event** — one JSONL line: a boundary crossing (`trace_start`, `step_complete`, `tool_call`, `error`, …).

See `references/event-schema.md` for the full field list, types, and a safe JSONL example.

## Storage convention

```
.context/traces/<trace_id>.jsonl   ← one file per trace, append-only
```

Add `.context/traces/` to `.gitignore`. Rotate or archive files older than your retention window — see `references/usage.md`.

## Viewing a trace

```bash
python scripts/trace_view.py <trace_id>          # timeline + summary
python scripts/trace_view.py --latest            # most recently modified trace
python scripts/trace_view.py --list              # enumerate available traces
python scripts/trace_view.py --help              # all options
```

`scripts/trace_view.py` is **self-contained stdlib Python** — run it directly. `references/usage.md` explains output columns and integration patterns (read, don't run).

## Integration: start / step / end

```python
import json, datetime, pathlib, sys

TRACES_DIR = pathlib.Path(".context/traces")

def trace_log(trace_id: str, **fields) -> None:
    """Append one event; swallow all errors so logging never breaks the pipeline."""
    try:
        TRACES_DIR.mkdir(parents=True, exist_ok=True)
        event = {"trace_id": trace_id, "ts": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"), **fields}
        with open(TRACES_DIR / f"{trace_id}.jsonl", "a") as f:
            f.write(json.dumps(event) + "\n")
    except Exception as exc:
        print(f"[trace] warn: {exc}", file=sys.stderr)

# Call 1 — at pipeline start
trace_log(tid, kind="trace_start", span="root", step=0,
          agent=ORCHESTRATOR_NAME, status="started",
          input_tokens=0, output_tokens=0, parent=None)

# Call 2 — after each agent step (repeat for every turn)
trace_log(tid, kind="step_complete", span=span_id, step=step_n,
          agent=agent_name, tool=tool_used_or_none, status="ok",
          input_tokens=in_t, output_tokens=out_t, parent=parent_span)

# Call 3 — at pipeline end (or on abort)
trace_log(tid, kind="trace_end", span="root", step=final_step_n,
          agent=ORCHESTRATOR_NAME, status="ok",
          input_tokens=0, output_tokens=0, parent=None)
```

## Anti-patterns

| Anti-pattern | Risk |
|---|---|
| Logging prompt text or user messages verbatim | PII / secrets leakage |
| Logging API keys, tokens, or env vars | Direct secret exposure |
| Raising exceptions inside `trace_log` | Breaks the pipeline; observability must fail open |
| Appending all runs to one file | Destroys per-trace isolation; `--latest` becomes meaningless |
| Logging response payloads > a few KB | Trace files bloat; slow to render and archive |

## Reference files

- `references/event-schema.md` — **READ** — field-by-field schema, hierarchy diagram, annotated example
- `references/usage.md` — **READ** — storage layout, rotation, output format, run-vs-read guide

## Script

- `scripts/trace_view.py` — **RUN** — self-contained timeline viewer; run `--help` before reading source
- `examples/selftest.sh` — **RUN** — renders the shipped demo trace and checks `--list` discovery

## Related skills in this bundle

- `eval-harness` — scores the traces this skill records (the demo trace is shared between the two).
- `prompt-contracts` — when a trace shows the same output rejected turn after turn, that skill finds which contract layer drifted.
- `registry-ssot` — the routing truth a healthy trace should reflect.
