---
name: ffmpeg
description: Work with ffmpeg — integrate, configure, and automate. Use when asked to set up ffmpeg, use ffmpeg API, integrate ffmpeg into a project, troubleshoot ffmpeg errors, or build ffmpeg automation.
license: Apache-2.0
metadata:
  author: SharpSkills
  version: 1.0.0
  category: development
  tags: [ffmpeg]
---

# Ffmpeg Skill

## Quick Start

```bash
pip install ffmpeg
```

```javascript
// Source: official — set ANTHROPIC_API_KEY to generate real patterns
const client = require('ffmpeg');
```

## When to Use
Use this skill when asked to:
- Set up ffmpeg
- Integrate ffmpeg API
- Configure ffmpeg authentication
- Troubleshoot ffmpeg errors
- Build automation with ffmpeg

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
- Docs: https://ffmpeg.com/docs
- GitHub: https://github.com/ffmpeg
