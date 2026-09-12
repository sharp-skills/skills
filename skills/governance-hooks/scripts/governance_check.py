#!/usr/bin/env python3
"""Harness-enforced governance checks for multi-agent systems.

Three checks over one JSON config (zones.json):

  no-touch        block writes/edits to protected globs
  secret-read /   block reads of secret-shaped paths and shell commands
  secret-cmd      that would dump them
  drift-snapshot/ detect governed config changing vs a reviewed snapshot
  drift-check

Plus `hook`: a ready pre-tool-use adapter that reads a tool-call JSON
({"tool_name": ..., "tool_input": {...}}) from stdin and applies the checks.

Exit convention (hook-native, deliberate — see SKILL.md design decision 1):
  0 = allow (including fail-open on internal error)
  2 = block, with an explanation for the model on stderr

Stdlib only. Rules are data: edit zones.json, not this file.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import re
import sys
from pathlib import Path

DEFAULT_CONFIG = {
    "override_env": "GOVERNANCE_OVERRIDE",
    "no_touch": [
        {"path": "config/registry.json", "reason": "single source of truth"},
        {"path": ".env*", "reason": "secrets"},
    ],
    "secret_globs": [
        ".env", ".env.*", "*.pem", "*.key", "*credentials*", "*secret*",
        "*apikey*", "*token*", "*.kdbx", "id_rsa*", "*.p12",
    ],
    "secret_cmd_patterns": [
        r"\bcat\b[^|;&]*\.env\b", r"\bcat\b[^|;&]*(secret|credential|apikey|token)",
        r"\benv\b\s*($|\|)", r"printenv", r"\bcat\b[^|;&]*id_rsa",
    ],
    "drift_files": [],
    "write_tools": ["Edit", "Write", "MultiEdit", "NotebookEdit"],
    "read_tools": ["Read"],
    "shell_tools": ["Bash"],
}


def load_config(path: str | None) -> dict:
    cfg = dict(DEFAULT_CONFIG)
    if path:
        try:
            user = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"ERROR: cannot read config {path}: {exc}", file=sys.stderr)
            sys.exit(2)
        if not isinstance(user, dict):
            print(f"ERROR: config must be a JSON object: {path}", file=sys.stderr)
            sys.exit(2)
        cfg.update(user)
    return cfg


def override_active(cfg: dict) -> bool:
    return os.environ.get(str(cfg.get("override_env", "GOVERNANCE_OVERRIDE"))) == "1"


def norm(path: str, root: Path) -> str:
    """Repo-relative, forward-slash form of a path for glob matching."""
    p = Path(path)
    try:
        p = p.resolve()
        p = p.relative_to(root.resolve())
    except (ValueError, OSError):
        pass
    return str(p).replace(os.sep, "/")


def match_zone(rel: str, zones: list) -> dict | None:
    base = rel.rsplit("/", 1)[-1]
    for zone in zones:
        pattern = str(zone.get("path", ""))
        if not pattern:
            continue
        if fnmatch.fnmatch(rel, pattern) or fnmatch.fnmatch(base, pattern) \
                or fnmatch.fnmatch(rel, pattern.rstrip("/") + "/*"):
            return zone
    return None


def check_no_touch(path: str, cfg: dict, root: Path) -> str | None:
    zone = match_zone(norm(path, root), cfg.get("no_touch") or [])
    if zone:
        reason = zone.get("reason", "protected")
        return (f"BLOCKED no-touch zone: '{zone['path']}' ({reason}). "
                f"Do not modify it directly — request a review/change through "
                f"the owner instead of retrying.")
    return None


def check_secret_read(path: str, cfg: dict, root: Path) -> str | None:
    rel = norm(path, root)
    base = rel.rsplit("/", 1)[-1].lower()
    for pattern in cfg.get("secret_globs") or []:
        if fnmatch.fnmatch(rel.lower(), str(pattern).lower()) or \
                fnmatch.fnmatch(base, str(pattern).lower()):
            return (f"BLOCKED secret read: '{rel}' matches '{pattern}'. "
                    f"Secrets must not enter the conversation/log. If you need "
                    f"a config key's NAME, grep for the key name instead of "
                    f"reading the file.")
    return None


def check_secret_cmd(cmd: str, cfg: dict) -> str | None:
    for pattern in cfg.get("secret_cmd_patterns") or []:
        try:
            if re.search(pattern, cmd):
                return (f"BLOCKED secret-exposing command (matches /{pattern}/). "
                        f"Command output would put secret values into the log.")
        except re.error:
            continue  # bad user pattern must not wedge the hook
    return None


def file_digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def drift_snapshot(cfg: dict, root: Path, lock_path: str) -> int:
    files = cfg.get("drift_files") or []
    if not files:
        print("ERROR: config has no drift_files to snapshot", file=sys.stderr)
        return 2
    lock: dict = {}
    for pattern in files:
        for p in sorted(root.glob(pattern)):
            if p.is_file():
                lock[norm(str(p), root)] = file_digest(p)
    if not lock:
        print("ERROR: drift_files matched nothing — refusing an empty snapshot "
              "(a guard over nothing is fail-open)", file=sys.stderr)
        return 2
    Path(lock_path).write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n",
                               encoding="utf-8")
    print(f"snapshot: {len(lock)} governed file(s) -> {lock_path}")
    return 0


def drift_check(cfg: dict, root: Path, lock_path: str) -> int:
    try:
        lock = json.loads(Path(lock_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot read lock {lock_path}: {exc}", file=sys.stderr)
        return 2
    drifted: list[str] = []
    for rel, digest in sorted(lock.items()):
        p = root / rel
        if not p.exists():
            drifted.append(f"{rel} (deleted)")
        elif file_digest(p) != digest:
            drifted.append(f"{rel} (modified)")
    if drifted:
        print("DRIFT in governed config (review or re-snapshot deliberately):",
              file=sys.stderr)
        for item in drifted:
            print(f"  ✗ {item}", file=sys.stderr)
        return 2
    print(f"no drift: {len(lock)} governed file(s) match the snapshot")
    return 0


def run_hook(cfg: dict, root: Path) -> int:
    """Pre-tool-use adapter: tool-call JSON on stdin -> allow/block."""
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0  # fail-open: unparseable hook input must not wedge the session
    if override_active(cfg):
        return 0
    try:
        tool = data.get("tool_name", "")
        ti = data.get("tool_input") or {}
        target = ti.get("file_path") or ti.get("notebook_path") or ""
        msgs: list[str] = []
        if tool in set(cfg.get("write_tools") or []) and target:
            for check in (check_no_touch, check_secret_read):
                m = check(target, cfg, root)
                if m:
                    msgs.append(m)
        elif tool in set(cfg.get("read_tools") or []) and target:
            m = check_secret_read(target, cfg, root)
            if m:
                msgs.append(m)
        elif tool in set(cfg.get("shell_tools") or []):
            m = check_secret_cmd(str(ti.get("command", "")), cfg)
            if m:
                msgs.append(m)
        if msgs:
            print("\n".join(msgs), file=sys.stderr)
            return 2
        return 0
    except Exception:
        return 0  # fail-open by design; see SKILL.md


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("command", choices=["no-touch", "secret-read", "secret-cmd",
                                        "drift-snapshot", "drift-check", "hook"])
    ap.add_argument("target", nargs="?", help="path (no-touch/secret-read) or command string (secret-cmd)")
    ap.add_argument("--config", help="zones.json (defaults are illustrative only)")
    ap.add_argument("--root", default=".", help="repo root for relative matching")
    ap.add_argument("--lock", default="governance.lock.json", help="drift lock file")
    args = ap.parse_args()

    cfg = load_config(args.config)
    root = Path(args.root)

    if args.command == "hook":
        return run_hook(cfg, root)
    if args.command == "drift-snapshot":
        return drift_snapshot(cfg, root, args.lock)
    if args.command == "drift-check":
        return drift_check(cfg, root, args.lock)

    if not args.target:
        print("ERROR: this command needs a target argument", file=sys.stderr)
        return 2
    if override_active(cfg):
        print("override active: allowed")
        return 0
    if args.command == "no-touch":
        msg = check_no_touch(args.target, cfg, root)
    elif args.command == "secret-read":
        msg = check_secret_read(args.target, cfg, root)
    else:
        msg = check_secret_cmd(args.target, cfg)
    if msg:
        print(msg, file=sys.stderr)
        return 2
    print("allowed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
