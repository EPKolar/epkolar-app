# -*- coding: utf-8 -*-
"""Verhaltenstests fuer die restlichen zahnlosen Lohn-Stellen aus den Mutationslaeufen B und K (26.11.2026, 3.9.1122).

Freigabe GF 26.11. abends: "JA zum Schaerfen der 18 offenen Tests (Stempel, Zulagen, OFFA), mit Grenze" -
nur Tests, kein Zeichen an Stempel-, Zulagen- oder Abgleich-Rechnung. Die OFFA-Faelle (B #18, #21, #22) stehen in
tests/test_abgleich_verhalten_v1122.py (Dateiname ohne die von Tor 7 gesperrten Teilwoerter).

Jeder Test schneidet den ECHTEN Code aus index.html und fuehrt ihn in node aus (TZ=Europe/Vienna). Die Mutation,
gegen die der jeweilige Test beissen muss, steht im Testkopf; die Probe dazu in
epk-tiefenpruefung-2026-11-26/B_mutation.md, Abschnitt "Lohn-/OFFA-Tests geschaerft 26.11.".

Herkunft der Sollwerte: je Test als "Regel:" angegeben. "Charakterisierung" heisst: keine schriftliche Regel gefunden,
der Test haelt das heutige Verhalten fest.
"""
import json
import os
import re
import shutil
import subprocess
import tempfile

import pytest

NODE = shutil.which("node")
needs_node = pytest.mark.skipif(not NODE, reason="node fehlt")


# ── Schnitt-Helfer ──────────────────────────────────────────────────────────
def _block(src, kopf, ende):
    assert src.count(kopf) == 1, "Anker nicht eindeutig: " + kopf[:80]
    i = src.index(kopf)
    return src[i:src.index(ende, i + len(kopf)) + len(ende)]


def _zeile(src, anfang):
    """Von einem eindeutigen Anfang bis Zeilenende."""
    assert src.count(anfang) == 1, "Anker nicht eindeutig: " + anfang[:80]
    i = src.index(anfang)
    return src[i:src.index("\n", i)]


def _marker(src, a, b):
    assert src.count(a) == 1 and src.count(b) == 1, a
    i = src.index(a)
    return src[i:src.index(b, i)]


def _fnb(src, name):
    """function NAME(...){...} - Klammern zaehlen, Strings und Kommentare ueberspringen."""
    m = list(re.finditer(r"(?:^|[;\s}])(function " + re.escape(name) + r"\()", src, re.M))
    assert len(m) == 1, (name, len(m))
    i = m[0].start(1)
    k = src.index("{", i)
    tiefe, p, n = 0, k, len(src)
    while p < n:
        c = src[p]
        if c in "\"'`":
            q = c
            p += 1
            while p < n and src[p] != q:
                p += 2 if src[p] == "\\" else 1
        elif src.startswith("/*", p):
            p = src.index("*/", p) + 1
        elif src.startswith("//", p) and src[p - 1] != ":":
            p = src.index("\n", p)
        elif c == "{":
            tiefe += 1
        elif c == "}":
            tiefe -= 1
            if tiefe == 0:
                return src[i:p + 1]
        p += 1
    raise AssertionError("Ende nicht gefunden: " + name)


def _node(js):
    fd, pfad = tempfile.mkstemp(suffix=".js", prefix="lohnz_")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(js)
        env = dict(os.environ, TZ="Europe/Vienna")
        r = subprocess.run([NODE, pfad], capture_output=True, text=True, encoding="utf-8", timeout=120, env=env)
    finally:
        os.remove(pfad)
    assert r.returncode == 0, r.stderr[-2000:]
    return json.loads(r.stdout.strip().splitlines()[-1])


VORSPANN = "var window={};var COLORS=new Proxy({},{get:function(){return '#000';}});\n"


def _zeit_kern(src):
    return (_marker(src, "//@ZEIT-RUNDUNG-START", "//@ZEIT-RUNDUNG-END") + "\n"
            + _zeile(src, "function _wrapHrs(von,bis){") + "\n")


