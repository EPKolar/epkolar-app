"""v1049 Flotte-Ausbau (19.11.2026) - Fristen, Kosten/Verbrauch, Fahrzeugakte, Fahrer-Klassen, CSV.

Analyse: docs/flotte/AUSBAU_2026-11-19.md. Alles hier ist NUR LESEN.

Verhaltenstests: die ECHTEN Funktionen werden aus index.html ausgeschnitten und in Node ausgefuehrt
(keine Attrappen). Jede Rechnung hat eine Umkehrprobe gegen die beiden Fallen, die in der Flotte schon
gebissen haben: Number(null)===0 und new Date(null) = 1.1.1970 erfinden Werte ("0 km/h", "inaktiv seit 1970").
"""
import json
import re
import subprocess

from conftest import run_node_snippet, _extract_fn

TZ = "process.env.TZ='Europe/Vienna';"
VARS = ("FZ_FRIST_RANG", "FZ_FRIST_ART", "FZ_FRIST_TXT")
BASIS = ("_fzZahl", "_fzDatumTeile", "_fzTagKey", "_fzTageBis")


def _block(index_html):
    a = index_html.index("//@FLOTTE-AUSBAU-START")
    b = index_html.index("//@FLOTTE-AUSBAU-END")
    return index_html[a:b]


def _zeitkonst(index_html):
    """Die echten TIME_*-Konstanten aus index.html (an die Quelle gebunden, keine Attrappe)."""
    z = re.findall(r"^const TIME_\w+=[^;\r\n]*;", index_html, re.M)
    assert any(x.startswith("const TIME_DAY=") for x in z), "TIME_DAY fehlt"
    return nl_join(z)


def nl_join(z):
    return "\n".join(z)


def _harness(index_html, *names):
    teile = [TZ, _zeitkonst(index_html)]
    for n in names:
        if n in VARS:
            m = re.search(r"^var " + n + r"=\{.*?\};\r?$", index_html, re.M)
            assert m, n + " nicht gefunden"
            teile.append(m.group(0).rstrip("\r"))
            continue
        fn = _extract_fn(index_html, n)
        assert fn, n + " nicht gefunden"
        teile.append(fn)
    return "\n".join(teile) + "\n"


def _eval(node_exe, index_html, ausdruck, *names):
    snip = _harness(index_html, *names) + "process.stdout.write(JSON.stringify(" + ausdruck + "));"
    return json.loads(run_node_snippet(node_exe, snip))


# fester Bezugspunkt: Do 19.11.2026 10:00 Wiener Zeit (im Snippet lokal gebaut)
NOW = "new Date(2026,10,19,10,0,0).getTime()"


# ── Grundbausteine + Umkehrproben der beiden Fallen ─────────────────────────

def test_zahl_null_ist_nan_nicht_null(node_exe, index_html):
    r = _eval(node_exe, index_html,
              "{falle:Number(null)===0,"
              "nul:isNaN(_fzZahl(null)),leer:isNaN(_fzZahl('')),undef:isNaN(_fzZahl(undefined)),"
              "txt:isNaN(_fzZahl('abc')),wahr:isNaN(_fzZahl(true)),"
              "komma:_fzZahl('52,3'),tausend:_fzZahl('1.234,5'),punkt:_fzZahl('52.3'),zahl:_fzZahl(7),null0:_fzZahl(0)}",
              "_fzZahl")
    assert r["falle"] is True, "Umkehrprobe: die Falle Number(null)===0 existiert"
    assert r["nul"] and r["leer"] and r["undef"] and r["txt"] and r["wahr"]
    assert r["komma"] == 52.3 and r["tausend"] == 1234.5 and r["punkt"] == 52.3
    assert r["zahl"] == 7 and r["null0"] == 0


def test_tagkey_null_ist_leer_nicht_1970(node_exe, index_html):
    r = _eval(node_exe, index_html,
              "{falle:new Date(null).getFullYear(),k:_fzTagKey(null),u:_fzTagKey(undefined),x:_fzTagKey('quatsch'),"
              "lokal:_fzTagKey(new Date(2026,10,19,0,30).getTime())}",
              "_fzTagKey")
    assert r["falle"] == 1970, "Umkehrprobe: new Date(null) ist 1970"
    assert r["k"] == "" and r["u"] == "" and r["x"] == ""
    # 00:30 Ortszeit = 23:30 UTC des Vortags - der Schluessel muss LOKAL bleiben
    assert r["lokal"] == "2026-11-19"


