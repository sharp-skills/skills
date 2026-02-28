---
name: twilio-sms
description: Work with twilio-sms — integrate, configure, and automate. Use when asked to set up twilio-sms, use twilio-sms API, integrate twilio-sms into a project, troubleshoot twilio-sms errors, or build twilio-sms automation.
license: Apache-2.0
metadata:
  author: SharpSkills
  version: 1.0.0
  category: development
  tags: [twilio-sms]
---

# Twilio-Sms Skill

## Quick Start

```bash
npm install twilio-sms
```

```javascript
// Source: official — set ANTHROPIC_API_KEY to generate real patterns
const client = require('twilio-sms');
```

## When to Use
Use this skill when asked to:
- Set up twilio-sms
- Integrate twilio-sms API
- Configure twilio-sms authentication
- Troubleshoot twilio-sms errors
- Build automation with twilio-sms

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
- Docs: https://twilio-sms.com/docs
- GitHub: https://github.com/twilio-sms
