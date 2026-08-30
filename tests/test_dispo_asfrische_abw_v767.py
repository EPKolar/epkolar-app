# -*- coding: utf-8 -*-
"""v3.9.767 — TEIL A: "Neu berechnen" holt frische Arbeitsscheine. TEIL B: nur GENEHMIGTE Abwesenheit blockt.

TEIL A
------
Bis v766 zog der Button nur dispo_blocks frisch; die Arbeitsscheine hingen am 5-Min-Poll -> der Klick
rechnete denselben Schein-Bestand neu -> derselbe Plan. Jetzt: Prop `onRefreshScheine` (Callsite in
ArbeitsscheinView) -> `_asPullFresh(setArbeitsscheine)` -> DANN `_doDispoRefresh()`.

WICHTIG (TABU): `_asPullFresh` ist der REINE DB-Pull (Schritt 3 aus `_juprowaSync` herausgezogen) —
KEIN `juprowa_fetch_worksheets`-RPC, KEINE arbeitsscheine-Reconciliation, vor allem KEIN
`_juprowaDrainPending` -> ein Klick loest KEINEN OFFA/Juprowa-Push aus. `_juprowaSync` nutzt denselben
Helper, damit es genau EINEN Pfad gibt (keine Dublette, 5-Min-Poll unveraendert).

TEIL B (Sebastian-Entscheid 20.07.)
-----------------------------------
Vorher blockten genehmigt UND beantragt die Kapazitaet. Jetzt blockt NUR `genehmigt`. Weil der
Overlay-Chip (`blockGrund`) aus `absAbz` abgeleitet wird, verschwindet beantragt damit automatisch auch
aus der Anzeige -> Konsistenz Anzeige == Kapazitaet (genau das war die Vorgabe).
"""
import re
import subprocess


def _panel(index_html):
    start = index_html.index("function DispoPanel({")
    end = index_html.index("function ArbeitsscheinView({", start)
    return index_html[start:end]


def _fn(index_html, name):
    m = re.search(r"(?:async )?function " + name + r"\(.*?\n\}", index_html, re.S)
    assert m, name + " nicht gefunden"
    return m.group(0)


# ================================================================ TEIL A

def test_aspullfresh_existiert_und_ist_reiner_pull(index_html):
    fn = _fn(index_html, "_asPullFresh")
    assert '_sbGet("arbeitsscheine")' in fn, "_asPullFresh zieht arbeitsscheine nicht"
    assert "setArbeitsscheine(" in fn, "_asPullFresh schreibt den State nicht"
    for verboten in ("_juprowaDrainPending", "_juprowaPush", "juprowa_fetch_worksheets",
                     "_sbPatch", "_sbPost", "_sbDelete"):
        assert verboten not in fn, \
            "TABU verletzt: _asPullFresh enthaelt " + verboten + " — der Button darf NICHT nach OFFA schreiben/pushen"


def test_juprowasync_nutzt_denselben_helper(index_html):
    """EIN Pfad statt Dublette — sonst driften Button-Pull und Poll-Pull auseinander."""
    fn = _fn(index_html, "_juprowaSync")
    assert "_asPullFresh(setArbeitsscheine)" in fn, \
        "_juprowaSync nutzt den gemeinsamen Pull-Helper nicht (Dublette/Drift-Gefahr)"


def test_button_reihenfolge_erst_as_dann_recompute(index_html):
    body = _panel(index_html)
    m = re.search(r"h\('button',\{onClick:function\(\)\{(.*?)\},style:\{\.\.\.bpS", body, re.S)
    assert m, "Button-onClick nicht mehr auffindbar"
    oc = m.group(1)
    assert "onRefreshScheine()" in oc, "Button zieht die Scheine nicht frisch"
    assert "_doDispoRefresh()" in oc, "Button rechnet nicht neu"
    assert oc.index("onRefreshScheine()") < oc.index("_doDispoRefresh()"), \
        "Reihenfolge falsch: der Recompute muss NACH dem AS-Pull laufen, sonst sieht er den alten Stand"
    assert ".then(" in oc, "kein Warten auf den Pull — der Recompute wuerde den alten Stand sehen"


def test_callsite_verdrahtet_bestandspfad(index_html):
    start = index_html.index("function ArbeitsscheinView({")
    view = index_html[start:]
    assert "onRefreshScheine: ()=>_asPullFresh(setArbeitsscheine)" in view, \
        "Callsite (Render DispoPanel) verdrahtet onRefreshScheine nicht auf den Bestands-Pull"


def test_kein_optional_chaining_in_neuen_teilen(index_html):
    assert "?." not in _fn(index_html, "_asPullFresh"), "optional chaining in _asPullFresh"


# ================================================================ TEIL B

def test_nur_genehmigt_blockt_statisch(index_html):
    fn = _fn(index_html, "_dispoAbwAbzug")
    assert '!=="genehmigt"' in fn, \
        "_dispoAbwAbzug blockt nicht mehr ausschliesslich auf genehmigt (Sebastian-Entscheid 20.07.)"
    assert '==="abgelehnt"' not in fn, "alte abgelehnt-Sonderregel noch drin — beantragt wuerde weiter blocken"


