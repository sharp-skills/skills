---
name: twilio-voice
description: Work with twilio-voice — integrate, configure, and automate. Use when asked to set up twilio-voice, use twilio-voice API, integrate twilio-voice into a project, troubleshoot twilio-voice errors, or build twilio-voice automation.
license: Apache-2.0
metadata:
  author: SharpSkills
  version: 1.0.0
  category: development
  tags: [twilio-voice]
---

# Twilio-Voice Skill

## Quick Start

```bash
npm install twilio-voice
```

```javascript
// Source: official — set ANTHROPIC_API_KEY to generate real patterns
const client = require('twilio-voice');
```

## When to Use
Use this skill when asked to:
- Set up twilio-voice
- Integrate twilio-voice API
- Configure twilio-voice authentication
- Troubleshoot twilio-voice errors
- Build automation with twilio-voice

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
- Docs: https://twilio-voice.com/docs
- GitHub: https://github.com/twilio-voice
