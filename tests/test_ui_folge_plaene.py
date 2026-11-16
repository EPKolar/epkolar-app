# -*- coding: utf-8 -*-
"""UI-Folge zu Plaene Stufe 2 - je Punkt ein Riegel MIT Umkehrprobe.

  1 Handy-Kopf    EINE Zeile ueber dem Plan (die Versionszeile schob ihn 364 -> 416 px); Version im Menue
  2 Status-Blatt  Raster mit 8 px Abstand und Spalten >= 120 px statt flex 30 % (abgeschnitten bei 360 px / im Tablet-Blatt)
  3 Schnellfilter Offen / In Arbeit / Ueberfaellig mit EINEM Tipp - am Handy AUF dem Plan (statt des Dauer-Hinweises)
  4 Zentrieren    erneuter Tipp auf DASSELBE Ticket zentriert wieder (Sperre nur gegen Neuzeichnen)
  6 PDF-Seiten    am Handy keine 110-px-Seitenleiste, Umschalter "Seite n/m"
  7 Manifest      background_color = helles V.bg (Standard-Thema hell); Startanzeige folgt der App-Wahl
  8 AS-Deep-Link  Reiter-Index aus der gerenderten Reiterliste (mit Chef) - Node fuehrt die echte Rechnung aus

Gemessen (Playwright, Offline-Sitzung, Schreibzugriffe abgefangen) - die Zahlen stehen im Bericht; hier wird
der Code festgehalten, der sie erzeugt.
"""
import io
import json
import os
import re

import pytest

from conftest import run_node_snippet

HIER = os.path.dirname(os.path.abspath(__file__))


def _vplan(src):
    a = src.index("function VPlan(")
    return src[a:src.index("// ═══════════ OFFA EXPORT", a)]


def _pvc(src):
    a = src.index("function PlanViewerCanvas(")
    return src[a:src.index("\nfunction ", a + 10)]


# ── 1 Handy-Kopf: eine Zeile ───────────────────────────────────────────────
def pruef_kopf(src):
    v = _vplan(src)
    b = []
    if "subView===\"viewer\"&&plans.length>0&&!isMob&&React.createElement('div', { style: {display:\"flex\",gap:8,alignItems:\"center\",flexWrap:\"wrap\",marginBottom:8}}" not in v:
        b.append("zweite Zeile (Version/Filterleiste) steht am Handy wieder ueber dem Plan")
    if 'isMob&&selPlan&&(_versionen.length>1?_mPunkt("uhr",_verText(_verAkt)' not in v:
        b.append("Handy-Menue ohne Planversion")
    if ", isMob&&_verListe(true)" not in v or ", _verListe(false)" not in v:
        b.append("Versionsliste nicht an beiden Stellen erreichbar")
    return b


def test_kopf(index_html):
    assert pruef_kopf(index_html) == []


@pytest.mark.parametrize("alt,neu", [
    ("subView===\"viewer\"&&plans.length>0&&!isMob&&React.createElement('div', { style: {display:\"flex\",gap:8,alignItems:\"center\",flexWrap:\"wrap\",marginBottom:8}}",
     "subView===\"viewer\"&&plans.length>0&&React.createElement('div', { style: {display:\"flex\",gap:8,alignItems:\"center\",flexWrap:\"wrap\",marginBottom:8}}"),
    (", isMob&&_verListe(true)", ""),
])
def test_kopf_umkehrprobe(index_html, alt, neu):
    assert alt in index_html, alt
    assert pruef_kopf(index_html.replace(alt, neu, 1)), "Riegel blind fuer: " + alt


# ── 2 Status-Knoepfe im Blatt ──────────────────────────────────────────────
def pruef_status_raster(src):
    a = src.index("function QuickEditPin(")
    q = src[a:src.index("\nfunction ", a + 10)]
    g = q[q.index("'aria-label':\"Status – speichert sofort\""):]
    g = g[:g.index("v.l)); })") + 10]
    b = []
    m = re.search(r'gridTemplateColumns:"repeat\(auto-fill, minmax\(min\(100%, (\d+)px\), 1fr\)\)", gap:(\d+)', g)
    if 'display:"grid"' not in g or not m:
        b.append("Status-Knoepfe nicht im Raster")
    elif int(m.group(1)) < 120 or int(m.group(2)) < 6:
        b.append("Rasterspalte < 120 px oder Abstand < 6 px - 'Abgeschlossen' (115 px) wird wieder abgeschnitten")
    if 'flex:"1 1 30%"' in g:
        b.append("Knoepfe wieder flex 30 %")
    if "minHeight:44" not in g:
        b.append("Knopf unter 44 px")
    return b


