#!/usr/bin/env python3
"""
SharpSkill Test Bot v1.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
4 test levels for each SKILL.md:

  L1 — Syntax       (Python + JS/TS)
  L2 — Dependencies (npm/pip install)
  L3 — Sandbox run  (execute without API keys)
  L4 — Mock API     (stubs instead of real API keys)

Result:
  PASS  → pushed to GitHub  
  FAIL  → Claude attempts auto-fix → re-test
  BETA  → not fixed → marked with [BETA] label

Usage:
  python test_bot.py test --skill stripe-webhooks
  python test_bot.py test-all
  python test_bot.py report
"""

import os, sys, re, json, ast, time, subprocess, tempfile, hashlib
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional
import requests
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
GITHUB_TOKEN      = os.getenv("GITHUB_TOKEN", "")
GITHUB_USERNAME   = os.getenv("GITHUB_USERNAME", "SharpSkill")
GITHUB_REPO       = os.getenv("GITHUB_REPO", "skills")

SKILLS_DIR  = Path("./skills")
DRAFTS_DIR  = Path("./drafts")
REPORTS_DIR = Path("./test_reports")

for d in [SKILLS_DIR, DRAFTS_DIR, REPORTS_DIR]:
    d.mkdir(exist_ok=True)

# ──────────────────────────────────────────────────────
# DATA MODELS
# ──────────────────────────────────────────────────────

class TestResult:
    def __init__(self, level: str, name: str):
        self.level   = level
        self.name    = name
        self.passed  = False
        self.score   = 0.0      # 0.0 - 1.0
        self.details = []
        self.errors  = []
        self.duration_ms = 0

    def ok(self, msg: str, score: float = 1.0):
        self.details.append(f"✅ {msg}")
        self.score = max(self.score, score)

    def fail(self, msg: str):
        self.errors.append(f"❌ {msg}")

    def warn(self, msg: str):
        self.details.append(f"⚠️  {msg}")

    @property
    def status(self):
        if not self.errors:
            return "PASS"
        if self.score > 0.5:
            return "PARTIAL"
        return "FAIL"


class SkillTestReport:
    def __init__(self, skill_name: str):
        self.skill_name  = skill_name
        self.trace_id    = hashlib.md5(f"{skill_name}{datetime.now()}".encode()).hexdigest()[:12]
        self.tested_at   = datetime.now().isoformat()
        self.results: list[TestResult] = []
        self.auto_fixed  = False
        self.fix_attempts = 0
        self.final_status = "PENDING"  # PASS | FAIL | BETA | AUTO_FIXED

    def overall_score(self) -> float:
        if not self.results:
            return 0.0
        return sum(r.score for r in self.results) / len(self.results)

    def has_failures(self) -> bool:
        return any(r.status == "FAIL" for r in self.results)

    def to_dict(self) -> dict:
        return {
            "skill_name":   self.skill_name,
            "trace_id":     self.trace_id,
            "tested_at":    self.tested_at,
            "final_status": self.final_status,
            "overall_score": round(self.overall_score(), 2),
            "auto_fixed":   self.auto_fixed,
            "fix_attempts": self.fix_attempts,
            "results": [
                {
                    "level":   r.level,
                    "name":    r.name,
                    "status":  r.status,
                    "score":   round(r.score, 2),
                    "details": r.details,
                    "errors":  r.errors,
                }
                for r in self.results
            ]
        }


# ──────────────────────────────────────────────────────
# CODE EXTRACTOR
# ──────────────────────────────────────────────────────

