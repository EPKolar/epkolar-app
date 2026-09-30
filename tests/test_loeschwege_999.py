# -*- coding: utf-8 -*-
"""R2 — die Löschwege waren strukturell blind.

`_sbDelete` und `_sbDeleteWhere` schickten ein DELETE los und gaben bei jedem
2xx hart `{ok:1}` zurück, **ohne je zu fragen, wie viele Zeilen weg sind**.
Gemessen: 41 Löschwege auf 29 Tabellen, darunter `time_entries` (4 Stellen),
`absence_files` (3 — Atteste, also Gesundheitsdaten) und `defects` (3).

Weist der Zeilenschutz ab, antwortet PostgREST mit 204 und null Zeilen. Das
sah aus wie ein Erfolg: der Auftrag verschwand aus der Warteschlange, und die
Zeile stand noch da.

## 🔴 Was hier BEWUSST NICHT gebaut ist — und das ist die eigentliche Aussage

**Ein Hinweis an den Nutzer.** Zwei Messungen sprechen dagegen, beide
gefahren statt vermutet:

1. **Der Warteschlangen-Weg wird wiederholt.** Ging die erste Antwort auf der
   Leitung verloren, findet der zweite Versuch null Zeilen — und die Zeile
   ist trotzdem korrekt gelöscht. Eine Meldung wäre dort schlicht falsch.
2. **`_sbDeleteWhere` räumt Kind-Datensätze ab.** Ein Projekt ohne Dokumente
   liefert null Zeilen, und das ist der **Normalfall**.

Am selben Tag habe ich genau diesen Fehler schon einmal gebaut: der
B2-Melder schlug bei jedem Einzelabruf an, weil `limit=1` genau eine Zeile
liefert (siehe `test_zuordnung_und_grenze_v995.py`). Eine Meldung, die zu oft
kommt, wird weggeklickt — danach ist auch der echte Fall unsichtbar.

**Deshalb nur die Hälfte, die eindeutig ist:** die App *erfährt* jetzt, wie
viele Zeilen wirklich weg sind, und legt es ab. Damit ist der Befund
**messbar** statt unsichtbar. Ob daraus eine Meldung wird und wo, ist eine
Entscheidung und steht auf der Entscheidungsliste.

## Zwei verschiedene Kopfzeilen, und der Grund ist die Antwortgröße

* `_sbDelete` löscht über `id=eq.<kennung>`, also höchstens **eine** Zeile →
  `Prefer: return=representation` ist dort billig.
* `_sbDeleteWhere` kann **viele** Zeilen treffen → dieselbe Kopfzeile wäre
  eine halbe Tabelle im Netz. Statt dessen `Prefer: count=exact`: die Zahl
  steht in `Content-Range`, der Rumpf bleibt leer.

🔴 **Kein `select=id`:** nicht jede Tabelle hier hat eine Spalte `id`
(`weekplan_rows` führt `row_id`, `absences` einen zusammengesetzten
Schlüssel). Ein `select=id` darauf gäbe einen 400er — der Löschvorgang würde
**abbrechen**. Eine Sparmaßnahme, die das Löschen kaputtmacht, ist keine.

🔴 **Und ein eigener Unfall beim Bauen:** der erste Kommentar enthielt den
Platzhalter aus dem `Content-Range`-Kopf wörtlich — die Zeichenfolge
Stern-Schrägstrich. Die **beendet einen Kommentar**. `node_check` wurde rot
und die Klammerbilanz sprang von `() -1` auf `() 0`. Beide Tore haben es
gefangen; im Kommentar steht die Zeichenfolge jetzt umschrieben.
"""
import io
import os
import re

HIER = os.path.dirname(os.path.abspath(__file__))
PFAD = os.path.join(HIER, "..", "index.html")


def _text():
    return io.open(PFAD, encoding="utf-8", newline="").read()


def _ohne_kommentare(s):
    s = re.sub(r"/\*.*?\*/", "", s, flags=re.S)
    return re.sub(r"//[^\n]*", "", s)


def _rumpf(name, laenge=2200):
    code = _ohne_kommentare(_text())
    i = code.find("async function %s(" % name)
    assert i > 0, "\U0001F534 %s ist weg." % name
    return code[i:i + laenge]


def test_koeder_die_kommentarbehandlung_traegt():
    mit = "/* HIER STAND return{ok:1}; */ x=1;"
    assert "return{ok:1};" not in _ohne_kommentare(mit), (
        "Ein Kommentar, der die alte Form zitiert, wird mitgezaehlt.")


def test_sbdelete_fragt_nach_den_geloeschten_zeilen():
    r = _rumpf("_sbDelete")
    assert 'return=representation' in r, (
        "\U0001F534 _sbDelete fragt die geloeschten Zeilen nicht mehr an. "
        "Dann ist der Weg\n  wieder blind: 204 mit null Zeilen sieht aus wie "
        "ein Erfolg, der Auftrag\n  verschwindet aus der Warteschlange, und "
        "die Zeile steht noch da.")
    assert "_sbLoeschZahl(table," in r, (
        "\U0001F534 Die Zahl wird nicht abgelegt - dann weiss die App es "
        "wieder nicht.")


