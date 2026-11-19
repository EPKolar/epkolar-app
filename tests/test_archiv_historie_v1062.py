# -*- coding: utf-8 -*-
"""v3.9.1062 - Fahrzeug-Archiv und Historie / Werkzeug-Selbstausleihe ohne "letzter gewinnt".

Teil 1: Seit 1060 reichte die Wurzel allen Ansichten nur nicht archivierte Fahrzeuge (fahrzeugeAktiv) -
auch Auswertung, Bueroexport (Tank-Kontrolle), Chef-/Home-Kostensummen, Fahrtenbuch und Wochenplan-
Historie. Sobald ein Fahrzeug archiviert wird, verloren vergangene Zeitraeume seine Tank-/km-Kosten.
Jetzt: Historie/Auswertung ueber die VOLLE Liste (archivierte markiert), Arbeitsansichten bleiben aktiv.

Teil 2: wzSelfOut schrieb unbedingt (PUT) - zwei Geraete konnten dasselbe Werkzeug ausleihen, der
spaetere gewann still. Jetzt bedingter PATCH (status=eq.verfuegbar), ehrliche Meldung bei 0 Zeilen,
offline mit Marke, die beim Abgleich den Konflikt erkennt statt zu ueberschreiben.

Gemessen wird mit Node am ECHTEN Code, aus index.html geschnitten (Zaehl-Assert je Anker), und an der
ECHTEN Verdrahtung der Wurzel (der Ausdruck hinter "fahrzeuge:" wird gelesen, nicht abgeschrieben).
Jede Zusicherung hat eine Umkehrprobe: mit der alten Verdrahtung / ohne Bedingung schlaegt sie an.
"""
import io
import json
import re
import subprocess
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]
INDEX = WURZEL / "index.html"


def _q():
    return io.open(INDEX, encoding="utf-8", newline="").read()


def _einmal(q, a):
    assert q.count(a) == 1, "Anker %d-mal: %r" % (q.count(a), a[:100])
    return q.index(a)


def _schnitt(q, a, e, ab=0):
    i = q.index(a, ab) if ab else _einmal(q, a)
    j = q.index(e, i + len(a))
    return q[i:j + len(e)]


def _fn_bereich(q, kopf):
    a = _einmal(q, kopf)
    return a, q.index("\nfunction ", a + 10)


def _zeile_ab(q, a):
    i = _einmal(q, a)
    return q[i:q.index("\r\n", i)]


def _klammer_fn(q, kopf):
    i = _einmal(q, kopf)
    d = 0
    for k in range(i, len(q)):
        c = q[k]
        if c == "{":
            d += 1
        elif c == "}":
            d -= 1
            if d == 0:
                return q[i:k + 1]
    raise AssertionError("Ende nicht gefunden: " + kopf)


def _node(prog, tmp_path, name):
    f = tmp_path / name
    f.write_text(prog, encoding="utf-8")
    r = subprocess.run(["node", str(f)], capture_output=True, text=True, encoding="utf-8", timeout=60)
    assert r.returncode == 0, r.stderr[-2000:]
    return json.loads(r.stdout.strip().splitlines()[-1])


def _fz_helfer(q):
    return "\n".join(_zeile_ab(q, k) for k in ("function _fzArchiviert(f){", "function _fzNurAktiv(l){", "function _fzNurArchiv(l){"))


def _wurzel_prop(q, comp, name):
    """Liest den Ausdruck, den die Wurzel der Ansicht fuer `name` reicht (None = nicht gereicht)."""
    i = _einmal(q, "React.createElement(%s, {" % comp)
    zeile = q[i:q.index("\n", i)]
    m = re.search(r"[{,]\s*" + name + r":\s*([A-Za-z_]+)\s*[,}]", zeile)
    return m.group(1) if m else None


