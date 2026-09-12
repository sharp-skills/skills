#!/usr/bin/env python3
"""Build a tool-call-validator schema (tools.json) from a real MCP tool list.

The validator checks proposed calls against an allowlist of tools and their
required arguments. Hand-writing that allowlist is the weak link: miss a tool
and legitimate calls are blocked; get a required-arg wrong and the check is
theater. But you don't have to write it — an MCP server already publishes the
list (`tools/list`), with each tool's input schema. This extractor turns that
real, authoritative list into the validator's schema, so the allowlist comes
from the server, not from your memory of it.

What it maps:
  * tool name                       -> allowlist key
  * inputSchema.required            -> required args
It deliberately does NOT guess `destructive`. Destructiveness is a policy
decision (a `bash` tool is only destructive on `rm -rf`, not by name), so the
extractor emits a `_needs_review` list of side-effecting-sounding tools for a
human to annotate — it never marks one destructive on its own. Guessing here is
the exact failure the validator exists to prevent.

  python3 extract_tools.py mcp-tools.json                 # -> tools.json on stdout
  python3 extract_tools.py mcp-tools.json --out tools.json

Accepts either a raw `tools/list` result (`{"tools": [...]}`) or a full JSON-RPC
envelope (`{"result": {"tools": [...]}}`).

Exit codes: 0 = schema written, 2 = bad input. Stdlib only, offline.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# A general executor is destructive by its ARGUMENT, not its name (`bash` running
# `rm -rf`), so it needs destructive_patterns, not a destructive flag — the exact
# case the validator's flagship example catches. Kept a separate bucket so the
# hint for the most dangerous tool class is specific, not silent.
GENERAL_EXECUTOR = re.compile(r"^(bash|sh|shell|zsh|cmd|powershell|pwsh|exec|eval|run_?command|system)$", re.I)

# Other name substrings that *suggest* a side effect — flagged for review, never auto-marked.
SIDE_EFFECT_HINT = re.compile(
    r"write|delete|remove|drop|truncate|exec|run|post|put|patch|create|update|"
    r"send|deploy|push|kill|reset|format", re.I)


def die(msg: str) -> "NoReturn":
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(2)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("mcp", help="MCP tools/list JSON (raw result or JSON-RPC envelope)")
    ap.add_argument("--out", help="write the schema here (default: stdout)")
    args = ap.parse_args()

    path = Path(args.mcp)
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        die(f"cannot read MCP tool list {path}: {exc}")
    if isinstance(doc, dict) and "result" in doc and isinstance(doc["result"], dict):
        doc = doc["result"]
    tools = doc.get("tools") if isinstance(doc, dict) else None
    if not isinstance(tools, list) or not tools:
        die("no non-empty 'tools' list found (expected tools/list output)")

    schema: dict[str, dict] = {}
    executors: list[str] = []
    side_effecting: list[str] = []
    for t in tools:
        if not isinstance(t, dict) or not t.get("name"):
            die("every tool needs a 'name'")
        name = str(t["name"])
        inp = t.get("inputSchema") or t.get("input_schema") or {}
        required = inp.get("required") if isinstance(inp, dict) else None
        entry: dict = {"required": list(required) if isinstance(required, list) else []}
        schema[name] = entry
        if GENERAL_EXECUTOR.match(name):
            executors.append(name)          # dangerous by argument -> destructive_patterns
        elif SIDE_EFFECT_HINT.search(name):
            side_effecting.append(name)      # dangerous by identity -> destructive: true

    out: dict = {"tools": schema}
    review: dict = {}
    if executors:
        review["general_executors"] = {
            "note": ("these run arbitrary commands — destructive by ARGUMENT, not "
                     "name (e.g. bash running 'rm -rf'). Add 'destructive_patterns' "
                     "to each; the validator matches them on the argument value."),
            "tools": sorted(executors),
        }
    if side_effecting:
        review["side_effecting"] = {
            "note": ("these tool names suggest a side effect; a human must mark "
                     "each 'destructive': true — the extractor never guesses."),
            "tools": sorted(side_effecting),
        }
    if review:
        out["_needs_review"] = review

    text = json.dumps(out, indent=2) + "\n"
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        flagged = len(executors) + len(side_effecting)
        print(f"wrote {len(schema)} tool(s) -> {args.out}"
              + (f"; {flagged} flagged for destructive-review "
                 f"({len(executors)} executor, {len(side_effecting)} side-effecting)" if flagged else ""),
              file=sys.stderr)
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