def test_tage_bis_lokal_und_sommerzeitfest(node_exe, index_html):
    r = _eval(node_exe, index_html,
              "{heute:_fzTageBis('2026-11-19'," + NOW + "),morgen:_fzTageBis('2026-11-20'," + NOW + "),"
              "gestern:_fzTageBis('2026-11-18'," + NOW + "),"
              "dst:_fzTageBis('2026-03-30',new Date(2026,2,28,23,30).getTime()),"
              "epoch:_fzTageBis('1970-01-01'," + NOW + "),nullen:_fzTageBis('0000-00-00'," + NOW + "),"
              "feb31:_fzTageBis('2026-02-31'," + NOW + "),nulldatum:_fzTageBis(null," + NOW + "),"
              "nullnow:_fzTageBis('2026-11-19',null)}",
              *BASIS)
    assert (r["heute"], r["morgen"], r["gestern"]) == (0, 1, -1)
    assert r["dst"] == 2, "Sommerzeit-Umstellung verschiebt die Tageszahl"
    for k in ("epoch", "nullen", "feb31", "nulldatum", "nullnow"):
        assert r[k] is None, k + " muss NaN sein (JSON null), kein erfundener Wert"


# ── Pickerl: dieselbe Regel wie window._pickerlStatus/_pickerlFrist ──────────

def _window_pickerl(index_html):
    teile = []
    for n in ("_pickerlStatus", "_pickerlFrist"):
        m = re.search(r"^window\." + n + r"=.*$", index_html, re.M)
        assert m, n
        teile.append(m.group(0).rstrip("\r"))
    return "var window={};\n" + "\n".join(teile) + "\n"


def test_pickerl_stufe_gleich_wie_bestandsregel(node_exe, index_html):
    """Gegen die ECHTEN Bestandsfunktionen mit dem echten 'jetzt' - kein Nachbau als Vergleich."""
    snip = (TZ + _window_pickerl(index_html) + _harness(index_html, *BASIS, "_fzPickerlStufe")
            + "var now=Date.now();var out=[];"
            "[-400,-200,-130,-100,-60,-40,-1,0,1,2,29,30,31,45,400].forEach(function(o){"
            "var d=new Date();d.setHours(12,0,0,0);d.setDate(d.getDate()+o);var iso=_fzTagKey(d.getTime());"
            "var st=window._pickerlStatus(iso);var fr=window._pickerlFrist(iso)||{};"
            "var alt=st==='ok'?'ok':st==='warn'?'bald':(fr.st==='toleranz'?'toleranz':'ueberfaellig');"
            "var neu=_fzPickerlStufe(iso,now);out.push([o,alt,neu.stufe,fr.tolBis||null,neu.tolBis]);});"
            "process.stdout.write(JSON.stringify(out));")
    for o, alt, neu, tol_alt, tol_neu in json.loads(run_node_snippet(node_exe, snip)):
        assert alt == neu, "Offset %d: Bestand %s, neu %s" % (o, alt, neu)
        assert tol_alt == tol_neu, "Offset %d: Toleranz %s vs %s" % (o, tol_alt, tol_neu)


def test_pickerl_toleranz_fest(node_exe, index_html):
    r = _eval(node_exe, index_html,
              "{tol:_fzPickerlStufe('2026-08-10'," + NOW + "),weg:_fzPickerlStufe('2026-06-15'," + NOW + "),"
              "muell:_fzPickerlStufe('1970-01-01'," + NOW + ")}",
              *BASIS, "_fzPickerlStufe")
    assert r["tol"]["stufe"] == "toleranz" and r["tol"]["tolBis"] == "2026-12-31"
    assert r["weg"]["stufe"] == "ueberfaellig" and r["weg"]["tolBis"] == "2026-10-31"
    assert r["muell"] is None, "1970 ist Datenmuell, keine 20.000 Tage ueberfaellige Frist"


# ── Fristen ueber den Fuhrpark ───────────────────────────────────────────────

