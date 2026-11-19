"""v1049 Flotte-Karte: Transporter-Marker, Info-Karte, Admin-Demo (Sebastian 19.11.:
"Fahrzeuge in der Flotte wirklich als kleine Transportbusse darstellen, sauber machen, und wenn
man draufklickt soll man Infos erhalten wie Geschwindigkeit etc.").

fz_positions ist leer (Tracker noch nicht bestellt) - die Kette ist darum NUR hier abgesichert.
Die Rechner leben im Sentinel //@FLOTTE-KARTE-START..END und laufen hier in Node, mit den
ECHTEN Konstanten aus index.html (TIME_*, COLORS per Regex aus der Quelle, keine Abschrift).

Geprueft wird Verhalten, jeweils mit Umkehrprobe:
  - Kartenzustand -> Farbe (faehrt gruen, steht orange, geparkt grau, veraltet hellgrau gestrichelt)
  - Kurs -> Himmelsrichtung, Richtung nur in Fahrt
  - Geschwindigkeit nur bei frischem Signal; nie "0 km/h"/"1970"/"NaN" aus null
  - Demo-Modus nur fuer Admins, Demo-Daten rufen keine Schreib-/Netzhelfer auf, die View
    sperrt im Demo-Modus Poll, Adress-Lookup, Fahrtenbuch und IMEI-Speichern
"""
import json
import re

from conftest import run_node_snippet, _extract_fn

NOW = 1768478400000  # 2026-01-15T12:00:00Z
MIN = 60 * 1000


def _consts(src):
    zeilen = re.findall(r"^const TIME_\w+=[^;\n]+;", src, re.M)
    assert len(zeilen) >= 4, "TIME_*-Konstanten nicht gefunden"
    m = re.search(r"const COLORS=\{[^}]*\};", src)
    assert m, "COLORS nicht gefunden"
    return "\n".join(zeilen) + "\n" + m.group(0) + "\n"


def _block(src):
    m = re.search(r"//@FLOTTE-KARTE-START\n(.*?)//@FLOTTE-KARTE-END", src, re.S)
    assert m, "Sentinel //@FLOTTE-KARTE fehlt"
    return m.group(1)


_DEPS = ["_flotteInactive", "_flotteRelTime", "_fzStampFink", "_fzHaversine", "_fzOdo",
         "_fzNormPos", "_fzSegmente", "_fbSummen"]

_OUT = ("function _out(v){process.stdout.write(JSON.stringify(v,function(k,x){"
        "return (typeof x==='number'&&Number.isNaN(x))?'NaN':x;}));}\n")


def _run(node_exe, src, expr, block=None, vorher=""):
    parts = [_consts(src), _OUT, vorher]
    for n in _DEPS:
        fn = _extract_fn(src, n)
        assert fn, n + " nicht gefunden"
        parts.append(fn + "\n")
    parts.append(block if block is not None else _block(src))
    parts.append("\n_out(" + expr + ");")
    return json.loads(run_node_snippet(node_exe, "".join(parts)))


def _ts(ms):
    return "new Date(" + str(ms) + ").toISOString()"


# ── 1) Kartenzustand -> Farbe ───────────────────────────────────────────────

FAELLE = {
    "faehrt": "{ts:%s,speed:52,ignition:true}" % _ts(NOW - 30 * 1000),
    "steht": "{ts:%s,speed:0,ignition:true}" % _ts(NOW - 2 * MIN),
    "aus": "{ts:%s,speed:0,ignition:false}" % _ts(NOW - 3 * 60 * MIN),
    "veraltet_alt": "{ts:%s,speed:0,ignition:false}" % _ts(NOW - 2 * 24 * 60 * MIN),
    "veraltet_fahrt": "{ts:%s,speed:60,ignition:true}" % _ts(NOW - 40 * MIN),
    "kein_ts": "{ts:null,speed:50,ignition:true}",
    "null": "null",
}