def test_status_raster(index_html):
    assert pruef_status_raster(index_html) == []


@pytest.mark.parametrize("alt,neu", [
    ('minmax(min(100%, 120px), 1fr))", gap:8', 'minmax(min(100%, 100px), 1fr))", gap:8'),
    ('\'aria-label\':"Status – speichert sofort", style:{display:"grid", gridTemplateColumns:', '\'aria-label\':"Status – speichert sofort", style:{display:"flex", flexWrap:"wrap", gridTemplateColumns:'),
])
def test_status_raster_umkehrprobe(index_html, alt, neu):
    assert alt in index_html, alt
    assert pruef_status_raster(index_html.replace(alt, neu, 1)), "Riegel blind fuer: " + alt


# ── 3 Schnellfilter (Handy: AUF dem Plan, statt des Dauer-Hinweises) ────────
def pruef_schnellfilter(src):
    v = _vplan(src)
    b = []
    i = v.find("'aria-label': \"Schnellfilter Status\"")
    if i < 0:
        b.append("kein Schnellfilter")
        return b
    box_a = v.index("React.createElement('div', { ref: _planBoxRef")
    box_e = v.index("_rechts&&React.createElement('div', { ref: _spalteRef")
    if not (box_a < i < box_e):
        b.append("Schnellfilter steht nicht auf dem Plan")
    if v.count("'aria-label': \"Schnellfilter Status\"") != 1:
        b.append("Schnellfilter doppelt (Kopf und Plan)")
    z = v[v.rindex("\n", 0, i):v.index("\n", i)]
    if "isMob&&_schnellAufPlan&&" not in z:
        b.append("Schnellfilter nicht auf das Handy beschraenkt")
    for soll in ('_fChip(filterStatus==="offen","Offen",()=>setFilterStatus(filterStatus==="offen"?"alle":"offen")',
                 '_fChip(filterStatus==="in_bearbeitung","In Arbeit",()=>setFilterStatus(filterStatus==="in_bearbeitung"?"alle":"in_bearbeitung")',
                 '_fChip(filterFrist==="ueberfaellig","Überfällig",()=>setFilterFrist(filterFrist==="ueberfaellig"?"alle":"ueberfaellig")'):
        if soll not in z:
            b.append("Schnellfilter fehlt/falsch: " + soll[:40])
    stil = v[v.index("const _schnellStil="):v.index("const _schnellStil=") + 200]
    if z.count("_schnellStil(") != 3 or 'pointerEvents:"auto"' not in stil:
        b.append("Knoepfe nicht tippbar (Leiste hat pointerEvents:none)")
    if 'flexWrap:"nowrap"' not in z or "right:82" not in z:
        b.append("Leiste bricht um oder laeuft unter die Werkzeugleiste")
    if "const _schnellAufPlan=!!selPlan&&plans.length>0&&!_altPlan&&!placing&&_planAlle.length>0&&!quickTicket&&!quickDefect&&!newTicket;" not in v:
        b.append("Knoepfe bleiben bei offenem Blatt (decken dann die obersten Pins)")
    if "selPlan&&plans.length>0&&!_altPlan&&!(isMob&&_schnellAufPlan)&&React.createElement('div', { 'aria-live': \"polite\"" not in v:
        b.append("Dauer-Hinweis und Knoepfe liegen uebereinander / Hinweis am Tablet weg")
    if 'sessionStorage.getItem("epk_hinweis_langtipp")' not in v or '"Lange tippen = neues Ticket hier (oder Plus-Knopf)"' not in v:
        b.append("Lange-Tipp-Hinweis am Handy nicht mehr auffindbar (einmal je Sitzung)")
    if "minWidth:isMob&&_planAlle.length>0?128:0" in v:
        b.append("Planwahl im Kopf wieder verkuerzt")
    return b


