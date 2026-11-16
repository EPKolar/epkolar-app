# -*- coding: utf-8 -*-
"""v3.9.1019 Systemeinstellungen: Beschriftung wurde am Handy Buchstabe fuer Buchstabe umbrochen.

Ursache (gemessen 16.11., Layout-Modell 360/412 px): das Eingabefeld bekam unter BP_MOB width:100%,
die Beschriftung (seit v1017 die lange Beschreibung statt des Schluessels) behielt 0 px Breite.
Jetzt bricht die ZEILE um (flexWrap), die Beschriftung hat eine Mindestbreite und bricht nur an Woertern.
Werte, Speicherweg (save/onBlur) und Schluessel bleiben unveraendert."""


def _zeile(html):
    i = html.index("'data-syscfg-zeile':row.key")
    return html[i - 120:html.index("saving[row.key]&&", i)]


def test_zeile_bricht_um_statt_zu_quetschen(index_html):
    z = _zeile(index_html)
    assert "flexWrap:'wrap'" in z
    assert "flex:'1 1 200px',minWidth:'min(200px,100%)'" in z
    assert "wordBreak:'normal'" in z


def test_feld_nie_mehr_volle_breite_neben_dem_label(index_html):
    z = _zeile(index_html)
    assert 'width:window.innerWidth<BP_MOB?"100%":130' not in z
    assert "width:130,maxWidth:'100%',flex:'0 0 auto'" in z


def test_speicherweg_unveraendert(index_html):
    z = _zeile(index_html)
    assert ("onBlur:e=>{if(e.target.value!==row.value){save(row.key,e.target.value);"
            "setCfg(p=>p.map(r=>r.key===row.key?{...r,value:e.target.value}:r));}}") in z


def test_umkehrprobe(index_html):
    kaputt = index_html.replace("flexWrap:'wrap',columnGap:12", "columnGap:12", 1)
    assert "flexWrap:'wrap'" not in _zeile(kaputt)
