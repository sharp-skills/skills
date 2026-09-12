# Trace Event Schema

A trace is an **append-only JSONL file** — one file per pipeline run. Each line is a
self-describing JSON object representing a single event.

## Trace → Span → Event hierarchy

```
trace (trace_id)
└── span "root"               ← trace_start / trace_end
    ├── span "agent-turn-1"   ← step_start / step_complete
    │   └── span "tool-0"     ← tool_call / tool_result
    └── span "agent-turn-2"
        └── span "tool-1"
```

A **span** is a named scope identified by `span` (string). Spans nest via the `parent` field.
Simple pipelines need only two levels: `"root"` and a per-step span. Complex fan-outs can
nest arbitrarily — each child span records its parent span id.

## Field reference

| Field | Type | Required | Notes |
|---|---|---|---|
| `trace_id` | string | yes | Unique run identifier. Use a short random ID or a slug, e.g. `"run-20260115-a3f2"`. Never embed user data. |
| `span` | string | yes | Scope name within the trace, e.g. `"root"`, `"search-0"`, `"tool-web_search"`. |
| `step` | integer | yes | Monotonically increasing counter within the trace (0, 1, 2, …). |
| `kind` | string | yes | Event type. See **Event kinds** below. |
| `ts` | string | yes | UTC timestamp, ISO-8601 with milliseconds: `"2026-01-15T10:00:01.234Z"`. |
| `agent` | string | yes | Name of the agent or component that emitted the event, e.g. `"orchestrator"`, `"researcher"`. |
| `tool` | string\|null | no | Name of the tool invoked, e.g. `"web_search"`, `"bash"`. Omit or `null` for non-tool events. |
| `status` | string | yes | Outcome: `"started"`, `"ok"`, `"error"`, `"skipped"`. |
| `input_tokens` | integer | yes | Tokens consumed in this step (0 if N/A). |
| `output_tokens` | integer | yes | Tokens generated in this step (0 if N/A). |
| `parent` | string\|null | yes | `span` value of the enclosing scope, or `null` for root events. |
| `error` | string\|null | no | Short error message (one line). `null` if no error. **Never include stack traces, secrets, or user data.** |
| `meta` | object\|null | no | Optional structured context — see **Safe payload guidance** below. |

### Event kinds

| `kind` | When to emit |
|---|---|
| `trace_start` | Immediately before the first agent step. |
| `trace_end` | After the final step completes (or on abort). |
| `step_start` | When an agent begins its turn (optional; useful for long steps). |
| `step_complete` | When an agent turn finishes successfully. |
| `tool_call` | When a tool invocation begins. |
| `tool_result` | When the tool returns (success or error). |
| `error` | Any unrecoverable failure within the pipeline. |

Emit at minimum: `trace_start`, one `step_complete` per agent turn, and `trace_end`.

## Safe payload guidance

The `meta` field carries structured context that aids debugging. Apply these rules:

**Include:**
- Goal/intent description sanitized to remove user PII (e.g. `"goal": "summarize the uploaded document"`)
- Agent configuration names, model IDs
- Tool parameter *names* (not values) or a parameter count
- Result *counts* (e.g. `"results_returned": 5`) rather than result content
- Pipeline mode, configuration flags

**Exclude — never log:**
- API keys, access tokens, secrets, passwords, env-var values
- User-supplied text beyond a short sanitized summary
- Full prompt text or agent responses
- File paths containing usernames or other PII
- Any content your system considers private or confidential

If unsure, log a token count or an enum label — never the payload itself.

## Annotated JSONL example

One complete trace with three events (each on its own line):

```jsonl
{"trace_id": "run-20260115-a3f2", "span": "root", "step": 0, "kind": "trace_start", "ts": "2026-01-15T10:00:00.000Z", "agent": "orchestrator", "tool": null, "status": "started", "input_tokens": 0, "output_tokens": 0, "parent": null, "error": null, "meta": {"goal": "research and summarize topic", "pipeline_mode": "sequential", "agent_count": 2}}
{"trace_id": "run-20260115-a3f2", "span": "search-0", "step": 1, "kind": "tool_call", "ts": "2026-01-15T10:00:01.234Z", "agent": "researcher", "tool": "web_search", "status": "ok", "input_tokens": 512, "output_tokens": 128, "parent": "root", "error": null, "meta": {"results_returned": 5}}
{"trace_id": "run-20260115-a3f2", "span": "root", "step": 2, "kind": "trace_end", "ts": "2026-01-15T10:00:04.891Z", "agent": "orchestrator", "tool": null, "status": "ok", "input_tokens": 0, "output_tokens": 0, "parent": null, "error": null, "meta": {"total_steps": 2}}
```

Note: `meta` values are counts and labels only — no user content, no secrets.

## Cross-runtime traces

When agents fan out across processes or runtimes, each runtime appends to the **same**
`trace_id` file. The `trace_id` is the coordination key — pass it as an environment variable
or in the task payload so every runtime knows which file to write.

Concurrent writes to the same file are safe when each `json.dumps(event) + "\n"` is a
single `write()` call on a **local POSIX filesystem** (atomic for lines < 4 KB on Linux/macOS
local drives). This guarantee does **not** hold for network-mounted directories: NFS, SMB/CIFS,
and Docker remote mounts do not provide POSIX `write()` atomicity. For those targets — or for
events larger than 4 KB — use a per-file write lock (e.g. `fcntl.flock`) or route all writes
through a logging sidecar that serializes appends.