DATEN = r"""
var ARCH="2026-11-19T10:00:00Z";
var ALLE=[
 {id:"fz1",kennzeichen:"TU-1AA",status:"aktiv",kmStand:1000,tankLog:[{preis:100,liter:50,datum:"2026-10-05"},{preis:40,liter:20,datum:"2026-11-03"}],schaeden:[]},
 {id:"fz2",kennzeichen:"TU-2BB",status:"aktiv",kmStand:2000,archiviert_am:ARCH,archiviert_von:"Admin",tankLog:[{preis:250,liter:120,datum:"2026-10-12"},{preis:60,liter:30,datum:"2026-11-02"}],schaeden:[{status:"offen"}]},
 {id:"fz3",kennzeichen:"TU-3CC",status:"stillgelegt",kmStand:3000,tankLog:[{preis:999,liter:1,datum:"2026-10-01"}],schaeden:[]}
];
var AKTIV=_fzNurAktiv(ALLE);
function ausdruck(n){if(n==="fahrzeuge")return ALLE;if(n==="fahrzeugeAktiv")return AKTIV;if(n==null)return undefined;throw new Error("unbekannter Ausdruck "+n);}
"""


# ══ Teil 1: Auswertung ══════════════════════════════════════════════════════

def _auswertung_lauf(q, tmp_path):
    a, e = _fn_bereich(q, "function AuswertungView({")
    v = q[a:e]
    daten = _schnitt(v, "  const _fzLbl=(f)=>", "  // ── Data: Zeiterfassung letzte 7 Tage", ab=1)
    assert v.count("  const _fzLbl=(f)=>") == 1
    k0 = 'React.createElement(Kpi, { label: "Fahrzeuge", value: '
    assert v.count(k0) == 1
    i = v.index(k0) + len(k0)
    kpi = v[i:v.index(', color: "#0ea5e9", i: 3', i)]
    wert, sub = kpi.split(", sub: ", 1)
    prop = _wurzel_prop(q, "AuswertungView", "fahrzeuge")
    prog = (_fz_helfer(q) + DATEN +
            "var _react={useMemo:{call:function(t,f){return f();}}};function _eur0(v){return '€ '+Math.round(v);}\n"
            "function lauf(fahrzeuge){\n" + daten.replace("  // ── Data: Zeiterfassung letzte 7 Tage", "") +
            "\nreturn {total:totalTankKosten,tank:fzTankProFz,km:fzKm,schaden:fzSchaeden,wert:(" + wert + "),sub:(" + sub + ")};}\n"
            "console.log(JSON.stringify(lauf(ausdruck(" + json.dumps(prop) + "))));\n")
    return prop, _node(prog, tmp_path, "auswertung.js")


def test_auswertung_zaehlt_archivierte_kosten_mit(tmp_path):
    prop, r = _auswertung_lauf(_q(), tmp_path)
    assert prop == "fahrzeuge", "die Auswertung bekommt wieder nur die aktiven: " + str(prop)
    assert r["total"] == 450, r  # 140 aktiv + 310 archiviert; stillgelegt bleibt draussen (v897)
    labels = {x["l"]: x["v"] for x in r["tank"]}
    assert labels == {"TU-1AA": 140, "TU-2BB (archiviert)": 310}, labels
    assert "TU-2BB (archiviert)" in [x["l"] for x in r["km"]]
    # offene Schaeden = Arbeit von heute -> nur aktive
    assert [x["l"] for x in r["schaden"]] == [], r["schaden"]
    # Zaehler bleibt "aktive Fahrzeuge" (nicht stillgelegt, nicht archiviert), Summe sagt, dass archivierte drin sind
    assert r["wert"] == 1 and r["sub"] == "€ 450 Tankkosten inkl. archivierte", r


def test_auswertung_umkehrprobe_alte_verdrahtung(tmp_path):
    q = _q()
    i = _einmal(q, "React.createElement(AuswertungView, {")
    zeile = q[i:q.index("\n", i)]
    alt = q.replace(zeile, zeile.replace("fahrzeuge: fahrzeuge,", "fahrzeuge: fahrzeugeAktiv,", 1), 1)
    assert alt != q
    prop, r = _auswertung_lauf(alt, tmp_path)
    assert prop == "fahrzeugeAktiv"
    assert r["total"] == 140, "Umkehrprobe: mit der alten Verdrahtung muessen die archivierten Kosten fehlen"


# ══ Chef-Uebersicht: Tankkosten gesamt / laufender Monat ════════════════════

