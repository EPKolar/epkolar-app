# -*- coding: utf-8 -*-
"""Tablet-Pruefung 1046 (Geraet ~1340 quer / ~800 hoch) - reine Anzeige.

Kontrast (Namenschips Planung, Rollen MA-Uebersicht, AS-Kalender, Material-
Prioritaet, Kalibrierung, Buero-Portal Tank/Attest, Fuehrerschein-Chips),
negativer Resturlaub rot, Werkzeugwert ehrlich, Diagrammfarben je Auftragsart,
Emoji -> Linien-Ikonen, Dispo-Sperrknopf ueber der Startzeit, Projektakte-Kopf,
Balkenbeschriftungen, letzter Juprowa-Sync nach dem Neuladen.

Die Kontraste werden mit derselben Rechnung wie _lesbar (index.html) NACHGERECHNET,
nicht abgeschrieben: wer _lesbar oder eine Grundfarbe aendert, sieht es hier.
"""
import re

import pytest


# ── Rechenwerk (WCAG 2.x) + _lesbar-Nachbau ─────────────────────────────

def _rgb(h):
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)]


def _f(v):
    v /= 255
    return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4


def _lum(c):
    c = _rgb(c) if isinstance(c, str) else c
    return 0.2126 * _f(c[0]) + 0.7152 * _f(c[1]) + 0.0722 * _f(c[2])


def _k(a, b):
    x, y = sorted((_lum(a), _lum(b)), reverse=True)
    return (x + 0.05) / (y + 0.05)


def _hx(c):
    return "#" + "".join("%02x" % int(round(v)) for v in c)


def _mix(oben, unten, alpha):
    a, b = _rgb(oben), _rgb(unten)
    return _hx([a[i] * alpha + b[i] * (1 - alpha) for i in range(3)])


def _lesbar(h, chip=False, dunkel=False):
    """Schrittgleich zu function _lesbar(h,chip) in index.html."""
    c = [float(v) for v in _rgb(h)]
    ziel = 255 if dunkel else 0
    for _ in range(40):
        if dunkel and not _lum(c) < (0.36 if chip else 0.33):
            break
        if not dunkel and not _lum(c) > (0.125 if chip else 0.145):
            break
        c = [v + (ziel - v) * 0.06 for v in c]
    return _hx(c)


HELL = "#ffffff"
DUNKEL = "#1c1f2e"  # V.cd dunkel


def test_lesbar_nachbau_passt_zum_original(index_html):
    """Koeder: steht die Rechnung in index.html noch so, wie sie hier nachgebaut ist?"""
    assert ('for(let i=0;i<40&&(_dark?L(c)<(chip?0.36:0.33):L(c)>(chip?0.125:0.145));i++)'
            'c=c.map(v=>v+(ziel-v)*0.06);') in index_html


# ── 1 Planung ────────────────────────────────────────────────────────────

ROLLEN = ("#ef4444", "#3b82f6", "#22c55e", "#f97316")


def test_planung_namenschip_lesbar(index_html):
    assert 'background:m.c+"22",color:_lesbar(m.c,true)' in index_html
    assert 'background:m.c+"22",color:m.c,' not in index_html  # Umkehrprobe: der alte Wert
    assert ('const _wpRolleDesk=(rr)=>rr==="Störungstechniker"?"#ef4444":rr==="Techniker"?"#3b82f6":'
            'rr==="Monteur"?"#22c55e":"#f97316";') in index_html
    zelle_h = _mix("#009640", HELL, .04)
    zelle_d = _mix("#009640", DUNKEL, .08)
    for c in ROLLEN:
        assert _k(c, _mix(c, zelle_h, 0x22 / 255)) < 3.1, "Ausgangslage nicht mehr wie gemessen"
        assert _k(_lesbar(c, True), _mix(c, zelle_h, 0x22 / 255)) >= 4.5, c
        assert _k(_lesbar(c, True, True), _mix(c, zelle_d, 0x22 / 255)) >= 4.5, c