def test_zustand_und_farbe(node_exe, index_html):
    expr = "{" + ",".join(
        "%s:_fzKartenZustand(%s,%d)" % (k, v, NOW) for k, v in FAELLE.items()
    ) + ",farbe:FZ_KARTE_FARBE,warn:COLORS.WARNING_FILL}"
    r = _run(node_exe, index_html, expr)
    assert (r["faehrt"], r["steht"], r["aus"]) == ("faehrt", "steht", "aus")
    assert r["veraltet_alt"] == "veraltet"
    assert r["veraltet_fahrt"] == "veraltet", "40 min alte Fahrt-Meldung ist keine Fahrt mehr"
    assert r["kein_ts"] == "kein_signal" and r["null"] == "kein_signal"
    f = r["farbe"]
    assert f["faehrt"] == "#009640"
    assert f["steht"] == r["warn"] == "#c2410c"
    assert f["aus"] not in (f["faehrt"], f["steht"]) and f["veraltet"] != f["aus"]


def test_marker_traegt_farbe_und_strichelung(node_exe, index_html):
    expr = ("{f:_fzVanMarkerHtml({zustand:'faehrt',heading:90,kennzeichen:'TU-1',gewaehlt:true}),"
            "v:_fzVanMarkerHtml({zustand:'veraltet',heading:90,kennzeichen:'TU-2'}),"
            "s:_fzVanMarkerHtml({zustand:'steht',heading:90,kennzeichen:'TU-3'}),"
            "x:_fzVanMarkerHtml({zustand:'faehrt',kennzeichen:'<img src=x onerror=alert(1)>'})}")
    r = _run(node_exe, index_html, expr)
    assert 'fill="#009640"' in r["f"] and "fz-van-sel" in r["f"] and "rotate(90deg)" in r["f"]
    assert "stroke-dasharray" in r["v"] and "rotate(" not in r["v"], "veraltet: gestrichelt, kein Zeiger"
    assert 'fill="#c2410c"' in r["s"] and "rotate(" not in r["s"], "im Stand kein Fahrtrichtungs-Zeiger"
    assert "<img" not in r["x"] and "&lt;img" in r["x"], "Kennzeichen muss escaped sein"


# ── 2) Kurs -> Himmelsrichtung ──────────────────────────────────────────────

def test_himmelsrichtung(node_exe, index_html):
    grade = [0, 22, 23, 45, 90, 135, 180, 225, 270, 315, 338, 359, -90, 405, "null", "''", "'abc'"]
    expr = "[" + ",".join("_fzRichtung(%s)" % g for g in grade) + "]"
    r = _run(node_exe, index_html, expr)
    assert r == ["N", "N", "NO", "NO", "O", "SO", "S", "SW", "W", "NW", "N", "N", "W", "NO", "", "", ""]


def test_heading_aus_raw_und_richtung_nur_in_fahrt(node_exe, index_html):
    fahrt = "{ts:%s,speed:52,ignition:true,raw:{course:44.6}}" % _ts(NOW - 20 * 1000)
    stand = "{ts:%s,speed:0,ignition:true,raw:{course:44}}" % _ts(NOW - 20 * 1000)
    expr = ("{a:_fzHeading({raw:{course:44.6}}),b:_fzHeading({raw:{heading:-10}}),c:_fzHeading({raw:{course:''}}),"
            "d:_fzHeading({}),e:_fzHeading(null),"
            "t1:_fzRichtungText(%s,%d),t2:_fzRichtungText(%s,%d),"
            "d1:_fzVanDreh('faehrt',270),d2:_fzVanDreh('faehrt',90),d3:_fzVanDreh('steht',90),d4:_fzVanDreh('faehrt',null)}"
            % (fahrt, NOW, stand, NOW))
    r = _run(node_exe, index_html, expr)
    assert (r["a"], r["b"], r["c"], r["d"], r["e"]) == (45, 350, None, None, None)
    assert r["t1"] == "Nordost (45°)"
    assert r["t2"] == "—", "Kurs im Stand ist Rauschen"
    assert r["d1"] == {"zeiger": 270, "spiegeln": True}
    assert r["d2"] == {"zeiger": 90, "spiegeln": False}
    assert r["d3"] == {"zeiger": None, "spiegeln": False}
    assert r["d4"] == {"zeiger": None, "spiegeln": False}


# ── 3/4) Geschwindigkeit nur frisch, nie aus null ───────────────────────────

