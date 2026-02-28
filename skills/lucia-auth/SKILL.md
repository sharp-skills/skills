---
name: lucia-auth
description: Work with lucia-auth — integrate, configure, and automate. Use when asked to set up lucia-auth, use lucia-auth API, integrate lucia-auth into a project, troubleshoot lucia-auth errors, or build lucia-auth automation.
license: Apache-2.0
compatibility:
- node >= 16
metadata:
  author: SharpSkills
  version: 1.0.0
  category: development
  tags: [lucia-auth, api, automation, integration, security, authentication]
---

# Lucia-Auth Skill

## Quick Start

```bash
npm install lucia-auth
```

```javascript
// Source: official — set ANTHROPIC_API_KEY to generate real patterns
const client = require('lucia-auth');
```

## When to Use
Use this skill when asked to:
- Set up lucia-auth
- Integrate lucia-auth API
- Configure lucia-auth authentication
- Troubleshoot lucia-auth errors
- Build automation with lucia-auth

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
- Docs: https://lucia-auth.com/docs
- GitHub: https://github.com/lucia-auth
