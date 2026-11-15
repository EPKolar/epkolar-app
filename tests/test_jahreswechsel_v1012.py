# -*- coding: utf-8 -*-
"""v3.9.1012 Jahreswechsel - KW-Navigation ueber die Jahresgrenze (KW 53/2026 -> KW 1/2027).

Befund: docs/befunde/bughunt/z2_jahreswechsel.md (+ zeit.md Z1). Bis v3.9.1011 war das Jahr in
WeekPlan und ZeiterfassungView `const yr=isoWY()` - bei jedem Render neu, nie Zustand - und jede
KW-Leiste klemmte gegen das LAUFENDE Jahr. Folgen:
  * in KW 53/2026 war "Woche vor" tot - KW 1/2027 liess sich im Dezember nicht vorplanen
    (Frist Dispo: Mitte Dezember);
  * ab Mo 04.01.2027 war KW 53/2026 nicht mehr erreichbar (Klemme bei 1);
  * ein ueber den 04.01.2027 offener Tab stand auf kw=53 + yr=2027 - eine Woche, die es nicht gibt;
  * der jahrlose Rueckfall wpHistory[kw] konnte eine Woche aus einem anderen Jahr zeigen.

Gemessen wird WIRKUNG: die echten Zeilen werden aus index.html geschnitten und in node mit
gefaelschtem Datum ausgefuehrt. Quelltext-Riegel laufen auf kommentarfreiem Text (die
Kur-Kommentare zitieren die alten Formen). Jede Gruppe hat eine Umkehrprobe.
"""
import json
import re

from conftest import run_node_snippet


# ── Hilfen ────────────────────────────────────────────────────────────────────

def _ohne_kommentare(s):
    s = re.sub(r"/\*.*?\*/", "", s, flags=re.S)
    return re.sub(r"(?m)^\s*//[^\n]*", "", s)


def _zeile(html, kopf):
    m = re.search(r"(?m)^" + re.escape(kopf) + r".*$", html)
    assert m, "Zeile nicht gefunden: " + kopf
    return m.group(0)


def _helfer(html):
    return "\n".join(_zeile(html, k) for k in (
        "const isoW=", "const isoWY=", "const _getMaxKW=", "const _kwZiel=",
        "const isoWof=", "const isoWYof="))


FAKE_DATE = (
    "const _RD=Date;globalThis.__NOW=0;"
    "class _FD extends _RD{constructor(...a){if(a.length===0){super(globalThis.__NOW);}else{super(...a);}}"
    "static now(){return globalThis.__NOW;}}"
    "globalThis.Date=_FD;"
    "const _setNow=(s)=>{globalThis.__NOW=new _RD(s).getTime();};"
)


def _node(node_exe, html, body):
    return json.loads(run_node_snippet(node_exe, FAKE_DATE + _helfer(html) + "\n" + body))


def _bauteil(html, kopf, ende):
    a = html.find(kopf)
    assert a != -1, "Bauteil fehlt: " + kopf
    e = html.find(ende, a + len(kopf))
    assert e > a, "Bauteil-Ende fehlt: " + ende
    return html[a:e]


def _weekplan(html):
    return _bauteil(html, "function WeekPlan({", "\nfunction ")


def _ze(html):
    return _bauteil(html, "function ZeiterfassungView({", "\nfunction ")


def _vzeit(html):
    return _bauteil(html, "function VZeit({", "\nfunction ")


# ── 1. Die eine Rechenregel: _kwZiel ─────────────────────────────────────────

