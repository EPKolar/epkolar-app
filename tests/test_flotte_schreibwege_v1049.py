"""v1049 Flotte-Schreibwege (19.11.2026) - drei Schreib-/Rechenfehler im Fahrzeugmodul.

1. Fahrzeug -> "Werkstatt-/Prueftermine" -> "+ Termin" rief addTermin(sel). addTermin nimmt kein Argument und
   speichert das ANDERE Formular (terminForm: Typ Service, Datum heute, leere Beschreibung) nach fz_termine.
   -> Leer-Termin statt der Eingabe; ein unberuehrtes Formular schrieb trotzdem.
2. Sammel-Tanken "entfernen" (batchDel) filterte nur den Bildschirm-Zustand; batchSave hatte die Tankung schon per
   tankLog_add in fahrzeuge.tank_log geschrieben -> nach dem Neuladen war sie wieder da.
3. Monatsauswertung Tanken: eine Tankung mit km 0 (Batch/QR ohne Tacho) setzte den Monats-Startpunkt auf 0.

Verhaltenstests: die ECHTEN Handler (Klick-Ausdruck des Knopfs, addTermin, addPruefTermin, batchDel, upd, die
Monats-IIFE) werden aus index.html ausgeschnitten und in Node ausgefuehrt. Attrappen gibt es nur fuer die Umgebung
(SQ.push, setState, Toast, Bestaetigung) - jeweils mit der echten Signatur. Jede Pruefung hat eine Umkehrprobe:
derselbe Lauf gegen den ALTEN Code (im Speicher zurueckgesetzt) muss den Fehler zeigen.
"""
import json

from conftest import run_node_snippet, _extract_fn


# ── Ausschneiden ────────────────────────────────────────────────────────────

def _scan_to(src, i, stop_chars):
    """Ab i bis zum ersten Zeichen aus stop_chars auf Klammertiefe 0 (Strings/Kommentare uebersprungen)."""
    depth = 0
    n = len(src)
    while i < n:
        ch = src[i]
        if ch in "\"'`":
            q = ch
            i += 1
            while i < n and src[i] != q:
                if src[i] == "\\":
                    i += 1
                i += 1
        elif src.startswith("/*", i):
            i = src.index("*/", i) + 1
        elif src.startswith("//", i):
            i = src.index("\n", i) - 1
        elif ch in "([{":
            depth += 1
        elif ch in ")]}":
            if depth == 0 and ch in stop_chars:
                return i
            depth -= 1
        elif depth == 0 and ch in stop_chars:
            return i
        i += 1
    raise AssertionError("Ende nicht gefunden")


def _comp_const(src, name, required=True):
    """`const NAME=...;` aus dem FahrzeugView-Rumpf (erste Fundstelle nach function FahrzeugView)."""
    base = src.index("function FahrzeugView(")
    key = "const " + name + "="
    a = src.find(key, base)
    if a < 0:
        assert not required, name + " nicht gefunden"
        return ""
    e = _scan_to(src, a + len(key), ";")
    return src[a:e + 1]


def _knopf_klick(src):
    """onClick-Ausdruck des "+ Termin"-Knopfs im Abschnitt Werkstatt-/Prueftermine."""
    a = src.index("Werkstatt-/Prüftermine")
    j = src.index('"+ Termin" )', a)
    k = src.rindex("onClick: ", a, j) + len("onClick: ")
    e = _scan_to(src, k, ",")
    return src[k:e].strip()


def _top(src, name):
    fn = _extract_fn(src, name)
    assert fn, name + " nicht gefunden"
    return fn


def _opt_chain(src):
    a = src.index("function _optionalChain(ops)")
    e = _scan_to(src, src.index("{", a) + 1, "}")
    return src[a:e + 1]


def _flotte_basis(src):
    teile = [_top(src, "_fzZahl"), _top(src, "_fzDatumTeile"), _top(src, "_fzTankStats")]
    if "function _fzPruefTerminNeu(" in src:
        teile.append(_top(src, "_fzPruefTerminNeu"))
        a = src.index("var FZ_PRUEFTERMIN_ART=")
        teile.append(src[a:src.index(";", a) + 1])
    if "function _fzTankMonate(" in src:
        teile.append(_top(src, "_fzTankMonate"))
    return "\n".join(teile) + "\n"


def _node(node_exe, snip):
    return json.loads(run_node_snippet(node_exe, snip))


# ── Bug 1: "+ Termin" bei Werkstatt-/Prueftermine ───────────────────────────