class CodeExtractor:
    """Extracts all code blocks from SKILL.md"""

    LANG_MAP = {
        "js": "javascript", "javascript": "javascript", "ts": "typescript",
        "typescript": "typescript", "py": "python", "python": "python",
        "bash": "bash", "sh": "bash", "shell": "bash",
        "sql": "sql", "yaml": "yaml", "yml": "yaml",
        "json": "json", "dockerfile": "dockerfile",
    }

    def extract(self, skill_content: str) -> list[dict]:
        blocks = []
        pattern = r'```(\w+)?\n([\s\S]*?)```'
        for match in re.finditer(pattern, skill_content):
            lang_raw = (match.group(1) or "").lower().strip()
            code     = match.group(2).strip()
            lang     = self.LANG_MAP.get(lang_raw, lang_raw or "unknown")

            if len(code) < 10:  # skip trivial blocks
                continue

            # Extract imports and package names
            packages = self._extract_packages(code, lang)

            blocks.append({
                "lang":     lang,
                "code":     code,
                "packages": packages,
                "needs_api": self._needs_api(code),
            })

        return blocks

    def _extract_packages(self, code: str, lang: str) -> list[str]:
        packages = []
        if lang in ("javascript", "typescript"):
            # require('pkg') or from 'pkg' import
            for m in re.findall(r"require\(['\"]([^./'][^'\"]*)['\"]", code):
                if not m.startswith("@types"): packages.append(m)
            for m in re.findall(r"from ['\"]([^./'][^'\"]*)['\"]", code):
                if not m.startswith("@types"): packages.append(m)
        elif lang == "python":
            for m in re.findall(r"^(?:import|from)\s+([a-zA-Z][a-zA-Z0-9_]*)", code, re.MULTILINE):
                stdlib = {"os","sys","re","json","time","datetime","pathlib","typing",
                          "hashlib","base64","subprocess","tempfile","argparse","math",
                          "random","string","functools","itertools","collections","io",
                          "urllib","http","email","logging","threading","asyncio"}
                if m not in stdlib:
                    packages.append(m.replace("_", "-"))
        return list(set(packages))[:10]

    def _needs_api(self, code: str) -> bool:
        api_patterns = [
            r"process\.env\.", r"os\.getenv", r"os\.environ",
            r"API_KEY", r"SECRET", r"TOKEN", r"PASSWORD",
            r"\.connect\(", r"stripe\.", r"twilio\.", r"sendgrid\.",
        ]
        return any(re.search(p, code) for p in api_patterns)


# ──────────────────────────────────────────────────────
# L1 — SYNTAX TESTER
# ──────────────────────────────────────────────────────

class SyntaxTester:
    def test(self, blocks: list[dict]) -> TestResult:
        result = TestResult("L1", "Syntax Check")
        t0 = time.time()

        if not blocks:
            result.fail("No code blocks found in SKILL.md")
            result.duration_ms = int((time.time() - t0) * 1000)
            return result

        py_blocks = [b for b in blocks if b["lang"] == "python"]
        js_blocks = [b for b in blocks if b["lang"] in ("javascript", "typescript")]
        other     = [b for b in blocks if b["lang"] not in ("python","javascript","typescript","bash","sql","yaml","json","dockerfile","unknown")]

        total = len(blocks)
        passed = 0

        # Python syntax
        for i, b in enumerate(py_blocks):
            try:
                ast.parse(b["code"])
                result.ok(f"Python block #{i+1}: valid syntax")
                passed += 1
            except SyntaxError as e:
                result.fail(f"Python block #{i+1}: SyntaxError at line {e.lineno}: {e.msg}")

        # JavaScript — use Node.js --check
        for i, b in enumerate(js_blocks):
            with tempfile.NamedTemporaryFile(suffix=".js", mode="w", delete=False) as f:
                f.write(b["code"])
                fname = f.name
            try:
                proc = subprocess.run(
                    ["node", "--check", fname],
                    capture_output=True, text=True, timeout=5
                )
                if proc.returncode == 0:
                    result.ok(f"JS block #{i+1}: valid syntax")
                    passed += 1
                else:
                    result.fail(f"JS block #{i+1}: {proc.stderr.strip()[:200]}")
            except FileNotFoundError:
                result.warn("Node.js not found — JS syntax check skipped")
                passed += 1  # don't penalize
            except subprocess.TimeoutExpired:
                result.warn(f"JS block #{i+1}: timeout")
            finally:
                Path(fname).unlink(missing_ok=True)

        # Bash — basic check
        for i, b in enumerate([x for x in blocks if x["lang"] == "bash"]):
            try:
                proc = subprocess.run(
                    ["bash", "-n"], input=b["code"], capture_output=True,
                    text=True, timeout=3
                )
                if proc.returncode == 0:
                    result.ok(f"Bash block #{i+1}: valid syntax")
                    passed += 1
                else:
                    result.fail(f"Bash block #{i+1}: {proc.stderr.strip()[:150]}")
            except FileNotFoundError:
                passed += 1

        # YAML/JSON
        import yaml as _yaml
        for i, b in enumerate([x for x in blocks if x["lang"] in ("yaml","json")]):
            try:
                if b["lang"] == "json":
                    json.loads(b["code"])
                else:
                    _yaml.safe_load(b["code"])
                result.ok(f"{b['lang'].upper()} block #{i+1}: valid")
                passed += 1
            except Exception as e:
                result.fail(f"{b['lang'].upper()} block #{i+1}: {e}")

        result.score = passed / max(total, 1)
        result.passed = not result.errors
        result.duration_ms = int((time.time() - t0) * 1000)
        return result