def test_kwziel_kanten(node_exe, index_html):
    r = _node(node_exe, index_html, (
        "process.stdout.write(JSON.stringify({"
        "max26:_getMaxKW(2026),max27:_getMaxKW(2027),"
        "vor_53_26:_kwZiel(2026,54),"
        "zurueck_1_27:_kwZiel(2027,0),"
        "vor_52_27:_kwZiel(2027,53),"
        "zurueck_1_28:_kwZiel(2028,0),"
        "mitte:_kwZiel(2026,30),"
        "ziel_27_53:_kwZiel(2026,53,2027),"
        "ziel_26_53:_kwZiel(2027,53,2026),"
        "ziel_27_1:_kwZiel(2026,1,2027)}));"))
    assert r["max26"] == 53 and r["max27"] == 52
    assert r["vor_53_26"] == [2027, 1], "Vor von KW 53/2026 muss KW 1/2027 sein: %r" % r
    assert r["zurueck_1_27"] == [2026, 53], "Zurueck von KW 1/2027 muss KW 53/2026 sein: %r" % r
    assert r["vor_52_27"] == [2028, 1], "2027 hat nur 52 Wochen - nach KW 52 kommt KW 1/2028: %r" % r
    assert r["zurueck_1_28"] == [2027, 52], "Zurueck von KW 1/2028 ist KW 52/2027, nicht 53: %r" % r
    assert r["mitte"] == [2026, 30]
    assert r["ziel_27_53"] == [2027, 52], "Ausdrueckliches Zieljahr 2027 darf KW 53 nicht stehenlassen"
    assert r["ziel_26_53"] == [2026, 53]
    assert r["ziel_27_1"] == [2027, 1]


SWEEP = (
    "const tot={neu:0,alt:0,falsch:0};"
    "const altVor=(y,k)=>[y,Math.max(1,Math.min(_getMaxKW(y),k+1))];"
    "const altZur=(y,k)=>[y,Math.max(1,Math.min(_getMaxKW(y),k-1))];"
    "for(let d=new _RD(2020,0,1);d<=new _RD(2035,11,31);d.setDate(d.getDate()+1)){"
    " const y=isoWYof(d),k=isoWof(d);"
    " const n=new _RD(d);n.setDate(n.getDate()+7);const p=new _RD(d);p.setDate(p.getDate()-7);"
    " const sn=[isoWYof(n),isoWof(n)],sp=[isoWYof(p),isoWof(p)];"
    " const v=_kwZiel(y,k+1),z=_kwZiel(y,k-1);"
    " if(v[0]===y&&v[1]===k)tot.neu++;if(z[0]===y&&z[1]===k)tot.neu++;"
    " if(v[0]!==sn[0]||v[1]!==sn[1])tot.falsch++;if(z[0]!==sp[0]||z[1]!==sp[1])tot.falsch++;"
    " const av=altVor(y,k),az=altZur(y,k);"
    " if(av[1]===k)tot.alt++;if(az[1]===k)tot.alt++;"
    "}"
    "process.stdout.write(JSON.stringify(tot));"
)


def test_sweep_2020_2035_keine_toten_navigationstage(node_exe, index_html):
    """Vor/Zurueck muss fuer JEDEN Tag 2020-2035 genau die ISO-Woche +-7 Tage treffen."""
    r = _node(node_exe, index_html, SWEEP)
    assert r["neu"] == 0, "%d tote Navigationstage mit _kwZiel" % r["neu"]
    assert r["falsch"] == 0, "%d Schritte landen nicht in der ISO-Woche +-7 Tage" % r["falsch"]
    # Umkehrprobe: die ALTE Klemme gegen das laufende Jahr muss die 223 Tage des Befunds liefern.
    assert r["alt"] == 223, "Koeder: die alte Klemme muesste 223 tote Tage zeigen, misst %d" % r["alt"]


# ── 2. WeekPlan: switchKw (echter Rumpf) ─────────────────────────────────────

