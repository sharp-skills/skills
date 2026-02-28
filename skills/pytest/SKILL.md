---
name: pytest
description: Work with pytest — integrate, configure, and automate. Use when asked to set up pytest, use pytest API, integrate pytest into a project, troubleshoot pytest errors, or build pytest automation.
license: Apache-2.0
compatibility:
- python >= 3.9
metadata:
  author: SharpSkills
  version: 1.0.0
  category: development
  tags: [pytest, python, pip, testing, qa]
---

# Pytest Skill

## Quick Start

```bash
pip install pytest
```

```javascript
// Source: official — set ANTHROPIC_API_KEY to generate real patterns
const client = require('pytest');
```

## When to Use
Use this skill when asked to:
- Set up pytest
- Integrate pytest API
- Configure pytest authentication
- Troubleshoot pytest errors
- Build automation with pytest

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
- Docs: https://pytest.com/docs
- GitHub: https://github.com/pytest
