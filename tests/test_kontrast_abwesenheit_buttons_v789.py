# -*- coding: utf-8 -*-
"""v3.9.789 — Kontrast der AbsView-Antragsbuttons "Krankmeldung"/"Zeitausgleich" (Sebastian 21.07., live).

Vorher: pastell rgba(.18)-Flaeche + heller Text (#fca5a5 rot / #d8b4fe violett) = praktisch unlesbar.
Fix: satte Fuellung + weisser Text (Krank #dc2626, ZA #7c3aed) wie "Urlaub beantragen" — WCAG >=4.5:1,
hell+dunkel identisch (button-bg theme-unabhaengig), Farb-Semantik (rot/violett) + Layout unveraendert.
"""


def test_krankmeldung_kraeftig_rot(index_html):
    """Krankmeldung-Button: lesbar UND ohne Gefahren-Rot.
    v3.9.1006 CI: v789 hatte die Lesbarkeit mit satter roter Fuellung geloest - Rot ist im CI
    aber Gefahr (Loeschen/Storno/Abmelden), eine Krankmeldung ist keine. Jetzt Sekundaerknopf
    (bsS: Schrift V.tx, gemessen >= 4,5:1 in beiden Themen, siehe test_ci_ep_kolar_v1006)."""
    assert 'setTyp("krankenstand");setReqOpen(true);}, style: {...bsS(),' in index_html
    assert 'background:"#dc2626",border:"none",color:"#fff",fontWeight:700,cursor:"pointer",fontFamily:"inherit"}}, "\U0001f912 Krankmeldung"' not in index_html
    # alte pastell/hellrote Alt-Werte weg
    assert 'background:"rgba(239,68,68,.18)",border:"2px solid rgba(239,68,68,.55)",color:"#fca5a5"' not in index_html


def test_zeitausgleich_kraeftig_violett(index_html):
    """Zeitausgleich-Button: lesbar, ohne Lila (v3.9.1006 CI: Lila trug keine Bedeutung) -
    Sekundaerknopf bsS mit Schrift V.tx."""
    assert 'setTyp("zeitausgleich");setReqOpen(true);}, style: {...bsS(),' in index_html
    assert 'background:"#7c3aed"' not in index_html
    # alte pastell/hellviolette Alt-Werte weg
    assert 'background:"rgba(168,85,247,.18)",border:"2px solid rgba(168,85,247,.55)",color:"#d8b4fe"' not in index_html


def test_urlaub_button_unveraendert_referenz(index_html):
    """Die Referenz 'Urlaub beantragen' (kraeftig gruen, weisser Text) bleibt unveraendert."""
    assert 'background:"#009640",border:"none",color:"#fff"' in index_html
    # Layout-Konsistenz: alle drei Antrags-Buttons nutzen dieselbe Padding/Radius-Basis
    assert index_html.count('padding:isMob?"10px 14px":"12px 20px",fontSize:isMob?12:14,borderRadius:10') >= 3
