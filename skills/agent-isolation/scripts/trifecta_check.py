#!/usr/bin/env python3
"""Check agent session isolation against the lethal-trifecta rule and its
companions, so a prompt-injected agent can't turn a mistake into real damage.

Running an agent inside a sandbox/VM protects your host and network — it does
NOT protect the accounts you log in *inside* it. The agent drives those sessions
as you. Real damage needs three capabilities in the SAME session at once:

  1. SENSITIVE  — a logged-in account or credential with real value.
  2. UNTRUSTED  — it ingests content an attacker can author (a web page, an
                  inbound DM/email). This is where the injection arrives.
  3. EXFIL      — a channel to send data or act outward (send mail/DM, HTTP
                  POST, publish).

Hold all three and an injected instruction hidden in untrusted content can read
the sensitive account and send it out. Remove ANY one leg from the session and
the injection is defused. So the primary rule is: never let one session carry
all three legs — SPLIT SESSIONS.

Checks over a sessions manifest:

  A. TRIFECTA   — no session holds sensitive + untrusted + exfil at once.
  B. APPROVAL   — any session that can take an irreversible action (send,
                  pay, delete, publish, change security) requires a
                  human-in-the-loop approval gate.
  C. IDENTITY   — no session runs as a forbidden identity (your primary email,
                  bank, password manager, work SSO). The agent uses its OWN
                  scoped identity; master accounts never go in the box.
  D. CLASSIFIED — every declared capability maps to a known leg/role, so an
                  unclassified tool can't smuggle a leg in unnoticed.

Manifest shape (sessions.json):
  {"forbidden_identities": ["owner-primary-email", "owner-bank"],
   "sessions": {
     "reader":  {"identity": "agent-scoped", "approval_required": false,
                 "capabilities": ["web_read", "inbound_dm"]},
     "operator":{"identity": "agent-scoped", "approval_required": true,
                 "capabilities": ["logged_in_browser", "send_dm"]}}}

Exit codes: 0 = isolation holds, 1 = violations, 2 = bad input. Stdlib only.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Each capability maps to the leg (or legs) it grants a session.
SENSITIVE = "sensitive"
UNTRUSTED = "untrusted"
EXFIL = "exfil"

TOOL_LEGS = {
    # sensitive: a logged-in account / credential with real value
    "logged_in_browser": {SENSITIVE},
    "email_account": {SENSITIVE},
    "bank_account": {SENSITIVE},
    "password_manager": {SENSITIVE},
    "cloud_admin": {SENSITIVE},
    "api_token_write": {SENSITIVE},
    # untrusted: ingests attacker-authorable content
    "web_read": {UNTRUSTED},
    "inbound_dm": {UNTRUSTED},
    "inbound_email": {UNTRUSTED},
    "rss_feed": {UNTRUSTED},
    # exfil / outward action
    "send_email": {EXFIL},
    "send_dm": {EXFIL},
    "http_post": {EXFIL},
    "publish": {EXFIL},
    # legs-free capabilities (read-only, no account, no send)
    "calculator": set(),
    "code_exec_sandboxed": set(),
    "local_scratch": set(),
}

# Capabilities whose use is irreversible and so require a human gate.
IRREVERSIBLE = {"send_email", "send_dm", "http_post", "publish",
                "payment", "delete_data", "security_change"}


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


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--manifest", required=True, help="sessions manifest JSON")
    args = ap.parse_args()

    man = load(args.manifest, "manifest")
    sessions = man.get("sessions")
    if not isinstance(sessions, dict) or not sessions:
        die("manifest has no non-empty 'sessions' object")
    forbidden = set(man.get("forbidden_identities") or [])

    violations: list[str] = []

    for sid, s in sorted(sessions.items()):
        if not isinstance(s, dict):
            violations.append(f"{sid}: session is not an object")
            continue
        caps = s.get("capabilities") or []
        legs: set[str] = set()
        for cap in caps:
            # D. every capability must be classified
            if cap not in TOOL_LEGS and cap not in IRREVERSIBLE:
                violations.append(
                    f"{sid}: capability {cap!r} is unclassified — classify it "
                    f"(it might grant a leg you're not counting)")
                continue
            legs |= TOOL_LEGS.get(cap, set())

        # A. lethal trifecta
        if {SENSITIVE, UNTRUSTED, EXFIL} <= legs:
            violations.append(
                f"{sid}: LETHAL TRIFECTA — this session holds sensitive access, "
                f"untrusted input, AND an exfil channel at once; an injection in "
                f"untrusted content can read the account and send it out. Split "
                f"it: move untrusted-reading to a session with no sensitive "
                f"account and no send capability.")

        # B. human-in-the-loop on irreversible actions
        irreversible_here = sorted(set(caps) & IRREVERSIBLE)
        if irreversible_here and s.get("approval_required") is not True:
            violations.append(
                f"{sid}: can take irreversible action(s) {irreversible_here} "
                f"without approval_required:true — a human must confirm sends, "
                f"payments, deletions, publishes, and security changes.")

        # C. forbidden identity
        ident = s.get("identity")
        if ident in forbidden:
            violations.append(
                f"{sid}: runs as forbidden identity {ident!r} — master/primary "
                f"accounts (bank, primary email, password manager, work SSO) "
                f"must never be handed to the agent; use a scoped agent identity.")
        elif not (isinstance(ident, str) and ident.strip()):
            violations.append(
                f"{sid}: no identity declared — state whose credentials this "
                f"session runs as so it can be checked against forbidden ones.")

    print(f"Checked {len(sessions)} session(s).")
    if violations:
        print(f"\n{len(violations)} violation(s):", file=sys.stderr)
        for v in violations:
            print(f"  ✗ {v}", file=sys.stderr)
        return 1
    print("✅ Isolation holds: no session carries the lethal trifecta, "
          "irreversible actions are gated, identities are scoped.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
