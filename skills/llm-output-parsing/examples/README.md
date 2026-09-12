# llm-output-parsing examples

Fixtures that prove both halves offline. Run `sh selftest.sh` (stdlib only).

## Half 1 — prose extraction (`parse_output.py`)

| File | Role |
|---|---|
| `spec.json` | Three targets: `verdict` (enum approve/reject/revise), `score` (number 0–100), `blocking` (boolean). |
| `out.clean.txt` | Labeled prose — `Verdict: approve`, `Score: 85`, `Blocking: no`; all extract cleanly. |
| `out.ambiguous.txt` | Unlabeled prose that argues "reject" then "approve" — the verdict is reported `ambiguous`, not guessed. |
| `out.problem.txt` | No verdict at all (`not_found`) and a `Score: 150` out of bounds (`invalid`); the labeled boolean still extracts. |

## Half 2 — mostly-JSON validation (`output_validate.py`, fixtures under `json-validation/`)

| File | Role |
|---|---|
| `json-validation/out.schema.json` | Schema subset: required fields, types, enum, numeric bounds. |
| `json-validation/out.clean.txt` | Bare valid JSON. |
| `json-validation/out.fenced.txt` | Valid JSON inside a ```json fence. |
| `json-validation/out.prose.txt` | Valid JSON buried in a preamble/coda. |
| `json-validation/out.trailingcomma.txt` | Valid but for a trailing comma (the one safe repair). |
| `json-validation/out.badenum.txt` | Parses, but an out-of-enum / out-of-bounds value → `invalid`. |
| `json-validation/out.notjson.txt` | Pure prose, no JSON → re-ask. |

`selftest.sh` asserts: prose clean → 0, ambiguous/problem → 1, missing spec → 2; JSON clean/fenced/prose/trailing-comma → 0, bad enum-or-bounds and non-JSON → 1, missing schema → 2.

Try it:

```bash
python3 ../scripts/parse_output.py    --spec spec.json --output out.ambiguous.txt          # prose
python3 ../scripts/output_validate.py --schema json-validation/out.schema.json --output json-validation/out.fenced.txt   # JSON
```

The lesson in one line: `out.ambiguous.txt` is exactly the case a first-match
regex gets wrong, and `json-validation/out.fenced.txt` is the "almost-JSON" a raw
`json.loads` crashes on — this skill refuses to guess on the first and safely
recovers the second.
