---
name: llm-output-parsing
description: >-
  Get a trustworthy typed value out of a model's response, or a clean re-ask — never a guess. Two shapes: free-form prose you can't get as JSON (extract a verdict/score/boolean, and flag conflicting values as ambiguous instead of grabbing the first match), and "mostly JSON" wrapped in fences (extract, safe-repair, validate against a schema, re-ask on failure). The rule both share: never invent a value. Use when a downstream agent consumes another agent's output and a naive regex or `json.loads` returns the wrong value or crashes. Works on any model's text, not a provider format.
license: Apache-2.0
---

# LLM Output Parsing

The dangerous bug in reading a model's output is the one that looks like success. You regex the first `approve` out of a judge's reply — but the judge *reasoned* "my instinct was to reject… on reflection, approve", so you extract `reject`, the exact opposite of the verdict, with total confidence and no error raised. Preventing that silent-wrong-answer is the point: when the text carries conflicting values this skill reports `ambiguous` and **refuses to pick**, because a wrong value that looks certain is worse than an honest "I couldn't tell — ask again."

That refusal is one rule — **never invent a value** — applied across the two shapes a consumed output arrives in: prose you can't get as JSON, and "mostly JSON" wrapped in fences and preambles. Each corrupts the pipeline *silently* if mishandled; this skill turns either into a trustworthy typed value or a clean re-ask.

## Two problems, one boundary

