# -*- coding: utf-8 -*-
"""v3.9.1096 OCR km-Stand ("Google Vision verbessern, der km-Stand wird nie erkannt").

Befund: die App verwarf `_j.km` der Edge Function und las selbst nur eine Zeile mit dem Wort KILOMETERSTAND;
die Edge Function kannte zusaetzlich nur "123456 km" ohne Tausenderpunkt. "KM-STAND", "Km:", "Tacho",
"123.456 km", "123 456" und Spaltensatz (Bezeichnungen und Werte in getrennten Bloecken) liefen leer.

TEIL A: logic.ts (Edge Function) - kmAusText auf ~20 synthetischen Proben (Belege mit/ohne km, Tachofotos),
        Plausi gegen den bisherigen Stand, Zeilen aus Wortboxen (kmAusVision), parseTankbeleg unveraendert.
TEIL B: App-Abschrift (@OCR-KM-Block in index.html) liefert auf denselben Proben dasselbe; _kmAusAntwort
        nimmt den Edge-km nur plausibel und faellt sonst auf den Rohtext zurueck.
TEIL C: Umkehrproben - der alte App- und der alte Edge-Parser scheitern an genau den neuen Faellen.
TEIL D: Verdrahtung - kmVorher/art:"tacho" im Aufruf, Hinweis am km-Feld, Antwort abwaertskompatibel.
"""
import io
import json
import os
import re
import subprocess
import tempfile

import pytest

from conftest import EPK_TEST_TIMEOUT

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FN_DIR = os.path.join(WURZEL, "supabase", "functions", "ocr_tankbeleg")
LOGIC = os.path.join(FN_DIR, "logic.ts")
INDEX_TS = os.path.join(FN_DIR, "index.ts")
INDEX_HTML = os.path.join(WURZEL, "index.html")


def _lies(p):
    with open(p, encoding="utf-8") as fh:
        return fh.read().replace("\r\n", "\n")


def _fn(src, name):
    """Top-level-Funktion `function name(` per Klammerzaehlung ausschneiden."""
    i = src.index("function " + name + "(")
    j = src.index("{", i)
    tiefe = 0
    for k in range(j, len(src)):
        if src[k] == "{":
            tiefe += 1
        elif src[k] == "}":
            tiefe -= 1
            if tiefe == 0:
                return src[i:k + 1]
    raise AssertionError(name)


def _app_block(html):
    a = html.index("/*@OCR-KM-START")
    b = html.index("/*@OCR-KM-END*/")
    return html[a:b]


# Altstand (origin/main 5807fce) woertlich: App-Helper v3.9.528 und km-Teil der Edge Function v9.
ALT_APP = r"""
function _kmFromBelegAlt(raw, curKm){
  if(!raw) return '';
  const L=String(raw).split(/\r?\n/);
  let v='';
  for(let i=0;i<L.length;i++){
    if(/KILOMETERSTAND/i.test(L[i])){
      let c=L[i].replace(/.*KILOMETERSTAND[^0-9]*/i,'');
      let m=c.match(/\d[\d.\s]*/);
      if(!m){ for(let k=1;k<=2&&i+k<L.length;k++){ const mm=L[i+k].match(/^\s*([\d.\s]{1,9})\s*$/); if(mm){ m=[mm[1]]; break; } } }
      if(m) v=m[0].replace(/[^\d]/g,'');
      break;
    }
  }
  if(!v) return '';
  let n=parseInt(v,10);
  if(!isFinite(n)||n<=0) return '';
  const cur=parseInt(curKm,10);
  if(isFinite(cur)&&cur>0){
    if(n<cur) return '';
    if(n>cur+100000) return '';
  }
  return String(n);
}
function _kmEdgeAlt(t){
  const _lines = t.split(/\r?\n/);
  const _ki = _lines.findIndex((l) => /KILOMETERSTAND/i.test(l));
  let kcand = null;
  if (_ki >= 0) {
    for (let i = _ki; i <= Math.min(_ki + 2, _lines.length - 1) && !kcand; i++) {
      const m = _lines[i].match(/\b0*([1-9]\d{2,6})\b(?!\s*\/\d)/);
      if (m) kcand = m[1];
    }
  }
  if (!kcand) { const m = t.match(/\b([1-9]\d{2,6})\s*km\b/i); if (m) kcand = m[1]; }
  if (kcand) { const k = parseInt(kcand, 10); if (k >= 1 && k <= 9999999) return String(k); }
  return '';
}
"""

