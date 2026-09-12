#!/usr/bin/env python3
"""Evaluate observability-tracing JSONL runs with a deterministic structural rubric."""

from __future__ import annotations

import argparse
import json
import pathlib
import shlex
import statistics
import subprocess
import sys
from typing import Any

DEFAULT_REQUIRED_EVENT_FIELDS = {
    "trace_id": "str",
    "span": "str",
    "step": "int",
    "kind": "str",
    "ts": "str",
    "agent": "str",
    "status": "str",
    "input_tokens": "int",
    "output_tokens": "int",
    "parent": "any",
}

DEFAULT_RUBRIC: dict[str, Any] = {
    "min_score": 80,
    "scored_kinds": ["step_complete"],
    "required_event_fields": DEFAULT_REQUIRED_EVENT_FIELDS,
    "required_meta_fields": [],
    "required_output_fields": [],
    "output_fields_meta_key": "output_fields",
    "confidence": {"meta_key": "confidence", "threshold": 0.7, "required": False, "blocking": True},
    "schema": {"meta_key": "schema_valid", "required": False},
    "alerts": {"meta_keys": ["alerts", "flags"], "blocking_labels": ["error", "blocked", "policy_violation"]},
    "blocking_statuses": ["error"],
    "weights": {"shape": 40, "contract": 25, "confidence": 15, "schema": 10, "status_alerts": 10},
}

BLOCKING_PREFIXES = (
    "MISSING_REQUIRED_FIELD:",
    "INVALID_TYPE:",
    "MISSING_CONTRACT_FIELD:",
    "LOW_CONFIDENCE:",
    "SCHEMA_INVALID:",
    "EVENT_STATUS_ERROR:",
    "EVENT_ERROR_PRESENT:",
    "ALERT_PRESENT:",
    "NO_SCORABLE_EVENTS",
)


