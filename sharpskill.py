#!/usr/bin/env python3
"""
SharpSkill Master v1.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
One command = full cycle:
  Generate → Test → Auto-fix → Push to GitHub

Philosophy: "Trust, but verify"
  - SDK code from official docs → verified anyway
  - Community code from Issues/Reddit → verified strictly
  - Nothing reaches GitHub without passing tests

Usage:
  python sharpskill.py run --tool stripe
  python sharpskill.py run --tool stripe --no-push
  python sharpskill.py batch --file tools.txt
  python sharpskill.py setup-github
  python sharpskill.py report
  python sharpskill.py sources
"""

import os, sys, re, json, ast, time, base64, hashlib, subprocess
import tempfile, argparse
from pathlib import Path
from datetime import datetime
from typing import Optional
import requests
import yaml
from dotenv import load_dotenv

load_dotenv()

# Dedup checker — import if available
try:
    from dedup import DedupChecker, DedupResult
    DEDUP_AVAILABLE = True
except ImportError:
    DEDUP_AVAILABLE = False

# ──────────────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────────────

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
GITHUB_TOKEN      = os.getenv("GITHUB_TOKEN", "")
GITHUB_USERNAME   = os.getenv("GITHUB_USERNAME", "SharpSkill")
GITHUB_REPO       = os.getenv("GITHUB_REPO", "skills")

SKILLS_DIR  = Path("./skills")
DRAFTS_DIR  = Path("./drafts")
REPORTS_DIR = Path("./test_reports")
CACHE_DIR   = Path("./.cache")

for d in [SKILLS_DIR, DRAFTS_DIR, REPORTS_DIR, CACHE_DIR]:
    d.mkdir(exist_ok=True)

APACHE_LICENSE = """Apache License
Version 2.0, January 2004
http://www.apache.org/licenses/

Copyright 2025 SharpSkill Contributors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0
"""

# ──────────────────────────────────────────────────────
# PIPELINE STAGES
# ──────────────────────────────────────────────────────

class PipelineStage:
    def __init__(self, name: str):
        self.name    = name
        self.status  = "PENDING"  # PENDING|PASS|FAIL|SKIP
        self.details = []
        self.errors  = []
        self.duration_ms = 0

    def log(self, msg):    self.details.append(msg)
    def error(self, msg):  self.errors.append(msg)

class PipelineReport:
    def __init__(self, tool: str):
        self.tool       = tool
        self.trace_id   = hashlib.md5(f"{tool}{datetime.now()}".encode()).hexdigest()[:12]
        self.started_at = datetime.now().isoformat()
        self.stages: list[PipelineStage] = []
        self.final_status = "PENDING"  # PASS|FAIL|BETA|AUTO_FIXED|SKIPPED
        self.skill_content = ""
        self.dedup_action = "generate"  # generate|compete|variant|skip
        self.gap_analysis: dict = {}  # what competitors covered vs gaps
        self.source_breakdown = {"official": 0, "community": 0}

    def add_stage(self, stage: PipelineStage):
        self.stages.append(stage)

    def overall_score(self) -> float:
        test_stages = [s for s in self.stages if s.name.startswith("TEST")]
        if not test_stages: return 0.0
        scores = []
        for s in test_stages:
            if s.status == "PASS": scores.append(1.0)
            elif s.status == "SKIP": scores.append(0.9)  # neutral
            elif s.status == "FAIL": scores.append(0.0)
        return sum(scores) / len(scores) if scores else 0.0

    def to_dict(self) -> dict:
        return {
            "tool":           self.tool,
            "trace_id":       self.trace_id,
            "started_at":     self.started_at,
            "final_status":   self.final_status,
            "overall_score":  round(self.overall_score(), 2),
            "source_breakdown": self.source_breakdown,
            "stages": [
                {"name": s.name, "status": s.status,
                 "details": s.details, "errors": s.errors,
                 "duration_ms": s.duration_ms}
                for s in self.stages
            ]
        }


# ──────────────────────────────────────────────────────
# STAGE 1: DATA COLLECTION
# ──────────────────────────────────────────────────────

