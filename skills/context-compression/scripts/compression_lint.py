#!/usr/bin/env python3
"""Lint a context-compaction config against the rules that keep it from
silently destroying a run.

Modern agent runtimes compact context for you — it is a config surface, not
code you write. The catch is that the *summary* model (the one that rewrites
old turns into a shorter form) has its own context window, and a handful of
settings decide whether compaction helps or quietly eats the conversation.

Checks:

  1. WINDOW (the hard rule): the compaction model's context window MUST be
     >= the main model's. If it is smaller, the very context that overflowed
     the main model cannot even be read by the summarizer — you get API errors
     and lost context, not a shorter history. This is why a tiny local model is
     the wrong summarizer for a large-window main model.

  2. MODEL DECLARED: a compaction model is named and resolvable in the model
     catalog, so its window is a known fact, not an assumption.

  3. PROTECT RECENT: protect_last_n is a positive integer — the freshest turns
     (the ones the agent is actively reasoning over) are never compacted.

  4. RATIOS: 0 < target_ratio < threshold < 1 — compaction triggers before the
     window is full and compresses to meaningfully less than the trigger, or it
     thrashes (compact, immediately over threshold again, compact...).

  5. ENABLED: compaction is on; a long multi-agent run with it off overflows
     the main window and drops context with no warning.

Config shape (config.json):
  {"enabled": true, "main_model": "big-cloud",
   "compaction": {"model": "flash", "threshold": 0.5,
                  "target_ratio": 0.2, "protect_last_n": 20}}
Catalog shape (models.json): {"big-cloud": {"context_window": 400000}, ...}

Exit codes: 0 = config is safe, 1 = violations, 2 = bad input. Stdlib only.
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


def window_of(catalog: dict, name: str) -> "int | None":
    entry = catalog.get(name)
    if isinstance(entry, dict):
        w = entry.get("context_window")
        return w if isinstance(w, int) and w > 0 else None
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--config", required=True, help="compaction config JSON")
    ap.add_argument("--models", required=True, help="model catalog JSON (name -> context_window)")
    args = ap.parse_args()

    cfg = load(args.config, "config")
    catalog = load(args.models, "models")

    comp = cfg.get("compaction")
    if not isinstance(comp, dict):
        die("config has no 'compaction' object")

    violations: list[str] = []

    # 5. enabled
    enabled = cfg.get("enabled")
    if enabled is not True:
        violations.append(
            "compaction is not enabled — a long run will overflow the main "
            "model window and drop context silently; set enabled:true (or move "
            "the run to a model whose window fits the whole task)")

    # 2 + 1. models resolvable, then the window rule
    main_name = cfg.get("main_model")
    comp_name = comp.get("model")
    main_w = window_of(catalog, main_name) if isinstance(main_name, str) else None
    comp_w = window_of(catalog, comp_name) if isinstance(comp_name, str) else None

    if not isinstance(main_name, str) or not main_name:
        violations.append("main_model is not named")
    elif main_w is None:
        violations.append(
            f"main_model {main_name!r} not in the catalog (or no context_window) "
            f"— cannot verify the window rule")
    if not isinstance(comp_name, str) or not comp_name:
        violations.append(
            "compaction.model is not named — the runtime will fall back to a "
            "default summarizer you didn't choose")
    elif comp_w is None:
        violations.append(
            f"compaction.model {comp_name!r} not in the catalog (or no "
            f"context_window) — cannot verify the window rule")

    if main_w is not None and comp_w is not None and comp_w < main_w:
        violations.append(
            f"compaction model window {comp_w} < main model window {main_w} — "
            f"the summarizer cannot read the context that overflowed the main "
            f"model; this errors and loses context. Pick a summarizer whose "
            f"window is >= the main model's ({main_w}).")

    # 3. protect recent turns
    pln = comp.get("protect_last_n")
    if not (isinstance(pln, int) and not isinstance(pln, bool) and pln > 0):
        violations.append(
            "protect_last_n must be a positive integer — the freshest turns "
            "must never be compacted out from under the agent")

    # 4. ratios
    thr = comp.get("threshold")
    tgt = comp.get("target_ratio")
    nums_ok = all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in (thr, tgt))
    if not nums_ok:
        violations.append("threshold and target_ratio must be numbers in (0,1)")
    else:
        if not 0 < thr < 1:
            violations.append(f"threshold {thr} must be in (0,1)")
        if not 0 < tgt < 1:
            violations.append(f"target_ratio {tgt} must be in (0,1)")
        if 0 < thr < 1 and 0 < tgt < 1 and not tgt < thr:
            violations.append(
                f"target_ratio {tgt} is not below threshold {thr} — compaction "
                f"would compress to at/above its own trigger and thrash")

    print(f"Linted compaction config for main_model={main_name!r}, "
          f"summarizer={comp_name!r}.")
    if violations:
        print(f"\n{len(violations)} violation(s):", file=sys.stderr)
        for v in violations:
            print(f"  ✗ {v}", file=sys.stderr)
        return 1
    print("✅ Compaction config is safe: summarizer window >= main, recent turns "
          "protected, ratios sane.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