ALT_KLICK = "()=>addTermin(sel)"


def _alt_termin_src(src):
    neu = _knopf_klick(src)
    assert neu != ALT_KLICK, "Knopf ist noch der alte"
    a = src.index("Werkstatt-/Prüftermine")
    j = src.index('"+ Termin" )', a)
    k = src.rindex("onClick: " + neu, a, j)
    return src[:k] + "onClick: " + ALT_KLICK + src[k + len("onClick: " + neu):]


def _termin_lauf(node_exe, src, art, datum, beschr, admin=True):
    umgebung = (
        "var SQ={_q:[],push:function(action){SQ._q.push(JSON.parse(JSON.stringify(action)));return Promise.resolve();}};\n"
        "var fahrzeuge=[{id:'fz1',kennzeichen:'TU-1',termine:[{id:'alt',art:'pickerl',datum:'2026-04-15',beschreibung:'Bestand',erledigt:false,by:'X'}]},{id:'fz2',termine:[]}];\n"
        "function setFahrzeuge(v){fahrzeuge=(typeof v==='function')?v(fahrzeuge):v;}\n"
        "var fzTermine=[];function setFzTermine(v){fzTermine=(typeof v==='function')?v(fzTermine):v;}\n"
        "var sel='fz1',isVAdmin=" + ("true" if admin else "false") + ",curUser={name:'Pinger Leo',role:'admin'};\n"
        "var terminForm={typ:'Service',beschreibung:'',datum:'2026-11-19',erledigt:0};function setTerminForm(v){terminForm=(typeof v==='function')?v(terminForm):v;}\n"
        "var showAddTermin=false;function setShowAddTermin(v){showAddTermin=v;}\n"
        "function td2(){return '2026-11-19';}\n"
        "var _u=0;function uid(){_u++;return 'id'+_u;}\n"
        "var tArt=" + json.dumps(art) + ",tDatum=" + json.dumps(datum) + ",tBeschr=" + json.dumps(beschr) + ";\n"
        "function setTArt(v){tArt=v;}function setTDatum(v){tDatum=v;}function setTBeschr(v){tBeschr=v;}\n"
        "var toasts=[];var window={__toast:function(m,k){toasts.push(String(m));}};\n"
    )
    handler = "\n".join(x for x in (
        _comp_const(src, "upd"),
        _comp_const(src, "addTermin"),
        _comp_const(src, "addPruefTermin", required=False),
    ) if x)
    snip = (_opt_chain(src) + "\n" + _flotte_basis(src) + umgebung + handler + "\n"
            "var klick=(" + _knopf_klick(src) + ");klick();\n"
            "process.stdout.write(JSON.stringify({q:SQ._q,fz:fahrzeuge,fzTermine:fzTermine,tArt:tArt,tDatum:tDatum,tBeschr:tBeschr,toasts:toasts}));")
    return _node(node_exe, snip)


def _pruef_eingabe_gespeichert(r):
    """Probleme (leer = ok), wenn die Eingabe reifen/2026-12-03/'Winterreifen montieren' gespeichert sein soll."""
    p = []
    if len(r["q"]) != 1:
        p.append("Schreibvorgaenge: %d" % len(r["q"]))
        return p
    a = r["q"][0]
    if a.get("url") != "/api/fahrzeuge/fz1" or a.get("method") != "PUT":
        p.append("falscher Weg: %s %s" % (a.get("method"), a.get("url")))
        return p
    if sorted(a["body"].keys()) != ["termine"]:
        p.append("Body nicht spaltengenau: %s" % sorted(a["body"].keys()))
    neu = [t for t in a["body"].get("termine", []) if t.get("id") != "alt"]
    if len(neu) != 1:
        p.append("neue Termine: %d" % len(neu))
        return p
    t = neu[0]
    if (t.get("art"), t.get("datum"), t.get("beschreibung"), t.get("erledigt"), t.get("by")) != \
            ("reifen", "2026-12-03", "Winterreifen montieren", False, "Pinger Leo"):
        p.append("Inhalt falsch: %r" % t)
    if not t.get("id"):
        p.append("keine id")
    return p