def test_abwabzug_verhalten_node_eval(index_html, tmp_path):
    """PURE-Kern echt ausfuehren: genehmigt blockt, beantragt/ausstehend/abgelehnt nicht."""
    fn = _fn(index_html, "_dispoAbwAbzug")
    js = fn + """
var out=[];
out.push(_dispoAbwAbzug({typ:'urlaub',status:'genehmigt',std:0},480));
out.push(_dispoAbwAbzug({typ:'urlaub',status:'beantragt',std:0},480));
out.push(_dispoAbwAbzug({typ:'urlaub',status:'ausstehend',std:0},480));
out.push(_dispoAbwAbzug({typ:'urlaub',status:'abgelehnt',std:0},480));
out.push(_dispoAbwAbzug({typ:'urlaub',std:0},480));
out.push(_dispoAbwAbzug({typ:'za',status:'genehmigt',std:4},480));
out.push(_dispoAbwAbzug({typ:'za',status:'beantragt',std:4},480));
out.push(_dispoAbwAbzug(null,480));
console.log(JSON.stringify(out));
"""
    f = tmp_path / "abw.js"
    f.write_text(js, encoding="utf-8")
    r = subprocess.run(["node", str(f)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    got = r.stdout.strip().splitlines()[-1]
    assert got == "[480,0,0,0,480,240,0,0]", (
        "Abwesenheits-Abzug falsch: erwartet genehmigt=Volltag(480)/Teiltag(240), "
        "beantragt+ausstehend+abgelehnt=0, fehlender Status blockt weiter (480). Bekommen: " + got)


# v3.9.915: FRUEHER stand hier ein Textvergleich auf zwei woertliche Zeilen,
# gesucht in einem festen Fenster von 7500 Zeichen. Beides war falsch.
#
# Der Textvergleich verlangte GENAU die Zeile, die am Feiertag abgestuerzt ist:
#     if(absAbz>=t.normMin){gruende.push(_dispoAbwLabel(ab.type));}
# Bei normMin 0 und fehlendem Eintrag ist 0>=0 wahr und ab undefined - der
# Riegel hat den Fehler also nicht gefunden, sondern FESTGEHALTEN, und waere
# gegen seine Reparatur rot geworden. Ein Riegel, der die Schreibweise
# abschreibt, misst die Schreibweise.
#
# Und das Fenster musste in v3.9.807 schon einmal von 6000 auf 7500 geweitet
# werden, weil ein Umbau die gesuchte Zeile hinausgeschoben hatte. Ein Fenster,
# dessen Breite man frei waehlt, misst die Fensterbreite mit.
#
# Die ABSICHT bleibt unveraendert - sie wird jetzt AUSGEFUEHRT statt gelesen.
def test_overlay_folgt_der_kapazitaet(index_html, tmp_path):
    """Anzeige == Kapazitaet: der Grund-Chip haengt an absAbz, nicht an einer zweiten Statusregel."""
    from _hilfen import dispo_zelle_programm, dispo_zelle_lauf

    werktag = {"key": "d", "iso": "2026-09-15", "wtag": "Di", "normMin": 510, "feiertag": False}
    feiertag = {"key": "d", "iso": "2026-10-26", "wtag": "Mo", "normMin": 0, "feiertag": True}

    def abw(**kw):
        eintrag = {"type": "urlaub", "status": "genehmigt", "hours": 0}
        eintrag.update(kw)
        return {"Huber_2026-09-15": eintrag}

    faelle = [
        {"t": werktag, "absMap": {}},
        {"t": werktag, "absMap": abw()},
        {"t": werktag, "absMap": abw(hours=4)},
        {"t": werktag, "absMap": abw(status="beantragt")},
        {"t": werktag, "absMap": abw(type="krankenstand")},
        {"t": feiertag, "absMap": {}},
    ]
    aus = dispo_zelle_lauf(dispo_zelle_programm(index_html), tmp_path, faelle, "v767.js")

    for i, r in enumerate(aus):
        assert r["ok"], "Fall {} wirft: {}".format(i, r.get("fehler"))

    # DIE Eigenschaft: am Werktag steht genau dann ein Abwesenheits-Chip da,
    # wenn auch Kapazitaet abgezogen wurde. Anzeige und Kapazitaet duerfen nicht
    # auseinanderlaufen - das war der ganze Sinn dieses Riegels.
    for i, r in enumerate(aus[:5]):
        assert bool(r["labels"]) == (r["abw"] > 0), (
            "Fall {}: Chip {} passt nicht zum Kapazitaetsabzug {} - "
            "Anzeige und Kapazitaet laufen auseinander".format(i, r["labels"], r["abw"]))

    assert aus[0]["labels"] == [] and aus[0]["abw"] == 0
    assert aus[1]["labels"] == ["Urlaub"] and aus[1]["abw"] == 510, "Volltag: voller Abzug"
    assert aus[2]["labels"] == ["Urlaub"] and aus[2]["abw"] == 240, "Teiltag: 4h = 240 min"
    assert aus[3]["labels"] == [] and aus[3]["abw"] == 0, \
        "Ein BEANTRAGTER Urlaub ist keine Abwesenheit - weder in der Anzeige noch in der Kapazitaet"
    assert aus[4]["labels"] == ["Krankenstand"], "Der Chip nennt den Typ, nicht 'abwesend'"
    assert aus[5]["labels"] == ["Feiertag"], \
        "Am Feiertag nennt die Zelle den Feiertag (v3.9.915) - vorher warf sie hier"