def test_planung_bemerkung_legende_fahrzeugkonflikt(index_html):
    assert 'color:r.bem?_lesbar("#d97706"):V.mt' in index_html
    assert _k(_lesbar("#d97706"), HELL) >= 4.5 and _k(_lesbar("#d97706", False, True), DUNKEL) >= 4.5
    assert "gap:5,fontWeight:700,color:_lesbar(f(k))}}" in index_html
    assert 'color:f.conflict?"#b91c1c":"#1d4ed8"' in index_html
    assert _k("#b91c1c", "#fee2e2") >= 4.5 and _k("#1d4ed8", "#dbeafe") >= 4.5


# ── 2 MA-Uebersicht ──────────────────────────────────────────────────────

def test_ma_uebersicht_rolle_lesbar(index_html):
    assert 'fontSize:UI.fMeta,color:_lesbar(roleC),fontWeight:600' in index_html
    for c in ("#22c55e", "#3b82f6", "#f97316"):
        assert _k(_lesbar(c), HELL) >= 4.5 and _k(_lesbar(c, False, True), DUNKEL) >= 4.5, c


# ── 3 AS-Kalender ────────────────────────────────────────────────────────

AS_STATUS_FARBEN = ("#eab308", "#84cc16", "#f97316", "#a3a3a3", "#3b82f6", "#22c55e", "#10b981", "#ef4444")


def test_as_kalender_chips(index_html):
    assert "color:_lesbar(_optionalChain([st, 'optionalAccess', _180 => _180.c])||\"#666\",true)" in index_html
    assert "color:_lesbar(_optionalChain([st, 'optionalAccess', _180b => _180b.c])||\"#666\",true)" in index_html
    assert "color:_lesbar(_optionalChain([st, 'optionalAccess', _181c => _181c.c])||\"#666\",true)}}, a.nummer)" in index_html
    m = re.search(r'we\?V\.weBg:"transparent",opacity:inM\?1:(\.\d+)', index_html)
    assert m, "Vormonats-Daempfung nicht gefunden"
    o = float(m.group(1))
    assert o < 1, "Vormonat soll gedaempft bleiben"
    for c in AS_STATUS_FARBEN:
        # aktueller Monat: >= 4,5
        assert _k(_lesbar(c, True), _mix(c, HELL, 24 / 255)) >= 4.5, c
        assert _k(_lesbar(c, True, True), _mix(c, DUNKEL, 24 / 255)) >= 4.5, c
        # Vormonat (ganze Zelle mit opacity o): >= 3
        for grund, dunkel in ((HELL, False), (DUNKEL, True)):
            t = _mix(_lesbar(c, True, dunkel), grund, o)
            g = _mix(_mix(c, grund, 24 / 255), grund, o)
            assert _k(t, g) >= 3, (c, dunkel, o, round(_k(t, g), 2))


def test_as_kalender_alte_daempfung_war_unlesbar():
    """Umkehrprobe: mit opacity .3 haelt kein Statusfarbe 3:1 - die Rechnung oben misst also wirklich."""
    t = _mix(_lesbar("#22c55e", True), HELL, .3)
    g = _mix(_mix("#22c55e", HELL, 24 / 255), HELL, .3)
    assert _k(t, g) < 3


# ── 4 / 5 Material + Werkzeuge ───────────────────────────────────────────

def test_material_pillen(index_html):
    assert 'background:p2.c+"18",color:_lesbar(p2.c,true)}}, _matIk("prio"' in index_html
    assert 'background:s.c+"18",color:_lesbar(s.c,true)}}, _matIk("status"' in index_html
    assert "color:prio===k?_lesbar(v.c,true):V.dm" in index_html
    creme = "#fffbeb"
    assert _k("#f59e0b", _mix("#f59e0b", creme, 24 / 255)) < 2.5  # wie gemessen (2,0)
    assert _k(_lesbar("#f59e0b", True), _mix("#f59e0b", creme, 24 / 255)) >= 4.5