# (name, text, vorherKm, art, erwartet_km, neu)  neu=True -> der Altstand (App) fand das nicht.
BELEG_FUSS = "DIESEL 45,32 L\nPREIS/L 1,789 EUR\nSUMME 81,08 EUR\n14.11.2026 10:37\nSTAN 046183/420\nBELEG-NR 004711"
PROBEN = [
    ("beleg_kilometerstand", "BP ROUTEX\nKILOMETERSTAND: 123456\n" + BELEG_FUSS, 123000, "beleg", "123456", False),
    ("beleg_km_stand_punkt", "ENI\nKM-STAND: 123.456\n" + BELEG_FUSS, 123000, "beleg", "123456", True),
    ("beleg_km_doppelpunkt_leer", "Km: 87 654\n" + BELEG_FUSS, 87000, "beleg", "87654", True),
    ("beleg_km_zeilenanfang", "SHELL\nKM 98765\n" + BELEG_FUSS, 98000, "beleg", "98765", True),
    ("beleg_tachostand", "Tachostand\n054321\n" + BELEG_FUSS, 54000, "beleg", "54321", True),
    ("beleg_laufleistung_einheit", "Laufleistung 123.456 km\n" + BELEG_FUSS, 0, "beleg", "123456", True),
    ("beleg_nur_einheit_punkt", "Fahrzeug W-12345X\n123.456 km\n" + BELEG_FUSS, 123000, "beleg", "123456", True),
    ("beleg_ohne_km", BELEG_FUSS, 120000, "beleg", "", False),
    ("beleg_ohne_km_ohne_vorher", BELEG_FUSS, 0, "beleg", "", False),
    ("beleg_km_null", "KILOMETERSTAND: 0\n" + BELEG_FUSS, 120000, "beleg", "", False),
    ("beleg_km_rueckwaerts", "KM-STAND 98000\n" + BELEG_FUSS, 120000, "beleg", "", False),
    ("beleg_km_absurd", "KM-STAND 9123456\n" + BELEG_FUSS, 120000, "beleg", "", False),
    ("beleg_kilometerpreis", "Kilometerpreis 0,42 EUR\n" + BELEG_FUSS, 0, "beleg", "", False),
    ("beleg_teilstrecke", "Strecke 12,5 km\n" + BELEG_FUSS, 0, "beleg", "", False),
    ("tacho_rein", "123456", 123000, "tacho", "123456", True),
    ("tacho_leerzeichen", "123 456 km\n1234,5\n12:34\n-3°C", 123000, "tacho", "123456", True),
    ("tacho_punkt_ohne_vorher", "123.456 km\nTRIP 1234,5 km\n12:34", 0, "tacho", "123456", True),
    ("tacho_fuehrende_null", "045123", 45000, "tacho", "45123", True),
    ("tacho_nur_stoer", "12:34\n1234,5\n45,32\n1,789", 0, "tacho", "", False),
    ("tacho_geschwindigkeit", "130 km/h\n98765\n22.11.2026", 98000, "tacho", "98765", True),
    ("tacho_naechste_ueber_vorher", "D 123460\nREICHWEITE 450 km\n99999", 123400, "tacho", "123460", True),
]

# Spaltensatz: Vision-Rohtext stellt Bezeichnungen und Werte in getrennte Bloecke - nur die Wortboxen helfen.
SPALTEN_ROH = "BP\nKILOMETERSTAND\nFAHRER-NR\nBETRAG\n123456\n0001\n81,08 EUR"


def _wort(text, x, y, h=20):
    return {"symbols": [{"text": c} for c in text],
            "boundingBox": {"vertices": [{"x": x, "y": y}, {"x": x + 10 * len(text), "y": y},
                                         {"x": x + 10 * len(text), "y": y + h}, {"x": x, "y": y + h}]}}


