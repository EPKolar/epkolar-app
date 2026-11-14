# -*- coding: utf-8 -*-
"""v3.9.1005 - Gehen <= Kommen ist UNGUELTIG (Entscheidung Sebastian: keine Nachtarbeit).

Vorher rechnete `_wrapHrs` bei bis < von stillschweigend +24 h: 16:00 -> 07:00
wurde zu 15 h, 22:00 -> 06:00 zu 8 h - eine Nachtschicht, die bei EP Kolar
nicht vorkommt. Gleich-Zeit (07:00 -> 07:00) ergab 0 und lief als "Pause zu
lang" in eine falsche Meldung.

Jetzt:
  * `_wrapHrs` liefert bei Spanne <= 0 `null` - keine Korrektur, kein Minus.
  * `_zeitEffektiveStunden` liefert dann `null` (keine Stundenzahl).
  * `_zeitDauerUngueltig(von,bis)` ist die EINE Pruefung fuer die Masken.
  * beide `addEntry` weisen VOR der bestehenden Rechnung ab, mit
    `ZEIT_BIS_VOR_VON_MSG`.
  * beide Stundenfelder zeigen die Meldung statt einer Zahl.

Die Regel wird am ECHTEN Code per node ausgefuehrt (aus index.html geschnitten),
mit Gegenprobe: dieselben Faelle gegen die ALTE Regel liefern 15 und 8 - der
Test kann den alten Fehler also sehen.
"""
import json
import re

from conftest import run_node_snippet, _extract_fn

MELDUNG = "Gehen-Zeit liegt vor Kommen-Zeit - bitte prüfen"
ALT_REGEL = "if(h<0)h+=24;return h;"
NEU_REGEL = "if(h<=0)return null;return h;"
NAMEN = ("_zeitParse", "_zeitFmt", "_zeitRundVon", "_zeitRundBis",
         "_wrapHrs", "_zeitEffektiveStunden", "_zeitDauerUngueltig")
FAELLE = [["07:00", "16:00"], ["16:00", "07:00"], ["22:00", "06:00"],
          ["07:00", "07:00"], ["", "16:00"], ["07:00", ""]]


def _bausatz(index_html):
    teile = []
    for n in NAMEN:
        f = _extract_fn(index_html, n)
        assert f, "Funktion nicht gefunden: " + n
        teile.append(f)
    return "var ZEIT_RASTER_MIN=5;\n" + "\n".join(teile) + "\n"


def _lauf(node_exe, code):
    snippet = code + (
        "const F=" + json.dumps(FAELLE) + ";"
        "process.stdout.write(JSON.stringify({"
        "wrap:F.slice(0,4).map(a=>_wrapHrs(a[0],a[1])),"
        "eff:F.map(a=>_zeitEffektiveStunden(a[0],a[1],0)),"
        "ung:F.map(a=>_zeitDauerUngueltig(a[0],a[1]))}));"
    )
    return json.loads(run_node_snippet(node_exe, snippet))


def test_die_regel_am_echten_code(node_exe, index_html):
    r = _lauf(node_exe, _bausatz(index_html))
    assert r["wrap"][0] == 9, "07:00->16:00 muss 9 h ergeben, war %s" % r["wrap"][0]
    assert r["wrap"][1] is None, "16:00->07:00 muss ungueltig sein (nicht -9, nicht +15), war %s" % r["wrap"][1]
    assert r["wrap"][2] is None, "22:00->06:00 muss ungueltig sein (keine Nachtarbeit), war %s" % r["wrap"][2]
    assert r["wrap"][3] is None, "07:00->07:00 muss ungueltig sein, war %s" % r["wrap"][3]


def test_effektive_stunden_ohne_zahl_bei_ungueltig(node_exe, index_html):
    r = _lauf(node_exe, _bausatz(index_html))
    assert r["eff"] == [9, None, None, None, None, None], r["eff"]


def test_pruefung_ungueltig(node_exe, index_html):
    """Leere Zeiten sind KEIN Fehler - das ist die Hintertuer fuer die Handeingabe."""
    r = _lauf(node_exe, _bausatz(index_html))
    assert r["ung"] == [False, True, True, True, False, False], r["ung"]


def test_gegenprobe_alte_regel_haette_15_und_8_geliefert(node_exe, index_html):
    code = _bausatz(index_html)
    assert code.count(NEU_REGEL) == 1, "neue Regel nicht (genau einmal) im geschnittenen Code"
    alt = code.replace(NEU_REGEL, ALT_REGEL, 1)
    r = _lauf(node_exe, alt)
    assert r["wrap"][:3] == [9, 15, 8], (
        "Gegenprobe: die alte +24h-Regel muss 9/15/8 liefern, sonst sieht "
        "dieser Test den alten Fehler nicht. War %s" % r["wrap"])
    assert r["ung"][1] is False and r["ung"][2] is False, (
        "Gegenprobe: unter der alten Regel war nichts ungueltig")


def test_meldung_wortgleich(index_html):
    assert ('var ZEIT_BIS_VOR_VON_MSG="%s";' % MELDUNG) in index_html


def test_beide_speicherwege_weisen_vor_der_rechnung_ab(index_html):
    muster = re.compile(
        r"if\(_zeitDauerUngueltig\(_rVon,_rBis\)\)\{if\(window\.__toast\)window\.__toast\("
        r"[^;]*ZEIT_BIS_VOR_VON_MSG[^;]*\);return;\}(?:/\*.*?\*/)?"
        r"if\(_rVon&&_rBis\)\{const _d=_wrapHrs\(_rVon,_rBis\)-addPause;", re.S)
    n = len(muster.findall(index_html))
    assert n == 2, ("Erwartet 2 Speicherwege (Projekt- und Haupt-Zeiterfassung), "
                    "die Gehen <= Kommen VOR der Rechnung abweisen; gefunden %d" % n)


def test_beide_stundenfelder_zeigen_die_meldung(index_html):
    n = index_html.count("_zeitDauerUngueltig(addVon,addBis)?React.createElement('div',{role:\"alert\"")
    assert n == 2, "Erwartet 2 Stundenfelder mit Meldung statt Zahl, gefunden %d" % n
    assert index_html.count('"⚠️ "+ZEIT_BIS_VOR_VON_MSG)') == 2


def test_keine_24h_addition_mehr(index_html):
    rumpf = _extract_fn(index_html, "_wrapHrs")
    assert "+=24" not in rumpf.replace(" ", ""), "die +24h-Addition steht wieder in _wrapHrs"
    assert NEU_REGEL in rumpf