def test_werkzeug_kalibrierung_lesbar(index_html):
    assert '{fontSize:UI.fMeta,color:_lesbar("#eab308"),fontWeight:700,marginTop:2}}, "Kalibrierung fällig" )' in index_html
    assert _k("#eab308", HELL) < 2  # gemessen 1,92
    assert _k(_lesbar("#eab308"), HELL) >= 4.5 and _k(_lesbar("#eab308", False, True), DUNKEL) >= 4.5


# ── 7 AS-Liste: Aktionen klebt rechts ────────────────────────────────────

def test_as_liste_aktionen_kleben_rechts(index_html):
    # Owner-Messung 1089: optionale Zeilentoenung tn, deckend ueber V.cd - ohne tn weiter genau V.cd (Pins nachgezogen)
    assert 'const _asAktKlebt=(tn)=>({position:"sticky",right:0,zIndex:1,background:tn?"linear-gradient("+tn+","+tn+"),"+V.cd:V.cd,' in index_html
    # Pin nachgezogen (AS Liste mittel, GF 19.11.2026 nach 1065): die Spalte
    # klebt weiter in der Stufe breit; am Tablet hochkant (mittel) deckte sie
    # BESTAETIGT zu und steht dort am Zeilenende im Rollkasten. Die Aufrufstellen
    # gehen deshalb ueber _asAktSpalte, das in breit genau _asAktKlebt liefert.
    assert 'const _asAktSpalte=(tn)=>(_asMittel?{}:_asAktKlebt(tn));' in index_html
    # Tablet-Runde 1077: Kopf in mittel deckend (_asKopfDeck)
    # 1089: Kopf ueber _asKopfKlebt deckend getoent (vorher weiss), Zelle mit Zeilentoenung der stornierten Zeile
    assert '{...thS(),..._asKopfDeck(),width:110,textAlign:"center",..._asKopfKlebt(_asAktSpalte())}}, "Aktionen")' in index_html
    assert '{...tdSt(),textAlign:"center",padding:"4px 2px",..._asAktSpalte(isSt?_AS_ST_TON:null)}}' in index_html
    # die Schreibwege der Zeile sind unberuehrt
    assert "openEdit(a);}, style: {...bpS,border:\"none\",borderRadius:4" in index_html


# ── 8 / 9 Buero-Portal + Mitarbeiter ─────────────────────────────────────

def test_buero_tank_attest_fs(index_html):
    assert 'color:_okG("#22c55e"),fontSize:12,fontWeight:700}},"\\u2713 alle kontrolliert")' in index_html
    assert 'color:"#22c55e",fontSize:12,fontWeight:700}},"\\u2713 alle kontrolliert")' not in index_html
    assert 'background:COLORS.WARNING+"22",color:_lesbar(COLORS.WARNING,true)' in index_html
    assert 'color:_lesbar(b.hasAtt?"#16a34a":COLORS.ERROR,true)}},b.hasAtt?"Attest vorhanden":"Attest fehlt")' in index_html
    assert 'color:_lesbar(COLORS.INFO,true),fontSize:UI.fMeta,fontWeight:700}}, k.trim())' in index_html
    assert _k("#006e30", HELL) >= 4.5  # _okG hell = EP_GREEN_DARK
    rosa = "#fee2e2"
    for c in ("#16a34a", "#ef4444"):
        assert _k(_lesbar(c, True), rosa) >= 4.5, c
    assert _k(_lesbar("#3b82f6", True), _mix("#3b82f6", HELL, .1)) >= 4.5
    assert _k(_lesbar("#f97316", True), _mix("#f97316", HELL, 0x22 / 255)) >= 4.5


# ── 10 Rest Urlaub ───────────────────────────────────────────────────────