SPALTEN_FTA = {"pages": [{"blocks": [
    {"paragraphs": [{"words": [_wort("BP", 10, 10)]}]},
    {"paragraphs": [{"words": [_wort("KILOMETERSTAND", 10, 50), _wort("FAHRER-NR", 10, 90), _wort("BETRAG", 10, 130)]}]},
    {"paragraphs": [{"words": [_wort("123456", 300, 52), _wort("0001", 300, 91), _wort("81,08", 300, 128), _wort("EUR", 360, 129)]}]},
]}]}

HARNESS = r"""
import * as L from "./logic.ts";
import { readFileSync } from "node:fs";
const P = JSON.parse(readFileSync("./proben.json", "utf8"));
const app = new Function(readFileSync("./app.js", "utf8") + "\nreturn {_kmAusText, _kmAusAntwort, _kmFromBeleg, _kmFromBelegAlt, _kmEdgeAlt};")();
const OUT = {neu: {}, app: {}, alt_app: {}, alt_edge: {}, antwort: {}, spalten: {}, beleg: null};
for (const [name, text, vk, art] of P.proben) {
  OUT.neu[name] = L.kmAusText(text, vk, art);
  OUT.app[name] = app._kmAusText(text, vk, art);
  OUT.alt_app[name] = art === "tacho" ? "" : app._kmFromBelegAlt(text, vk);
  OUT.alt_edge[name] = app._kmEdgeAlt(text);
}
OUT.spalten.vision = L.kmAusVision(P.spalten_roh, P.spalten_fta, 123000, "beleg");
OUT.spalten.nur_roh = L.kmAusText(P.spalten_roh, 123000, "beleg");
OUT.spalten.zeilen = L.zeilenAusAnnotation(P.spalten_fta);
OUT.spalten.ohne_fta = L.kmAusVision(P.spalten_roh, null, 123000, "beleg");
OUT.beleg = L.parseTankbeleg("KM-STAND 123.456\n" + P.fuss);
OUT.beleg_alt_fuss = L.parseTankbeleg(P.fuss);
const A = app._kmAusAntwort;
OUT.antwort = {
  neu_edge: A({km_quelle: "beleg_label", km: "123456", km_sicher: true, rawText: ""}, 123000, "beleg"),
  neu_edge_rueckwaerts: A({km_quelle: "beleg_label", km: "98000", rawText: "KM-STAND 123.456"}, 123000, "beleg"),
  alt_edge_kaputt: A({km: "046183", rawText: "KM-STAND 123.456\nSTAN 046183/420"}, 123000, "beleg"),
  alt_edge_nichts: A({km: "", rawText: P.fuss}, 123000, "beleg"),
  tacho_alt_edge: A({km: "", rawText: "123 456 km\n12:34"}, 123000, "tacho"),
  tacho_neu_edge_sprung: A({km_quelle: "tacho", km: "160000", rawText: "160000"}, 123000, "tacho"),
  kein_json: A(null, 123000, "beleg"),
  neu_edge_unpl: A({km_quelle: "", km: "", km_unplausibel: "98000", km_stelle: "KM-STAND 98000", rawText: ""}, 123000, "beleg"),
  vorher_text: A({km_quelle: "beleg_label", km: "123.456", rawText: ""}, "123.000", "beleg"),
};
OUT.fromBeleg = app._kmFromBeleg("KM-STAND: 123.456", 123000);
console.log(JSON.stringify(OUT));
"""


