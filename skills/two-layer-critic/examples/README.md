# Examples — two-layer-critic

Run the self-test (no network, stdlib only):

```bash
sh selftest.sh
```

| Case | Input | Expected |
|---|---|---|
| Routing | `--mode STANDARD` / `DEEP` / `FAST` | `cheap` / `premium` / `skip` |
| Unknown mode | `--mode BOGUS` | exit 2 (loud) |
| Good review | `review.good.json` — 2 structured findings, verdict FAIL | exit 0 |
| Bad review | `review.bad.json` — 4 planted violations | exit 1, all named |

The four planted violations in `review.bad.json`:

1. Verdict `SCORE_74` — score creep instead of pass/fail.
2. Four findings — over the cap of three.
3. A finding missing `fix_direction` — unstructured.
4. Severity `NIT` — outside the declared severity scale.
