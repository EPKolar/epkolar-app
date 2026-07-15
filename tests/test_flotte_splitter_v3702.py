"""v3.9.702 — Flotte-Fahrtenbuch vergrößerbar (Drag-Splitter + Maximieren-Toggle).

Zwei Mechanismen wie im Windows Explorer:
 1. Drag-Splitter zwischen oberem Bereich (Fleet-Liste + Karte) und dem Fahrtenbuch-Panel.
 2. Maximieren-Toggle (⛶) im Fahrtenbuch-Kopf — Panel füllt den ganzen Flotte-Tab.

Die interaktiven Teile (ziehen, invalidateSize) prüft das Browser-Pflicht-Gate; hier die
Struktur-Invarianten, damit sie nicht versehentlich verschwinden.
"""


# ── Charts wachsen mit (SvgBar/SvgLine höhenfähig) ────────────────────────────
def test_svgbar_akzeptiert_maxH_deckel_hebbar(index_html):
    assert 'function SvgBar({data,height=140,color="#f97316",fmt,maxH})' in index_html
    assert 'maxHeight:((maxH&&maxH>0)?maxH:240)+"px"' in index_html


def test_svgline_akzeptiert_maxH(index_html):
    assert 'function SvgLine({data,width=320,height=150,color="#f97316",fmt,maxH})' in index_html
    assert 'maxHeight:((maxH&&maxH>0)?maxH+"px":"none")' in index_html


def test_charts_bekommen_gemessene_hoehe(index_html):
    """Beide Fahrtenbuch-Charts bekommen die nachgemessene chartH — sonst nur Leerraum."""
    assert index_html.count("height:chartH,maxH:chartH") == 2


def test_resize_observer_misst_den_inhaltsbereich(index_html):
    assert "const _bodyRef=_react.useRef.call(void 0, null);" in index_html
    assert "new ResizeObserver(" in index_html
    assert "ref:_bodyRef,style:{flex:1,minHeight:0,overflow:'auto'" in index_html


# ── Drag-Splitter ─────────────────────────────────────────────────────────────
def test_splitter_existiert_mit_row_resize(index_html):
    assert "onMouseDown:_onSplitMouseDown,onTouchStart:_onSplitTouchStart" in index_html
    assert "cursor:'row-resize'" in index_html


def test_splitter_haelt_min_hoehen_ein(index_html):
    """Weder Karte noch Fahrtenbuch dürfen auf 0 kollabieren."""
    assert "FLOTTE_MIN_TOP=180" in index_html
    assert "FLOTTE_MIN_BUCH=180" in index_html
    assert "if(nh<FLOTTE_MIN_TOP)nh=FLOTTE_MIN_TOP;" in index_html


def test_splitter_ruft_invalidateSize(index_html):
    """Leaflet braucht nach dem Ziehen invalidateSize, sonst Kachel-Löcher."""
    assert "_map.current.invalidateSize()" in index_html
    # In der Splitter-Bewegung throttled per rAF:
    assert "requestAnimationFrame(function(){_rafSplit.current=false;_mapInval();})" in index_html


def test_hoehe_wird_pro_geraet_persistiert(index_html):
    assert "localStorage.getItem('epk_flotte_topH')" in index_html
    assert "localStorage.setItem('epk_flotte_topH'," in index_html


# ── Maximieren-Toggle ─────────────────────────────────────────────────────────
def test_maximieren_button_im_kopf(index_html):
    assert "props.onToggleMax?h('button',{onClick:props.onToggleMax" in index_html


def test_maximieren_fuellt_den_tab_und_esc_schliesst(index_html):
    assert "if(maxBuch)return h('div',{style:{height:'calc(100dvh - 150px)'" in index_html
    assert "if(e.key==='Escape')setMaxBuch(false);" in index_html


def test_mobile_hat_maximieren_aber_keinen_splitter(index_html):
    """Mobile (<600px): kein Drag-Splitter, aber der Maximieren-Toggle greift."""
    assert "if(maxBuch)return h('div',{style:{height:'calc(100dvh - 128px)'" in index_html


# ── Worker-FahrtenbuchPanel bleibt unangetastet ───────────────────────────────
def test_worker_fahrtenbuchpanel_unveraendert(index_html):
    """Das andere (v3.5.79) FahrtenbuchPanel darf keine Maximier-/Splitter-Logik bekommen."""
    import re
    m = re.search(r"function FahrtenbuchPanel\(\{workerId.*?\n\}\n", index_html, re.S)
    assert m, "Worker-FahrtenbuchPanel nicht gefunden"
    body = m.group(0)
    for fremd in ("onToggleMax", "maxBuch", "epk_flotte_topH", "_onSplitMouseDown"):
        assert fremd not in body, f"'{fremd}' ist ins Worker-Panel geleakt"