def test_termin_speichert_genau_die_eingabe(node_exe, index_html):
    r = _termin_lauf(node_exe, index_html, "reifen", "2026-12-03", "Winterreifen montieren")
    assert _pruef_eingabe_gespeichert(r) == []
    # Bestand bleibt, das richtige Fahrzeug, lokaler Zustand = gesendeter Zustand
    fz1 = [f for f in r["fz"] if f["id"] == "fz1"][0]
    assert [t["id"] for t in fz1["termine"]].count("alt") == 1 and len(fz1["termine"]) == 2
    assert fz1["termine"] == r["q"][0]["body"]["termine"]
    assert [f for f in r["fz"] if f["id"] == "fz2"][0]["termine"] == []
    # nichts in die fremde Liste (fz_termine / Service-Termine)
    assert r["fzTermine"] == []
    # Formular zurueckgesetzt
    assert (r["tArt"], r["tDatum"], r["tBeschr"]) == ("service", "", "")


def test_termin_umkehrprobe_alter_knopf_schreibt_leer_termin(node_exe, index_html):
    r = _termin_lauf(node_exe, _alt_termin_src(index_html), "reifen", "2026-12-03", "Winterreifen montieren")
    assert _pruef_eingabe_gespeichert(r) != [], "Umkehrprobe: der alte Knopf muss den Fehler zeigen"
    # genau der gemeldete Schaden: Service, heute, leer, nach fz_termine
    a = r["q"][0]
    assert a["url"] == "/api/fz-termine/fz1" and a["method"] == "POST"
    assert (a["body"]["typ"], a["body"]["datum"], a["body"]["beschreibung"]) == ("Service", "2026-11-19", "")


def test_termin_leeres_formular_schreibt_nie(node_exe, index_html):
    for art, datum, beschr in (("service", "", ""), ("service", "", "Text ohne Datum"),
                               ("reifen", "0000-00-00", "x"), ("reifen", "quatsch", "x"),
                               ("erfunden", "2026-12-03", "x")):
        r = _termin_lauf(node_exe, index_html, art, datum, beschr)
        assert r["q"] == [], (art, datum, beschr)
        fz1 = [f for f in r["fz"] if f["id"] == "fz1"][0]
        assert len(fz1["termine"]) == 1 and r["fzTermine"] == []
        assert any("⚠️" in t for t in r["toasts"])
    # ohne Admin-Recht ebenfalls nichts
    r = _termin_lauf(node_exe, index_html, "reifen", "2026-12-03", "x", admin=False)
    assert r["q"] == []


def test_termin_umkehrprobe_leeres_formular_schrieb_frueher(node_exe, index_html):
    r = _termin_lauf(node_exe, _alt_termin_src(index_html), "service", "", "")
    assert len(r["q"]) == 1, "Umkehrprobe: der alte Knopf schrieb auch bei leerem Formular"


def test_termin_leere_beschreibung_erlaubt(node_exe, index_html):
    r = _termin_lauf(node_exe, index_html, "pickerl", "2027-01-10", "   ")
    assert len(r["q"]) == 1
    neu = [t for t in r["q"][0]["body"]["termine"] if t["id"] != "alt"][0]
    assert (neu["art"], neu["datum"], neu["beschreibung"]) == ("pickerl", "2027-01-10", "")


def test_termin_knopf_ohne_datum_gesperrt(index_html):
    a = index_html.index("Werkstatt-/Prüftermine")
    j = index_html.index('"+ Termin" )', a)
    knopf = index_html[index_html.rindex("React.createElement('button'", a, j):j]
    assert "disabled: !tDatum" in knopf


# ── Bug 2: Sammel-Tanken "entfernen" ────────────────────────────────────────

ALT_BATCHDEL = (
    "const batchDel=(rowId)=>{\n"
    "    const row=batchRows.find(r=>r.id===rowId);if(!row)return;\n"
    "    // Remove from fahrzeuge tankLog\n"
    "    setFahrzeuge(p=>p.map(f=>f.id===row.fzId?{...f,tankLog:(f.tankLog||[]).filter(t=>t.id!==rowId)}:f));\n"
    "    setBatchRows(p=>p.filter(r=>r.id!==rowId));\n"
    "    _optionalChain([window, 'access', _681 => _681.__toast, 'optionalCall', _682 => _682(\"🗑️ Tankung entfernt\")]);\n"
    "  };"
)


def _alt_batch_src(src):
    neu = _comp_const(src, "batchDel")
    assert neu != ALT_BATCHDEL
    assert src.count(neu) == 1
    return src.replace(neu, ALT_BATCHDEL)


