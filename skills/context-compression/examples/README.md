# context-compression examples

Fixtures that prove the linter offline. Run `sh selftest.sh` (stdlib only).

| File | Role |
|---|---|
| `models.json` | Model catalog: name → context_window. `big-cloud-main` (400K), `flash-summarizer` (1M, cheap+large), `small-local-3b` (8K, the trap), `same-as-main` (400K). |
| `compaction.good.json` | Safe config: large-window cheap summarizer, protect_last_n 20, threshold 0.5 > target 0.2. |
| `compaction.bad.json` | Three mistakes at once: `small-local-3b` summarizer (8K < 400K window rule), `target_ratio` 0.7 ≥ threshold 0.5 (thrash), `protect_last_n` 0. |
| `selftest.sh` | Asserts safe → 0; window/ratio/protect, disabled, and unknown-model cases → 1; missing file → 2. |

Try it:

```bash
python3 ../scripts/compression_lint.py --config compaction.bad.json --models models.json
```

The headline line to look for:

```
compaction model window 8192 < main model window 400000 — the summarizer
cannot read the context that overflowed the main model; this errors and
loses context. Pick a summarizer whose window is >= the main model's (400000).
```
