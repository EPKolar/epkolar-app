# -*- coding: utf-8 -*-
"""v3.9.1053 - Funde aus dem Scan 1051 (390 hell/dunkel, 844x390 quer, 1200 Tablet).

Reine Anzeige: (1) Fokus-/Sprung-Scrollen haelt am Telefon Abstand zur Fussleiste
(Werkzeug-Suche), (2) Flotte-Leerzustand liegt UNTER den Leaflet-Controls,
(3) Kontraste (Kopf-Slogan dunkel, MA-Uebersicht, Abwesenheiten, QR-Scan, Dispo,
Team-Timeline), (4) Projektakte-Kopf: Kunde/Ort unter 1200 px in eigener Zeile.

Die Riegel pruefen den neuen Code positiv, rechnen die Kontraste der eingesetzten
Farben gegen die im Scan GEMESSENEN Hintergruende nach und machen dort, wo es
sinnvoll ist, die Gegenprobe: mit dem alten Ausdruck muss der Riegel fallen.
"""
import re


def _lum(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    f = lambda v: v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2])


def _kontrast(a, b):
    x, y = sorted((_lum(a), _lum(b)), reverse=True)
    return (x + 0.05) / (y + 0.05)


def _lesbar(h, dark):
    """Nachbau von _lesbar (index.html) fuer Text (chip=False)."""
    n = int(h.lstrip("#"), 16)
    c = [(n >> 16) & 255, (n >> 8) & 255, n & 255]

    def lum(x):
        return _lum("#" + "".join("%02x" % round(v) for v in x))

    ziel = 255 if dark else 0
    for _ in range(40):
        if dark and not lum(c) < 0.33:
            break
        if not dark and not lum(c) > 0.145:
            break
        c = [v + (ziel - v) * 0.06 for v in c]
    return "#" + "".join("%02x" % round(v) for v in c)


def _v_dm_hell(src):
    m = re.search(r'dm:"(#[0-9A-Fa-f]{6})",\s*mt:"#646E68"', src)
    assert m, "V.dm (hell) nicht gefunden"
    return m.group(1)


def _umkehr(pruef, src, neu, alt):
    assert pruef(src), "Riegel greift am neuen Stand nicht"
    assert neu in src
    assert not pruef(src.replace(neu, alt)), "Gegenprobe: alter Stand muesste fallen"


# ── 1 Werkzeug-Suche / Fussleiste ────────────────────────────────────────

_SP = ("React.createElement('main', { className: \"main-pad\", ...mainSwipe, style: ww<BP_MOB?{scrollPaddingBottom:"
       "\"calc(var(--epk-bar-h,58px) + var(--epk-bar-warn,24px) + env(safe-area-inset-bottom,0px))\"}:undefined}")


def test_main_pad_scroll_padding_ueber_fussleiste(index_html):
    assert index_html.count(_SP) == 1
    # dieselben Groessen wie die Endreserve - nicht auseinanderlaufen
    assert ":root{--epk-bar-h:58px;--epk-bar-warn:24px}" in index_html


def test_wz_klebe_suche_und_fz_leiste_unveraendert(index_html):
    assert "function _wzKlebTop(ww){return ww<=600?-10:(ww<1200?-20:null);}" in index_html
    assert '...(_wzKleb!=null?{position:"sticky",top:_wzKleb,zIndex:3,background:V.bg,paddingTop:8,paddingBottom:8}:{})' in index_html
    assert '...(_fzKleb!=null?{position:"sticky",top:_fzKleb,zIndex:3,background:V.bg}:{})' in index_html
    # Kopf, Sync-Streifen und OfflineBanner stehen VOR <main class="main-pad"> - ausserhalb des Rollers
    main = index_html.index("React.createElement('main', { className: \"main-pad\"")
    assert index_html.index("React.createElement(OfflineBanner, {") < main
    assert index_html.index('" Server nicht erreichbar') < main


# ── 2 Flotte ─────────────────────────────────────────────────────────────

def _flotte_ok(src):
    i = src.find("'data-fz-leer':'1'")
    if i < 0:
        return False
    s = src[i:i + 400]
    m = re.search(r"zIndex:(\d+)", s)
    return bool(m) and 700 < int(m.group(1)) < 1000 and "padding:'10px 58px 24px'" in s


def test_flotte_leerzustand_unter_leaflet_controls(index_html):
    _umkehr(_flotte_ok, index_html, "inset:0,zIndex:900,display:'flex'", "inset:0,zIndex:1100,display:'flex'")
    # Karte bleibt im eigenen Stapelkontext
    assert "'data-fz-karte':'1',style:{position:'relative',zIndex:0,isolation:'isolate'" in index_html


# ── 3 Kontraste ──────────────────────────────────────────────────────────

def test_kopf_slogan_dunkel_lesbar(index_html):
    assert index_html.count("color:_dark?_lesbar(EP_GRAY):EP_GRAY") == 2
    assert "fontSize:UI.fMeta,color:EP_GRAY," not in index_html
    assert _kontrast("#6d6e71", "#181c19") < 4.5  # gemessener Fund
    assert _kontrast(_lesbar("#6d6e71", True), "#181c19") >= 4.5
    assert _kontrast("#6d6e71", "#ffffff") >= 4.5  # hell bleibt CI-Grau