def _batch_lauf(node_exe, src, bestaetigt=True):
    umgebung = (
        "var SQ={_q:[],push:function(action){SQ._q.push(JSON.parse(JSON.stringify(action)));return Promise.resolve();}};\n"
        "var fahrzeuge=[{id:'fz1',kmStand:100500,tankLog:["
        "{id:'tkB',datum:'2026-11-19',liter:40,preis:62,km:0,foto:'',kontrolliert:false,kontrolliert_von:null,kontrolliert_am:null},"
        "{id:'tkA',datum:'2026-11-01',liter:35,preis:55,km:100500,foto:'',kontrolliert:true,kontrolliert_von:'B',kontrolliert_am:'2026-11-02'}]},"
        "{id:'fz2',tankLog:[{id:'tkB',datum:'2026-11-19',liter:1,preis:1,km:1}]}];\n"
        "function setFahrzeuge(v){fahrzeuge=(typeof v==='function')?v(fahrzeuge):v;}\n"
        "var batchRows=[{id:'tkB',fzId:'fz1',kennzeichen:'TU-1',datum:'2026-11-19',liter:40,preis:62,km:0}];\n"
        "function setBatchRows(v){batchRows=(typeof v==='function')?v(batchRows):v;}\n"
        "var gefragt=[];function _confirmModal(msg,opts){gefragt.push(String(msg));return Promise.resolve(" + ("true" if bestaetigt else "false") + ");}\n"
        "var toasts=[];var window={__toast:function(m,k){toasts.push(String(m));}};\n"
    )
    snip = (_opt_chain(src) + "\n" + umgebung + _comp_const(src, "upd") + "\n" + _comp_const(src, "batchDel") + "\n"
            "Promise.resolve(batchDel('tkB')).then(function(){process.stdout.write(JSON.stringify({q:SQ._q,fz:fahrzeuge,rows:batchRows,gefragt:gefragt}));});")
    return _node(node_exe, snip)


def _pruef_server_loeschung(r):
    p = []
    if len(r["q"]) != 1:
        return ["Schreibvorgaenge: %d" % len(r["q"])]
    a = r["q"][0]
    if (a.get("url"), a.get("method")) != ("/api/fahrzeuge/fz1", "PUT"):
        p.append("falscher Weg: %s %s" % (a.get("method"), a.get("url")))
    if sorted(a.get("body", {}).keys()) != ["tankLog"]:
        p.append("Body nicht spaltengenau: %s" % sorted(a.get("body", {}).keys()))
    ids = [t.get("id") for t in a.get("body", {}).get("tankLog", [])]
    if ids != ["tkA"]:
        p.append("tank_log danach: %r" % ids)
    return p


def test_batch_entfernen_loescht_auf_dem_server(node_exe, index_html):
    r = _batch_lauf(node_exe, index_html)
    assert _pruef_server_loeschung(r) == []
    # der verbleibende Eintrag ist unveraendert (Kontrolle bleibt), anderes Fahrzeug unberuehrt
    tka = r["q"][0]["body"]["tankLog"][0]
    assert tka["kontrolliert"] is True and tka["kontrolliert_von"] == "B" and tka["km"] == 100500
    fz1 = [f for f in r["fz"] if f["id"] == "fz1"][0]
    assert [t["id"] for t in fz1["tankLog"]] == ["tkA"]
    assert [f for f in r["fz"] if f["id"] == "fz2"][0]["tankLog"][0]["id"] == "tkB"
    assert r["rows"] == [] and len(r["gefragt"]) == 1


def test_batch_umkehrprobe_alter_code_loescht_nur_lokal(node_exe, index_html):
    r = _batch_lauf(node_exe, _alt_batch_src(index_html))
    assert _pruef_server_loeschung(r) != [], "Umkehrprobe: der alte Code muss den Fehler zeigen"
    assert r["q"] == [], "alter Code schrieb nichts - deshalb kam die Tankung nach dem Neuladen zurueck"
    assert r["rows"] == []


def test_batch_abbrechen_schreibt_nichts(node_exe, index_html):
    r = _batch_lauf(node_exe, index_html, bestaetigt=False)
    assert r["q"] == [] and len(r["rows"]) == 1
    assert len([f for f in r["fz"] if f["id"] == "fz1"][0]["tankLog"]) == 2


def test_batch_weg_ist_der_tanklog_weg_von_addtank(index_html):
    """Kein neuer Schreibweg: derselbe Diff-PUT der tankLog-Spalte wie beim Tank-Dialog (addTank)."""
    assert "},u=>({tankLog:u.tankLog,kmStand:u.kmStand}));" in index_html
    assert "u=>({tankLog:u.tankLog})" in _comp_const(index_html, "batchDel")


# ── Bug 3: Monatsauswertung Tanken ──────────────────────────────────────────