# ── B #5  Projektzeit: kein Auto-Raster (ZEIT_RASTER_MIN = 1) ────────────────
# Regel: index.html Kommentar an ZEIT_RASTER_MIN (v3.9.1110, GF 24.11.2026): "Projektzeit wird NICHT mehr automatisch
# gerundet ... Raster 1 = _zeitRundVon/_zeitRundBis normalisieren nur noch 7:03 -> 07:03". CHANGELOG 3.9.1110.
# Mutation: ZEIT_RASTER_MIN 1 -> 5 (Rueckfall auf die alte 5-min-Rundung zulasten des Monteurs).
@needs_node
def test_b5_projektzeit_wird_nicht_mehr_gerundet(index_html):
    js = VORSPANN + _zeit_kern(index_html) + r"""
console.log(JSON.stringify({
  raster: ZEIT_RASTER_MIN,
  v1: _zeitRundVon("07:01"), b1: _zeitRundBis("16:59"), v2: _zeitRundVon("7:03"), b2: _zeitRundBis("16:47"),
  e1: _zeitEffektiveStunden("07:01","16:59",1), e2: _zeitEffektiveStunden("07:03","16:47",0.5),
  e3: _zeitEffektiveStunden("07:00","16:00",1)
}));"""
    r = _node(js)
    assert r["raster"] == 1, r
    assert (r["v1"], r["b1"], r["v2"], r["b2"]) == ("07:01", "16:59", "07:03", "16:47"), r
    # 07:01-16:59 = 9 h 58 min - 1 h = 8,97 h; mit 5-min-Raster waeren es 07:05-16:55 = 8,83 h (-8 min am Tag)
    assert r["e1"] == 8.97, r
    assert r["e2"] == 9.23, r   # 07:03-16:47 = 9 h 44 min - 0,5 h
    assert r["e3"] == 8.0, r


# ── K #12  Eingabe nur in Viertelstunden (ZEIT_EINGABE_RASTER_MIN = 15) ──────
# Regel: Kommentar ZEIT_EINGABE_RASTER_MIN (v3.9.1110 GF: "15 min = kleinste Faktura-Einheit") und _zeitEingabeFehler
# ("Was der Nutzer NICHT geaendert hat, wird nicht geprueft"). Mutation: ZEIT_EINGABE_RASTER_MIN 15 -> 5.
@needs_node
def test_k12_eingabe_nur_viertelstunden(index_html):
    js = VORSPANN + _zeit_kern(index_html) + r"""
var F=_zeitEingabeFehler;
console.log(JSON.stringify({
  r: ZEIT_EINGABE_RASTER_MIN,
  von705: F("07:05","16:00",null,null), von710: F("07:10","16:00",null,null),
  bis1610: F("07:00","16:10",null,null), ok: F("07:15","16:45",null,null),
  std71: F("","",7.1,null), std7083: F("","",7.0833,null), std725: F("","",7.25,null),
  altUnveraendert: F("07:05","16:00",null,{von:"07:05",bis:"16:00",stunden:8}),
  altGeaendert: F("07:10","16:00",null,{von:"07:05",bis:"16:00",stunden:8}),
  imR: [_zeitImRaster("07:45"),_zeitImRaster("07:50"),_stdImRaster(1.75),_stdImRaster(1.5833)]
}));"""
    r = _node(js)
    assert r["r"] == 15, r
    assert r["von705"] and r["von705"].startswith("Von nur in Viertelstunden"), r
    assert r["von710"] and r["von710"].startswith("Von nur in Viertelstunden"), r
    assert r["bis1610"] and r["bis1610"].startswith("Bis nur in Viertelstunden"), r
    assert r["ok"] is None, r
    assert r["std71"] and "0,25-Schritten" in r["std71"], r
    assert r["std7083"] and "0,25-Schritten" in r["std7083"], r   # 7 h 05 min
    assert r["std725"] is None, r
    assert r["altUnveraendert"] is None, r     # alter krummer Eintrag bleibt speicherbar
    assert r["altGeaendert"] and r["altGeaendert"].startswith("Von nur"), r
    assert r["imR"] == [True, False, True, False], r