FZ = [
    {"id": "a", "kennzeichen": "TU-1", "pickerl": "2026-06-15", "naechstService": "2026-11-19"},
    {"id": "b", "kennzeichen": "TU-2", "pickerl": "", "naechstService": "2027-05-01",
     "vignette_typ": "Jahresvignette", "vignette_bis": "2026-12-01",
     "termine": [{"art": "reifen", "datum": "2026-11-25", "beschreibung": "Winterreifen"},
                 {"art": "service", "datum": "2026-11-01", "erledigt": True}]},
    {"id": "c", "kennzeichen": "TU-3", "status": "stillgelegt", "pickerl": "2020-01-01"},
    {"id": "d", "kennzeichen": "TU-4", "pickerl": "0000-00-00", "naechstService": None},
]
TERMINE = [
    {"fahrzeug_id": "b", "typ": "Service", "datum": "2026-11-10", "erledigt": 0},
    {"fahrzeug_id": "b", "typ": "UVV-Prüfung", "datum": "2026-11-12", "erledigt": "1"},
    {"fahrzeug_id": "a", "typ": "Pickerl/§57a", "datum": "2026-11-12", "erledigt": True},
    {"fahrzeug_id": "zz", "typ": "Service", "datum": "2026-11-20", "erledigt": 0},
]
FRIST_FNS = BASIS + ("_fzPickerlStufe", "_fzTerminErledigt", "_fzFristen") + VARS


def test_fristen_ueber_fuhrpark(node_exe, index_html):
    r = _eval(node_exe, index_html,
              "_fzFristen(" + json.dumps(FZ) + "," + NOW + "," + json.dumps(TERMINE) + ")"
              ".map(function(x){return [x.kennzeichen,x.art,x.stufe,isNaN(x.tage)?null:x.tage,x.hinweis];})",
              *FRIST_FNS)
    kz = {x[0] for x in r}
    assert "TU-3" not in kz, "stillgelegt gehoert nicht in die Fristen"
    zeilen = {(x[0], x[1], x[2]) for x in r}
    assert ("TU-1", "pickerl", "ueberfaellig") in zeilen
    assert ("TU-1", "service", "ueberfaellig") in zeilen, "Service heute = faellig (wie _fzServiceFaellig)"
    assert ("TU-2", "pickerl", "fehlt") in zeilen
    assert ("TU-2", "vignette", "bald") in zeilen
    assert ("TU-2", "termin", "bald") in zeilen                       # Winterreifen (JSON am Fahrzeug)
    assert ("TU-2", "termin", "ueberfaellig") in zeilen              # fz_termine 10.11. offen
    assert ("TU-4", "pickerl", "ungueltig") in zeilen, "0000-00-00 = Datum pruefen, nicht 'ueberfaellig seit Jahr 0'"
    assert ("TU-4", "service", "fehlt") in zeilen, "naechstService null = nicht erfasst (kein 1970)"
    termine = [x for x in r if x[1] == "termin"]
    assert len(termine) == 2, "erledigte (true/'1') und fremde fahrzeug_id duerfen nicht erscheinen: %r" % termine
    # Reihenfolge: dringendste zuerst
    rang = {"ueberfaellig": 0, "toleranz": 1, "bald": 2, "ok": 3, "fehlt": 4, "ungueltig": 4}
    rs = [rang[x[2]] for x in r]
    assert rs == sorted(rs)


def test_service_zaehlung_gleich_wie_kachel(node_exe, index_html):
    """Die Fristen-Ansicht darf nicht eine andere Zahl 'Service faellig' nennen als die Kachel."""
    serv = _extract_fn(index_html, "_fzServiceFaellig")
    assert serv
    fz = [{"id": str(i), "kennzeichen": "K" + str(i), "naechstService": d}
          for i, d in enumerate(["2026-11-18", "2026-11-19", "2026-11-20", "2025-01-01", "2027-01-01", ""])]
    # gegen das echte 'jetzt', weil _fzServiceFaellig new Date() liest
    snip = (_harness(index_html, *FRIST_FNS) + serv + "\n"
            "var fz=" + json.dumps(fz) + ";var t=new Date();function iso(o){var d=new Date();d.setHours(12,0,0,0);d.setDate(d.getDate()+o);return _fzTagKey(d.getTime());}"
            "fz[0].naechstService=iso(-1);fz[1].naechstService=iso(0);fz[2].naechstService=iso(1);"
            "var kachel=fz.filter(_fzServiceFaellig).length;"
            "var neu=_fzFristen(fz,Date.now(),[]).filter(function(x){return x.art==='service'&&x.stufe==='ueberfaellig';}).length;"
            "process.stdout.write(JSON.stringify([kachel,neu]));")
    kachel, neu = json.loads(run_node_snippet(node_exe, snip))
    assert kachel == neu == 3


