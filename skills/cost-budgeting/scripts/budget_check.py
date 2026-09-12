#!/usr/bin/env python3
"""Budget check for recorded multi-agent runs.

Reads a per-trace JSONL file (observability-tracing format: one event per
line with `agent`, `input_tokens`, `output_tokens`) and checks it against
declared budgets:

  budgets.json:
  {"derived_from": "traces 2026-06, healthy median x1.5",
   "run":    {"max_total_tokens": 20000, "max_steps": 40},
   "agents": {"analyst":  {"max_input_tokens": 4000, "max_output_tokens": 1500, "max_steps": 3},
              "engineer": {"max_input_tokens": 8000, "max_output_tokens": 3000}},
   "require_coverage": true}

Per-agent numbers are TOTALS across the run (an agent called twice spends
twice). `require_coverage` flags agents seen in the trace but absent from
budgets — an unbudgeted agent is an unmetered one.

Exit codes: 0 = within budget, 1 = overruns/coverage gaps, 2 = bad input.
Stdlib only.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

STRUCTURAL_KINDS = {"trace_start", "trace_end"}


def die(msg: str) -> "NoReturn":
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(2)


def resolve_trace(trace_id: str | None, latest: bool, traces_dir: pathlib.Path) -> pathlib.Path:
    if latest:
        if not traces_dir.is_dir():
            die(f"traces dir not found: {traces_dir}")
        files = sorted(traces_dir.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not files:
            die(f"no .jsonl traces in {traces_dir}")
        return files[0]
    if not trace_id:
        die("provide a trace id/path or --latest")
    p = pathlib.Path(trace_id)
    if p.exists():
        return p
    p = traces_dir / (trace_id if trace_id.endswith(".jsonl") else f"{trace_id}.jsonl")
    if not p.exists():
        die(f"trace not found: {p}")
    return p


def load_events(path: pathlib.Path) -> list[dict]:
    events = []
    try:
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                ev = json.loads(line)
            except json.JSONDecodeError as exc:
                die(f"invalid JSON on line {n}: {exc}")
            if isinstance(ev, dict):
                events.append(ev)
    except OSError as exc:
        die(f"cannot read trace: {exc}")
    if not events:
        die(f"trace is empty: {path}")
    return events


def tally(events: list[dict]) -> tuple[dict, int, int]:
    per_agent: dict[str, dict] = {}
    total_tokens = 0
    steps = 0
    for ev in events:
        if ev.get("kind") in STRUCTURAL_KINDS:
            continue
        steps += 1
        agent = str(ev.get("agent", "unknown"))
        a = per_agent.setdefault(agent, {"input": 0, "output": 0, "steps": 0})
        for key, field in (("input", "input_tokens"), ("output", "output_tokens")):
            v = ev.get(field)
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                a[key] += int(v)
                total_tokens += int(v)
        a["steps"] += 1
    return per_agent, total_tokens, steps


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("trace_id", nargs="?", help="trace id, path, or filename under --traces-dir")
    ap.add_argument("--latest", action="store_true", help="check the most recent trace")
    ap.add_argument("--traces-dir", default=".context/traces")
    ap.add_argument("--budgets", required=True, help="budgets.json")
    args = ap.parse_args()

    try:
        budgets = json.loads(pathlib.Path(args.budgets).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        die(f"cannot read budgets: {exc}")

    trace = resolve_trace(args.trace_id, args.latest, pathlib.Path(args.traces_dir))
    per_agent, total_tokens, steps = tally(load_events(trace))

    overruns: list[str] = []
    agent_budgets = budgets.get("agents") or {}

    print(f"trace: {trace}")
    print(f"{'agent':<20} {'in':>8} {'out':>8} {'steps':>6}   budget verdict")
    for agent, a in sorted(per_agent.items()):
        b = agent_budgets.get(agent)
        verdict = "unbudgeted"
        if b:
            probs = []
            if b.get("max_input_tokens") is not None and a["input"] > b["max_input_tokens"]:
                probs.append(f"input {a['input']}>{b['max_input_tokens']}")
            if b.get("max_output_tokens") is not None and a["output"] > b["max_output_tokens"]:
                probs.append(f"output {a['output']}>{b['max_output_tokens']}")
            if b.get("max_steps") is not None and a["steps"] > b["max_steps"]:
                probs.append(f"steps {a['steps']}>{b['max_steps']}")
            verdict = "OVER: " + "; ".join(probs) if probs else "ok"
            overruns += [f"{agent}: {p} — near-budget calls are decomposition "
                         f"candidates, not timeout-increase requests" for p in probs]
        elif budgets.get("require_coverage"):
            overruns.append(f"{agent}: seen in the trace but has no budget — "
                            f"an unbudgeted agent is an unmetered one")
        print(f"{agent:<20} {a['input']:>8} {a['output']:>8} {a['steps']:>6}   {verdict}")

    run_b = budgets.get("run") or {}
    print(f"\nrun total: {total_tokens} tokens, {steps} steps")
    if run_b.get("max_total_tokens") is not None and total_tokens > run_b["max_total_tokens"]:
        overruns.append(f"run: total {total_tokens} > {run_b['max_total_tokens']} tokens")
    if run_b.get("max_steps") is not None and steps > run_b["max_steps"]:
        overruns.append(f"run: {steps} > {run_b['max_steps']} steps")

    if overruns:
        print(f"\n{len(overruns)} overrun(s)/gap(s):", file=sys.stderr)
        for o in overruns:
            print(f"  ✗ {o}", file=sys.stderr)
        return 1
    print("✅ within budget")
    return 0


if __name__ == "__main__":
    sys.exit(main())
