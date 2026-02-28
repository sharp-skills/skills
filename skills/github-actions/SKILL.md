---
name: github-actions
description: Work with github-actions — integrate, configure, and automate. Use when asked to set up github-actions, use github-actions API, integrate github-actions into a project, troubleshoot github-actions errors, or build github-actions automation.
license: Apache-2.0
compatibility:
- node >= 16
metadata:
  author: SharpSkills
  version: 1.0.0
  category: development
  tags: [github-actions, api, automation, integration]
---

# Github-Actions Skill

## Quick Start

```bash
pip install github-actions
```

```javascript
// Source: official — set ANTHROPIC_API_KEY to generate real patterns
const client = require('github-actions');
```

## When to Use
Use this skill when asked to:
- Set up github-actions
- Integrate github-actions API
- Configure github-actions authentication
- Troubleshoot github-actions errors
- Build automation with github-actions

## Core Patterns

### Pattern 1: Basic Usage (Source: official)
```javascript
// TODO: Set ANTHROPIC_API_KEY for AI-generated patterns from official docs
```

## Production Notes

Set `ANTHROPIC_API_KEY` in `.env` for AI-generated production notes from real GitHub Issues data.

## Failure Modes
| Symptom | Root Cause | Fix |
|---------|-----------|-----|
| Auth error | Invalid API key | Check environment variable |
| Timeout | Network issue | Add retry with backoff |

## Pre-Deploy Checklist
- [ ] API key set in production environment
- [ ] Error handling on all API calls
- [ ] Rate limiting / retry logic added

## Resources
- Docs: https://github-actions.com/docs
- GitHub: https://github.com/github-actions
