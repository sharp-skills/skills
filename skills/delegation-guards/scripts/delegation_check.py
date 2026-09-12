#!/usr/bin/env python3
"""Bound agent delegation so a spawning system can't explode into a runaway swarm.

When agents can spawn subagents, three failure modes turn a useful pattern into
a cost-and-latency bomb: unbounded recursion (an agent that keeps delegating
deeper), unbounded fan-out (one agent spawning dozens of children), and
delegation cycles (A delegates to B delegates back to A). None of these announce
themselves — the run just gets slower and more expensive until something times
out or the bill arrives.

Two modes, because a budget that only tells you *why the bill was huge* is worth
far less than one that *refuses the spawn that would blow it*:

  * AUDIT (--tree)      — verify a whole delegation tree after (or during) a run:
                          depth, fan-out, total, cycles, dangling parents.
  * ADMISSION (--candidate) — the pre-spawn gate: given the current tree and one
                          proposed child, answer ALLOW / DENY *before* the spawn
                          happens, so a breach never materialises. This is where
                          enforcement belongs; the audit is the backstop.

AUDIT checks over a spawn tree:
  1. DEPTH   — no path from the root exceeds max_depth.
  2. FAN-OUT — no single agent spawns more than max_fanout children.
  3. TOTAL   — the whole tree stays under max_total nodes (depth and fan-out can
     each be fine while their product is not).
  4. CYCLES  — no node is its own ancestor, and every parent reference resolves.

ADMISSION checks the same budgets against the *would-be* tree (current + 1):
  parent resolves · new depth (parent depth + 1) · parent's new fan-out ·
  new total. Any breach → DENY with the reason; otherwise ALLOW.

Tree (spawns.json): a flat list of nodes, each with its parent (root parent=null):
  {"nodes": [{"id": "root", "parent": null, "agent": "orchestrator"},
             {"id": "n1", "parent": "root", "agent": "researcher"}]}
Policy (policy.json): {"max_depth": 3, "max_fanout": 5, "max_total": 20}
Candidate: --candidate parent=<existing-node-id>

Exit codes: 0 = within budget / ALLOW, 1 = violations / DENY, 2 = bad input.
Stdlib only.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


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


def build(nodes: list) -> "tuple[dict, dict]":
    """Return (parent map, children-count map); validate node shape."""
    parent: dict[str, "str | None"] = {}
    for n in nodes:
        if not isinstance(n, dict) or "id" not in n:
            die("every node needs an 'id'")
        parent[n["id"]] = n.get("parent")
    children: dict[str, int] = {}
    for nid, par in parent.items():
        if par is not None:
            children[par] = children.get(par, 0) + 1
    return parent, children


def depth_of(nid: str, parent: dict) -> "tuple[int, bool]":
    """Hops from nid to root (root = 0). Returns (depth, cyclic)."""
    seen: set = set()
    cur = nid
    depth = 0
    while cur is not None:
        if cur in seen:
            return depth, True
        seen.add(cur)
        cur = parent.get(cur)
        if cur is not None:
            depth += 1
    return depth, False


def audit(nodes, parent, children, max_depth, max_fanout, max_total):
    violations: list[str] = []
    worst_depth = 0

    for nid, par in sorted(parent.items()):
        if par is not None and par not in parent:
            violations.append(f"{nid}: parent {par!r} is not a known node")

    for nid in sorted(parent):
        depth, cyclic = depth_of(nid, parent)
        if cyclic:
            violations.append(f"{nid}: delegation cycle detected (…→{nid}→…) — an infinite loop")
            continue
        worst_depth = max(worst_depth, depth)
        if depth > max_depth:
            violations.append(f"{nid}: delegation depth {depth} exceeds max_depth {max_depth} — runaway recursion")

    for nid, c in sorted(children.items()):
        if c > max_fanout:
            violations.append(f"{nid}: spawns {c} children (> max_fanout {max_fanout}) — fan-out explosion")

    if len(nodes) > max_total:
        violations.append(f"tree has {len(nodes)} nodes (> max_total {max_total}) — swarm over budget")

    return violations, worst_depth


def admit(cand_parent, nodes, parent, children, max_depth, max_fanout, max_total):
    """Would spawning one child under cand_parent breach a budget?
    Returns a list of DENY reasons (empty = ALLOW)."""
    if cand_parent not in parent:
        return [f"candidate parent {cand_parent!r} is not a known node — nothing to spawn under"]

    reasons: list[str] = []
    pdepth, cyclic = depth_of(cand_parent, parent)
    if cyclic:
        return [f"candidate parent {cand_parent!r} sits on a delegation cycle — fix the tree before spawning"]

    new_depth = pdepth + 1
    new_fanout = children.get(cand_parent, 0) + 1
    new_total = len(nodes) + 1

    if new_depth > max_depth:
        reasons.append(f"would create depth {new_depth} (> max_depth {max_depth}) — runaway recursion")
    if new_fanout > max_fanout:
        reasons.append(f"parent {cand_parent!r} would have {new_fanout} children (> max_fanout {max_fanout}) — fan-out explosion")
    if new_total > max_total:
        reasons.append(f"would make {new_total} total nodes (> max_total {max_total}) — swarm over budget")
    return reasons


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--tree", required=True, help="delegation tree JSON")
    ap.add_argument("--policy", required=True, help="budget policy JSON")
    ap.add_argument("--candidate", help="pre-spawn admission: parent=<node-id>")
    args = ap.parse_args()

    tree = load(args.tree, "tree")
    pol = load(args.policy, "policy")
    nodes = tree.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        die("tree has no non-empty 'nodes' list")
    max_depth = pol.get("max_depth", 3)
    max_fanout = pol.get("max_fanout", 5)
    max_total = pol.get("max_total", 20)

    parent, children = build(nodes)

    # --- ADMISSION mode: gate one proposed spawn before it happens ---
    if args.candidate is not None:
        spec = args.candidate.strip()
        if not spec.startswith("parent="):
            die("--candidate must be of the form parent=<node-id>")
        cand_parent = spec[len("parent="):].strip()
        if not cand_parent:
            die("--candidate parent id is empty")
        reasons = admit(cand_parent, nodes, parent, children, max_depth, max_fanout, max_total)
        print(f"Admission: spawn under {cand_parent!r} against a {len(nodes)}-node tree, "
              f"budgets d={max_depth}/f={max_fanout}/n={max_total}.")
        if reasons:
            print(f"\n❌ DENY ({len(reasons)} reason(s)):", file=sys.stderr)
            for r in reasons:
                print(f"  ✗ {r}", file=sys.stderr)
            return 1
        print("✅ ALLOW: the spawn stays within depth, fan-out, and total budgets.")
        return 0

    # --- AUDIT mode: verify the whole tree ---
    violations, worst_depth = audit(nodes, parent, children, max_depth, max_fanout, max_total)
    print(f"Delegation tree: {len(nodes)} node(s), worst depth {worst_depth}, "
          f"budgets d={max_depth}/f={max_fanout}/n={max_total}.")
    if violations:
        print(f"\n{len(violations)} violation(s):", file=sys.stderr)
        for v in violations:
            print(f"  ✗ {v}", file=sys.stderr)
        return 1
    print("✅ Delegation within budget: depth, fan-out, and total under caps, no cycles.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
