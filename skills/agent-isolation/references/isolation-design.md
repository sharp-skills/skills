# Isolation design notes

Loaded on demand. The full threat model, the session-role split, how to
classify a new capability, and the smallest safe starting point.

## The threat model in one paragraph

An autonomous agent is useful because it acts with your authority. That same
authority is the risk: if the agent is prompt-injected (a malicious instruction
hidden in a web page, an email, a DM) or simply reasons wrongly, it acts with
your authority in whatever it can reach. Sandboxes and VMs bound the *machine*
(host filesystem, network) — they do not bound the *accounts* logged in inside
them, because the agent is supposed to use those. So containment has to happen
at the level of "what can any one session touch," not just "is it in a box."

## Why the trifecta framing works

Most injection defenses try to detect the bad instruction. That's a losing
game — untrusted content is unbounded and attackers adapt. The trifecta framing
gives up on detection and removes *capability* instead: an injection can only
cause damage if the session it lands in can both reach something valuable and
send something out. Take away either, and the worst an injection achieves is
making a powerless session do powerless things. It converts an unwinnable
detection problem into a winnable configuration problem.

The three legs, precisely:

- **Sensitive** — a *logged-in* account or a credential with real value.
  Read-only access to public data is not sensitive; a session logged into your
  store admin is.
- **Untrusted** — content whose author you don't control reaches the model's
  context: fetched web pages, inbound messages/email, RSS, tool results that
  echo third-party text. This is the injection channel.
- **Exfil / outward action** — the session can emit: send mail/DM, POST to an
  arbitrary URL, publish, or otherwise move data or effects outside the
  boundary.

## Session roles: trusted vs sandboxed

Resolve the tension between "logged-in browsing" and "reading untrusted input"
by giving them different sessions:

- **Trusted session** (`main`-like): full tools, logged-in browser, may hold a
  sensitive account. Used **only for your own self-initiated tasks** — never
  driven by inbound/untrusted content. Because nothing untrusted steers it, the
  injection leg is absent even though sensitive + exfil are present.
- **Sandboxed session** (`non-main`-like): handles **all** inbound/untrusted
  work — reading web pages, triaging DMs. Stripped of power: no logged-in
  browser, no send, cron/gateway/extra nodes disabled. Because it holds neither
  sensitive access nor an exfil channel, injection has nothing to grab or send.

Note a real runtime constraint that makes this natural: hardened sandbox modes
frequently **disable the browser outright**. That's not an obstacle — it's the
correct shape. Logged-in browsing lives in the trusted, self-initiated session;
untrusted reading lives in the powerless sandboxed one. If you ever feel forced
to give the sandboxed session a logged-in browser "for convenience," you are
about to rebuild the trifecta.

## Echelon 1 is human, not technical

The highest-leverage control needs no code: **the agent never logs in as you.**
It gets a dedicated identity — its own email, app-passwords or minimal-scope API
tokens instead of master passwords, read-only where possible, and a low-limit
virtual card (never a real bank card) for anything involving money. Your
primary email, bank, password manager, government, and work accounts simply
never enter the agent's box. The checker encodes this as `forbidden_identities`
so the rule is enforced, not remembered.

## Human-in-the-loop on the irreversible

Some actions can't be undone: sending a message, moving money, deleting data,
publishing, changing a password/2FA/security setting. These require an explicit
human approval before execution, regardless of how confident the agent is.
Bounded autonomy means the agent can do a great deal on its own *up to* the
irreversible step, then stops for a human. The checker fails any session that
can take such an action without an approval gate.

## Classifying a new capability

When you add a tool, decide its leg before you wire it in:

- Does it expose a logged-in account or a credential with value? → **sensitive**.
- Can attacker-authored content reach the model through it? → **untrusted**.
- Can it send data out or cause an outward effect? → **exfil** (and probably
  **irreversible**, so it needs approval too).
- None of the above (pure local compute, sandboxed code, scratch space) → no
  leg.

Leave a capability unclassified and the checker refuses to pass it — an
unlabeled tool is exactly how a leg sneaks into a session nobody audited.

## The 80/20 to start today (no config framework needed)

Echelons 1 and 2 alone remove most of the risk: give the agent its own
identity, keep bank/primary/master accounts out entirely, use a low-limit
virtual card, and **never mix "reading untrusted content" with "a logged-in
sensitive account" in one session.** Everything else — sandbox modes, approval
gates, allowlists, audit — hardens from there.
