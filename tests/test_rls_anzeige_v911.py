# -*- coding: utf-8 -*-
"""v3.9.911 - Die Kacheln lesen die Marke: der Kreis schliesst sich.

v3.9.910 hat die Wurzel markiert - ein leeres Array aus einem 401/403 traegt
seither seinen Grund. Gebracht hat das allein noch nichts: die drei Kacheln
standen bei einem FEHLER zwar richtig auf `null`, aber **ein 403 ist fuer sie
gar kein Fehler**. Er kommt als leere Liste im Erfolgspfad an, `.length` ist 0,
und der Auffangzweig sieht ihn nie.

    Rechtefehler -> markiertes Array -> Merkliste -> drei Punkte auf dem Schirm

Erst mit diesem Schritt ist die Kette durchgaengig.

DREI STELLEN, gemessen - nicht geschaetzt: ein Durchgang ueber die Datei nach
dem Muster "Abrufergebnis wird unmittelbar zu einer angezeigten Zahl" findet
genau drei:

    material_orders      -> Offene Anforderungen
    gefahrstoff_files    -> SDB-Dokumente
    absences (beantragt) -> Offene Antraege

Die dritte schliesst den Kreis zu v3.9.898: dort sagte der Schirm "Alle
bearbeitet", ohne je gemessen zu haben. Ein 403 auf `absences` erzeugte genau
dieselbe Falschaussage - nur ueber die Zahl statt ueber das Wort.

Bei den Gefahrenstoffen ist die falsche Null am unangenehmsten: sie behauptet,
es liege kein Sicherheitsdatenblatt vor.

WARUM DIESER RIEGEL DEN HELFER AUSFUEHRT
────────────────────────────────────────
`_rlsLeer` ist eine Ja/Nein-Entscheidung ueber fremde Daten. Ob er richtig
entscheidet, sieht man seiner Schreibweise nicht an - man muss ihn fuettern.
Der Riegel schneidet ihn woertlich aus index.html und laesst ihn in Node gegen
fuenf Faelle laufen, darunter die beiden, die auseinandergehalten werden
muessen: ein markiertes leeres Array und ein echtes leeres Array.
"""
import json
import os
import re

from conftest import run_node_snippet
from _hilfen import nur_code


def _helfer(index_html):
    i = index_html.index("function _rlsLeer(liste){")
    j = index_html.index("}", index_html.index("catch(_rl)", i)) + 1
    # bis zum Ende der Funktion: das schliessende } der Funktion selbst
    ende = index_html.index("}", j) + 1
    return index_html[i:ende]


def test_der_helfer_entscheidet_richtig(node_exe, index_html):
    """DIE MARKE. Fuenf Faelle, und die ersten beiden sind der ganze Punkt:
    ein markiertes leeres Array muss ANDERS behandelt werden als ein echtes."""
    fn = _helfer(index_html)
    snippet = fn + chr(10) + """
var markiert=[];markiert.__rlsFehler=403;markiert.__rlsTab='absences';
var echt=[];
var voll=[{id:1}];
process.stdout.write(JSON.stringify({
  markiert:_rlsLeer(markiert),
  echt_leer:_rlsLeer(echt),
  voll:_rlsLeer(voll),
  nichts:_rlsLeer(null),
  undef:_rlsLeer(undefined)
}));"""
    ist = json.loads(run_node_snippet(node_exe, snippet))
    assert ist["markiert"] is True, (
        "Ein markiertes leeres Array wird nicht als Rechtefehler erkannt - dann "
        "zeigt die Kachel wieder 0, und eine 0 ist eine Auskunft, nach der "
        "jemand handelt."
    )
    assert ist["echt_leer"] is False, (
        "Ein WIRKLICH leeres Ergebnis wird als Rechtefehler gewertet - dann "
        "zeigen die Kacheln dauerhaft drei Punkte, obwohl alles in Ordnung ist. "
        "Das waere die umgekehrte Luege."
    )
    for k in ("voll", "nichts", "undef"):
        assert ist[k] is False, (
            "Fall %r wird faelschlich als Rechtefehler gewertet: %r" % (k, ist)
        )


def test_alle_drei_kacheln_fragen_nach(index_html):
    code = nur_code(index_html)
    # v3.9.911: hier stand zuerst eine GESAMTZAHL (`count("_rlsLeer(") == 5`).
    # Sie war falsch - der window-Export traegt keine Klammer, es sind vier -,
    # und das war heute schon die vierte Fehlzaehlung derselben Art. Die Summe
    # war nur bequem; die AUSSAGE sind die drei benannten Stellen. Eine Zahl,
    # die man beim Hinzufuegen einer Zeile nachziehen muss, misst ohnehin die
    # Buchhaltung und nicht die Eigenschaft.
    assert "function _rlsLeer(liste){" in code, (
        "Der Helfer fehlt - dann kann keine Kachel nach der Marke fragen."
    )
    for stelle in ("setMatOpen(_rlsLeer(mo)?null:",
                   "setGsCount(_rlsLeer(gf)?null:",
                   "setAbsPending(_rlsLeer(ab)?null:"):
        assert stelle in code, (
            "Diese Kachel fragt nicht nach der Marke: " + stelle
        )


def test_kein_abruf_wurde_veraendert(index_html):
    """GEGENPROBE zur Abgrenzung: die Abfragen selbst bleiben Zeichen fuer
    Zeichen gleich. Diese Version aendert nur, wie das ERGEBNIS gelesen wird -
    haette sie an den Filtern gedreht, waeren die Zahlen andere geworden und
    niemand haette gewusst, woran es liegt."""
    for abruf in ("_sbGet('material_orders','select=id,status')",
                  "_sbGet('gefahrstoff_files','select=id')",
                  "_sbGet('absences','status=eq.beantragt&select=id')"):
        assert abruf in index_html, (
            "Der Abruf %r hat sich veraendert - diese Version durfte nur das "
            "Lesen des Ergebnisses anfassen." % abruf
        )


def test_der_helfer_wirft_nie(index_html):
    """Ein Helfer, der bei fremden Daten wirft, macht aus einem Rechtefehler
    einen Absturz - genau das Gegenteil seines Zwecks."""
    fn = _helfer(index_html)
    assert "try{" in fn and "catch(_rl){return false;}" in fn, (
        "_rlsLeer ist nicht abgesichert."
    )
    assert "return false;" in fn, (
        "Im Zweifel muss der Helfer FALSE sagen - er darf nie selbst der Grund "
        "sein, warum etwas nicht angezeigt wird."
    )


# ══ Umkehrprobe ═════════════════════════════════════════════════════════════

def test_umkehrprobe_der_riegel_kann_rot_werden(node_exe, index_html):
    """Mit einem Helfer, der immer false sagt, MUSS der Marken-Fall durchfallen.
    Ohne diese Probe waere der Riegel oben gruen, ohne etwas zu messen."""
    kaputt = "function _rlsLeer(liste){return false;}"
    snippet = kaputt + chr(10) + """
var markiert=[];markiert.__rlsFehler=403;
process.stdout.write(JSON.stringify({markiert:_rlsLeer(markiert)}));"""
    ist = json.loads(run_node_snippet(node_exe, snippet))
    assert ist["markiert"] is False, (
        "Die Gegenprobe misst nichts - selbst ein immer-falsch-Helfer besteht "
        "sie, dann ist der Riegel oben wertlos."
    )
