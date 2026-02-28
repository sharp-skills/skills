#!/usr/bin/env python3
"""
SharpSkill Deduplication Checker v2.0
Checks ALL known skill repos in the ecosystem.
Strategy: Path 1+3 — write independently, know the full market.
"""
import os, re, json, time
from pathlib import Path
from typing import Optional
import requests
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN    = os.getenv("GITHUB_TOKEN", "")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME", "SharpSkill")
GITHUB_REPO     = os.getenv("GITHUB_REPO", "skills")
CACHE_DIR       = Path("./.cache")
CACHE_DIR.mkdir(exist_ok=True)

COMPETITORS = {
    "anthropic": {
        "repo": "anthropics/skills", "skills_path": "skills",
        "license": "Apache-2.0", "url": "https://github.com/anthropics/skills",
        "tier": "official",
        "known": {
            "pdf","docx","pptx","xlsx","frontend-design","skill-creator",
            "algorithmic-art","canvas-design","slack-gif-creator",
            "artifacts-builder","webapp-testing","mcp-server-builder",
        }
    },
    "terminalskills": {
        "repo": "TerminalSkills/skills", "skills_path": "skills",
        "license": "Apache-2.0", "url": "https://github.com/TerminalSkills/skills",
        "tier": "competitor",
        "known": {
            "pdf-analyzer","excel-processor","code-reviewer","git-commit-pro",
            "api-tester","docker-helper","web-scraper","data-visualizer",
            "markdown-writer","sql-optimizer","test-generator","security-audit",
            "code-migration","cicd-pipeline","mcp-server-builder","prompt-tester",
            "monorepo-manager","data-validator","log-analyzer",
        }
    },
    "alirezarezvani": {
        "repo": "alirezarezvani/claude-skills", "skills_path": "",
        "license": "MIT", "url": "https://github.com/alirezarezvani/claude-skills",
        "tier": "competitor",
        "known": {
            "content-creator","ceo-advisor","cto-advisor","marketing-skill",
            "sales-skill","hr-advisor","legal-advisor","financial-advisor",
            "product-manager","ux-researcher","data-analyst","security-expert",
            "devops-engineer","cloud-architect","api-designer","database-admin",
            "mobile-developer","web-developer","ml-engineer","blockchain-developer",
        }
    },
    "obra-superpowers": {
        "repo": "obra/superpowers", "skills_path": "skills",
        "license": "MIT", "url": "https://github.com/obra/superpowers",
        "tier": "competitor",
        "known": {
            "tdd","debugging","collaboration","brainstorm","write-plan",
            "execute-plan","code-review","refactor","documentation","git-workflow",
        }
    },
    "hashicorp": {
        "repo": "hashicorp/agent-skills", "skills_path": "skills",
        "license": "MPL-2.0", "url": "https://github.com/hashicorp/agent-skills",
        "tier": "enterprise",
        "known": {
            "terraform","vault","consul","nomad","packer",
            "waypoint","hcp-terraform","terraform-cloud",
        }
    },
    "composio": {
        "repo": "ComposioHQ/awesome-claude-skills", "skills_path": "skills",
        "license": "Apache-2.0", "url": "https://github.com/ComposioHQ/awesome-claude-skills",
        "tier": "community",
        "known": {"connect-apps","aws-skills","changelog-generator","artifacts-builder"}
    },
}

ALIASES = {
    "pdf": "pdf-analyzer", "pdf-reader": "pdf-analyzer",
    "excel": "excel-processor", "csv": "excel-processor",
    "code-review": "code-reviewer", "git": "git-commit-pro",
    "docker": "docker-helper", "dockerfile": "docker-helper",
    "scraper": "web-scraper", "web-scraping": "web-scraper",
    "sql": "sql-optimizer", "testing": "test-generator",
    "security": "security-audit", "ci-cd": "cicd-pipeline",
    "mcp": "mcp-server-builder", "tf": "terraform",
    "word": "docx", "powerpoint": "pptx", "spreadsheet": "xlsx",
}


