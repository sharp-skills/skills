#!/usr/bin/env python3
"""Audit an agent's factual claims for grounding in the source context it was given.

A hallucination is a claim with no support in the material the agent was working
from. You can't detect that by reading the claim — it's fluent and confident by
construction. You *can* detect it structurally: require every factual claim to
cite a source, require the cited source to exist, and require the source to
actually mention what the claim asserts. What survives all three is grounded;
what fails is a hallucination or a mis-citation, flagged before a human trusts it.

Checks per claim:

  1. CITED     — the claim cites at least one source. An uncited factual claim
     is ungrounded by definition; it may be true, but nothing here supports it.
  2. RESOLVES  — every cited source id exists in the provided context. A citation
     to a source that isn't there is a fabricated reference (a common and
     convincing hallucination shape).
  3. SUPPORTED — the claim's salient terms actually appear in the cited
     source(s). Citing a real but irrelevant source ("cited [3], which is about
     something else") fails here. This is a lexical-overlap heuristic, not
     entailment — it catches the obvious mis-cite, not subtle misreading.

Output (output.json):
  {"claims": [{"id": "c1", "text": "Revenue rose 12% in Q2.", "sources": ["s1"]}]}
Context (context.json):
  {"sources": {"s1": {"text": "Q2 revenue increased 12% year over year."}}}

Exit codes: 0 = every claim grounded, 1 = ungrounded/mis-cited, 2 = bad input.
Stdlib only.
"""

from __future__ import annotations

import argparse
import json
import re
import shlex
import subprocess
import sys
from pathlib import Path

STOP = {
    "the", "a", "an", "and", "or", "but", "of", "to", "in", "on", "for", "with",
    "is", "are", "was", "were", "be", "been", "by", "at", "as", "it", "its",
    "this", "that", "these", "those", "from", "up", "down", "over", "than",
}


def die(msg: str) -> "NoReturn":
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(2)


def load(path: str, what: str) -> dict:
    try:
        doc = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        die(f"cannot read {what} {path}: {exc}")
    if not isinstance(doc, dict):
        die(f"{what} must be a JSON object: {path}")
    return doc


def terms(text: str) -> set[str]:
    words = re.findall(r"[A-Za-z0-9]+", text.lower())
    return {w for w in words if len(w) > 2 and w not in STOP}


def entailment_layer(passed: list[tuple[str, str, str]], cmd: str) -> tuple[list[str], list[str]]:
    """The last mile the lexical floor can't reach: does the source *entail* the claim?

    Runs ONLY on claims that already passed the structural gates (cheap filter
    first), following cross-model-verification's discipline (author != verifier).
    For each surviving claim it asks the external model a closed question and
    collects an ADVISORY finding when the verdict is 'no' or 'partial'. Fails
    SOFT: any error degrades to the lexical result with a note, and the layer
    never changes the exit code — promote it to a gate only after calibration
    (see references/grounding-design.md).

    Returns (advisory_findings, notes).
    """
    findings: list[str] = []
    ran = 0
    for cid, claim_text, source_text in passed:
        prompt = (
            "You are an independent grounding verifier (NOT the author). Answer "
            "ONLY whether the SOURCE entails the CLAIM. Reply with ONLY JSON: "
            '{"entails": "yes|no|partial", "evidence": "the supporting sentence or \'\'"}.'
            f"\n\nCLAIM:\n{claim_text[:2000]}\n\nSOURCE:\n{source_text[:6000]}"
        )
        try:
            r = subprocess.run(shlex.split(cmd) + [prompt],
                               capture_output=True, text=True, timeout=120)
            a, b = r.stdout.find("{"), r.stdout.rfind("}")
            verdict = json.loads(r.stdout[a:b + 1]) if a != -1 and b != -1 else None
            if not isinstance(verdict, dict):
                raise ValueError("no JSON object in verifier output")
        except Exception as exc:
            return [], [f"entailment verifier unavailable ({type(exc).__name__}) — "
                        f"kept the lexical result (control arm); exit code unaffected"]
        ran += 1
        ent = str(verdict.get("entails", "")).lower()
        if ent in ("no", "partial"):
            findings.append(
                f"{cid}: lexical overlap passed but the source does NOT fully "
                f"entail the claim (verdict: {ent}) — the mis-entailment the "
                f"overlap heuristic structurally cannot catch [ADVISORY]")
    return findings, [f"entailment verifier ran on {ran} grounded claim(s): "
                      f"{len(findings)} advisory finding(s)"]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--output", required=True, help="agent output with claims JSON")
    ap.add_argument("--context", required=True, help="provided source context JSON")
    ap.add_argument("--min-support", type=float, default=0.5,
                    help="min fraction of a claim's salient terms found in cited sources")
    ap.add_argument("--entailment-cmd",
                    help="external verifier CLI run on structurally-grounded claims (claim+source appended as last arg); "
                         "JSON verdict on stdout; fails soft; advisory (never changes the exit code)")
    args = ap.parse_args()

    out = load(args.output, "output")
    ctx = load(args.context, "context")
    claims = out.get("claims")
    if not isinstance(claims, list) or not claims:
        die("output has no non-empty 'claims' list")
    sources = ctx.get("sources")
    if not isinstance(sources, dict):
        die("context must have a 'sources' object")

    violations: list[str] = []
    grounded = 0
    passed: list[tuple[str, str, str]] = []  # (id, claim_text, cited_source_text) for the entailment layer

    for c in claims:
        if not isinstance(c, dict):
            violations.append("a claim is not an object")
            continue
        cid = c.get("id") or "<no-id>"
        cited = c.get("sources") or []

        # 1. cited at all
        if not cited:
            violations.append(f"{cid}: no citation — factual claim is ungrounded")
            continue

        # 2. citations resolve
        missing = [s for s in cited if s not in sources]
        if missing:
            violations.append(f"{cid}: cites source(s) {missing} that are not in the context — fabricated reference")
            continue

        # 3. cited sources actually mention the claim's terms
        claim_terms = terms(c.get("text", ""))
        cited_text = " ".join(sources[s].get("text", "") if isinstance(sources[s], dict) else "" for s in cited)
        src_terms = terms(cited_text)
        if claim_terms:
            overlap = len(claim_terms & src_terms) / len(claim_terms)
            if overlap < args.min_support:
                violations.append(
                    f"{cid}: cited source(s) cover only {overlap:.0%} of the claim's "
                    f"terms (< {args.min_support:.0%}) — the citation doesn't substantiate it")
                continue
        grounded += 1
        passed.append((cid, c.get("text", ""), cited_text))

    print(f"Audited {len(claims)} claim(s); {grounded} grounded.")

    # Optional entailment layer: advisory, fails soft, runs only on survivors.
    if args.entailment_cmd and passed:
        advisory, notes = entailment_layer(passed, args.entailment_cmd)
        for n in notes:
            print(f"  [note] {n}")
        for a in advisory:
            print(f"  ~ {a}", file=sys.stderr)

    if violations:
        print(f"\n{len(violations)} finding(s):", file=sys.stderr)
        for v in violations:
            print(f"  ✗ {v}", file=sys.stderr)
        return 1
    print("✅ Every claim is grounded: cited, the citations resolve, and the "
          "sources substantiate the claim's terms.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
