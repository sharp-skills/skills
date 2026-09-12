# Examples — task-triage

Run the self-test (no network, stdlib only):

```bash
sh selftest.sh
```

| Case | Goal | Expected |
|---|---|---|
| Short route | "write a blog post…" | template `content`, 3 agents, terminal reachable |
| Force rule | "add a billing endpoint with stripe" | `legal` in `forced` regardless of template |
| Safe default | unrecognized goal | template `full`, whole crew |
| Bilingual guard | «оплата картой и персональные данные» | `legal` forced from Russian vocabulary |
| Anti-stall | `triage-config.stall.json` (content route without its closer) | exit 2: no terminal reachable |
| Fail-soft | `--llm-cmd /nonexistent-classifier` | exit 0, `source: rules` |

`registry.json` uses the same shape as the `registry-ssot` examples — one
registry format across the bundle.
