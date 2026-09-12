#!/usr/bin/env python3
"""Check that prompts are versioned artifacts, not files edited in place.

A prompt is production behavior. Change it silently and you've shipped a
behavior change with no version, no changelog, and no way back — and when a
run regresses, nothing tells you the prompt moved. This check treats prompts
like any other release artifact: each is pinned by a content hash, every
version carries a changelog, and there's a valid rollback target.

Checks per prompt:

  1. PINNED     — the on-disk prompt's content hash equals the hash recorded for
     its active version. A mismatch means the file was edited without a version
     bump: the headline drift this skill prevents.
  2. ACTIVE     — the active version actually exists in the version history.
  3. CHANGELOG  — every version records a non-empty changelog line, so the
     history says *what changed and why*, not just *that* it changed.
  4. ROLLBACK   — the declared rollback_to target is a known prior version, so a
     bad deploy can be reverted to something that exists.

Manifest (prompts.json):
  {"prompts": {
     "planner": {"active": "v3", "file": "planner.txt", "rollback_to": "v2",
                 "versions": {"v1": {"hash": "...", "changelog": "initial"},
                              "v2": {"hash": "...", "changelog": "edge case"},
                              "v3": {"hash": "<sha256 of planner.txt>",
                                     "changelog": "tighten constraints"}}}}}

Hashes are sha256 of the prompt file's bytes, hex. Paths resolve relative to the
manifest's directory. Exit codes: 0 = versioning holds, 1 = violations, 2 = bad
input. Stdlib only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


def die(msg: str) -> "NoReturn":
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(2)


def sha256_file(path: Path) -> "str | None":
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--manifest", required=True, help="prompt version manifest JSON")
    args = ap.parse_args()

    mpath = Path(args.manifest)
    try:
        doc = json.loads(mpath.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        die(f"cannot read manifest {args.manifest}: {exc}")
    prompts = doc.get("prompts") if isinstance(doc, dict) else None
    if not isinstance(prompts, dict) or not prompts:
        die("manifest has no non-empty 'prompts' object")
    base = mpath.resolve().parent

    violations: list[str] = []

    for name, p in sorted(prompts.items()):
        if not isinstance(p, dict):
            violations.append(f"{name}: entry is not an object")
            continue
        versions = p.get("versions")
        if not isinstance(versions, dict) or not versions:
            violations.append(f"{name}: no 'versions' history")
            continue
        active = p.get("active")

        # 2. active resolvable
        if active not in versions:
            violations.append(
                f"{name}: active version {active!r} is not in the version "
                f"history {sorted(versions)}")
        else:
            # 1. pin holds
            rec = versions[active].get("hash") if isinstance(versions[active], dict) else None
            fname = p.get("file")
            if not isinstance(fname, str) or not fname:
                violations.append(f"{name}: no 'file' to hash")
            else:
                actual = sha256_file(base / fname)
                if actual is None:
                    violations.append(f"{name}: prompt file {fname!r} not readable")
                elif rec != actual:
                    violations.append(
                        f"{name}: file {fname!r} hash {actual[:12]}… != recorded "
                        f"{str(rec)[:12]}… for active {active!r} — the prompt was "
                        f"edited without a version bump")

        # 3. changelog on every version
        for ver, meta in sorted(versions.items()):
            cl = meta.get("changelog") if isinstance(meta, dict) else None
            if not (isinstance(cl, str) and cl.strip()):
                violations.append(f"{name}:{ver}: empty changelog — record what changed and why")

        # 4. rollback target exists
        rb = p.get("rollback_to")
        if rb is not None and rb not in versions:
            violations.append(
                f"{name}: rollback_to {rb!r} is not a known version — a revert "
                f"would point at nothing")

    print(f"Checked {len(prompts)} prompt(s).")
    if violations:
        print(f"\n{len(violations)} violation(s):", file=sys.stderr)
        for v in violations:
            print(f"  ✗ {v}", file=sys.stderr)
        return 1
    print("✅ Prompt versioning holds: pins match, active resolves, every version "
          "has a changelog, rollback targets exist.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