ALT_MONAT_IIFE = (
    '(()=>{\n'
    '            const byMonth={};(selFz.tankLog||[]).forEach(t=>{const m=(t.datum||"").slice(0,7);if(!m)return;if(!byMonth[m])byMonth[m]={liter:0,kosten:0,cnt:0,minKm:Infinity,maxKm:0,tanks:[]};byMonth[m].liter+=t.liter||0;byMonth[m].kosten+=t.preis||0;byMonth[m].cnt++;if(t.km<byMonth[m].minKm)byMonth[m].minKm=t.km;if(t.km>byMonth[m].maxKm)byMonth[m].maxKm=t.km;byMonth[m].tanks.push({km:t.km,liter:t.liter||0});});/* v3.9.600 #13: tanks[] je Monat fuer slice(1)-Konsumrechnung */\n'
    '            const months=Object.keys(byMonth).sort().reverse();\n'
    '            return (React.createElement(\'div\', { style: {overflowX:"auto"}}, React.createElement(\'table\', { style: {width:"100%",borderCollapse:"collapse",fontSize:12}}, React.createElement(\'thead\', {}, React.createElement(\'tr\', {}, React.createElement(\'th\', { style: thS()}, "Monat"), React.createElement(\'th\', { style: thS()}, "Tankungen"), React.createElement(\'th\', { style: thS()}, "Liter ges." ), React.createElement(\'th\', { style: thS()}, "Kosten ges." ), React.createElement(\'th\', { style: thS()}, "Ø €/L" ), React.createElement(\'th\', { style: thS()}, "km gefahren" ), React.createElement(\'th\', { style: thS()}, "Ø L/100km" )))\n'
    '            , React.createElement(\'tbody\', {}, months.map(m=>{const d=byMonth[m];const kmDiff=d.maxKm>d.minKm?d.maxKm-d.minKm:0;/* v3.9.600 #13 Bug-Hunt: Verbrauch wie "Ø Verbrauch" (:21805) berechnen — erste Monats-Tankung (bei minKm) NICHT mitzaehlen (ihr Sprit wurde VOR minKm/im Vormonat verfahren), sonst ~Verdopplung + faelschlich rote Ampel. "Liter ges."-Spalte bleibt bewusst d.liter (alle Tankungen). */const _v600S=[...(d.tanks||[])].sort((a,b)=>a.km-b.km);const _v600ConsL=_v600S.slice(1).reduce((s,x)=>s+(x.liter||0),0);const avg=(kmDiff>0&&_v600S.length>1)?_n((_v600ConsL/kmDiff*100),1):"—";const avgPrice=d.liter>0?_n((d.kosten/d.liter),3):"—";const moLabel=m.split("-")[1]+"/"+m.split("-")[0];\n'
    '              return (React.createElement(\'tr\', { key: m}, React.createElement(\'td\', { style: {...tdSt(),fontWeight:700}}, moLabel), React.createElement(\'td\', { style: {...tdSt(),textAlign:"center"}}, d.cnt), React.createElement(\'td\', { style: {...tdSt(),textAlign:"right",fontFamily:"monospace"}}, _n(d.liter,1), " L" ), React.createElement(\'td\', { style: {...tdSt(),textAlign:"right",fontFamily:"monospace",fontWeight:600}}, fmt$(d.kosten) ), React.createElement(\'td\', { style: {...tdSt(),textAlign:"right"}}, avgPrice), React.createElement(\'td\', { style: {...tdSt(),textAlign:"right",fontFamily:"monospace"}}, kmDiff>0?kmDiff.toLocaleString("de-AT")+" km":"—"), React.createElement(\'td\', { style: {...tdSt(),textAlign:"center",fontWeight:700,color:parseFloat(avg)>12?"#ef4444":parseFloat(avg)>8?"#f97316":_okG("#22c55e")}}, avg)));\n'
    '            })))));\n'
    '          })()'
)


def _monat_iife(src):
    a = src.index('"Monatsauswertung Tanken"')
    s = src.index("(()=>{", a)
    e = src.index("})()", s) + len("})()")
    return s, e


def _alt_monat_src(src):
    s, e = _monat_iife(src)
    assert src[s:e] != ALT_MONAT_IIFE
    return src[:s] + ALT_MONAT_IIFE + src[e:]


