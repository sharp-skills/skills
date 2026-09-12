# Examples — cost-budgeting

Run the self-test (no network, stdlib only):

```bash
sh selftest.sh
```

| Fixture | What it demonstrates | Expected |
|---|---|---|
| `traces/demo-run-001.jsonl` + `budgets.json` | Healthy run within derived budgets | exit 0 |
| `traces/over-budget-run.jsonl` | Engineer blows input/output ceilings; run total exceeded | exit 1, overruns named per agent and per run |
| coverage case (selftest drops one agent from budgets) | Agent seen in trace but unbudgeted | exit 1, "unmetered" flag |

`budgets.json` records its own derivation (`derived_from`) — that field is
part of the method, not decoration. `demo-run-001.jsonl` is the bundle's
shared healthy trace: record with `observability-tracing`, budget-check
here, score with `eval-harness`.
