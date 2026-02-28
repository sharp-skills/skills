# Contributing to SharpSkills

SharpSkills is built on one principle: **quality over quantity**.
Every skill must contain real, working code — written from official documentation, not generated placeholders.

Use cases come first — they define the real problems people face. Skills are the tools we build to solve them.

---

## The Standard: What "Real" Means

Before writing a skill, look at [`skills/stripe/SKILL.md`](skills/stripe/SKILL.md) or [`skills/express/SKILL.md`](skills/express/SKILL.md) as the gold standard.

A skill is **real** when:
- Every code snippet runs without modification (no TODOs, no `// ...`, no placeholder values)
- Package names in `npm install` / `pip install` actually exist on npm/PyPI
- Patterns come from the tool's official docs or real GitHub Issues/Stack Overflow
- The Failure Modes table lists errors users actually encounter (copied from real issues)
- Pre-Deploy Checklist reflects production experience

A skill is **not acceptable** when it contains:
- `// TODO: ...` or placeholder comments
- `require('jira')` / `require('algolia')` when no such npm package exists
- Generic errors like "Auth error | Invalid API key | Check environment variable"
- AI-generated guesses about an API without reading the actual docs

---

## Skill Structure

```
skills/your-skill-name/
└── SKILL.md         # Required. Exact filename, case-sensitive.
```

No `README.md` inside the skill folder.

### SKILL.md Template

```markdown
---
name: your-skill-name
description: >-
  What it does and when to use it. Use when asked to: list 6-8 specific
  trigger phrases that match what users actually type.
license: Apache-2.0
compatibility:
  - node >= 18
  - python >= 3.9
metadata:
  author: your-github-username
  version: 1.0.0
  category: development
  tags:
    - primary-tag
    - secondary-tag
    - language
    - use-case
---

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

Exact prompt: "Add Stripe subscriptions to my Express app"

## Real-World Example
Specific persona + situation + outcome.

## Related Skills
- [stripe](../skills/stripe/) — payment processing patterns
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
