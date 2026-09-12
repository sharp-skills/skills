#!/bin/sh
# Self-test for context-compression: the linter accepts a safe compaction config
# and catches the window-rule violation plus the ratio/protect mistakes.
cd "$(dirname "$0")" || exit 2
L=../scripts/compression_lint.py
fail=0

python3 "$L" --config compaction.good.json --models models.json >/dev/null 2>&1
[ $? -eq 0 ] && echo "PASS  safe config -> exit 0" || { echo "FAIL  good config"; fail=1; }

out=$(python3 "$L" --config compaction.bad.json --models models.json 2>&1); code=$?
[ $code -eq 1 ] && echo "PASS  bad config -> exit 1" || { echo "FAIL  bad config (got $code)"; fail=1; }
echo "$out" | grep -q "window 8192 < main model window 400000" && echo "PASS  window rule caught" || { echo "FAIL  window rule"; fail=1; }
echo "$out" | grep -q "protect_last_n must be a positive integer" && echo "PASS  protect_last_n caught" || { echo "FAIL  protect check"; fail=1; }
echo "$out" | grep -q "not below threshold" && echo "PASS  ratio thrash caught" || { echo "FAIL  ratio check"; fail=1; }

# disabled compaction is a violation
out=$(python3 - "$L" <<'PY'
import json, subprocess, sys, tempfile, os
L = sys.argv[1]
cfg = json.load(open("compaction.good.json")); cfg["enabled"] = False
fd, p = tempfile.mkstemp(suffix=".json"); os.write(fd, json.dumps(cfg).encode()); os.close(fd)
r = subprocess.run([sys.executable, L, "--config", p, "--models", "models.json"],
                   capture_output=True, text=True)
os.unlink(p); sys.stdout.write(r.stderr); sys.exit(r.returncode)
PY
); code=$?
[ $code -eq 1 ] && echo "PASS  disabled compaction -> exit 1" || { echo "FAIL  disabled (got $code)"; fail=1; }
echo "$out" | grep -q "not enabled" && echo "PASS  enabled check caught" || { echo "FAIL  enabled detail"; fail=1; }

# unknown summarizer -> can't verify window rule
out=$(python3 - "$L" <<'PY'
import json, subprocess, sys, tempfile, os
L = sys.argv[1]
cfg = json.load(open("compaction.good.json")); cfg["compaction"]["model"] = "mystery-model"
fd, p = tempfile.mkstemp(suffix=".json"); os.write(fd, json.dumps(cfg).encode()); os.close(fd)
r = subprocess.run([sys.executable, L, "--config", p, "--models", "models.json"],
                   capture_output=True, text=True)
os.unlink(p); sys.stdout.write(r.stderr); sys.exit(r.returncode)
PY
); code=$?
[ $code -eq 1 ] && echo "PASS  unknown summarizer -> exit 1" || { echo "FAIL  unknown model (got $code)"; fail=1; }
echo "$out" | grep -q "not in the catalog" && echo "PASS  unresolvable model caught" || { echo "FAIL  catalog detail"; fail=1; }

python3 "$L" --config no-such.json --models models.json >/dev/null 2>&1
[ $? -eq 2 ] && echo "PASS  missing config -> exit 2" || { echo "FAIL  input error"; fail=1; }

[ $fail -eq 0 ] && echo "SELFTEST OK" || echo "SELFTEST FAILED"
exit $fail