def test_sbdeletewhere_zaehlt_ueber_die_kopfzeile():
    r = _rumpf("_sbDeleteWhere")
    assert "count=exact" in r, (
        "\U0001F534 _sbDeleteWhere zaehlt nicht mehr.")
    assert "content-range" in r.lower(), (
        "\U0001F534 Die Zahl wird nicht aus Content-Range gelesen.")
    assert "return=representation" not in r, (
        "\U0001F534 Hier steht return=representation. Dieser Weg kann VIELE "
        "Zeilen treffen -\n  die Zeilen zurueckzuholen ist eine halbe Tabelle "
        "im Netz. count=exact liefert\n  nur die Zahl.")


def test_kein_select_id_auf_den_loeschwegen():
    """🔴 Nicht jede Tabelle hat eine Spalte `id`.

    `weekplan_rows` führt `row_id`, `absences` einen zusammengesetzten
    Schlüssel. Ein `select=id` darauf gäbe einen 400er - und der
    Löschvorgang bräche ab. Eine Sparmaßnahme, die das Löschen kaputtmacht,
    ist keine.
    """
    for name in ("_sbDelete", "_sbDeleteWhere"):
        r = _rumpf(name)
        assert "select=id" not in r, (
            "\U0001F534 %s haengt `select=id` an. Auf einer Tabelle ohne "
            "Spalte `id` gibt das\n  einen 400er, und das Loeschen bricht "
            "ab." % name)


def test_die_loeschwege_melden_dem_nutzer_NICHTS():
    """🔴 Die Gegenprobe zur Kur - und die wichtigste Probe hier.

    Ein Hinweis an dieser Stelle wäre falsch: der Warteschlangen-Weg wird
    wiederholt (der zweite Versuch findet null Zeilen, obwohl richtig
    gelöscht wurde), und eine Löschkaskade auf ein Projekt ohne
    Kind-Datensätze trifft regelmäßig null Zeilen.

    Genau diesen Fehler habe ich am 30.09. schon einmal gebaut. Wer ihn hier
    einbaut, macht die Meldung wertlos, bevor sie je gebraucht wird.
    """
    for name in ("_sbDelete", "_sbDeleteWhere"):
        r = _rumpf(name)
        assert "__toast" not in r, (
            "\U0001F534 %s meldet dem Nutzer etwas. Das ist hier FALSCH:\n"
            "  * der Warteschlangen-Weg wird wiederholt - der zweite Versuch "
            "findet null\n    Zeilen, obwohl richtig geloescht wurde;\n"
            "  * eine Loeschkaskade auf ein Projekt ohne Kind-Datensaetze "
            "trifft regelmaessig\n    null Zeilen, und das ist der "
            "Normalfall.\n"
            "  Was zu oft kommt, wird weggeklickt - danach ist auch der "
            "echte Fall unsichtbar." % name)


def test_der_rueckgabewert_bleibt_fuer_alle_aufrufer_gleich():
    """Rund 40 Aufrufer lesen `{ok:1}`. Keiner darf sein Verhalten ändern."""
    for name in ("_sbDelete", "_sbDeleteWhere"):
        r = _rumpf(name)
        assert "return{ok:1,zeilen:" in r, (
            "\U0001F534 %s gibt nicht mehr `{ok:1,...}` zurueck. Die Zahl "
            "darf dazukommen,\n  das Feld `ok` nicht verschwinden." % name)


def test_der_kommentar_enthaelt_kein_kommentar_ende():
    """🔴 Die Zeichenfolge Stern-Schrägstrich beendet einen Kommentar.

    Beim Bauen ist genau das passiert: der `Content-Range`-Platzhalter stand
    wörtlich im Kommentar, `node_check` wurde rot und die Klammerbilanz
    sprang von `() -1` auf `() 0`.
    """
    t = _text()
    i = t.find("function _sbLoeschZahl(")
    assert i > 0, "\U0001F534 Der Zaehler ist weg."
    # Von hier bis zum Ende von _sbDeleteWhere: jeder Kommentar muss genau
    # EINMAL enden.
    j = t.find("async function _sbUpsert", i)
    stueck = t[i:j if j > i else i + 6000]
    for m in re.finditer(r"/\*.*?\*/", stueck, flags=re.S):
        rumpf = m.group(0)[2:-2]
        assert "*/" not in rumpf, (
            "\U0001F534 Ein Kommentar enthaelt die Zeichenfolge "
            "Stern-Schraegstrich und endet\n  damit mitten im Satz. Der Rest "
            "wird als Code gelesen.")