def test_ma_uebersicht_nullen_lesbar(index_html):
    assert ('md.daysPlanned>=3?_lesbar("#f97316"):md.daysPlanned>0?_lesbar("#3b82f6"):V.dm,fontFamily:mono}}, md.daysPlanned)'
            in index_html)
    assert "color:t>0?_lesbar('#f97316'):V.dm}},t>0?t+' MA':'—')" in index_html
    dm = _v_dm_hell(index_html)
    for bg in ("#ffffff", "#fbfbfb", "#dbebe1"):
        assert _kontrast(dm, bg) >= 4.5, bg
    for h in ("#f97316", "#3b82f6"):
        assert _kontrast(_lesbar(h, False), "#ffffff") >= 4.5, h


def _abw_ok(src):
    return ("color:(ys.krankenstandStd||0)>0?UI.fehler:V.dm}}, _absH((ys.krankenstandStd||0),1)" in src  # Tablet-Runde 1077 (3): eine Nachkommastelle (68,5 statt 69)
            and 'color:kontUnlesbar?V.dm:rest<=20?UI.fehler:rest<=50?_lesbar("#eab308"):_okG("#22c55e")}}' in src)


def test_abwesenheiten_null_stunden_neutral(index_html):
    _umkehr(_abw_ok, index_html, "color:(ys.krankenstandStd||0)>0?UI.fehler:V.dm}}", "color:COLORS.ERROR}}")
    for bg in ("#fafafa", "#ffffff"):
        assert _kontrast("#ef4444", bg) < 4.5  # gemessener Fund
        assert _kontrast("#B91C1C", bg) >= 4.5
        assert _kontrast(_v_dm_hell(index_html), bg) >= 4.5
        assert _kontrast(_lesbar("#eab308", False), bg) >= 4.5
    for bg in ("#262b28", "#1e2320"):
        assert _kontrast("#FF6B6B", bg) >= 4.5


def test_qr_scan_texte_lesbar(index_html):
    assert '{fontSize:14,fontWeight:700,color:_lesbar(COLORS.WARNING),marginBottom:12}}, _asIk("kamera","Arbeitsschein QR-Code scannen")' in index_html
    assert 'asScanMsg.startsWith("❌")?_lesbar("#dc2626"):_lesbar("#ca8a04")}}, _scanMsgInhalt(asScanMsg))' in index_html
    assert '{fontSize:20,fontWeight:800,color:_lesbar(COLORS.WARNING),' in index_html
    assert _kontrast(_lesbar("#f97316", False), "#f2f4f2") >= 4.5
    assert _kontrast(_lesbar("#ca8a04", False), "#f1ecd6") >= 4.5
    assert _kontrast(_lesbar("#f97316", True), "#1e2320") >= 4.5


def _dispo_ok(src):
    return 'color:o.geplant?V.dm:(isFix?V.tx:(_dark?"#fdba74":"#9a3412")),fontVariantNumeric:"tabular-nums"}}' in src


def test_dispo_startzeit_dunkler(index_html):
    _umkehr(_dispo_ok, index_html, '(isFix?V.tx:(_dark?"#fdba74":"#9a3412")),fontVariantNumeric', '(isFix?V.tx:(_dark?"#fdba74":"#c2410c")),fontVariantNumeric')
    for bg in ("#f2eee7", "#efeae3"):
        assert _kontrast("#c2410c", bg) < 4.5  # gemessener Fund
        assert _kontrast("#9a3412", bg) >= 4.5


def test_team_timeline_tageszahlen(index_html):
    assert 'color:isToday?"#fff":V.dm,background:isToday?V.ac:we?"rgba(100,100,100,.06)":"transparent"' in index_html
    assert 'color:isToday?"#fff":we?V.mt:V.dm' not in index_html
    assert _kontrast("#646e68", "#e9ebe9") < 4.5  # gemessener Fund (V.mt)
    assert _kontrast(_v_dm_hell(index_html), "#e9ebe9") >= 4.5


# ── 4 Projektakte-Kopf ───────────────────────────────────────────────────

def test_projektakte_kopf_kunde_ort_eigene_zeile(index_html):
    assert ('{display:"flex",alignItems:"center",...(!isMob&&ww<1200?{flexWrap:"wrap"}:{}),gap:6,minWidth:0,flex:1}}, '
            "isMob&&React.createElement('button', { onClick: () => setMobNav(true)") in index_html
    assert 'display:isMob?"none":"-webkit-box",...(!isMob&&ww<1200?{flex:"1 1 0%"}:{})}}, p.name)' in index_html
    assert 'overflow:"hidden",...(!isMob&&ww<1200?{flexBasis:"100%"}:{})}}' in index_html
    # die Ellipse innen bleibt als letzter Rueckfall
    a = index_html.index('className: "topbar-detail", title:')
    assert 'whiteSpace:"nowrap",overflow:"hidden",textOverflow:"ellipsis"' in index_html[a:a + 1200]
    # ww ist in ProjectShell gebunden (isTab=ww<768 steht vor dem Kopf)
    k = index_html.index('className: "topbar-detail", title:')
    assert index_html.rfind("const isTab=ww<768;", 0, k) > k - 20000
