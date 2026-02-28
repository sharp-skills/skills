---
name: argocd
description: Work with argocd — integrate, configure, and automate. Use when asked to set up argocd, use argocd API, integrate argocd into a project, troubleshoot argocd errors, or build argocd automation.
license: Apache-2.0
metadata:
  author: SharpSkills
  version: 1.0.0
  category: development
  tags: [argocd]
---

# Argocd Skill

## Quick Start

```bash
pip install argocd
```

```javascript
// Source: official — set ANTHROPIC_API_KEY to generate real patterns
const client = require('argocd');
```

## When to Use
Use this skill when asked to:
- Set up argocd
- Integrate argocd API
- Configure argocd authentication
- Troubleshoot argocd errors
- Build automation with argocd

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
- Docs: https://argocd.com/docs
- GitHub: https://github.com/argocd