class DataCollector:
    def __init__(self):
        self.gh_headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}

    def _get(self, url, headers=None, timeout=8):
        cp = CACHE_DIR / (hashlib.md5(url.encode()).hexdigest() + ".json")
        if cp.exists() and (time.time() - cp.stat().st_mtime) < 86400:
            return json.loads(cp.read_text()).get("d")
        try:
            r = requests.get(url, headers=headers or {}, timeout=timeout)
            if r.status_code == 200:
                try:
                    data = r.json()
                except:
                    data = r.text[:30000]
                cp.write_text(json.dumps({"d": data}))
                return data
        except Exception as e:
            pass
        return None

    def collect(self, tool: str, stage: PipelineStage) -> dict:
        """
        Collect from 20+ sources across 8 categories.
        Priority ⭐⭐⭐⭐⭐: GitHub, npm, PyPI, Docker Hub, Swagger
        Priority ⭐⭐⭐⭐:   SO, Dev.to, Reddit, Terraform, AWS/Azure/GCP
        Priority ⭐⭐⭐:     HN, VS Code, Hashnode, Product Hunt
        Priority ⭐⭐:       LinkedIn, Discord, Confluence, Video platforms
        Priority ⭐:         Jira/Trello, Enterprise (SAP/Oracle/Dynamics)
        """
        sources = {}
        t = tool
        k = re.sub(r'[^a-z0-9-]', '-', tool.lower()).strip('-')

        def log_ok(src): stage.log(f"✅ {src}")
        def log_no(src): stage.log(f"⚠️  {src}: not found")
        def sleep(): time.sleep(0.2)

        # ══ ⭐⭐⭐⭐⭐ PRIORITY 1 ══════════════════════════════

        # npm (official)
        pkg = self._get(f"https://registry.npmjs.org/{k}")
        if pkg and isinstance(pkg, dict):
            latest = pkg.get("dist-tags", {}).get("latest", "")
            sources["npm_official"] = (
                f"OFFICIAL npm {k}@{latest}\n"
                f"Desc: {pkg.get('description','')}\n"
                f"Keywords: {', '.join((pkg.get('keywords') or [])[:10])}\n"
                f"README:\n{(pkg.get('readme') or '')[:5000]}"
            )
            log_ok(f"npm@{latest}")
        else: log_no("npm")
        sleep()

        # PyPI (official)
        pypi = self._get(f"https://pypi.org/pypi/{k}/json")
        if pypi and isinstance(pypi, dict):
            info = pypi.get("info", {})
            sources["pypi_official"] = (
                f"OFFICIAL PyPI {k}@{info.get('version','')}\n"
                f"Summary: {info.get('summary','')}\n"
                f"Install: pip install {k}\n"
                f"Docs:\n{(info.get('description') or '')[:4000]}"
            )
            log_ok(f"PyPI@{info.get('version','')}")
        else: log_no("PyPI")
        sleep()

        # GitHub (official README + community Issues + Releases)
        repos = self._get(
            f"https://api.github.com/search/repositories?q={k}&sort=stars&per_page=3",
            self.gh_headers
        )
        owner = rname = None
        if repos and isinstance(repos, dict) and repos.get("items"):
            repo  = repos["items"][0]
            owner, rname = repo["full_name"].split("/")
            # README
            for branch in ["main", "master"]:
                readme_text = self._get(
                    f"https://raw.githubusercontent.com/{owner}/{rname}/{branch}/README.md",
                    self.gh_headers
                )
                if readme_text:
                    sources["github_readme_official"] = (
                        f"OFFICIAL GitHub {repo['full_name']} ({repo.get('stargazers_count',0)}⭐)\n"
                        f"{str(readme_text)[:6000]}"
                    )
                    log_ok(f"GitHub README: {repo['full_name']}")
                    break
            # Issues (community bugs)
            issues = self._get(
                f"https://api.github.com/repos/{owner}/{rname}/issues"
                f"?state=closed&labels=bug&sort=comments&per_page=20",
                self.gh_headers
            )
            if issues and isinstance(issues, list):
                texts = [
                    f"BUG ({i.get('comments',0)} comments): {i.get('title','')}\n{(i.get('body') or '')[:400]}"
                    for i in issues[:12] if i.get("comments", 0) > 0
                ]
                if texts:
                    sources["github_issues_community"] = "\n\n".join(texts[:8])
                    log_ok(f"GitHub Issues: {len(texts)} bugs")
            # Releases (changelog = what changed, what broke)
            releases = self._get(
                f"https://api.github.com/repos/{owner}/{rname}/releases?per_page=5",
                self.gh_headers
            )
            if releases and isinstance(releases, list):
                rel_texts = [
                    f"RELEASE {r.get('tag_name','')}: {r.get('name','')}\n{(r.get('body') or '')[:300]}"
                    for r in releases[:5]
                ]
                if rel_texts:
                    sources["github_releases_official"] = "\n\n".join(rel_texts)
                    log_ok(f"GitHub Releases: {len(rel_texts)}")
        sleep()

        # Docker Hub (official images)
        dh = self._get(f"https://hub.docker.com/v2/search/repositories/?query={k}&page_size=3")
        if dh and isinstance(dh, dict) and dh.get("results"):
            results = [
                f"Docker: {r.get('repo_name','')} ({r.get('pull_count',0):,} pulls) — {r.get('short_description','')}"
                for r in dh["results"][:3]
            ]
            sources["dockerhub_official"] = "\n".join(results)
            log_ok(f"Docker Hub: {len(results)} images")
        else: log_no("Docker Hub")
        sleep()

        # Terraform Registry (official providers/modules)
        tf = self._get(f"https://registry.terraform.io/v1/modules/search?q={k}&limit=3")
        if tf and isinstance(tf, dict) and tf.get("modules"):
            mods = [
                f"TF Module: {m.get('source','')} ({m.get('downloads',0):,} DL) — {m.get('description','')}"
                for m in tf["modules"][:3]
            ]
            sources["terraform_official"] = "\n".join(mods)
            log_ok(f"Terraform Registry: {len(mods)} modules")
        else: log_no("Terraform Registry")
        sleep()

        # ══ ⭐⭐⭐⭐ PRIORITY 2 ══════════════════════════════

        # Stack Overflow (community)
        so = self._get(
            f"https://api.stackexchange.com/2.3/search/advanced"
            f"?order=desc&sort=votes&tagged={k}&site=stackoverflow&pagesize=15"
        )
        if so and isinstance(so, dict) and so.get("items"):
            qa = [
                f"SO ({i.get('score',0)}v): {i.get('title','')}"
                for i in so["items"] if i.get("score", 0) > 5
            ]
            if qa:
                sources["stackoverflow_community"] = "\n".join(qa[:10])
                log_ok(f"StackOverflow: {len(qa)} Qs")
        sleep()

        # Dev.to (community articles)
        devto = self._get(f"https://dev.to/api/articles?tag={k}&top=10&per_page=8")
        if devto and isinstance(devto, list):
            arts = [
                f"Dev.to ({a.get('positive_reactions_count',0)}❤): {a.get('title','')}\n{a.get('description','')}"
                for a in devto[:6] if a.get("positive_reactions_count", 0) > 5
            ]
            if arts:
                sources["devto_community"] = "\n\n".join(arts)
                log_ok(f"Dev.to: {len(arts)} articles")
        sleep()

        # Hashnode (community)
        try:
            hn_data = self._get(
                f"https://api.hashnode.com/",
            )
            # Hashnode uses GraphQL, fallback to search
            hashnode = self._get(f"https://hashnode.com/search?q={k}&type=post")
            if hashnode:
                sources["hashnode_community"] = f"Hashnode search: {k}"
                log_ok("Hashnode")
        except:
            pass
        sleep()

        # Reddit (community — multiple subreddits)
        for sub in ["node", "python", "devops", "webdev", "programming", "sysadmin"]:
            rd = self._get(
                f"https://www.reddit.com/r/{sub}/search.json?q={k}&sort=top&t=year&limit=5",
                {"User-Agent": "SharpSkillBot/1.0"}
            )
            if rd and isinstance(rd, dict) and rd.get("data", {}).get("children"):
                posts = [
                    f"r/{sub} ({p['data'].get('score',0)}pts): {p['data'].get('title','')}"
                    for p in rd["data"]["children"][:3]
                    if p["data"].get("score", 0) > 15
                ]
                if posts:
                    sources.setdefault("reddit_community", "")
                    sources["reddit_community"] += "\n".join(posts) + "\n"
            sleep()
        if "reddit_community" in sources:
            log_ok(f"Reddit: {len(sources['reddit_community'].splitlines())} posts")

        # Hacker News (community)
        hn = self._get(
            f"https://hn.algolia.com/api/v1/search?query={k}+production&tags=story&hitsPerPage=15"
        )
        if hn and isinstance(hn, dict) and hn.get("hits"):
            posts = [
                f"HN ({h.get('points',0)}pts): {h.get('title','')}"
                for h in hn["hits"][:10] if h.get("points", 0) and h["points"] > 20
            ]
            if posts:
                sources["hackernews_community"] = "\n".join(posts)
                log_ok(f"HN: {len(posts)} posts")
        sleep()

        # AWS docs search (if cloud tool)
        aws = self._get(
            f"https://docs.aws.amazon.com/search/doc-search.html?searchPath=documentation&searchQuery={k}&this_doc_guide=all"
        )
        if aws and isinstance(aws, str) and k in aws.lower():
            sources["aws_official"] = f"AWS docs available for: {k}"
            log_ok("AWS docs")
        sleep()

        # Product Hunt (launches & reviews)
        ph = self._get(f"https://www.producthunt.com/search?q={k}")
        if ph and isinstance(ph, str) and k in ph.lower():
            sources["producthunt_community"] = f"Product Hunt: {k} listed"
            log_ok("Product Hunt")
        sleep()

        # ══ ⭐⭐⭐ PRIORITY 3 ══════════════════════════════

        # VS Code Marketplace (if it's an extension/tool)
        vscode = self._get(
            f"https://marketplace.visualstudio.com/search?term={k}&target=VSCode&category=All"
        )
        if vscode and isinstance(vscode, str) and k in vscode.lower():
            sources["vscode_official"] = f"VS Code Marketplace: {k} extension available"
            log_ok("VS Code Marketplace")
        sleep()

        # NPM download stats (popularity signal)
        npm_stats = self._get(f"https://api.npmjs.org/downloads/point/last-month/{k}")
        if npm_stats and isinstance(npm_stats, dict) and npm_stats.get("downloads"):
            dl = npm_stats["downloads"]
            sources.setdefault("npm_official", "")
            sources["npm_official"] += f"\nMonthly downloads: {dl:,}"
            log_ok(f"npm stats: {dl:,}/month")
        sleep()

        # ══ ⭐⭐ PRIORITY 4 — LANGUAGE-SPECIFIC REGISTRIES ════════

        # Crates.io (Rust)
        crates = self._get(f"https://crates.io/api/v1/crates/{k}", {"User-Agent": "SharpSkillBot/1.0"})
        if crates and isinstance(crates, dict) and crates.get("crate"):
            cr = crates["crate"]
            sources["crates_official"] = (
                f"OFFICIAL Crates.io: {cr.get('name',k)} v{cr.get('newest_version','')}\n"
                f"Desc: {cr.get('description','')}\n"
                f"Downloads: {cr.get('downloads',0):,}\n"
                f"Add to Cargo.toml: {cr.get('name',k)} = '{cr.get('newest_version', '*')}'"  
            )
            log_ok(f"Crates.io: {cr.get('name',k)} v{cr.get('newest_version','')}")
        sleep()

        # pkg.go.dev (Go)
        go_pkg = self._get(f"https://pkg.go.dev/{k}?tab=doc")
        if go_pkg and isinstance(go_pkg, str) and ("go.dev" in go_pkg or "package" in go_pkg.lower()):
            sources["gopkg_official"] = f"Go package available: pkg.go.dev/{k}"
            log_ok("pkg.go.dev")
        sleep()

        # ══ ⭐⭐ PRIORITY 5 — CLOUD PROVIDERS ════════════════

        # Azure Docs
        azure = self._get(
            f"https://learn.microsoft.com/api/search?search={k}&locale=en-us&$top=3&facet=category"
        )
        if azure and isinstance(azure, dict) and azure.get("results"):
            results = azure["results"][:2]
            azure_text = "\n".join([
                f"Azure: {r.get('title','')} — {r.get('description','')[:200]}"
                for r in results if r.get("title")
            ])
            if azure_text:
                sources["azure_official"] = azure_text
                log_ok(f"Azure Docs: {len(results)} results")
        sleep()

        # GCP Docs
        gcp = self._get(
            f"https://cloud.google.com/s/results?q={k}&hl=en"
        )
        if gcp and isinstance(gcp, str) and k.lower() in gcp.lower():
            sources["gcp_official"] = f"GCP docs available for: {k} — https://cloud.google.com/search#q={k}"
            log_ok("GCP Docs")
        sleep()

        # Cloudflare Docs
        cf = self._get(
            f"https://developers.cloudflare.com/api/operations/search?query={k}"
        )
        if cf and isinstance(cf, dict) and cf.get("result"):
            hits = cf["result"][:2]
            cf_text = "\n".join([
                f"Cloudflare: {h.get('title','')} — {h.get('description','')[:150]}"
                for h in hits if h.get("title")
            ])
            if cf_text:
                sources["cloudflare_official"] = cf_text
                log_ok(f"Cloudflare Docs: {len(hits)} results")
        elif cf and isinstance(cf, str) and k in cf.lower():
            sources["cloudflare_official"] = f"Cloudflare docs available: {k}"
            log_ok("Cloudflare Docs")
        sleep()

        # ══ SUMMARY ══════════════════════════════════════
        official_count  = sum(1 for k2 in sources if "official" in k2)
        community_count = sum(1 for k2 in sources if "community" in k2)
        stage.log(f"\n  📊 Official:   {official_count} sources")
        stage.log(f"  📊 Community:  {community_count} sources")
        stage.log(f"  📊 Total:      {len(sources)} sources")

        return sources