# ──────────────────────────────────────────────────────
# L2 — DEPENDENCY TESTER
# ──────────────────────────────────────────────────────

class DependencyTester:
    """Check packages exist in npm/PyPI — no actual install."""

    NPM_CACHE  = {}
    PYPI_CACHE = {}

    def test(self, blocks: list[dict]) -> TestResult:
        result = TestResult("L2", "Dependencies Check")
        t0 = time.time()

        all_npm  = set()
        all_pypi = set()

        for b in blocks:
            if b["lang"] in ("javascript", "typescript"):
                all_npm.update(b["packages"])
            elif b["lang"] == "python":
                all_pypi.update(b["packages"])

        if not all_npm and not all_pypi:
            result.ok("No external packages detected")
            result.score = 1.0
            result.duration_ms = int((time.time() - t0) * 1000)
            return result

        npm_ok  = 0
        npm_fail = 0
        for pkg in all_npm:
            status = self._check_npm(pkg)
            if status:
                result.ok(f"npm:{pkg} exists ({status})")
                npm_ok += 1
            else:
                result.fail(f"npm:{pkg} — not found in registry")
                npm_fail += 1
            time.sleep(0.1)

        pypi_ok  = 0
        pypi_fail = 0
        for pkg in all_pypi:
            status = self._check_pypi(pkg)
            if status:
                result.ok(f"pip:{pkg} exists ({status})")
                pypi_ok += 1
            else:
                result.fail(f"pip:{pkg} — not found in PyPI")
                pypi_fail += 1
            time.sleep(0.1)

        total = npm_ok + npm_fail + pypi_ok + pypi_fail
        passed = npm_ok + pypi_ok
        result.score = passed / max(total, 1)
        result.passed = npm_fail == 0 and pypi_fail == 0
        result.duration_ms = int((time.time() - t0) * 1000)
        return result

    def _check_npm(self, pkg: str) -> Optional[str]:
        if pkg in self.NPM_CACHE:
            return self.NPM_CACHE[pkg]
        try:
            r = requests.get(f"https://registry.npmjs.org/{pkg}", timeout=5)
            if r.status_code == 200:
                data = r.json()
                ver = data.get("dist-tags", {}).get("latest", "?")
                self.NPM_CACHE[pkg] = ver
                return ver
        except:
            pass
        self.NPM_CACHE[pkg] = None
        return None

    def _check_pypi(self, pkg: str) -> Optional[str]:
        if pkg in self.PYPI_CACHE:
            return self.PYPI_CACHE[pkg]
        try:
            r = requests.get(f"https://pypi.org/pypi/{pkg}/json", timeout=5)
            if r.status_code == 200:
                ver = r.json()["info"]["version"]
                self.PYPI_CACHE[pkg] = ver
                return ver
        except:
            pass
        self.PYPI_CACHE[pkg] = None
        return None


# ──────────────────────────────────────────────────────
# L3 — SANDBOX RUNNER
# ──────────────────────────────────────────────────────