SPEED = {
    "frisch": ("{ts:%s,speed:52.4}" % _ts(NOW - 30 * 1000), "52 km/h"),
    "frisch_null": ("{ts:%s,speed:null}" % _ts(NOW - 30 * 1000), "—"),
    "frisch_leer": ("{ts:%s,speed:''}" % _ts(NOW - 30 * 1000), "—"),
    "frisch_nan": ("{ts:%s,speed:'x'}" % _ts(NOW - 30 * 1000), "—"),
    "frisch_null_stand": ("{ts:%s,speed:0}" % _ts(NOW - 30 * 1000), "0 km/h"),
    "alt_20min": ("{ts:%s,speed:80}" % _ts(NOW - 20 * MIN), "—"),
    "alt_3tage": ("{ts:%s,speed:80}" % _ts(NOW - 3 * 24 * 60 * MIN), "—"),
    "ts_null": ("{ts:null,speed:50}", "—"),
    "ts_fehlt": ("{speed:50}", "—"),
    "kein_p": ("null", "—"),
}


def test_geschwindigkeit_nur_bei_frischem_signal(node_exe, index_html):
    expr = "{" + ",".join("%s:_fzSpeedAnzeige(%s,%d)" % (k, v[0], NOW) for k, v in SPEED.items()) + "}"
    r = _run(node_exe, index_html, expr)
    for k, (_, soll) in SPEED.items():
        assert r[k] == soll, (k, r[k])


def test_null_erzeugt_nie_1970_nan_oder_0kmh(node_exe, index_html):
    leer = ["null", "{}", "{ts:null,speed:null,ignition:null,lat:null,lon:null}", "{ts:'',speed:''}"]
    expr = "[" + ",".join(
        "[_fzSpeedAnzeige(%s,%d),_fzRichtungText(%s,%d),JSON.stringify(_fzLetztesSignal(%s,%d)),"
        "_fzKartenZustand(%s,%d),_fzImeiTail(null)]" % (p, NOW, p, NOW, p, NOW, p, NOW) for p in leer) + "]"
    r = _run(node_exe, index_html, expr)
    for zeile in r:
        text = " ".join(str(x) for x in zeile)
        assert "1970" not in text and "NaN" not in text and "0 km/h" not in text, zeile
        assert zeile[2] == "null" and zeile[3] == "kein_signal"


def test_umkehrprobe_ohne_nullwache_kaeme_0kmh(node_exe, index_html):
    """Der Null-Test muss zuschlagen, wenn die Wache fehlt (Number(null)===0)."""
    blk = _block(index_html)
    alt = "if(v===undefined||v===null||v==='')return null;\n  var n=Number(v);\n  return (isFinite(n)&&n>=0)?n:null;"
    assert blk.count(alt) == 1
    kaputt = blk.replace(alt, "var n=Number(v);\n  return (isFinite(n)&&n>=0)?n:null;")
    r = _run(node_exe, index_html, "_fzSpeedAnzeige({ts:%s,speed:null},%d)" % (_ts(NOW - 1000), NOW), block=kaputt)
    assert r == "0 km/h", "Umkehrprobe: ohne Wache wird null zu 0 km/h"


def test_letztes_signal(node_exe, index_html):
    r = _run(node_exe, index_html, "_fzLetztesSignal({ts:%s},%d)" % (_ts(NOW - 3 * MIN), NOW))
    assert r["rel"] == "vor 3 min" and re.match(r"^\d\d:\d\d$", r["abs"])


# ── km / Fahrten / Route heute aus der on-demand-Historie ───────────────────

def _fahrt_js(start_ms, n, schritt_s=30):
    pts = []
    for i in range(n):
        pts.append("{ts:%s,lat:%.5f,lon:%.5f,speed:50,ignition:true}" % (
            _ts(start_ms + i * schritt_s * 1000), 48.40 + i * 0.001, 15.80 + i * 0.003))
    return "[" + ",".join(pts) + "]"