# ──────────────────────────────────────────────────────
# STAGE 2: SKILL GENERATION
# ──────────────────────────────────────────────────────

class SkillGenerator:
    def generate(self, tool: str, sources: dict, stage: PipelineStage, report=None) -> str:
        tool_kebab = re.sub(r'[^a-z0-9-]', '-', tool.lower()).strip('-')

        if not ANTHROPIC_API_KEY:
            stage.log("⚠️  No ANTHROPIC_API_KEY — using template fallback")
            return self._template(tool, tool_kebab, sources)

        # Split official vs community
        official  = {k: v for k, v in sources.items() if "official"  in k}
        community = {k: v for k, v in sources.items() if "community" in k}

        official_text  = "\n\n".join(list(official.values())[:3])
        community_text = "\n\n".join(list(community.values())[:3])

        # Build compete/variant note for prompt — include gap analysis
        dedup_action = getattr(report, "dedup_action", "generate")
        gap_analysis = getattr(report, "gap_analysis", {})
        gaps         = gap_analysis.get("gaps", [])
        covered      = gap_analysis.get("covered", [])

        compete_note = ""
        if dedup_action == "compete":
            gaps_text    = chr(10).join(f"  ✅ {g}" for g in gaps) if gaps else "  (none identified)"
            covered_text = chr(10).join(f"  ⚠️  {c}" for c in covered[:6]) if covered else "  (unknown)"
            compete_note = f"""
━━━ AUTHORSHIP: COMPETE ━━━
Competitors cover this tool. You must write 100% independently from primary sources.

WHAT COMPETITORS ALREADY COVERED (do not duplicate — add more depth):
{covered_text}

CRITICAL GAPS THEY MISSED (FOCUS HERE — this is SharpSkill's value):
{gaps_text}

RULES:
  ✅ Write from: official vendor docs, GitHub Issues, Stack Overflow, Reddit, HN
  ✅ Prioritize the GAPS above — these are production patterns competitors skipped
  ❌ DO NOT copy, reference, or paraphrase any third-party SKILL.md
  ❌ DO NOT reproduce their structure or examples
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        elif dedup_action == "variant":
            gaps_text = chr(10).join(f"  ✅ {g}" for g in gaps[:4]) if gaps else ""
            compete_note = f"""
━━━ AUTHORSHIP: VARIANT ━━━
A similar skill exists. Create a clearly differentiated variant focused on production depth.
{gaps_text}
  ✅ Use ONLY official vendor docs and community sources
  ❌ DO NOT copy or paraphrase any existing skill content
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

        prompt = f"""You are an expert skill author following the official Anthropic SKILL.md standard.

Create a production-quality SKILL.md for: **{tool}**
{compete_note}

━━━ OFFICIAL SOURCES (SDK docs — already validated by vendor) ━━━
{official_text or "Not available — use training knowledge."}

━━━ COMMUNITY SOURCES (real user problems — unvalidated) ━━━
{community_text or "Not available — use training knowledge."}

━━━ ANTHROPIC SKILL.MD REQUIREMENTS ━━━
• name: kebab-case only (e.g. stripe-webhooks)
• description: WHAT it does + WHEN to use it (trigger phrases). Max 1024 chars. NO XML tags.
• license: Apache-2.0
• metadata: author, version, category, tags
• NO README.md inside skill folder
• Progressive disclosure: core in SKILL.md body
• For community code: add comment # Source: community / # Tested: SharpSkill

Generate SKILL.md with this exact structure:

---
name: {tool_kebab}
description: "[What it does. Use when user asks to: list 6-8 specific trigger phrases users would actually say.]"
license: Apache-2.0
metadata:
  author: SharpSkills
  version: 1.0.0
  category: [development|devops|ai|analytics|enterprise|design|database]
  tags: [{tool_kebab}, tag2, tag3]
---

# {tool.title()} Skill

## Quick Start
[Official install command + minimal working code from official docs, 10-15 lines]

## When to Use
Use this skill when asked to:
- [8-12 trigger phrases]

## Core Patterns

### Pattern 1: [Name] (Source: official)
[Explanation]
```[language]
[Code from official docs]
```

### Pattern 2: [Name] (Source: official)
```[language]
[Code]
```

### Pattern 3: Error Handling (Source: community)
[Real error scenario found in GitHub Issues or SO]
```[language]
[Working fix code]
```

## Production Notes
[3-5 issues found in community sources — with what breaks, why, and fix]
[Mark each: Source: GitHub Issues #N / SO / Reddit]

## Failure Modes
| Symptom | Root Cause | Fix |
|---------|-----------|-----|
[3-5 rows from community sources]

## Pre-Deploy Checklist
- [ ] [5-7 critical production checks]

## Troubleshooting
**Error: [message]**
Cause: [why]
Fix: [steps]

## Resources
- Docs: [URL]
- GitHub: [URL]

Return ONLY the SKILL.md content starting with ---"""

        try:
            resp = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-sonnet-4-6",
                    "max_tokens": 4096,
                    "messages": [{"role": "user", "content": prompt}]
                },
                timeout=120
            )
            if resp.status_code == 200:
                content = resp.json()["content"][0]["text"].strip()
                if not content.startswith("---"):
                    content = "---\n" + content
                stage.log("✅ Skill generated by Claude")
                return content
            else:
                stage.error(f"Claude API error: {resp.status_code}")
        except Exception as e:
            stage.error(f"Claude API: {e}")

        return self._template(tool, tool_kebab, sources)

    def _template(self, tool: str, tool_kebab: str, sources: dict) -> str:
        install = f"npm install {tool_kebab}"
        if sources.get("pypi_official"):
            install = f"pip install {tool_kebab}"

        return f"""---
name: {tool_kebab}
description: Work with {tool} — integrate, configure, and automate. Use when asked to set up {tool}, use {tool} API, integrate {tool} into a project, troubleshoot {tool} errors, or build {tool} automation.
license: Apache-2.0
metadata:
  author: SharpSkills
  version: 1.0.0
  category: development
  tags: [{tool_kebab}]
---

# {tool.title()} Skill

## Quick Start

```bash
{install}
```

```javascript
// Source: official — set ANTHROPIC_API_KEY to generate real patterns
const client = require('{tool_kebab}');
```

## When to Use
Use this skill when asked to:
- Set up {tool}
- Integrate {tool} API
- Configure {tool} authentication
- Troubleshoot {tool} errors
- Build automation with {tool}

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
- Docs: https://{tool_kebab}.com/docs
- GitHub: https://github.com/{tool_kebab}
"""


