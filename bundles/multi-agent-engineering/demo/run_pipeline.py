#!/usr/bin/env python3
"""End-to-end demo: run a tiny multi-agent pipeline that COMPOSES bundle skills.

One run, four skills wired over one shared registry and one trace:
  * registry-ssot        — routing is DERIVED from the registry's bus graph here,
                           never a second hardcoded map.
  * status-gates         — every emitted status is checked at the routing boundary
                           by the real `status_gate.py` before it is allowed to route.
  * observability-tracing— every step is appended to a JSONL trace in the canonical
                           schema, so the shipped trace_view / eval / budget tools read it.
  * (downstream, see demo.sh) eval-harness scores the trace, cost-budgeting checks it.

Scripted agent outputs keep the demo deterministic and offline; a real pipeline
gets these from models. Stdlib only.

  python3 run_pipeline.py --registry registry.json --out .context/traces --trace-id demo-e2e-001
  python3 run_pipeline.py ... --inject-bad-status   # engineer emits an unroutable status

Exit: 0 = pipeline reached the terminal event, 1 = it failed (e.g. gate rejection).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
# Skills are siblings of demo/ in the source repo, or under ../../../skills/
# when the bundle ships inside a library as bundles/<name>/.
BUNDLE = HERE.parent
if not (BUNDLE / "status-gates").is_dir() and (HERE.parents[2] / "skills" / "status-gates").is_dir():
    BUNDLE = HERE.parents[2] / "skills"
STATUS_GATE = BUNDLE / "status-gates" / "scripts" / "status_gate.py"

# What each agent produces when it runs (deterministic stand-in for a model call):
# the event it emits, a confidence, its token cost, its output fields, optional tool.
SCRIPT = {
    "analyst":  {"event": "ANALYSIS_COMPLETE", "confidence": 82, "in": 1840, "out": 620,
                 "fields": ["status", "summary", "confidence"]},
    "engineer": {"event": "BUILD_COMPLETE", "confidence": 77, "in": 3200, "out": 1450,
                 "fields": ["status", "artifacts", "confidence"],
                 "tool": {"name": "run_tests", "in": 120, "out": 40, "exit": 0}},
    "reviewer": {"event": "RUN_ARCHIVED", "confidence": 90, "in": 2100, "out": 380,
                 "fields": ["status", "verdict", "confidence"]},
}
T0 = datetime(2026, 7, 7, 10, 0, 0, tzinfo=timezone.utc)


def ts(sec: int) -> str:
    return (T0 + timedelta(seconds=sec)).strftime("%Y-%m-%dT%H:%M:%SZ")


def gate(registry: str, agent: str, status: str) -> tuple[bool, str]:
    """Call the REAL status-gates checker. Returns (routes?, message)."""
    r = subprocess.run(
        [sys.executable, str(STATUS_GATE), "--registry", registry,
         "--agent", agent, "--status", status],
        capture_output=True, text=True)
    return r.returncode == 0, (r.stdout + r.stderr).strip()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--registry", required=True)
    ap.add_argument("--out", required=True, help="traces directory")
    ap.add_argument("--trace-id", default="demo-e2e-001")
    ap.add_argument("--inject-bad-status", action="store_true",
                    help="make the engineer emit a plausible-but-unroutable status")
    args = ap.parse_args()

    reg = json.loads(Path(args.registry).read_text(encoding="utf-8"))
    bus = reg["bus_graph"]                       # <- routing DERIVED from the registry
    current = reg["entry_events"][0]
    terminals = set(reg.get("terminal_events", []))

    outdir = Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)
    trace_path = outdir / f"{args.trace_id}.jsonl"

    events: list[dict] = []
    tid = args.trace_id

    def rec(ev: dict) -> None:
        events.append(ev)

    rec({"trace_id": tid, "ts": ts(0), "kind": "trace_start", "span": "root", "step": 0,
         "agent": "orchestrator", "status": "started", "input_tokens": 0,
         "output_tokens": 0, "parent": None})

    sec, step, failed = 5, 1, False
    print(f"dispatch: entry event {current!r} (routing derived from registry.bus_graph)")

    while current not in terminals:
        subs = bus.get(current, [])
        if not subs:
            print(f"  ✗ no subscriber for {current!r} and it is not terminal — lost wiring",
                  file=sys.stderr)
            failed = True
            break
        agent = subs[0]
        spec = SCRIPT[agent]
        status = spec["event"]
        if args.inject_bad_status and agent == "engineer":
            status = "SUCCESS"                   # plausible, but not in engineer.publishes

        if spec.get("tool"):
            tl = spec["tool"]
            rec({"trace_id": tid, "ts": ts(sec), "kind": "tool_call", "span": f"s{step}t",
                 "step": step, "agent": agent, "tool": tl["name"], "status": "ok",
                 "input_tokens": tl["in"], "output_tokens": tl["out"],
                 "parent": f"s{step}", "meta": {"exit_code": tl["exit"]}})
            sec += 3

        # --- STATUS GATE: check the status at the routing boundary, before routing ---
        routes, msg = gate(args.registry, agent, status)
        print(f"  [{agent}] emits {status!r} -> gate: {'ROUTES' if routes else 'REJECTED'}")
        if not routes:
            print("    " + msg.replace("\n", "\n    "))
            rec({"trace_id": tid, "ts": ts(sec), "kind": "step_complete", "span": f"s{step}",
                 "step": step, "agent": agent, "tool": None, "status": "error",
                 "input_tokens": spec["in"], "output_tokens": spec["out"], "parent": "root",
                 "meta": {"event": "PIPELINE_FAILED", "confidence": spec["confidence"],
                          "schema_valid": False, "output_fields": spec["fields"],
                          "alert": "unroutable_status", "rejected_status": status}})
            failed = True
            break

        rec({"trace_id": tid, "ts": ts(sec), "kind": "step_complete", "span": f"s{step}",
             "step": step, "agent": agent, "tool": None, "status": "ok",
             "input_tokens": spec["in"], "output_tokens": spec["out"], "parent": "root",
             "meta": {"event": status, "confidence": spec["confidence"],
                      "schema_valid": True, "output_fields": spec["fields"]}})
        current = status                          # the emitted event routes to the next agent
        sec += 10
        step += 1

    rec({"trace_id": tid, "ts": ts(sec), "kind": "trace_end", "span": "root", "step": step,
         "agent": "orchestrator", "status": "error" if failed else "ok",
         "input_tokens": 0, "output_tokens": 0, "parent": None})

    trace_path.write_text("\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8")
    print(f"trace: wrote {len(events)} events -> {trace_path}"
          f"  ({'FAILED' if failed else 'reached ' + ', '.join(terminals)})")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