def test_heute_km_fahrten_route(node_exe, index_html):
    # Mitternacht LOKAL im Node-Prozess bestimmen, die Fahrt liegt 2 h danach.
    expr = ("(function(){var n=new Date(%d);var mn=new Date(n.getFullYear(),n.getMonth(),n.getDate()).getTime();"
            "var rows=%s;"
            "var heute=rows.map(function(p,i){return Object.assign({},p,{ts:new Date(mn+2*TIME_HOUR+i*30*TIME_SECOND).toISOString()});});"
            "var gestern=heute.map(function(p){return Object.assign({},p,{ts:new Date(new Date(p.ts).getTime()-TIME_DAY).toISOString()});});"
            "var muell=[{ts:null,lat:1,lon:1,speed:9},{ts:'',lat:1,lon:1}];"
            "var jetzt=mn+5*TIME_HOUR;"
            "return {h:_fzHeuteAusTrack(heute.concat(muell),jetzt,500),"
            "g:_fzHeuteAusTrack(gestern,jetzt,500),"
            "voll:_fzHeuteAusTrack(heute,jetzt,heute.length),"
            "leer:_fzHeuteAusTrack([],jetzt,500)};})()") % (NOW, _fahrt_js(0, 20))
    r = _run(node_exe, index_html, expr)
    h = r["h"]
    assert h["fahrten"] == 1 and h["km"] > 1 and len(h["punkte"]) == 20 and h["teilweise"] is False
    assert h["gueltig"] == 20, "Zeilen ohne ts zaehlen nicht (new Date(null) waere 1970)"
    assert r["g"]["fahrten"] == 0 and r["g"]["km"] == 0 and r["g"]["punkte"] == []
    assert r["voll"]["teilweise"] is True, "Limit erreicht und nicht bis Mitternacht -> Untergrenze"
    assert r["leer"] == {"km": 0, "fahrten": 0, "teilweise": False, "punkte": [], "gueltig": 0}


# ── Demo-Modus: nur Admin, nie schreiben ────────────────────────────────────

ROLLEN = [
    ("{role:'admin'}", "?flottedemo=1", True),
    ("{role:'admin'}", "?x=1&flottedemo=1", True),
    ("{role:'admin'}", "?flottedemo=0", False),
    ("{role:'admin'}", "?flottedemo=10", False),
    ("{role:'admin'}", "", False),
    ("{role:'projektleiter'}", "?flottedemo=1", False),
    ("{role:'buero'}", "?flottedemo=1", False),
    ("{role:'monteur'}", "?flottedemo=1", False),
    ("{role:'Admin'}", "?flottedemo=1", False),
    ("{}", "?flottedemo=1", False),
    ("null", "?flottedemo=1", False),
    ("undefined", "?flottedemo=1", False),
]


def _rollen_expr():
    return "[" + ",".join("_fzDemoErlaubt(%s,%s)" % (u, json.dumps(q)) for u, q, _ in ROLLEN) + "]"


def test_demo_nur_fuer_admin(node_exe, index_html):
    r = _run(node_exe, index_html, _rollen_expr())
    assert r == [soll for _, _, soll in ROLLEN]


def test_umkehrprobe_demo_ohne_rollenpruefung(node_exe, index_html):
    blk = _block(index_html)
    alt = "if(!user||user.role!=='admin')return false;"
    assert blk.count(alt) == 1
    r = _run(node_exe, index_html, _rollen_expr(), block=blk.replace(alt, ""))
    assert r != [soll for _, _, soll in ROLLEN], "Umkehrprobe: ohne Rollenpruefung muss der Test rot werden"
    assert r[7] is True, "ein Monteur kaeme dann in den Demo-Modus"


_FALLEN = ("var _rufe=[];"
           "function _falle(n){return function(){_rufe.push(n);throw new Error('verboten: '+n);};}"
           "globalThis.fetch=_falle('fetch');var _sbPatch=_falle('_sbPatch');var _sbPost=_falle('_sbPost');"
           "var _sbDelete=_falle('_sbDelete');var _fzUpsertFahrten=_falle('_fzUpsertFahrten');"
           "var _fzPatchFahrt=_falle('_fzPatchFahrt');var _geoCacheSet=_falle('_geoCacheSet');"
           "var _geoNominatim=_falle('_geoNominatim');var _geoCacheGet=_falle('_geoCacheGet');"
           "var SyncQueue={add:_falle('SyncQueue.add'),push:_falle('SyncQueue.push'),enqueue:_falle('SyncQueue.enqueue')};"
           "try{globalThis.localStorage={setItem:_falle('localStorage.setItem'),getItem:function(){return null;}};}catch(e){}\n")


