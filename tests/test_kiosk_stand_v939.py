# -*- coding: utf-8 -*-
"""v3.9.939 Phase B1 - die Wandtafel behauptet keine Aktualitaet mehr.

ZWEI BEFUNDE, EINE WURZEL
─────────────────────────
S1  "Stand HH:MM" war die UHR. Gemessen ueber 80 Sekunden: der Stand wanderte
    09:42 -> 09:43, waehrend die Aktualisierung mit HTTP 500 scheiterte.
    `setStand(new Date())` stand VOR dem Abruf und unbedingt. Wer die Tafel
    fotografiert, sah eine frische Uhrzeit ueber moeglicherweise stundenalten
    Daten.

A1  `window.__kioskAsErr` faengt HTTP 500, HTTP 401 und kaputtes JSON - aber
    NICHT den abgebrochenen fetch. Gemessen: 500 -> 'HTTP500', 401 ->
    'HTTP401', kaputtes JSON -> 'parse', Erfolg -> null, ABGEBROCHEN ->
    undefined. Genau im haeufigsten Ausfall blieb der Marker leer.

WIE HIER GEMESSEN WIRD
──────────────────────
Der Marker wird AUSGEFUEHRT, nicht gelesen: `_kioskWeekArbeitsscheine` wird
woertlich aus index.html geschnitten und unter Node mit vier verschiedenen
fetch-Attrappen gefahren. Ein Riegel, der nur nach `'net'` im Quelltext
sucht, koennte nicht unterscheiden, ob der Zweig auch ERREICHT wird - und
genau darum ging es: der alte Code hatte die Absicht im Kommentar
("RLS/Netz") und den Zweig nicht.
"""
import io
import json
import re
import subprocess
import sys
import tempfile
import os

import pytest

from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def roh():
    return io.open(str(WURZEL / "index.html"), encoding="utf-8", newline="").read()


@pytest.fixture(scope="module")
def marker_ergebnisse(roh):
    """Faehrt _kioskWeekArbeitsscheine unter Node mit vier fetch-Attrappen.

    Gibt {fall: markerwert} zurueck. `undefined` erscheint als "<undefined>",
    damit der Unterschied zu null sichtbar bleibt - das war der ganze Befund.
    """
    i = roh.index("async function _kioskWeekArbeitsscheine(){")
    j = roh.index("/* v3.9.706:", i)
    fn = roh[i:j]
    assert "_authRetry" in fn and len(fn) < 3000, len(fn)

    prog = """
const FAELLE = {
  ok:      {art:"ok"},
  http500: {art:"status", status:500},
  http401: {art:"status", status:401},
  parse:   {art:"parse"},
  netz:    {art:"wurf"}
};
const ergebnis = {};
const SB_REST = "http://x";
function _fT(o){return o;}
function _sbH(h){return h;}
function _kioskWeekRange(){return {p_from:"2026-01-01",p_to:"2026-01-07"};}
let _fall = null;
async function _authRetry(fn){ return await fn(); }
global.fetch = async function(){
  const f = FAELLE[_fall];
  if (f.art === "wurf") throw new TypeError("Failed to fetch");
  if (f.art === "status") return {ok:false, status:f.status,
                                  text: async()=>"body", json: async()=>null};
  if (f.art === "parse") return {ok:true, status:200,
                                 text: async()=>"", json: async()=>{throw new Error("bad json");}};
  return {ok:true, status:200, text: async()=>"[]", json: async()=>[{id:1}]};
};
global.window = {};
global.console = {error:()=>{}, warn:()=>{}, log:()=>{}};
__FN__
(async()=>{
  for (const name of Object.keys(FAELLE)) {
    _fall = name;
    delete global.window.__kioskAsErr;
    let ret = null, warf = false;
    try { ret = await _kioskWeekArbeitsscheine(); } catch(e){ warf = true; }
    const m = global.window.__kioskAsErr;
    ergebnis[name] = {marker: (m === undefined ? "<undefined>" : m),
                      rueckgabe: (ret === null ? "null" : typeof ret),
                      warf: warf};
  }
  process.stdout.write(JSON.stringify(ergebnis));
})();
""".replace("__FN__", fn)

    tmp = tempfile.NamedTemporaryFile(suffix=".js", delete=False, mode="w",
                                      encoding="utf-8")
    try:
        tmp.write(prog)
        tmp.close()
        r = subprocess.run(["node", tmp.name], capture_output=True, text=True,
                           timeout=60)
        assert r.returncode == 0, "Node: %s" % (r.stderr[-900:],)
        return json.loads(r.stdout)
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass


# ── A1: der Marker ist vollstaendig ───────────────────────────────────────

def test_der_abgebrochene_fetch_setzt_den_marker(marker_ergebnisse):
    """DER Befund. Vorher blieb hier <undefined>, und die Tafel zeigte stumm
    die Vorwoche - im haeufigsten Ausfall von allen."""
    d = marker_ergebnisse["netz"]
    assert d["marker"] == "net", (
        "Bei abgebrochenem fetch steht im Marker %r statt 'net'." % d["marker"])
    assert not d["warf"], (
        "Die Funktion wirft jetzt nach aussen - der Aufrufer im Boot faengt "
        "das nicht, und die Tafel waere leer statt eine Woche alt.")
    assert d["rueckgabe"] == "null", (
        "Die Rueckgabe ist %r statt null - der Consumer soll bewusst die alte "
        "Woche behalten (Offline-Faehigkeit)." % d["rueckgabe"])


@pytest.mark.parametrize("fall,erwartet", [
    ("ok", None),
    ("http500", "HTTP500"),
    ("http401", "HTTP401"),
    ("parse", "parse"),
])
def test_die_bestehenden_faelle_sind_unveraendert(marker_ergebnisse, fall, erwartet):
    """Der Netzfall durfte die vier anderen nicht verschieben."""
    ist = marker_ergebnisse[fall]["marker"]
    assert ist == erwartet, (
        "Fall %s liefert %r statt %r." % (fall, ist, erwartet))


def test_der_erfolgsfall_gibt_daten_zurueck(marker_ergebnisse):
    """KOEDER. Lieferte auch der Gutfall null, sagten die Fehlerfaelle nichts
    aus - dann tut die Funktion naemlich nie etwas."""
    assert marker_ergebnisse["ok"]["rueckgabe"] == "object", (
        "Der Erfolgsfall gibt %r zurueck - dann misst diese Datei nichts."
        % marker_ergebnisse["ok"]["rueckgabe"])


# ── S1: der Stand ist das Datenalter ──────────────────────────────────────

def test_der_stand_wird_nur_nach_erfolg_gesetzt(roh):
    """Vorher stand `setStand(new Date())` VOR dem Abruf und unbedingt."""
    i = roh.find("Auto-Refresh 60s (Fetch erneut + Stand updaten)")
    assert i > 0, "Der Auffrisch-Umlauf der Wandtafel wurde nicht gefunden."
    # Das Fenster endet an der Abhaengigkeitsliste DIESES Effekts, nicht
    # nach 2600 Zeichen: die pauschale Laenge reichte in den naechsten
    # Effekt hinein und zaehlte dessen Timer mit - mein Pruefstand meldete
    # "zwei Timer", wo einer steht.
    _e = roh.index("},60000)", i)
    block = roh[i:roh.index(",[]);", _e) + 5]
    assert "setStand(new Date());" in block, (
        "Im Umlauf wird der Stand nicht mehr gesetzt.")
    # KOMMENTARBLIND pruefen. Der erklaerende Kommentar an dieser Stelle
    # nennt "setStand(new Date()) stand hier VOR dem Abruf" - er sagt ja
    # gerade, was FRUEHER war. Ein roher Textriegel schlaegt darauf an und
    # meldet den Fehler, den er beschreibt. Das ist mir in diesem Umbau
    # zum dritten Mal passiert; dafuer gibt es scripts/code_scan.py.
    import sys as _sys
    _sys.path.insert(0, str(WURZEL / "scripts"))
    from code_scan import ist_code as _ist_code
    vor_abruf_ende = i + block.index("const raw=")
    feld = _ist_code(roh)
    im_code = [p for p in range(i, vor_abruf_ende)
               if feld[p] and roh.startswith("setStand", p)]
    assert not im_code, (
        "Der Stand wird VOR dem Abruf gesetzt (Codestellen %s) - dann "
        "wandert er weiter, auch wenn der Abruf scheitert. Genau der "
        "Befund." % im_code)
    i_pruef = block.index("if(Array.isArray(raw))")
    i_setz = block.index("setStand(new Date());")
    assert i_pruef < i_setz, (
        "Der Stand wird gesetzt, bevor geprueft ist, ob Daten ankamen.")


