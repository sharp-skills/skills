---
name: pdf-lib
description: Work with pdf-lib — integrate, configure, and automate. Use when asked to set up pdf-lib, use pdf-lib API, integrate pdf-lib into a project, troubleshoot pdf-lib errors, or build pdf-lib automation.
license: Apache-2.0
metadata:
  author: SharpSkills
  version: 1.0.0
  category: development
  tags: [pdf-lib]
---

# Pdf-Lib Skill

## Quick Start

```bash
npm install pdf-lib
```

```javascript
// Source: official — set ANTHROPIC_API_KEY to generate real patterns
const client = require('pdf-lib');
```

## When to Use
Use this skill when asked to:
- Set up pdf-lib
- Integrate pdf-lib API
- Configure pdf-lib authentication
- Troubleshoot pdf-lib errors
- Build automation with pdf-lib

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
- Docs: https://pdf-lib.com/docs
- GitHub: https://github.com/pdf-lib
