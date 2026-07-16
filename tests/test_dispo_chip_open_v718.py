# -*- coding: utf-8 -*-
"""v3.9.718 — Dispo P1-b: Chip + Wartelisten-Eintrag oeffnen den Arbeitsschein.

Sebastian: jeder Vorschlags-Chip UND jeder Wartelisten-Eintrag ist klickbar und oeffnet den AS im
Edit-Formular (window.__asOpenId-Muster v489, setSub 'liste' + openEdit). Der ✓-Uebernehmen-Button
bleibt separat (stopPropagation, damit Uebernehmen nicht zugleich oeffnet). Schein-Nr. am Chip anzeigen.
Struktur-Pins (DispoPanel ist React; Verhalten laeuft im Browser-Smoke).
"""


def _panel(index_html):
    start = index_html.index("function DispoPanel({")
    end = index_html.index("function ArbeitsscheinView({", start)
    return index_html[start:end]


def test_dispopanel_signature_onopenschein(index_html):
    assert "function DispoPanel({arbeitsscheine,monteure,wpHistory,abs,onUebernehmen,onOpenSchein,onDrop})" in index_html


def test_chip_oeffnet_schein(index_html):
    body = _panel(index_html)
    # Chip-Flaeche klickbar -> __asOpenId-Muster + onOpenSchein-Callback
    assert "window.__asOpenId=c.scheinId" in body
    assert "onOpenSchein(c.scheinId)" in body


def test_uebernehmen_stopt_propagation(index_html):
    body = _panel(index_html)
    idx = body.index("onUebernehmen(c.scheinId,m.id,t.iso,_eff,_dispoMinToHHMM(_win.startMin))")
    seg = body[idx - 140:idx]
    assert "stopPropagation" in seg, "Uebernehmen-Button ohne stopPropagation -> oeffnet zugleich den Schein"


def test_wartelisten_eintrag_oeffnet_schein(index_html):
    body = _panel(index_html)
    seg = body[body.index("Nicht eingeplant"):]
    assert "onOpenSchein(w.scheinId)" in seg


def test_chip_zeigt_scheinnr(index_html):
    body = _panel(index_html)
    seg = body[body.index("chips.map(function(c,ci)"):body.index("chips.length?h('div'")]
    # v3.9.742 #23: Chip rendert via gemeinsame _chipBox; die Schein-Nr. kommt aus _cs=_scheinById(...).
    assert "_cs=_scheinById(c.scheinId)" in seg and "nummer:(_cs.nummer" in seg, "Schein-Nr. fehlt am Chip"


def test_callsite_onopenschein_setzt_sub_und_openedit(index_html):
    i = index_html.index('sub==="dispo"&&React.createElement(DispoPanel,')
    seg = index_html[i:i + 1200]  # v733: onUebernehmen-Callback wuchs (terminZeit + Startzeit-Toast)
    assert "onOpenSchein:" in seg
    assert 'setSub("liste")' in seg
    assert "openEdit(" in seg