def test_schnellfilter(index_html):
    assert pruef_schnellfilter(index_html) == []


@pytest.mark.parametrize("alt,neu", [
    ('()=>setFilterFrist(filterFrist==="ueberfaellig"?"alle":"ueberfaellig"),"sf_ue"', '()=>setFilterStatus("offen"),"sf_ue"'),
    ('boxShadow:"0 2px 8px rgba(0,0,0,.25)",pointerEvents:"auto",flexShrink:0});', 'boxShadow:"0 2px 8px rgba(0,0,0,.25)",flexShrink:0});'),
    ("&&_planAlle.length>0&&!quickTicket&&!quickDefect&&!newTicket;", "&&_planAlle.length>0;"),
    ('try{if(sessionStorage.getItem("epk_hinweis_langtipp"))return;', "try{"),
    ("selPlan&&plans.length>0&&!_altPlan&&!(isMob&&_schnellAufPlan)&&React.createElement('div', { 'aria-live'", "selPlan&&plans.length>0&&!_altPlan&&React.createElement('div', { 'aria-live'"),
])
def test_schnellfilter_umkehrprobe(index_html, alt, neu):
    assert alt in index_html, alt
    assert pruef_schnellfilter(index_html.replace(alt, neu, 1)), "Riegel blind fuer: " + alt


# ── 7b Startanzeige folgt der App-Wahl ──────────────────────────────────────
def _kontrast(a, b):
    def lum(h):
        c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
        return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
    x, y = sorted([lum(a), lum(b)])
    return (y + 0.05) / (x + 0.05)


def pruef_startanzeige(src):
    b = []
    a = src.index('<div id="ep-boot-indicator"')
    kopf = src[:a]
    boot = src[a:src.index("},8000);", a)]
    m = re.search(r':root\[data-epk-thema="hell"\]\{([^}]*)\}</style>\s*$', kopf)
    if not m:
        b.append("keine helle Startanzeige direkt vor dem Element (Schluessel data-epk-thema aus Zeile 2)")
        return b
    var = dict(re.findall(r"(--epk-boot-[a-z0-9]+):(#[0-9A-Fa-f]{6})", m.group(1)))
    if var.get("--epk-boot-bg", "").upper() != "#F2F4F2":
        b.append("heller Grund nicht #F2F4F2")
    # jede Schriftfarbe auf dem hellen Grund >= 4,5:1; weisse Knopfschrift auf dem Knopfgrund ebenso
    for k in ("tx", "dm", "dm2", "fehler", "text", "orange", "klein", "warn"):
        w = var.get("--epk-boot-" + k)
        if not w or _kontrast(w, var.get("--epk-boot-bg", "#000000")) < 4.5:
            b.append("Kontrast --epk-boot-%s < 4,5:1" % k)
    if var.get("--epk-boot-orange") and _kontrast("#FFFFFF", var["--epk-boot-orange"]) < 4.5:
        b.append("Knopfschrift auf --epk-boot-orange < 4,5:1")
    if "prefers-color-scheme" in m.group(0):
        b.append("Startanzeige liest die Geraete-Einstellung")
    roh = re.findall(r"(?:color|background|border(?:-top-color)?):\s*(#[0-9a-fA-F]{3,6})", boot)
    roh = [c for c in roh if c.lower() not in ("#fff",)]
    if roh:
        b.append("feste Farben in der Startanzeige: %s" % sorted(set(roh)))
    if "background:var(--epk-boot-bg,#0f1117)" not in boot:
        b.append("Dunkel nicht mehr die bisherige Farbe (Rueckfallwert)")
    return b


def test_startanzeige(index_html):
    assert pruef_startanzeige(index_html) == []


@pytest.mark.parametrize("alt,neu", [
    ("--epk-boot-dm:#5B6660;", "--epk-boot-dm:#9AA39E;"),
    ('color:var(--epk-boot-fehler,#ff6666);margin-bottom:8px">⚠️ App startet nicht', 'color:#ff6666;margin-bottom:8px">⚠️ App startet nicht'),
    (':root[data-epk-thema="hell"]{--epk-boot-bg', ':root[data-x="hell"]{--epk-boot-bg'),
])
def test_startanzeige_umkehrprobe(index_html, alt, neu):
    assert alt in index_html, alt
    assert pruef_startanzeige(index_html.replace(alt, neu, 1)), "Riegel blind fuer: " + alt