# ── K #13  Arbeitsschein: Fahrzeit im 15-min-Raster ─────────────────────────
# Regel: saveAs-Kommentar "v3.9.1110 GF 24.11.: 15-min-Raster; unveraenderte alte Werte bleiben" und Meldung
# "Fahrzeit nur in Viertelstunden". Mutation: ["fahrzeit","Fahrzeit"] aus der _asKrumm-Feldliste entfernt.
@needs_node
def test_k13_arbeitsschein_fahrzeit_im_raster(index_html):
    kern = _block(index_html, "const _asAlt=editId?(arbeitsscheine.find(a=>a.id===editId)||{}):{};const _asKrumm=",
                  "return Number(v)%ZEIT_EINGABE_RASTER_MIN!==0;});")
    js = VORSPANN + "const ZEIT_EINGABE_RASTER_MIN=" + re.search(r"const ZEIT_EINGABE_RASTER_MIN=(\d+);", index_html).group(1) + ";\n" + r"""
function pruef(form,editId,arbeitsscheine){%s
return _asKrumm?_asKrumm[1]:null;}
var AS=[{id:"s1",fahrzeit:10,stunden:30}];
console.log(JSON.stringify([
  pruef({fahrzeit:10},null,AS), pruef({fahrzeit:15,stunden:30},null,AS), pruef({stunden:50},null,AS),
  pruef({fahrzeit:10,stunden:30},"s1",AS), pruef({fahrzeit:20,stunden:30},"s1",AS), pruef({fahrzeit:""},null,AS),
  pruef({fahrzeit:"45",stunden:"120"},null,AS)
]));""" % kern
    r = _node(js)
    assert r == ["Fahrzeit", None, "Arbeitszeit", None, "Fahrzeit", None, None], r


# ── B #9  PZE-Monatszeilen: der letzte Monatstag ist dabei ──────────────────
def _pze_kern(src):
    teile = [_marker(src, "//@STEMPEL-HELPERS-START", "//@STEMPEL-HELPERS-END"),
             _zeile(src, "const isoWof=(dd)=>"),
             _block(src, "function _kvTagesnorm(dow,feiertag){", "\n}")]
    for n in ("_easterSunday", "_isATFeiertag", "_pzeDayKey", "_pzeGroupByDay", "_pzeUngerade", "_pzeAutoPause",
              "_pzeTagRow", "_pzeKW", "_resolveApprK", "_pzeBuildRows"):
        teile.append(_fnb(src, n))
    return VORSPANN + "\n".join(teile).replace("const isoWof=", "var isoWof=") + "\n"


STEMPEL_JS = r"""
function tag(wid,iso,von,bis){return [{worker_id:wid,direction:"kommen",ts:new Date(iso+"T"+von+":00").toISOString()},
                                      {worker_id:wid,direction:"gehen",ts:new Date(iso+"T"+bis+":00").toISOString()}];}
"""


# Regel: Kommentar ueber _pzeBuildRows (v3.9.776 / v3.9.700-DST-Lektion): "die kalendarische Tagesiteration ...
# Maerz 30 statt 31 Zeilen" war der Fehler; jeder Kalendertag von..bis einschliesslich. Mutation: Schleife <= -> <.
@needs_node
def test_b9_pze_zeilen_bis_einschliesslich_monatsletztem(index_html):
    js = _pze_kern(index_html) + STEMPEL_JS + r"""
var W={id:"w1",name:"Monteur A",role:"Monteur"};
var evs=[].concat(tag("w1","2026-03-31","07:00","16:00"),tag("w1","2026-12-31","07:00","16:00"),tag("w1","2026-02-27","07:00","16:00"));
function lauf(von,bis){var r=_pzeBuildRows(W,von,bis,evs,STEMPEL_PAUSE_FALLBACK,[],{},{});
  if(!r.length)return {n:0};var l=r[r.length-1];return {n:r.length,erster:r[0].datum,letzter:l.datum,nettoLetzter:l.nettoMin};}
console.log(JSON.stringify({mar:lauf("2026-03-01","2026-03-31"),dez:lauf("2026-12-01","2026-12-31"),
  feb:lauf("2026-02-01","2026-02-28"),tag:lauf("2026-03-31","2026-03-31")}));"""
    r = _node(js)
    assert r["mar"] == {"n": 31, "erster": "2026-03-01", "letzter": "2026-03-31", "nettoLetzter": 480}, r
    assert r["dez"] == {"n": 31, "erster": "2026-12-01", "letzter": "2026-12-31", "nettoLetzter": 480}, r
    assert r["feb"]["n"] == 28 and r["feb"]["letzter"] == "2026-02-28", r
    assert r["tag"]["n"] == 1 and r["tag"]["nettoLetzter"] == 480, r   # von == bis: genau ein Tag