def test_buero_resturlaub_negativ_rot(index_html):
    regel = '(typeof r.rest==="number"&&r.rest<0)?UI.fehler:UI.markeTxt'
    assert index_html.count(regel) == 2, "Karte und Tabelle"
    # dieselbe Regel wie die Urlaub-Kachel
    assert 'color:(typeof rest==="number"&&rest<0)?UI.fehler:UI.markeTxt' in index_html
    # Umkehrprobe: kein festes Gruen mehr am Rest
    assert '_okG("#22c55e")}},_projStdDE(r.rest,1))' not in index_html
    assert '_okG("#22c55e"),fontSize:15}},_projStdDE(r.rest,1))' not in index_html


# ── 11 Werkzeugwert ──────────────────────────────────────────────────────

def test_werkzeug_wert_ehrlich(index_html):
    assert "const totalWert=_react.useMemo.call(void 0, ()=>werkzeuge.reduce((s,w)=>s+(w.wert||0),0),[werkzeuge]);" in index_html
    assert ('(w.wert>0)?w.wert.toLocaleString("de-AT"):React.createElement(\'span\', '
            '{ style: {color:V.dm,fontWeight:400}, title: "Kein Wert erfasst"}, "—")') in index_html
    assert "fontFamily:mono,fontWeight:600}}, (w.wert||0).toLocaleString(\"de-AT\"))" not in index_html
    assert '" ("+_n+" bewertet)"' in index_html


# ── 12 Diagramm nach Art ─────────────────────────────────────────────────

def test_auftragsart_farben_verschieden(index_html):
    m = re.search(r"const _AS_ART_FARBE=\{([^}]+)\}", index_html)
    assert m
    farben = dict(re.findall(r'([a-z]+):"(#[0-9a-f]{6})"', m.group(1)))
    art = re.search(r"const AS_ART=\{(.+?)\};", index_html).group(1)
    schluessel = re.findall(r"([a-z]+):\{l:", art)
    assert set(schluessel) == set(farben), (schluessel, farben)
    assert len(set(farben.values())) == len(farben), "zwei Arten teilen eine Farbe"
    assert "c:_AS_ART_FARBE[k]||\"#6b7280\"" in index_html
    werte = list(farben.values())
    for i in range(len(werte)):
        for j in range(i + 1, len(werte)):
            a, b = _rgb(werte[i]), _rgb(werte[j])
            d = sum((a[n] - b[n]) ** 2 for n in range(3)) ** .5
            assert d > 60, (werte[i], werte[j], d)
    assert ':"#22c55e"})),[arbeitsscheine]);' not in index_html  # Umkehrprobe: kein Sammel-Gruen


# ── 13 Emoji -> Linien-Ikonen ────────────────────────────────────────────