# ── 4 erneut tippen = wieder zentrieren ────────────────────────────────────
def pruef_zentrieren(src):
    v = _vplan(src)
    pv = _pvc(src)
    b = []
    if "_react.useEffect.call(void 0, () => { _lastCenteredRef.current = null; }, [zentrierNr]);" not in pv:
        b.append("kein Aufheben der Zentrier-Sperre bei neuem Tipp")
    else:
        r = pv.index("_lastCenteredRef.current = null; }, [zentrierNr]);")
        z1 = pv.find("}, [selectedTicket && selectedTicket.id, pageDims, pageNum, pageCount, zentrierNr]);")
        z2 = pv.find("}, [selectedTicket && selectedTicket.id, _imgReady, _planSrc, zentrierNr]);")
        if z1 < 0 or z2 < 0:
            b.append("Zentrier-Effekte laufen bei neuem Tipp nicht neu")
        elif not (r < z1 and r < z2):
            b.append("Aufheben steht hinter den Zentrier-Effekten (Effekt-Reihenfolge)")
    if "_setZentrierNr(n=>n+1);setSelTicket(t);setQuickTicket(t);" not in v:
        b.append("Pin-Tipp zaehlt nicht hoch")
    if '(t)=>{setSelTicket(t);_setZentrierNr(n=>n+1);setSideMode("tickets");' not in v:
        b.append("Zeilen-Tipp zaehlt nicht hoch")
    if "zentrierNr: _zentrierNr" not in v:
        b.append("PlanViewerCanvas bekommt den Zaehler nicht")
    return b


def test_zentrieren(index_html):
    assert pruef_zentrieren(index_html) == []


@pytest.mark.parametrize("alt,neu", [
    ("_react.useEffect.call(void 0, () => { _lastCenteredRef.current = null; }, [zentrierNr]);", ""),
    ("}, [selectedTicket && selectedTicket.id, _imgReady, _planSrc, zentrierNr]);", "}, [selectedTicket && selectedTicket.id, _imgReady, _planSrc]);"),
    ("_setZentrierNr(n=>n+1);setSelTicket(t);setQuickTicket(t);", "setSelTicket(t);setQuickTicket(t);"),
])
def test_zentrieren_umkehrprobe(index_html, alt, neu):
    assert alt in index_html, alt
    assert pruef_zentrieren(index_html.replace(alt, neu, 1)), "Riegel blind fuer: " + alt


# ── 6 PDF-Seiten am Handy ──────────────────────────────────────────────────
def pruef_pdf_seiten(src):
    pv = _pvc(src)
    b = []
    if 'const _pvHandy = typeof window !== "undefined" && window.innerWidth < BP_MOB;' not in pv:
        b.append("keine Handy-Erkennung im Plan-Viewer")
    if "pageCount > 1 && !_pvHandy ? React.createElement('div', {\n      style: {width: 110," not in pv.replace("\r\n", "\n"):
        b.append("110-px-Seitenleiste auch am Handy")
    if '"Seite " + pageNum + "/" + pageCount' not in pv:
        b.append("Umschalter ohne 'Seite n/m'")
    return b


def test_pdf_seiten(index_html):
    assert pruef_pdf_seiten(index_html) == []


@pytest.mark.parametrize("alt,neu", [
    ("pageCount > 1 && !_pvHandy ? React.createElement('div', {", "pageCount > 1 ? React.createElement('div', {"),
    ('"Seite " + pageNum + "/" + pageCount', 'pageNum + "/" + pageCount'),
])
def test_pdf_seiten_umkehrprobe(index_html, alt, neu):
    assert alt in index_html, alt
    assert pruef_pdf_seiten(index_html.replace(alt, neu, 1)), "Riegel blind fuer: " + alt


