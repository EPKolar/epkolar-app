# -*- coding: utf-8 -*-
"""v3.9.909 - eine ausgebliebene Messung darf nicht als ZAHL erscheinen.

Achtzehn Faelle: wo ein Abruf fehlschlaegt oder noch laeuft, muss der Zustand
`null` sein und die Kachel "nicht gemessen" bzw. "…" zeigen - nicht `0`. Eine
0 behauptet ein Messergebnis, das es nicht gibt. Das war die Wurzel des
Befundes vom 29.08.2026.

🔴 DIESE DATEI HAT 29 TAGE UND 75 COMMITS LANG NICHTS GEMESSEN
──────────────────────────────────────────────────────────────
Sie kam am 29.08.2026 mit v3.9.909 herein - als ENTWURF, geschrieben als
eigenstaendiges Programm mit `main(pfad)` und `sys.exit`. Der Dateiname beginnt
mit `test_`, sie liegt in `tests/`, sie ist fehlerfrei, und von Hand meldet sie
GRUEN 18/18. Nur: **sie enthielt keine einzige `def test_`-Funktion.** pytest
hat daraus null Faelle eingesammelt, und kein Skript hat sie aufgerufen.

Ein funktionsfaehiger, gruener, wirkungsloser Riegel. Gefunden am 27.09.2026
von einer Messung, die die Dateien auf der Platte mit dem verglich, was
`pytest --collect-only` tatsaechlich einsammelt - nicht von einem Blick in die
Datei, denn von innen sieht sie richtig aus.

Dieselbe Krankheit wie ein Pruefer, der in keiner Kette haengt: die ANWESENHEIT
einer Pruefung ist kein Beleg, dass sie laeuft.

v3.9.960: in pytest-Faelle umgeschrieben, mit Koeder. Der alte `main(pfad)`
bleibt erhalten - er ist die Form, in der die Datei ausserhalb des Repos gegen
eine fremde Kopie gefahren werden kann, und genau so ist die Umkehrprobe
entstanden.

Kommentarblind ueber `tests/_hilfen.nur_code`. Der alte Kopf behauptete das
schon, waehrend die Datei ihre EIGENE Fassung mitbrachte - noch eine
Behauptung, die der Code nicht hielt. Gegengemessen, bevor umgestellt wurde:
beide Streicher geben fuer alle 18 Faelle dasselbe Ergebnis.
"""
import io
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _hilfen import nur_code  # noqa: E402


# (Name, muss_vorkommen, darf_nicht_vorkommen)
FAELLE = [
    # 1 - Chef-Dashboard: drei Kacheln, deren Zustand auf null steht
    ("kachel_matOpen",   "catch(_){if(a)setMatOpen(null);}",   "catch(_){if(a)setMatOpen(0);}"),
    ("kachel_gsCount",   "catch(_){if(a)setGsCount(null);}",   "catch(_){if(a)setGsCount(0);}"),
    ("kachel_absPending", "catch(_){if(a)setAbsPending(null);}", "catch(_){if(a)setAbsPending(0);}"),
    # 2 - Monatsabrechnung offen
    ("finkOpen_catch",   "catch(_){if(alive)setFinkOpen(null);}", "catch(_){if(alive)setFinkOpen([]);}"),
    ("finkOpen_abruf",   "&select=worker_id,monat,status');",
     "&select=worker_id,monat,status').catch(()=>[]);"),
    # 3 - Abwesend naechste Woche
    ("nextWeekAbs_ungeladen", "{setNextWeekAbs(null);return;}", "{setNextWeekAbs([]);return;}"),
    ("nextWeekAbs_catch", "catch(_){setNextWeekAbs(null);}", "catch(_){setNextWeekAbs([]);}"),
    # 4 - Maengel & Tickets
    ("mtStats_catch", "setMtStats({tOpen:null,tOver:null,dOpen:null,dOver:null,top:[]})",
     "setMtStats({tOpen:0,tOver:0,dOpen:0,dOver:0,top:[]})"),
    ("mtStats_gate", "mtStats&&(mtStats.tOpen===null||mtStats.tOpen>0||mtStats.dOpen>0)",
     "mtStats&&(mtStats.tOpen>0||mtStats.dOpen>0)&&"),
    ("mtStats_abruf", 'status,project_id");\n    const df=', 'status,project_id").catch(()=>[]);'),
    # 5 - Monatsabrechnungs-Kachel im Ops-Dashboard
    ("finkStats_init", "pendingDetails:[],geladen:false}", "diffWarn:0,pendingDetails:[]});"),
    ("finkStats_stats", "diffWarn,pendingDetails,geladen:true}", "diffWarn,pendingDetails};"),
    ("finkStats_leer_ist_messung", "if(!Array.isArray(data))return;", "if(!data||!data.length)return;"),
    ("finkStats_kachel", 'finkStats.geladen?"Alle abgeglichen":"nicht gemessen"',
     'finkStats.offen+" offen":"Alle abgeglichen")'),
    # 6 - Live-KPIs
    ("liveKpis_init", "{matOpen:null,matTotal:null,btWeek:null,btTotal:null,actToday:null,loading:false}",
     "{matOpen:0,matTotal:0,btWeek:0,btTotal:0,actToday:0,loading:false}"),
    ("liveKpis_material", 'liveKpis.matOpen==null?"…":liveKpis.matOpen', 'fontFamily:mono}}, liveKpis.matOpen)'),
    ("liveKpis_bautagebuch", 'liveKpis.btWeek==null?"…":liveKpis.btWeek', 'fontFamily:mono}}, liveKpis.btWeek)'),
    ("liveKpis_team", 'liveKpis.actToday==null?"…":liveKpis.actToday', 'fontFamily:mono}}, liveKpis.actToday)'),
]


