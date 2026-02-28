---
name: multer
description: Work with multer — integrate, configure, and automate. Use when asked to set up multer, use multer API, integrate multer into a project, troubleshoot multer errors, or build multer automation.
license: Apache-2.0
metadata:
  author: SharpSkills
  version: 1.0.0
  category: development
  tags: [multer]
---

# Multer Skill

## Quick Start

```bash
npm install multer
```

```javascript
// Source: official — set ANTHROPIC_API_KEY to generate real patterns
const client = require('multer');
```

## When to Use
Use this skill when asked to:
- Set up multer
- Integrate multer API
- Configure multer authentication
- Troubleshoot multer errors
- Build automation with multer

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
- Docs: https://multer.com/docs
- GitHub: https://github.com/multer