def _chef_lauf(q, tmp_path):
    a, e = _fn_bereich(q, "function ChefDashboard({")
    v = q[a:e]
    s = _schnitt(v, "const _fzHistC=", "\r\n", ab=1)
    assert v.count("const _fzHistC=") == 1
    s2 = _schnitt(v, "  const _moNow=_td.slice(0,7);", "\r\n", ab=1)
    s3 = _schnitt(v, "  const tankMTD=", "\r\n", ab=1)
    pf, pa = _wurzel_prop(q, "ChefDashboard", "fahrzeuge"), _wurzel_prop(q, "ChefDashboard", "fahrzeugeAlle")
    prog = (_fz_helfer(q) + DATEN + "var _td='2026-11-19';\nfunction lauf(fahrzeuge,fahrzeugeAlle){" + s + s2 + s3 +
            "return {gesamt:totalTank,monat:tankMTD};}\n"
            "console.log(JSON.stringify(lauf(ausdruck(" + json.dumps(pf) + "),ausdruck(" + json.dumps(pa) + "))));\n")
    return (pf, pa), _node(prog, tmp_path, "chef.js")


def test_chef_tankkosten_mit_archivierten(tmp_path):
    p, r = _chef_lauf(_q(), tmp_path)
    assert p == ("fahrzeugeAktiv", "fahrzeuge"), p
    assert r == {"gesamt": 1449, "monat": 100}, r  # Monat 11: 40 aktiv + 60 archiviert


def test_chef_umkehrprobe(tmp_path):
    q = _q()
    i = _einmal(q, "React.createElement(ChefDashboard, {")
    zeile = q[i:q.index("\n", i)]
    alt = q.replace(zeile, zeile.replace(" fahrzeugeAlle: fahrzeuge,", "", 1), 1)
    assert alt != q
    p, r = _chef_lauf(alt, tmp_path)
    assert r["monat"] == 40, "Umkehrprobe: ohne fahrzeugeAlle fehlt der Monatsanteil des archivierten Fahrzeugs"


# ══ Home: Tankkosten je Fahrzeug im Monat / 6-Monats-Verlauf ════════════════

def _home_lauf(q, tmp_path):
    a, e = _fn_bereich(q, "function HomeView({")
    v = q[a:e]
    h = _schnitt(v, "  const _fzHist=", "\r\n", ab=1)
    assert v.count("  const _fzHist=") == 1
    mc = _schnitt(v, "        const fzMonthCosts=", ".sort((a,b)=>b.cost-a.cost);", ab=1)
    assert v.count("        const fzMonthCosts=") == 1
    lp = _schnitt(v, "let cost=0,lit=0;", "}}));", ab=1)
    assert v.count("let cost=0,lit=0;") == 1
    pf, pa = _wurzel_prop(q, "HomeView", "fahrzeuge"), _wurzel_prop(q, "HomeView", "fahrzeugeAlle")
    prog = (_fz_helfer(q) + DATEN + "function td2(){return '2026-11-19';}\n"
            "function lauf(fahrzeuge,fahrzeugeAlle){" + h + "const curMo=td2().slice(0,7);" + mc +
            "const key='2026-10';" + lp + "return {monat:fzMonthCosts,okt:cost};}\n"
            "console.log(JSON.stringify(lauf(ausdruck(" + json.dumps(pf) + "),ausdruck(" + json.dumps(pa) + "))));\n")
    return (pf, pa), _node(prog, tmp_path, "home.js")


def test_home_monatskosten_mit_archivierten(tmp_path):
    p, r = _home_lauf(_q(), tmp_path)
    assert p == ("fahrzeugeAktiv", "fahrzeuge"), p
    assert [(x["kz"], x["cost"]) for x in r["monat"]] == [("TU-2BB (archiviert)", 60), ("TU-1AA", 40)], r
    assert r["okt"] == 1349, r  # Oktober: 100 + 250 + 999 (Verlauf zaehlt alle, wie bisher)


def test_home_umkehrprobe(tmp_path):
    q = _q()
    i = _einmal(q, "React.createElement(HomeView, {")
    zeile = q[i:q.index("\n", i)]
    alt = q.replace(zeile, zeile.replace(" fahrzeugeAlle: fahrzeuge,", "", 1), 1)
    p, r = _home_lauf(alt, tmp_path)
    assert r["okt"] == 1099 and [x["kz"] for x in r["monat"]] == ["TU-1AA"], "Umkehrprobe griff nicht"


# ══ Bueroexport: Tank-Kontrolle ═════════════════════════════════════════════

