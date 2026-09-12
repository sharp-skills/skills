# Usage Guide: Run vs Read

## Quick reference

| What | Action | Why |
|---|---|---|
| `scripts/trace_view.py` | **RUN** | Renders timeline; source is stdlib boilerplate |
| `references/event-schema.md` | **READ** | Field docs and JSONL example |
| `references/usage.md` | **READ** | This file — storage, rotation, integration |

---

## Storage layout

```
<project-root>/
└── .context/
    └── traces/
        ├── run-20260115-a3f2.jsonl
        ├── run-20260115-b91c.jsonl
        └── ...
```

`.gitignore` entry (add once):
```
.context/traces/
```

Traces live outside version control. They are ephemeral operational data, not source artifacts.

### Naming convention

Use a short, collision-resistant trace ID. Recommended patterns:

```
run-<YYYYMMDD>-<random4>         # e.g. run-20260115-a3f2
<pipeline-name>-<timestamp-ms>   # e.g. research-1737028801234
```

Avoid embedding user data in the trace ID — it may appear in log lines.

---

## Rotation and archiving

Traces accumulate over time. Apply a retention policy appropriate to your use case:

**Delete old traces** (simplest — use if you don't need long-term history):
```bash
# Delete traces older than 7 days
find .context/traces -name "*.jsonl" -mtime +7 -delete
```

**Archive to compressed storage**:
```bash
# Compress traces older than 30 days into a dated archive
find .context/traces -name "*.jsonl" -mtime +30 \
  | tar -czf ".context/traces/archive-$(date +%Y%m).tar.gz" -T - --remove-files
```

Run either as a cron job or as a `trace_end` hook in the pipeline. Keep the active
traces directory small — rendering 1 000 small JSONL files is fast; rendering a 50 MB
file is not.

---

## Viewer output format

```
python scripts/trace_view.py run-20260115-a3f2
```

```
🧵  trace  run-20260115-a3f2
    goal  "research and summarize topic"

  10:00:00  ▶  TRACE START    orchestrator      [0→0]
  10:00:01  ✓  TOOL CALL      researcher    tool:web_search  [512→128]
  10:00:04  ✓  TRACE END      orchestrator      [0→0]

  ── 2 steps · 2 agents · 512↑ 128↓ tokens · 0 errors
```

**Columns** (left to right): `HH:MM:SS` timestamp · status icon · event kind · agent name
· tool name (if any) · `[input→output]` token counts · error message (if any).

**Summary line**: step count · distinct agent count · total input↑ and output↓ tokens
· error count.

### Useful invocations

```bash
# Render a specific trace
python scripts/trace_view.py run-20260115-a3f2

# Render the most recently modified trace (useful during development)
python scripts/trace_view.py --latest

# List all traces with event counts and sizes
python scripts/trace_view.py --list

# Show span IDs and parent relationships
python scripts/trace_view.py --verbose run-20260115-a3f2

# Use a non-default traces directory
python scripts/trace_view.py --traces-dir /var/log/myapp/traces run-20260115-a3f2

# Override via environment variable
TRACES_DIR=/var/log/myapp/traces python scripts/trace_view.py --latest

# Full option reference
python scripts/trace_view.py --help
```

---

## Integration patterns

### Minimal (lifecycle start/end)

The minimum viable integration wraps `_run` with `trace_start` and `trace_end` events. Per-step logging is shown in the next section.

```python
import json, sys, datetime, pathlib

TRACES_DIR = pathlib.Path(".context/traces")

def trace_log(trace_id: str, **fields) -> None:
    try:
        TRACES_DIR.mkdir(parents=True, exist_ok=True)
        event = {
            "trace_id": trace_id,
            "ts": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
            **fields,
        }
        with open(TRACES_DIR / f"{trace_id}.jsonl", "a") as f:
            f.write(json.dumps(event) + "\n")
    except Exception as exc:
        print(f"[trace] warn: {exc}", file=sys.stderr)   # fail open


def run_pipeline(goal: str) -> dict:
    tid = generate_trace_id()
    step_counter = 0

    trace_log(tid, kind="trace_start", span="root", step=0,
              agent="orchestrator", status="started",
              input_tokens=0, output_tokens=0, parent=None,
              meta={"goal": sanitize(goal)})
    try:
        result = _run(tid, goal)
        trace_log(tid, kind="trace_end", span="root", step=step_counter,
                  agent="orchestrator", status="ok",
                  input_tokens=0, output_tokens=0, parent=None)
        return result
    except Exception as exc:
        trace_log(tid, kind="trace_end", span="root", step=step_counter,
                  agent="orchestrator", status="error",
                  input_tokens=0, output_tokens=0, parent=None,
                  error=str(exc)[:200])
        raise
```

### Per-step logging

Inside the agent dispatch loop, wrap each step:

```python
step = 0

def dispatch(agent_name: str, task: dict, tid: str, parent_span: str) -> dict:
    global step
    span = f"{agent_name}-{step}"
    step += 1

    trace_log(tid, kind="step_start", span=span, step=step,
              agent=agent_name, status="started",
              input_tokens=task.get("input_tokens", 0),
              output_tokens=0, parent=parent_span)

    result = call_agent(agent_name, task)
    in_t = result.get("input_tokens", 0)
    out_t = result.get("output_tokens", 0)

    trace_log(tid, kind="step_complete", span=span, step=step,
              agent=agent_name, status="ok",
              input_tokens=in_t, output_tokens=out_t, parent=parent_span,
              tool=result.get("tool_used"))

    return result
```

### Tool-level logging

For tool calls inside an agent, emit `tool_call` and `tool_result` pairs:

```python
def traced_tool(tid: str, agent: str, tool_name: str, parent: str, fn, *args, **kwargs):
    global step
    step += 1
    span = f"tool-{tool_name}-{step}"

    trace_log(tid, kind="tool_call", span=span, step=step,
              agent=agent, tool=tool_name, status="started",
              input_tokens=0, output_tokens=0, parent=parent)
    try:
        result = fn(*args, **kwargs)
        trace_log(tid, kind="tool_result", span=span, step=step + 1,
                  agent=agent, tool=tool_name, status="ok",
                  input_tokens=0, output_tokens=0, parent=parent)
        return result
    except Exception as exc:
        trace_log(tid, kind="tool_result", span=span, step=step + 1,
                  agent=agent, tool=tool_name, status="error",
                  input_tokens=0, output_tokens=0, parent=parent,
                  error=str(exc)[:200])
        raise
```

### Cross-runtime fan-out

When agents run in separate processes or machines, pass `trace_id` via task payload:

```python
# Orchestrator side
task_payload = {
    "trace_id": tid,      # ← forward the trace context
    "parent_span": span,
    "task": "...",
}
dispatch_to_worker(task_payload)

# Worker side (any runtime that can write to the shared traces directory)
def handle_task(payload: dict) -> None:
    tid = payload["trace_id"]
    parent = payload["parent_span"]
    # ... do work ...
    trace_log(tid, kind="step_complete", span="worker-0", step=1,
              agent="worker", status="ok", parent=parent,
              input_tokens=in_t, output_tokens=out_t)
```

If workers cannot reach the shared filesystem, have each worker return its events to the
orchestrator to flush, or write to its own file and merge with `cat` at the end.

---

## Pairing observability with evaluation

A trace is the input to an eval harness. Once a run is traced, an evaluator can replay
the events without re-running the pipeline:

```python
events = [json.loads(l) for l in open(f".context/traces/{tid}.jsonl") if l.strip()]
steps = [e for e in events if e["kind"] == "step_complete"]
# evaluate quality, confidence, off-plan flags, token budget, etc.
```

Use this same event stream as the stable input for any later quality evaluator or
budget guardrail; the evaluator should consume the trace rather than re-running the
pipeline.