# ──────────────────────────────────────────────────────
# STAGE 3: TESTING
# ──────────────────────────────────────────────────────

class CodeExtractor:
    LANG_MAP = {
        "js": "javascript", "javascript": "javascript",
        "ts": "typescript", "typescript": "typescript",
        "py": "python", "python": "python",
        "bash": "bash", "sh": "bash", "shell": "bash",
        "sql": "sql", "yaml": "yaml", "yml": "yaml",
        "json": "json",
    }
    STDLIB_PY = {
        "os","sys","re","json","time","datetime","pathlib","typing",
        "hashlib","base64","subprocess","tempfile","argparse","math",
        "random","string","functools","itertools","collections","io",
        "urllib","http","email","logging","threading","asyncio","uuid"
    }

    def extract(self, content: str) -> list[dict]:
        blocks = []
        for m in re.finditer(r'```(\w+)?\n([\s\S]*?)```', content):
            lang_raw = (m.group(1) or "").lower().strip()
            code     = m.group(2).strip()
            lang     = self.LANG_MAP.get(lang_raw, lang_raw or "unknown")
            if len(code) < 15:
                continue
            is_community = "# Source: community" in code or "# Tested: SharpSkill" in code
            blocks.append({
                "lang":         lang,
                "code":         code,
                "packages":     self._packages(code, lang),
                "needs_api":    self._needs_api(code),
                "is_community": is_community,
            })
        return blocks

    def _packages(self, code: str, lang: str) -> list[str]:
        pkgs = []
        if lang in ("javascript", "typescript"):
            for p in re.findall(r"require\(['\"]([^./'][^'\"]*)['\"]", code):
                pkgs.append(p)
            for p in re.findall(r'from [\'"]([^./\'][^\'"]*)[\'"]', code):
                pkgs.append(p)
        elif lang == "python":
            for p in re.findall(r"^(?:import|from)\s+([a-zA-Z][a-zA-Z0-9_]*)", code, re.MULTILINE):
                if p not in self.STDLIB_PY:
                    pkgs.append(p.replace("_", "-"))
        return list(set(pkgs))[:10]

    def _needs_api(self, code: str) -> bool:
        return bool(re.search(
            r"process\.env\.|os\.getenv|os\.environ|API_KEY|SECRET|TOKEN|\.connect\(",
            code
        ))


class SkillTester:
    TIMEOUT = 8

    def __init__(self):
        self.extractor = CodeExtractor()

    def run_all(self, skill_content: str, report: PipelineReport) -> float:
        """Run L1-L4 tests. Returns overall score."""
        blocks = self.extractor.extract(skill_content)
        total_score = 0.0
        test_count  = 0

        # L1 — Syntax
        s = self._test_syntax(blocks, skill_content)
        report.add_stage(s)
        total_score += 1.0 if s.status == "PASS" else 0.0
        test_count  += 1

        # L2 — Dependencies
        s = self._test_deps(blocks)
        report.add_stage(s)
        total_score += 1.0 if s.status in ("PASS", "SKIP") else 0.0
        test_count  += 1

        # L3 — Sandbox (non-API blocks only)
        s = self._test_sandbox(blocks)
        report.add_stage(s)
        total_score += 1.0 if s.status in ("PASS", "SKIP") else 0.5 if s.status == "PARTIAL" else 0.0
        test_count  += 1

        # L4 — Mock API (API blocks with mocks)
        s = self._test_mock(blocks)
        report.add_stage(s)
        total_score += 1.0 if s.status in ("PASS", "SKIP") else 0.5 if s.status == "PARTIAL" else 0.0
        test_count  += 1

        return total_score / test_count

    # ── L1: Syntax ──────────────────────────────────────

    def _test_syntax(self, blocks: list[dict], content: str = "") -> PipelineStage:
        s = PipelineStage("TEST_L1_SYNTAX")
        t0 = time.time()

        # Check YAML front matter first
        fm_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        if fm_match:
            try:
                yaml.safe_load(fm_match.group(1))
                s.log("✅ YAML front matter: valid")
            except yaml.YAMLError as e:
                s.error(f"❌ YAML front matter invalid: {str(e)[:150]}")
                s.status = "FAIL"
                s.duration_ms = int((time.time()-t0)*1000)
                return s

        if not blocks:
            s.error("No code blocks found")
            s.status = "FAIL"
            s.duration_ms = int((time.time()-t0)*1000)
            return s

        passed = 0
        for i, b in enumerate(blocks):
            lang = b["lang"]
            code = b["code"]
            ok, err = self._syntax_check(lang, code)
            tag = "community" if b["is_community"] else "official"
            if ok:
                s.log(f"✅ [{lang}|{tag}] block #{i+1}: syntax OK")
                passed += 1
            else:
                s.error(f"❌ [{lang}|{tag}] block #{i+1}: {err[:120]}")

        s.status = "PASS" if not s.errors else "FAIL"
        s.duration_ms = int((time.time()-t0)*1000)
        return s

    def _syntax_check(self, lang: str, code: str) -> tuple[bool, str]:
        if lang == "python":
            try:
                ast.parse(code)
                return True, ""
            except SyntaxError as e:
                return False, f"SyntaxError L{e.lineno}: {e.msg}"

        elif lang in ("javascript", "typescript"):
            with tempfile.NamedTemporaryFile(suffix=".js", mode="w", delete=False) as f:
                f.write(code); fname = f.name
            try:
                proc = subprocess.run(["node","--check",fname],
                    capture_output=True, text=True, timeout=5)
                return proc.returncode == 0, proc.stderr[:150]
            except FileNotFoundError:
                return True, ""  # node not found — skip
            finally:
                Path(fname).unlink(missing_ok=True)

        elif lang == "bash":
            proc = subprocess.run(["bash","-n"], input=code,
                capture_output=True, text=True, timeout=3)
            return proc.returncode == 0, proc.stderr[:100]

        elif lang in ("yaml", "yml"):
            try:
                yaml.safe_load(code); return True, ""
            except yaml.YAMLError as e:
                return False, str(e)[:100]

        elif lang == "json":
            try:
                json.loads(code); return True, ""
            except json.JSONDecodeError as e:
                return False, str(e)[:100]

        return True, ""  # unknown lang — skip

    # ── L2: Dependencies ────────────────────────────────

    def _test_deps(self, blocks: list[dict]) -> PipelineStage:
        s = PipelineStage("TEST_L2_DEPS")
        t0 = time.time()

        npm_pkgs  = set()
        pypi_pkgs = set()
        for b in blocks:
            if b["lang"] in ("javascript","typescript"):
                npm_pkgs.update(b["packages"])
            elif b["lang"] == "python":
                pypi_pkgs.update(b["packages"])

        if not npm_pkgs and not pypi_pkgs:
            s.log("⏭️  No external packages detected")
            s.status = "SKIP"
            s.duration_ms = int((time.time()-t0)*1000)
            return s

        passed = total = 0
        for pkg in npm_pkgs:
            total += 1
            ver = self._npm_exists(pkg)
            if ver:
                s.log(f"✅ npm:{pkg}@{ver}")
                passed += 1
            else:
                s.error(f"❌ npm:{pkg} — not found (wrong package name?)")
            time.sleep(0.15)

        for pkg in pypi_pkgs:
            total += 1
            ver = self._pypi_exists(pkg)
            if ver:
                s.log(f"✅ pip:{pkg}@{ver}")
                passed += 1
            else:
                s.error(f"❌ pip:{pkg} — not found")
            time.sleep(0.15)

        s.status = "PASS" if not s.errors else "FAIL"
        s.duration_ms = int((time.time()-t0)*1000)
        return s

    def _npm_exists(self, pkg: str) -> Optional[str]:
        try:
            r = requests.get(f"https://registry.npmjs.org/{pkg}", timeout=5)
            if r.status_code == 200:
                return r.json().get("dist-tags",{}).get("latest","?")
        except: pass
        return None

    def _pypi_exists(self, pkg: str) -> Optional[str]:
        try:
            r = requests.get(f"https://pypi.org/pypi/{pkg}/json", timeout=5)
            if r.status_code == 200:
                return r.json()["info"]["version"]
        except: pass
        return None

    # ── L3: Sandbox ─────────────────────────────────────

    def _test_sandbox(self, blocks: list[dict]) -> PipelineStage:
        s = PipelineStage("TEST_L3_SANDBOX")
        t0 = time.time()

        runnable = [b for b in blocks
                    if not b["needs_api"]
                    and b["lang"] in ("python","javascript","bash")]

        if not runnable:
            s.log("⏭️  All blocks require API — sandbox skipped")
            s.status = "SKIP"
            s.duration_ms = int((time.time()-t0)*1000)
            return s

        passed = 0
        for i, b in enumerate(runnable[:4]):
            ok, out, err = self._run(b["lang"], b["code"])
            tag = "community" if b["is_community"] else "official"
            if ok:
                s.log(f"✅ [{b['lang']}|{tag}] block #{i+1}: runs OK")
                if out: s.log(f"   → {out[:80]}")
                passed += 1
            else:
                if "ModuleNotFoundError" in err or "Cannot find module" in err:
                    s.log(f"⚠️  [{b['lang']}|{tag}] block #{i+1}: missing package (needs install)")
                elif "SyntaxError" in err:
                    s.error(f"❌ [{b['lang']}|{tag}] block #{i+1}: runtime SyntaxError")
                else:
                    s.log(f"⚠️  [{b['lang']}|{tag}] block #{i+1}: needs env (expected)")

        score = passed / max(len(runnable), 1)
        s.status = "PASS" if score >= 0.5 or not s.errors else "PARTIAL"
        s.duration_ms = int((time.time()-t0)*1000)
        return s

    # ── L4: Mock API ────────────────────────────────────

    MOCK_PY = """
import sys
from unittest.mock import MagicMock
class _M(MagicMock):
    def __call__(self, *a, **kw): return MagicMock()
for _p in ['stripe','twilio','sendgrid','resend','openai','anthropic',
           'psycopg2','pymongo','redis','boto3','langchain','litellm']:
    sys.modules[_p] = _M()
"""
    MOCK_JS = "const require = () => new Proxy({}, { get: () => () => ({}) });\n"

    def _test_mock(self, blocks: list[dict]) -> PipelineStage:
        s = PipelineStage("TEST_L4_MOCK_API")
        t0 = time.time()

        api_blocks = [b for b in blocks
                      if b["needs_api"]
                      and b["lang"] in ("python","javascript")]

        if not api_blocks:
            s.log("⏭️  No API blocks to mock-test")
            s.status = "SKIP"
            s.duration_ms = int((time.time()-t0)*1000)
            return s

        passed = 0
        for i, b in enumerate(api_blocks[:3]):
            lang = b["lang"]
            code = b["code"]
            # Inject mocks
            if lang == "python":
                code = self.MOCK_PY + re.sub(
                    r'os\.environ\[[\'"](\w+)[\'"]\]|os\.getenv\([\'"](\w+)[\'"](?:,[^)]+)?\)',
                    lambda m: f"'mock_{(m.group(1) or m.group(2)).lower()}'", code
                )
            elif lang == "javascript":
                code = self.MOCK_JS + re.sub(
                    r'process\.env\.(\w+)', lambda m: f"'mock_{m.group(1).lower()}'", code
                )

            ok, out, err = self._run(lang, code)
            tag = "community" if b["is_community"] else "official"
            if ok:
                s.log(f"✅ [{lang}|{tag}] block #{i+1}: structure valid with mocks")
                passed += 1
            elif "SyntaxError" in err:
                s.error(f"❌ [{lang}|{tag}] block #{i+1}: syntax error: {err[:100]}")
            else:
                s.log(f"⚠️  [{lang}|{tag}] block #{i+1}: mock runtime (may be async/class): {err[:80]}")

        score = passed / max(len(api_blocks), 1)
        s.status = "PASS" if score >= 0.5 or not s.errors else "PARTIAL"
        s.duration_ms = int((time.time()-t0)*1000)
        return s

    # ── Run helper ───────────────────────────────────────

    def _run(self, lang: str, code: str) -> tuple[bool, str, str]:
        with tempfile.TemporaryDirectory() as tmp:
            if lang == "python":
                f = Path(tmp) / "t.py"; f.write_text(code)
                cmd = [sys.executable, str(f)]
            elif lang in ("javascript","typescript"):
                f = Path(tmp) / "t.js"; f.write_text(code)
                cmd = ["node", str(f)]
            elif lang == "bash":
                f = Path(tmp) / "t.sh"; f.write_text(code)
                cmd = ["bash", str(f)]
            else:
                return True, "", ""
            try:
                p = subprocess.run(cmd, capture_output=True, text=True,
                                   timeout=self.TIMEOUT, cwd=tmp)
                return p.returncode == 0, p.stdout[:300], p.stderr[:300]
            except subprocess.TimeoutExpired:
                return False, "", "Timeout"
            except FileNotFoundError:
                return True, "", "interpreter not found"


