"""
_pdfStr Transliteration (v3.9.841) — lesbare PDFs für alle Generatoren.

jsPDF-Standardfont kann nur latin1 (WinAnsi). Vorher entfernte _pdfStr JEDES
Nicht-latin1-Zeichen still — auch Gedankenstriche, typografische Anführungszeichen
und technische Symbole (Ω/μ) aus User-Text/Messwerten. Jetzt: erst transliterieren,
dann strippen. Betrifft Ticket-/Plan-Report-/Checklisten-/PZE-PDF.
"""
import re
import json
from conftest import run_node_snippet


def _pdfstr_src(index_html):
    m = re.search(r"function _pdfStr\(s\)\{return.*?\.trim\(\);\}", index_html, re.S)
    assert m, "_pdfStr nicht gefunden"
    return m.group(0)


def test_transliteration_via_node(index_html, node_exe):
    src = _pdfstr_src(index_html)
    cases = [
        ["a – b", "a - b"],       # en-dash
        ["a — b", "a - b"],       # em-dash
        ["„Titel“", '"Titel"'],  # „ "
        ["5 Ω", "5 Ohm"],         # Ohm (greek Omega)
        ["5 Ω", "5 Ohm"],         # Ohm sign
        ["μF", "uF"],             # greek mu
        ["café", "café"],    # é ist latin1 -> bleibt
        ["a…b", "a...b"],         # …
        ["x → y", "x -> y"],      # →
        ["✅ ok", "ok"],           # Emoji -> gestrippt + getrimmt
        ["2² m", "2² m"],    # ² ist latin1 -> bleibt (wichtig: mm²)
    ]
    snippet = src + "\nconst t=" + json.dumps(cases) + ";console.log(JSON.stringify(t.map(([i,e])=>({e,g:_pdfStr(i)}))));"
    out = json.loads(run_node_snippet(node_exe, snippet))
    for row in out:
        assert row["g"] == row["e"], f"_pdfStr falsch: {row}"


def test_latin1_bleibt_erhalten(index_html):
    # die Transliteration darf latin1-Zeichen (Umlaute, ², ³, °, µ) NICHT anfassen
    src = _pdfstr_src(index_html)
    # ² ³ ° µ (0xB2/0xB3/0xB0/0xB5) tauchen NICHT als Ersetzungsziel auf
    assert "²" not in src and "³" not in src, "latin1 ²/³ faelschlich in der Transliteration"
