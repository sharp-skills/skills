# Grounding audit design

Loaded on demand. Structuring output for auditability, the overlap heuristic's
honest limits, adding an entailment layer, and tuning.

## Make the agent emit claims, not prose

The audit is only possible if the output exposes its claims and their support.
Ask the agent for structured output:

```json
{"claims": [
  {"id": "c1", "text": "Q2 revenue increased 12% year over year.", "sources": ["s1"]},
  {"id": "c2", "text": "Growth was driven by enterprise subscriptions.", "sources": ["s1"]}]}
```

against a context of `{sources: {s1: {text: "..."}}}`. This is a small prompt
change with a large payoff: every assertion now carries its own provenance, and
the chain from claim to source is machine-checkable. A free paragraph, however
well-written, is unauditable — you'd be back to reading for wrongness, which is
the thing that doesn't work. Enforce the `{claim, sources}` shape with `llm-output-parsing` (its JSON-validation path).

Not every sentence is a factual claim — framing, transitions, and hedges aren't.
Have the agent mark which spans are load-bearing factual claims (the ones a reader
would act on) and audit those; don't force a citation onto "In summary,".

## The overlap heuristic, honestly

The support gate measures how many of a claim's salient terms appear in its cited
sources. This is deliberately simple, and its limits are real:

- **What it catches well:** uncited claims, fabricated references, and gross
  mis-cites (a real source that shares almost no vocabulary with the claim).
  These are the common, cheap-to-catch failures.
- **What it misses:** a source that uses the claim's words but doesn't actually
  support the assertion ("revenue" and "12%" both appear, but the source said
  revenue *fell* 12%); paraphrase and synonymy (source says "increased", claim
  says "rose") can under-count support.

So a pass means "the citation is plausibly on-topic," not "the claim is true."
Treat it as a floor that removes the obvious garbage, freeing a more expensive
check to focus on the survivors.

## Add an entailment layer on top

For the last mile — does the source actually *entail* the claim — use a model,
following `cross-model-verification`'s discipline. This is **shipped as a seam**:
`grounding_check.py --entailment-cmd "<cli>"`.

- It runs **only on claims that pass the structural gates** (cheap filter first).
- It gives the verifier the claim and its cited source text and asks a closed
  question, expecting JSON `{"entails": "yes|no|partial", "evidence": "..."}`.
  Author ≠ verifier: don't let the agent grade its own grounding.
- It **fails soft** (a dead/missing/malformed verifier degrades to the lexical
  result with a note) and is **advisory** — a `no`/`partial` verdict is printed
  as an `[ADVISORY]` finding but does **not** change the exit code. Promote it to
  a gate only after calibration, as a project-local decision; the structural
  gates keep owning the exit code so CI never depends on model credentials.

```bash
python3 grounding_check.py --output claims.json --context sources.json \
    --entailment-cmd "my-verifier-cli --json"
```

`examples/fake_entailer.py` is a model-free stand-in the self-test uses to prove
the seam wires and stays advisory. Structural gate + entailment layer together
give both cheap coverage and depth.

## Tuning `--min-support`

- **Default 0.5** works for prose claims where paraphrase is expected.
- **Raise it** for claims that carry specific figures, names, or dates — those
  should appear near-verbatim in the source, so demand higher overlap.
- **Per-claim thresholds** beat one global number if your output mixes exact
  data with loose summary; carry an expected-strictness on the claim.

If legitimate claims keep failing on synonymy, that's a signal to add the
entailment layer rather than to lower the threshold into uselessness.

## Grounding is relative to the provided context

"Grounded" here means *supported by the sources the agent was given* — not *true
in the world*. If the retrieved context is wrong or incomplete, a faithful agent
produces a faithfully-wrong claim that passes this audit. Source quality
(retrieval relevance, document trust) is a separate problem upstream; this audit
guarantees the agent didn't invent beyond its material, which is the specific
failure it's built to catch. Track the two separately so a grounding pass is
never mistaken for a correctness guarantee.
