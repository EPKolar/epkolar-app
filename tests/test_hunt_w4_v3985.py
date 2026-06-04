"""v3.9.125 — Hunt-Welle 4 (Finder F/G/H) + Sebastian-Regel: Monteur darf keine Scheine anlegen."""


def test_monteur_cannot_create_as(index_html):
    # Sebastian 04.06.2026: Monteur darf GAR KEINE Arbeitsscheine anlegen.
    assert "as_create:isA||isPL||isB||isOM||isTech" in index_html, (
        "as_create darf Monteur NICHT mehr enthalten (kein isField mehr)"
    )
    # Defense-in-Depth im saveAs: Neuanlage geblockt, Bearbeiten bleibt
    assert "if(isMonteurRole&&!isAdmin&&!editId){" in index_html
    assert "Monteure dürfen keine Arbeitsscheine anlegen" in index_html


def test_as_dauer_comma_normalized(index_html):
    # G1: "3,5" hätte via parseFloat 3.0 ergeben — Komma-Norm im Save-Payload
    assert 'const _normDauer=(form.dauer!==""&&form.dauer!=null)?String(form.dauer).replace(",","."):form.dauer;' in index_html
    assert index_html.count("dauer:_normDauer") == 2  # beide _finalForm-Zweige


def test_projekt_betrag_clamped(index_html):
    # G2: negative Auftragssummen verfälschten Budget-Auswertungen
    assert 'betrag:Math.max(0,parseFloat(e.target.value)||0)' in index_html


def test_projekt_datums_plausibilitaet(index_html):
    # G3: ende < start war speicherbar
    assert 'if(form.start&&form.ende&&form.ende<form.start){' in index_html
    assert "Ende-Datum liegt vor dem Start-Datum" in index_html


def test_overflow_fixes_wave4(index_html):
    # H4 Chef-Ampeln, H5 MA-Liste, H6 Fahrzeug-Termine
    assert "maxWidth:isMob?150:280,overflow:'hidden',textOverflow:'ellipsis'" in index_html
    assert 'fontSize:isMob?15:13,fontWeight:600,overflow:"hidden",textOverflow:"ellipsis"' in index_html
    assert '{flex:1,minWidth:0}}, React.createElement(\'div\', { style: {fontSize:13,fontWeight:600,overflow:"hidden"' in index_html


def test_empty_states_wave4(index_html):
    # F9 Mängel-Empty + F11 VDoku-Suchtreffer
    assert "Noch keine Mängel erfasst" in index_html
    assert "Keine Treffer für" in index_html
