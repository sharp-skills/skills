---
name: agent-isolation
description: Keep a prompt-injected or mistaken agent from doing real damage by isolating what each session can touch — never letting one session hold sensitive access, untrusted input, and an outbound channel at the same time (the lethal trifecta). Use this when an agent logs into real accounts, drives a browser, or reads inbound messages/web pages an attacker can author; when deciding which capabilities may share a session; or when giving an agent bounded autonomy over money, publishing, or communication. A sandbox or VM protects your host and network — it does not protect the accounts you log in inside it.
license: Apache-2.0
---

# Agent Isolation

The reflex is to think a VM or sandbox makes an agent safe. It makes your **host and network** safe. It does nothing for the accounts you log in *inside* it — the agent drives those sessions as you, by design, because acting as you is the whole point. So the real question isn't "is the agent contained?" but "if this agent is prompt-injected or simply wrong, what can it reach?" This skill is the discipline that keeps the answer small.

It comes from designing how to log real accounts into an autonomous browser agent safely. The core move is not a clever sandbox setting — it's refusing to let any one session hold all three capabilities an attack needs.

## The lethal trifecta

The framing and the name are **Simon Willison's** — see his writing on the lethal
trifecta and on prompt injection generally. What this skill adds is not the idea
but its enforcement: turning a rule people agree with into a check that reads a
session manifest and fails the build.

Real damage from a prompt injection needs three things **in the same session at once**:

1. **Sensitive access** — a logged-in account or credential with real value.
2. **Untrusted input** — the agent ingests content an attacker can author: a web page, an inbound DM, an inbound email. This is where the malicious instruction arrives.
3. **Exfiltration** — a way to send data out or act outward: send mail/DM, HTTP POST, publish.

Hold all three and a hidden instruction in a fetched web page can read the logged-in account and mail its contents out — the agent did it "as you." **Remove any one leg and the injection is defused.** A session that reads untrusted content but holds no account and cannot send is harmless no matter what it reads. A session logged into a sensitive account that never touches untrusted input has nothing to be injected *with*.

So the primary rule is **split sessions**: never co-locate the three legs. The checker's headline job is to prove no session carries all three.

## Defense in echelons (one wall fails, the next holds)

Isolation is the load-bearing wall, but not the only one. In priority order:

- **Separate identity (most important, zero tech).** The agent uses its *own* scoped identity — a dedicated email, app-passwords, minimal-scope tokens, a low-limit virtual card. Your bank, primary email, password manager, and work SSO never go in the box. The checker enforces a `forbidden_identities` list so a master account can't be wired into a session by accident.
- **Break the trifecta (isolation).** As above — split sessions so no one of them is dangerous.
- **Sandbox untrusted work.** Give the session that reads inbound/untrusted content the least power: no logged-in browser, no send. Real runtimes give you the lever — a browser agent like Claude-in-Chrome or OpenClaw's browser, sandbox modes in the orchestration SDKs, per-tool permissions. (Note the common tension: a hardened sandbox mode often *disables the browser entirely* — which is exactly why logged-in browsing belongs only in a trusted, self-initiated session, never an inbound-driven one.)
- **Human-in-the-loop on irreversible actions.** Sends, payments, deletions, publishing, and security/2FA changes require manual approval. The checker fails any session that can take an irreversible action without an approval gate.
- **Audit & reversibility.** Everything the agent holds should be revocable in minutes (scoped tokens, virtual cards, throwaway accounts), and every action should land in the trace (`observability-tracing`).

## Run vs read

| Resource | Action | Why |
|---|---|---|
| `scripts/trifecta_check.py` | **RUN** | Maps each session's capabilities to legs and fails: any session with all three legs, an ungated irreversible action, a forbidden identity, or an unclassified capability. |
| `references/isolation-design.md` | **READ** | The threat model in full, the main-vs-sandboxed session split, the 80/20 to start today, and how to classify a new capability. |
| `examples/selftest.sh` | **RUN** | Proves the checker on a safe split-session layout and an unsafe one. |

```bash
python3 .../trifecta_check.py --manifest sessions.json
```

## Common pitfalls

- **"It's in a VM, so it's safe."** The VM guards the host and network, not the accounts inside. Injection acts within those sessions regardless of the VM.
- **One convenient do-everything session.** The single most common cause of the trifecta: a helpful assistant that reads your inbox, is logged into your accounts, and can reply. That's all three legs.
- **Logging in as yourself.** Master accounts handed to an agent turn every agent mistake into a personal one. Scoped agent identity only; the checker's `forbidden_identities` makes it enforceable.
- **Trusting inbound as if you wrote it.** Inbound DMs, emails, and fetched pages are untrusted input — the injection vector. Keep them out of any session that also has sensitive access or a send channel.
- **Irreversible actions with no human gate.** Autonomy over money/publishing/deletion without approval means a single bad step is unrecoverable.
- **An unclassified capability.** A tool nobody labeled might grant any leg; the checker refuses to pass a capability it can't classify, so the trifecta can't hide behind a vague name.

## Verification checklist

- [ ] `sh examples/selftest.sh` passes (split sessions → 0; trifecta, ungated irreversible, forbidden identity, unclassified capability → 1; missing file → 2).
- [ ] No session holds sensitive + untrusted + exfil together (checked in CI, not by eye).
- [ ] Every capability in every session maps to a known leg; nothing unclassified.
- [ ] Sessions with irreversible actions require human approval.
- [ ] No session runs as a forbidden (master/primary) identity; agent identities are scoped and revocable.

## Related skills in this bundle

- `governance-hooks` — the harness-level guard (no-touch zones, secrets, drift); isolation is the account-level guard. Both assume the agent can misbehave and contain the blast radius.
- `observability-tracing` — the audit leg: every action an isolated session takes lands in the trace, so an incident is reconstructable and reversible.
- `event-envelope` — the `runtime` tag lets policy differ by runtime (e.g. a browser runtime treated as untrusted), which is where isolation decisions attach.
- `mechanize-agents` — a deterministic `code` handler with a validated payload is a way to remove a leg: mechanical, no account, no free-form send.