# ── Tankbuch: Kosten und Verbrauch ───────────────────────────────────────────

TANK_FNS = BASIS + ("_fzTankStats",)


def test_tankstats_robust(node_exe, index_html):
    f = {"tankLog": [
        {"liter": "50,0", "preis": "80", "km": 10000, "datum": "2026-10-01"},
        {"liter": 40, "preis": 64, "km": 10500, "datum": "2026-10-15"},
        {"liter": 30, "preis": None, "km": 0, "datum": "2026-11-01"},
        {"liter": None, "preis": 10, "km": 11000, "datum": "2026-11-02"},
        None,
    ]}
    r = _eval(node_exe, index_html, "_fzTankStats(" + json.dumps(f) + "," + NOW + ")", *TANK_FNS)
    assert r["anzahl"] == 3, "Eintrag ohne Liter zaehlt nicht als Tankung"
    assert r["liter"] == 120 and r["euro"] == 144
    assert r["ohneKm"] == 1 and r["ohnePreis"] == 1
    assert abs(r["l100"] - 8.0) < 1e-9, "40 L auf 500 km; erste Tankung zaehlt nicht"
    assert abs(r["euroKm"] - 64 / 500) < 1e-9
    assert r["plausibel"] is True
    assert r["letzte"] == "2026-11-01"
    assert abs(r["euroProL"] - 144 / 90) < 1e-9, "Literpreis nur ueber Tankungen MIT Preis"
    # Oktober+November im 12-Monats-Fenster, Buch beginnt im Oktober -> 2 Monate
    assert r["euro12"] == 144 and abs(r["euroMonat"] - 72) < 1e-9


def test_umkehrprobe_alter_verbrauch_mit_km_null(node_exe, index_html):
    """Die alte Inline-Rechnung nahm km 0 (Batch/QR ohne Tacho) als Startpunkt - der neue Rechner nicht."""
    log = [{"liter": 30, "km": 0}, {"liter": 50, "km": 10000}, {"liter": 40, "km": 10500}]
    alt = ("(function(){const sorted=[..." + json.dumps(log) + "].sort((a,b)=>a.km-b.km);const diff=sorted[sorted.length-1].km-sorted[0].km;"
           "const lit=sorted.slice(1).reduce((s,t)=>s+t.liter,0);return lit/diff*100;})()")
    r = _eval(node_exe, index_html,
              "{alt:" + alt + ",neu:_fzTankStats({tankLog:" + json.dumps(log) + "}," + NOW + ").l100}", *TANK_FNS)
    assert r["alt"] < 1, "Umkehrprobe: die alte Rechnung liefert den falschen Wert (<1 L/100 km)"
    assert abs(r["neu"] - 8.0) < 1e-9
    assert "const sorted=[...(selFz.tankLog||[])].sort((a,b)=>a.km-b.km)" not in index_html, \
        "die alte Ø-Verbrauch-Rechnung steht noch im Tankprotokoll"
    assert "const _ts=_fzTankStats(selFz,Date.now());" in index_html


def test_tankstats_ohne_preis_kein_erfundener_monatswert(node_exe, index_html):
    r = _eval(node_exe, index_html,
              "_fzTankStats({tankLog:[{liter:40,km:100,datum:'2026-11-01'},{liter:40,km:600,datum:'2026-11-10'}]}," + NOW + ")",
              *TANK_FNS)
    assert r["euroMonat"] is None, "ohne einen Preis im Fenster: unbekannt (NaN), nicht 0 €/Monat"
    assert r["euroKm"] is None and r["euroProL"] is None
    assert abs(r["l100"] - 8.0) < 1e-9


def test_tankstats_unplausibel_und_zu_wenig(node_exe, index_html):
    r = _eval(node_exe, index_html,
              "{tipp:_fzTankStats({tankLog:[{liter:50,km:1000},{liter:100,km:1050}]}," + NOW + "),"
              "eins:_fzTankStats({tankLog:[{liter:50,km:1000}]}," + NOW + "),"
              "leer:_fzTankStats({}," + NOW + "),nix:_fzTankStats(null," + NOW + ")}",
              *TANK_FNS)
    assert r["tipp"]["plausibel"] is False, "200 L/100 km ist ein Tippfehler im km-Stand"
    assert r["eins"]["l100"] is None
    assert r["leer"]["anzahl"] == 0 and r["nix"]["anzahl"] == 0
    assert r["leer"]["euroMonat"] is None