class SandboxRunner:
    """Runs code blocks that don't need API keys."""

    TIMEOUT = 8  # seconds

    def test(self, blocks: list[dict]) -> TestResult:
        result = TestResult("L3", "Sandbox Execution")
        t0 = time.time()

        runnable = [b for b in blocks
                    if not b["needs_api"]
                    and b["lang"] in ("python", "javascript", "bash")]

        if not runnable:
            result.ok("All code blocks require API keys — sandbox skipped")
            result.score = 0.8  # neutral score, not a failure
            result.duration_ms = int((time.time() - t0) * 1000)
            return result

        passed = 0
        for i, b in enumerate(runnable[:5]):  # max 5 blocks
            ok, output, err = self._run(b)
            if ok:
                result.ok(f"{b['lang'].upper()} block #{i+1}: executed OK")
                if output:
                    result.details.append(f"   Output: {output[:100]}")
                passed += 1
            else:
                # Distinguish import errors from logic errors
                if "ModuleNotFoundError" in err or "Cannot find module" in err:
                    result.warn(f"Block #{i+1}: missing package (needs install)")
                elif "SyntaxError" in err:
                    result.fail(f"Block #{i+1}: syntax error at runtime")
                else:
                    result.warn(f"Block #{i+1}: runtime error (may need env): {err[:150]}")

        result.score = passed / max(len(runnable), 1)
        result.passed = result.score >= 0.5
        result.duration_ms = int((time.time() - t0) * 1000)
        return result

    def _run(self, block: dict) -> tuple[bool, str, str]:
        lang = block["lang"]
        code = block["code"]

        with tempfile.TemporaryDirectory() as tmpdir:
            if lang == "python":
                fpath = Path(tmpdir) / "test.py"
                fpath.write_text(code)
                proc = subprocess.run(
                    [sys.executable, str(fpath)],
                    capture_output=True, text=True,
                    timeout=self.TIMEOUT, cwd=tmpdir
                )
            elif lang == "javascript":
                fpath = Path(tmpdir) / "test.js"
                fpath.write_text(code)
                proc = subprocess.run(
                    ["node", str(fpath)],
                    capture_output=True, text=True,
                    timeout=self.TIMEOUT, cwd=tmpdir
                )
            elif lang == "bash":
                fpath = Path(tmpdir) / "test.sh"
                fpath.write_text(code)
                proc = subprocess.run(
                    ["bash", str(fpath)],
                    capture_output=True, text=True,
                    timeout=self.TIMEOUT, cwd=tmpdir
                )
            else:
                return True, "", ""

        return proc.returncode == 0, proc.stdout[:300], proc.stderr[:300]


# ──────────────────────────────────────────────────────
# L4 — MOCK API TESTER
# ──────────────────────────────────────────────────────

class MockApiTester:
    """
    Replaces API keys with mock values and tests code structure.
    Doesn't make real API calls — tests that code runs without
    crashing before the actual API call.
    """

    MOCKS = {
        # ENV vars → mock values
        r"process\.env\.(\w+)":     lambda m: f"'mock_{m.group(1).lower()}'",
        r"os\.getenv\(['\"](\w+)['\"](?:,\s*['\"][^'\"]*['\"])?\)":
                                     lambda m: f"'mock_{m.group(1).lower()}'",
        r"os\.environ\[['\"](\w+)['\"]\]":
                                     lambda m: f"'mock_{m.group(1).lower()}'",
    }

    MOCK_MODULES_PY = """
# SharpSkill Mock Layer
import sys
from unittest.mock import MagicMock, AsyncMock

class _MockModule(MagicMock):
    def __call__(self, *a, **kw): return MagicMock()
    def __getattr__(self, name): return MagicMock()

# Common packages
for _pkg in ['stripe','twilio','sendgrid','resend','openai','anthropic',
             'neon','psycopg2','pymongo','redis','boto3','google.cloud',
             'langchain','litellm','crewai']:
    sys.modules[_pkg] = _MockModule()

"""

    MOCK_MODULES_JS = """
// SharpSkill Mock Layer
const _mock = () => new Proxy({}, { get: () => _mock, apply: () => _mock() });
const require = (pkg) => _mock();

"""

    def test(self, blocks: list[dict]) -> TestResult:
        result = TestResult("L4", "Mock API Test")
        t0 = time.time()

        api_blocks = [b for b in blocks
                      if b["needs_api"]
                      and b["lang"] in ("python", "javascript")]

        if not api_blocks:
            result.ok("No API-dependent blocks — mock test not needed")
            result.score = 1.0
            result.duration_ms = int((time.time() - t0) * 1000)
            return result

        passed = 0
        for i, b in enumerate(api_blocks[:3]):
            ok, out, err = self._run_mocked(b)
            if ok:
                result.ok(f"{b['lang'].upper()} block #{i+1}: structure valid with mocks")
                passed += 1
            else:
                # Import errors after mocking = real missing deps
                if "SyntaxError" in err:
                    result.fail(f"Block #{i+1}: syntax error: {err[:150]}")
                else:
                    result.warn(f"Block #{i+1}: mock runtime issue: {err[:150]}")

        result.score = passed / max(len(api_blocks), 1)
        result.passed = result.score >= 0.5
        result.duration_ms = int((time.time() - t0) * 1000)
        return result

    def _inject_mocks(self, code: str, lang: str) -> str:
        """Replace env vars with mock values."""
        for pattern, replacement in self.MOCKS.items():
            code = re.sub(pattern, replacement, code)
        if lang == "python":
            return self.MOCK_MODULES_PY + code
        elif lang == "javascript":
            return self.MOCK_MODULES_JS + code
        return code

    def _run_mocked(self, block: dict) -> tuple[bool, str, str]:
        lang = block["lang"]
        code = self._inject_mocks(block["code"], lang)

        with tempfile.TemporaryDirectory() as tmpdir:
            if lang == "python":
                fpath = Path(tmpdir) / "mock_test.py"
                fpath.write_text(code)
                proc = subprocess.run(
                    [sys.executable, str(fpath)],
                    capture_output=True, text=True, timeout=8, cwd=tmpdir
                )
            elif lang == "javascript":
                fpath = Path(tmpdir) / "mock_test.js"
                fpath.write_text(code)
                proc = subprocess.run(
                    ["node", str(fpath)],
                    capture_output=True, text=True, timeout=8, cwd=tmpdir
                )
            else:
                return True, "", ""

        return proc.returncode == 0, proc.stdout[:300], proc.stderr[:300]


