# Examples — experience-loop

Run the self-test (no network, stdlib only; uses a temp file, leaves nothing
behind):

```bash
sh selftest.sh
```

| Case | What it proves | Expected |
|---|---|---|
| First record (obs 90) | Bootstrap 70 → EMA 76.0 — the exact α=0.3 math | printed transition matches |
| Second record (obs 50) | 76.0 → 68.2 — recent behavior dominates smoothly | printed transition matches |
| Structured entry | `{category, insight, outcome}` recorded, shown, counted | visible in `show` |
| Incomplete entry | `--category` without insight/outcome refused | exit 2 |
| Staleness | fresh file passes; `--max-age-days 0.00001` fails | exit 0 / exit 1 |

To try the loop by hand:

```bash
python3 ../scripts/learnings.py record --file demo.json --agent analyst \
  --confidence 85 --category retry_loop \
  --insight "reject message lacked allowed vocabulary" \
  --outcome "teaching rejection added; converges in one retry"
python3 ../scripts/learnings.py show --file demo.json
```
