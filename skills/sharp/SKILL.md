---
name: sharp
description: Work with sharp — integrate, configure, and automate. Use when asked to set up sharp, use sharp API, integrate sharp into a project, troubleshoot sharp errors, or build sharp automation.
license: Apache-2.0
compatibility:
- node >= 16
metadata:
  author: SharpSkills
  version: 1.0.0
  category: development
  tags: [sharp, api, automation, integration]
---

# Sharp Skill

## Quick Start

```bash
pip install sharp
```

```javascript
// Source: official — set ANTHROPIC_API_KEY to generate real patterns
const client = require('sharp');
```

## When to Use
Use this skill when asked to:
- Set up sharp
- Integrate sharp API
- Configure sharp authentication
- Troubleshoot sharp errors
- Build automation with sharp

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
- Docs: https://sharp.com/docs
- GitHub: https://github.com/sharp
