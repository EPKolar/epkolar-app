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
  - test_no_hook_after_early_return_general: HARTE Assertion fuer alle
    anderen PascalCase-Komponenten (v3.9.961, siehe unten).

v3.9.961 — DER ALLGEMEINE FALL WAR EIN `print`, KEIN RIEGEL
───────────────────────────────────────────────────────────
`test_no_hook_after_early_return_general` enthielt KEIN einzelnes `assert`,
nur ein `print("[soft-flag] ...")` am Ende (Befund:
docs/befunde/WAS_LAEUFT_WIRKLICH.md §2 A2). Der Docstring nannte das Absicht,
mit der Begruendung "App-Pfad ist abgedeckt vom ersten Test".

Diese Begruendung traegt nicht: der erste Test deckt AUSSCHLIESSLICH `App` ab,
die anderen 86 Komponenten deckt er gar nicht — und React-#310 entsteht in
jeder Komponente gleich. Ein `print` sieht in einem `-q`-Lauf niemand; als
Riegel konnte der Fall nicht rot werden. Die Historie liefert keine zweite
Begruendung (`git log -- tests/test_hook_order_static.py`: ein einziger
Commit, 1eb4bfc, ohne Hinweis auf eine gewollte Weichheit).

GEMESSEN VOR DEM UMBAU, 27.09.2026, gegen den heutigen Bestand:
  betrachtete Komponenten (ohne App):     86
  davon mit Hook zwischen zwei returns:    0
  Hook-Zeilen auf Einzug 2 im Bestand:   213
  return-Zeilen auf Einzug 2 im Bestand: 486
Die Menge ist also nicht leer, und die harte Zusicherung ist heute gruen. Sie
ist damit kein Umschreiben eines roten Riegels, sondern das Einschalten eines
abgeschalteten. Die Fundliste bleibt als Fehlermeldung erhalten, statt in
stdout zu verschwinden.

