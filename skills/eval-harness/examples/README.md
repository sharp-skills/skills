# Examples — eval-harness

Run the self-test (no network, no credentials, stdlib only):

```bash
sh selftest.sh
```

| Fixture | What it demonstrates | Expected |
|---|---|---|
| `traces/demo-run-001.jsonl` | Healthy 3-agent run, full contract metadata in `meta` | exit 0, score 100 |
| `traces/weak-run.jsonl` | `status:error`, missing token fields, `schema_valid:false`, alert label | exit 1, blocking flags |
| `traces/broken-run.jsonl` | Malformed JSONL line | exit 2 (never silently 0) |
| `traces/golden-low-confidence.jsonl` | Confidence dimension: 0.3 below the 0.7 threshold, all else perfect | exit 1, `LOW_CONFIDENCE` |
| `traces/golden-alert-label.jsonl` | Alert dimension: blocking label on an otherwise perfect event | exit 1, `ALERT_PRESENT` |
| `traces/golden-no-scorable.jsonl` | Edge case: trace with start/end only | exit 1, `NO_SCORABLE_EVENTS` |
| `traces/golden-contract.jsonl` + `rubric-contract.json` | Contract dimension: passes the default rubric, fails a stricter project rubric | exit 0 / exit 1 |
| `baseline-demo.json` | Saved baseline of the healthy run for regression comparison | weak-run vs it → exit 1 |
| `grounding/context.json` | The sources an agent was given (`{sources: {s1: {text}}}`) | — |
| `grounding/output.good.json` | `{claim, sources}` output where every claim cites a resolving, substantiating source | exit 0 |
| `grounding/output.bad.json` | Uncited claim (`b1`), mis-cited claim (`b2`), fabricated reference `s9` (`b3`) | exit 1, three grounding findings |

Each golden isolates one rubric dimension, so a future rubric change that
breaks a dimension breaks the self-test — the goldens are the rubric's own
regression suite. The `grounding/` fixtures do the same for the grounding
audit: one grounded output and one that fails each of the three gates.

`demo-run-001.jsonl` is the same trace shipped with
`multi-agent-engineering/observability-tracing` — record with that skill,
score with this one.
