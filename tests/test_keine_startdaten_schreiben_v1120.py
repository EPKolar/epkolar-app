"""v3.9.1120 (Nachtrag) - Startdaten werden NIE in die Datenbank geschrieben.

Bis 3.9.1119 schrieb die App beim Admin-Start bei einer leeren projects- bzw.
workers-Tabelle die fest eingebauten Listen INIT_PROJECTS / MONT per _sbUpsert
in die Datenbank. Ausserdem fiel die Fahrzeugansicht bei leerer API und leerem
IndexedDB auf DEMO_FZ zurueck (echt aussehende Kennzeichen).

Seit dem Nachtrag zu 1120:
  - keine Schleife/kein map/forEach ueber eine GROSS_GESCHRIEBENE Konstante
    (INIT_*, MONT, DEMO_*) mit einem DB-Schreibaufruf im Rumpf
  - leere Tabelle -> deutliche Meldung (Texte unten), nichts angelegt
  - DEMO_FZ existiert nicht mehr und ist kein Rueckfall
Umkehrprobe: dieselbe Pruefung gegen 05cfb99 (3.9.1119) MUSS die zwei alten
Schreibwege finden.
"""
import io
import os
import re
import subprocess

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASIS = "05cfb99"

KONST = r"(?:INIT_[A-Z0-9_]+|MONT|DEMO_[A-Z0-9_]+)"
SCHREIBEN = re.compile(
    r"_sbUpsert\(|_sbPost\(|_sbPatch\(|_sbInsertIfAbsent\(|SQ\.(?:add|push)\("
    r"|API\.\w*(?:save|create|add|post|put|update|upsert)\w*\(", re.I)

TEXTE = (
    "Keine Projekte in der Datenbank - bitte Admin verst\u00e4ndigen. Es wurde nichts angelegt.",
    "Keine Mitarbeiter in der Datenbank - bitte Admin verst\u00e4ndigen. Es wurde nichts angelegt.",
    "Keine Benutzer in der Datenbank geladen - bitte Admin verst\u00e4ndigen. Es wurde nichts angelegt.",
)


def _jetzt():
    return io.open(os.path.join(ROOT, "index.html"), encoding="utf-8", newline="").read()


def _basis():
    try:
        out = subprocess.run(["git", "-C", ROOT, "show", BASIS + ":index.html"],
                             capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        pytest.skip("Basis %s nicht im Repo lesbar" % BASIS)
    return out.stdout.decode("utf-8")


def _ohne_kommentare(src):
    # Blockkommentare und //-Zeilenkommentare (nicht in URLs wie https://) entfernen
    src = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
    return re.sub(r"(?<![:\"'\\])//[^\r\n]*", "", src)


def _rumpf(src, start):
    """Text ab der ersten '{' bzw. '(' nach start bis zur passenden Klammer."""
    i = start
    while i < len(src) and src[i] not in "{(":
        i += 1
    if i >= len(src):
        return ""
    auf = src[i]
    zu = "}" if auf == "{" else ")"
    tiefe = 0
    for j in range(i, min(len(src), i + 20000)):
        c = src[j]
        if c == auf:
            tiefe += 1
        elif c == zu:
            tiefe -= 1
            if tiefe == 0:
                return src[i:j + 1]
    return src[i:i + 20000]


def schreibwege_aus_konstanten(src):
    """Funde (Konstante, Ausschnitt) fuer Schleifen ueber Konstanten mit Schreibaufruf."""
    code = _ohne_kommentare(src)
    funde = []
    # for(const x of KONST) { ... }   /   for(... in KONST)
    for m in re.finditer(r"for\s*\(\s*(?:const|let|var)\s+\w+\s+(?:of|in)\s+(" + KONST + r")\s*\)", code):
        koerper = _rumpf(code, m.end())
        if SCHREIBEN.search(koerper):
            funde.append((m.group(1), code[m.start():m.start() + 160]))
    # KONST.map/forEach/filter/reduce(...)
    for m in re.finditer(r"\b(" + KONST + r")\s*\.\s*(?:map|forEach|filter|reduce|flatMap|some|every)\s*\(", code):
        koerper = _rumpf(code, m.end() - 1)
        if SCHREIBEN.search(koerper):
            funde.append((m.group(1), code[m.start():m.start() + 160]))
    # Promise.all(KONST.map(...)) faellt unter den zweiten Fall
    return funde


def test_kein_schreibweg_aus_konstanten_listen():
    funde = schreibwege_aus_konstanten(_jetzt())
    assert not funde, "DB-Schreibweg aus fest eingebauter Liste: %r" % funde


def test_umkehrprobe_basis_findet_die_zwei_alten_seeds():
    funde = schreibwege_aus_konstanten(_basis())
    namen = sorted(k for k, _ in funde)
    assert namen == ["INIT_PROJECTS", "MONT"], (
        "Die Pruefung muss in 05cfb99 genau die zwei alten Seeds finden "
        "(sonst misst sie nichts): %r" % funde)


def test_meldetexte_vorhanden_und_verdrahtet():
    s = _jetzt()
    for t in TEXTE:
        assert s.count(t) == 1, "Meldetext fehlt: %s" % t
    code = _ohne_kommentare(s)
    assert 'if(_pConfirmEmpty){_startdatenFehler("projects");}' in code
    assert 'if(_wConfirmEmpty){_startdatenFehler("workers");}' in code
    assert '_startdatenFehler("users")' in code
    # Meldung = console.error + Hinweisleiste + Toast
    a = code.index("const _startdatenFehler=")
    teil = code[a:a + 400]
    assert "console.error(" in teil and "setStartFehler(" in teil and "addToast(" in teil
    assert "'data-startfehler'" in code


def test_leer_nachweis_bleibt_erhalten():
    code = _ohne_kommentare(_jetzt())
    for t in ("projects", "workers"):
        assert ('await _sbGet("%s","select=id&limit=1")' % t) in code


def test_kein_demo_fahrzeug_rueckfall():
    s = _jetzt()
    assert "DEMO_FZ" not in s
    assert "setFahrzeuge(DEMO_" not in s
    code = _ohne_kommentare(s)
    assert re.search(r"else setFahrzeuge\(\[\]\);", code)
    assert "}).catch(()=>setFahrzeuge([]));" in code
    assert '"Keine Fahrzeuge vorhanden"' in code


def test_umkehrprobe_basis_hat_demo_rueckfall():
    b = _basis()
    assert "setFahrzeuge(DEMO_FZ)" in b and "const DEMO_FZ=[" in b
