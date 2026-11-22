# -*- coding: utf-8 -*-
"""v3.9.1095 - sechs Testerfunde zur Anzeige, erst gemessen, dann gebaut.

Gemessen am 22.11.2026 (Prod, nur lesend):
1. Projektakte "Arbeitstage 36 = Eintraege 36": KEIN Fehler. uniqueDays zaehlt
   new Set(datum).size. Projekt pmof9xiwk hatte bis 19.11. 14:01 genau 36
   Eintraege an 36 Tagen; seitdem 37 Eintraege an 36 Tagen (zwei Monteure am
   19.11.). p4: 94 Eintraege, 65 Tage. Gesichert: Zaehlung bleibt distinct.
2. Wochenbericht: Tageszellen 2 Stellen ("3,00"), Summen 1 Stelle ("3,0")
   -> eine Konstante BER_STD_STELLEN=2 fuer alle drei.
3. Kilometerprotokoll: 33 von 43 km_log-Zeilen tragen {km,date} ohne datum/by
   (geschrieben vom Tank-/km-Abgleich in apiPatch). Anzeige las nur datum/by.
4. O L/100 km: Formel stimmt (Liter ohne erste Tankung / km erste..letzte),
   aber die Zeile zeigte nur "Liter" = ALLE Tankungen -> Basis jetzt sichtbar.
5. Stammdaten "noch nichts erfasst" bei allen 19 Fahrzeugen, obwohl
   versicherung/reifen (Fahrzeugfelder) bei 15 befuellt sind.
6. "Kalibrierung faellig (6)" vs Donut "(1)": seit v1073 heisst der Status
   "Zur Kalibrierung" (Status-Zaehlung, 1); jetzt steht die Datum-Zahl (6) im
   Titel des Donuts daneben. Die Status-Zaehlung selbst bleibt.
Jeder Riegel hat eine Umkehrprobe.
"""
import json
import re

import pytest

from conftest import run_node_snippet


def _fn(src, name):
    """Top-level function NAME bis zur naechsten Top-Level-Funktion/-Konstante."""
    a = src.find("\nfunction " + name + "(")
    assert a != -1, name
    m = re.compile(r"\n(function |var |const |let |/\*)").search(src, a + 1)
    return src[a + 1:m.start()]


def _var(src, kopf):
    a = src.find(kopf)
    assert a != -1, kopf
    return src[a:src.index("\n};", a) + 3]


# ── 1 Arbeitstage = verschiedene Tage ───────────────────────────────────────
def pruef_arbeitstage(src):
    return ("const uniqueDays=new Set(pe.map(e=>e.datum||e.date).filter(Boolean)).size;" in src
            and "\"Arbeitstage\"), React.createElement('div', { style: {fontSize:22,fontWeight:800}}, uniqueDays)" in src)


def test_1_arbeitstage_zaehlt_verschiedene_tage(index_html, node_exe):
    assert pruef_arbeitstage(index_html)
    zeile = re.search(r"const uniqueDays=[^;]+;", index_html).group(0)
    pe = [{"date": "2026-11-19"}, {"date": "2026-11-19"}, {"date": "2026-11-18"}]
    out = run_node_snippet(node_exe, "const pe=" + json.dumps(pe) + ";" + zeile + "process.stdout.write(String(uniqueDays));")
    assert out == "2"


def test_1_umkehr_eintraege_statt_tage(index_html):
    kaputt = index_html.replace("}, uniqueDays)),", "}, pe.length)),", 1)
    assert kaputt != index_html and not pruef_arbeitstage(kaputt)


# ── 2 Wochenbericht eine Stellenzahl ────────────────────────────────────────
def _ber(src):
    a = src.find("const BER_STD_STELLEN=")
    return src[a:src.index("\nfunction printForm(", a)] if a != -1 else ""


def pruef_wochenbericht(src):
    b = _ber(src)
    if not b:
        return ["BER_STD_STELLEN fehlt"]
    feh = []
    if not re.search(r"const BER_STD_STELLEN=2;", b):
        feh.append("Stellenzahl nicht 2")
    for v in ("h", "sum", "totalH"):
        if "_projStdDE(" + v + ",BER_STD_STELLEN)" not in b:
            feh.append(v + " nicht ueber BER_STD_STELLEN")
    if re.search(r"_projStdDE\((h|sum|totalH),\d\)", b):
        feh.append("feste Stellenzahl im Wochenbericht")
    return feh


def test_2_wochenbericht_einheitlich(index_html, node_exe):
    assert pruef_wochenbericht(index_html) == []
    f = _fn(index_html, "_projStdDE")
    out = run_node_snippet(node_exe, f + "process.stdout.write([_projStdDE(3,2),_projStdDE(7.75,2)].join('|'));")
    assert out == "3,00|7,75"