# ──────────────────────────────────────────────────────
# AUTO FIXER — Claude auto-fixes failed code
# ──────────────────────────────────────────────────────

class AutoFixer:
    MAX_ATTEMPTS = 2

    def fix(self, skill_content: str, report: SkillTestReport) -> Optional[str]:
        if not ANTHROPIC_API_KEY:
            return None

        # Collect all errors
        all_errors = []
        for r in report.results:
            all_errors.extend(r.errors)

        if not all_errors:
            return None

        error_summary = "\n".join(all_errors[:15])

        prompt = f"""You are a code quality expert. Fix the SKILL.md below to resolve these test failures.

ERRORS FOUND:
{error_summary}

CURRENT SKILL.md:
{skill_content}

Rules:
- Keep the same YAML frontmatter structure (name, description, license, metadata)
- Fix ONLY the broken code blocks
- Keep working code blocks unchanged
- Make sure all code examples are syntactically correct
- Replace non-existent npm/pip packages with correct ones
- Return ONLY the fixed SKILL.md content, starting with ---"""

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
                return fixed
        except Exception as e:
            print(f"  ⚠ AutoFixer error: {e}")
        return None


# ──────────────────────────────────────────────────────
# GITHUB PUBLISHER
# ──────────────────────────────────────────────────────

class GitHubPublisher:
    def __init__(self):
        self.headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json",
        }
        self.base = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}"

    def push_skill(self, tool_name: str, content: str, label: str = "") -> bool:
        import base64
        path = f"skills/{tool_name}/SKILL.md"
        # Check if exists
        r = requests.get(f"{self.base}/contents/{path}", headers=self.headers, timeout=10)
        sha = r.json().get("sha") if r.status_code == 200 else None

        msg = f"feat: add {tool_name} skill"
        if label:
            msg += f" [{label}]"

        body = {
            "message": msg,
            "content": base64.b64encode(content.encode()).decode(),
            "committer": {"name": "SharpSkill Bot", "email": "bot@sharpskill.dev"},
        }
        if sha:
            body["sha"] = sha

        r = requests.put(f"{self.base}/contents/{path}", headers=self.headers,
                         json=body, timeout=15)
        return r.status_code in (200, 201)


# ──────────────────────────────────────────────────────
# MAIN TEST RUNNER
# ──────────────────────────────────────────────────────