def test_die_uhr_und_das_datenalter_sind_zwei_merker(roh):
    assert "const [jetzt,setJetzt]=_react.useState.call(void 0, Date.now());" in roh, (
        "Es gibt keinen getrennten Uhr-Merker - dann kann der Alterstext nicht "
        "mitwachsen, ohne den Stand zu verschieben.")
    assert "setJetzt(Date.now());" in roh, "Die Uhr wird nicht fortgeschrieben."
    assert roh.count("setJetzt(Date.now())") == 1, (
        "Die Uhr wird an %d Stellen gestellt." % roh.count("setJetzt(Date.now())"))


def test_die_schwelle_ist_eine_benannte_konstante(roh):
    m = re.search(r"const KIOSK_STAND_WARN_MS=([^;]+);", roh)
    assert m, "Die Schwelle ist keine benannte Konstante."
    assert "15" in m.group(1) and "60" in m.group(1), (
        "Die Schwelle ist %r - erwartet 15 Minuten." % m.group(1))
    assert roh.count("KIOSK_STAND_WARN_MS") >= 2, (
        "Die Konstante wird nirgends benutzt.")


def test_die_anzeige_nennt_das_alter_im_klartext(roh):
    i = roh.find('"Daten von "')
    assert i > 0, "Die Anzeige sagt nicht 'Daten von ...'."
    block = roh[max(0, i - 1400):i + 260]
    assert "jetzt-stand.getTime()" in block, (
        "Das Alter wird nicht aus der Differenz von Uhr und Stand gerechnet.")
    assert "KIOSK_STAND_WARN_MS" in block, (
        "Die Anzeige kennt die Schwelle nicht.")
    assert "nicht aktualisiert" in block, (
        "Es gibt keinen Klartext zum Alter - ein Zeitstempel allein sagt nicht, "
        "dass er alt ist.")


def test_die_warnung_haengt_nicht_an_der_farbe_allein(roh):
    """Auf einer Baustelle steht man in der Sonne, und Rot-Gruen ist die
    haeufigste Farbsehschwaeche. Farbe darf die Information nicht tragen."""
    i = roh.find('"Daten von "')
    block = roh[max(0, i - 1400):i + 260]
    assert "_warn?20:14" in block, (
        "Die Schriftgroesse aendert sich im Warnfall nicht - auf "
        "Wandmonitor-Entfernung ist das der wichtigste Unterschied.")
    assert "fontWeight:_warn?800:400" in block, (
        "Das Schriftgewicht aendert sich nicht.")
    assert "_warn?(' \\u00b7 '+_txt):''" in block or "_txt" in block, (
        "Der Warnfall traegt keinen zusaetzlichen TEXT - dann haengt die "
        "Information an der Farbe allein.")


def test_es_bleibt_bei_einem_umlauf(roh):
    """Kein zweiter Timer: der bestehende 60-s-Umlauf macht beides."""
    i = roh.find("Auto-Refresh 60s (Fetch erneut + Stand updaten)")
    # Das Fenster endet an der Abhaengigkeitsliste DIESES Effekts, nicht
    # nach 2600 Zeichen: die pauschale Laenge reichte in den naechsten
    # Effekt hinein und zaehlte dessen Timer mit - mein Pruefstand meldete
    # "zwei Timer", wo einer steht.
    _e = roh.index("},60000)", i)
    block = roh[i:roh.index(",[]);", _e) + 5]
    assert block.count("setInterval") == 1, (
        "Im Auffrisch-Block stehen %d Timer - erwartet genau einer."
        % block.count("setInterval"))