class EvalInputError(Exception):
    """Usage, input, parse, or config error."""


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_rubric(path: str | None) -> dict[str, Any]:
    rubric = DEFAULT_RUBRIC
    if not path:
        return dict(rubric)
    try:
        with open(path, "r", encoding="utf-8") as handle:
            custom = json.load(handle)
    except OSError as exc:
        raise EvalInputError(f"cannot read rubric: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise EvalInputError(f"invalid rubric JSON: {exc}") from exc
    if not isinstance(custom, dict):
        raise EvalInputError("rubric JSON must be an object")
    merged = deep_merge(rubric, custom)
    weights = merged.get("weights", {})
    if not isinstance(weights, dict):
        raise EvalInputError("rubric weights must be an object")
    try:
        weight_total = sum(float(value) for value in weights.values())
    except (TypeError, ValueError) as exc:
        raise EvalInputError("rubric weights must be numeric") from exc
    if round(weight_total, 6) != 100.0:
        raise EvalInputError(f"rubric weights must sum to 100, got {weight_total:g}")
    return merged


def find_latest_trace(traces_dir: pathlib.Path) -> pathlib.Path:
    if not traces_dir.exists():
        raise EvalInputError(f"traces dir not found: {traces_dir}")
    candidates = sorted(traces_dir.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        raise EvalInputError(f"no .jsonl traces found in {traces_dir}")
    return candidates[0]


def resolve_trace_path(trace_id: str | None, latest: bool, traces_dir: pathlib.Path) -> pathlib.Path:
    if latest:
        return find_latest_trace(traces_dir)
    if not trace_id:
        raise EvalInputError("provide trace_id or --latest")
    candidate = pathlib.Path(trace_id)
    if candidate.exists():
        return candidate
    name = trace_id if trace_id.endswith(".jsonl") else f"{trace_id}.jsonl"
    path = traces_dir / name
    if not path.exists():
        raise EvalInputError(f"trace not found: {path}")
    return path


def load_events(path: pathlib.Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    try:
        with open(path, "r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise EvalInputError(f"invalid JSON on line {line_number}: {exc}") from exc
                if not isinstance(event, dict):
                    raise EvalInputError(f"line {line_number} is not a JSON object")
                event["_line"] = line_number
                events.append(event)
    except OSError as exc:
        raise EvalInputError(f"cannot read trace: {exc}") from exc
    if not events:
        raise EvalInputError(f"trace is empty: {path}")
    return events


def type_ok(value: Any, type_name: str) -> bool:
    if type_name == "any":
        return True
    if type_name == "str":
        return isinstance(value, str)
    if type_name == "int":
        return isinstance(value, int) and not isinstance(value, bool)
    if type_name == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if type_name == "bool":
        return isinstance(value, bool)
    if type_name == "list":
        return isinstance(value, list)
    if type_name == "dict":
        return isinstance(value, dict)
    return True


def flag(flags: list[str], text: str) -> None:
    flags.append(text)


def get_meta(event: dict[str, Any]) -> dict[str, Any]:
    meta = event.get("meta")
    return meta if isinstance(meta, dict) else {}


def output_field_names(meta: dict[str, Any], key: str) -> set[str]:
    value = meta.get(key)
    if isinstance(value, dict):
        return {str(k) for k in value.keys()}
    if isinstance(value, list):
        return {str(v) for v in value}
    return set()


def score_event(event: dict[str, Any], event_index: int, rubric: dict[str, Any]) -> tuple[float, list[str]]:
    flags: list[str] = []
    weights = rubric.get("weights", DEFAULT_RUBRIC["weights"])
    score = 0.0

    required_fields = rubric.get("required_event_fields", DEFAULT_REQUIRED_EVENT_FIELDS)
    shape_checks = 0
    shape_passes = 0
    if isinstance(required_fields, dict):
        for field, type_name in required_fields.items():
            shape_checks += 1
            if field not in event:
                flag(flags, f"MISSING_REQUIRED_FIELD:{event_index}:{field}")
            elif not type_ok(event[field], str(type_name)):
                flag(flags, f"INVALID_TYPE:{event_index}:{field}")
            else:
                shape_passes += 1
    score += float(weights.get("shape", 40)) * (shape_passes / shape_checks if shape_checks else 1.0)

    meta = get_meta(event)
    contract_checks = 0
    contract_passes = 0
    for field in rubric.get("required_meta_fields", []) or []:
        contract_checks += 1
        if field in meta:
            contract_passes += 1
        else:
            flag(flags, f"MISSING_CONTRACT_FIELD:{event_index}:meta.{field}")

    output_key = str(rubric.get("output_fields_meta_key", "output_fields"))
    produced_fields = output_field_names(meta, output_key)
    for field in rubric.get("required_output_fields", []) or []:
        contract_checks += 1
        if str(field) in produced_fields:
            contract_passes += 1
        else:
            flag(flags, f"MISSING_CONTRACT_FIELD:{event_index}:{field}")
    contract_ratio = contract_passes / contract_checks if contract_checks else 1.0
    score += float(weights.get("contract", 25)) * contract_ratio

    conf_cfg = rubric.get("confidence", {}) if isinstance(rubric.get("confidence"), dict) else {}
    conf_key = str(conf_cfg.get("meta_key", "confidence"))
    conf_required = bool(conf_cfg.get("required", False))
    conf_threshold = float(conf_cfg.get("threshold", 0.7))
    conf_value = meta.get(conf_key)
    if conf_value is None:
        if conf_required:
            flag(flags, f"MISSING_CONTRACT_FIELD:{event_index}:meta.{conf_key}")
            conf_ratio = 0.0
        else:
            conf_ratio = 0.75
    elif isinstance(conf_value, (int, float)) and not isinstance(conf_value, bool):
        if float(conf_value) >= conf_threshold:
            conf_ratio = 1.0
        else:
            low_conf_flag = "LOW_CONFIDENCE" if bool(conf_cfg.get("blocking", True)) else "LOW_CONFIDENCE_INFO"
            flag(flags, f"{low_conf_flag}:{event_index}:{conf_value}")
            conf_ratio = max(0.0, float(conf_value) / conf_threshold) if conf_threshold else 0.0
    else:
        flag(flags, f"INVALID_TYPE:{event_index}:meta.{conf_key}")
        conf_ratio = 0.0
    score += float(weights.get("confidence", 15)) * conf_ratio

    schema_cfg = rubric.get("schema", {}) if isinstance(rubric.get("schema"), dict) else {}
    schema_key = str(schema_cfg.get("meta_key", "schema_valid"))
    schema_required = bool(schema_cfg.get("required", False))
    schema_value = meta.get(schema_key)
    if schema_value is True:
        schema_ratio = 1.0
    elif schema_value is False:
        flag(flags, f"SCHEMA_INVALID:{event_index}")
        schema_ratio = 0.0
    elif schema_required:
        flag(flags, f"MISSING_CONTRACT_FIELD:{event_index}:meta.{schema_key}")
        schema_ratio = 0.0
    else:
        schema_ratio = 0.75
    score += float(weights.get("schema", 10)) * schema_ratio

    status_ratio = 1.0
    status = event.get("status")
    blocking_statuses = {str(s) for s in rubric.get("blocking_statuses", ["error"])}
    if status in blocking_statuses:
        flag(flags, f"EVENT_STATUS_ERROR:{event_index}:{status}")
        status_ratio = 0.0
    if event.get("error"):
        flag(flags, f"EVENT_ERROR_PRESENT:{event_index}")
        status_ratio = 0.0

    alerts_cfg = rubric.get("alerts", {}) if isinstance(rubric.get("alerts"), dict) else {}
    alert_keys = alerts_cfg.get("meta_keys", ["alerts", "flags"])
    blocking_labels = {str(v).lower() for v in alerts_cfg.get("blocking_labels", [])}
    for key in alert_keys:
        value = meta.get(key)
        labels: list[str] = []
        if isinstance(value, list):
            labels = [str(item) for item in value]
        elif isinstance(value, str) and value:
            labels = [value]
        elif isinstance(value, dict):
            labels = [str(k) for k, enabled in value.items() if enabled]
        for label in labels:
            if not blocking_labels or label.lower() in blocking_labels:
                flag(flags, f"ALERT_PRESENT:{event_index}:{label}")
                status_ratio = 0.0
    score += float(weights.get("status_alerts", 10)) * status_ratio

    return max(0.0, min(100.0, score)), flags


def _judge_digest(events: list[dict[str, Any]], rubric: dict[str, Any]) -> dict[str, Any]:
    """A SANITIZED digest to send a judge — never raw outputs, prompts, or secrets.
    Only event shape and the sanitized `meta` labels the trace already carries."""
    scored_kinds = {str(k) for k in rubric.get("scored_kinds", ["step_complete"])}
    rows = []
    for i, e in enumerate(events, 1):
        if e.get("kind") not in scored_kinds:
            continue
        meta = e.get("meta") or {}
        rows.append({
            "i": i, "agent": e.get("agent"), "status": e.get("status"),
            # only enum-ish / boolean / numeric labels, no free text
            "event": meta.get("event"), "confidence": meta.get("confidence"),
            "schema_valid": meta.get("schema_valid"), "alert": meta.get("alert"),
        })
    return {"events": rows}


def llm_judge(events: list[dict[str, Any]], rubric: dict[str, Any],
              cmd: str | None = None) -> Any:
    """Content-quality judging seam.

    - `cmd is None`  -> return None (the historical stub; structural-only CI).
    - `cmd` given    -> shell out to an external judge CLI (a sanitized digest
      prompt appended as the last arg), expect a JSON verdict, and **fail soft**:
      any error (missing binary, timeout, non-JSON) returns None, never a
      fabricated score. The result is advisory and kept separate from the
      structural score — it never changes the structural exit code. Promoting a
      judge score to a release gate is a project-local decision *after*
      calibration (see references/judge.md), not this seam's job.
    """
    if not cmd:
        return None
    prompt = (
        "You are an independent content-quality judge for a multi-agent run. "
        "You are given a SANITIZED digest (event shape and labels only, no raw "
        "outputs). Assess overall content quality and return ONLY JSON: "
        '{"score": 0-100, "label": "pass|warn|fail", "findings": '
        '[{"i": <event-index>, "severity": "low|medium|high", "reason": "..."}]}.'
        "\n\nDIGEST:\n" + json.dumps(_judge_digest(events, rubric), ensure_ascii=False)[:6000]
    )
    try:
        r = subprocess.run(shlex.split(cmd) + [prompt],
                           capture_output=True, text=True, timeout=120)
        a, b = r.stdout.find("{"), r.stdout.rfind("}")
        verdict = json.loads(r.stdout[a:b + 1]) if a != -1 and b != -1 else None
        return verdict if isinstance(verdict, dict) else None
    except Exception:
        return None


def bar(score: float, width: int = 24) -> str:
    filled = round((score / 100.0) * width)
    return "█" * filled + "░" * (width - filled)


def evaluate(events: list[dict[str, Any]], rubric: dict[str, Any]) -> dict[str, Any]:
    scored_kinds = {str(kind) for kind in rubric.get("scored_kinds", ["step_complete"])}
    all_flags: list[str] = []
    per_agent: dict[str, list[float]] = {}
    scored_count = 0

    for idx, event in enumerate(events, 1):
        # Parse every event for blocking runtime failures.
        if event.get("status") in set(rubric.get("blocking_statuses", ["error"])):
            flag(all_flags, f"EVENT_STATUS_ERROR:{idx}:{event.get('status')}")
        if event.get("error"):
            flag(all_flags, f"EVENT_ERROR_PRESENT:{idx}")

        if event.get("kind") not in scored_kinds:
            continue
        scored_count += 1
        score, flags = score_event(event, idx, rubric)
        all_flags.extend(flags)
        agent = str(event.get("agent", "unknown"))
        per_agent.setdefault(agent, []).append(score)

    if scored_count == 0:
        flag(all_flags, "NO_SCORABLE_EVENTS")

    agent_scores = {agent: statistics.mean(scores) for agent, scores in sorted(per_agent.items())}
    overall = statistics.mean(agent_scores.values()) if agent_scores else 0.0
    return {"overall": overall, "agent_scores": agent_scores, "flags": sorted(set(all_flags)), "scored_events": scored_count}


def is_blocking(flag_text: str) -> bool:
    return flag_text.startswith(BLOCKING_PREFIXES)


def save_baseline(path: pathlib.Path, trace_path: pathlib.Path, result: dict[str, Any], min_score: float) -> None:
    import datetime

    payload = {
        "version": 1,
        "trace": trace_path.name,
        "saved_at": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
        "min_score": min_score,
        "overall": round(result["overall"], 4),
        "agent_scores": {agent: round(score, 4) for agent, score in result["agent_scores"].items()},
        "flags": result["flags"],
        "scored_events": result["scored_events"],
    }
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except OSError as exc:
        raise EvalInputError(f"cannot write baseline: {exc}") from exc


def load_baseline(path: pathlib.Path) -> dict[str, Any]:
    if not path.exists():
        raise EvalInputError(f"baseline not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EvalInputError(f"cannot read baseline: {exc}") from exc
    if not isinstance(data, dict) or "overall" not in data or "agent_scores" not in data:
        raise EvalInputError(f"baseline has no overall/agent_scores: {path}")
    return data


def compare_to_baseline(result: dict[str, Any], baseline: dict[str, Any], max_drop: float) -> tuple[list[str], list[str]]:
    """Return (report_lines, regressions). Any regression should fail CI."""
    lines: list[str] = []
    regressions: list[str] = []

    base_overall = float(baseline["overall"])
    delta = result["overall"] - base_overall
    lines.append(f"overall: {base_overall:.1f} -> {result['overall']:.1f} ({delta:+.1f})")
    if delta < -max_drop:
        regressions.append(f"OVERALL_SCORE_DROP:{delta:+.1f}")

    base_agents = baseline.get("agent_scores") or {}
    for agent in sorted(set(base_agents) | set(result["agent_scores"])):
        old = base_agents.get(agent)
        new = result["agent_scores"].get(agent)
        if old is None:
            lines.append(f"agent {agent}: (new) -> {new:.1f}")
        elif new is None:
            lines.append(f"agent {agent}: {float(old):.1f} -> (missing)")
            regressions.append(f"AGENT_MISSING:{agent}")
        else:
            agent_delta = new - float(old)
            lines.append(f"agent {agent}: {float(old):.1f} -> {new:.1f} ({agent_delta:+.1f})")
            if agent_delta < -max_drop:
                regressions.append(f"AGENT_SCORE_DROP:{agent}:{agent_delta:+.1f}")

    base_flags = set(baseline.get("flags") or [])
    new_flags = [item for item in result["flags"] if item not in base_flags]
    for item in new_flags:
        lines.append(f"new flag: {item}")
        if is_blocking(item):
            regressions.append(f"NEW_BLOCKING_FLAG:{item}")
    return lines, regressions


def print_report(trace_path: pathlib.Path, result: dict[str, Any], min_score: float, judge_result: Any, judge_requested: bool, judge_cmd_given: bool = False) -> None:
    print(f"trace: {trace_path}")
    print(f"scored events: {result['scored_events']}")
    print("\nper-agent structural score:")
    if result["agent_scores"]:
        for agent, score in result["agent_scores"].items():
            print(f"  {agent:24} {score:6.1f}  {bar(score)}")
    else:
        print("  (none)")
    print(f"\noverall structural score: {result['overall']:.1f}")
    print(f"minimum passing score:    {min_score:.1f}")

    flags = result["flags"]
    print("\nflags:")
    if flags:
        for item in flags:
            marker = "BLOCK" if is_blocking(item) else "INFO"
            print(f"  [{marker}] {item}")
    else:
        print("  none")

    if judge_requested:
        print("\njudge (advisory, separate from the structural score):")
        if judge_result is None:
            if judge_cmd_given:
                print("  unavailable: --judge-cmd failed soft (no binary / timeout / non-JSON); structural score unchanged")
            else:
                print("  unavailable: llm_judge() stub returned None; pass --judge-cmd to wire a real judge")
            print("  [INFO] JUDGE_UNAVAILABLE")
        else:
            print(json.dumps(judge_result, indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Evaluate an observability-tracing JSONL run with a deterministic structural rubric.",
    )
    parser.add_argument("trace_id", nargs="?", help="Trace id, trace JSONL path, or filename under --traces-dir")
    parser.add_argument("--latest", action="store_true", help="Evaluate the most recently modified .jsonl trace")
    parser.add_argument("--traces-dir", default=".context/traces", help="Directory containing per-trace JSONL files")
    parser.add_argument("--rubric", help="Optional JSON rubric config to merge over defaults")
    parser.add_argument("--min-score", type=float, help="Override the rubric minimum passing score")
    parser.add_argument("--judge", action="store_true", help="Call the LLM-as-judge seam; without --judge-cmd the stub returns None")
    parser.add_argument("--judge-cmd", help="External judge CLI; a sanitized digest is appended as the last arg; JSON verdict on stdout; fails soft (advisory, never gates the structural score)")
    parser.add_argument("--baseline", help="Compare against a saved baseline JSON; regressions fail the run")
    parser.add_argument("--save-baseline", help="Write this run's scores/flags to a baseline JSON (after comparison, if both given)")
    parser.add_argument("--max-drop", type=float, default=0.0, help="Allowed score drop vs baseline before failing (default 0)")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.trace_id and args.latest:
            raise EvalInputError("--latest and trace_id are mutually exclusive")
        rubric = load_rubric(args.rubric)
        min_score = float(args.min_score if args.min_score is not None else rubric.get("min_score", 80))
        traces_dir = pathlib.Path(args.traces_dir)
        trace_path = resolve_trace_path(args.trace_id, args.latest, traces_dir)
        events = load_events(trace_path)
        result = evaluate(events, rubric)
        judge_requested = args.judge or bool(args.judge_cmd)
        judge_result = llm_judge(events, rubric, args.judge_cmd) if judge_requested else None
        print_report(trace_path, result, min_score, judge_result, judge_requested, bool(args.judge_cmd))

        regressions: list[str] = []
        if args.baseline:
            baseline = load_baseline(pathlib.Path(args.baseline))
            lines, regressions = compare_to_baseline(result, baseline, args.max_drop)
            print(f"\nbaseline comparison ({args.baseline}):")
            for line in lines:
                print(f"  {line}")
            if regressions:
                print("  regressions:")
                for item in regressions:
                    print(f"    [BLOCK] {item}")
            else:
                print("  no regressions")
        if args.save_baseline:
            save_baseline(pathlib.Path(args.save_baseline), trace_path, result, min_score)
            print(f"\nbaseline saved: {args.save_baseline}")
    except EvalInputError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    blocking_flags = [item for item in result["flags"] if is_blocking(item)]
    if result["overall"] < min_score or blocking_flags or regressions:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