def _buero_lauf(q, tmp_path):
    a, e = _fn_bereich(q, "function VBueroExport({")
    v = q[a:e]
    rows = _schnitt(v, "const rows=(fahrzeuge||[]).flatMap(f=>(f.tankLog||[])", ";\r\n", ab=1)
    assert v.count("const rows=(fahrzeuge||[]).flatMap(f=>(f.tankLog||[])") == 1
    prop = _wurzel_prop(q, "VBueroExport", "fahrzeuge")
    prog = (_fz_helfer(q) + DATEN + "function lauf(fahrzeuge){" + rows +
            "return rows.map(function(r){return r.f.id+'/'+r.e.preis;});}\n"
            "console.log(JSON.stringify(lauf(ausdruck(" + json.dumps(prop) + "))));\n")
    return prop, _node(prog, tmp_path, "buero.js")


def test_buero_tankkontrolle_zeigt_archivierte(tmp_path):
    q = _q()
    prop, r = _buero_lauf(q, tmp_path)
    assert prop == "fahrzeuge"
    assert "fz2/250" in r and "fz2/60" in r, r
    a, e = _fn_bereich(q, "function VBueroExport({")
    v = q[a:e]
    assert v.count('(_fzArchiviert(r.f)?" (archiviert)":"")') == 2, "Markierung Handy + Tabelle"


def test_buero_umkehrprobe(tmp_path):
    q = _q()
    i = _einmal(q, "React.createElement(VBueroExport, {")
    zeile = q[i:q.index("\n", i)]
    alt = q.replace(zeile, zeile.replace("fahrzeuge: fahrzeuge,", "fahrzeuge: fahrzeugeAktiv,", 1), 1)
    prop, r = _buero_lauf(alt, tmp_path)
    assert not any(x.startswith("fz2/") for x in r), "Umkehrprobe griff nicht"


# ══ Verdrahtung: wer bekommt was ════════════════════════════════════════════

def test_arbeitsansichten_bleiben_aktiv():
    q = _q()
    for comp in ("HomeView", "ChefDashboard", "WeekPlan", "FlotteView"):
        assert _wurzel_prop(q, comp, "fahrzeuge") == "fahrzeugeAktiv", comp
        assert _wurzel_prop(q, comp, "fahrzeugeAlle") == "fahrzeuge", comp
    for comp in ("AuswertungView", "VBueroExport", "MitarbeiterView"):
        assert _wurzel_prop(q, comp, "fahrzeuge") == "fahrzeuge", comp
    assert _wurzel_prop(q, "FahrzeugView", "fahrzeuge") == "fahrzeuge"
    assert "WochenplanTafel,{wpHistory:wpHistory,monteure:monteure,fahrzeuge:fahrzeugeAktiv," in q  # Kiosk
    assert "_fzRef.current=fahrzeugeAktiv;" in q  # Pickerl-/Service-Hinweise
    assert '(fahrzeugeAktiv||[]).filter(f=>_nrm(f.kennzeichen).includes(ql)' in q  # Schnellsuche


def test_wochenplan_loest_ueber_volle_liste_auf_auswahl_bleibt_aktiv():
    q = _q()
    a, e = _fn_bereich(q, "function WeekPlan({")
    v = q[a:e]
    assert "const _fzWpAlle=fahrzeugeAlle||fahrzeuge||[];" in v
    assert "(fahrzeuge||[]).find(" not in v, "eine Zuteilung loest wieder nur ueber die aktiven auf"
    assert v.count("_fzWpAlle.find(") == 6
    assert 'const spezFz=(fahrzeuge||[]).filter(f=>f.status!=="stillgelegt"' in v  # Auswahl


def test_fahrtenbuch_panel_auswahl_aktiv_eintraege_voll(tmp_path):
    q = _q()
    a, e = _fn_bereich(q, "function FahrtenbuchPanel({")
    v = q[a:e]
    sel = "_fzNurAktiv(fahrzeuge).map(f=>React.createElement('option',{key:f.id,value:f.id},f.kennzeichen+' '+f.marke))"
    assert v.count(sel) == 1
    assert v.count("const fz=(fahrzeuge||[]).find(f=>f.id===e.fahrzeug_id);") == 2
    zeile = _schnitt(v, "fz?(fz.kennzeichen||\"\")", ":e.fahrzeug_id)", ab=1)[:-1]  # ohne die schliessende Klammer von createElement
    prog = (_fz_helfer(q) + DATEN + "var React={createElement:function(t,p,x){return x;}};\n"
            "function lauf(fahrzeuge){var e={fahrzeug_id:'fz2'};var fz=(fahrzeuge||[]).find(f=>f.id===e.fahrzeug_id);"
            "return {auswahl:" + sel + ",zeile:" + zeile + "};}\n"
            "console.log(JSON.stringify(lauf(ALLE)));\n")
    r = _node(prog, tmp_path, "fbpanel.js")
    assert r["auswahl"] == ["TU-1AA undefined", "TU-3CC undefined"], r
    assert r["zeile"] == "TU-2BB (archiviert)", r