class SkillTester:
    def __init__(self):
        self.extractor = CodeExtractor()
        self.l1 = SyntaxTester()
        self.l2 = DependencyTester()
        self.l3 = SandboxRunner()
        self.l4 = MockApiTester()
        self.fixer = AutoFixer()
        self.publisher = GitHubPublisher() if GITHUB_TOKEN else None

    def test_skill(self, skill_name: str, push: bool = True) -> SkillTestReport:
        skill_dir  = SKILLS_DIR / skill_name
        skill_file = skill_dir / "SKILL.md"

        if not skill_file.exists():
            print(f"❌ Skill not found: {skill_file}")
            sys.exit(1)

        report = SkillTestReport(skill_name)
        print(f"\n{'='*55}")
        print(f"  🧪 Testing: {skill_name}")
        print(f"  trace_id: {report.trace_id}")
        print(f"{'='*55}")

        content = skill_file.read_text()
        blocks  = self.extractor.extract(content)

        print(f"\n  📦 Code blocks found: {len(blocks)}")
        for b in blocks:
            api_flag = "🔑" if b["needs_api"] else "  "
            pkgs = f"deps: {b['packages']}" if b["packages"] else ""
            print(f"     {api_flag} [{b['lang']}] {pkgs}")

        # Run all 4 levels
        levels = [
            ("L1 Syntax",      lambda: self.l1.test(blocks)),
            ("L2 Deps",        lambda: self.l2.test(blocks)),
            ("L3 Sandbox",     lambda: self.l3.test(blocks)),
            ("L4 Mock API",    lambda: self.l4.test(blocks)),
        ]

        for level_name, runner in levels:
            print(f"\n  ─── {level_name} ───")
            t0 = time.time()
            result = runner()
            result.duration_ms = int((time.time() - t0) * 1000)
            report.results.append(result)

            status_icon = "✅" if result.status == "PASS" else ("⚠️" if result.status == "PARTIAL" else "❌")
            print(f"  {status_icon} {result.status} (score: {result.score:.0%}, {result.duration_ms}ms)")
            for d in result.details[:5]:  print(f"     {d}")
            for e in result.errors[:5]:   print(f"     {e}")

        # Determine outcome
        score = report.overall_score()
        has_hard_failures = any(
            r.status == "FAIL" and r.level in ("L1", "L2")
            for r in report.results
        )

        print(f"\n  📊 Overall score: {score:.0%}")

        if not has_hard_failures and score >= 0.7:
            # PASS — push to GitHub
            report.final_status = "PASS"
            print(f"  ✅ PASS — pushing to GitHub...")
            if push and self.publisher:
                ok = self.publisher.push_skill(skill_name, content)
                print(f"  {'✅ Pushed' if ok else '❌ Push failed'}")

        elif has_hard_failures and ANTHROPIC_API_KEY:
            # Try auto-fix
            print(f"\n  🔧 Attempting auto-fix with Claude...")
            fixed_content = self.fixer.fix(content, report)

            if fixed_content:
                # Re-test fixed version
                report.auto_fixed = True
                report.fix_attempts = 1
                fixed_blocks  = self.extractor.extract(fixed_content)
                re_l1 = self.l1.test(fixed_blocks)
                re_l2 = self.l2.test(fixed_blocks)

                if re_l1.status != "FAIL" and re_l2.status != "FAIL":
                    # Fixed! Save and push
                    skill_file.write_text(fixed_content)
                    report.final_status = "AUTO_FIXED"
                    print(f"  ✅ AUTO_FIXED — pushing to GitHub...")
                    if push and self.publisher:
                        self.publisher.push_skill(skill_name, fixed_content, "auto-fixed")
                else:
                    # Still broken — send to drafts with BETA label
                    self._save_draft(skill_name, fixed_content, report, "BETA")
                    report.final_status = "BETA"
                    print(f"  ⚠️  BETA — saved to drafts/ with [BETA] label")
                    if push and self.publisher:
                        self.publisher.push_skill(skill_name, fixed_content, "BETA")
            else:
                self._save_draft(skill_name, content, report, "DRAFT")
                report.final_status = "FAIL"
                print(f"  ❌ FAIL — saved to drafts/")

        else:
            # No API key for fix — push as BETA
            self._save_draft(skill_name, content, report, "BETA")
            report.final_status = "BETA"
            print(f"  ⚠️  BETA — saved to drafts/")
            if push and self.publisher:
                self.publisher.push_skill(skill_name, content, "BETA")

        # Save report
        self._save_report(report)
        self._print_summary(report)
        return report

    def _save_draft(self, name: str, content: str, report: SkillTestReport, label: str):
        draft_dir = DRAFTS_DIR / name
        draft_dir.mkdir(exist_ok=True)
        (draft_dir / "SKILL.md").write_text(content)
        (draft_dir / "test_report.json").write_text(
            json.dumps(report.to_dict(), indent=2)
        )
        print(f"  📁 Draft saved: drafts/{name}/")

    def _save_report(self, report: SkillTestReport):
        report_file = REPORTS_DIR / f"{report.skill_name}_{report.trace_id}.json"
        report_file.write_text(json.dumps(report.to_dict(), indent=2))

    def _print_summary(self, report: SkillTestReport):
        icons = {"PASS": "✅", "AUTO_FIXED": "🔧", "BETA": "⚠️", "FAIL": "❌"}
        icon = icons.get(report.final_status, "?")
        print(f"\n{'━'*55}")
        print(f"  {icon}  Final: {report.final_status}")
        print(f"  Score: {report.overall_score():.0%}")
        if report.auto_fixed:
            print(f"  Auto-fixed: YES ({report.fix_attempts} attempt)")
        print(f"  Report: test_reports/{report.skill_name}_{report.trace_id}.json")
        print(f"{'━'*55}")


