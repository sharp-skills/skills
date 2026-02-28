---
name: nodemailer
description: Work with nodemailer — integrate, configure, and automate. Use when asked to set up nodemailer, use nodemailer API, integrate nodemailer into a project, troubleshoot nodemailer errors, or build nodemailer automation.
license: Apache-2.0
metadata:
  author: SharpSkills
  version: 1.0.0
  category: development
  tags: [nodemailer]
---

# Nodemailer Skill

## Quick Start

```bash
npm install nodemailer
```

```javascript
// Source: official — set ANTHROPIC_API_KEY to generate real patterns
const client = require('nodemailer');
```

## When to Use
Use this skill when asked to:
- Set up nodemailer
- Integrate nodemailer API
- Configure nodemailer authentication
- Troubleshoot nodemailer errors
- Build automation with nodemailer

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
- Docs: https://nodemailer.com/docs
- GitHub: https://github.com/nodemailer
