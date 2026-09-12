# Examples — prompt-contracts

Run the self-test (no network, stdlib only):

```bash
sh selftest.sh
```

| Config | What it demonstrates | Expected |
|---|---|---|
| `config.clean.json` | Registry, schemas, and prompts agree | exit 0 |
| `config.broken.json` | Forbidden status hidden in a `oneOf` branch (F-2) + stale worked example in a prompt (F-4) | exit 1 |
| `config.badwiring.json` | Glob matching nothing fails loudly (F-3) | exit 2 |

The planted defects mirror real incidents from `references/failure-catalog.md`.

## Versioning fixtures (`versioning/`, for `prompt_version_check.py`)

| File | What it demonstrates | Expected |
|---|---|---|
| `versioning/prompts.good.json` + `planner.txt`/`router.txt` | Prompts pinned by content hash, active resolves, changelog per version, valid rollback | exit 0 |
| `versioning/prompts.bad.json` | Edit-in-place drift (hash≠pin), empty changelog, dangling `rollback_to`, missing active version | exit 1 |

Hashes are sha256 of the prompt file's bytes; paths resolve relative to the manifest.
