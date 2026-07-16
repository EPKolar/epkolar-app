# -*- coding: utf-8 -*-
"""v3.9.725 — Register #14: KW-Navigation — durchschalten statt aufklappen.

Sebastian: prominente KW-Tabs [◀] KW30(N) | KW31(N) | KW32(N) [▶] im Wochenplanungs-Stil, aktive KW
gefuellt, Zaehler "(N geplant)" + Auslastung%; GLEICH Desktop und Mobile. Immer GENAU EINE KW als
Raster; Tab-Wechsel ohne Re-Compute. ◀/▶ am Rand disabled (Tooltip Horizont). Gewaehlte KW ueberlebt
"Neu berechnen". Uebernahme schreibt das Datum der AKTIVEN KW (v722 gepinnt). Die v722-Klapp-Sektionen
entfallen ersatzlos.
"""


def _panel(index_html):
    start = index_html.index("function DispoPanel({")
    end = index_html.index("function ArbeitsscheinView({", start)
    return index_html[start:end]


def test_kw_index_state(index_html):
    body = _panel(index_html)
    assert "_kwIdx" in body and "_setKwIdx" in body, "aktive KW nicht als eigener State (ueberlebt Neu-berechnen)"


def test_klapp_sektionen_entfallen(index_html):
    body = _panel(index_html)
    assert "_setOpenW" not in body and "_openW" not in body, "alte Klapp-Sektionen (v722) nicht entfernt"
    assert "_setMobKw" not in body and "_mobKw" not in body, "alter Mobile-KW-State (v722) nicht entfernt"


def test_blaetter_buttons_disabled_am_rand(index_html):
    body = _panel(index_html)
    # ◀ und ▶ Blaetter-Buttons
    assert "◀" in body and "▶" in body, "Blaetter-Pfeile fehlen"
    assert "disabled:" in body, "Blaetter-Buttons nicht am Rand disabled"
    assert "Planungshorizont" in body, "Tooltip 'Planungshorizont' fehlt"


def test_ein_raster_pro_kw(index_html):
    body = _panel(index_html)
    # Es wird genau eine aktive Woche gerendert (_weekTable auf die aktive KW), nicht alle gestapelt.
    assert "wochen[_ak]" in body or "wochen[_kwIdx]" in body, "aktive KW wird nicht einzeln gerendert"


def test_uebernahme_schreibt_aktive_kw(index_html):
    # v722-Verhalten gepinnt: Uebernahme uebergibt t.iso (Datum der jeweiligen Zelle/KW).
    body = _panel(index_html)
    # v3.9.732 #16b: Dauer-Arg ist jetzt _effDauer(c); das KW-Datum t.iso bleibt unveraendert.
    assert "onUebernehmen(c.scheinId,m.id,t.iso,_effDauer(c))" in body, "Uebernahme schreibt nicht das KW-Datum"