- **Prose you can't get as JSON.** The producer is a component you don't control, a model answering conversationally, or an LLM judge burying its verdict in reasoning: *"my first instinct was to reject this, but on reflection I'd approve it, maybe 85% confident."* You still need the decision out of that text.
- **"Mostly JSON."** You asked for JSON and got JSON *with company*: a ```json fence, a "Here's the result:" preamble, a "let me know if you need changes" coda, a trailing comma learned from a million code samples. Every one makes `json.loads(raw)` throw.

Different inputs, different failure modes — but the same consumer boundary and the same refusal to guess. Handle the one you have.

## Half 1 — recovering a signal from prose

This is the half that catches the silent-wrong-answer above. Extraction reports one of four honest outcomes per target:

- **ok** — exactly one unambiguous, valid value. Use it.
- **not_found** — no value present. The caller re-asks or applies a *documented* default — a knowing choice, not a silent zero.
- **ambiguous** — multiple *conflicting* values (both "approve" and "reject" appear). **The caller must not guess.** Re-ask, or escalate to a human. This is the outcome the naive regex never surfaces and the whole reason this half exists.
- **invalid** — a value was found but fails its type, enum, or bounds (a score of 150, an enum word not in the set).

**Prefer labels, fall back to scanning.** Extraction is most reliable when the signal is *labeled* — "Verdict: approve", "Score: 85", "Blocking: no" — so it looks for `name: value` / `name = value` / `name is value` first. Only if there's no label does it scan the whole text, and that's exactly where ambiguity is likely (reasoning and conclusion both mention enum values). Practical guidance: **prompt the producer to label its answers**, even in prose. A labeled prose output is nearly as parseable as JSON.

## Half 2 — validating "mostly JSON"

When you *did* get JSON, the boundary is a four-stage pipeline, and its safety rule is the same: locating and de-fencing JSON is deterministic and lossless; *filling in a missing field or fixing a wrong one is authorship* — the model's job, via a bounded retry, not something a parser papers over.

1. **Extract.** Pull the JSON from a fenced block if present; otherwise scan for the outermost balanced `{...}`/`[...]` and ignore the prose around it. Most "invalid" model output is valid JSON wearing a coat.
2. **Repair — safely only.** Strip trailing commas and nothing else. Safe repairs cannot change the parsed value; anything that could (quoting a bareword, inventing a close brace) is off-limits — a silently-wrong object is worse than a clean failure.
3. **Parse.** `json.loads` the candidate. If it still won't parse after the safe repair, that's a re-ask, not a heroics problem.
4. **Validate.** Required fields present, types correct, enums and numeric bounds respected — where a structurally-valid but semantically-wrong output (an out-of-range score, an invented enum value) is caught before it reaches a consumer.

The three JSON outcomes map to the three exit codes: **valid (0)** hand downstream; **invalid (1)** re-ask with the specific error as feedback ("field `confidence` must be 0–100; you returned 150") up to a bounded number of retries; **input error (2)** the schema itself is unreadable — a wiring problem, not a model one.

## Which half, and when

If you control the producer, **ask for JSON and use Half 2** — it's more reliable. Half 1 is the fallback for when you can't change the producer (a component you don't own, an inherently narrative answer, a judge that reasons out loud). Prose extraction is second choice, not the default.

## Run vs read

| Resource | Action | Why |
|---|---|---|
| `scripts/parse_output.py` | **RUN** | Half 1: extract enum / number / boolean targets from prose (label-first, scan fallback); reports ok / not_found / ambiguous / invalid per target. |
| `scripts/output_validate.py` | **RUN** | Half 2: extract → safe-repair → parse → validate one raw output against a schema subset (required, type, enum, min/max). |
| `references/parsing-design.md` | **READ** | Why ambiguity beats first-match, prompting for labels, handling each outcome. |
| `references/validation-design.md` | **READ** | The safe-vs-unsafe repair line, the bounded retry loop, and where this sits vs schema contracts. |
| `examples/selftest.sh` | **RUN** | Proves both halves: prose ambiguity/missing/out-of-range, and JSON messy-but-valid / invalid / non-JSON. |

```bash
python3 .../parse_output.py    --spec spec.json           --output raw.txt   # prose
python3 .../output_validate.py --schema json-validation/out.schema.json --output raw.txt   # mostly-JSON
```

## Common pitfalls

- **First-match extraction (prose).** Grabbing the first enum word ignores that the model may argue the other side first — the silent-wrong-answer bug this is built to prevent.
- **`json.loads(raw)` with no extraction (JSON).** Crashes on the fence, the preamble, the coda — i.e. on most real outputs. Extract first.
- **"Repairing" by guessing.** Adding a missing field or coercing a wrong enum hides a real model error and ships a plausible-looking lie. Repair only what can't change meaning; escalate the rest to a re-ask.
- **Guessing on ambiguity.** If the prose says both, the honest answer is "ask again", never a coin flip dressed as certainty.
- **Retrying without the error.** "Try again" gets the same output; "field X must be an integer, you sent a string" gets a fix. Feed the specific failure back.
- **Unbounded retries.** A model that can't produce valid output in 2–3 tries won't on the 10th; cap it and surface the failure (see `two-layer-critic`'s retry cap).
- **Treating not_found as a default value.** "No verdict found" is not "reject"; surface it and let the caller decide.

## Verification checklist

- [ ] `sh examples/selftest.sh` passes (prose clean → 0, ambiguous/missing/out-of-range → 1, missing spec → 2; JSON clean/fenced/prose/trailing-comma → 0, bad enum-or-bounds and non-JSON → 1, missing schema → 2).
- [ ] Conflicting prose values produce `ambiguous`, and the caller re-asks rather than guessing.
- [ ] Only value-preserving JSON repairs are applied; nothing is invented.
- [ ] Invalid output triggers a bounded re-ask carrying the specific error, not a crash or a coercion.
- [ ] JSON (Half 2) is used instead of prose extraction wherever the producer can be changed.

## Related skills in this bundle

- `prompt-contracts` — validates the output *schema* statically (enums narrow the registry); this validates a runtime *instance* against that schema.
- `event-envelope` — the envelope carries an opaque `payload`; this is how a consumer safely turns that payload text into a checked object.
- `cross-model-verification` / `two-layer-critic` — a verifier's or judge's verdict often arrives as prose; this is how you extract it, ambiguity and all, then validate it before acting.
- `eval-harness` — both refuse to manufacture certainty a source doesn't support; here it's the extracted value, there (its grounding check) it's the factual claim.