def _lauf(node_exe, logic_src=None, app_src=None):
    html = _lies(INDEX_HTML)
    if app_src is None:
        app_src = _app_block(html)
    app_js = _fn(html, "_fzZahl") + "\n" + _fn(html, "_ganzZahl") + "\n" + app_src + "\n" + ALT_APP
    proben = {"proben": [list(p[:4]) for p in PROBEN], "spalten_roh": SPALTEN_ROH, "spalten_fta": SPALTEN_FTA,
              "fuss": BELEG_FUSS}
    with tempfile.TemporaryDirectory() as d:
        for name, inhalt in (("logic.ts", logic_src if logic_src is not None else _lies(LOGIC)), ("app.js", app_js),
                             ("h.mjs", HARNESS), ("proben.json", json.dumps(proben))):
            with io.open(os.path.join(d, name), "w", encoding="utf-8", newline="\n") as f:
                f.write(inhalt)
        r = subprocess.run([node_exe, "--experimental-strip-types", "--no-warnings", "h.mjs"], cwd=d,
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=EPK_TEST_TIMEOUT)
    assert r.returncode == 0, r.stderr[-3000:]
    return json.loads(r.stdout.strip().splitlines()[-1])


@pytest.fixture(scope="module")
def E(node_exe):
    return _lauf(node_exe)


def _fehler(E, quelle):
    return [(p[0], E[quelle][p[0]]["km"], p[4]) for p in PROBEN if E[quelle][p[0]]["km"] != p[4]]


# ── TEIL A: Edge-Logik ──────────────────────────────────────────────────────
def test_edge_logik_alle_proben(E):
    assert _fehler(E, "neu") == []


def test_edge_quelle_und_sicher(E):
    assert E["neu"]["beleg_kilometerstand"] == {"km": "123456", "quelle": "beleg_label", "sicher": True,
                                                "stelle": "KILOMETERSTAND: 123456", "unplausibel": ""}
    assert E["neu"]["beleg_nur_einheit_punkt"]["quelle"] == "beleg_einheit"
    assert E["neu"]["tacho_rein"]["quelle"] == "tacho"
    # ohne bisherigen Stand nie "sicher"
    assert E["neu"]["beleg_laufleistung_einheit"]["sicher"] is False
    leer = {"km": "", "quelle": "", "sicher": False, "stelle": "", "unplausibel": ""}
    # Beleg mit Litern/Preis/Uhrzeit/STAN/Belegnummer und ohne km: NICHTS (nicht 0, kein Literwert, keine Markierung)
    for name in ("beleg_ohne_km", "beleg_ohne_km_ohne_vorher", "beleg_km_null", "beleg_kilometerpreis", "tacho_nur_stoer"):
        assert E["neu"][name] == leer, name


def test_fundstelle_und_unplausibel_markiert(E):
    n = E["neu"]
    assert n["beleg_km_stand_punkt"]["stelle"] == "KM-STAND: 123.456"
    assert n["beleg_tachostand"]["stelle"] == "Tachostand 054321"  # Bezeichnung + Wertzeile darunter
    assert n["tacho_leerzeichen"]["stelle"] == "123 456 km"
    # unter bisherigem Stand / absurder Sprung: KEIN Vorschlag, aber markiert mit Fundstelle
    assert n["beleg_km_rueckwaerts"] == {"km": "", "quelle": "", "sicher": False,
                                         "stelle": "KM-STAND 98000", "unplausibel": "98000"}
    assert n["beleg_km_absurd"]["km"] == "" and n["beleg_km_absurd"]["unplausibel"] == "9123456"


def test_spaltensatz_ueber_wortboxen(E):
    s = E["spalten"]
    assert s["nur_roh"]["km"] == ""  # Rohtext allein: Bezeichnung und Wert getrennt
    assert "KILOMETERSTAND 123456" in s["zeilen"].splitlines()
    assert s["vision"]["km"] == "123456" and s["vision"]["quelle"] == "beleg_label"
    assert s["ohne_fta"]["km"] == ""  # ohne Boxen kein erfundener Wert


def test_parse_tankbeleg_unveraendert_plus_km(E):
    assert E["beleg"] == {"datum": "2026-11-14", "liter": "45.32", "preis": "81.08", "km": "123456"}
    assert E["beleg_alt_fuss"]["km"] == ""  # STAN 046183/420 / BELEG-NR 004711 nie als km


# ── TEIL B: App-Abschrift ───────────────────────────────────────────────────
def test_app_abschrift_gleich_edge(E):
    assert _fehler(E, "app") == []
    assert {k: v for k, v in E["app"].items()} == {k: v for k, v in E["neu"].items()}