def _wp_switch_snippet(html, start_yr, start_kw, aufruf, now="2026-12-28T10:00:00"):
    wp = _weekplan(html)
    m = re.search(r"\n  const switchKw=\(newKw,newYr\)=>\{\n.*?\n  \};\n", wp, re.S)
    assert m, "WeekPlan-switchKw (newKw,newYr) nicht gefunden"
    sw = m.group(0)
    wpkey = _zeile(wp, "  const _wpKey=")
    getY = _zeile(wp, "  const _wpGetY=")
    return (
        "_setNow('" + now + "');"
        "let wpHistory={'2026-53':[{id:'a53'}],'2027-1':[{id:'b1'}],'2026-1':[{id:'c1'}],'1':[{id:'legacy1'}],'53':[{id:'legacy53'}]};"
        "let yr=" + str(start_yr) + ",kw=" + str(start_kw) + ";let rows=[{id:'aktiv'}];"
        "const out={};const setKw=v=>{out.kw=v;};const setYr=v=>{out.yr=v;};const setRows=v=>{out.rows=v.map(r=>r.id);};"
        "const setWpHistory=f=>{const h=f(wpHistory);out.abgelegt=Object.keys(h).filter(k=>h[k]===rows);};"
        "const wpSaveTimer={current:null};const saveDirty=()=>{};const wpInitRef={current:false};"
        "const padWpRows=x=>x;const migrateRows=x=>x;const _isPaddingRow=()=>false;"
        "const _wpLastSaved={current:null};const _wpDirtyIds={current:new Set()};const _wpDeletedIds={current:new Set()};"
        "const setCellPick=()=>{};const setSelCells=()=>{};const dragRef={current:null};"
        + wpkey + "\n" + getY + "\n" + sw +
        aufruf + ";process.stdout.write(JSON.stringify(out));"
    )


def test_weekplan_vor_von_2026_53_nach_2027_1(node_exe, index_html):
    r = _node(node_exe, index_html, _wp_switch_snippet(index_html, 2026, 53, "switchKw(kw+1)"))
    assert (r["yr"], r["kw"]) == (2027, 1), r
    assert r["rows"] == ["b1"], "Zeilen der Zielwoche muessen aus 2027-1 kommen: %r" % r
    assert r["abgelegt"] == ["2026-53"], "die abgehende Woche gehoert unter 2026-53: %r" % r


def test_weekplan_zurueck_von_2027_1_nach_2026_53(node_exe, index_html):
    r = _node(node_exe, index_html, _wp_switch_snippet(index_html, 2027, 1, "switchKw(kw-1)",
                                                       now="2027-01-05T10:00:00"))
    assert (r["yr"], r["kw"]) == (2026, 53), r
    assert r["rows"] == ["a53"], r
    assert r["abgelegt"] == ["2027-1"], r


def test_weekplan_2027_hat_nur_52_wochen(node_exe, index_html):
    r = _node(node_exe, index_html, _wp_switch_snippet(index_html, 2027, 52, "switchKw(kw+1)",
                                                       now="2027-12-27T10:00:00"))
    assert (r["yr"], r["kw"]) == (2028, 1), r
    r = _node(node_exe, index_html, _wp_switch_snippet(index_html, 2027, 1, "switchKw(53,2027)",
                                                       now="2027-01-05T10:00:00"))
    assert (r["yr"], r["kw"]) == (2027, 52), r


def test_weekplan_kein_jahrloser_rueckfall_im_fremden_jahr(node_exe, index_html):
    """2027-1 leer + jahrloser Eintrag '1' vorhanden: im Dezember 2026 darf der Sprung nach
    2027-1 NICHT den jahrlosen Eintrag zeigen (der gehoert zum laufenden Jahr 2026)."""
    snip = _wp_switch_snippet(index_html, 2026, 53, "delete wpHistory['2027-1'];switchKw(kw+1)")
    r = _node(node_exe, index_html, snip)
    assert (r["yr"], r["kw"]) == (2027, 1)
    assert r["rows"] == [], "Fremdjahr-Rueckfall: %r" % r
    # Gegenprobe: im laufenden Jahr bleibt der Rueckfall wie bisher (heutige Daten unveraendert)
    snip = _wp_switch_snippet(index_html, 2026, 2, "delete wpHistory['2026-1'];switchKw(kw-1)",
                              now="2026-01-14T10:00:00")
    r = _node(node_exe, index_html, snip)
    assert (r["yr"], r["kw"]) == (2026, 1)
    assert r["rows"] == ["legacy1"], "der Altbestands-Rueckfall im laufenden Jahr ist weg: %r" % r


