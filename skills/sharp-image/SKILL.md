---
name: sharp-image
description: Work with sharp-image — integrate, configure, and automate. Use when asked to set up sharp-image, use sharp-image API, integrate sharp-image into a project, troubleshoot sharp-image errors, or build sharp-image automation.
license: Apache-2.0
compatibility:
- node >= 16
metadata:
  author: SharpSkills
  version: 1.0.0
  category: development
  tags: [sharp-image, api, automation, integration]
---

# Sharp-Image Skill

## Quick Start

```bash
npm install sharp-image
```

```javascript
// Source: official — set ANTHROPIC_API_KEY to generate real patterns
const client = require('sharp-image');
```

## When to Use
Use this skill when asked to:
- Set up sharp-image
- Integrate sharp-image API
- Configure sharp-image authentication
- Troubleshoot sharp-image errors
- Build automation with sharp-image

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
- Docs: https://sharp-image.com/docs
- GitHub: https://github.com/sharp-image