def test_2_umkehr_summe_mit_einer_stelle(index_html):
    kaputt = index_html.replace("_projStdDE(sum,BER_STD_STELLEN)", "_projStdDE(sum,1)", 1)
    assert kaputt != index_html and pruef_wochenbericht(kaputt) != []


# ── 3 Kilometerprotokoll: Datum + Erfasser ──────────────────────────────────
TANK = [{"id": "tk1", "datum": "2026-06-22", "by": "Sebastian G.", "km": "115694", "liter": "27.64"},
        {"id": "tk2", "datum": "2026-07-01", "by": "Christoph R.", "km": 117492, "liter": 74.19}]
KM = [{"km": 129453, "datum": "2026-11-11", "note": "", "by": "Pinger Leo"},
      {"km": 115694, "date": "2026-06-22"},
      {"id": "km_tk2", "km": 117492, "date": "2026-07-02"},
      {"km": 99999, "date": "2026-07-05"}]


def _km_js(src):
    return _fn(src, "_fzZahl") + "\n" + _fn(src, "_fzKmZeileAnz") + "\n"


def test_3_km_zeile_datum_und_erfasser(index_html, node_exe):
    js = _km_js(index_html) + ("const f={tankLog:" + json.dumps(TANK) + "};const K=" + json.dumps(KM) + ";"
                               "process.stdout.write(JSON.stringify(K.map(k=>_fzKmZeileAnz(f,k))));")
    r = json.loads(run_node_snippet(node_exe, js))
    assert [x["datum"] for x in r] == ["2026-11-11", "2026-06-22", "2026-07-02", "2026-07-05"]
    assert [x["wer"] for x in r] == ["Pinger Leo", "Sebastian G.", "Christoph R.", ""]
    assert r[1]["quelle"] == "tank" and r[0]["quelle"] == ""
    assert r[3]["grund"].startswith("Erfasser nicht gespeichert")


def pruef_km_anzeige(src):
    z = [l for l in src.splitlines() if '_fzSekKopf("lineal","Kilometerprotokoll")' in l]
    if len(z) != 1:
        return ["Kopf fehlt"]
    i = src.index('_fzSekKopf("lineal","Kilometerprotokoll")')
    teil = src[i:i + 1500]
    feh = []
    if "fdt(k.datum)" in teil or ", k.by)" in teil:
        feh.append("liest nur datum/by")
    if "_fzKmZeileAnz(selFz,k)" not in teil or 'fdt(_kz.datum)||"—"' not in teil or '_kz.wer||"—"' not in teil:
        feh.append("ohne _fzKmZeileAnz/Strich")
    return feh


def test_3_anzeige_ueber_helfer(index_html):
    assert pruef_km_anzeige(index_html) == []


def test_3_umkehr_alte_anzeige(index_html, node_exe):
    i = index_html.index("(function(){const _kz=_fzKmZeileAnz(selFz,k);")
    e = index_html.index("})()", i) + 4
    kaputt = index_html[:i] + 'fdt(k.datum), " · "  , k.by' + index_html[e:]
    assert pruef_km_anzeige(kaputt) != []
    # und der Helfer ohne date-Rueckfall waere rot
    k2 = index_html.replace('var dat=(k&&(k.datum||k.date))||"";', 'var dat=(k&&k.datum)||"";', 1)
    assert k2 != index_html
    r = json.loads(run_node_snippet(node_exe, _km_js(k2) + "process.stdout.write(JSON.stringify(_fzKmZeileAnz({},{km:1,date:'2026-06-22'})));"))
    assert r["datum"] == ""


# ── 4 Verbrauch: Basis sichtbar, Formel unveraendert ────────────────────────
TANK4 = [{"datum": "2026-06-22", "km": "115694", "liter": "27.64", "preis": 50},
         {"datum": "2026-07-01", "km": "117492", "liter": "74.19", "preis": 120},
         {"datum": "2026-07-05", "km": "118250", "liter": "25,75", "preis": 40},
         {"datum": "2026-07-06", "km": 0, "liter": "10", "preis": 15}]


def _tank_js(src):
    return "\n".join([_fn(src, "_fzDE"), _fn(src, "_fzZahl"), _fn(src, "_fzDatumTeile"),
                      _fn(src, "_fzTankStats"), _fn(src, "_fzL100Basis")]) + "\n"