# ── B #16  Entfernungszulage aus der Stempeluhr: Monatsende ────────────────
# Regel: Kommentar ueber _ezTageAusStempel (v3.9.1107, GF 24.11.2026): Tagesstunden = Netto laut Stempeluhr fuer den
# Monat, nur Tage mit Stempelung. Mutation: Monatsende = Laenge des Vormonats (new Date(y,m,0) -> new Date(y,m-1,0)).
@needs_node
def test_b16_ez_aus_stempel_zaehlt_den_31(index_html):
    js = _pze_kern(index_html) + _fnb(index_html, "_ezTageAusStempel") + "\n" + STEMPEL_JS + r"""
var W={id:"w1",name:"Monteur A",role:"Monteur"};
var evs=[].concat(tag("w1","2026-12-01","07:00","16:00"),tag("w1","2026-12-30","07:00","12:00"),tag("w1","2026-12-31","07:00","16:30"),
  tag("w2","2026-12-31","07:00","16:00"),tag("w1","2026-03-31","06:00","16:00"),tag("w1","2026-02-28","07:00","15:00"));
console.log(JSON.stringify({dez:_ezTageAusStempel(evs,W,null,"2026-12"),mar:_ezTageAusStempel(evs,W,null,"2026-03"),
  feb:_ezTageAusStempel(evs,W,null,"2026-02"),ohne:_ezTageAusStempel(evs,{name:"x"},null,"2026-12")}));"""
    r = _node(js)
    # 07:00-16:00 = 9 h - 60 min Pause = 8 h; 07:00-12:00 = 5 h - 1 h = 4 h; 07:00-16:30 = 8,5 h
    assert r["dez"] == {"2026-12-01": 8, "2026-12-30": 4, "2026-12-31": 8.5}, r
    assert r["mar"] == {"2026-03-31": 9}, r   # nach der Sommerzeit-Umstellung, 31-Tage-Monat
    assert r["feb"] == {"2026-02-28": 7}, r
    assert r["ohne"] == {}, r


# ── B #10  Pausenregeln (lohnwirksam) nur fuer echtes Admin ────────────────
# Regel: Kommentar an der Einbindung "v3.9.639: Stempel-Pausenregeln pro Rolle - nur echtes Admin (isWAdm), nicht
# PL/Buero" und am Stempel-Block ("Konfig-UI ... Gate isWAdm"). Mutation: isWAdm zusaetzlich fuer Rolle buero.
ALLE_ROLLEN = ["admin", "projektleiter", "buero", "obermonteur", "techniker", "monteur", "helfer", "lager_display"]


@needs_node
def test_b10_pausenregeln_nur_admin(index_html):
    gate = _block(index_html, "const isWAdm=curUser.role", ";")
    einbau = _block(index_html, "isWAdm&&React.createElement(StempelPauseConfig", "} )")
    kv = _block(index_html, "isWAdm&&React.createElement(KVRulesConfig", "} )")
    innen = _block(_fnb(index_html, "StempelPauseConfig"), "const _isAdmin=_cu.role", ";")
    js = r"""
var StempelPauseConfig=function(){},KVRulesConfig=function(){};var isMob=false;
var React={createElement:function(t){return {typ:t===StempelPauseConfig?"pause":"kv"};}};
var out=%s.map(function(role){var curUser={role:role,name:"U"};%s
var _cu=curUser;%s
var a=(%s);var b=(%s);
return {role:role,isWAdm:!!isWAdm,pause:!!(a&&a.typ==="pause"),kv:!!(b&&b.typ==="kv"),innen:!!_isAdmin};});
console.log(JSON.stringify(out));""" % (json.dumps(ALLE_ROLLEN), gate, innen, einbau, kv)
    r = _node(js)
    for x in r:
        soll = x["role"] == "admin"
        assert x["isWAdm"] is soll and x["pause"] is soll and x["kv"] is soll and x["innen"] is soll, x


# ── B #12  Zulagen-Monat: Grenzen 6,0 h und 11,0 h ─────────────────────────
# Regel: Kommentar _kvTaggeldTag "je Tag: >11h -> taggeldAb11h; >6h -> taggeldAb6h; sonst 0" - beide Grenzen STRENG.
# Saetze aus KV_RULES_FALLBACK (v3.9.785: klein 11,94; taggeldAb11h 30,00). Mutation: Zaehler tage11 bei a>=11.
def _kv_kern(src):
    return (VORSPANN + _block(src, "const KV_RULES_FALLBACK={", "\n};") + "\n"
            + _marker(src, "//@KV-ZULAGEN-START", "//@KV-ZULAGEN-END") + "\n")