def test_weekplan_umschalter_rueckweg_mit_jahr(node_exe, index_html):
    r = _node(node_exe, index_html, _wp_switch_snippet(index_html, 2027, 1, "switchKw(53,2026)"))
    assert (r["yr"], r["kw"]) == (2026, 53), r


# ── 3. Offener Tab ueber Mo 04.01.2027 (echte Kopfzeilen, Hook-Attrappe) ─────

def _tab_snippet(kopfzeilen):
    return (
        "const _store=[];let _i=0;"
        "const _react={useState:{call:(_t,init)=>{const j=_i++;if(!(j in _store))_store[j]=init;"
        "return [_store[j],v=>{_store[j]=v;}];}}};"
        "const render=(s)=>{_setNow(s);_i=0;" + kopfzeilen +
        "return {curKw,curYr:(typeof curYr!=='undefined'?curYr:null),yr,kw,max:_getMaxKW(yr)};};"
        "const a=render('2026-12-31T16:00:00');const b=render('2027-01-04T07:30:00');"
        "process.stdout.write(JSON.stringify({a,b}));"
    )


def test_offener_tab_ueber_den_jahreswechsel(node_exe, index_html):
    for name, teil in (("WeekPlan", _weekplan(index_html)), ("ZeiterfassungView", _ze(index_html))):
        kopf = _zeile(teil, "  const curKw=isoW();")
        kwz = "const [kw,setKw]=_react.useState.call(void 0, curKw);"
        assert kwz in teil, name
        r = _node(node_exe, index_html, _tab_snippet(kopf + "\n" + kwz))
        assert (r["a"]["yr"], r["a"]["kw"]) == (2026, 53), (name, r)
        b = r["b"]
        assert (b["curYr"], b["curKw"]) == (2027, 1), (name, r)
        assert (b["yr"], b["kw"]) == (2026, 53), (
            "%s: der offene Tab muss auf der gueltigen Woche 2026-53 bleiben, nicht auf %r" % (name, b))
        assert b["kw"] <= b["max"], "%s: KW %d gibt es in %d nicht" % (name, b["kw"], b["yr"])


def test_umkehrprobe_alte_kopfzeile_landet_auf_2027_53(node_exe, index_html):
    alt = "const curKw=isoW();const yr=isoWY();\nconst [kw,setKw]=_react.useState.call(void 0, curKw);"
    r = _node(node_exe, index_html, _tab_snippet(alt))
    assert (r["b"]["yr"], r["b"]["kw"]) == (2027, 53), (
        "Koeder: die alte Form muesste den Tab auf 2027-53 stellen - sonst misst der Test nichts: %r" % r)
    assert r["b"]["kw"] > r["b"]["max"]


# ── 4. ZeiterfassungView: switchKw (echte Zeile) ─────────────────────────────

def _ze_switch(node_exe, html, yr, kw, aufruf):
    zeile = _zeile(_ze(html), "  const switchKw=(newKw,newYr)=>")
    return _node(node_exe, html, (
        "let yr=%d,kw=%d;const out={};const setKw=v=>{out.kw=v;};const setYr=v=>{out.yr=v;};" % (yr, kw)
        + zeile + "\n" + aufruf + ";process.stdout.write(JSON.stringify(out));"))


def test_ze_navigation_ueber_die_jahresgrenze(node_exe, index_html):
    assert _ze_switch(node_exe, index_html, 2026, 53, "switchKw(kw+1)") == {"yr": 2027, "kw": 1}
    assert _ze_switch(node_exe, index_html, 2027, 1, "switchKw(kw-1)") == {"yr": 2026, "kw": 53}
    assert _ze_switch(node_exe, index_html, 2027, 52, "switchKw(kw+1)") == {"yr": 2028, "kw": 1}
    assert _ze_switch(node_exe, index_html, 2026, 53, "switchKw(1,2027)") == {"yr": 2027, "kw": 1}


