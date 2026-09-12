# Fixtures

Two action logs for the same shape of task — a multi-day booking session — one
recoverable and one not.

| File | What it is |
|---|---|
| `actions.good.jsonl` | A session that can be replayed: every non-deterministic outcome recorded, side effects keyed or skipped, retries capped, caches scoped and expiring. |
| `actions.bad.jsonl` | A **plausible** log from a system that works right up until the first crash — not malformed junk. Each line carries `_fails_because` stating the exact failure it encodes. |
| `selftest.sh` | 13 assertions: the clean log passes, each failure mode is named in the output, `--strict` adds exactly one check, and an unreadable input exits 2 rather than passing quietly. |

Run:

```sh
sh selftest.sh
```

The bad fixture is deliberately realistic. A checker that only rejects broken JSON
proves nothing — the question is whether it rejects a *sick system* that looks healthy,
which is why every line here is something a real implementation emits.
