#!/usr/bin/env python3
"""A stand-in content-quality judge for tests: emits a JSON verdict, no model.
Proves the --judge-cmd seam wires end-to-end and stays advisory. Not shipped as
a real judge — a real one calls a model (see references/judge.md)."""
import json
print(json.dumps({"score": 78, "label": "warn",
                  "findings": [{"i": 2, "severity": "low",
                                "reason": "engineer step confidence below target"}]}))
