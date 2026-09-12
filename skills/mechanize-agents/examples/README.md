# Examples — mechanize-agents

Run the self-test (no network, stdlib only):

```bash
sh selftest.sh
```

| Fixture | What it demonstrates | Expected |
|---|---|---|
| `handlers.good.json` | Two code agents + one hybrid with a proper defer status | exit 0 |
| `handlers.broken.json` | Four flip hazards at once | exit 1, all four named |

The four planted hazards in the broken manifest:

1. `session_mgr` is `runtime: "code"` in the registry but has no handler —
   the dispatcher would fan out to nothing.
2. The git handler may emit `GITHUB_FORCE_PUSHED`, which the registry never
   publishes — violates same-events-out.
3. The hybrid gate defers via `ANALYSIS_COMPLETE` — a real bus event; defer
   must be an internal hand-off.
4. `ghost_agent` has a handler but no registry entry — explicit wiring fails
   loudly instead of silently checking nothing.
