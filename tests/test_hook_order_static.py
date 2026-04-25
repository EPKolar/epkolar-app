"""Statischer Hook-Order-Linter — Schutz gegen React-#310-Regression (v3.8.50 Hotfix).

Hintergrund: Vor dem Hotfix gab es einen `setKat`-Call innerhalb eines useEffect,
der NACH dem `if(appLoading) return ...` stand. React-Komponenten muessen aber
ALLE Hook-Calls VOR jedem early-return haben, sonst wechselt die Hook-Ordnung
zwischen Renders -> Error #310.

Die Tests scannen den kompilierten App-Body in index.html statisch:
  - test_no_hook_after_early_return_in_App: HARTE Assertion. Im Body von
    `function App(){ ... }` darf zwischen dem ersten und letzten return-at-indent-2
    KEIN React-Hook-Call (useState/useEffect/useRef/useMemo/useCallback) auf
    indent 2 liegen.
  - test_no_hook_after_early_return_general: SOFT-Check fuer alle anderen
    PascalCase-Komponenten. Nur wenn App betroffen waere, faellt der Test
    hart durch (App-Pfad ist abgedeckt vom ersten Test, deshalb nur Warning
    via stdout fuer Rest).
"""

from __future__ import annotations

import re
from pathlib import Path

INDEX = Path(__file__).resolve().parent.parent / "index.html"

HOOK_RE = re.compile(r"^  _react\.(useState|useEffect|useRef|useMemo|useCallback)\b")
RETURN_RE = re.compile(r"^  (if\s*\([^)]*\)\s*return\b|return\b)")
APP_OPEN_RE = re.compile(r"^\s*function\s+App\s*\(\s*\)\s*\{")
COMP_OPEN_RE = re.compile(r"^\s*function\s+([A-Z][A-Za-z0-9_]*)\s*\(")
APP_END_RE = re.compile(r"^\s{0,1}\}")


def _load_lines() -> list[str]:
    return INDEX.read_text(encoding="utf-8").splitlines(keepends=True)


def _function_span(lines: list[str], start_idx: int) -> int:
    """Return the line-index (exclusive) where the top-level function ends.

    Heuristic: first line after `start_idx` whose dedent matches "}" at column 0
    or 1 (the bundled output uses indent 1 for top-level closers).
    """
    for i in range(start_idx + 1, len(lines)):
        if APP_END_RE.match(lines[i].rstrip()):
            return i
    return len(lines)


def _violations_in_span(lines: list[str], start: int, end: int) -> list[int]:
    """Return line-indices of hook calls that appear between the first and
    last return-at-indent-2 inside [start, end)."""
    returns: list[int] = []
    hooks: list[int] = []
    for i in range(start + 1, end):
        if RETURN_RE.match(lines[i]):
            returns.append(i)
        if HOOK_RE.match(lines[i]):
            hooks.append(i)
    if len(returns) < 2:
        return []
    first_ret, last_ret = returns[0], returns[-1]
    return [h for h in hooks if first_ret < h < last_ret]


def test_no_hook_after_early_return_in_App() -> None:
    lines = _load_lines()
    app_start = None
    for i, line in enumerate(lines):
        if APP_OPEN_RE.match(line):
            app_start = i
            break
    assert app_start is not None, "function App() not found in index.html"
    app_end = _function_span(lines, app_start)

    violations = _violations_in_span(lines, app_start, app_end)
    sample = "\n".join(
        f"  L{v + 1}: {lines[v].rstrip()[:120]}" for v in violations[:5]
    )
    assert not violations, (
        f"React-Hook(s) zwischen erstem und letztem return im App-Body "
        f"gefunden ({len(violations)}) — verletzt Rules of Hooks und kann "
        f"React-#310 ausloesen.\nFundstellen:\n{sample}"
    )


def test_no_hook_after_early_return_general() -> None:
    lines = _load_lines()
    flagged: list[tuple[str, int, int]] = []
    i = 0
    while i < len(lines):
        m = COMP_OPEN_RE.match(lines[i])
        if not m:
            i += 1
            continue
        name = m.group(1)
        if name == "App":
            i += 1
            continue
        end = _function_span(lines, i)
        violations = _violations_in_span(lines, i, end)
        if violations:
            flagged.append((name, i + 1, len(violations)))
        i = end + 1

    if flagged:
        msg = ", ".join(
            f"{n}@L{ln} ({c} Hook(s) zw. Returns)" for n, ln, c in flagged[:10]
        )
        print(
            f"[soft-flag] Hook-Order-Verdacht in {len(flagged)} Komponente(n): "
            f"{msg}"
        )