TANKLOG = (
    "["
    "{id:'b1',datum:'2026-10-20',liter:40,preis:60,km:0},"          # Batch ohne Tacho
    "{id:'a1',datum:'2026-10-05',liter:30,preis:48,km:100000},"
    "{id:'a2',datum:'2026-10-25',liter:'35',preis:'56',km:100500},"  # Textwerte (Altbestand)
    "{id:'n1',datum:'2026-11-02',liter:20,preis:31,km:0}"           # Monat nur ohne km
    "]"
)


def _monat_lauf(node_exe, src):
    s, e = _monat_iife(src)
    snip = (
        _flotte_basis(src) + _top(src, "_n") + "\n"
        "var fmt$=function(n){return 'EUR '+Number(n).toFixed(2);};\n"
        "var React={createElement:function(t,p){return {t:t,c:Array.prototype.slice.call(arguments,2)};}};\n"
        "function tdSt(){return {};}function thS(){return {};}function _okG(h){return h;}var V={dm:'#999'};\n"
        "var selFz={id:'fz1',tankLog:" + TANKLOG + "};\n"
        "var baum=" + src[s:e] + ";\n"
        "function txt(n){if(n===null||n===undefined||n===false)return '';if(typeof n!=='object')return String(n);"
        "if(Array.isArray(n))return n.map(txt).join('');return (n.c||[]).map(txt).join('');}\n"
        "function finde(n,t){if(!n||typeof n!=='object')return null;if(Array.isArray(n)){for(var i=0;i<n.length;i++){var x=finde(n[i],t);if(x)return x;}return null;}"
        "if(n.t===t)return n;return finde(n.c,t);}\n"
        "var tb=finde(baum,'tbody');var zeilen=[];(tb.c||[]).forEach(function(c){(Array.isArray(c)?c:[c]).forEach(function(tr){"
        "zeilen.push((tr.c||[]).map(txt));});});\n"
        "process.stdout.write(JSON.stringify(zeilen));"
    )
    return _node(node_exe, snip)


def _pruef_monate(z):
    """Erwartet: Monat, Tankungen, Liter, Kosten, Ø€/L, km gefahren, ØL/100km"""
    p = []
    if len(z) != 2:
        return ["Zeilen: %r" % z]
    nov, okt = z
    if okt[0] != "10/2026" or okt[1] != "3":
        p.append("Oktober Kopf: %r" % okt[:2])
    if okt[2] != "105.0 L":
        p.append("Oktober Liter (alle Tankungen, Text addiert): %r" % okt[2])
    if okt[3] != "EUR 164.00":
        p.append("Oktober Kosten: %r" % okt[3])
    if okt[5] != "500 km":
        p.append("Oktober km gefahren: %r" % okt[5])
    if okt[6] != "7.0":
        p.append("Oktober Verbrauch (35 L / 500 km): %r" % okt[6])
    if nov[0] != "11/2026" or nov[2] != "20.0 L" or nov[3] != "EUR 31.00":
        p.append("November Liter/Kosten: %r" % nov[:4])
    if nov[5] != "—" or nov[6] != "—":
        p.append("November ohne km muss '—' zeigen: %r" % nov[5:])
    return p


def test_monat_km0_verzerrt_nicht(node_exe, index_html):
    assert _pruef_monate(_monat_lauf(node_exe, index_html)) == []


def test_monat_umkehrprobe_alter_rechner_verzerrt(node_exe, index_html):
    p = _pruef_monate(_monat_lauf(node_exe, _alt_monat_src(index_html)))
    assert p != [], "Umkehrprobe: der alte Rechner muss den Fehler zeigen"
    assert any("km gefahren" in x for x in p) and any("Verbrauch" in x for x in p), p


def test_tank_monate_helfer_direkt(node_exe, index_html):
    snip = (_flotte_basis(index_html) + "var f={tankLog:" + TANKLOG + ".concat([null,{datum:'0000-00-00',liter:9,km:5},{datum:'2026-10-30',liter:null,preis:null,km:null}])};\n"
            "process.stdout.write(JSON.stringify({r:_fzTankMonate(f),leer:_fzTankMonate(null),kaputt:_fzTankMonate({tankLog:'x'})}));")
    r = _node(node_exe, snip)
    assert r["leer"] == [] and r["kaputt"] == []
    okt = [m for m in r["r"] if m["monat"] == "2026-10"][0]
    assert okt["anzahl"] == 4 and okt["liter"] == 105 and okt["euro"] == 164
    assert okt["strecke"] == 500 and abs(okt["l100"] - 7.0) < 1e-9
    assert [m["monat"] for m in r["r"]] == ["2026-11", "2026-10"]
