#!/usr/bin/env python3
"""One-shot bracket sanity for index.html.

Baseline: ( ) -2 / { } 0 / [ ] 0
Strips strings, template literals, comments before counting.
"""
import re
import sys
from pathlib import Path

target = Path(sys.argv[1] if len(sys.argv) > 1 else "index.html")
src = target.read_text(encoding="utf-8")

# Order matters: comments first, then strings.
patterns = [
    r"/\*[\s\S]*?\*/",
    r"//[^\n]*",
    r'"(?:[^"\\]|\\.)*"',
    r"'(?:[^'\\]|\\.)*'",
    r"`(?:[^`\\]|\\.)*`",
]
stripped = re.sub("|".join(patterns), "", src)

paren = stripped.count("(") - stripped.count(")")
brace = stripped.count("{") - stripped.count("}")
brack = stripped.count("[") - stripped.count("]")

print(f"() {paren}")
print(f"{{}} {brace}")
print(f"[] {brack}")

ok = paren == -2 and brace == 0 and brack == 0
sys.exit(0 if ok else 1)
