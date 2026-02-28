---
name: helm
description: Work with helm — integrate, configure, and automate. Use when asked to set up helm, use helm API, integrate helm into a project, troubleshoot helm errors, or build helm automation.
license: Apache-2.0
compatibility:
- node >= 16
metadata:
  author: SharpSkills
  version: 1.0.0
  category: development
  tags: [helm, api, automation, integration]
---

# Helm Skill

## Quick Start

```bash
pip install helm
```

```javascript
// Source: official — set ANTHROPIC_API_KEY to generate real patterns
const client = require('helm');
```

## When to Use
Use this skill when asked to:
- Set up helm
- Integrate helm API
- Configure helm authentication
- Troubleshoot helm errors
- Build automation with helm

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
- Docs: https://helm.com/docs
- GitHub: https://github.com/helm