# ── Fahrzeugakte, Fahrer, CSV ────────────────────────────────────────────────

def test_akte_chronik(node_exe, index_html):
    f = {"tankLog": [{"liter": 40, "preis": 60, "km": 1000, "datum": "2026-10-01", "by": "Max"}],
         "serviceheft": [{"datum": "2026-09-01", "art": "Service", "beschreibung": "Ölwechsel", "kosten": "250", "km": 900}],
         "schaeden": [{"datum": "2026-11-02", "beschreibung": "Delle", "status": "offen"}],
         "kmLog": [{"id": "km_tk1", "km": 1000, "date": "2026-10-01"}, {"km": 1200, "datum": "2026-11-05", "note": "Wien"}, {"km": 5, "datum": None}]}
    r = _eval(node_exe, index_html, "_fzAkte(" + json.dumps(f) + ")", *BASIS, "_fzAkte")
    arten = [e["art"] for e in r]
    assert arten == ["km-Stand", "Schaden", "Tanken", "Service", "km-Stand"], arten
    assert r[-1]["datum"] == "", "ohne Datum ans Ende, nicht als 1970 nach vorne/hinten sortiert"
    assert r[3]["euro"] == 250
    assert all(e["text"] != "" or e["art"] == "km-Stand" for e in r)
    assert not any(e.get("km") == 1000 and e["art"] == "km-Stand" for e in r), "km_-Zeilen des Tank-Syncs doppeln die Tankung"


def test_fahrer_klassen(node_exe, index_html):
    fz = [{"id": "1", "kennzeichen": "LKW-1", "typ": "LKW", "fahrer": "m1"},
          {"id": "2", "kennzeichen": "LKW-2", "typ": "LKW", "fahrer": "m2"},
          {"id": "3", "kennzeichen": "TR-1", "typ": "Transporter", "fahrer": "m3"},
          {"id": "4", "kennzeichen": "TR-2", "typ": "Transporter", "fahrer": "mx"},
          {"id": "5", "kennzeichen": "AN-1", "typ": "Anhänger", "fahrer": "m1"},
          {"id": "6", "kennzeichen": "TR-3", "typ": "Transporter", "fahrer": "m1"},
          {"id": "7", "kennzeichen": "TR-4", "typ": "Transporter"}]
    ma = [{"id": "m1", "n": "Anna", "fs": "B, BE"}, {"id": "m2", "n": "Bert", "fs": "B,C"}, {"id": "m3", "n": "Cem", "fs": ""}]
    r = _eval(node_exe, index_html, "_fzFahrerCheck(" + json.dumps(fz) + "," + json.dumps(ma) + ")"
              ".map(function(x){return [x.kennzeichen,x.stufe];})", "_fzFahrerCheck")
    d = dict(r)
    assert d == {"LKW-1": "klasse", "LKW-2": "ok", "TR-1": "fehlt", "TR-2": "unbekannt", "TR-3": "ok"}, d
    assert r[0][1] == "unbekannt"


def test_csv_formelschutz_und_zahlen(node_exe, index_html):
    r = _eval(node_exe, index_html,
              "{csv:_fzCsv(['A','B'],[['=SUMME(1)','-12'],['sag \"hi\"',null],['@x','+5']]),"
              "z1:_fzCsvZahl(NaN,2),z2:_fzCsvZahl(null,2),z3:_fzCsvZahl(1234.5,2)}",
              "_fzCsvZelle", "_fzCsv", "_fzCsvZahl")
    csv = r["csv"]
    assert csv.startswith("﻿")
    zeilen = csv[1:].split("\r\n")
    assert zeilen[0] == '"A";"B"'
    assert zeilen[1] == '"\'=SUMME(1)";"-12"', "Formel entschaerft, reine Zahl bleibt Zahl"
    assert zeilen[2] == '"sag ""hi""";""'
    assert zeilen[3] == '"\'@x";"\'+5"'
    assert r["z1"] == "" and r["z2"] == "", "unbekannt = leere Zelle, nicht 0"
    assert r["z3"] == "1234,50"


# ── Render-Rauchprobe: die drei Ansichten laufen mit echten Daten durch ──────