# ── 7 Manifest: heller Startbildschirm ─────────────────────────────────────
def pruef_manifest(manifest_text, src):
    m = json.loads(manifest_text)
    hell = re.search(r'light:\{bg:"(#[0-9A-Fa-f]{6})"', src).group(1)
    b = []
    if m.get("background_color", "").lower() != hell.lower():
        b.append("background_color %s != helles V.bg %s" % (m.get("background_color"), hell))
    if m.get("theme_color") != "#009640":
        b.append("theme_color nicht Markengruen")
    return b


def _manifest():
    return io.open(os.path.join(HIER, "..", "manifest.json"), encoding="utf-8").read()


def test_manifest_hell(index_html):
    assert pruef_manifest(_manifest(), index_html) == []


def test_manifest_hell_umkehrprobe(index_html):
    t = _manifest()
    assert '"background_color": "#F2F4F2"' in t
    assert pruef_manifest(t.replace('"background_color": "#F2F4F2"', '"background_color": "#0f1117"'), index_html)


# ── 8 AS-Deep-Link: Reiter-Index ───────────────────────────────────────────
NUTZER = [
    {"role": "admin", "rolle": "Geschaeftsfuehrer"},
    {"role": "projektleiter", "rolle": "Geschäftsführer"},
    {"role": "projektleiter", "rolle": "Projektleiter"},
    {"role": "buero", "rolle": "Backoffice"},
    {"role": "monteur", "rolle": "Monteur"},
]


def _deeplink_lauf(node_exe, src):
    """Fuehrt die ECHTE Reiterliste (_allTabs + Filter), die ECHTE alte Rechnung (_navIds/vis) und _asReiterIdx aus."""
    zeile = lambda anker: src[src.index(anker):src.index("\n", src.index(anker))]
    nav = re.sub(r"/\*.*?\*/", "", zeile("const _navIds=["))
    vis = zeile("const vis=_navIds.filter(")
    fn = zeile("function _asReiterIdx(")
    b = src.index("const _allTabs=[")
    tabs = src[b:src.index("const safeKat=", b)]
    r0 = src.index("const ROLES={")
    roles = src[r0 + len("const ROLES="):src.index("\n};", r0) + 2]
    js = ("const FINKZEIT_ENABLED=true;const V={ac:'#009640'};const COLORS={ERROR:'#ef4444'};const _bauproOffenCount=0;\n"
          "const ROLES=" + roles + ";\nfunction hasPerm(u,m){return ((ROLES[u.role]||{}).modules||[]).indexOf(m)>=0;}function canDo(){return false;}\n"
          + fn + "\nfunction lauf(curUser){" + nav + "\n" + vis + "\n" + tabs +
          "\nconst i=_asReiterIdx(tabs,vis);return {neu:tabs[i]&&tabs[i].perm, leer:_asReiterIdx([],vis), alt:tabs[vis.indexOf('arbeitsscheine')].perm};}\n"
          "process.stdout.write(JSON.stringify(" + json.dumps(NUTZER, ensure_ascii=False) + ".map(lauf)));")
    return json.loads(run_node_snippet(node_exe, js))


def test_deeplink_trifft_arbeitsscheine(index_html, node_exe):
    r = _deeplink_lauf(node_exe, index_html)
    assert [x["neu"] for x in r] == ["arbeitsscheine"] * len(NUTZER), r
    # Beleg, dass es den Fehler gab: die alte Rechnung landet bei Admin und GF auf "projekte"
    assert [x["alt"] for x in r[:2]] == ["projekte", "projekte"], r
    assert all(x["leer"] == 2 for x in r)                  # leere Liste: alte Rechnung als Rueckfall


def test_deeplink_umkehrprobe(index_html, node_exe):
    kaputt = index_html.replace("if(t.length)return t.findIndex(", "if(false)return t.findIndex(", 1)
    assert kaputt != index_html
    r = _deeplink_lauf(node_exe, kaputt)
    assert [x["neu"] for x in r[:2]] != ["arbeitsscheine", "arbeitsscheine"]


def test_deeplink_nimmt_die_gerenderte_liste(index_html):
    assert "const idx=_asReiterIdx(_tabsListeRef.current,vis);" in index_html
    assert "_tabsCountRef.current=tabs.length||1;_tabsListeRef.current=tabs;" in index_html
