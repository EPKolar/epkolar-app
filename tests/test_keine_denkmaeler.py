# -*- coding: utf-8 -*-
"""Kein Riegel darf die EXISTENZ einer ungelesenen Groesse festschreiben.

Ohne Versionsnummer im Namen: dieser Riegel sichert die TESTSUITE selbst, keine
App-Version.

WARUM ES DAS GIBT
─────────────────
An zwei Tagen ist derselbe Fall FUENFMAL aufgetreten:

    _kapReal        v3.9.896   eine Zuweisung, null Leser
    Basis 38,5h     v3.9.898   pinnte die SCHWAECHERE von zwei Rechnungen
    _normFrei       v3.9.900   null Leser - und die Funktion dahinter vermass
                               seit v3.9.790 einen Weg, den niemand geht
    _evCache        v3.9.900   von drei Pins wurden zwei korrekt stillgelegt,
                               der EXISTENZ-Pin blieb und hielt toten Code
                               samt luegendem Kommentar am Leben
    _dispoNormFrei  v3.9.900   Funktion und window-Export haingen an derselben
                               ungelesenen Zuweisung

Jedes Mal war die Wirkung dieselbe: der Riegel hat keine Eigenschaft gesichert,
sondern den AUSBAU verhindert. Kein Schutz, ein Denkmal. Und er wird ROT, wenn
jemand aufraeumt - er bestraft also genau die richtige Handlung.

WAS DIESER RIEGEL PRUEFT
────────────────────────
Fuer jede Zusicherung der Form

    assert "var X=..." in <irgendwas>          (auch const/let)

muss der Name X im KOMMENTARFREIEN Code von index.html mindestens ZWEIMAL
vorkommen: die Zuweisung selbst plus wenigstens einen Leser. Genau einmal heisst:
niemand liest ihn, der Pin sichert nur sein Dasein.

DREI ENTSCHEIDUNGEN, die diesen Riegel benutzbar halten:

1. Gelesen wird ueber `ast`, nicht ueber Zeilen. Ein Docstring, der einen
   entfernten Pin ZITIERT - und davon gibt es hier mehrere, weil jede Entfernung
   begruendet wird -, ist keine Zusicherung. Ein zeilenbasierter Scanner haelt
   ihn faelschlich fuer einen; genau das ist mir beim Bauen passiert.
2. Gezaehlt wird KOMMENTARBLIND. Die Changelog-Zeile in index.html ist ueber
   200.000 Zeichen lang und taeuscht sonst Leser vor - dieselbe Falle, die in
   diesem Repo an zwei Tagen elfmal zugeschnappt ist.
3. `not in`-Zusicherungen sind ausdruecklich in Ordnung und werden ignoriert.
   Sie tun das Gegenteil: sie verhindern die RUECKKEHR toten Codes. Davon gibt
   es im Bestand mehrere, und sie sind wertvoll.
"""
import ast
import io
import os
import re

from _hilfen import nur_code

MUSTER = re.compile(r"^(?:var|const|let)\s+([A-Za-z_$][\w$]*)\s*=")

# Bewusste Ausnahmen. Ein Name gehoert nur hierher, wenn er nachweislich ueber
# Destrukturierung, dynamischen Zugriff oder als Objektfeld gelesen wird - dann
# faellt sein Name kein zweites Mal, obwohl es Leser gibt.
# Format: name -> Begruendung. Leer heisst: bisher kein solcher Fall gefunden.
AUSNAHMEN = {}