def test_demo_daten_rufen_nichts_auf(node_exe, index_html):
    expr = ("(function(){var d=_fzDemoDaten(%d);"
            "var h=d.fahrzeuge.map(function(f){var p=d.positions.filter(function(x){return x.fahrzeug_id===f.id;})[0];"
            "return [f.id,f._demo,_fzKartenZustand(p,%d)];});"
            "var t=_fzHeuteAusTrack(d.tracks['demo-1'],%d,500);"
            "return {rufe:_rufe,h:h,ids:d.positions.map(function(p){return p.fahrzeug_id;}),t:t,json:JSON.stringify(d).length};})()"
            % (NOW, NOW, NOW))
    r = _run(node_exe, index_html, expr, vorher=_FALLEN)
    assert r["rufe"] == [], "Demo-Daten haben einen Schreib-/Netzhelfer angefasst: %s" % r["rufe"]
    assert [x[0] for x in r["h"]] == ["demo-1", "demo-2", "demo-3", "demo-4"]
    assert all(x[1] is True for x in r["h"])
    assert [x[2] for x in r["h"]] == ["faehrt", "steht", "aus", "veraltet"], "jede Farbe einmal zeigen"
    assert all(i.startswith("demo-") for i in r["ids"])
    assert r["t"]["fahrten"] == 1 and len(r["t"]["punkte"]) >= 2


def test_umkehrprobe_fallen_greifen(node_exe, index_html):
    """Schutz nie ausgeloest = kein Schutz: die Fallen muessen einen Aufruf wirklich melden."""
    blk = _block(index_html) + "\nfunction _fzDemoDatenKaputt(n){_fzUpsertFahrten([]);return _fzDemoDaten(n);}\n"
    expr = "(function(){try{_fzDemoDatenKaputt(%d);}catch(e){}return _rufe;})()" % NOW
    r = _run(node_exe, index_html, expr, block=blk, vorher=_FALLEN)
    assert r == ["_fzUpsertFahrten"]


def _flotte_view(src):
    a = src.index("function FlotteView(props){")
    return src[a:src.index("//@FLOTTE-AUSBAU-START", a)]


def _demo_luecken(view):
    """Welche Lese-/Schreibwege der FlotteView sind im Demo-Modus NICHT gesperrt?"""
    luecken = []
    poll = view[view.index("/* Positionen laden + Live-Poll"):]
    if poll.find("if(_demo){setSt(") < 0 or poll.find("if(_demo){setSt(") > poll.find("_flotteFetchPositions()"):
        luecken.append("Positions-Poll")
    imei = view[view.index("const _imeiSpeichern=async function(fid){"):]
    if imei.find("if(_demo){") < 0 or imei.find("if(_demo){") > imei.find("_sbPatch("):
        luecken.append("IMEI-Speichern")
    orte = view[view.index("const [fzOrte,setFzOrte]"):]
    if orte.find("if(_demo)return;") < 0 or orte.find("if(_demo)return;") > orte.find("_geoCacheGet("):
        luecken.append("Adress-Cache")
    if "if(_demo||!selFid||!_selKey" not in view:
        luecken.append("Adress-Lookup")
    if view.count("(_demo?_panelBuchDemo:_panelBuch)") != 2:
        luecken.append("Fahrtenbuch")
    if "_demo?Promise.resolve(" not in view:
        luecken.append("Spur-Abruf")
    if "props.onOpenFahrzeug&&!_demo&&!f._demo" not in view:
        luecken.append("Fahrzeug oeffnen")
    if "const _demo=_fzDemoErlaubt(props.curUser," not in view:
        luecken.append("Rollen-Tor")
    return luecken


def test_view_sperrt_im_demo_alle_wege(index_html):
    assert _demo_luecken(_flotte_view(index_html)) == []