def test_4_formel_und_basis(index_html, node_exe):
    js = _tank_js(index_html) + ("const t=_fzTankStats({tankLog:" + json.dumps(TANK4) + "},Date.parse('2026-11-22'));"
                                 "process.stdout.write(JSON.stringify({l100:t.l100,L:t.literBasis,s:t.strecke,liter:t.liter,b:_fzL100Basis(t)}));")
    r = json.loads(run_node_snippet(node_exe, js))
    assert r["s"] == 118250 - 115694
    assert abs(r["L"] - (74.19 + 25.75)) < 1e-9          # ohne erste Tankung, ohne km-0-Tankung
    assert abs(r["l100"] - r["L"] / r["s"] * 100) < 1e-9  # nachrechenbar aus der gezeigten Basis
    assert abs(r["liter"] - (27.64 + 74.19 + 25.75 + 10)) < 1e-9  # Spalte Liter = alle
    assert r["b"] == "99,9 L auf 2.556 km"


def pruef_basis_anzeige(src):
    feh = []
    if src.count("_fzL100Basis(t)?") < 2:
        feh.append("Kosten-Ansicht ohne Basis")
    if '" ("+_fzL100Basis(_ts)+", erste Tankung nicht mitgezählt)"' not in src:
        feh.append("Detail ohne Basis")
    return feh


def test_4_basis_in_allen_drei_anzeigen(index_html):
    assert pruef_basis_anzeige(index_html) == []


def test_4_umkehr(index_html):
    kaputt = index_html.replace('" ("+_fzL100Basis(_ts)+", erste Tankung nicht mitgezählt)"', '""', 1)
    assert kaputt != index_html and pruef_basis_anzeige(kaputt) != []


# ── 5 Stammdaten-Zusammenfassung ────────────────────────────────────────────
def _stamm_js(src):
    return "\n".join([_var(src, "var FZ_STAMM_FELDER={"), _fn(src, "_fzZahl"), _fn(src, "_fzDatumTeile"),
                      _fn(src, "_fzStammWert"), _fn(src, "_fzStammRest")]) + "\n"


def test_5_fahrzeugfelder_zaehlen(index_html, node_exe):
    js = _stamm_js(index_html) + (
        "const a=_fzStammRest({versicherung:'Wiener Städtische Pol.Nr.: 1023625709',reifen:'255/55/R17'},null,[],true);"
        "const b=_fzStammRest({versicherung:'Wiener Städtische',reifen:''},null,[],false);"
        "const c=_fzStammRest({versicherung:'',reifen:'',reifen_lager:'Reifen Huber',service_km_intervall:30000},{leasing_geber:'X',versicherung_polizze:'P1'},[],true);"
        "const d=_fzStammRest({versicherung:'WSt'},{},['Versicherung bis 01.01.2027'],true);"
        "const e=_fzStammRest({},null,[],true);"
        "process.stdout.write(JSON.stringify([a,b,c,d,e]));")
    a, b, c, d, e = json.loads(run_node_snippet(node_exe, js))
    assert a == ["Versicherung Wiener Städtische Pol.Nr.: 1023625709", "Reifen 255/55/R17"]
    assert b == []  # ohne Finanzrecht keine Versicherung in der Zeile "Reifen & Service-Intervall"
    assert c == ["Leasing", "Versicherung", "Reifen eingelagert", "Service-Intervall"]
    assert d == []  # schon genannt -> nicht doppelt
    assert e == []  # leer bleibt leer -> "noch nichts erfasst"


def pruef_stamm(src):
    return "zusammen=zusammen.concat(_fzStammRest(f,finDa?fin:null,zusammen,siehtFinanz));" in src


def test_5_zusammenfassung_nutzt_helfer(index_html):
    assert pruef_stamm(index_html)
    assert "zusammen.length?zusammen.join(' · '):'noch nichts erfasst'" in index_html


def test_5_umkehr(index_html):
    kaputt = index_html.replace("zusammen=zusammen.concat(_fzStammRest(f,finDa?fin:null,zusammen,siehtFinanz));", "", 1)
    assert kaputt != index_html and not pruef_stamm(kaputt)


# ── 6 Werkzeuge: Status-Donut nennt die Datum-Faelligkeit ───────────────────
def pruef_wz(src):
    return ("const wzKalibDatum=_react.useMemo.call(void 0, ()=>werkzeuge.filter(w=>_wzKalibFaellig(w)).length,[werkzeuge]);" in src
            and '{key:"wzStatus",title:"Werkzeuge nach Status"+(wzKalibDatum>0?" · Kalibrierung fällig (nach Datum): "+wzKalibDatum:""),' in src
            # die Status-Zaehlung selbst bleibt (v1073-Riegel)
            and "Object.entries(WZ_STATUS).map(([k,v])=>({l:v.l,v:werkzeuge.filter(w=>w.status===k).length" in src)


def test_6_titel_nennt_datum_zahl(index_html):
    assert pruef_wz(index_html)


def test_6_umkehr(index_html):
    kaputt = index_html.replace('title:"Werkzeuge nach Status"+(wzKalibDatum>0?', 'title:"Werkzeuge nach Status"+(false?', 1)
    assert kaputt != index_html and not pruef_wz(kaputt)