def test_flotte_fahrtenbuch_mit_historie():
    q = _q()
    a, e = _fn_bereich(q, "function FlotteView(")
    v = q[a:e]
    assert "const trackerFzHist=((_demo&&_demoDaten)?fahrzeuge:(props.fahrzeugeAlle||fahrzeuge)).filter(" in v
    assert "const _panelBuch=h(FahrtenbuchView,{fahrzeuge:trackerFzHist," in v
    assert "var fleet=_fzFleetZeilen(fahrzeuge,byId,_now2);" in v  # Karte/Liste bleiben aktiv
    a, e = _fn_bereich(q, "function FahrtenbuchView(")
    assert "+(_fzArchiviert(f)?' · archiviert':'')" in q[a:e]


# ══ Teil 2: Werkzeug-Selbstausleihe ═════════════════════════════════════════

WZ_STUBS = r"""
var SB_REST="https://x/rest/v1";var aufrufe=[];var rlsLeer=false;var netzKaputt=false;var http500=false;
var DB={};
function _onAuthFail(){}
async function _dbOhneDateien(t,i,d){return d;}
async function _authRetry(f){return f();}
function _fT(x){return x;}
function _sbWH(){return {};}
async function fetch(url,init){
  if(netzKaputt)throw new TypeError("Failed to fetch");
  var m=/\/werkzeuge\?id=eq\.([^&]+)(&status=eq\.([a-z]+))?$/.exec(url);aufrufe.push({url:url,method:init.method,body:JSON.parse(init.body)});
  if(http500)return {ok:false,status:500,text:async function(){return "boom";}};
  var id=decodeURIComponent(m[1]);var row=DB[id];var treffer=row&&(!m[3]||row.status===m[3]);
  if(treffer&&!rlsLeer)Object.assign(row,JSON.parse(init.body));
  var out=(treffer&&!rlsLeer)?[Object.assign({},row)]:[];
  return {ok:true,status:200,json:async function(){return out;}};
}
async function _sbGet(t,filter){var id=decodeURIComponent(/id=eq\.([^&]+)/.exec(filter)[1]);return DB[id]?[Object.assign({},DB[id])]:[];}
"""


def _wz_helfer(q):
    h = _schnitt(q, "async function _wzAusleiheBedingt(id,patch,wer){", "\r\n}\r\n")
    t = _schnitt(q, "function _wzAusleiheText(r,name,ausWarteschlange){", '  return "";}')
    return h + "\n" + t + "\n"


WZ_PROBE = r"""
(async function(){
var out={};var P={status:"ausgegeben",zugewiesen:"A",standort:"Baustelle"};
DB={w1:{id:"w1",status:"verfuegbar",zugewiesen:"",projekt:"",standort:"Lager"}};
out.ok=(await _wzAusleiheBedingt("w1",P,"A")).ergebnis;out.okDb=DB.w1.zugewiesen;
out.url=aufrufe[0].url;out.method=aufrufe[0].method;
// Wettlauf: B tippt auf einem zweiten Geraet, sieht noch "verfuegbar" - die Zeile gehoert aber schon A
var rB=await _wzAusleiheBedingt("w1",{status:"ausgegeben",zugewiesen:"B",standort:"Baustelle"},"B");
out.race=rB.ergebnis;out.raceDb=DB.w1.zugewiesen;out.raceText=_wzAusleiheText(rB,"Bohrhammer",false);
out.raceQueue=_wzAusleiheText(rB,null,true);
out.meins=(await _wzAusleiheBedingt("w1",P,"A")).ergebnis;
DB={w2:{id:"w2",status:"reparatur",zugewiesen:"",standort:"Werkstatt"}};
var rR=await _wzAusleiheBedingt("w2",P,"A");out.rep=rR.ergebnis;out.repText=_wzAusleiheText(rR,"",false);
DB={w3:{id:"w3",status:"verfuegbar"}};rlsLeer=true;var rV=await _wzAusleiheBedingt("w3",P,"A");out.rls=rV.ergebnis;out.rlsText=_wzAusleiheText(rV,"",false);rlsLeer=false;
DB={};out.fehlt=(await _wzAusleiheBedingt("w9",P,"A")).ergebnis;
DB={w4:{id:"w4",status:"verfuegbar"}};http500=true;try{await _wzAusleiheBedingt("w4",P,"A");out.e500="kein Fehler";}catch(e){out.e500=e.message;}http500=false;
console.log(JSON.stringify(out));
})();
"""