def test_app_antwort_auswertung(E):
    A = E["antwort"]
    assert A["neu_edge"]["km"] == "123456" and A["neu_edge"]["sicher"] is True
    assert A["neu_edge_rueckwaerts"]["km"] == "123456"  # Edge-km unplausibel -> Rohtext
    assert A["alt_edge_kaputt"]["km"] == "123456"  # alte Fassung ohne km_quelle: Edge-km nie blind genommen
    assert A["alt_edge_nichts"]["km"] == ""
    assert A["tacho_alt_edge"]["km"] == "123456"  # alte Fassung ignoriert art -> App wertet Rohtext als Tacho
    assert A["tacho_neu_edge_sprung"]["km"] == ""  # +37000 > Tacho-Sprung 20000
    assert A["kein_json"]["km"] == ""
    assert A["vorher_text"]["km"] == "123456"  # _ganzZahl: "123.456" / "123.000"
    assert E["fromBeleg"] == "123456"
    assert A["neu_edge_unpl"]["km"] == "" and A["neu_edge_unpl"]["unplausibel"] == "98000"
    assert A["neu_edge_unpl"]["stelle"] == "KM-STAND 98000"


# ── TEIL C: Umkehrproben ────────────────────────────────────────────────────
def test_altstand_scheitert_an_den_neuen_faellen(E):
    neu = [p for p in PROBEN if p[5]]
    assert len(neu) >= 12
    for p in neu:
        assert E["alt_app"][p[0]] != p[4], p[0]
    # der alte Edge-Parser fand die Punkt-/Leerzeichen-Formate ebenfalls nicht
    for name in ("beleg_km_stand_punkt", "beleg_km_doppelpunkt_leer", "beleg_nur_einheit_punkt", "tacho_leerzeichen"):
        assert E["alt_edge"][name] != dict((p[0], p[4]) for p in PROBEN)[name], name
    # alte Faelle bleiben gleich (kein Rueckschritt)
    for p in PROBEN:
        if not p[5] and p[3] == "beleg":
            assert E["alt_app"][p[0]] == p[4], p[0]


def test_verdorbene_logik_wird_erkannt(node_exe):
    src = _lies(LOGIC)
    kaputt = src.replace("if (vorher > 0) return n >= vorher && n <= vorher + sprung;", "if (vorher > 0) return n > 0;", 1)
    assert kaputt != src
    E2 = _lauf(node_exe, logic_src=kaputt)
    assert _fehler(E2, "neu") != []
    html = _lies(INDEX_HTML)
    app = _app_block(html)
    kaputt_app = app.replace("if(vk>0)return n>=vk&&n<=vk+sprung;", "if(vk>0)return n>0;", 1)
    assert kaputt_app != app
    E3 = _lauf(node_exe, app_src=kaputt_app)
    assert _fehler(E3, "app") != []


# ── TEIL D: Verdrahtung ─────────────────────────────────────────────────────
def test_edge_index_verdrahtung():
    s = _lies(INDEX_TS)
    assert 'import { kmAusVision, parseTankbeleg } from "./logic.ts";' in s
    assert "function parseTankbeleg" not in s  # nur noch in logic.ts
    assert 'if (body?.art === "tacho") art = "tacho";' in s
    assert "kmAusVision(rawText, r0?.fullTextAnnotation, kmVorher, art)" in s
    # abwaertskompatibel: alle alten Felder bleiben in der Antwort
    m = re.search(r"return json\(\{ ok: true, \.\.\.fields, (.*?) \}\);", s)
    assert m and "confidence" in m.group(1) and "rawText" in m.group(1) and "km_quelle" in m.group(1)
    assert "GOOGLE_VISION_KEY" in s and "auth.getUser()" in s  # Auth/Schluessel unberuehrt


