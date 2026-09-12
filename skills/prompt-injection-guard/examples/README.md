# prompt-injection-guard examples

Fixtures that prove the scan offline. Run `sh selftest.sh` (stdlib only).

| File | Role |
|---|---|
| `content.good.jsonl` | Untrusted spans delimited as data (incl. one with a proper unpredictable marker `<<DATA-9f3a12c7>>`), plus a trusted instruction — no signatures, nothing undelimited, boundary intact. |
| `content.bad.jsonl` | One per class: an instruction override, an undelimited `web` span, a `system:`/"you are now" role spoof, injected `<tool_call>` markup — and `b5`, a **boundary escape** where the untrusted text contains its own marker `<<DATA-1234abcd>>` and climbs out of the data region. |
| `content.weakmarker.jsonl` | An untrusted span wrapped in a guessable static marker `<<UNTRUSTED>>` — a **warning** by default (exit 0), a hard finding under `--strict`. |
| `selftest.sh` | Asserts clean → 0; undelimited-untrusted, boundary escape, each signature class → 1; guessable marker → warn/`--strict`; missing file → 2. |

Try it:

```bash
python3 ../scripts/injection_scan.py --content content.bad.jsonl            # see the boundary escape on b5
python3 ../scripts/injection_scan.py --content content.weakmarker.jsonl --strict
```

The load-bearing checks are the boundary ones (escape + unpredictable marker);
the signature list at the top of `scripts/injection_scan.py` is the cheap,
bypassable second wall. Delimiting and `agent-isolation` do the real work.