def test_wz_bedingte_ausleihe(tmp_path):
    r = _node(WZ_STUBS + _wz_helfer(_q()) + WZ_PROBE, tmp_path, "wz.js")
    assert r["ok"] == "ok" and r["okDb"] == "A"
    assert r["method"] == "PATCH" and r["url"].endswith("/werkzeuge?id=eq.w1&status=eq.verfuegbar"), r
    assert r["race"] == "vergeben" and r["raceDb"] == "A", "der zweite hat den ersten ueberschrieben"
    assert r["raceText"] == "Werkzeug wurde inzwischen von jemand anderem ausgeliehen (Bohrhammer)"
    assert r["raceQueue"] == "Offline-Ausleihe nicht übernommen: Werkzeug wurde inzwischen von jemand anderem ausgeliehen"
    assert r["meins"] == "meins"
    assert r["rep"] == "vergeben" and r["repText"] == "Werkzeug ist inzwischen nicht mehr verfügbar"
    assert r["rls"] == "verweigert" and "keine Schreibberechtigung" in r["rlsText"]
    assert r["fehlt"] == "fehlt"
    assert r["e500"].startswith("HTTP500")


def test_wz_umkehrprobe_ohne_bedingung_gewinnt_der_letzte(tmp_path):
    h = _wz_helfer(_q())
    alt = h.replace('+"&status=eq.verfuegbar"', "", 1)
    assert alt != h
    r = _node(WZ_STUBS + alt + WZ_PROBE, tmp_path, "wz_alt.js")
    assert r["race"] == "ok" and r["raceDb"] == "B", "Umkehrprobe: ohne Bedingung muss der letzte gewinnen"


SELF_STUBS = r"""
var window={__t:[]};window.__toast=function(m,k){window.__t.push(m);};
var _react={useRef:{call:function(t,v){return {current:v};}}};
var WZ=[{id:"w1",name:"Bohrhammer",status:"verfuegbar",zugewiesen:"",projekt:"",standort:"Lager"}];
var _wzRef={current:WZ};var SQ={l:[],push:function(x){this.l.push(x);}};
var online=true;function _netzOnline(){return online;}
function setWerkzeuge(fn){WZ=fn(WZ);_wzRef.current=WZ;}var SC=null;function setScannedWz(fn){SC=fn(SC);}
var curUser={name:"Anna",monteurId:"A"};var _myMid="A";var pushNotif=function(){};
"""


def _self_out(q):
    a = "const _wzAusleiheLaeuft=_react.useRef.call(void 0, {});"
    return _schnitt(q, a, "delete _wzAusleiheLaeuft.current[id];});};")


SELF_PROBE = r"""
function warte(){return new Promise(function(r){setTimeout(r,30);});}
(async function(){
var out={};
DB={w1:{id:"w1",status:"ausgegeben",zugewiesen:"B",projekt:"",standort:"Baustelle"}};
wzSelfOut("w1");await warte();
out.konflikt={zug:WZ[0].zugewiesen,status:WZ[0].status,sq:SQ.l.length,toast:window.__t.slice(-1)[0]};
WZ=[{id:"w1",name:"Bohrhammer",status:"verfuegbar",zugewiesen:"",projekt:"",standort:"Lager"}];_wzRef.current=WZ;
DB={w1:{id:"w1",status:"verfuegbar",zugewiesen:"",projekt:"",standort:"Lager"}};
wzSelfOut("w1");await warte();
out.ok={zug:WZ[0].zugewiesen,db:DB.w1.zugewiesen,sq:SQ.l.length};
WZ=[{id:"w1",name:"Bohrhammer",status:"verfuegbar",zugewiesen:"",projekt:"",standort:"Lager"}];_wzRef.current=WZ;
online=false;wzSelfOut("w1");await warte();online=true;
out.offline={zug:WZ[0].zugewiesen,sq:SQ.l.slice(-1)[0]};
WZ=[{id:"w1",name:"Bohrhammer",status:"verfuegbar",zugewiesen:"",projekt:"",standort:"Lager"}];_wzRef.current=WZ;
netzKaputt=true;wzSelfOut("w1");await warte();netzKaputt=false;
out.netz={zug:WZ[0].zugewiesen,n:SQ.l.length,marke:SQ.l.slice(-1)[0].body._nurWennVerfuegbar};
console.log(JSON.stringify(out));
})();
"""