def _stillgelegt(fn):
    """Traegt die Funktion eine pytest-Stilllegung?

    Das Repo hat dafuer bereits eine Form, und sie ist die richtige: in v3.9.769
    wurden drei Pins auf den alten Stempel-Scanpfad mit
    `@pytest.mark.skip(reason="... Dieser Pin testet toten Code.")` ausser Kraft
    gesetzt - Begruendung im Klartext, Pin bleibt lesbar, laeuft aber nicht mehr.
    Ein Riegel, der eine EIGENE Ausnahmeliste erzwingt, wuerde daneben eine
    zweite Buchfuehrung aufmachen. Beim Bauen hat genau dieser Fall meinen
    Riegel rot gemacht - zu Recht, und die Lehre war meine.
    """
    for d in fn.decorator_list:
        text = ast.dump(d)
        if "'skip'" in text or "'skipif'" in text or '"skip"' in text:
            return True
    return False


def _pins(pfad):
    """Liefert (name, zeile) je positiver Existenz-Zusicherung in einer Datei.

    Ueber den Syntaxbaum, damit Fliesstext in Docstrings nicht mitzaehlt.
    Stillgelegte Testfunktionen werden uebersprungen.
    """
    quelle = io.open(pfad, encoding="utf-8", newline="").read()
    try:
        baum = ast.parse(quelle)
    except SyntaxError:
        return []
    aus = []
    knoten_liste = []
    for fn in ast.walk(baum):
        if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if _stillgelegt(fn):
                continue
            knoten_liste.extend(ast.walk(fn))
    for knoten in knoten_liste:
        if not isinstance(knoten, ast.Assert):
            continue
        pruef = knoten.test
        if not isinstance(pruef, ast.Compare) or len(pruef.ops) != 1:
            continue
        if not isinstance(pruef.ops[0], ast.In):      # NotIn wird uebersprungen
            continue
        links = pruef.left
        if not (isinstance(links, ast.Constant) and isinstance(links.value, str)):
            continue
        m = MUSTER.match(links.value)
        if m:
            aus.append((m.group(1), knoten.lineno))
    return aus


def test_kein_pin_sichert_eine_ungelesene_groesse(repo_root, index_html):
    code = nur_code(index_html)
    verdacht = []
    geprueft = 0
    for datei in sorted(os.listdir(os.path.join(repo_root, "tests"))):
        if not (datei.startswith("test_") and datei.endswith(".py")):
            continue
        for name, zeile in _pins(os.path.join(repo_root, "tests", datei)):
            geprueft += 1
            if name in AUSNAHMEN:
                continue
            if code.count(name) <= 1:
                verdacht.append("%s:%d  ->  %s (%d Vorkommen im Code)"
                                % (datei, zeile, name, code.count(name)))

    assert geprueft > 100, (
        "Nur %d Existenz-Pins gefunden - der Riegel misst offenbar nicht mehr, "
        "was er messen soll. Erwartet werden mehrere hundert." % geprueft
    )
    assert not verdacht, (
        "Diese Riegel sichern die EXISTENZ einer Groesse, die im Code sonst "
        "nirgends vorkommt - sie schuetzen also keine Eigenschaft, sondern "
        "verhindern den Ausbau toten Codes:" + chr(10)
        + chr(10).join("   " + v for v in verdacht) + chr(10) + chr(10)
        + "Entweder die Groesse hat wirklich keinen Leser - dann gehoert BEIDES "
        "weg, der Code und der Pin -, oder sie wird ueber Destrukturierung bzw. "
        "dynamisch gelesen; dann traegst du sie mit Begruendung in AUSNAHMEN ein."
    )


def test_umkehrprobe_der_riegel_kann_rot_werden(repo_root, index_html, tmp_path):
    """DIE GEGENPROBE. Eine erfundene Testdatei mit einem Pin auf einen Namen,
    den es in index.html nicht gibt, MUSS als Verdacht auffallen.

    Ohne sie waere der Riegel oben gruen, ohne je etwas zu messen - genau der
    Zustand, den er anprangert."""
    p = tmp_path / "test_erfunden.py"
    p.write_text(
        'def test_x(index_html):' + chr(10) +
        '    assert "var _gibtEsGarNicht_x9=1;" in index_html' + chr(10),
        encoding="utf-8")
    gefunden = _pins(str(p))
    assert gefunden == [("_gibtEsGarNicht_x9", 2)], (
        "Der Pin wurde nicht erkannt - dann findet der Riegel oben auch echte "
        "Denkmaeler nicht: " + repr(gefunden)
    )
    code = nur_code(index_html)
    assert code.count("_gibtEsGarNicht_x9") == 0, (
        "Der erfundene Name kommt in index.html vor - die Probe taugt nicht."
    )


