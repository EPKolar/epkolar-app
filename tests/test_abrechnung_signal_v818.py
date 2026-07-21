# -*- coding: utf-8 -*-
"""v3.9.818 — Abrechnungs-Signal (Paket E): 'Erledigt, noch nicht fakturiert' im Chef-Dashboard.

Reine Anzeige: erledigte Scheine (status "erledigt", noch nicht abgerechnet/bar_bezahlt) werden im
Sorgen-Widget sichtbar + verlinkt, damit fertige Arbeit nicht unbemerkt unfakturiert liegen bleibt.
Kein Schreibpfad. Dieser Test pinnt die Verdrahtung.
"""


def test_asErledigtOffen_berechnet(index_html):
    # Count der Scheine mit status "erledigt" (im useMemo, ueber arbeitsscheine).
    assert 'const asErledigtOffen=_react.useMemo.call(void 0, ()=>(arbeitsscheine||[]).filter(function(a){return a&&a.scheinstatus==="erledigt";}).length,[arbeitsscheine]);' in index_html, \
        "asErledigtOffen-Berechnung fehlt/veraendert"


def test_in_sorgenTotal(index_html):
    assert "+(finkOpen?finkOpen.length:0)+asErledigtOffen;" in index_html, "asErledigtOffen nicht in sorgenTotal"


def test_alert_div_und_deeplink(index_html):
    assert "asErledigtOffen>0&&React.createElement('div'" in index_html, "Alert-Div fehlt (nur >0 anzeigen)"
    assert "Erledigt, noch nicht fakturiert" in index_html, "Alert-Text fehlt"
    # Deep-Link zu den Arbeitsscheinen.
    a = index_html.index("asErledigtOffen>0&&React.createElement('div'")
    block = index_html[a:a + 600]
    assert "onNav('arbeitsscheine')" in block, "Deep-Link zu Arbeitsscheinen fehlt im Alert"


def test_reine_anzeige_kein_schreibpfad(index_html):
    # Der Alert-Block darf nichts schreiben (SQ.push/updAs).
    a = index_html.index("asErledigtOffen>0&&React.createElement('div'")
    block = index_html[a:a + 600]
    assert "SQ.push" not in block and "updAs" not in block, "Abrechnungs-Signal darf reine Anzeige sein"