@pytest.mark.parametrize("neu", [
    'telefon:["M13.832 16.568',
    'euro:["M4 10h12","M4 14h9",',
    '_dpIkTxt("⏰",_morgenOhneZeit+" am "+_morgenLabel+" ohne Zeit"))',
    'color:_lesbar(COLORS.INFO),border:"1px solid "+COLORS.INFO',
    'textDecoration:"none"}},_zpIkI("telefon"),o.tel)',
    '(o.meta?" · ":""),o.meta?_dpMetaIk(o.meta):null)',
    'function _dpMetaIk(t){',
    '_ikVw("personen","Monteur-\\u00dcbersicht (alle Daten)"))',
    '"Klick auf die Zeile oder den Knopf ",_zpIkI("stift")," \\u00f6ffnet die Zeiteintr\\u00e4ge des Monteurs je Kalenderwoche',  # Paket 14 (GF 24.11.2026): KW-Auswahl statt letzte 50 - Text nachgezogen | v3.9.1109 GF: Hinweis angepasst; vorher "Der Knopf ",_zpIkI("stift"),"öffnet ...
    '_ik("stift",16))',
    '_ikVw("kalender","KW-Filter"))',
    '_ikVw("kalender","Abwesenheiten "+_abYr))',
    '_ikVw("fieber","Krankenstand "+_abYr))',
    '_zpIk("hochladen","AU hochladen",14))',
    "_ikVw('euro','Entfernungszulage'))",
    # Paket 15 Nachbau: der Knopf steht jetzt als Konstante _pzeKnopf (Monatszeile ODER Export-Leiste) - die dritte
    # Klammer schloss vorher die Monatszeile; alter Wert: "_zpIk('dokument','PZE-PDF (Lohnverrechner)')))"
    "_zpIk('dokument','PZE-PDF (Lohnverrechner)'));",
    "_zpIk('regler','Zulagensätze bearbeiten',14),_klappIk(_ezRateEdit,14))",  # v3.9.1050: ▼ -> Linien-Chevron
    "justifyContent:'center'}},_ik('links',18))",
    "justifyContent:'center'}},_ik('rechts',18))",
    "_zpIk('links','Monat',16))",
    "'Monat',_ik('rechts',16)))",
])
def test_linien_ikonen(index_html, neu):
    assert neu in index_html


@pytest.mark.parametrize("alt", [
    '"☎ "+o.tel', '},"⏰ "+_morgenOhneZeit', '"\\ud83d\\udc65 Monteur-', '"\\ud83d\\udca1 \\u270f',
    '}, "\\u270f\\ufe0f")', '"\\ud83d\\udcc5 Abwesenheiten', '"\\ud83e\\udd12 Krankenstand',
    '"\\u2b06\\ufe0f AU hochladen"', "'💶 Entfernungszulage'", "'📄 PZE-PDF", "'⚙ Zulagensätze",
    "'‹ Monat'", "'Monat ›'", "minHeight:isMob?38:0}},'‹')", "minHeight:isMob?38:0}},'›')",
])
def test_emoji_weg(index_html, alt):
    assert alt not in index_html


def test_dispo_meta_ikone_verzweigt_richtig(node_exe, index_html, tmp_path):
    """_dpMetaIk ausgefuehrt: ⚡/🏗 werden Ikone + Rest, alles andere bleibt Text."""
    import subprocess
    a = index_html.index("function _dpMetaIk(t){")
    fn = index_html[a:index_html.index("\n", a)]
    js = ("var React={Fragment:'F',createElement:function(){return Array.prototype.slice.call(arguments);}};"
          "function _zpIkI(n){return 'IK:'+n;}" + fn +
          "console.log(JSON.stringify([_dpMetaIk('⚡ Störungsdienst · dringend'),_dpMetaIk('vor 🏗 BVH X · hohe Prio'),_dpMetaIk('12 km')]));")
    p = tmp_path / "m.js"
    p.write_text(js, encoding="utf-8")
    out = subprocess.run([node_exe, str(p)], capture_output=True, text=True, encoding="utf-8", timeout=60)
    assert out.returncode == 0, out.stderr
    import json
    r = json.loads(out.stdout)
    assert r[0] == ["F", None, "IK:blitz", "Störungsdienst · dringend"]
    assert r[1] == ["F", None, "vor ", "IK:helm", "BVH X · hohe Prio"]
    assert r[2] == "12 km"


def test_offa_excel_unberuehrt(index_html):
    assert '"EXCEL Export"' in index_html  # GF 24.11.2026: Beschriftung 'OFFA Excel' -> 'EXCEL Export' (nur Text; Export, Spalten, Format unveraendert); vorher "OFFA Excel"


# ── 14 Dispo-Sperrknopf ──────────────────────────────────────────────────