_UI_STUBS = r"""
var _hooks=[];var React={createElement:function(t,p){var c=Array.prototype.slice.call(arguments,2);if(typeof t==='function')return t(Object.assign({},p||{},{children:c}));return {t:t,p:p||{},c:c};},Fragment:'frag'};
var _react={useState:{call:function(_x,init){return [typeof init==='function'?init():init,function(){}];}},useEffect:{call:function(_x,fn){_hooks.push(fn);}}};
var V={bg:'#fff',cd:'#fff',bd:'#ddd',tx:'#111',dm:'#555',mt:'#888',ac:'#009640',acTx:'#00722F'};
var mono='monospace';function CC(){return {};}function II(){return {};}function bsS(){return {};}function thS(){return {};}function tdSt(){return {};}
function _ik(n){return {t:'svg',p:{n:n},c:[]};}function _ikVw(n,t){return {t:'ik',p:{n:n},c:[t]};}
function _dl(){}var window={};var navigator={onLine:false};
function _sbGet(){return Promise.resolve([]);}
"""


def _texte(node):
    return ("function _tx(n){if(n===null||n===undefined||n===false||n===true)return '';"
            "if(typeof n==='string'||typeof n==='number')return String(n);"
            "if(Array.isArray(n))return n.map(_tx).join(' ');return (n.c||[]).map(_tx).join(' ');}")


