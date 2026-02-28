---
name: nextauth
description: Work with nextauth — integrate, configure, and automate. Use when asked to set up nextauth, use nextauth API, integrate nextauth into a project, troubleshoot nextauth errors, or build nextauth automation.
license: Apache-2.0
metadata:
  author: SharpSkills
  version: 1.0.0
  category: development
  tags: [nextauth]
---

# Nextauth Skill

## Quick Start

```bash
npm install nextauth
```

```javascript
// Source: official — set ANTHROPIC_API_KEY to generate real patterns
const client = require('nextauth');
```

## When to Use
Use this skill when asked to:
- Set up nextauth
- Integrate nextauth API
- Configure nextauth authentication
- Troubleshoot nextauth errors
- Build automation with nextauth

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
- Docs: https://nextauth.com/docs
- GitHub: https://github.com/nextauth