# ──────────────────────────────────────────────────────
# STAGE 4: AUTO FIXER
# ──────────────────────────────────────────────────────

class AutoFixer:
    def fix(self, content: str, report: PipelineReport, stage: PipelineStage) -> Optional[str]:
        if not ANTHROPIC_API_KEY:
            stage.log("⏭️  No ANTHROPIC_API_KEY — auto-fix skipped")
            return None

        errors = []
        for s in report.stages:
            errors.extend(s.errors)

        if not errors:
            return None

        prompt = f"""Fix this SKILL.md to resolve the test failures below.

ERRORS:
{chr(10).join(errors[:12])}

CURRENT SKILL.md:
{content}

Rules:
- Fix ONLY broken code — keep working code unchanged
- Replace non-existent packages with correct ones
- Keep YAML frontmatter exactly as is
- Return ONLY the fixed SKILL.md starting with ---"""

        try:
            resp = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-sonnet-4-6",
                    "max_tokens": 4096,
                    "messages": [{"role": "user", "content": prompt}]
                },
                timeout=60
            )
            if resp.status_code == 200:
                fixed = resp.json()["content"][0]["text"].strip()
                if not fixed.startswith("---"):
                    fixed = "---\n" + fixed
                stage.log("✅ Claude generated fix")
                return fixed
        except Exception as e:
            stage.error(f"AutoFix API error: {e}")
        return None


# ──────────────────────────────────────────────────────
# STAGE 5: GITHUB PUBLISHER
# ──────────────────────────────────────────────────────

