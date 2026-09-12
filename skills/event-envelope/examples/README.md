# event-envelope examples

Fixtures that prove both checks offline. Run `sh selftest.sh` (stdlib only).

The runtime names here (`main`, `worker`, `verifier`, `browser`, `code`) are
deliberately generic roles — substitute your own stack's runtimes (e.g. a
Claude Code agent, an OpenAI Codex worker, a Hermes/LangGraph-orchestrated step,
a browser driver, a deterministic code handler). The check cares about the enum
being *one closed set kept equal to the dispatcher's*, not what you name them.

| File | Role |
|---|---|
| `envelope.schema.json` | The wire contract: required fields, runtime enum, mode enum, score bounds. |
| `runtimes.source` | Canonical runtime set the dispatcher routes on — equal to the schema enum. |
| `runtimes.drifted.source` | Same set plus `remote-gpu`, a runtime the schema doesn't know yet → drift. |
| `envelopes.good.jsonl` | Four well-formed events across four runtimes (note the `null` score on an infra event). |
| `envelopes.bad.jsonl` | One event per flaw: missing `trace_id`, unknown runtime, unknown `pipeline_mode`, out-of-range score. |
| `selftest.sh` | Asserts: aligned → 0, drift → 1 (names the runtime), malformed stream → 1 (each flaw), no-args → 2. |

Try it:

```bash
# drift check alone — schema enum vs dispatcher set
python3 ../scripts/envelope_check.py --schema envelope.schema.json \
    --runtimes-source runtimes.drifted.source

# wire check alone — validate a stream
python3 ../scripts/envelope_check.py --schema envelope.schema.json \
    --events envelopes.bad.jsonl
```
