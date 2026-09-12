#!/usr/bin/env python3
"""A stand-in entailment verifier for tests: emits a JSON verdict, no model.
Reports 'partial' so the seam surfaces one advisory mis-entailment finding —
the last-mile case the lexical-overlap floor structurally cannot catch. Proves
the --entailment-cmd seam wires and stays advisory. Not a real verifier."""
import json
print(json.dumps({"entails": "partial",
                  "evidence": "source mentions the terms but does not assert the exact claim"}))