@needs_node
def test_b12_zulagen_monat_grenzen_6_und_11(index_html):
    js = _kv_kern(index_html) + r"""
var R=KV_RULES_FALLBACK;
console.log(JSON.stringify({
  m: _kvZulagenMonat([6.0,6.01,11.0,11.01,5.99,0,null],[],R),
  nur11: _kvZulagenMonat([11.0],[],R), ueber11: _kvZulagenMonat([11.01],[],R),
  t: [_kvTaggeldTag(6.0,R),_kvTaggeldTag(6.01,R),_kvTaggeldTag(11.0,R),_kvTaggeldTag(11.01,R)]
}));"""
    r = _node(js)
    assert r["t"] == [0, 11.94, 11.94, 30], r
    assert r["nur11"] == {"tage6": 1, "tage11": 0, "taggeldSum": 11.94}, r
    assert r["ueber11"] == {"tage6": 0, "tage11": 1, "taggeldSum": 30}, r
    m = r["m"]
    assert (m["tage6"], m["tage11"]) == (2, 1), m
    assert abs(m["taggeldSum"] - (2 * 11.94 + 30)) < 1e-9, m


# Befund (Rand von B #11/#12, schon in B_mutation.md als Beobachtung): der Rueckfallsatz in _kvTaggeldTag ist 11,71,
# die Regel (KV_RULES_FALLBACK v3.9.785) sagt "11,71->11,94 ... Alt-Satz 11,71 war falsch". Wirkt nur, wenn rules ohne
# taggeldAb6h ankommen; ausgezahlt wird laut Code ueber _ezEffTage/_ezSaetze (dort 11,94).
@needs_node
@pytest.mark.xfail(strict=True, reason="Befund 26.11.: _kvTaggeldTag-Rueckfall taggeldAb6h ist 11,71, Regel v3.9.785 sagt 11,94 (Alt-Satz falsch); _kvZulagenMonat([7]) ohne rules liefert 11,71")
def test_b12_befund_rueckfallsatz_klein_ist_alt(index_html):
    js = _kv_kern(index_html) + "console.log(JSON.stringify([_kvTaggeldTag(7,{}),_kvZulagenMonat([7],[],null).taggeldSum]));"
    r = _node(js)
    assert r == [11.94, 11.94], r


# ── B #14  Zulagen-Saetze: Rueckfall klein/mittel/gross ─────────────────────
# Regel: KV_RULES_FALLBACK v3.9.785 "Entfernungszulage MITTEL (30,00) / GROSS (62,04) EUR/Tag (KV ab 01.01.2026)",
# klein = taggeldAb6h 11,94. Mutation: in _ezSaetze die Rueckfallsaetze mittel/gross vertauscht.
@needs_node
def test_b14_ez_saetze_rueckfall_und_kv(index_html):
    js = VORSPANN + _block(index_html, "const KV_RULES_FALLBACK={", "\n};") + "\n" + "\n".join(
        _fnb(index_html, n) for n in ("_ezKey", "_ezDayEff", "_ezEffTage", "_ezSaetze")) + r"""
var flags={}; flags[_ezKey("w1","2026-12-01")]={stufe:"mittel"}; flags[_ezKey("w1","2026-12-02")]={stufe:"gross"};
flags[_ezKey("w1","2026-12-03")]={stufe:"klein"};
console.log(JSON.stringify({
  leer:_ezSaetze({}), nul:_ezSaetze(null), kv:_ezSaetze(KV_RULES_FALLBACK), teil:_ezSaetze({ezMittel:31.5}),
  null0:_ezSaetze({taggeldAb6h:0,ezMittel:0,ezGross:0}),
  eff:_ezEffTage({},flags,"w1",_ezSaetze({}),{}), effKv:_ezEffTage({},flags,"w1",_ezSaetze(KV_RULES_FALLBACK),{})
}));"""
    r = _node(js)
    soll = {"klein": 11.94, "mittel": 30, "gross": 62.04}
    assert r["leer"] == soll and r["nul"] == soll and r["kv"] == soll, r
    assert r["teil"] == {"klein": 11.94, "mittel": 31.5, "gross": 62.04}, r
    assert r["null0"] == {"klein": 0, "mittel": 0, "gross": 0}, r   # 0 ist ein Wert, kein Rueckfall
    for k in ("eff", "effKv"):
        e = r[k]
        assert (e["tageKlein"], e["tageMittel"], e["tageGross"]) == (1, 1, 1), e
        assert abs(e["sum"] - (11.94 + 30 + 62.04)) < 1e-9, e