class DedupResult:
    def __init__(self, tool):
        self.tool       = tool
        self.tool_kebab = re.sub(r'[^a-z0-9-]', '-', tool.lower()).strip('-')
        self.conflicts: list[dict] = []
        self.similar_skills: list[str] = []
        self.recommendation = "GENERATE"
        self.reason = ""

    @property
    def has_conflicts(self):
        return len(self.conflicts) > 0

    def add_conflict(self, source, skill_name, match_type, url="", tier=""):
        self.conflicts.append({
            "source": source, "skill_name": skill_name,
            "match_type": match_type, "url": url, "tier": tier,
        })

    def summary(self):
        if not self.conflicts and not self.similar_skills:
            return f"✅ '{self.tool_kebab}' — unique skill across the entire ecosystem"
        lines = []
        if self.conflicts:
            lines.append(f"⚠️  '{self.tool_kebab}' found in:")
            for c in self.conflicts:
                icon = "🔴" if c["match_type"] == "exact" else "🟡"
                lines.append(f"   {icon} [{c['tier']}] {c['source']}: {c['skill_name']} ({c['match_type']})")
                if c["url"]: lines.append(f"      → {c['url']}")
        if self.similar_skills:
            lines.append(f"🔍 Similar: {', '.join(self.similar_skills[:5])}")
        lines.append(f"📋 {self.recommendation} — {self.reason}")
        return "\n".join(lines)


