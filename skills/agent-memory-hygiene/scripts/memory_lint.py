#!/usr/bin/env python3
"""Lint an agent's persistent memory store for the four ways memory rots.

Agent memory is seductive: write a fact once, recall it forever. But memory that
isn't maintained becomes a liability — it goes stale and misleads, it grows
without bound and drowns recall, it quietly accumulates secrets that then leak
into every context that reads it, and it absorbs attacker-authored "facts" that
later get trusted. This check enforces hygiene over a memory store so recall
stays trustworthy.

Checks per entry (and over the store):

  1. PROVENANCE — every entry records where it came from (a source / trace id).
     A fact with no origin can't be trusted, audited, or retired on cause.

  2. FRESHNESS  — every entry carries a timestamp, and an entry older than the
     max age without an update is flagged for review. Memory is point-in-time;
     an un-reviewed old fact is asserted as current and misleads.

  3. NO SECRETS — no entry contains a credential or obvious PII. Memory is read
     into many contexts with little scoping, so a secret in memory is a secret
     leaked widely. Keep secrets in a vault, references in memory.

  4. NO POISON  — an entry sourced from untrusted content may not be marked as
     an authoritative fact. Untrusted input recorded as fact is how a prompt
     injection becomes permanent (pairs with agent-isolation).

Store-level: exact-duplicate text and a total-size cap catch unbounded growth.

Store shape (store.json):
  {"entries": [
     {"id": "u1", "text": "...", "updated": "2026-06-01T00:00:00Z",
      "source": "trace-abc", "trust": "verified", "type": "fact"}]}

Exit codes: 0 = memory is healthy, 1 = violations, 2 = bad input. Stdlib only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

SECRETS = [
    (re.compile(r"\bsk-[A-Za-z0-9]{16,}"), "API key (sk-...)"),
    (re.compile(r"\bghp_[A-Za-z0-9]{20,}"), "GitHub token (ghp_...)"),
    (re.compile(r"\bAKIA[0-9A-Z]{12,}"), "AWS access key"),
    (re.compile(r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----"), "private key"),
    (re.compile(r"(?i)\bpassword\s*[:=]\s*\S+"), "inline password"),
    (re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"), "email address (PII)"),
]
UNTRUSTED = {"untrusted", "web", "inbound", "external"}
AUTHORITATIVE = {"fact", "rule", "policy"}


def die(msg: str) -> "NoReturn":
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(2)


def parse_ts(v) -> "datetime | None":
    if not isinstance(v, str) or not v.strip():
        return None
    s = v.strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--store", required=True, help="memory store JSON")
    ap.add_argument("--max-age-days", type=int, default=180, help="flag entries older than this")
    ap.add_argument("--max-entries", type=int, default=500, help="store-size cap")
    ap.add_argument("--now", help="ISO timestamp treated as 'now' (default: real now)")
    args = ap.parse_args()

    try:
        doc = json.loads(Path(args.store).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        die(f"cannot read store {args.store}: {exc}")
    entries = doc.get("entries") if isinstance(doc, dict) else doc
    if not isinstance(entries, list):
        die("store must be a list of entries or an object with 'entries'")

    now = parse_ts(args.now) if args.now else datetime.now(timezone.utc)
    if args.now and now is None:
        die(f"--now is not a valid ISO timestamp: {args.now!r}")

    violations: list[str] = []
    seen: dict[str, str] = {}

    for e in entries:
        if not isinstance(e, dict):
            violations.append("an entry is not an object")
            continue
        eid = e.get("id") or "<no-id>"
        text = e.get("text") if isinstance(e.get("text"), str) else ""

        # 1. provenance
        if not (isinstance(e.get("source"), str) and e["source"].strip()):
            violations.append(f"{eid}: no 'source' — a fact with no origin can't be trusted or retired on cause")

        # 2. freshness
        ts = parse_ts(e.get("updated") or e.get("created"))
        if ts is None:
            violations.append(f"{eid}: no valid 'updated'/'created' timestamp — staleness can't be assessed")
        else:
            age = (now - ts).days
            if age > args.max_age_days:
                violations.append(f"{eid}: {age}d old (> {args.max_age_days}d) and un-reviewed — re-verify or retire")

        # 3. no secrets / PII
        for rx, label in SECRETS:
            if rx.search(text):
                violations.append(f"{eid}: contains {label} — keep secrets in a vault, a reference in memory")
                break

        # 4. no poison (untrusted recorded as authoritative)
        trust = str(e.get("trust", "")).lower()
        etype = str(e.get("type", "")).lower()
        if trust in UNTRUSTED and etype in AUTHORITATIVE:
            violations.append(
                f"{eid}: sourced from {trust!r} but stored as {etype!r} — untrusted "
                f"content must not be recorded as an authoritative fact")

        # store-level: exact duplicate
        norm = " ".join(text.split()).lower()
        if norm and norm in seen:
            violations.append(f"{eid}: duplicate text of {seen[norm]} — dedupe to bound growth")
        elif norm:
            seen[norm] = eid

    if len(entries) > args.max_entries:
        violations.append(
            f"store has {len(entries)} entries (> cap {args.max_entries}) — "
            f"distill and retire; unbounded memory drowns recall")

    print(f"Linted {len(entries)} memory entr(ies) (max age {args.max_age_days}d, cap {args.max_entries}).")
    if violations:
        print(f"\n{len(violations)} violation(s):", file=sys.stderr)
        for v in violations:
            print(f"  ✗ {v}", file=sys.stderr)
        return 1
    print("✅ Memory is healthy: every entry has provenance, is fresh, secret-free, "
          "and untrusted content isn't stored as fact.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
