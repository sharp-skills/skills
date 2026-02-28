---
name: jaeger
description: Work with jaeger — integrate, configure, and automate. Use when asked to set up jaeger, use jaeger API, integrate jaeger into a project, troubleshoot jaeger errors, or build jaeger automation.
license: Apache-2.0
metadata:
  author: SharpSkills
  version: 1.0.0
  category: development
  tags: [jaeger]
---

# Jaeger Skill

## Quick Start

```bash
pip install jaeger
```

```javascript
// Source: official — set ANTHROPIC_API_KEY to generate real patterns
const client = require('jaeger');
```

## When to Use
Use this skill when asked to:
- Set up jaeger
- Integrate jaeger API
- Configure jaeger authentication
- Troubleshoot jaeger errors
- Build automation with jaeger

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
- Docs: https://jaeger.com/docs
- GitHub: https://github.com/jaeger