def test_not_in_zusicherungen_werden_nicht_bemaengelt(tmp_path):
    """Gegenprobe zur anderen Seite: `not in` verhindert die RUECKKEHR toten
    Codes und ist ausdruecklich erwuenscht. Wuerde der Riegel das anmahnen,
    zwaenge er dazu, gute Schutzriegel zu entfernen."""
    p = tmp_path / "test_verbot.py"
    p.write_text(
        'def test_x(index_html):' + chr(10) +
        '    assert "const commitImport=" not in index_html' + chr(10),
        encoding="utf-8")
    assert _pins(str(p)) == [], (
        "Eine not-in-Zusicherung wurde als Existenz-Pin gewertet."
    )


def test_stillgelegte_pins_zaehlen_nicht(tmp_path):
    """Gegenprobe zur Stilllegung - IN BEIDE RICHTUNGEN, sonst waere
    `_stillgelegt` selbst ungemessen und koennte alles durchwinken.

    Der echte Fall aus dem Bestand: test_stempel_hardening_v3662 pinnt Zeilen
    des alten Stempel-Scanpfads, den v3.9.769 durch eine Server-Prozedur ersetzt
    hat. Die Namen gibt es in index.html nicht mehr - der Pin ist aber korrekt
    mit `@pytest.mark.skip(reason="... Dieser Pin testet toten Code.")`
    stillgelegt. Genau daran ist dieser Riegel beim Bauen rot geworden."""
    gemeinsam = ('    assert "const _laengstWeg=1;" in index_html' + chr(10))

    mit = tmp_path / "test_mit_skip.py"
    mit.write_text('import pytest' + chr(10) +
                   '@pytest.mark.skip(reason="Dieser Pin testet toten Code.")' + chr(10) +
                   'def test_x(index_html):' + chr(10) + gemeinsam,
                   encoding="utf-8")
    assert _pins(str(mit)) == [], (
        "Ein stillgelegter Pin wurde mitgezaehlt - dann muesste man ihn "
        "loeschen statt ihn lesbar und begruendet stehenzulassen."
    )

    ohne = tmp_path / "test_ohne_skip.py"
    ohne.write_text('def test_x(index_html):' + chr(10) + gemeinsam,
                    encoding="utf-8")
    assert len(_pins(str(ohne))) == 1, (
        "DIESELBE Zusicherung ohne Stilllegung wurde NICHT gezaehlt - dann "
        "misst _stillgelegt nichts und winkt alles durch."
    )


def test_fliesstext_in_docstrings_zaehlt_nicht(tmp_path):
    """Beim Bauen dieses Riegels bin ich genau darauf hereingefallen: jede
    Entfernung eines Denkmals wird im Docstring BEGRUENDET und zitiert dabei die
    entfernte Zeile. Ein zeilenbasierter Scanner haelt das fuer eine
    Zusicherung."""
    p = tmp_path / "test_prosa.py"
    p.write_text(
        '"""Hier stand frueher:' + chr(10) +
        '    assert "var _laengstWeg=1;" in index_html' + chr(10) +
        'und wurde in v3.9.900 entfernt."""' + chr(10) +
        'def test_x():' + chr(10) +
        '    pass' + chr(10),
        encoding="utf-8")
    assert _pins(str(p)) == [], (
        "Zitierter Fliesstext wurde als Zusicherung gewertet - dann wird der "
        "Riegel bei jeder gut begruendeten Entfernung rot."
    )
