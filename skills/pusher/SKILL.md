---
name: pusher
description: Work with pusher — integrate, configure, and automate. Use when asked to set up pusher, use pusher API, integrate pusher into a project, troubleshoot pusher errors, or build pusher automation.
license: Apache-2.0
compatibility:
- node >= 16
metadata:
  author: SharpSkills
  version: 1.0.0
  category: development
  tags: [pusher, javascript, nodejs, npm]
---

# Pusher Skill

## Quick Start

```bash
pip install pusher
```

```javascript
// Source: official — set ANTHROPIC_API_KEY to generate real patterns
const client = require('pusher');
```

## When to Use
Use this skill when asked to:
- Set up pusher
- Integrate pusher API
- Configure pusher authentication
- Troubleshoot pusher errors
- Build automation with pusher

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
- Docs: https://pusher.com/docs
- GitHub: https://github.com/pusher