# ── B #35  Monatsfreigabe-Meldungen: nie an inaktive/gesperrte Benutzer ────
# Regel: Kommentar "MELDUNGEN ... Ziel NUR die betroffene Person bzw. Rolle" + _mfAktiv (active 0/false, locked 1/true
# = nicht aktiv) im Rollenfilter. Die Inaktiv-Regel selbst steht nur im Code (_mfAktiv) - Charakterisierung dieser
# Teilregel. Mutation: _mfZiele Rollenzweig ohne _mfAktiv(u).
@needs_node
def test_b35_mf_meldungen_nie_an_inaktive(index_html):
    js = VORSPANN + "\n".join([
        _zeile(index_html, "var MF_MONTEUR_ROLLEN="), _zeile(index_html, "var MF_NOTIF_ROLLE="),
        _fnb(index_html, "_mfPrefAn"), _fnb(index_html, "_mfAktiv"), _fnb(index_html, "_mfMonteurUser"),
        _fnb(index_html, "_mfZiele")]) + r"""
var U=[
 {id:"b1",role:"buero"},{id:"b2",role:"buero",active:false},{id:"b3",role:"buero",active:0},
 {id:"b4",role:"buero",locked:true},{id:"b5",role:"buero",locked:1},{id:"b6",role:"buero",active:1,locked:0},
 {id:"a1",role:"admin"},{id:"a2",role:"admin",locked:true},{id:"a3",role:"admin",active:false},
 {id:"m2",role:"monteur",monteurId:"w1",locked:true},{id:"m1",role:"monteur",monteurId:"w1"},
 {id:"m3",role:"monteur",monteurId:"w2"}];
var row={worker_id:"w1",period:"2026-11"};
console.log(JSON.stringify({buero:_mfZiele("mf_freigegeben",row,U,{}),admin:_mfZiele("mf_admin_bereit",row,U,{}),
  monteur:_mfZiele("mf_monteur_bereit",row,U,{}),aus:_mfZiele("mf_freigegeben",row,U,{b1:{mf_freigegeben:false}})}));"""
    r = _node(js)
    assert r["buero"] == ["b1", "b6"], r
    assert r["admin"] == ["a1"], r
    assert r["monteur"] == ["m1"], r
    assert r["aus"] == ["b6"], r


# ── B #36  Dashboard: Namen offener Monatsabrechnungen nur Admin/PL ────────
# Regel: HomeView isAdmin = admin oder projektleiter; der Hinweis haengt an "&&isAdmin". Keine eigene schriftliche Regel
# zur Namensliste gefunden - Charakterisierung (Namen fremder Monteure gehoeren nicht auf das Monteur-Dashboard).
# Mutation: Hinweis ohne &&isAdmin.
@needs_node
def test_b36_finkzeit_hinweis_mit_namen_nur_admin_pl(index_html):
    isadm = _block(index_html, "const isAdmin=_optionalChain([curUser, 'optionalAccess', _243 => _243.role])", ";")
    hinweis = _block(index_html, "if(FINKZEIT_ENABLED&&finkStats.offen>0", "details:_details});\n  }")
    js = _block(index_html, "function _optionalChain(ops) {", "return value; }") + r"""
var FINKZEIT_ENABLED=true;var onNav=function(){};
var finkStats={offen:2,pendingDetails:[{label:"Oktober 2026",workers:["Monteur A","Monteur B"]}]};
var out=%s.map(function(role){var curUser={role:role};var alerts=[];%s
%s
return {role:role,n:alerts.length,details:alerts.length?alerts[0].details:null};});
console.log(JSON.stringify(out));""" % (json.dumps(ALLE_ROLLEN), isadm, hinweis)
    r = _node(js)
    for x in r:
        if x["role"] in ("admin", "projektleiter"):
            assert x["n"] == 1 and x["details"] == ["Oktober 2026 — Monteur A, Monteur B"], x
        else:
            assert x["n"] == 0, x


