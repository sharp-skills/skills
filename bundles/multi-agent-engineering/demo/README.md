# End-to-end composition demo

The skills in this bundle are not a pile of singles — they compose into one
system. This demo proves it: a tiny multi-agent run wired through **five skills
over one shared registry and one trace**, stdlib Python only, offline,
deterministic.

```bash
sh demo.sh
```

## What it wires together

```
registry.json  ──(single source of truth)──┐
                                            │
   registry-ssot: validate the wiring ◀─────┤
                                            │
   run_pipeline.py                          │
     • routing DERIVED from registry.bus_graph   (registry-ssot principle in code)
     • each emitted status checked by status-gates' real status_gate.py
     • each step appended to a JSONL trace        (observability-tracing schema)
                                            │
                    .context/traces/demo-e2e-001.jsonl
                                            │
   observability-tracing: replay the timeline ◀───┤
   eval-harness:          score the outputs   ◀───┤
   cost-budgeting:        check per-agent budgets ◀┘
```

Every arrow is a **real shipped script** from the skill, run against the same
two files — not a reimplementation. The demo is the integration test for the
bundle's central claim.

## What each step proves

| Step | Skill | What you see |
|---|---|---|
| 1 | `registry-ssot` | The shared `registry.json` is valid wiring (no orphans, dead-ends, or drift). |
| 2 | `registry-ssot` + `status-gates` + `observability-tracing` | The pipeline routes by **deriving** the next agent from the registry's bus graph; each emitted status is gated at the routing boundary before it routes; each step lands in the trace. |
| 3 | `observability-tracing` | `trace_view.py` replays the run as a timeline — logged once, viewed without re-running. |
| 4 | `eval-harness` | `eval_run.py` scores the recorded outputs against a structural rubric (100.0, no flags). |
| 5 | `cost-budgeting` | `budget_check.py` reads the *same* trace and confirms every agent stayed within its per-agent token budget. |
| 6 | `status-gates` | The engineer emits a plausible-but-unroutable `SUCCESS`; the gate **rejects it with the allowed vocabulary** and the run fails *loudly* with `PIPELINE_FAILED` — instead of routing nowhere and stalling with every component reporting success. |

## One registry, both skills

`registry-ssot` stores agents as a list of `{id, publishes, subscribes_to}`;
`status-gates` originally read a `{id: {publishes}}` dict. They now both read the
**same** `registry.json` — the gate normalizes either shape — so the router and
the runtime gate share one source of truth rather than a gate-private copy. (This
seam was found by building this demo; closing it is what makes "one registry"
literally true.)

## Notes

- `.context/traces/` is generated on each run; it is gitignored, not shipped.
- The agent outputs in `run_pipeline.py` are scripted so the demo is deterministic
  and needs no model or network; a real pipeline gets them from agents. The
  wiring, gating, tracing, scoring, and budgeting around them are the real thing.
