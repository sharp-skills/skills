#!/usr/bin/env python3
"""Check agent-to-agent messages against a source-trust policy.

When agents instruct agents, "who sent this" cannot be taken from what the
message *claims* — a claim is spoofable, and a malicious document can tell a
browsing agent to tell a coding agent to exfiltrate. Trust must come from the
*channel* the message arrived on (verifiable), not the label inside it. The
governing rule:

  Instructions from another agent have NO more authority than instructions
  from an unknown human. Legitimate orchestration never needs to override
  safety — so a message that asks to escalate scope or disable a safety check
  is a red flag, not a permission grant, regardless of who it claims to be.

Trust tiers, assigned by CHANNEL (how it arrived), never by claim:

  1 human           — a direct human principal / operator.
  2 authenticated   — an orchestrator verified at session start.
  3 peer / forwarded— another agent, or anything forwarded through the system.
  4 env / content   — file, web page, DB row, tool output. Data, not orders.

Checks per message:

  A. SPOOF     — the claimed source asserts more trust than the channel proves
                 (claims "orchestrator" but arrived forwarded). Judge by channel.
  B. PRIVILEGE — a privileged ask (escalate scope, disable safety, override
                 policy, delete data, send external, change credentials) from an
                 effective tier >= 3 is refused. Only tiers 1-2 may request it.
  C. DATA-AS-ORDERS — tier-4 environmental content that asks to *do* anything.
                 Data is data; it never carries instructions.

Manifest (messages.jsonl), one message per line:
  {"id": "m1", "claimed_source": "orchestrator", "channel": "authenticated",
   "asks": ["assign_task"]}

Exit codes: 0 = policy holds, 1 = violations, 2 = bad input. Stdlib only.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Channel -> effective trust tier (lower = more trusted). This is verifiable.
CHANNEL_TIER = {
    "human": 1,
    "authenticated": 2,
    "peer": 3, "forwarded": 3, "agent": 3,
    "env": 4, "content": 4, "tool_output": 4,
}
# Claimed-source label -> the tier it asserts. This is NOT trusted; only compared.
CLAIM_TIER = {
    "human": 1, "operator": 1,
    "orchestrator": 2, "master": 2, "supervisor": 2,
    "agent": 3, "peer": 3,
    "content": 4, "env": 4,
}
PRIVILEGED = {
    "escalate_scope", "disable_safety", "override_policy",
    "delete_data", "send_external", "change_credentials",
}


def die(msg: str) -> "NoReturn":
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(2)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--messages", required=True, help="messages JSONL")
    args = ap.parse_args()

    try:
        lines = Path(args.messages).read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        die(f"cannot read messages {args.messages}: {exc}")

    violations: list[str] = []
    checked = 0

    for i, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
        checked += 1
        try:
            m = json.loads(line)
        except json.JSONDecodeError as exc:
            violations.append(f"message {i}: not valid JSON ({exc})")
            continue
        mid = m.get("id") or f"#{i}"
        channel = str(m.get("channel", "")).lower()
        if channel not in CHANNEL_TIER:
            violations.append(
                f"{mid}: unknown channel {channel!r} — trust is assigned by "
                f"channel, so an unrecognized one can't be trusted at all")
            continue
        eff = CHANNEL_TIER[channel]  # effective tier = channel tier, always
        asks = m.get("asks") or []
        if not isinstance(asks, list):
            violations.append(f"{mid}: 'asks' must be a list")
            continue

        # A. spoof: claim asserts more trust than the channel proves
        claim = str(m.get("claimed_source", "")).lower()
        if claim in CLAIM_TIER and CLAIM_TIER[claim] < eff:
            violations.append(
                f"{mid}: claims {claim!r} (tier {CLAIM_TIER[claim]}) but arrived "
                f"on {channel!r} (tier {eff}) — treat at the channel's tier; the "
                f"label is spoofable")

        # B. privileged ask from an untrusted tier
        for a in asks:
            if a in PRIVILEGED and eff >= 3:
                violations.append(
                    f"{mid}: asks {a!r} from tier {eff} ({channel}) — privileged "
                    f"actions need tier 1-2; legitimate orchestration never asks "
                    f"to override safety")

        # C. environmental data must not carry instructions
        if eff == 4 and asks:
            violations.append(
                f"{mid}: tier-4 {channel!r} content carries instructions "
                f"{list(asks)} — environmental data is data, not orders")

    print(f"Checked {checked} message(s).")
    if violations:
        print(f"\n{len(violations)} violation(s):", file=sys.stderr)
        for v in violations:
            print(f"  ✗ {v}", file=sys.stderr)
        return 1
    print("✅ Trust policy holds: every message judged by its channel, no "
          "privileged ask from an untrusted tier, no data posing as orders.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