def _node_datei(node_exe, tmp_path, snip):
    """Grosse Schnipsel ueber eine Datei - die Windows-Kommandozeile fasst nur 32k Zeichen."""
    f = tmp_path / "rauch.js"
    f.write_text(snip, encoding="utf-8")
    r = subprocess.run([node_exe, str(f)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    assert r.returncode == 0, r.stderr
    return r.stdout.strip()


def test_ansichten_rendern_ohne_fehler(node_exe, index_html, tmp_path):
    linien = []
    for pat in (r"^const COLORS=\{.*?\};", r"^const fmt\$=.*$"):
        m = re.search(pat, index_html, re.M)
        assert m, pat
        linien.append(m.group(0).rstrip("\r"))
    ui = re.search(r"const UI=\{grund:.*?fSeite:22,", index_html)
    assert ui
    ui_zeile = ui.group(0).rstrip(",") + "};"
    # die Kommentare im UI-Objekt duerfen bleiben - es ist gueltiges JS
    fns = BASIS + ("_fzPickerlStufe", "_fzTerminErledigt", "_fzFristen", "_fzTankStats", "_fzServiceStats",
                   "_fzAkte", "_fzFahrerCheck", "_fzCsvZelle", "_fzCsv", "_fzCsvZahl", "_fzTageTxt", "_fzDatumAnz",
                   "_fzStufeChip", "_fzCsvLaden", "_fzChipBtn", "FlotteFristenPanel", "FlotteKostenPanel",
                   "FahrzeugAkteKarte", "_n")
    fz = [dict(FZ[0], marke="Ford", modell="Transit", fahrer="m1", typ="LKW",
               tankLog=[{"liter": 40, "preis": 60, "km": 1000, "datum": "2026-10-01"},
                        {"liter": 45, "preis": 70, "km": 1600, "datum": "2026-11-01"}],
               serviceheft=[{"datum": "2026-09-01", "kosten": 300, "docs": [{"id": "d"}]}],
               schaeden=[{"status": "offen", "beschreibung": "Delle", "datum": "2026-11-02"}]),
          FZ[1], FZ[3], {"id": "leer", "kennzeichen": "TU-9"}]
    ma = [{"id": "m1", "n": "Anna", "fs": "B"}]
    snip = (TZ + _UI_STUBS + "\n".join(linien) + "\n" + ui_zeile + "\n"
            + "\n".join(_harness(index_html, *VARS).split("\n")[1:]) + "\n"
            + "\n".join(_extract_fn(index_html, n) for n in fns) + "\n" + _texte(None) + "\n"
            "var fz=" + json.dumps(fz) + ",ma=" + json.dumps(ma) + ";var out={};"
            "[false,true].forEach(function(mob){"
            "out['fristen'+mob]=_tx(FlotteFristenPanel({fahrzeuge:fz,monteure:ma,isMob:mob,zeigeFahrer:true,onOpen:function(){}}));"
            "out['kosten'+mob]=_tx(FlotteKostenPanel({fahrzeuge:fz,isMob:mob,onOpen:function(){}}));"
            "out['akte'+mob]=_tx(FahrzeugAkteKarte({f:fz[0],isMob:mob}));"
            "out['akteLeer'+mob]=_tx(FahrzeugAkteKarte({f:fz[3],isMob:mob}));});"
            "out.ohne=FahrzeugAkteKarte({f:null});"
            "_hooks.forEach(function(fn){var c=fn();if(typeof c==='function')c();});out.effekte=_hooks.length;"
            "process.stdout.write(JSON.stringify(out));")
    r = json.loads(_node_datei(node_exe, tmp_path, snip))
    for mob in ("false", "true"):
        fr, ko, ak, al = r["fristen" + mob], r["kosten" + mob], r["akte" + mob], r["akteLeer" + mob]
        assert "Fristen im Fuhrpark" in fr and "TU-1" in fr and "überfällig" in fr
        assert "Geplante Werkstatt-Termine werden geladen" in fr, "Ladezustand der Termine ehrlich benannt"
        assert "braucht C1 oder C" in fr, "LKW-Fahrer mit nur B muss auffallen"
        assert "Kosten und Verbrauch" in ko and "TU-9" in ko
        assert "NaN" not in ko and "NaN" not in fr and "NaN" not in ak and "NaN" not in al, "NaN darf nie angezeigt werden"
        assert "1970" not in fr + ko + ak + al, "kein erfundenes Epoch-Datum"
        assert "Fahrzeugakte" in ak and "Chronik (" in ak
        assert "Chronik (0 Einträge)" in al
    assert r["ohne"] is None
    assert r["effekte"] == 2, "der Termin-Abruf (offline-Zweig) laeuft ohne Fehler durch"


# ── Form-Riegel: nur lesen, eingebunden, Tablet-Befund ──────────────────────

def test_ausbau_block_schreibt_nichts(index_html):
    b = _block(index_html)
    for verboten in ("SQ.push", "_sbPatch", "_sbPost", "_sbDelete", "setFahrzeuge", "upd(", "localStorage.setItem", "?."):
        assert verboten not in b, "Ausbau-Block darf nicht schreiben / kein optional chaining: " + verboten
    assert "_sbGet('fz_termine')" in b, "einziger Netzzugriff: Lesen der Termine"


def test_ansichten_eingebunden_und_gegated(index_html):
    assert 'isVAdmin&&view==="fristen"&&React.createElement(FlotteFristenPanel' in index_html
    assert 'isVAdmin&&view==="kosten"&&React.createElement(FlotteKostenPanel' in index_html
    assert 'React.createElement(FahrzeugAkteKarte, {key: "akte_"+selFz.id, f: selFz' in index_html
    assert 'if(!isVAdmin&&(view==="fristen"||view==="kosten"))setView("liste");' in index_html
    # Liste/Kacheln werden unter Fristen/Kosten ausgeblendet - aber nur fuer Verwalter
    assert '&&(!isVAdmin||(view!=="fristen"&&view!=="kosten"))&&' in index_html


def test_flotte_zeile_kennzeichen_schrumpft_nie(index_html):
    a = index_html.index("const _fleetZeile=function(row){")
    z = index_html[a:index_html.index("const _imeiZeile=", a)]
    i = z.index("row.f.kennzeichen||'?'")
    kopf = z[max(0, i - 700):i]
    assert "flex:'0 0 auto'" in kopf, "Kennzeichen-Spalte muss starr sein (Tablet hochkant)"
    assert "{minWidth:0,flex:1}}" not in kopf, "Umkehrprobe: der alte schrumpfende Container ist zurueck"
    assert "flexShrink:0,minWidth:110" not in z, "der rechte Block darf das Kennzeichen nicht mehr verdraengen"
    assert "flex:'1 1 auto',minWidth:0" in z


def test_gps_leerzustand_ehrlich(index_html):
    a = index_html.index("const _panelKarte=")
    k = index_html[a:index_html.index("const _panelBuch=", a)]
    assert "(st.loaded&&!st.missing&&trackerFz.length===0)?" in k
    assert "Noch keine GPS-Tracker" in k
    assert "Noch keine Tracker zugeordnet" in k
    # das Banner bleibt fuer die anderen Leerfaelle
    assert "View fz_latest fehlt" in k and "Noch keine Tracker-Daten" in k
