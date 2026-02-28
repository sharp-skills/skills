---
name: linear
description: Work with linear — integrate, configure, and automate. Use when asked to set up linear, use linear API, integrate linear into a project, troubleshoot linear errors, or build linear automation.
license: Apache-2.0
metadata:
  author: SharpSkills
  version: 1.0.0
  category: development
  tags: [linear]
---

# Linear Skill

## Quick Start

```bash
pip install linear
```

```javascript
// Source: official — set ANTHROPIC_API_KEY to generate real patterns
const client = require('linear');
```

## When to Use
Use this skill when asked to:
- Set up linear
- Integrate linear API
- Configure linear authentication
- Troubleshoot linear errors
- Build automation with linear

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
- Docs: https://linear.com/docs
- GitHub: https://github.com/linear
