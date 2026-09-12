# Examples — governance-hooks

Run the self-test (no network, stdlib only):

```bash
sh selftest.sh
```

| Check | Fixture / input | Expected |
|---|---|---|
| no-touch allow | `src/main.py` | exit 0 |
| no-touch block | `config/registry.json`, `migrations/001_init.sql` | exit 2, reason on stderr |
| secret read block | `.env` | exit 2 |
| secret command block / allow | `cat .env` / `ls -la` | exit 2 / exit 0 |
| named override | `GOVERNANCE_OVERRIDE=1` + protected path | exit 0 |
| hook adapter | tool-call JSON on stdin (block, allow, fail-open) | exit 2 / 0 / 0 |
| drift | snapshot → clean → mutate `demo/config/app.json` → dirty | 0 → 0 → 2 |

`zones.json` here is a minimal working config; the full field reference is in
`references/wiring.md`.
