# Contributing to SharpSkills

Thank you for your interest in contributing. SharpSkills is built on one principle: **quality over quantity**. Every skill must solve a real problem, be accurate, and pass automated testing before it reaches users.

Use cases come first — they define the real problems people face. Skills are the tools we build to solve them.

---

## Creating a Use Case

Use cases are problem-first guides that show how AI agents solve real challenges. They live in the `use-cases/` directory.

A use case can stand on its own. If no skill exists yet for the problem you're describing, that's fine — your use case helps identify what skills need to be built.

### 1. Pick a Real Problem

Every use case starts with a pain point someone actually has. Ask:

- Is this a problem developers encounter regularly?
- Can I describe a specific persona who faces this problem?
- Does the walkthrough lead to a concrete, measurable outcome?

### 2. Create the File

```bash
touch use-cases/your-use-case-slug.md
```

Filenames use lowercase kebab-case matching the slug field (e.g., `handle-stripe-webhooks.md`).

### 3. Write the Use Case

```markdown
---
title: "Action-Oriented Title"
slug: your-use-case-slug
description: "One sentence explaining the use case."
skills: [skill-name]  # omit if no matching skills exist yet
category: development
tags: [tag1, tag2, tag3]
---

## The Problem
Describe the specific pain point. Be concrete.

## The Solution
Explain the approach in 2-3 sentences.

## Step-by-Step Walkthrough

### 1. First step
Tell the reader exactly what to say to the AI agent:
```
The exact prompt the user would type.
```

## Real-World Example
A specific persona, a specific situation, a specific outcome.

## Related Skills
- [skill-name](../skills/skill-name/) — What it adds to this workflow
```

---

## Creating a New Skill

Before creating a skill, ask:

- What use case does this serve?
- Would a developer use this at least weekly?
- Is this covered by the official documentation, real GitHub Issues, or Stack Overflow?

### 1. Create the Directory

```bash
mkdir -p skills/your-skill-name
```

Skill names use lowercase kebab-case (e.g., `stripe`, `rate-limit-handling`).

### 2. Write the SKILL.md

```markdown
---
name: your-skill-name
description: "What it does. Use when asked to: list 6-8 trigger phrases."
license: Apache-2.0
metadata:
  author: your-github-username
  version: "1.0.0"
  category: development
  tags: ["tag1", "tag2", "tag3"]
---

# Skill Name

## Quick Start
Install command + minimal working example.

## When to Use
Trigger phrases — what the user would actually say.

## Core Patterns
2-4 real production patterns with code.

## Production Notes
Common gotchas from real GitHub Issues and Stack Overflow.

## Failure Modes
| Symptom | Root Cause | Fix |

## Pre-Deploy Checklist
- [ ] Item 1
```

### 3. Test Before Submitting

Every skill must pass 4 automated tests:

```bash
python sharpskill.py run --tool your-skill-name --no-push
```

| Level | What it checks |
|---|---|
| L1 | Syntax — valid Python, JS, Bash, YAML |
| L2 | Dependencies — packages exist on npm / PyPI |
| L3 | Sandbox — code runs without crashing |
| L4 | Mock API — API calls are structurally valid |

**Score must be 100% to submit.** Skills with failures go to `drafts/` and are marked `[BETA]`.

---

## Skill Quality Guidelines

**What makes a good skill:**
- Serves a real use case developers face regularly
- Instructions are precise enough that an AI can follow them without guessing
- Examples use realistic data, not lorem ipsum or placeholder values
- Covers failure modes and how to recover from them
- Works across different AI tools — not vendor-specific

**What to avoid:**
- Skills without a clear use case
- Vague instructions like "process the data" without explaining how
- Skills that duplicate built-in tool capabilities
- Placeholder content or generic examples
- Instructions longer than 300 lines (split into multiple skills instead)

---

## Submitting a Pull Request

### For a New Use Case

1. Fork the repository
2. Create a branch: `git checkout -b add-use-case/your-use-case-slug`
3. Add `use-cases/your-use-case-slug.md`
4. Update the use cases list in `README.md`
5. Submit a PR with title: `Add use case: your-use-case-slug`

### For a New Skill

1. Fork the repository
2. Create a branch: `git checkout -b add-skill/your-skill-name`
3. Add `skills/your-skill-name/SKILL.md`
4. Run `python sharpskill.py run --tool your-skill-name --no-push` — score must be 100%
5. Update the skills table in `README.md`
6. Submit a PR with title: `Add skill: your-skill-name`

---

## Categories

| Category | Description |
|---|---|
| `documents` | PDF, Word, document processing |
| `development` | Code review, testing, refactoring |
| `data-ai` | Data analysis, ML, AI integrations |
| `devops` | Docker, CI/CD, infrastructure |
| `business` | Spreadsheets, reports, billing |
| `design` | UI/UX, design systems |
| `automation` | Web scraping, workflow automation |
| `research` | Search, summarization, analysis |
| `productivity` | Git, documentation, tooling |
| `content` | Writing, markdown, documentation |

---

## Questions

Open an issue on GitHub.