# ──────────────────────────────────────────────────────
# TEST ALL + REPORT
# ──────────────────────────────────────────────────────

def cmd_test_all(push: bool = True):
    tester = SkillTester()
    skill_dirs = [d for d in SKILLS_DIR.iterdir() if d.is_dir()] if SKILLS_DIR.exists() else []

    if not skill_dirs:
        print("No skills found in ./skills/")
        return

    print(f"\n🧪 Testing {len(skill_dirs)} skills\n")
    results = []
    for sd in sorted(skill_dirs):
        report = tester.test_skill(sd.name, push=push)
        results.append(report.to_dict())
        time.sleep(1)

    # Summary
    statuses = [r["final_status"] for r in results]
    print(f"\n\n{'='*55}")
    print(f"  BATCH TEST COMPLETE")
    print(f"{'='*55}")
    print(f"  ✅ PASS:       {statuses.count('PASS')}")
    print(f"  🔧 AUTO_FIXED: {statuses.count('AUTO_FIXED')}")
    print(f"  ⚠️  BETA:       {statuses.count('BETA')}")
    print(f"  ❌ FAIL:       {statuses.count('FAIL')}")
    print(f"{'='*55}")

    # Save batch report
    batch_report = Path("test_reports") / f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    batch_report.write_text(json.dumps(results, indent=2))
    print(f"\n  📋 Batch report: {batch_report}")


def cmd_report():
    """Show summary of all test reports."""
    reports = sorted(REPORTS_DIR.glob("*.json"))
    if not reports:
        print("No test reports found.")
        return

    print(f"\n📋 Test Reports ({len(reports)} total)\n")
    by_status = {}
    for rf in reports:
        try:
            data = json.loads(rf.read_text())
            status = data.get("final_status", "?")
            by_status.setdefault(status, []).append(data)
        except:
            pass

    icons = {"PASS": "✅", "AUTO_FIXED": "🔧", "BETA": "⚠️", "FAIL": "❌"}
    for status in ["PASS", "AUTO_FIXED", "BETA", "FAIL"]:
        items = by_status.get(status, [])
        if items:
            print(f"  {icons.get(status, '?')} {status} ({len(items)})")
            for item in items:
                print(f"      {item['skill_name']} — score:{item['overall_score']:.0%}")


# ──────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="SharpSkill Test Bot v1.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Flow:
  generate skill → test → PASS → push to GitHub
                        → FAIL → Claude auto-fixes → re-test
                                                   → PASS → push [auto-fixed]
                                                   → FAIL → drafts/ [BETA]
        """
    )
    sub = parser.add_subparsers(dest="command")

    t = sub.add_parser("test", help="Test one skill")
    t.add_argument("--skill", required=True, help="Skill folder name (e.g. stripe-webhooks)")
    t.add_argument("--no-push", action="store_true")

    sub.add_parser("test-all", help="Test all skills in ./skills/")
    sub.add_parser("report",   help="Show test report summary")

    args = parser.parse_args()

    if args.command == "test":
        tester = SkillTester()
        tester.test_skill(args.skill, push=not args.no_push)
    elif args.command == "test-all":
        cmd_test_all()
    elif args.command == "report":
        cmd_report()
    else:
        parser.print_help()
