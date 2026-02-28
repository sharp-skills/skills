---
name: nginx
description: Work with nginx — integrate, configure, and automate. Use when asked to set up nginx, use nginx API, integrate nginx into a project, troubleshoot nginx errors, or build nginx automation.
license: Apache-2.0
metadata:
  author: SharpSkills
  version: 1.0.0
  category: development
  tags: [nginx]
---

# Nginx Skill

## Quick Start

```bash
npm install nginx
```

```javascript
// Source: official — set ANTHROPIC_API_KEY to generate real patterns
const client = require('nginx');
```

## When to Use
Use this skill when asked to:
- Set up nginx
- Integrate nginx API
- Configure nginx authentication
- Troubleshoot nginx errors
- Build automation with nginx

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
- Docs: https://nginx.com/docs
- GitHub: https://github.com/nginx
