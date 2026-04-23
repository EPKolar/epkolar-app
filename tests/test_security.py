"""Security invariants — no obvious injection sinks."""
import re


def test_no_eval_calls(index_html):
    # Allow eval in comments/strings, flag on bare function calls.
    # Simple heuristic: find "eval(" NOT preceded by a letter.
    hits = [(m.start(), m.group(0)) for m in re.finditer(r"(?<![A-Za-z_])eval\s*\(", index_html)]
    # Filter out cases inside quoted strings (cheap check: same line starts with quote)
    real = []
    for pos, snippet in hits:
        line_start = index_html.rfind("\n", 0, pos) + 1
        line_end = index_html.find("\n", pos)
        line = index_html[line_start:line_end if line_end != -1 else len(index_html)]
        # Skip if line contains a quote before the eval
        before_eval = line[: pos - line_start]
        if before_eval.count('"') % 2 == 1 or before_eval.count("'") % 2 == 1:
            continue
        real.append((pos, line.strip()))
    assert not real, f"Unexpected eval() calls: {real[:3]}"


def test_no_toplevel_document_write(index_html):
    # document.write on the main document is banned (it re-opens and destroys the DOM).
    # But <win>.document.write() on a freshly opened print window is legit (controlled HTML
    # for the print iframe / popup).
    lines = index_html.splitlines()
    bad = []
    for i, line in enumerate(lines, 1):
        # match " document.write" (leading space/tab/semicolon) but not "<var>.document.write"
        stripped = line.lstrip()
        if "document.write" in stripped and ".document.write" not in stripped[:200]:
            # Still could be inside a child-window context if we miss the prefix —
            # the safer filter is: the position right before "document.write" is NOT
            # an identifier char.
            pos = stripped.find("document.write")
            prev = stripped[pos - 1] if pos > 0 else ""
            if prev not in ("." , "_") and not prev.isalnum():
                bad.append((i, stripped[:120]))
    assert not bad, f"top-level document.write calls found: {bad[:3]}"


def test_no_function_constructor(index_html):
    # new Function(...) is as bad as eval
    assert not re.search(r"\bnew\s+Function\s*\(", index_html), "new Function(...) not allowed"


def test_offline_pw_is_not_plain_base64_write(index_html):
    # Regression guard for v3.8.33: make sure we no longer write btoa(user+":"+pw)
    legacy = re.search(r'offlinePwHash",\s*btoa\s*\(', index_html)
    assert not legacy, "Legacy plain-btoa write to offlinePwHash detected (must use _OFFPW.create)"