Der Abtaster selbst wurde NICHT angefasst: `_violations_in_span` teilen sich
beide Faelle, eine Aenderung dort haette den App-Fall mitverschoben. Seine
bekannte Grenze steht als Kommentar bei der Funktion.
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
    last return-at-indent-2 inside [start, end).

    BEKANNTE GRENZE (v3.9.961 benannt, nicht geaendert): bei `len(returns) < 2`
    gibt die Funktion leer zurueck. Eine Komponente mit GENAU EINEM
    early-return, hinter dem ein Hook steht, wird damit nicht gemeldet. Das ist
    nicht repariert worden, weil `test_no_hook_after_early_return_in_App`
    denselben Abtaster benutzt und jede Aenderung hier auch dort wirkt — eine
    Verschaerfung gehoert gemessen und einzeln beurteilt, nicht im
    Vorbeigehen. Es ist ein Loch im Riegel, kein Mangel in index.html.
    """
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


def komponenten(lines: list[str]) -> list[tuple[str, int, int]]:
    """(name, start_idx, end_idx) je PascalCase-Komponente ausser `App`.

    Der Gang durch die Datei ist woertlich der aus der Fassung vor v3.9.961 —
    nur herausgezogen, damit die Koeder unten ihn mit selbstgebauten Zeilen
    fuettern koennen. Ohne diesen Schnitt haette der Riegel keine Selbstprobe,
    und ein blind gewordener Abtaster waere wieder gruen.
    """
    aus: list[tuple[str, int, int]] = []
    i = 0
    while i < len(lines):
        m = COMP_OPEN_RE.match(lines[i])
        if not m:
            i += 1
            continue
        if m.group(1) == "App":
            i += 1
            continue
        end = _function_span(lines, i)
        aus.append((m.group(1), i, end))
        i = end + 1
    return aus


def verdachte(lines: list[str]) -> list[tuple[str, int, int]]:
    """(name, zeilennummer, anzahl) je Komponente mit Hook zwischen Returns."""
    aus: list[tuple[str, int, int]] = []
    for name, start, end in komponenten(lines):
        v = _violations_in_span(lines, start, end)
        if v:
            aus.append((name, start + 1, len(v)))
    return aus


# Untergrenzen der Grundgesamtheit, gemessen am 27.09.2026 (86 / 213 / 486).
# Bewusst weit unter dem Messwert: dieser Riegel soll rot werden, wenn die
# Abtaster den Bestand NICHT MEHR TREFFEN, nicht wenn jemand eine Komponente
# umbaut.
_MIND_KOMPONENTEN = 40
_MIND_HOOKZEILEN = 100
_MIND_RETURNZEILEN = 100


def test_selbstprobe_die_anker_treffen_den_bestand() -> None:
    """Die stille Form, gegen die BEIDE Faelle dieser Datei wehrlos waeren.

    HOOK_RE und RETURN_RE haengen an der Schreibweise des Buendels
    (`  _react.useState(`, Einzug 2). Aendert der Erzeuger diese Schreibweise,
    treffen beide Ausdruecke NULL Zeilen — und dann melden
    `test_no_hook_after_early_return_in_App` UND der allgemeine Fall gruen,
    ohne etwas gemessen zu haben. Eine leere Grundgesamtheit besteht keine
    Probe, also wird sie hier belegt statt vorausgesetzt.
    """
    lines = _load_lines()
    hooks = sum(1 for ln in lines if HOOK_RE.match(ln))
    returns = sum(1 for ln in lines if RETURN_RE.match(ln))
    komps = komponenten(lines)
    assert len(komps) >= _MIND_KOMPONENTEN, (
        f"Nur {len(komps)} PascalCase-Komponenten gefunden (erwartet "
        f">={_MIND_KOMPONENTEN}, gemessen 86) — COMP_OPEN_RE trifft den "
        f"Bestand nicht mehr, der Riegel unten urteilt ueber fast nichts."
    )
    assert hooks >= _MIND_HOOKZEILEN, (
        f"Nur {hooks} Hook-Zeilen auf Einzug 2 gefunden (erwartet "
        f">={_MIND_HOOKZEILEN}, gemessen 213) — HOOK_RE trifft die Schreibweise "
        f"des Buendels nicht mehr. Beide Faelle dieser Datei waeren damit "
        f"still gruen."
    )
    assert returns >= _MIND_RETURNZEILEN, (
        f"Nur {returns} return-Zeilen auf Einzug 2 gefunden (erwartet "
        f">={_MIND_RETURNZEILEN}, gemessen 486) — RETURN_RE trifft nicht mehr."
    )
    assert _function_span(lines, 0) < len(lines), (
        "APP_END_RE findet keine Funktionsgrenze — dann ist jede Spanne die "
        "ganze Datei und jede Aussage darueber wertlos."
    )


def test_no_hook_after_early_return_general() -> None:
    """HARTE Assertion fuer alle PascalCase-Komponenten ausser App.

    Vor v3.9.961 stand hier nur ein `print`. Warum das keine Absicht sein
    kann, steht im Modul-Docstring.
    """
    lines = _load_lines()
    flagged = verdachte(lines)
    msg = ", ".join(
        f"{n}@L{ln} ({c} Hook(s) zw. Returns)" for n, ln, c in flagged[:10]
    )
    assert not flagged, (
        f"React-Hook(s) zwischen erstem und letztem return in "
        f"{len(flagged)} Komponente(n) — verletzt Rules of Hooks und kann "
        f"React-#310 ausloesen (der Fehler, den v3.8.50 geheilt hat).\n"
        f"Fundstellen: {msg}"
    )


# ── Koeder: ein Fall je Form, damit die 0 oben etwas bedeutet ──────────────

def _zeilen(*texte: str) -> list[str]:
    """Selbstgebaute Zeilen in derselben Form wie `_load_lines` sie liefert."""
    return [t + "\n" for t in texte]


_KOEDER_ROT = [
    ("Hook zwischen zwei returns", _zeilen(
        "function Foo(){",
        "  if(loading) return null;",
        "  _react.useState(0);",
        "  return 1;",
        "}")),
    ("useEffect statt useState", _zeilen(
        "function Bar(){",
        "  if(x) return null;",
        "  _react.useEffect(function(){},[]);",
        "  return 1;",
        "}")),
    ("nackter return als Grenze", _zeilen(
        "function Baz(){",
        "  return;",
        "  _react.useMemo(function(){},[]);",
        "  return 1;",
        "}")),
    ("zwei Hooks, eine Komponente", _zeilen(
        "function Qux(){",
        "  if(a) return null;",
        "  _react.useRef(null);",
        "  _react.useCallback(function(){},[]);",
        "  return 1;",
        "}")),
    ("zweite Komponente nach einer heilen", _zeilen(
        "function Heil(){",
        "  _react.useState(0);",
        "  if(a) return null;",
        "  return 1;",
        "}",
        "function Kaputt(){",
        "  if(a) return null;",
        "  _react.useState(0);",
        "  return 1;",
        "}")),
]

_KOEDER_GRUEN = [
    ("Hooks VOR dem ersten return", _zeilen(
        "function Bar(){",
        "  _react.useState(0);",
        "  if(x) return null;",
        "  return 1;",
        "}")),
    ("App wird hier nicht beurteilt (eigener Fall)", _zeilen(
        "function App(){",
        "  if(x) return null;",
        "  _react.useState(0);",
        "  return 1;",
        "}")),
    ("kleingeschriebene Hilfsfunktion ist keine Komponente", _zeilen(
        "function helper(){",
        "  if(x) return null;",
        "  _react.useState(0);",
        "  return 1;",
        "}")),
    ("Hook auf tieferem Einzug gehoert nicht zur Komponente", _zeilen(
        "function Tief(){",
        "  if(x) return null;",
        "    _react.useState(0);",
        "  return 1;",
        "}")),
]


def test_koeder_der_allgemeine_riegel_findet_jede_form() -> None:
    assert len(_KOEDER_ROT) >= 5, "Koederliste ausgeduennt"
    for name, lines in _KOEDER_ROT:
        assert verdachte(lines), (
            f"KOEDER NICHT GEFUNDEN ({name}) — der Riegel oben wuerde diese "
            f"Hook-Order-Verletzung durchwinken."
        )


def test_gegenprobe_der_allgemeine_riegel_meldet_nichts_falsches() -> None:
    assert len(_KOEDER_GRUEN) >= 4, "Gegenprobenliste ausgeduennt"
    for name, lines in _KOEDER_GRUEN:
        assert not verdachte(lines), (
            f"FEHLALARM ({name}): {verdachte(lines)!r}"
        )


def test_selbstprobe_eine_leere_menge_wird_als_leer_erkannt() -> None:
    """Die Wache in test_selbstprobe_die_anker_treffen_den_bestand muss eine
    ausgefallene Messung sehen koennen — sonst waere sie selbst die naechste
    stille Prueferin."""
    assert komponenten([]) == [], "leere Datei liefert Komponenten"
    assert verdachte([]) == [], "leere Datei liefert Verdachte"
    assert komponenten(_zeilen("var a=1;", "function helper(){}", "}")) == [], (
        "eine Datei ohne PascalCase-Komponente liefert Komponenten")