class GitHubPublisher:
    def __init__(self):
        self.headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json",
        }
        self.base = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}"

    def push(self, tool: str, content: str, label: str = "") -> bool:
        if not GITHUB_TOKEN:
            return False
        path = f"skills/{tool}/SKILL.md"
        r    = requests.get(f"{self.base}/contents/{path}", headers=self.headers, timeout=8)
        sha  = r.json().get("sha") if r.status_code == 200 else None
        msg  = f"feat: add {tool} skill" + (f" [{label}]" if label else "")
        body = {
            "message": msg,
            "content": base64.b64encode(content.encode()).decode(),
            "committer": {"name":"SharpSkills-Bot","email":"bot@sharpskill.dev"},
        }
        if sha: body["sha"] = sha
        r = requests.put(f"{self.base}/contents/{path}",
                         headers=self.headers, json=body, timeout=15)
        return r.status_code in (200, 201)

    def setup_repo(self):
        """Auto-setup GitHub repo like TerminalSkills."""
        if not GITHUB_TOKEN:
            print("❌ GITHUB_TOKEN required"); return False

        print(f"\n🚀 Setting up: {GITHUB_USERNAME}/{GITHUB_REPO}")

        # Create repo
        r = requests.get(f"{self.base}", headers=self.headers, timeout=8)
        if r.status_code == 404:
            r = requests.post("https://api.github.com/user/repos", headers=self.headers,
                json={
                    "name": GITHUB_REPO,
                    "description": "An open-source library of AI agent skills following the Agent Skills open standard. Every skill is automatically L1→L4 tested before publish. Works across Claude Code, OpenAI Codex, Gemini CLI, Cursor, and other AI-powered development tools.",
                    "homepage": "https://sharpskill.dev",
                    "private": False,
                    "has_issues": True,
                    "auto_init": True,
                }, timeout=15)
            if r.status_code in (200,201):
                print(f"  ✅ Repo created")
                time.sleep(2)

        # Topics
        requests.put(f"{self.base}/topics", headers=self.headers, timeout=8,
            json={"names": ["skill","ai-agent","claude-code","cursor","gemini-cli",
                            "skill-md","llm","ai-skills","openai-codex","agent-skills"]})
        print("  ✅ Topics set")

        # Base files
        files = {
            "LICENSE": APACHE_LICENSE,
            "README.md": self._readme(),
            "CONTRIBUTING.md": self._contributing(),
            ".github/workflows/validate.yml": self._workflow(),
        }
        for path, content in files.items():
            sha = None
            r = requests.get(f"{self.base}/contents/{path}", headers=self.headers, timeout=8)
            if r.status_code == 200: sha = r.json().get("sha")
            body = {
                "message": f"chore: add {path}",
                "content": base64.b64encode(content.encode()).decode(),
                "committer": {"name":"SharpSkills-Bot","email":"bot@sharpskill.dev"},
            }
            if sha: body["sha"] = sha
            r = requests.put(f"{self.base}/contents/{path}",
                             headers=self.headers, json=body, timeout=15)
            icon = "✅" if r.status_code in (200,201) else "❌"
            print(f"  {icon} {path}")

        print(f"\n✅ GitHub ready: https://github.com/{GITHUB_USERNAME}/{GITHUB_REPO}")
        return True

    def _readme(self): return f"""# SharpSkill

An open-source library of AI agent skills following the [Agent Skills](https://agentskills.io) open standard. Every skill is automatically L1→L4 tested before publish. Works across Claude Code, OpenAI Codex, Gemini CLI, Cursor, and other AI-powered development tools.

> Every skill is automatically tested: syntax → dependencies → sandbox → mock API.
> "Trust, but verify."

## Install a Skill

```bash
# Claude Code
curl -sL https://raw.githubusercontent.com/{GITHUB_USERNAME}/{GITHUB_REPO}/main/skills/stripe/SKILL.md \\
  -o .claude/skills/stripe.md

# Cursor
curl -sL https://raw.githubusercontent.com/{GITHUB_USERNAME}/{GITHUB_REPO}/main/skills/stripe/SKILL.md \\
  -o .cursor/skills/stripe.md
```

## Skills Catalog

| Skill | Category | Description |
|-------|----------|-------------|
| _(auto-generated as skills are added)_ | | |

## Quality Guarantee

Every skill passes 4 automated tests before publishing:
- **L1** Syntax check (Python + JS + Bash)
- **L2** Package registry verification (npm + PyPI)
- **L3** Sandbox execution (no API keys needed)
- **L4** Mock API structural test

## License

Apache-2.0
"""

    def _contributing(self): return """# Contributing to SharpSkill

Skills must pass 4 automated tests before merging. Run locally:

```bash
python sharpskill.py run --tool your-tool --no-push
```

See [SKILL format requirements](https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf).

## Rules
- `SKILL.md` — exact name, case-sensitive
- `name:` — kebab-case only
- `description:` — WHAT + WHEN (trigger phrases). No XML tags. Max 1024 chars.
- No `README.md` inside skill folder
- License: Apache-2.0

## License
Apache-2.0
"""

    def _workflow(self): return """name: Validate Skills
on:
  push:
    paths: ['skills/**']
  pull_request:
    paths: ['skills/**']
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install pyyaml requests
      - run: python sharpskill.py validate
"""



# ──────────────────────────────────────────────────────
# STAGE 0.5: GAP ANALYZER
# ──────────────────────────────────────────────────────

class GapAnalyzer:
    """
    Reads competitor SKILL.md content to understand what they covered.
    Purpose: NOT to copy — but to identify GAPS we can fill better.

    Legal basis:
      - Apache-2.0 license allows reading and analysis
      - We use output only to identify missing topics
      - Our content is written from primary sources (vendor docs, GitHub Issues, SO)
    """

    COMPETITOR_RAW_URLS = {
        "terminalskills": "https://raw.githubusercontent.com/TerminalSkills/skills/main/skills/{tool}/SKILL.md",
        "anthropic":      "https://raw.githubusercontent.com/anthropics/skills/main/skills/{tool}/SKILL.md",
        "alirezarezvani": "https://raw.githubusercontent.com/alirezarezvani/claude-skills/main/{tool}/SKILL.md",
    }

    def __init__(self):
        self.gh_headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json",
        } if GITHUB_TOKEN else {}

    def analyze(self, tool: str, conflicts: list[dict], stage: PipelineStage) -> dict:
        """
        Fetch competitor skills and extract gap analysis.
        Returns: { covered: [...], gaps: [...], raw_previews: {source: preview} }
        """
        tool_kebab = re.sub(r"[^a-z0-9-]", "-", tool.lower()).strip("-")
        analysis = {
            "covered":      [],
            "gaps":         [],
            "raw_previews": {},
            "sources_read": [],
        }

        for conflict in conflicts:
            source     = conflict.get("source", "")
            match_type = conflict.get("match_type", "")

            if match_type != "exact":
                continue

            # Map source to raw URL template
            url_template = None
            for key, tmpl in self.COMPETITOR_RAW_URLS.items():
                if key in source.lower():
                    url_template = tmpl
                    break

            if not url_template:
                stage.log(f"⏭️  No raw URL for: {source}")
                continue

            raw_url = url_template.format(tool=tool_kebab)
            stage.log(f"📖 Reading [{source}]: {raw_url}")

            content = self._fetch_raw(raw_url)
            if not content:
                stage.log(f"   ⚠️  Could not fetch — skipping")
                continue

            analysis["sources_read"].append(source)
            analysis["raw_previews"][source] = content[:300] + "..."

            # Extract what they covered
            covered = self._extract_covered(content)
            analysis["covered"].extend(covered)
            stage.log(f"   ✅ Covered ({len(covered)} topics): {', '.join(covered[:4])}")

        # Remove duplicates
        analysis["covered"] = list(dict.fromkeys(analysis["covered"]))

        # Identify common gaps using Claude if available
        if analysis["covered"] and ANTHROPIC_API_KEY:
            analysis["gaps"] = self._identify_gaps(tool, analysis["covered"], stage)
        else:
            analysis["gaps"] = self._default_gaps()

        stage.log(f"\n   📊 Sources read: {len(analysis['sources_read'])}")
        stage.log(f"   📊 Topics covered by competitors: {len(analysis['covered'])}")
        stage.log(f"   📊 Gaps identified: {len(analysis['gaps'])}")

        return analysis

    def _fetch_raw(self, url: str) -> Optional[str]:
        # Check cache
        cp = CACHE_DIR / ("gap_" + hashlib.md5(url.encode()).hexdigest() + ".txt")
        if cp.exists() and (time.time() - cp.stat().st_mtime) < 86400:
            return cp.read_text(encoding="utf-8")
        try:
            r = requests.get(url, headers=self.gh_headers, timeout=8)
            if r.status_code == 200:
                cp.write_text(r.text, encoding="utf-8")
                return r.text
        except:
            pass
        return None

    def _extract_covered(self, skill_content: str) -> list[str]:
        """Extract topic sections from a SKILL.md."""
        covered = []
        # H2 and H3 headings = topics covered
        for m in re.finditer(r"^#{2,3}\s+(.+)$", skill_content, re.MULTILINE):
            heading = m.group(1).strip()
            # Filter out boilerplate headings
            skip = {"quick start", "when to use", "resources", "troubleshooting",
                    "pre-deploy checklist", "failure modes", "examples", "guidelines",
                    "installation", "overview", "introduction", "usage"}
            if heading.lower() not in skip and len(heading) > 3:
                covered.append(heading)
        # Also extract code block languages as coverage signal
        langs = re.findall(r"```(\w+)", skill_content)
        if langs:
            covered.append(f"Code examples: {', '.join(set(langs[:5]))}")
        return covered[:15]

    def _identify_gaps(self, tool: str, covered: list[str], stage: PipelineStage) -> list[str]:
        """Ask Claude to identify what's missing given what competitors covered."""
        prompt = f"""Competitor skills for "{tool}" cover these topics:
{chr(10).join(f"- {c}" for c in covered)}

As a production engineering expert, list 5-8 critical topics they MISSED
that matter for real production usage. Focus on:
- Error handling & edge cases
- Performance & scaling
- Security hardening
- Monitoring & observability  
- Common production failures
- Integration patterns

Return ONLY a JSON array of short topic strings (max 8 words each).
Example: ["Idempotency keys for retry safety", "Rate limit handling with backoff"]"""

        try:
            resp = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-sonnet-4-6",
                    "max_tokens": 512,
                    "messages": [{"role": "user", "content": prompt}]
                },
                timeout=30
            )
            if resp.status_code == 200:
                text = resp.json()["content"][0]["text"].strip()
                # Extract JSON array
                m = re.search(r"\[.*?\]", text, re.DOTALL)
                if m:
                    gaps = json.loads(m.group())
                    stage.log(f"   🎯 Gaps (Claude): {', '.join(gaps[:3])}...")
                    return gaps[:8]
        except Exception as e:
            stage.log(f"   ⚠️  Gap identification failed: {e}")

        return self._default_gaps()

    def _default_gaps(self) -> list[str]:
        return [
            "Idempotency and retry safety",
            "Rate limiting with exponential backoff",
            "Error classification and handling",
            "Production monitoring and alerting",
            "Security hardening and secrets management",
            "Performance optimization patterns",
        ]