def _befunde(code):
    """Die Beurteilung eines Standes. Leere Liste = gruen."""
    rot = []
    for name, muss, darf_nicht in FAELLE:
        if muss not in code:
            rot.append(name + ": FEHLT -> " + muss[:70])
        if darf_nicht and darf_nicht in code:
            rot.append(name + ": STEHT NOCH DA -> " + darf_nicht[:70])
    return rot


# ── ab v3.9.960: pytest sammelt das hier wirklich ein ──────────────────────

def test_die_fallliste_ist_nicht_leer():
    """Ohne diese Pruefung ist alles darunter wertlos.

    `_befunde` gibt bei leerer Fallliste eine leere Liste zurueck - also GRUEN,
    ohne eine einzige Messung. Genau diese Form (eine Schleife ueber einer
    leeren Menge, die als Erfolg gilt) ist der Grund, warum diese Datei
    ueberhaupt existiert.
    """
    assert len(FAELLE) == 18, (
        "Die Fallliste fuehrt %d Faelle, erwartet 18. Sinkt die Zahl, ist eine "
        "Kachel aus der Aufsicht gefallen - und dann meldet dieser Riegel "
        "gruen fuer etwas, das er nicht mehr ansieht." % len(FAELLE))
    for name, muss, _ in FAELLE:
        assert muss and name, "Fall %r hat kein Suchmuster." % name


@pytest.mark.parametrize("fall", FAELLE, ids=[f[0] for f in FAELLE])
def test_eine_ausgebliebene_messung_ist_null_und_keine_null(fall, index_html):
    """Je Fall einzeln, damit im roten Fall die KACHEL in der Meldung steht.

    Ein einziger Sammelfall haette denselben Schutz, aber die Meldung waere
    "18 Faelle, einer rot" - und man muesste erst suchen, welcher.
    """
    name, muss, darf_nicht = fall
    code = nur_code(index_html)
    assert muss in code, (
        "%s: die gehaertete Form fehlt.\n  erwartet: %s\n"
        "Steht dort wieder eine 0 statt null, behauptet die Kachel ein "
        "Messergebnis, das es nicht gibt - ein fehlgeschlagener Abruf sieht "
        "dann aus wie 'nichts offen'." % (name, muss[:100]))
    if darf_nicht:
        assert darf_nicht not in code, (
            "%s: die alte, falsche Form steht noch da.\n  gefunden: %s"
            % (name, darf_nicht[:100]))


def test_der_riegel_wird_bei_einer_zurueckgedrehten_kachel_rot(index_html):
    """KOEDER - und zwar genau die Mutation, mit der die Wirkung dieser Datei
    am 27.09. von Hand belegt wurde: setMatOpen(null) -> setMatOpen(0).

    Ohne diesen Fall waere "18 gruen" die Aussage eines Riegels, von dem
    niemand weiss, ob er ueberhaupt rot werden kann. Vier Wochen lang war er
    genau das.
    """
    code = nur_code(index_html)
    anker = "catch(_){if(a)setMatOpen(null);}"
    assert anker in code, (
        "Der Anker fuer den Koeder fehlt. Dann gehoert der Koeder an einen "
        "anderen der 18 Faelle - nicht weggelassen.")
    kaputt = code.replace(anker, "catch(_){if(a)setMatOpen(0);}", 1)
    rot = _befunde(kaputt)
    assert rot, (
        "KOEDER NICHT GEFUNDEN: eine zurueckgedrehte Kachel (0 statt null) "
        "wird nicht erkannt. Dann ist die Liste der 18 gruenen Faelle die "
        "Aussage eines Riegels, der nicht rot werden kann.")
    assert any(r.startswith("kachel_matOpen") for r in rot), (
        "Der Koeder wird gemeldet, aber unter dem falschen Namen: %s" % rot[:3])


def main(pfad):
    """Der eigenstaendige Aufruf, erhalten und bewusst.

    So ist diese Datei am 27.09. gegen eine KOPIE gefahren worden, um zu
    belegen, dass sie wirkt - pytest sammelte sie damals nicht ein. Ein
    Werkzeug, mit dem man einen fremden Stand pruefen kann, ist es wert,
    behalten zu werden. Es ersetzt aber die Faelle oben nicht: genau das war
    der Fehler.
    """
    code = nur_code(io.open(pfad, encoding="utf-8", newline="").read())
    rot = _befunde(code)
    for z in rot:
        print("ROT " + z)
    print(("GRUEN %d/%d" % (len(FAELLE), len(FAELLE))) if not rot
          else ("ROT %d Befunde" % len(rot)))
    return 1 if rot else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