# ── 5. Projekt-Zeiterfassung (VZeit): Montag der gewaehlten Woche ────────────

def test_vzeit_montag_im_gewaehlten_jahr(node_exe, index_html):
    v = _vzeit(index_html)
    km = _zeile(v, "  const kwMon=")
    body = re.search(r"\(\)=>\{(.*?)return d;\}", km).group(1)
    r = _node(node_exe, index_html, (
        "const f=(calYr,calKw)=>{" + body + "return d.getFullYear()+'-'+(d.getMonth()+1)+'-'+d.getDate();};"
        "process.stdout.write(JSON.stringify([f(2026,53),f(2027,1),f(2027,52)]));"))
    assert r == ["2026-12-28", "2027-1-4", "2027-12-27"], r


# ── 6. Kiosk-Tafel: jahrloser Rueckfall nur im laufenden ISO-Jahr ─────────────

def test_kiosk_kein_fremdjahr(node_exe, index_html):
    tafel = _bauteil(index_html, "function WochenplanTafel(", "\nfunction ")
    zeile = _zeile(tafel, "  const rows=(wpHistory[yr+'-'+kw]")
    ausdruck = re.search(r"const rows=(\(.*?\|\|\[\]\))", zeile).group(1)
    r = _node(node_exe, index_html, (
        "const wpHistory={'1':[{id:'legacy1'}],'47':[{id:'legacy47'}]};"
        "const f=(now,yr,kw)=>{_setNow(now);return " + ausdruck + ".map(x=>x.id);};"
        "process.stdout.write(JSON.stringify({"
        "neujahr:f('2027-01-01T10:00:00',2027,1),"
        "november:f('2026-11-20T10:00:00',2026,47)}));"))
    assert r["neujahr"] == [], "Tafel zeigt am 01.01.2027 einen jahrlosen Eintrag: %r" % r
    assert r["november"] == ["legacy47"], "Rueckfall im laufenden Jahr ist weg (heutige Daten!): %r" % r


# ── 7. Quelltext-Riegel je Ansicht (kommentarfrei) + Umkehrproben ─────────────

def _riegel(html):
    fehler = []
    wp = _ohne_kommentare(_weekplan(html))
    ze = _ohne_kommentare(_ze(html))
    vz = _ohne_kommentare(_vzeit(html))
    if "const [yr,setYr]=_react.useState.call(void 0, curYr);" not in wp:
        fehler.append("WP: yr ist kein Zustand")
    if "const yr=isoWY()" in wp:
        fehler.append("WP: yr wieder Konstante")
    if "setYr(_tYr)" not in wp:
        fehler.append("WP: switchKw setzt das Jahr nicht")
    if "_wpGetY(_tYr,newKw)" not in wp:
        fehler.append("WP: Zielzeilen nicht aus dem Zieljahr")
    if "},[wpHistory,kw,yr]);" not in wp:
        fehler.append("WP: Nachlade-Effekt hoert nicht auf yr")
    if "year:yr,week:kw" not in wp:
        fehler.append("WP: Upsert schreibt year/week nicht aus dem Zustand")
    for alt in ("switchKw(Math.max(1,kw-1))", "switchKw(Math.min(_getMaxKW(yr),kw+1))",
                "kw===curKw&&React.createElement(Badge", "kw>curKw&&", "kw<curKw&&"):
        if alt in wp:
            fehler.append("WP: alte Form zurueck: " + alt)
    if "const _wpIstAktuell=(kw===curKw&&yr===curYr);" not in wp:
        fehler.append("WP: Aktuell vergleicht nicht (Jahr,KW)")
    if "switchKw(curKw,curYr)" not in wp:
        fehler.append("WP: Rueckweg ohne Jahr")
    if "const [yr,setYr]=_react.useState.call(void 0, curYr);" not in ze:
        fehler.append("ZE: yr ist kein Zustand")
    if "const yr=isoWY()" in ze:
        fehler.append("ZE: yr wieder Konstante")
    if "_kwZiel(yr,newKw,newYr)" not in ze:
        fehler.append("ZE: switchKw rollt nicht")
    if "(kw===curKw&&yr===curYr)&&React.createElement(Badge" not in ze:
        fehler.append("ZE: Aktuell vergleicht nicht (Jahr,KW)")
    if "(kw!==curKw||yr!==curYr)&&React.createElement('button',{onClick:()=>switchKw(curKw,curYr)," not in ze:
        fehler.append("ZE: Heute-Knopf ohne Jahr")
    if "const [calYr,setCalYr]=_react.useState.call(void 0, isoWY());" not in vz:
        fehler.append("VZeit: kein Jahr-Zustand")
    if "new Date(calYr,0,4)" not in vz or "[calKw,calYr]" not in vz:
        fehler.append("VZeit: kwMon rechnet nicht im gewaehlten Jahr")
    if "_kwZiel(calYr,calKw-1)" not in vz or "_kwZiel(calYr,calKw+1)" not in vz:
        fehler.append("VZeit: Pfeile rollen nicht")
    if "Math.min(_getMaxKW(isoWY()),k+1)" in vz or "Math.max(1,k-1)" in vz:
        fehler.append("VZeit: alte Klemme zurueck")
    if "(calKw===isoW()&&calYr===isoWY())" not in vz:
        fehler.append("VZeit: Aktuell vergleicht nicht (Jahr,KW)")
    return fehler


