# Examples — observability-tracing

Run the self-test (no network, stdlib only):

```bash
sh selftest.sh
```

`traces/demo-run-001.jsonl` is a healthy three-agent run in the documented
event format (`trace_start` → steps with token counts and contract `meta` →
`trace_end`). Render it:

```bash
python3 ../scripts/trace_view.py --traces-dir traces demo-run-001
```

The same file ships with `multi-agent-engineering/eval-harness` — record here,
score there.
