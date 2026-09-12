#!/usr/bin/env python3
"""
Render a multi-agent trace as a human-readable timeline.

Requires Python 3.8+. No third-party dependencies.

Usage:
  python scripts/trace_view.py <trace_id>
  python scripts/trace_view.py --latest
  python scripts/trace_view.py --list
  python scripts/trace_view.py [options]

Reads JSONL files from .context/traces/ by default. Override with:
  --traces-dir <path>
  TRACES_DIR=<path> python scripts/trace_view.py ...

Event schema: references/event-schema.md
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import sys
from pathlib import Path

DEFAULT_TRACES_SUBPATH = ".context/traces"

STATUS_ICON = {
    "started": "▶",
    "ok": "✓",
    "complete": "✓",
    "error": "✗",
    "skipped": "⊘",
}

KIND_LABEL = {
    "trace_start":   "TRACE START  ",
    "trace_end":     "TRACE END    ",
    "step_start":    "STEP START   ",
    "step_complete": "STEP DONE    ",
    "tool_call":     "TOOL CALL    ",
    "tool_result":   "TOOL RESULT  ",
    "error":         "ERROR        ",
}


# ---------------------------------------------------------------------------
# Directory resolution
# ---------------------------------------------------------------------------

def find_traces_dir(override: str | None = None) -> Path:
    """Locate the traces directory, searching upward from cwd if needed."""
    if override:
        p = Path(override).expanduser()
        if not p.exists():
            sys.exit(f"error: traces directory not found: {p}")
        return p

    env = os.environ.get("TRACES_DIR")
    if env:
        p = Path(env).expanduser()
        if p.exists():
            return p

    # Walk upward from cwd looking for .context/traces/
    for parent in [Path.cwd()] + list(Path.cwd().parents):
        candidate = parent / ".context" / "traces"
        if candidate.is_dir():
            return candidate

    # Fall back to cwd-relative default (may not exist yet — callers handle this)
    return Path(DEFAULT_TRACES_SUBPATH)


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------

def load_trace(traces_dir: Path, trace_id: str) -> tuple[list[dict] | None, Path]:
    """Return (events, path). events is None if the file does not exist."""
    path = traces_dir / f"{trace_id}.jsonl"
    if not path.exists():
        return None, path

    events: list[dict] = []
    with open(path, encoding="utf-8") as fh:
        for lineno, raw in enumerate(fh, 1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                events.append(json.loads(raw))
            except json.JSONDecodeError as exc:
                print(f"  [warn] line {lineno} malformed JSON: {exc}", file=sys.stderr)
    return events, path


def latest_trace_id(traces_dir: Path) -> str | None:
    """Return the stem of the most recently modified .jsonl file."""
    if not traces_dir.is_dir():
        return None
    files = sorted(traces_dir.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0].stem if files else None


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_list(traces_dir: Path) -> int:
    if not traces_dir.is_dir():
        print(f"No traces directory found at {traces_dir}")
        return 1

    files = sorted(traces_dir.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        print(f"No traces in {traces_dir}")
        return 0

    print(f"Traces in {traces_dir}/\n")
    header = f"  {'TRACE ID':<42}  {'EVENTS':>6}  {'SIZE':>8}  MODIFIED"
    print(header)
    print("  " + "-" * (len(header) - 2))
    for f in files:
        stat = f.stat()
        with open(f, encoding="utf-8") as fh:
            lines = sum(1 for ln in fh if ln.strip())
        mtime = datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        size = f"{stat.st_size:,}"
        print(f"  {f.stem:<42}  {lines:>6}  {size:>8}  {mtime}")
    return 0


def cmd_render(trace_id: str, traces_dir: Path, verbose: bool = False) -> int:
    events, path = load_trace(traces_dir, trace_id)

    if events is None:
        print(f"Trace not found: {path}")
        print("Run with --list to see available traces.")
        return 1

    if not events:
        print(f"Trace {trace_id} exists but contains no events.")
        return 1

    # --- Header ---
    start_event = next((e for e in events if e.get("kind") == "trace_start"), {})
    goal = (start_event.get("meta") or {}).get("goal", "")
    print(f"\n🧵  trace  {trace_id}")
    if goal:
        print(f'    goal  "{goal}"')
    print()

    # --- Timeline ---
    agents_seen: set[str] = set()
    tools_seen: set[str] = set()
    total_in = total_out = step_count = 0
    errors: list[dict] = []

    for e in events:
        kind    = e.get("kind", "unknown")
        ts_raw  = e.get("ts", "")
        agent   = e.get("agent") or "?"
        tool    = e.get("tool") or ""
        status  = e.get("status") or ""
        in_t    = int(e.get("input_tokens") or 0)
        out_t   = int(e.get("output_tokens") or 0)
        span    = e.get("span") or ""
        parent  = e.get("parent") or ""
        error   = e.get("error")

        agents_seen.add(agent)
        if tool:
            tools_seen.add(tool)
        total_in  += in_t
        total_out += out_t
        if kind == "error" or error:
            errors.append(e)
        if kind not in ("trace_start",):
            step_count += 1

        ts_display = ts_raw[11:19] if len(ts_raw) >= 19 else ts_raw
        icon  = STATUS_ICON.get(status, "·")
        label = KIND_LABEL.get(kind, f"{kind:<13}")

        parts = [f"  {ts_display}  {icon}  {label}  {agent:<16}"]
        if tool:
            parts.append(f"tool:{tool:<18}")
        if in_t or out_t:
            parts.append(f"[{in_t}→{out_t}]")
        if error:
            parts.append(f"!! {error}")
        if verbose and span:
            parent_str = f" parent={parent}" if parent else ""
            parts.append(f"({span}{parent_str})")

        print("  ".join(parts))

    # --- Summary ---
    print()
    print(f"  ── {step_count} steps  ·  {len(agents_seen)} agents  "
          f"·  {total_in:,}↑ {total_out:,}↓ tokens  "
          f"·  {len(errors)} error{'s' if len(errors) != 1 else ''}")

    if tools_seen:
        print(f"     tools used: {', '.join(sorted(tools_seen))}")

    if errors:
        print()
        print("  Errors:")
        for e in errors:
            ts_display = (e.get("ts") or "")[11:19]
            print(f"    [{ts_display}] {e.get('agent', '?')}: {e.get('error', '(no message)')}")

    print()
    return 0


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        prog="trace_view.py",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "trace_id",
        nargs="?",
        help="Trace ID to render (filename without .jsonl). "
             "Omit to use --latest.",
    )
    parser.add_argument(
        "--latest",
        action="store_true",
        help="Render the most recently modified trace.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all available traces with event counts and sizes.",
    )
    parser.add_argument(
        "--traces-dir",
        metavar="DIR",
        help=f"Path to traces directory (default: {DEFAULT_TRACES_SUBPATH}, "
             "searched upward from cwd). Also settable via TRACES_DIR env var.",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show span IDs and parent relationships in the timeline.",
    )
    args = parser.parse_args()

    traces_dir = find_traces_dir(args.traces_dir)

    if args.list:
        return cmd_list(traces_dir)

    if args.latest or not args.trace_id:
        trace_id = latest_trace_id(traces_dir)
        if not trace_id:
            print(f"No traces found in {traces_dir}")
            return 1
        return cmd_render(trace_id, traces_dir, verbose=args.verbose)

    return cmd_render(args.trace_id, traces_dir, verbose=args.verbose)


if __name__ == "__main__":
    sys.exit(main())