class DedupChecker:
    def __init__(self):
        self.gh_headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json",
        } if GITHUB_TOKEN else {}
        self._caches: dict = {}

    def check(self, tool: str) -> DedupResult:
        result = DedupResult(tool)
        tool_k = result.tool_kebab

        # 1. Own repo — if found → SKIP immediately
        self._check_own(tool_k, result)
        if any(c["tier"] == "own" and c["match_type"] == "exact" for c in result.conflicts):
            self._set_recommendation(result)
            return result

        # 2. All competitors
        for comp_id, comp in COMPETITORS.items():
            skills = self._fetch(comp_id, comp)
            if tool_k in skills:
                result.add_conflict(
                    comp_id, tool_k, "exact",
                    f"{comp['url']}/tree/main/skills/{tool_k}",
                    comp["tier"]
                )

        # 3. Aliases
        canonical = ALIASES.get(tool_k)
        if canonical:
            for comp_id, comp in COMPETITORS.items():
                skills = self._fetch(comp_id, comp)
                if canonical in skills:
                    result.add_conflict(
                        f"{comp_id} (alias)", canonical, "alias",
                        comp["url"], comp["tier"]
                    )

        # 4. Fuzzy
        all_known = set()
        all_known.update(self._fetch_own())
        for comp_id, comp in COMPETITORS.items():
            all_known.update(self._fetch(comp_id, comp))
        tool_words = set(tool_k.split("-"))
        similar = []
        for known in all_known:
            if known == tool_k: continue
            if tool_k in known or known in tool_k:
                similar.append(known); continue
            known_words = set(known.split("-"))
            if len(tool_words & known_words) >= 2:
                similar.append(known)
        result.similar_skills = sorted(set(similar))[:6]

        self._set_recommendation(result)
        return result

    def get_all_known_skills(self) -> dict:
        result = {"sharpskill": self._fetch_own()}
        for comp_id, comp in COMPETITORS.items():
            result[comp_id] = self._fetch(comp_id, comp)
        return result

    def _check_own(self, tool_k, result):
        if (Path("./skills") / tool_k / "SKILL.md").exists():
            result.add_conflict("SharpSkill (local)", tool_k, "exact",
                                f"skills/{tool_k}/SKILL.md", "own")
            return
        own = self._fetch_own()
        if tool_k in own:
            result.add_conflict(
                "SharpSkill (GitHub)", tool_k, "exact",
                f"https://github.com/{GITHUB_USERNAME}/{GITHUB_REPO}/tree/main/skills/{tool_k}",
                "own"
            )

    def _fetch_own(self) -> set:
        key = "own"
        if key in self._caches: return self._caches[key]
        cp = CACHE_DIR / "sharpskill_own.json"
        if cp.exists() and (time.time() - cp.stat().st_mtime) < 3600:
            skills = set(json.loads(cp.read_text()))
            self._caches[key] = skills
            return skills
        skills = set()
        local = Path("./skills")
        if local.exists():
            skills.update(d.name for d in local.iterdir() if d.is_dir())
        try:
            r = requests.get(
                f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/contents/skills",
                headers=self.gh_headers, timeout=8)
            if r.status_code == 200:
                skills.update(i["name"] for i in r.json() if i["type"] == "dir")
                cp.write_text(json.dumps(list(skills)))
        except: pass
        self._caches[key] = skills
        return skills

    def _fetch(self, comp_id: str, comp: dict) -> set:
        if comp_id in self._caches: return self._caches[comp_id]
        cp = CACHE_DIR / f"comp_{comp_id}.json"
        if cp.exists() and (time.time() - cp.stat().st_mtime) < 21600:
            skills = set(json.loads(cp.read_text()))
            self._caches[comp_id] = skills
            return skills
        skills = set(comp.get("known", set()))
        repo   = comp["repo"]
        spath  = comp["skills_path"]
        url    = f"https://api.github.com/repos/{repo}/contents/{spath}".rstrip("/")
        try:
            r = requests.get(url, headers=self.gh_headers, timeout=8)
            if r.status_code == 200 and isinstance(r.json(), list):
                skills.update(i["name"] for i in r.json() if i["type"] == "dir")
            # PRs
            r2 = requests.get(
                f"https://api.github.com/repos/{repo}/pulls?state=open&per_page=100",
                headers=self.gh_headers, timeout=8)
            if r2.status_code == 200:
                for pr in r2.json():
                    m = re.search(r'add[s]?\s+([a-z0-9-]+)\s+skill',
                                  pr.get("title","").lower())
                    if m: skills.add(m.group(1))
            cp.write_text(json.dumps(list(skills)))
        except: pass
        self._caches[comp_id] = skills
        return skills

    def _set_recommendation(self, result: DedupResult):
        exact   = [c for c in result.conflicts if c["match_type"] == "exact"]
        own_hit = any(c["tier"] == "own" for c in exact)
        if own_hit:
            result.recommendation = "SKIP"
            result.reason = "already in SharpSkill — not writing twice"
        elif not result.conflicts:
            result.recommendation = "GENERATE"
            result.reason = "unique topic — full pipeline"
        elif exact:
            sources = list({c["source"] for c in exact})
            result.recommendation = "COMPETE"
            result.reason = (
                f"topic exists in: {', '.join(sources)}. "
                f"Writing independently from vendor docs + GitHub Issues + SO/Reddit"
            )
        else:
            result.recommendation = "COMPETE"
            result.reason = "similar topic — writing under our name from primary sources"


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="SharpSkill Dedup Checker v2.0")
    parser.add_argument("--tool",    help="Check one tool")
    parser.add_argument("--scan",    action="store_true", help="Full market map")
    parser.add_argument("--refresh", action="store_true", help="Clear cache")
    args = parser.parse_args()

    if args.refresh:
        for cp in CACHE_DIR.glob("comp_*.json"): cp.unlink()
        for cp in CACHE_DIR.glob("sharpskill_*.json"): cp.unlink()
        print("✅ Cache cleared")

    if args.scan:
        checker    = DedupChecker()
        all_skills = checker.get_all_known_skills()
        print(f"\n{'━'*55}")
        print(f"  📊 Full Skill Market Map")
        print(f"{'━'*55}")
        total = 0
        for source, skills in all_skills.items():
            tier = COMPETITORS.get(source, {}).get("tier", "own").upper()
            print(f"\n  [{tier}] {source} — {len(skills)} skills")
            for s in sorted(skills)[:15]:
                print(f"    • {s}")
            if len(skills) > 15:
                print(f"    ... +{len(skills)-15} more")
            total += len(skills)
        print(f"\n  Total: {total} known skills across {len(all_skills)} repos")

    elif args.tool:
        checker = DedupChecker()
        result  = checker.check(args.tool)
        print(f"\n{'━'*55}")
        print(result.summary())
        print(f"{'━'*55}")
    else:
        parser.print_help()