# ── K #10  Woche aus dem Geraetespeicher: Montag bis Sonntag ───────────────
# Regel: loadWeek "const to=isoDate(6); /* v3.9.546: bis Sonntag (Zeit#2) */" und v3.9.926 (Cache-Rueckfall bei 401,
# sonst traegt der Monteur seine Stunden doppelt ein). Mutation: _wocheAusCache dt<=to -> dt<to.
@needs_node
def test_k10_woche_aus_cache_mit_sonntag(index_html):
    cache = _zeile(index_html, "const _wocheAusCache=()=>")
    pos = index_html.index(cache)
    def zurueck(anfang):
        i = index_html.rfind(anfang, 0, pos)
        assert i > 0, anfang
        return index_html[i:index_html.index("\n", i)]
    kwmon = zurueck("const kwMon=_react.useMemo.call(void 0, ()=>{")
    daydate = zurueck("const dayDate=(off)=>")
    isodate = zurueck("const isoDate=(off)=>")
    fromto = zurueck("const from=isoDate(0);const to=isoDate(6);")
    js = (_zeile(index_html, "const _ymd=d=>`") + "\n" + r"""
var _react={useMemo:{call:function(_,f){return f();}}};
function woche(yr,kw,selWorker,entries){%s
%s
%s
%s
%s
return {from:from,to:to,daten:_wocheAusCache().map(function(e){return (e.datum||e.date).slice(0,10);})};}
var E=[{worker:"M1",datum:"2026-08-30"},{worker:"M1",datum:"2026-08-31"},{w:"M1",date:"2026-09-03T00:00:00"},
       {worker_id:"M1",datum:"2026-09-05"},{worker:"M1",datum:"2026-09-06"},{worker:"M1",datum:"2026-09-07"},
       {worker:"M2",datum:"2026-09-06"}];
console.log(JSON.stringify(woche(2026,36,"M1",E)));""" % (kwmon, daydate, isodate, fromto, cache))
    r = _node(js)
    assert r["from"] == "2026-08-31" and r["to"] == "2026-09-06", r
    assert r["daten"] == ["2026-08-31", "2026-09-03", "2026-09-05", "2026-09-06"], r


# ── K #16  Urlaubskontingent: nur die Eintraege GENAU dieses Namens ────────
# Regel: Schluessel = name_iso (Kommentar _ezAbsSet "Key = workerName_iso (Muster ... key.indexOf(name+'_')===0)");
# K_mutation2 #16: Urlaub von "Hansi" darf bei "Hans" nicht zaehlen. Mutation (K #16): startsWith(m+"_") -> startsWith(m)
# - fuer sich allein GLEICHWERTIG (dateStr=key.replace(m+"_","") und die Jahrespruefung fangen es), siehe Bericht.
@needs_node
def test_k16_yearstk_namenspraefix(index_html):
    js = VORSPANN + "\n".join([
        _block(index_html, "const AT_T={", "\n};").replace("const AT_T=", "var AT_T="),
        _fnb(index_html, "_easterSunday"), _fnb(index_html, "_isATFeiertag"), _fnb(index_html, "_wocheOfK"),
        _fnb(index_html, "_stdVonTagK"), _fnb(index_html, "_resolveApprK"), _fnb(index_html, "_yearStK")]) + r"""
var abs={"Hans_2026-03-02":{type:"urlaub",hours:8},"Hansi_2026-03-03":{type:"urlaub",hours:8},
  "Hansi_2026-03-04":{type:"urlaub",hours:8},"Hans_2025-12-30":{type:"urlaub",hours:8},
  "Hans Peter_2026-03-05":{type:"urlaub",hours:8},"Hans_2026-03-09":{type:"urlaub",hours:8}};
var ap={"Hans_2026-03-02":"genehmigt","Hansi_2026-03-03":"genehmigt","Hansi_2026-03-04":"genehmigt","Hans_2026-03-09":"abgelehnt"};
function k(m){var r=_yearStK(abs,ap,{},m,2026);return [r.urlaub,r.urlaubStd,r.urlaubGenehmigt];}
console.log(JSON.stringify({hans:k("Hans"),hansi:k("Hansi"),peter:k("Hans Peter")}));"""
    r = _node(js)
    assert r["hans"] == [1, 8, 1], r       # nur 02.03.; 2025 und abgelehnter 09.03. zaehlen nicht
    assert r["hansi"] == [2, 16, 2], r
    assert r["peter"] == [1, 8, 0], r      # ohne Entscheidung = ausstehend


