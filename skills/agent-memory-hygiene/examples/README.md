# agent-memory-hygiene examples

Fixtures that prove the lint offline. Run `sh selftest.sh` (stdlib only; passes a
fixed `--now` so the freshness check is deterministic).

| File | Role |
|---|---|
| `store.good.json` | Four healthy entries — each has a source and timestamp, no secrets, and the one untrusted-sourced entry is typed `note`, not `fact`. |
| `store.bad.json` | One entry per rot: a secret (password + API key), a missing `source`, a 2024 entry (stale vs `--now` 2026-07-06), an inbound-DM "fact" (poison), and a duplicate of another entry. |
| `selftest.sh` | Asserts healthy → 0; each rot and the size cap → 1; missing store → 2. |

Try it:

```bash
python3 ../scripts/memory_lint.py --store store.bad.json --now 2026-07-06T00:00:00Z
python3 ../scripts/memory_lint.py --store store.good.json --max-entries 2   # trip the size cap
```

Extend the secret patterns in `scripts/memory_lint.py` (`SECRETS`) for your own
credential formats; tune `--max-age-days` to how fast your facts go stale.
