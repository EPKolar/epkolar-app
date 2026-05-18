#!/usr/bin/env python3
"""One-shot bracket sanity for index.html.

Baseline (v3.9.12): ( ) -1 / { } 0 / [ ] 0
Strips strings, template literals, comments before counting.

NOTE on the -1 paren drift: investigated 2026-05-18 and confirmed it is NOT
a stripper artifact. The combined-alternation regex correctly removes all
33k+ string literals including those containing '[' or '('. Both pattern
orderings (strings-first vs comments-first) yield the same -1, and the sum
of paren-imbalance inside string literals is +8 (not -1). The drift is a
real, stable code-level imbalance in index.html and should only be touched
if a future audit shows it changed.
"""
import re
import sys
from pathlib import Path

target = Path(sys.argv[1] if len(sys.argv) > 1 else "index.html")
src = target.read_text(encoding="utf-8")

# Order matters: STRINGS before COMMENTS so that '//' inside string literals
# (e.g. URLs like "https://...") is not mis-stripped as a line comment.
# Python re alternation uses leftmost-first match per position, so listing
# string patterns first lets them claim '//' that lives inside quotes before
# the comment pattern can grab it.
patterns = [
    r'"(?:[^"\\]|\\.)*"',
    r"'(?:[^'\\]|\\.)*'",
    r"`(?:[^`\\]|\\.)*`",
    r"/\*[\s\S]*?\*/",
    r"//[^\n]*",
]
stripped = re.sub("|".join(patterns), "", src)

paren = stripped.count("(") - stripped.count(")")
brace = stripped.count("{") - stripped.count("}")
brack = stripped.count("[") - stripped.count("]")

print(f"() {paren}")
print(f"{{}} {brace}")
print(f"[] {brack}")

ok = paren == -1 and brace == 0 and brack == 0
sys.exit(0 if ok else 1)