def test_sperrknopf_ueberdeckt_keine_kachel(index_html):
    # AS Hochformat (GF 19.11.2026): die alte Rechnung 28 >= 2 + 24 war gruen, am Tablet lag der Knopf
    # trotzdem ueber der Karte - die Hausregel (pointer coarse) macht JEDEN Knopf 44 hoch. Jetzt je
    # Zweig: grob (Touch) Streifen 48 gegen Knopf 44, fein (Maus) 28 gegen 24.
    m = re.search(r"paddingTop:_hasToggle\?\(_dpGrob\?(\d+):(\d+)\):4", index_html)
    assert m
    knopf = re.search(r"style:\{position:\"absolute\",top:(\d+),right:8,zIndex:3,.*?minHeight:_dpGrob\?(\d+):(\d+),", index_html)
    assert knopf
    top = int(knopf.group(1))
    assert int(m.group(1)) >= top + int(knopf.group(2)), "Kopfstreifen (Touch) kleiner als der Knopf"
    assert int(m.group(2)) >= top + int(knopf.group(3)), "Kopfstreifen (Maus) kleiner als der Knopf"
    assert int(knopf.group(2)) >= 44, "Touch-Knopf unter 44 px"
    assert '"(pointer: coarse), (max-width: 768px)"' in index_html, "_dpGrob folgt nicht der Hausregel"


# ── 15 Projektakte-Kopf ──────────────────────────────────────────────────

def test_projektakte_kopf_name_vorrang(index_html):
    assert ('{ title: p.name, style: {fontSize:13,fontWeight:600,overflow:"hidden",textOverflow:"ellipsis",..._zweiZeilen,'
            'minWidth:0,flex:"0 1 auto",lineHeight:1.2,display:isMob?"none":"-webkit-box",'
            '...(!isMob&&ww<1200?{flex:"1 1 0%"}:{})}}, p.name)') in index_html  # Scan 1051 (v1053): unter 1200 Grundbreite 0, Kunde/Ort in eigener Zeile
    assert 'className: "topbar-detail", title: (p.kunde||"")+" · "+(p.ort||""), style: {fontSize:12,color:V.dm,flex:"0 100 auto",minWidth:0,overflow:"hidden",...(!isMob&&ww<1200?{flexBasis:"100%"}:{})}}' in index_html
    # kein Inline-display am Detail - sonst ueberstimmt es die Regel .topbar-detail{display:none} unter 600 px
    a = index_html.index('className: "topbar-detail", title:')
    assert "display" not in index_html[a:a + 200]


# ── 16 Balkenbeschriftungen ──────────────────────────────────────────────

def test_balkenbeschriftung_passt_in_den_platz(index_html):
    assert ("const maxL=Math.max(4,Math.min(many?10:8,Math.floor((many?2:1)*(bw+6)/(UI.fMeta*0.62))));"
            in index_html)
    assert "Math.min(140,longestLabel*8+10)" in index_html  # D8-Schranke unberuehrt
    fmeta = 12
    for n in range(1, 25):
        many = n > 6
        bw = max(18, min(36, 260 / n)) if many else min(40, (280 // n))
        maxl = max(4, min(10 if many else 8, int(((2 if many else 1) * (bw + 6)) // (fmeta * 0.62))))
        breite = (maxl + 1) * fmeta * 0.62  # + Auslassungszeichen
        platz = (2 if many else 1) * (bw + 6)
        if maxl > 4:
            assert breite <= platz + fmeta * 0.62, (n, maxl, breite, platz)


# ── 17 letzter Sync nach Neuladen ────────────────────────────────────────

def test_kopf_sync_liest_gespeicherten_zeitpunkt(index_html):
    assert 'const ts=typeof window!=="undefined"&&(window._lastJuprowaSyncAt||_jpLetzterAbrufMs());' in index_html
    assert 'const ts=typeof window!=="undefined"&&window._lastJuprowaSyncAt;' not in index_html
    assert 'localStorage.setItem("epk_last_juprowa_pull",String(_jpms))' in index_html
    assert 'function _jpLetzterAbrufMs(){' in index_html
