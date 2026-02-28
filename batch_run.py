#!/usr/bin/env python3
"""SharpSkills Batch Runner"""
import subprocess, sys, time
from pathlib import Path

TOOLS_FILE = "tools_priority.txt"
LOG_FILE   = "batch_run.log"
PUSH       = "--no-push" not in sys.argv

tools = [t.strip() for t in Path(TOOLS_FILE).read_text().splitlines() if t.strip()]
print(f"Batch run: {len(tools)} tools | Push: {PUSH}")
print("="*55)

results = {"pass": [], "skip": [], "fail": [], "error": []}

for i, tool in enumerate(tools, 1):
    print(f"\n[{i}/{len(tools)}] {tool}")
    cmd = ["python3", "sharpskill.py", "run", "--tool", tool]
    if not PUSH:
        cmd.append("--no-push")
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        out = r.stdout + r.stderr
        if "SKIPPED" in out:
            print("  SKIP")
            results["skip"].append(tool)
        elif "PASS" in out and "Score:" in out:
            score = next((l for l in out.splitlines() if "Score:" in l), "")
            print(f"  PASS {score.strip()}")
            results["pass"].append(tool)
        elif "FAIL" in out:
            print("  FAIL")
            results["fail"].append(tool)
        else:
            print("  UNKNOWN")
            results["error"].append(tool)
        with open(LOG_FILE, "a") as f:
            f.write(f"\n{'='*40}\n{tool}\n{out}\n")
    except subprocess.TimeoutExpired:
        print("  TIMEOUT")
        results["error"].append(tool)
    except Exception as e:
        print(f"  ERROR: {e}")
        results["error"].append(tool)
    time.sleep(1)

print(f"\n{'='*55}")
print(f"PASS:  {len(results['pass'])} - {', '.join(results['pass'])}")
print(f"SKIP:  {len(results['skip'])}")
print(f"FAIL:  {len(results['fail'])} - {', '.join(results['fail'])}")
print(f"ERROR: {len(results['error'])} - {', '.join(results['error'])}")