def test_app_verdrahtung():
    h = _lies(INDEX_HTML)
    assert h.count("/*@OCR-KM-START") == 1 and h.count("/*@OCR-KM-END*/") == 1
    assert "body:JSON.stringify({image:dataUrl,kmVorher:_vk})" in h
    assert 'body:JSON.stringify({image:dataUrl,art:"tacho",kmVorher:_vk})' in h
    assert "const _ke=_kmAusAntwort(_j,_vk,'beleg');const _km=_ke.km;" in h
    assert h.count("setTankKm(_km);_tankKmVorschlag({feld:_km,km:_km,stelle:_ke.stelle,unplausibel:''},_vk);") == 2
    assert "const _tankKmVorschlag=(o,vk)=>{const v=o?Object.assign({},o,{fz:showTank,vk:vk}):null;setTankKmOcr(v);try{window.__tankKmOcr=v;}catch(_w){}};" in h
    # Hinweis nur fuer dasselbe Fahrzeug, solange Feld UND Fahrzeug-Stand noch zum Vorschlag passen (nach Speichern weg)
    assert "tankKmOcr&&tankKmOcr.fz===showTank&&tankKm===tankKmOcr.feld&&(_ganzZahl(((fahrzeuge||[]).find(f=>f.id===showTank)||{}).kmStand)||0)===tankKmOcr.vk&&React.createElement" in h
    assert "unplausibel, nicht übernommen" in h
    # neues Foto verwirft den alten Vorschlag (Beleg + Tacho)
    assert h.count("_tankKmVorschlag(null,0);") == 2
    assert "aus Foto erkannt – bitte prüfen" in h
    assert '_ikVw("kamera","Tacho fotografieren")' in h
    assert "onChange: e=>{handleTankFoto(e,parseTachoFoto);" in h
    # Tacho-Foto wird nie als Beleg gespeichert und nie automatisch gespeichert
    tacho = h[h.index("const parseTachoFoto=(dataUrl)=>{"):h.index("const handleTankFoto=(e,_ziel)=>{")]
    assert "setTankFoto" not in tacho and "addTank" not in tacho and "upd(" not in tacho
    # alter Pfad ueber nur KILOMETERSTAND ist weg
    assert "replace(/.*KILOMETERSTAND[^0-9]*/i,'')" not in h


def test_kontrolldialog_zeigt_zahl_und_fundstelle():
    h = _lies(INDEX_HTML)
    m = h[h.index("window._tankConfirmModal=function("):]
    m = m[:m.index("\n};\n")]
    assert "const _ko=init.kmOcr||window.__tankKmOcr||null;" in m
    assert "if(_ko&&_ko.km&&String(init.km)===String(_ko.km)&&(parseInt(_ko.vk,10)||0)===currentKm){" in m
    assert "'📷 aus Foto erkannt: '+Number(_ko.km).toLocaleString('de-AT')+' km – bitte prüfen'" in m
    assert "' · Stelle: »'+_ko.stelle+'«'" in m
    assert "oh.textContent=" in m and "oh.innerHTML" not in m  # Belegtext nie als HTML


def test_speichern_bleibt_teilschreiben():
    """Die Foto-km aendern nur das Formularfeld; gespeichert wird wie bisher ueber addTank -> Diff-PUT nur
    tank_log/km_stand (+ _tankAtomar-Hinweis fuer fz_tanklog_add). Nie das ganze Fahrzeug."""
    h = _lies(INDEX_HTML)
    add = h[h.index("  const addTank=async (fzId)=>{"):h.index("  const addSchaden=async(fzId)=>{")]
    m = re.search(r"\},u=>\(\{(_tankAtomar:\{[^}]*\},[^)]*)\}\)\);", add)
    assert m, "Diff-PUT von addTank nicht gefunden"
    keys = {k.split(":")[0] for k in re.sub(r"\{[^}]*\}", "", m.group(1)).split(",") if k}
    assert keys <= {"_tankAtomar", "tankLog", "kmStand", "kmLogId"}, keys
    for name in ("parseTankBeleg", "parseTachoFoto"):
        a = h.index("  const " + name + "=(dataUrl)=>{")
        b = h.index("\n  };\n", a)
        teil = h[a:b]
        assert "upd(" not in teil and "_sbPatch" not in teil and "apiPatch" not in teil and "addTank" not in teil, name