def test_quelltext_riegel(index_html):
    f = _riegel(index_html)
    assert not f, "\n".join(f)


UMKEHR = [
    ("setKw(newKw);setYr(_tYr);", "setKw(newKw);"),
    ("},[wpHistory,kw,yr]);", "},[wpHistory,kw]);"),
    ("const _newRows=padWpRows(migrateRows(_wpGetY(_tYr,newKw)||[]));",
     "const _newRows=padWpRows(migrateRows(_wpGet(newKw)||[]));"),
    ("onClick: ()=>switchKw(kw+1)", "onClick: ()=>switchKw(Math.min(_getMaxKW(yr),kw+1))"),
    ("const _wpIstAktuell=(kw===curKw&&yr===curYr);", "const _wpIstAktuell=(kw===curKw);"),
    ("const switchKw=(newKw,newYr)=>{const _z=_kwZiel(yr,newKw,newYr);",
     "const switchKw=(newKw,newYr)=>{const _z=[yr,Math.max(1,Math.min(_getMaxKW(yr),newKw))];"),
    ("(kw!==curKw||yr!==curYr)&&React.createElement('button',{onClick:()=>switchKw(curKw,curYr),",
     "kw!==curKw&&React.createElement('button',{onClick:()=>switchKw(curKw),"),
    ("new Date(calYr,0,4)", "new Date(yr,0,4)"),
    ("_kwZiel(calYr,calKw+1)", "_kwZiel(isoWY(),calKw+1)"),
]


def test_umkehrproben_riegel_schlagen_an(index_html):
    assert not _riegel(index_html)
    for neu, alt in UMKEHR:
        assert neu in index_html, "Umkehrprobe: Anker fehlt: " + neu
        mut = index_html.replace(neu, alt, 1)
        assert _riegel(mut), "Umkehrprobe stumm - Rueckbau bleibt gruen: " + neu


def test_umkehrprobe_kwziel_rollt_nicht(node_exe, index_html):
    """Wird _kwZiel zur alten Klemme zurueckgebaut, muss der Sweep rot werden."""
    zeile = _zeile(index_html, "const _kwZiel=")
    koeder = "const _kwZiel=(y,k,ny)=>[y,Math.max(1,Math.min(_getMaxKW(y),k))];"
    mut = index_html.replace(zeile, koeder, 1)
    r = _node(node_exe, mut, SWEEP)
    assert r["neu"] == 223 and r["falsch"] > 0, "Koeder: Sweep misst nichts: %r" % r
