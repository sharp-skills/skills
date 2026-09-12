#!/usr/bin/env python3
"""
pin_check — prove a multi-agent system's model choices are pinned and testable.

"Changing anything changes everything." A model identifier that can resolve to
different weights tomorrow is an undeclared dependency: the system's behaviour
changes with no commit, no review, and no way to bisect. This checker reads a
model manifest — one entry per place a model is chosen — and refuses the four
shapes that make a version change undetectable.

The pin test is deliberately vendor-neutral: a pin holds when **the identifier
you request is the artifact you received**. If `model` and `resolved` differ,
you asked for an alias and the provider picked; that is floating by definition,
whatever the naming scheme.

Usage:
  pin_check.py --manifest models.json [--strict] [--quiet]

Exit codes:
  0  every component is pinned and comparable
  1  at least one violation
  2  usage / unreadable / malformed input (fail loud, never silently pass)

stdlib only, offline. It inspects the declaration, not the provider, so it works
for any vendor and runs in CI without credentials or network.
"""

import argparse
import json
import sys

# Substrings that mark an identifier as resolving at call time rather than at
# pin time. Vendor-neutral: every provider spells "newest" somehow.
FLOATING_MARKERS = ("latest", "newest", "stable", "*", "^", "~", ">=", "<=", "@dev")

# Upgrade policies that keep a human or a shadow run between a new release and
# production. Anything else means a release reaches users unmeasured.
SAFE_UPGRADE = {"shadow", "manual"}

# Comparison methods. Score-only comparison is the documented trap: deltas stay
# flat while behaviour shifts enough that users notice.
TRAJECTORY_COMPARE = {"trajectory", "trajectory+score"}

REQUIRED = ("id", "model", "resolved")


def floating_marker(identifier):
    """Return the floating marker found in an identifier, or None."""
    low = identifier.lower()
    for marker in FLOATING_MARKERS:
        if marker in low:
            return marker
    return None


def check_component(comp, index, strict):
    """Yield human-readable violations for one manifest entry."""
    where = comp.get("id") or f"component[{index}]"

    model = comp.get("model", "")
    resolved = comp.get("resolved", "")

    # 1. Pinned — the name you request is the artifact you got.
    marker = floating_marker(model)
    if marker:
        yield (
            f"{where}: model '{model}' contains the floating marker '{marker}' — it "
            f"resolves at call time, so the weights can change with no commit"
        )
    elif model != resolved:
        yield (
            f"{where}: model '{model}' resolved to '{resolved}' — you named an alias "
            f"and the provider chose; pin the resolved identifier instead"
        )

    # 2. A frozen probe set — without one there is nothing to compare against.
    probes = comp.get("probe_set")
    if not probes:
        yield (
            f"{where}: no probe_set — a version change cannot be detected without a "
            f"frozen set of inputs to replay against both versions"
        )

    # 3. Upgrade policy — a release must not reach users unmeasured.
    upgrade = comp.get("upgrade")
    if upgrade not in SAFE_UPGRADE:
        got = upgrade if upgrade else "not declared"
        yield (
            f"{where}: upgrade policy is {got} — must be 'shadow' (run the new version "
            f"beside the old on the probe set) or 'manual'; anything else ships an "
            f"unmeasured model to users"
        )

    # 4. The runtime is part of the pin. Swapping a model can force a toolchain
    #    upgrade — an older CLI/SDK can reject a newer model outright.
    if "runtime" not in comp:
        yield (
            f"{where}: runtime not declared — write the client/CLI/SDK version that was "
            f"verified with this model, or an explicit null if there genuinely is none. "
            f"A model swap can be blocked by a toolchain that predates it"
        )

    # 5. (--strict) How versions get compared.
    if strict:
        compare = comp.get("compare")
        if compare not in TRAJECTORY_COMPARE:
            got = compare if compare else "not declared"
            yield (
                f"{where}: compare is {got} — score-only comparison misses behaviour "
                f"change; declare 'trajectory' and diff what the agent actually did"
            )


def load(path):
    """Read the manifest, or exit 2. Malformed input must never pass quietly."""
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError:
        sys.stderr.write(f"pin_check: no such manifest: {path}\n")
        raise SystemExit(2)
    except json.JSONDecodeError as exc:
        sys.stderr.write(f"pin_check: {path} is not valid JSON: {exc}\n")
        raise SystemExit(2)

    components = data.get("components") if isinstance(data, dict) else None
    if not isinstance(components, list) or not components:
        sys.stderr.write(
            f"pin_check: {path} has no non-empty 'components' list — an empty manifest "
            f"would pass every check while pinning nothing\n"
        )
        raise SystemExit(2)
    return components


def main():
    parser = argparse.ArgumentParser(
        description="Check that every model choice is pinned, probed, and comparable."
    )
    parser.add_argument("--manifest", required=True, help="path to the model manifest JSON")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="also require an explicit trajectory-based comparison method",
    )
    parser.add_argument("--quiet", action="store_true", help="print the summary line only")
    args = parser.parse_args()

    components = load(args.manifest)

    violations = []
    seen = set()

    for index, comp in enumerate(components):
        if not isinstance(comp, dict):
            sys.stderr.write(f"pin_check: components[{index}] is not an object\n")
            raise SystemExit(2)

        missing = [field for field in REQUIRED if field not in comp]
        if missing:
            sys.stderr.write(
                f"pin_check: components[{index}] missing required field(s): "
                f"{', '.join(missing)}\n"
            )
            raise SystemExit(2)

        ident = comp["id"]
        if ident in seen:
            sys.stderr.write(f"pin_check: duplicate component id '{ident}'\n")
            raise SystemExit(2)
        seen.add(ident)

        violations.extend(check_component(comp, index, args.strict))

    if violations and not args.quiet:
        for violation in violations:
            print(f"  ✗ {violation}")

    count = len(violations)
    if count:
        print(f"pin_check: {count} violation{'s' if count != 1 else ''} "
              f"across {len(components)} component(s)")
        return 1

    print(f"pin_check: {len(components)} component(s) pinned, probed and comparable")
    return 0


if __name__ == "__main__":
    sys.exit(main())