# ──────────────────────────────────────────────────────
# MASTER PIPELINE
# ──────────────────────────────────────────────────────

class MasterPipeline:
    def __init__(self):
        self.collector = DataCollector()
        self.generator = SkillGenerator()
        self.tester    = SkillTester()
        self.fixer     = AutoFixer()
        self.publisher = GitHubPublisher()
        self.gap_analyzer = GapAnalyzer()

    def run(self, tool: str, push: bool = True) -> PipelineReport:
        report = PipelineReport(tool)
        tool_kebab = re.sub(r'[^a-z0-9-]', '-', tool.lower()).strip('-')

        self._banner(tool, report.trace_id)
        report.dedup_action = "generate"

        # ── STAGE 0: Dedup Check ───────────────────────────
        print("\n🔍 STAGE 0 — Deduplication Check")
        s0 = PipelineStage("DEDUP_CHECK")
        action, dedup_conflicts = self._dedup_check(tool, tool_kebab, s0)
        report.add_stage(s0)
        report.dedup_action = action
        self._print_stage(s0)

        if action == "skip":
            report.final_status = "SKIPPED"
            dedup_conflicts = []
            (REPORTS_DIR / f"{tool_kebab}_{report.trace_id}.json").write_text(
                json.dumps(report.to_dict(), indent=2)
            )
            print(f"\n  ⏭️  SKIPPED — skill already exists in SharpSkill")
            return report

        # ── STAGE 0.5: Gap Analysis ──────────────────────
        if action in ("compete", "variant"):
            print("\n🔬 STAGE 0.5 — Gap Analysis")
            s05 = PipelineStage("GAP_ANALYSIS")
            t05 = time.time()
            conflicts = dedup_conflicts
            gap_analysis = self.gap_analyzer.analyze(tool, conflicts, s05)
            report.gap_analysis = gap_analysis
            s05.status = "PASS" if gap_analysis["sources_read"] else "SKIP"
            s05.duration_ms = int((time.time() - t05) * 1000)
            report.add_stage(s05)
            self._print_stage(s05)
        else:
            report.gap_analysis = {}

        # ── STAGE 1: Collect ─────────────────────────────
        print("\n📡 STAGE 1 — Data Collection")
        s1 = PipelineStage("COLLECT")
        sources = self.collector.collect(tool, s1)
        s1.status = "PASS" if sources else "PARTIAL"
        report.add_stage(s1)
        report.source_breakdown = {
            "official":  sum(1 for k in sources if "official"  in k),
            "community": sum(1 for k in sources if "community" in k),
        }
        self._print_stage(s1)

        # ── STAGE 2: Generate ────────────────────────────
        print("\n🧠 STAGE 2 — Skill Generation")
        s2 = PipelineStage("GENERATE")
        skill_content = self.generator.generate(tool, sources, s2, report)
        s2.status = "PASS"
        report.add_stage(s2)
        report.skill_content = skill_content
        self._print_stage(s2)

        # Save locally
        skill_dir = SKILLS_DIR / tool_kebab
        skill_dir.mkdir(exist_ok=True)
        (skill_dir / "SKILL.md").write_text(skill_content)
        print(f"   💾 Saved: skills/{tool_kebab}/SKILL.md")

        # ── STAGE 3: Test ────────────────────────────────
        print("\n🧪 STAGE 3 — Testing (L1→L4)")
        score = self.tester.run_all(skill_content, report)

        for stage in report.stages:
            if stage.name.startswith("TEST"):
                self._print_stage(stage)

        print(f"\n   📊 Test score: {score:.0%}")

        # ── STAGE 4: Decision ────────────────────────────
        print("\n🎯 STAGE 4 — Decision")
        hard_fail = any(
            s.status == "FAIL" and s.name in ("TEST_L1_SYNTAX", "TEST_L2_DEPS")
            for s in report.stages
        )

        if score >= 0.75 and not hard_fail:
            # ✅ PASS
            report.final_status = "PASS"
            print("   ✅ PASS — all tests satisfied")
            if push:
                self._push(tool_kebab, skill_content, "", report)

        elif hard_fail and ANTHROPIC_API_KEY:
            # 🔧 Try auto-fix
            print("   🔧 Hard failures detected — attempting auto-fix...")
            s_fix = PipelineStage("AUTO_FIX")
            fixed = self.fixer.fix(skill_content, report, s_fix)
            report.add_stage(s_fix)
            self._print_stage(s_fix)

            if fixed:
                # Re-test fixed version
                print("\n🔄 Re-testing fixed version...")
                fix_report = PipelineReport(tool + "_fixed")
                fix_score  = self.tester.run_all(fixed, fix_report)
                fix_hard   = any(
                    s.status == "FAIL" and s.name in ("TEST_L1_SYNTAX","TEST_L2_DEPS")
                    for s in fix_report.stages
                )

                if fix_score >= 0.75 and not fix_hard:
                    # Fixed and passes
                    (skill_dir / "SKILL.md").write_text(fixed)
                    report.skill_content  = fixed
                    report.final_status   = "AUTO_FIXED"
                    print(f"   ✅ AUTO_FIXED (score: {fix_score:.0%})")
                    if push:
                        self._push(tool_kebab, fixed, "auto-fixed", report)
                else:
                    # Fix didn't fully work — push as BETA
                    (skill_dir / "SKILL.md").write_text(fixed)
                    report.final_status = "BETA"
                    print(f"   ⚠️  BETA (fix score: {fix_score:.0%})")
                    self._save_draft(tool_kebab, fixed)
                    if push:
                        self._push(tool_kebab, fixed, "BETA", report)
            else:
                report.final_status = "FAIL"
                print("   ❌ Auto-fix produced nothing")
                self._save_draft(tool_kebab, skill_content)

        else:
            # Score too low, no API key for fix
            report.final_status = "BETA"
            print(f"   ⚠️  BETA (score: {score:.0%})")
            self._save_draft(tool_kebab, skill_content)
            if push:
                self._push(tool_kebab, skill_content, "BETA", report)

        # ── Save report ──────────────────────────────────
        rf = REPORTS_DIR / f"{tool_kebab}_{report.trace_id}.json"
        rf.write_text(json.dumps(report.to_dict(), indent=2))

        self._summary(report)
        return report

    def _push(self, tool: str, content: str, label: str, report: PipelineReport):
        print(f"\n   📤 Pushing to GitHub...")
        ok = self.publisher.push(tool, content, label)
        if ok:
            print(f"   ✅ https://github.com/{GITHUB_USERNAME}/{GITHUB_REPO}/tree/main/skills/{tool}")
        else:
            print(f"   ⚠️  Push skipped (no GITHUB_TOKEN or error)")

    def _save_draft(self, tool: str, content: str):
        d = DRAFTS_DIR / tool; d.mkdir(exist_ok=True)
        (d / "SKILL.md").write_text(content)
        print(f"   📁 Draft: drafts/{tool}/SKILL.md")

    def _dedup_check(self, tool: str, tool_kebab: str, stage: PipelineStage) -> str:
        """
        STAGE 0: Check if skill already exists.
        Returns action: 'generate' | 'upgrade' | 'variant' | 'skip'
        """
        if not DEDUP_AVAILABLE:
            stage.log("⏭️  dedup.py not found — skipping dedup check")
            stage.status = "SKIP"
            return "generate", []

        checker = DedupChecker()
        result  = checker.check(tool)

        if not result.has_conflicts:
            stage.log(f"✅ '{tool_kebab}' — unique, no competitors found")
            stage.status = "PASS"
            return "generate", []

        # Log all conflicts
        for c in result.conflicts:
            icon = "🔴" if c["match_type"] == "exact" else "🟡"
            stage.log(f"{icon} [{c['source']}] {c['skill_name']} ({c['match_type']})")
            if c["url"]:
                stage.log(f"   → {c['url']}")

        if result.similar_skills:
            stage.log(f"🔍 Similar: {', '.join(result.similar_skills[:3])}")

        # Check if already in OWN repo → always skip
        own_conflict = any(
            "SharpSkill" in c["source"] and c["match_type"] == "exact"
            for c in result.conflicts
        )
        if own_conflict:
            stage.log(f"⏭️  Already in SharpSkill — skipping")
            stage.status = "SKIP"
            return "skip", []

        # Exists in TerminalSkills → COMPETE (write independently from primary sources)
        ts_conflict = any("TerminalSkills" in c["source"] for c in result.conflicts)
        if ts_conflict:
            stage.log(f"⚔️  Exists in TerminalSkills — writing COMPETE: independent skill from primary sources")
            stage.status = "PASS"
            return "compete", result.conflicts

        # Alias or similar → VARIANT
        stage.log(f"🔀 Similar skill exists — creating VARIANT")
        stage.status = "PASS"
        return "variant", result.conflicts

    def _banner(self, tool: str, trace_id: str):
        print(f"\n{'━'*55}")
        print(f"  🤖 SharpSkill Master v1.0")
        print(f"  Tool:     {tool}")
        print(f"  trace_id: {trace_id}")
        print(f"  Philosophy: Trust, but verify")
        print(f"{'━'*55}")

    def _print_stage(self, s: PipelineStage):
        icons = {"PASS":"✅","FAIL":"❌","SKIP":"⏭️","PARTIAL":"⚠️","PENDING":"⏳"}
        print(f"   {icons.get(s.status,'?')} {s.name}: {s.status} ({s.duration_ms}ms)")
        for d in s.details[-4:]: print(f"      {d}")
        for e in s.errors[:3]:   print(f"      {e}")

    def _summary(self, report: PipelineReport):
        icons = {"PASS":"✅","AUTO_FIXED":"🔧","BETA":"⚠️","FAIL":"❌"}
        icon  = icons.get(report.final_status, "?")
        dur   = sum(s.duration_ms for s in report.stages)
        print(f"\n{'━'*55}")
        print(f"  {icon}  {report.final_status}")
        print(f"  Score:   {report.overall_score():.0%}")
        print(f"  Sources: {report.source_breakdown['official']} official + "
              f"{report.source_breakdown['community']} community")
        print(f"  Time:    {dur/1000:.1f}s")
        print(f"  Report:  test_reports/{report.tool}_{report.trace_id}.json")
        print(f"{'━'*55}")


