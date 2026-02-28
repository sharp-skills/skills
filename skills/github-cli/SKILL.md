---
name: github-cli
description: Work with github-cli — integrate, configure, and automate. Use when asked to set up github-cli, use github-cli API, integrate github-cli into a project, troubleshoot github-cli errors, or build github-cli automation.
license: Apache-2.0
compatibility:
- node >= 16
metadata:
  author: SharpSkills
  version: 1.0.0
  category: development
  tags: [github-cli, api, automation, integration]
---

# Github-Cli Skill

## Quick Start

```bash
pip install github-cli
```

```javascript
// Source: official — set ANTHROPIC_API_KEY to generate real patterns
const client = require('github-cli');
```

## When to Use
Use this skill when asked to:
- Set up github-cli
- Integrate github-cli API
- Configure github-cli authentication
- Troubleshoot github-cli errors
- Build automation with github-cli

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
- Docs: https://github-cli.com/docs
- GitHub: https://github.com/github-cli