def _self_lauf(q, quelle, tmp_path, name):
    netz = _schnitt(q, "function _netzFehlerArt(e,online){", "\r\n}\r\n") + "\n" + _zeile_ab(q, "function _netzFehlerTransient(e,online){")
    prog = (WZ_STUBS + SELF_STUBS + _klammer_fn(q, "function _optionalChain(ops) {") + "\n" + netz + "\n" +
            _wz_helfer(q) + quelle + "\n" + SELF_PROBE)
    return _node(prog, tmp_path, name)


def test_wz_selbstausleihe_echt(tmp_path):
    q = _q()
    r = _self_lauf(q, _self_out(q), tmp_path, "self.js")
    k = r["konflikt"]
    assert k["zug"] == "B" and k["status"] == "ausgegeben" and k["sq"] == 0, k  # Serverstand, nichts eingereiht
    assert "Werkzeug wurde inzwischen von jemand anderem ausgeliehen" in k["toast"], k
    assert r["ok"] == {"zug": "A", "db": "A", "sq": 0}, r["ok"]
    o = r["offline"]
    assert o["zug"] == "A" and o["sq"]["method"] == "PUT" and o["sq"]["url"] == "/api/werkzeuge/w1"
    assert o["sq"]["body"] == {"status": "ausgegeben", "zugewiesen": "A", "standort": "Baustelle", "_nurWennVerfuegbar": "A"}
    assert r["netz"] == {"zug": "A", "n": 2, "marke": "A"}, r["netz"]


def test_wz_selbstausleihe_umkehrprobe(tmp_path):
    q = _q()
    s = _self_out(q)
    alt = s.replace("_wzAusleiheBedingt(id,_patch,_myMid).then(", "Promise.resolve({ergebnis:\"ok\"}).then(", 1)
    assert alt != s
    r = _self_lauf(q, alt, tmp_path, "self_alt.js")
    assert r["konflikt"]["zug"] == "A", "Umkehrprobe: ohne Bedingung haette die App den Konflikt nicht bemerkt"


ZWEIG_PROBE = r"""
var window={__t:[],ev:[]};window.__toast=function(m){window.__t.push(m);};window.dispatchEvent=function(e){window.ev.push(e);};
function CustomEvent(n,o){this.type=n;this.detail=o.detail;}
(async function(){
var out={};
DB={w1:{id:"w1",status:"ausgegeben",zugewiesen:"B",projekt:"",standort:"Baustelle"}};
out.r=await T("werkzeuge","w1","PUT",{status:"ausgegeben",zugewiesen:"A",standort:"Baustelle",_nurWennVerfuegbar:"A"});
out.db=DB.w1.zugewiesen;out.toast=window.__t[0];out.ev=window.ev.map(function(e){return [e.type,e.detail.id,e.detail.zeile.zugewiesen];});
out.body=aufrufe[0].body;
out.ohne=await T("werkzeuge","w1","PUT",{status:"verfuegbar",zugewiesen:"",projekt:"",standort:"Lager"});
DB={w1:{id:"w1",status:"ausgegeben",zugewiesen:"A"}};window.__t=[];
out.meins=await T("werkzeuge","w1","PUT",{status:"ausgegeben",zugewiesen:"A",standort:"Baustelle",_nurWennVerfuegbar:"A"});out.meinsToast=window.__t.length;
console.log(JSON.stringify(out));
})();
"""


