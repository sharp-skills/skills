---
name: socket-io
description: Work with socket-io — integrate, configure, and automate. Use when asked to set up socket-io, use socket-io API, integrate socket-io into a project, troubleshoot socket-io errors, or build socket-io automation.
license: Apache-2.0
metadata:
  author: SharpSkills
  version: 1.0.0
  category: development
  tags: [socket-io]
---

# Socket-Io Skill

## Quick Start

```bash
npm install socket-io
```

```javascript
// Source: official — set ANTHROPIC_API_KEY to generate real patterns
const client = require('socket-io');
```

## When to Use
Use this skill when asked to:
- Set up socket-io
- Integrate socket-io API
- Configure socket-io authentication
- Troubleshoot socket-io errors
- Build automation with socket-io

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
- Docs: https://socket-io.com/docs
- GitHub: https://github.com/socket-io