# ── K #19  Wochen-Stundenbestaetigung: GE = Ende der LETZTEN Buchung ───────
# Regel: Kommentar v3.9.879 LOHN: "ko und ge stammten BEIDE aus arr[ri] ... Bei drei Buchungen war GE das Ende der
# ZWEITEN statt der letzten". KO aus der ersten, GE aus der letzten Buchung. Mutation: _eL = arr[0].
@needs_node
def test_k19_wochen_stz_gehen_aus_letzter_buchung(index_html):
    ko = _block(index_html, "const _e0=arr.length?arr[0]:null;", "const ko=(_e0&&_e0.von)?esc(_e0.von):\"\";")
    ge = _block(index_html, "const _eL=arr.length?", "const ge=(_eL&&_eL.bis)?esc(_eL.bis):\"\";")
    js = r"""
function esc(s){return String(s);}
function tag(arr){%s
%s
return [ko,ge];}
console.log(JSON.stringify([
  tag([{von:"07:00",bis:"10:00"},{von:"10:30",bis:"13:00"},{von:"13:30",bis:"16:15"}]),
  tag([{von:"07:00",bis:"15:30"}]), tag([]), tag([{von:"07:00",bis:"12:00"},{von:"12:30"}])
]));""" % (ko, ge)
    r = _node(js)
    assert r == [["07:00", "16:15"], ["07:00", "15:30"], ["", ""], ["07:00", ""]], r


# ── K #28  Wochenplanung: hoechste ISO-KW eines Jahres ─────────────────────
# Regel: Kommentar v3.9.483 "Der 28.12. liegt IMMER in der letzten ISO-Woche"; v3.9.1012 _kwZiel-Kommentar
# (KW53/2026 erreichbar, kein 2027-53). Mutation: _getMaxKW 28.12. -> 31.12.
@needs_node
def test_k28_max_kw_und_jahreswechsel(index_html):
    js = (_zeile(index_html, "const _getMaxKW=(year)=>") + "\n" + _zeile(index_html, "const _kwZiel=(y,k,ny)=>") + r"""
console.log(JSON.stringify({max:[2020,2024,2025,2026,2027,2032].map(_getMaxKW),
  z:[_kwZiel(2025,53),_kwZiel(2026,53),_kwZiel(2026,54),_kwZiel(2027,0),_kwZiel(2026,1),_kwZiel(2027,53,2027)]}));""")
    r = _node(js)
    assert r["max"] == [53, 52, 52, 53, 52, 53], r
    assert r["z"] == [[2026, 1], [2026, 53], [2027, 1], [2026, 53], [2026, 1], [2027, 52]], r


# ── K #29  Anmeldung: Sperrkennzeichen aus login_lookup weist ab ───────────
# Regel: Kommentar v3.9.1056 Fund 6: "login_lookup liefert ... nur fuer aktive, nicht gesperrte Konten. Unbekannt,
# gesperrt, ohne E-Mail ... zeigen DIESELBE Meldung" (die alte Server-Fassung mit ganzer Zeile wird weiter verstanden).
# Mutation (K #29): if(!email||(user&&user.locked)){ -> if(!email){.
@needs_node
def test_k29_login_lookup_gesperrt_weist_neutral_ab(index_html):
    seg = _block(index_html, "const _neutral=\"Anmeldung fehlgeschlagen", "throw new Error(_neutral+\" [B20-B]\");}")
    js = r"""
var console_err=[];var console={error:function(){console_err.push(1);},log:function(){}};
function pruef(user){%s
return "weiter:"+email;}
function lauf(u){try{return pruef(u);}catch(e){return "ab:"+e.message;}}
process.stdout.write(JSON.stringify([lauf({email:"a@b.at"}),lauf({email:"a@b.at",locked:true}),lauf({email:" a@b.at ",locked:false}),
  lauf({}),lauf({email:"   "}),lauf(null),lauf({email:"a@b.at",locked:1})])+"\n");""" % seg
    r = _node(js)
    neutral = "ab:Anmeldung fehlgeschlagen – Benutzername oder Passwort prüfen [B20-B]"
    assert r == ["weiter:a@b.at", neutral, "weiter:a@b.at", neutral, neutral, neutral, neutral], r