def test_warteschlange_erkennt_konflikt(tmp_path):
    q = _q()
    a, e = _fn_bereich(q, "async function _translateAndExec(url,method,body){")
    v = q[a:e]
    k = '  if(resource==="werkzeuge"&&idOrSub&&method==="PUT"&&body&&body._nurWennVerfuegbar){'
    assert v.count(k) == 1
    zweig = _schnitt(v, k, "    return{ok:1};\r\n  }\r\n", ab=1)
    # der Zweig steht VOR dem allgemeinen PUT
    assert v.index(k) < v.index("  // ─── Generic CRUD ───")
    prog = WZ_STUBS + _wz_helfer(q) + "async function T(resource,idOrSub,method,body){\n" + zweig + 'return "durch";}\n' + ZWEIG_PROBE
    r = _node(prog, tmp_path, "zweig.js")
    assert r["r"] == {"ok": 1} and r["db"] == "B", r  # nicht ueberschrieben
    assert "_nurWennVerfuegbar" not in r["body"], r["body"]
    assert r["toast"].endswith("Offline-Ausleihe nicht übernommen: Werkzeug wurde inzwischen von jemand anderem ausgeliehen"), r
    assert r["ev"] == [["epk-wz-konflikt", "w1", "B"]]
    assert r["ohne"] == "durch", "Eintraege ohne Marke muessen den allgemeinen Weg nehmen"
    assert r["meins"] == {"ok": 1} and r["meinsToast"] == 0
    # die Wurzel uebernimmt den Serverstand
    assert 'window.addEventListener("epk-wz-konflikt",f);return ()=>window.removeEventListener("epk-wz-konflikt",f);' in q


def test_wz_projekt_und_pins_unberuehrt():
    q = _q()
    # projekt: Ausgabe per Scan setzt es auch nicht - Semantik unklar, bewusst unveraendert
    assert 'const _patch={status:"ausgegeben",zugewiesen:_myMid,standort:"Baustelle"};' in q
    assert "86400000" not in _wz_helfer(q) and "86400000" not in _self_out(q)


# ══ Fahrzeuge-Seite: Kostenuebersicht und Fuhrpark-Export ═══════════════════

def test_fuhrpark_export_und_kosten_mit_archivierten(tmp_path):
    q = _q()
    a, e = _fn_bereich(q, "function FahrzeugView({")
    v = q[a:e]
    x = _schnitt(v, "const _fzX=", ";", ab=1)
    st = '_fzArchiviert(f)?("archiviert"+(_fzArchivDatum(f.archiviert_am)?" "+_fzArchivDatum(f.archiviert_am):"")):f.status'
    assert v.count(st) == 1 and v.count("const _fzX=") == 1
    k0 = "React.createElement(FlotteKostenPanel, {fahrzeuge: "
    assert v.count(k0) == 1
    i = v.index(k0) + len(k0)
    kf = v[i:v.index(", isMob: isMob, finanzen: _finKarte, onOpen: ", i)]
    j = v.index("onOpen: ", i) + len("onOpen: ")
    oo = v[j:v.index("}})", j) + 1]
    prog = (_fz_helfer(q) + _zeile_ab(q, "function _fzArchivDatum(iso){") + DATEN +
            "var window={t:[]};window.__toast=function(m){window.t.push(m);};var gesetzt=[];function setSel(id){gesetzt.push(id);}\n"
            "var fahrzeugeAlle=ALLE;var fahrzeuge=_fzNurAktiv(ALLE);var visibleFz=fahrzeuge;" + x + ";\n"
            "var status=_fzX.map(function(f){return " + st + ";});var kosten=(" + kf + ").map(function(f){return f.id;});"
            "var onOpen=" + oo + ";onOpen('fz2');onOpen('fz1');\n"
            "console.log(JSON.stringify({ids:_fzX.map(function(f){return f.id;}),status:status,kosten:kosten,gesetzt:gesetzt,toast:window.t}));\n")
    r = _node(prog, tmp_path, "fzview.js")
    assert r["ids"] == ["fz1", "fz3", "fz2"], r
    assert r["status"] == ["aktiv", "stillgelegt", "archiviert 19.11.2026"], r
    assert r["kosten"] == ["fz1", "fz3", "fz2"], r
    assert r["gesetzt"] == ["fz1"] and len(r["toast"]) == 1, "archiviertes Fahrzeug darf die Bearbeitung nicht oeffnen"
    a, e = _fn_bereich(q, "function FlotteKostenPanel(props){")
    assert q[a:e].count("(r.f.kennzeichen||'?')+(_fzArchiviert(r.f)?' (archiviert)':''))") == 2