def test_umkehrprobe_view_ohne_sperren(index_html):
    v = _flotte_view(index_html)
    for alt, name in [
        ("if(_demo){setSt(", "Positions-Poll"),
        ("if(_demo){if(window.__toast)window.__toast('Demo-Modus: es wird nichts gespeichert'", "IMEI-Speichern"),
        ("if(_demo)return;/* v1049 Demo: kein Lesezugriff */", "Adress-Cache"),
        ("(_demo?_panelBuchDemo:_panelBuch)", "Fahrtenbuch"),
    ]:
        assert alt in v
        assert name in _demo_luecken(v.replace(alt, "/*weg*/", 1)), name


# ── Verdrahtung ─────────────────────────────────────────────────────────────

def test_fahrtenbuch_folgt_der_auswahl(index_html):
    """Versteckter Pfad: initialFid wirkte nur beim ersten Mount."""
    fb = _extract_fn(index_html, "FahrtenbuchView")
    assert "if(props.initialFid)setFid(props.initialFid);},[props.initialFid,props.fidAnstoss]);" in fb
    assert "initialFid:buchFid,fidAnstoss:buchAnstoss," in index_html


def test_poll_passt_nur_einmal_ein(index_html):
    v = _flotte_view(index_html)
    assert "if(_fitDone.current)pts=[];else if(pts.length)_fitDone.current=true;" in v
    i = v.index("if(_fitDone.current)pts=[];")
    assert i < v.index("else if(pts.length){try{_map.current.fitBounds(pts,"), "Wache muss VOR dem Einpassen stehen"


def test_marker_ist_transporter_mit_44px(index_html):
    v = _flotte_view(index_html)
    assert "iconSize:[44,44],iconAnchor:[22,22]" in v
    assert "m.on('click',function(){_waehle(f.id);});" in v
    assert "keyboard:true" in v
    assert "FZ_LABEL_MIN_ZOOM" in v


def test_fahrzeug_oeffnen_nutzt_bestehenden_deeplink(index_html):
    assert ('onOpenFahrzeug: (fid)=>{const idx=tabs.findIndex(t=>t.perm==="fahrzeuge");'
            'if(idx>=0&&hasPerm(curUser,"fahrzeuge")){window.__pendingFzSel=fid;setKat(idx);}}') in index_html


def test_imei_nur_fuer_admins(index_html):
    v = _flotte_view(index_html)
    assert "if(_istAdmin&&f.tracker_imei)_trk=" in v
    assert "const _istAdmin=!!(props.curUser&&props.curUser.role==='admin');" in v


# ── A55-Befunde (Handy, dunkel, v1048) ──────────────────────────────────────

def _panel_karte(src):
    a = src.index("const _panelKarte=h('div',")
    return src[a:src.index("\n", a)]


def test_karte_eigener_stapelkontext(index_html):
    """HOCH: Leaflet-Panes (z 400-1000) lagen am Handy UEBER dem Mehr-Sheet der App."""
    kopf = _panel_karte(index_html)
    assert "position:'relative',zIndex:0,isolation:'isolate'" in kopf


def test_umkehrprobe_stapelkontext(index_html):
    kopf = _panel_karte(index_html).replace("zIndex:0,isolation:'isolate',", "")
    assert "isolation:'isolate'" not in kopf


def test_handy_liste_ohne_leerflaeche(index_html):
    assert "listOpen?h('div',{style:{maxHeight:280,display:'flex',flexDirection:'column'}},_panelListe):null" in index_html
    assert "listOpen?h('div',{style:{height:280}},_panelListe)" not in index_html


def test_km_deutsches_format(node_exe, index_html):
    r = _run(node_exe, index_html, "[_fzKmDe(0,1),_fzKmDe(12.34,1),_fzKmDe(3.456,2),_fzKmDe(null,1),_fzKmDe('',1),_fzKmDe('x',1)]")
    assert r[0] == "0,0" and r[1] == "12,3" and r[2] == "3,46"
    assert r[3:] == ["", "", ""], "kein 0 aus null"


def test_summe_ohne_fahrten_strich(index_html):
    fb = _extract_fn(index_html, "FahrtenbuchView")
    assert "):'Summe: —')" in fb
    assert "'Summe: '+_n(sumKm" not in fb, "Umkehrprobe: Punkt-Format ist zurueck"
