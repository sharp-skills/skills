#!/usr/bin/env python3
"""Persistent agent experience: EMA confidence + structured learnings.

One JSON file holds per-agent experience:

  {"version": 1, "last_updated": "...",
   "agents": {"analyst": {
      "session_count": 12,
      "ema_confidence": 76.4,
      "learnings": [{"ts": "...", "category": "schema_drift",
                     "insight": "...", "outcome": "...", "retired": false}]}}}

Subcommands:
  record           add a learning and fold confidence into the EMA
  show [agent]     print current experience (all agents or one)
  check-staleness  exit 1 if the file hasn't been written in --max-age-days

EMA: new = alpha*observation + (1-alpha)*old, alpha default 0.3 — recent
behavior dominates, ancient history fades, one outlier can't swing it.

Exit codes: 0 ok · 1 stale (check-staleness only) · 2 bad input. Stdlib only.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

EMA_ALPHA = 0.3
BOOTSTRAP_CONFIDENCE = 70.0   # a new agent starts at a typical floor, not at 0


def die(msg: str) -> "NoReturn":
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(2)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load(path: Path) -> dict:
    if not path.exists():
        return {"version": 1, "last_updated": None, "agents": {}}
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        die(f"cannot read {path}: {exc}")
    if not isinstance(doc, dict) or "agents" not in doc:
        die(f"{path} is not a learnings file (no 'agents')")
    return doc


def save(path: Path, doc: dict) -> None:
    doc["last_updated"] = now_iso()
    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def ema(old: float, observation: float, alpha: float) -> float:
    return round(alpha * observation + (1 - alpha) * old, 3)


def cmd_record(args) -> int:
    if not (0 <= args.confidence <= 100):
        die("confidence must be 0..100")
    path = Path(args.file)
    doc = load(path)
    agent = doc["agents"].setdefault(args.agent, {
        "session_count": 0,
        "ema_confidence": BOOTSTRAP_CONFIDENCE,
        "learnings": [],
    })
    agent["session_count"] += 1
    old = float(agent.get("ema_confidence", BOOTSTRAP_CONFIDENCE))
    agent["ema_confidence"] = ema(old, args.confidence, args.alpha)
    if args.category or args.insight:
        if not (args.category and args.insight and args.outcome):
            die("a learning needs --category, --insight AND --outcome "
                "(unstructured entries can't be counted, so they can't graduate)")
        agent["learnings"].append({
            "ts": now_iso(), "category": args.category,
            "insight": args.insight, "outcome": args.outcome, "retired": False,
        })
    save(path, doc)
    print(f"{args.agent}: sessions={agent['session_count']} "
          f"ema {old:.1f} -> {agent['ema_confidence']:.1f}"
          + (f" · learning[{args.category}] recorded" if args.category else ""))
    return 0


def cmd_show(args) -> int:
    doc = load(Path(args.file))
    agents = doc["agents"]
    names = [args.agent] if args.agent else sorted(agents)
    if args.agent and args.agent not in agents:
        die(f"no such agent: {args.agent}")
    print(f"last_updated: {doc.get('last_updated')}")
    for name in names:
        a = agents[name]
        active = [l for l in a.get("learnings", []) if not l.get("retired")]
        cats: dict[str, int] = {}
        for l in active:
            cats[l["category"]] = cats.get(l["category"], 0) + 1
        top = ", ".join(f"{c}×{n}" for c, n in
                        sorted(cats.items(), key=lambda kv: -kv[1])[:3]) or "—"
        print(f"  {name:<20} ema={a.get('ema_confidence', 0):5.1f} "
              f"sessions={a.get('session_count', 0):<4} "
              f"active_learnings={len(active):<3} top: {top}")
        if args.agent:
            for l in active:
                print(f"    [{l['category']}] {l['insight']} -> {l['outcome']}")
    return 0


def cmd_staleness(args) -> int:
    path = Path(args.file)
    doc = load(path)
    last = doc.get("last_updated")
    if not last:
        print(f"STALE: {path} has never been written — the capture end of the "
              f"loop is not wired", file=sys.stderr)
        return 1
    try:
        age = datetime.now(timezone.utc) - datetime.fromisoformat(last.replace("Z", "+00:00"))
    except ValueError:
        die(f"unparseable last_updated: {last}")
    days = age.total_seconds() / 86400
    if days > args.max_age_days:
        print(f"STALE: last write {days:.1f} days ago (max {args.max_age_days}) — "
              f"a memory nobody writes is decoration; check the recorder hook",
              file=sys.stderr)
        return 1
    print(f"fresh: last write {days:.1f} days ago (max {args.max_age_days})")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("record", help="record a run's confidence (+ optional learning)")
    r.add_argument("--file", required=True)
    r.add_argument("--agent", required=True)
    r.add_argument("--confidence", type=float, required=True, help="0..100 for this run")
    r.add_argument("--alpha", type=float, default=EMA_ALPHA)
    r.add_argument("--category")
    r.add_argument("--insight")
    r.add_argument("--outcome")
    r.set_defaults(fn=cmd_record)

    s = sub.add_parser("show", help="print experience (all agents or one)")
    s.add_argument("agent", nargs="?")
    s.add_argument("--file", required=True)
    s.set_defaults(fn=cmd_show)

    c = sub.add_parser("check-staleness", help="exit 1 if the loop stopped writing")
    c.add_argument("--file", required=True)
    c.add_argument("--max-age-days", type=float, default=14)
    c.set_defaults(fn=cmd_staleness)

    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
