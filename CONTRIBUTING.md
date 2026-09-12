# Contributing to SharpSkills

SharpSkills is built on one principle: **quality over quantity**.
Every skill must contain real, working code — written from official documentation, not generated placeholders.

Use cases come first — they define the real problems people face. Skills are the tools we build to solve them.

---

## The Standard: What "Real" Means

Before writing a skill, look at [`skills/tool-call-validator/SKILL.md`](skills/tool-call-validator/SKILL.md) as the gold standard: a practice, the checker that enforces it, fixtures that show it going red, and a self-test.

Two kinds of skill live here, and the bar is the same for both:

- **Tool skills** — how to use one library, service or CLI (its API, its
  flags, its errors). Written from the official documentation only; every
  package name and snippet verified against it.
- **Practice skills** — how to build or operate something (the
  `multi-agent-engineering` collection). Written from operating a real system;
  every rule ships with a runnable checker under `scripts/` and fixtures under
  `examples/` that prove the checker catches the failure it describes.

A skill is **real** when:
- Every code snippet runs without modification (no TODOs, no `// ...`, no placeholder values)
- Package names in `npm install` / `pip install` actually exist on npm/PyPI
- Patterns come from the tool's official docs or real GitHub Issues/Stack Overflow
- The Failure Modes table lists errors users actually encounter (copied from real issues)
- Pre-Deploy Checklist reflects production experience
- For a practice skill: the checker goes red on the bad fixture and green on the good one, and `examples/selftest.sh` proves it

A skill is **not acceptable** when it contains:
- `// TODO: ...` or placeholder comments
- `require('jira')` / `require('algolia')` when no such npm package exists
- Generic errors like "Auth error | Invalid API key | Check environment variable"
- AI-generated guesses about an API without reading the actual docs

---

## Skill Structure

```
skills/your-skill-name/
├── SKILL.md         # Required. Exact filename, case-sensitive.
├── scripts/         # Optional. Runnable checkers/tools the skill refers to.
├── references/      # Optional. Longer material SKILL.md links to.
└── examples/        # Optional. Fixtures and a self-test (examples/selftest.sh).
```

`SKILL.md` is the only required file and must stand on its own. No `README.md`
at the skill root — `SKILL.md` is the skill's front page (a `README.md` inside
`examples/` that explains the fixtures is fine).

Skills that belong to an audited set live in `skills/` like any other and are
listed by their collection under `bundles/<collection>/`, which holds the
collection's README, demos and one-command audit.

### Front matter

`name`, `description` and `license` are required; the rest is optional but
welcome. Quote or fold the description (`>-`) — an unquoted `: ` inside it is
invalid YAML and fails CI.

```yaml
---
name: your-skill-name
description: >-
  What it does and when to use it. Use when asked to: list 6-8 specific
  trigger phrases that match what users actually type.
license: Apache-2.0
compatibility:          # optional
  - node >= 18
  - python >= 3.9
metadata:               # optional
  author: your-github-username
  version: 1.0.0
  category: development
  tags: [primary-tag, secondary-tag, language, use-case]
---
```

### Tool skill template

```markdown

# Tool Name

One-paragraph summary: what it is, why you'd use it, what it's best for.

## Installation

npm install actual-package-name

## Quick Start

Minimal working example — copy-paste and run.

## When to Use

- "phrase users actually type"
- "another real trigger phrase"

## Core Patterns

### Pattern 1: Name

Real code. 3-5 patterns total.

## Production Notes

Numbered gotchas from official docs and real GitHub Issues.

## Failure Modes

| Symptom | Root Cause | Fix |
|---------|-----------|-----|
| Exact error message | Why it happens | Specific fix |

## Pre-Deploy Checklist

- [ ] Specific checklist item

## Resources

- Docs: https://...
- GitHub: https://...
```

### Practice skill shape

No fixed template — see any skill in `skills/` from the
`multi-agent-engineering` collection. What every one of them has: the rule and
why it exists, what goes wrong without it, a checker in `scripts/` (stdlib
only, offline, exit 0/1), good and bad fixtures in `examples/` with a note on
*why* the bad one fails, and `examples/selftest.sh` that runs the checker
against both.

---

## Before Writing a Skill

1. **Read the official docs** — Getting Started + API reference minimum
2. **Check real issues** — GitHub Issues + Stack Overflow for common errors → Failure Modes
3. **Test the Quick Start** — run it locally to confirm it works
4. **Verify package names** — `npm info <package>` or `pip index versions <package>`

---

## Creating a Use Case

Use cases live in `use-cases/` and describe problems, not tools.

```bash
touch use-cases/your-use-case-slug.md
```

Template:

```markdown
---
title: "Action-Oriented Title"
slug: your-use-case-slug
description: "One sentence explaining the use case."
skills: [skill-name]
category: development
tags: [tag1, tag2]
---

## The Problem
Concrete pain point.

## The Solution
2-3 sentences. Name the skills.

## Step-by-Step Walkthrough

### 1. First step

Exact prompt: "Validate every tool call my agent makes before it runs"

## Real-World Example
Specific persona + situation + outcome.

## Related Skills
- [tool-call-validator](../skills/tool-call-validator/) — pre-flight check on agent tool calls
```

---

## Submitting a Pull Request

New skill:
```bash
git checkout -b add-skill/your-skill-name
git commit -m "Add skill: your-skill-name"
```

New use case:
```bash
git checkout -b add-use-case/your-slug
git commit -m "Add use case: your-slug"
```

---

## Categories

| Category | Description |
|---|---|
| `agents` | Building and operating LLM agents and multi-agent systems |
| `development` | APIs, SDKs, libraries, frameworks |
| `devops` | Docker, CI/CD, infrastructure, Kubernetes |
| `data-ai` | Databases, ML, AI, vector stores |
| `security` | Auth, JWT, secrets, encryption |
| `testing` | Unit, integration, E2E testing |
| `observability` | Logging, metrics, tracing |
| `messaging` | Queues, pub/sub, real-time |
| `storage` | Files, object storage, CDN |
| `productivity` | Git, CLI tools, workflow |
| `content` | Email, SMS, notifications |

---

Questions? Open an issue on GitHub.
