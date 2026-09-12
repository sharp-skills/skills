# Examples — status-gates

Run the self-test (no network, stdlib only):

```bash
sh selftest.sh
```

| Case | Input | Expected |
|---|---|---|
| Publish-event routes | `business_analyst` + `BA_COMPLETE` | exit 0 |
| Invented status | `business_analyst` + `SUCCESS` | exit 2, message lists allowed vocabulary |
| Skip form | `cto` + `CTO_SKIPPED` | exit 0 |
| Shared failure terminal | `cto` + `PIPELINE_FAILED` | exit 0 |
| Named observer | `event_bus` + `DELIVERED` | exit 0 (exempt) |
| Unknown agent | `stranger` + anything | exit 0 (fail-open — registration is another check's job) |
| No status emitted | `business_analyst`, no `--status` | exit 0 |

`gate-config.json` deliberately uses the same vocabulary as the
`prompt-contracts` config — one contract, enforced statically there and at
runtime here.
