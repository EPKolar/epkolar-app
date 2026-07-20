# -*- coding: utf-8 -*-
"""v3.9.766 — Dispo "Neu berechnen" = echte Datenfrische.

Befund: der Kopf-Button rief nur _setTick(t=>t+1) — ein deterministischer Recompute auf
UNVERAENDERTEN Daten, also fuer die Disponentin sichtbar wirkungslos (sie klickt, nichts
aendert sich, obwohl der DB-Stand laengst weiter ist).

Fix: onClick ruft _doDispoRefresh() (v761, Z.~9407) — zieht dispo_blocks frisch nach
window.__dispoBlocks und tickt erst DANACH. Der Geste-Guard (_gestureRef/_dragRef) greift
automatisch, der Pfad ist READ-ONLY (v745-Garantie: kein Write im Panel-Body).

NICHT gebaut (bewusst, Auftrags-Halt): der arbeitsscheine-Stand haengt weiter am bestehenden
5-Min-Poll. Ein Einmal-Trigger aus dem Panel gaebe es nur ueber eine NEUE Eltern-Prop, weil
setArbeitsscheine in ArbeitsscheinView lebt, nicht in DispoPanel — das waere neues Wiring,
kein Bestandspfad. test_kein_as_pull_im_panel pinnt genau das.
"""
import re


def _panel(index_html):
    start = index_html.index("function DispoPanel({")
    end = index_html.index("function ArbeitsscheinView({", start)
    return index_html[start:end]


def _button(index_html):
    body = _panel(index_html)
    # v3.9.767: onClick ist seit der onRefreshScheine-Verdrahtung mehrzeilig -> re.S statt Ein-Zeilen-Match.
    m = re.search(r"h\('button',\{onClick:.*?\"↻ Neu berechnen\"\)", body, re.S)
    assert m, "Button '↻ Neu berechnen' nicht mehr auffindbar (Renderpfad veraendert?)"
    return m.group(0)


# ---------------------------------------------------------------- Button-Wiring

def test_button_ruft_dorefresh(index_html):
    btn = _button(index_html)
    assert "_doDispoRefresh()" in btn, \
        "'Neu berechnen' ruft _doDispoRefresh nicht — ohne Re-Fetch ist der Klick wirkungslos"


def test_button_nicht_mehr_nur_settick(index_html):
    btn = _button(index_html)
    assert "_setTick(" not in btn, \
        "Button tickt wieder direkt (_setTick) statt ueber _doDispoRefresh — Regression auf den Alt-Befund"


def test_dorefresh_existiert_und_zieht_blocks(index_html):
    body = _panel(index_html)
    assert "var _doDispoRefresh=function(){" in body, "_doDispoRefresh fehlt/Signatur veraendert"
    m = re.search(r"var _doDispoRefresh=function\(\)\{.*?\n  \};", body, re.S)
    assert m, "_doDispoRefresh-Rumpf nicht lesbar"
    fn = m.group(0)
    assert '_sbGet("dispo_blocks")' in fn, "_doDispoRefresh zieht dispo_blocks nicht frisch"
    assert "window.__dispoBlocks=" in fn, "frischer Stand landet nicht in window.__dispoBlocks"
    assert "_setTick(" in fn, "_doDispoRefresh rechnet nicht neu"


# ---------------------------------------------------------------- v745 read-only

def test_refresh_pfad_bleibt_readonly(index_html):
    m = re.search(r"var _doDispoRefresh=function\(\)\{.*?\n  \};", _panel(index_html), re.S)
    fn = m.group(0)
    for schreib in ("_sbPost", "_sbPatch", "_sbDelete", "updAs("):
        assert schreib not in fn, \
            "v745 verletzt: _doDispoRefresh schreibt (" + schreib + ") — der Panel-Body bleibt schreibfrei"


def test_geste_guard_bleibt(index_html):
    m = re.search(r"var _doDispoRefresh=function\(\)\{.*?\n  \};", _panel(index_html), re.S)
    fn = m.group(0)
    assert "_gestureRef.current||_dragRef.current" in fn, \
        "Geste-Guard weg — ein Klick waehrend Drag reisst den Chip aus der Hand"


# ---------------------------------------------------------------- Halt-Befund gepinnt

def test_kein_as_pull_im_panel_body(index_html):
    """v3.9.767 umgestellt: das Panel darf den AS-Pull NICHT selbst fahren — nur die Prop rufen.

    Vorher (v766) pinnte dieser Test 'Panel zieht ueberhaupt keine AS'. Seit der Prop onRefreshScheine
    existiert, ist die Aussage: der Pull-Mechanismus (_juprowaSync/_asPullFresh/_sbGet arbeitsscheine)
    bleibt im Eltern-Component, das Panel kennt nur den Prop-Namen (v745: kein Fetch/Write im Panel-Body).
    """
    body = _panel(index_html)
    assert "_juprowaSync(" not in body, "DispoPanel ruft _juprowaSync direkt — gehoert in den Parent"
    assert "_asPullFresh(" not in body, "DispoPanel ruft den AS-Pull selbst — gehoert an die Prop-Callsite"
    assert '_sbGet("arbeitsscheine")' not in body, "DispoPanel fetcht arbeitsscheine selbst (v745 verletzt)"
    assert "onRefreshScheine" in body, "Prop onRefreshScheine im Panel nicht verdrahtet"


def test_dispopanel_signatur_v767(index_html):
    assert ("function DispoPanel({arbeitsscheine,monteure,wpHistory,abs,onUebernehmen,"
            "onOpenSchein,onDrop,onToggleBlock,onRefreshScheine}){") in index_html, \
        "DispoPanel-Signatur veraendert — Prop-Pins v715-718/v734/v760 mitziehen"