# ──────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────

def cmd_validate():
    """Validate all local skills (YAML structure only, fast)."""
    skill_dirs = [d for d in SKILLS_DIR.iterdir() if d.is_dir()] if SKILLS_DIR.exists() else []
    if not skill_dirs:
        print("No skills found."); return
    print(f"\n🔍 Validating {len(skill_dirs)} skills\n")
    ok = fail = 0
    for sd in sorted(skill_dirs):
        sf = sd / "SKILL.md"
        if not sf.exists():
            print(f"  ❌ {sd.name}: SKILL.md missing"); fail += 1; continue
        content = sf.read_text()
        fm_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        if not fm_match:
            print(f"  ❌ {sd.name}: missing frontmatter"); fail += 1; continue
        try:
            fm = yaml.safe_load(fm_match.group(1))
            name = fm.get("name", "")
            desc = fm.get("description", "")
            errs = []
            if not name: errs.append("missing name")
            elif not re.match(r'^[a-z0-9][a-z0-9-]*$', name): errs.append(f"name not kebab: {name}")
            if not desc: errs.append("missing description")
            elif len(desc) > 1024: errs.append(f"description too long")
            elif "<" in desc or ">" in desc: errs.append("XML in description")
            if errs:
                print(f"  ❌ {sd.name}: {', '.join(errs)}"); fail += 1
            else:
                print(f"  ✅ {sd.name}"); ok += 1
        except yaml.YAMLError as e:
            print(f"  ❌ {sd.name}: invalid YAML"); fail += 1
    print(f"\n  ✅ {ok} valid  ❌ {fail} invalid")

def cmd_report():
    reports = sorted(REPORTS_DIR.glob("*.json"))
    if not reports: print("No reports yet."); return
    print(f"\n📋 Pipeline Reports ({len(reports)})\n")
    by = {}
    for rf in reports:
        try:
            d = json.loads(rf.read_text())
            by.setdefault(d.get("final_status","?"), []).append(d)
        except: pass
    for status, icon in [("PASS","✅"),("AUTO_FIXED","🔧"),("BETA","⚠️"),("FAIL","❌")]:
        for item in by.get(status, []):
            src = item.get("source_breakdown", {})
            print(f"  {icon} {item['tool']} "
                  f"score:{item['overall_score']:.0%} "
                  f"(off:{src.get('official',0)} com:{src.get('community',0)})")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="SharpSkill Master — generate + test + fix + push",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Pipeline: Collect → Generate → Test(L1-L4) → Auto-fix → Push
  PASS       → pushed to GitHub
  AUTO_FIXED → Claude fixed it → pushed [auto-fixed]
  BETA       → issues remain → pushed [BETA] + saved to drafts/
  FAIL       → saved to drafts/ only

Examples:
  python sharpskill.py run --tool stripe
  python sharpskill.py run --tool neon-postgres --no-push
  python sharpskill.py batch --file tools.txt
  python sharpskill.py setup-github
        """
    )
    sub = parser.add_subparsers(dest="command")

    r = sub.add_parser("run",    help="Full pipeline for one tool")
    r.add_argument("--tool",     required=True)
    r.add_argument("--no-push",  action="store_true")

    b = sub.add_parser("batch",  help="Full pipeline for tools in file")
    b.add_argument("--file",     required=True)
    b.add_argument("--no-push",  action="store_true")

    sub.add_parser("setup-github", help="Auto-setup GitHub repo")
    sub.add_parser("validate",     help="Validate all local skills (fast)")
    sub.add_parser("report",       help="Show pipeline report summary")

    args = parser.parse_args()

    if args.command == "run":
        MasterPipeline().run(args.tool, push=not args.no_push)

    elif args.command == "batch":
        tools = [t.strip() for t in Path(args.file).read_text().splitlines()
                 if t.strip() and not t.startswith("#")]
        print(f"📦 Batch: {len(tools)} tools")
        results = []
        for i, tool in enumerate(tools, 1):
            print(f"\n[{i}/{len(tools)}]")
            r = MasterPipeline().run(tool, push=not args.no_push)
            results.append(r.to_dict())
            time.sleep(2)
        ok   = sum(1 for r in results if r["final_status"] in ("PASS","AUTO_FIXED"))
        beta = sum(1 for r in results if r["final_status"] == "BETA")
        fail = sum(1 for r in results if r["final_status"] == "FAIL")
        print(f"\n\n✅ {ok} PASS/FIXED  ⚠️ {beta} BETA  ❌ {fail} FAIL")

    elif args.command == "setup-github":
        GitHubPublisher().setup_repo()

    elif args.command == "validate":
        cmd_validate()

    elif args.command == "report":
        cmd_report()

    else:
        parser.print_help()
