# -*- coding: utf-8 -*-
"""v3.9.928 - sechs Verbraucher, bei denen der Rechtefehler nicht ANGEZEIGT,
sondern GESCHRIEBEN wird.

DIE WURZEL (v3.9.910, unveraendert)
-----------------------------------
`_sbGet` / `_sbGetOrder` / `_sbGetUsersSafe` geben bei 401/403 ein leeres Array
auf dem ERFOLGSPFAD zurueck. Kein Auffangzweig sieht das. Das Array traegt seit
v3.9.910 die Marke `__rlsFehler`, `_rlsLeer(liste)` liest sie.

v3.9.911 (Kacheln), v3.9.912 (Warteschlange), v3.9.913 (Fahrtenbuch) und
v3.9.926 (Zeitwoche) haben je EINEN Verbraucher nachgezogen - jeder einzeln und
meist zufaellig gefunden. Dieser Riegel deckt die Fundorte ab, bei denen die
Folge nicht eine falsche Anzeige ist, sondern ein LOESCHEN, ein UEBERSCHREIBEN
oder ein abgelegter BELEG:

  1. Wochenplanung. ODB.save auf den Speicher meta mit einem LEEREN Objekt ->
     der Offline-Vorrat der Dispo wird ersetzt; beim naechsten Start ohne Netz
     ist die Wochenplanung weg. Der Zwilling an derselben Ablage (:8546) fragt
     laengst Object.keys(...).length - diese Stelle fragte nichts.

  2. Projektfotos. ODB.save auf fotos_<id> mit einer LEEREN Liste -> die
     Baudokumentation eines Projekts wird aus dem Geraetespeicher geloescht.
     Der Auffangzweig direkt darunter laedt danach genau das, was der Fehler
     hinterlassen hat.

  3. Seed-Waechter aus v3.9.208. Er sollte verhindern, dass ein transienter
     Leer-Load echte Projekte/Mitarbeiter mit INIT_PROJECTS bzw. MONT-Festwerten
     ueberschreibt. Sein fail-closed-Zweig war der `catch` - und seit v3.9.910
     wirft ein Rechtefehler nicht mehr. Der Waechter war damit TOT: ein 403 sah
     aus wie "die Tabelle ist wirklich leer", also genau wie der Ausloeser.

  4. Bautagebuch-Ausdruck. Fuer "wir wissen es nicht" gab es in diesem Beleg
     keine Darstellung - der Fototeil fiel stumm weg. Deshalb ein eigener
     Zustand, und weil es ein Beleg ist, sagt der Ausdruck es selbst.

  5. Stempel-Pausenregeln. Das Formular baut sein Speicherobjekt AUS DEM NICHTS
     neu auf (nur aus defVal und roles). Waren die beiden Lesevorgaenge nicht
     lesbar, zeigte es den Festwert und KEINE Rolle - ein Klick auf Speichern
     ersetzte jede rollenbezogene Pausenregel durch den Standardwert. Lohn.

  6. Personalzeit-Nachweis. stempel_log leer -> der Ausdruck zeigt einen Monat
     OHNE Stempelzeiten samt Soll/Ist-Saldo, obwohl die Zeiten in der Datenbank
     liegen. Derselbe Fall wie das Fahrtenbuch in v3.9.913.

WAS DIESER RIEGEL MISST
-----------------------
Nicht die Schreibweise. Die Rumpfe werden WOERTLICH aus index.html geschnitten
und mit Node AUSGEFUEHRT - je mit drei bis vier Faellen:

    markiert (401/403)  -> es darf NICHT geschrieben / gedruckt / geseedet werden
    wirklich leer       -> es MUSS geschrieben / gedruckt / geseedet werden
    Daten da            -> Normalfall unveraendert

DER ZWEITE FALL IST DER WICHTIGERE. Ein Auffangzweig, der IMMER greift, waere
schlimmer als der Fehler, den er behebt: ein geloeschtes Foto tauchte aus dem
Vorrat wieder auf, eine geleerte Woche kaeme nie im Vorrat an, eine wirklich
leere Tabelle wuerde nie initialisiert, und auf jedem zweiten Nachweis stuende
eine Stoerung, die es nicht gab.

Jede Reparatur hat ausserdem eine GEGENPROBE: der Riegel wird aus dem
geschnittenen Rumpf wieder entfernt und der Schaden muss zurueckkehren. Ohne sie
waere nicht belegt, dass der Messaufbau den Fehler ueberhaupt SIEHT.

ROT, BIS DIE ANKER/ERSATZ-PAARE ANGEWENDET SIND
-----------------------------------------------
Dieser Riegel ist die ABNAHMEPRUEFUNG fuer v3.9.928, nicht die Beschreibung des
Ist-Zustands. Gegen den unveraenderten Stand (v3.9.926) sind 12 der 13 Faelle
rot; gegen eine Fassung mit allen 14 Paaren sind alle 13 gruen - so gemessen
gegen eine Arbeitskopie, bevor die Paare uebergeben wurden.

NICHT ABGEDECKT - ABSICHTLICH
-----------------------------
Das Kundenportal. Dort liefert RLS ohne Policy HTTP 200 mit 0 Zeilen (belegt in
sql/portal_anon_policy_drop_v3.9.156.sql: "GET /projects?select=id -> 0 rows").
Ein Rechtefehler kommt dort gar nicht als Fehler an, die Marke kann also nie
gesetzt werden. Jeder Versuch, sie dort zu lesen, misst nichts.
"""
import json
import re
import subprocess

from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]
INDEX = WURZEL / "index.html"


def _quelle():
    return INDEX.read_text(encoding="utf-8")


def _schnitt(quelle, anfang, ende):
    assert quelle.count(anfang) == 1, (
        "Anfangsmarke nicht eindeutig (%d Treffer) - der Riegel misst dann "
        "nichts: %r" % (quelle.count(anfang), anfang[:60]))
    i = quelle.index(anfang)
    j = quelle.index(ende, i) + len(ende)
    return quelle[i:j]


def _node(programm, tmp_path, name, eingabe):
    p = tmp_path / name
    p.write_text(programm, encoding="utf-8")
    r = subprocess.run(["node", str(p), json.dumps(eingabe)],
                       capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, r.stderr
    return {z["name"]: z for z in json.loads(r.stdout)}


# ══════════════════════════════════════════════════════════════════════════
# 1. WOCHENPLANUNG - der Offline-Vorrat der Dispo
# ══════════════════════════════════════════════════════════════════════════

WP_ANFANG = "const wprs=await API.getWeekplanRows();"
WP_ENDE = ('try{ODB.save("meta",wpH);}'
           "catch(_e){console.warn('[silent-odb]',_e&&_e.message||_e);}")

WP_KOPF = """
"use strict";
var _gespeichert = null;
var _merk = function(store, data){ _gespeichert = {store: store, data: data}; };
var ODB = { save: _merk, saveProj: _merk };
function _rlsLeer(l){ try{ return !!(l && l.__rlsFehler); }catch(e){ return false; } }
function _safeJsonParse(s, d){ try{ return JSON.parse(s); }catch(e){ return d; } }
var window = {};
var _historie = null;
function setWpHistory(f){ _historie = (typeof f === 'function') ? f({}) : f; }
async function _lauf(vomServer){
  _gespeichert = null; _historie = null;
  var isPoll = false;
  var API = { getWeekplanRows: function(){ return Promise.resolve(vomServer); } };
"""

WP_FUSS = """
  return {gespeichert: _gespeichert, historie: _historie};
}
var f = JSON.parse(process.argv[2]);
var aus = [];
(async function(){
  for (const fall of f.faelle) {
    var vom = (fall.zeilen || []).slice();
    if (fall.markiert) { vom.__rlsFehler = 403; }
    await _lauf(vom);
    aus.push({
      name: fall.name,
      geschrieben: _gespeichert !== null,
      store: _gespeichert ? _gespeichert.store : null,
      wochen: _gespeichert ? Object.keys(_gespeichert.data).length : -1
    });
  }
  console.log(JSON.stringify(aus));
})();
"""

WP_FAELLE = [
    {"name": "Rechtefehler (403)", "markiert": True, "zeilen": []},
    {"name": "wirklich leer", "markiert": False, "zeilen": []},
    {"name": "Daten da", "markiert": False, "zeilen": [
        {"row_id": "r1", "year": 2026, "week": 36, "bvh": "BVH A",
         "proj_id": "p1", "bem": "", "z": {}, "sort_order": 1},
        {"row_id": "r2", "year": 2026, "week": 37, "bvh": "BVH B",
         "proj_id": "p2", "bem": "", "z": {}, "sort_order": 1},
    ]},
]


def test_dispo_ein_rechtefehler_loescht_den_offline_vorrat_nicht(tmp_path):
    schnitt = _schnitt(_quelle(), WP_ANFANG, WP_ENDE)
    aus = _node(WP_KOPF + schnitt + WP_FUSS, tmp_path, "wp.js",
                {"faelle": WP_FAELLE})

    assert aus["Rechtefehler (403)"]["geschrieben"] is False, (
        "Bei einem Rechtefehler darf der Offline-Vorrat der Dispo NICHT "
        "ueberschrieben werden - sonst ist die Wochenplanung beim naechsten "
        "Start ohne Netz weg. Geschrieben in: %s"
        % aus["Rechtefehler (403)"]["store"])

    # DER WICHTIGERE FALL
    assert aus["wirklich leer"]["geschrieben"] is True, (
        "Eine wirklich leere, GELESENE Antwort muss weiterhin in den Vorrat - "
        "sonst kaeme eine geleerte Woche dort nie an.")

    assert aus["Daten da"]["wochen"] == 2, (
        "Der Normalfall muss zwei Kalenderwochen in den Vorrat schreiben. "
        "Geschrieben: %d" % aus["Daten da"]["wochen"])


def test_gegenprobe_dispo_ohne_riegel_wird_der_vorrat_geleert(tmp_path):
    """Ohne diese Umkehr waere nicht belegt, dass der Aufbau den Fehler SIEHT."""
    schnitt = _schnitt(_quelle(), WP_ANFANG, WP_ENDE)
    alt = schnitt.replace("if(_rlsLeer(wprs))return;", "", 1)
    assert alt != schnitt, (
        "Die Umkehr hat nichts entfernt - der Riegel misst nichts")

    aus = _node(WP_KOPF + alt + WP_FUSS, tmp_path, "wp_alt.js",
                {"faelle": WP_FAELLE})
    assert aus["Rechtefehler (403)"]["geschrieben"] is True, (
        "Die alte Fassung MUSS bei einem Rechtefehler schreiben - sonst misst "
        "dieser Riegel nichts.")
    assert aus["Rechtefehler (403)"]["wochen"] == 0, (
        "Und sie MUSS ein LEERES Objekt schreiben - das ist der Schaden.")


# ══════════════════════════════════════════════════════════════════════════
# 2. PROJEKTFOTOS - die Baudokumentation im Geraetespeicher
# ══════════════════════════════════════════════════════════════════════════

FO_ANFANG = "let _gotServer=false;"
# v3.9.928 NACHGEZOGEN: dieser Riegel wurde gegen eine voruebergehend
# gepatchte Fassung geschrieben, in der ein PARALLELER Lauf ODB.save schon
# zu ODB.saveProj gemacht hatte. Diese Aenderung ist nicht im Baum - der
# Anwender der Paare hat es selbst gemerkt und an genau dieser Stelle
# abgebrochen. Die Schreibweise, die wirklich dasteht, ist ODB.save.
# v3.9.928: DER NAME DIESES AUFRUFS HAT SICH BINNEN EINER STUNDE ZWEIMAL
# GEAENDERT - ODB.saveProj, dann ODB.save, dann wieder ODB.saveProj, weil
# v3.9.927 einen eigenen Projekt-Speicher angelegt hat. Zweimal wurde dieser
# Riegel rot, ohne dass sich am VERHALTEN etwas geaendert haette.
#
# Deshalb haengt der Schnitt nicht mehr am Funktionsnamen. Die Eigenschaft
# ist: der Foto-Vorrat wird geschrieben, und dieses Schreiben ist gegen einen
# Rechtefehler abgesichert. Wie die Speicherfunktion heisst, ist nicht die
# Eigenschaft - es ist ihr Name.
_FO_SCHWANZ = '("fotos_"+p.id,rows||[]);'
_FO_MUSTER = re.compile(r'ODB\.\w+' + re.escape(_FO_SCHWANZ))


def _fo_ende(quelle):
    m = _FO_MUSTER.search(quelle)
    assert m, ('Der Schreibvorgang des Foto-Vorrats ist nicht mehr zu '
               'finden - dieser Riegel misst dann nichts.')
    return m.group(0)

FO_KOPF = """
"use strict";
var _gespeichert = null;
var _angezeigt = null;
var _merk = function(store, data){ _gespeichert = {store: store, data: data}; };
var ODB = { save: _merk, saveProj: _merk };
function _rlsLeer(l){ try{ return !!(l && l.__rlsFehler); }catch(e){ return false; } }
var _rowsFuerLauf = null;
async function _sbGetOrder(){ return _rowsFuerLauf; }
function setPhotos(x){ _angezeigt = x; }
var API = { getToken: function(){ return "jwt"; } };
var p = { id: "P-1" };
var active = true;
async function _lauf(vomServer){
  _gespeichert = null; _angezeigt = null; _rowsFuerLauf = vomServer;
"""

FO_FUSS = """
  }
  return {gespeichert: _gespeichert, angezeigt: _angezeigt, gotServer: _gotServer};
}
var f = JSON.parse(process.argv[2]);
var aus = [];
(async function(){
  for (const fall of f.faelle) {
    var vom = (fall.zeilen || []).slice();
    if (fall.markiert) { vom.__rlsFehler = 403; }
    var r = await _lauf(vom);
    aus.push({
      name: fall.name,
      geschrieben: r.gespeichert !== null,
      anzahlImVorrat: r.gespeichert ? r.gespeichert.data.length : -1,
      angezeigt: r.angezeigt === null ? -1 : r.angezeigt.length,
      gotServer: !!r.gotServer
    });
  }
  console.log(JSON.stringify(aus));
})();
"""

FO_FAELLE = [
    {"name": "Rechtefehler (403)", "markiert": True, "zeilen": []},
    {"name": "wirklich keine Fotos", "markiert": False, "zeilen": []},
    {"name": "Fotos da", "markiert": False,
     "zeilen": [{"id": "f1"}, {"id": "f2"}, {"id": "f3"}]},
]


def test_fotos_ein_rechtefehler_loescht_den_bildvorrat_nicht(tmp_path):
    # Der geschnittene Rumpf steht in index.html innerhalb von
    # `if(API.getToken()){` - die schliessende Klammer liegt hinter der
    # Endmarke und wird im FUSS ergaenzt. Die Verzweigungen selbst bleiben
    # woertlich, wie sie in der Datei stehen.
    _q = _quelle()
    schnitt = _schnitt(_q, FO_ANFANG, _fo_ende(_q))
    aus = _node(FO_KOPF + schnitt + FO_FUSS, tmp_path, "fo.js",
                {"faelle": FO_FAELLE})

    assert aus["Rechtefehler (403)"]["geschrieben"] is False, (
        "Bei einem Rechtefehler darf der Bildvorrat des Projekts NICHT "
        "ueberschrieben werden - die Baudokumentation waere danach auch ohne "
        "Netz weg.")
    assert aus["Rechtefehler (403)"]["angezeigt"] == -1, (
        "Und die leere Liste darf auch nicht als Ergebnis angezeigt werden.")
    assert aus["Rechtefehler (403)"]["gotServer"] is False, (
        "_gotServer muss false bleiben, damit der Geraetespeicher darunter "
        "einspringt.")

    # DER WICHTIGERE FALL
    assert aus["wirklich keine Fotos"]["geschrieben"] is True, (
        "Ein Projekt, das WIRKLICH keine Fotos hat, muss die leere Liste "
        "weiterhin in den Vorrat schreiben - sonst taucht ein geloeschtes Foto "
        "aus dem Vorrat wieder auf.")
    assert aus["wirklich keine Fotos"]["anzahlImVorrat"] == 0

    assert aus["Fotos da"]["anzahlImVorrat"] == 3, (
        "Der Normalfall muss die drei Fotos in den Vorrat schreiben.")
    assert aus["Fotos da"]["angezeigt"] == 3


def test_gegenprobe_fotos_ohne_riegel_wird_der_bildvorrat_geleert(tmp_path):
    _q = _quelle()
    schnitt = _schnitt(_q, FO_ANFANG, _fo_ende(_q))
    alt = re.sub(r'if\(!_rlsLeer\(rows\)\)(ODB\.\w+\()', r'\1', schnitt, count=1)
    assert alt != schnitt, (
        "Die Umkehr hat nichts entfernt - der Riegel misst nichts")

    aus = _node(FO_KOPF + alt + FO_FUSS, tmp_path, "fo_alt.js",
                {"faelle": FO_FAELLE})
    assert aus["Rechtefehler (403)"]["geschrieben"] is True, (
        "Die alte Fassung MUSS bei einem Rechtefehler schreiben.")
    assert aus["Rechtefehler (403)"]["anzahlImVorrat"] == 0, (
        "Und sie MUSS eine LEERE Liste schreiben - das ist der Schaden.")


# ══════════════════════════════════════════════════════════════════════════
# 3. DER SEED-WAECHTER AUS v3.9.208 - sein catch war der fail-closed-Zweig
# ══════════════════════════════════════════════════════════════════════════

SEED_KOPF = """
"use strict";
function _rlsLeer(l){ try{ return !!(l && l.__rlsFehler); }catch(e){ return false; } }
var _antwort = null;
var _wirft = false;
async function _sbGet(){ if(_wirft) throw new Error("HTTP500"); return _antwort; }
async function _lauf(antwort, wirft){
  _antwort = antwort; _wirft = wirft;
  let _pConfirmEmpty = true;
  let _wConfirmEmpty = true;
"""

SEED_FUSS = """
  return {p: _pConfirmEmpty, w: _wConfirmEmpty};
}
var f = JSON.parse(process.argv[2]);
var aus = [];
(async function(){
  for (const fall of f.faelle) {
    var vom = (fall.zeilen || []).slice();
    if (fall.markiert) { vom.__rlsFehler = 403; }
    var r = await _lauf(vom, !!fall.wirft);
    aus.push({name: fall.name, seedetProjekte: r.p, seedetWorker: r.w});
  }
  console.log(JSON.stringify(aus));
})();
"""

SEED_FAELLE = [
    {"name": "Rechtefehler (403)", "markiert": True, "zeilen": []},
    {"name": "wirklich leere Tabelle", "markiert": False, "zeilen": []},
    {"name": "Tabelle hat Zeilen", "markiert": False, "zeilen": [{"id": "x"}]},
    {"name": "harter Fehler (wirft)", "markiert": False, "zeilen": [],
     "wirft": True},
]

SEED_P = ('try{const _pc=await _sbGet("projects","select=id&limit=1");'
          "if(_rlsLeer(_pc)||(_pc&&_pc.length))_pConfirmEmpty=false;}"
          "catch(_pe){_pConfirmEmpty=false;}")
SEED_W = ('try{const _wc=await _sbGet("workers","select=id&limit=1");'
          "if(_rlsLeer(_wc)||(_wc&&_wc.length))_wConfirmEmpty=false;}"
          "catch(_we){_wConfirmEmpty=false;}")


def _seed_schnitt(quelle):
    for marke in (SEED_P, SEED_W):
        assert quelle.count(marke) == 1, (
            "Der Seed-Waechter steht nicht (mehr) genau einmal in dieser "
            "Form - der Riegel misst dann nichts: %r" % marke[:60])
    return SEED_P + "\n" + SEED_W


def test_seed_ein_rechtefehler_startet_den_ueberschreibenden_seed_nicht(tmp_path):
    aus = _node(SEED_KOPF + _seed_schnitt(_quelle()) + SEED_FUSS,
                tmp_path, "seed.js", {"faelle": SEED_FAELLE})

    assert aus["Rechtefehler (403)"]["seedetProjekte"] is False, (
        "Ein Rechtefehler darf den Projekt-Seed NICHT ausloesen - er "
        "ueberschreibt echte Projekte mit INIT_PROJECTS (der Fall, gegen den "
        "v3.9.208 geschrieben wurde).")
    assert aus["Rechtefehler (403)"]["seedetWorker"] is False, (
        "Ein Rechtefehler darf den Mitarbeiter-Seed NICHT ausloesen - er "
        "ueberschreibt Geburtsdatum, Fuehrerschein und SVNR mit MONT-Festwerten.")

    # DER WICHTIGERE FALL: der Waechter darf nicht IMMER blocken.
    assert aus["wirklich leere Tabelle"]["seedetProjekte"] is True, (
        "Eine WIRKLICH leere, gelesene Tabelle muss weiterhin initialisiert "
        "werden - sonst waere eine frische Installation nie befuellbar.")
    assert aus["wirklich leere Tabelle"]["seedetWorker"] is True

    assert aus["Tabelle hat Zeilen"]["seedetProjekte"] is False
    assert aus["harter Fehler (wirft)"]["seedetProjekte"] is False, (
        "Der alte fail-closed-Zweig (catch) muss unveraendert weiter greifen.")


def test_gegenprobe_seed_ohne_riegel_laeuft_der_seed_beim_rechtefehler(tmp_path):
    alt = (SEED_P.replace("_rlsLeer(_pc)||(_pc&&_pc.length)", "(_pc&&_pc.length)")
           + "\n"
           + SEED_W.replace("_rlsLeer(_wc)||(_wc&&_wc.length)", "(_wc&&_wc.length)"))
    aus = _node(SEED_KOPF + alt + SEED_FUSS, tmp_path, "seed_alt.js",
                {"faelle": SEED_FAELLE})
    assert aus["Rechtefehler (403)"]["seedetProjekte"] is True, (
        "Die alte Fassung MUSS beim Rechtefehler seeden - sonst misst dieser "
        "Riegel nichts.")
    assert aus["Rechtefehler (403)"]["seedetWorker"] is True
    assert aus["harter Fehler (wirft)"]["seedetProjekte"] is False, (
        "Der catch war auch vorher richtig - die Umkehr darf ihn nicht "
        "verfaelschen.")


# ══════════════════════════════════════════════════════════════════════════
# 4. BAUTAGEBUCH-AUSDRUCK - der Beleg sagt selbst, dass er unvollstaendig ist
# ══════════════════════════════════════════════════════════════════════════

BT_ANFANG = "let fotos=[];"
BT_ENDE = "if(fotos.length){"

BT_KOPF = """
"use strict";
function _rlsLeer(l){ try{ return !!(l && l.__rlsFehler); }catch(e){ return false; } }
var _hinweis = null;
var PAST = "#888";
function _blk(titel, text, y, farbe){ _hinweis = {titel: titel, text: text}; return y + 10; }
var _rowsFuerLauf = null;
async function _sbGet(){ if(_rowsFuerLauf === "wirft") throw new Error("HTTP500"); return _rowsFuerLauf; }
var API = { getToken: function(){ return "jwt"; } };
var e = { id: "BT-1" };
async function _lauf(vomServer){
  _hinweis = null; _rowsFuerLauf = vomServer;
  var y = 20;
"""

BT_FUSS = """
  }
  return {hinweis: _hinweis, fotos: fotos.length};
}
var f = JSON.parse(process.argv[2]);
var aus = [];
(async function(){
  for (const fall of f.faelle) {
    var vom = fall.wirft ? "wirft" : (fall.zeilen || []).slice();
    if (fall.markiert) { vom.__rlsFehler = 403; }
    var r = await _lauf(vom);
    aus.push({
      name: fall.name,
      hinweis: r.hinweis ? r.hinweis.titel : null,
      fotos: r.fotos
    });
  }
  console.log(JSON.stringify(aus));
})();
"""

BT_FAELLE = [
    {"name": "Rechtefehler (403)", "markiert": True, "zeilen": []},
    {"name": "wirklich keine Fotos", "markiert": False, "zeilen": []},
    {"name": "Fotos da", "markiert": False,
     "zeilen": [{"id": "f1"}, {"id": "f2"}]},
    {"name": "harter Fehler (wirft)", "markiert": False, "wirft": True},
]


def test_bautagebuch_der_ausdruck_meldet_seine_luecke(tmp_path):
    schnitt = _schnitt(_quelle(), BT_ANFANG, BT_ENDE)
    aus = _node(BT_KOPF + schnitt + BT_FUSS, tmp_path, "bt.js",
                {"faelle": BT_FAELLE})

    assert aus["Rechtefehler (403)"]["hinweis"] == "Fotodokumentation", (
        "Der Ausdruck muss selbst sagen, dass der Fototeil nicht geladen "
        "werden konnte - er ist ein abgelegter Beleg, und eine stumme Luecke "
        "sieht darin aus wie 'es gab keine Fotos'. Gedruckt: %r"
        % aus["Rechtefehler (403)"]["hinweis"])
    assert aus["harter Fehler (wirft)"]["hinweis"] == "Fotodokumentation", (
        "Der geworfene Fehler (Netz/5xx) ist derselbe Fall und muss denselben "
        "Hinweis drucken.")

    # DER WICHTIGERE FALL
    assert aus["wirklich keine Fotos"]["hinweis"] is None, (
        "Ein Eintrag, der WIRKLICH keine Fotos hat, darf keinen Warnhinweis "
        "tragen - sonst steht auf jedem zweiten Beleg eine Stoerung, die es "
        "nicht gab.")
    assert aus["Fotos da"]["hinweis"] is None
    assert aus["Fotos da"]["fotos"] == 2


def test_gegenprobe_bautagebuch_ohne_riegel_faellt_der_fototeil_stumm_weg(tmp_path):
    schnitt = _schnitt(_quelle(), BT_ANFANG, BT_ENDE)
    alt = schnitt.replace("if(_rlsLeer(r))_fotoUnlesbar=true;else ", "", 1)
    assert alt != schnitt, (
        "Die Umkehr hat nichts entfernt - der Riegel misst nichts")

    aus = _node(BT_KOPF + alt + BT_FUSS, tmp_path, "bt_alt.js",
                {"faelle": BT_FAELLE})
    assert aus["Rechtefehler (403)"]["hinweis"] is None, (
        "Die alte Fassung MUSS den Fototeil stumm weglassen - sonst misst "
        "dieser Riegel nichts.")
    assert aus["Fotos da"]["fotos"] == 2, (
        "Der Normalfall war auch vorher richtig - die Umkehr darf ihn nicht "
        "verfaelschen.")


# ══════════════════════════════════════════════════════════════════════════
# 5. STEMPEL-PAUSENREGELN - der Speichern-Knopf baut sein Objekt AUS DEM NICHTS
# ══════════════════════════════════════════════════════════════════════════

PR_LADEN_ANFANG = "let rls={};"
PR_LADEN_ENDE = "setRoles(rs);"

PR_LADEN_KOPF = """
"use strict";
function _rlsLeer(l){ try{ return !!(l && l.__rlsFehler); }catch(e){ return false; } }
var _cfg = null, _wk = null, _rollen = null;
async function _sbGet(tabelle){
  return (String(tabelle) === 'workers') ? _wk : _cfg;
}
function setRoles(x){ _rollen = x; }
async function _lauf(cfg, wk){
  _cfg = cfg; _wk = wk; _rollen = null;
  var a = true;
"""

PR_LADEN_FUSS = """
  return _rollen;
}
var f = JSON.parse(process.argv[2]);
var aus = [];
(async function(){
  for (const fall of f.faelle) {
    var cfg = (fall.cfg || []).slice(); if (fall.cfgMarkiert) cfg.__rlsFehler = 403;
    var wk  = (fall.wk  || []).slice(); if (fall.wkMarkiert)  wk.__rlsFehler  = 403;
    var r = await _lauf(cfg, wk);
    aus.push({name: fall.name, markiert: _rlsLeer(r), rollen: (r||[]).length});
  }
  console.log(JSON.stringify(aus));
})();
"""

PR_CFG_OK = [{"value": '{"default":30,"monteur":45,"buero":0}'}]
PR_WK_OK = [{"role": "monteur"}, {"role": "buero"}, {"role": "monteur"}]

PR_FAELLE = [
    {"name": "Rollen nicht lesbar", "cfg": PR_CFG_OK, "wk": [], "wkMarkiert": True},
    {"name": "Regeln nicht lesbar", "cfg": [], "cfgMarkiert": True, "wk": PR_WK_OK},
    {"name": "alles gelesen", "cfg": PR_CFG_OK, "wk": PR_WK_OK},
    {"name": "wirklich leer", "cfg": [], "wk": []},
]

PR_SAVE_ANFANG = "if(_rlsLeer(roles)){setMsg("
PR_SAVE_ENDE = "roles.forEach(r=>{const c=_clamp(vals[r]);if(c!==null)out[r]=c;});"

PR_SAVE_KOPF = """
"use strict";
function _rlsLeer(l){ try{ return !!(l && l.__rlsFehler); }catch(e){ return false; } }
var STEMPEL_PAUSE_MIN = 30;
var _gemeldet = null;
function setMsg(m){ _gemeldet = m; }
var window = { __toast: function(){} };
function _clamp(v){ var n = parseInt(v, 10); if (isNaN(n)) return null; if (n < 0) n = 0; if (n > 120) n = 120; return n; }
function _speichern(roles, vals, defVal){
"""

PR_SAVE_FUSS = """
  return out;
}
var f = JSON.parse(process.argv[2]);
var aus = [];
for (const fall of f.faelle) {
  var roles = (fall.roles || []).slice();
  if (fall.markiert) { roles.__rlsFehler = -1; }
  _gemeldet = null;
  var out = _speichern(roles, fall.vals || {}, fall.defVal);
  aus.push({
    name: fall.name,
    gespeichert: out !== undefined,
    schluessel: out === undefined ? -1 : Object.keys(out).length
  });
}
console.log(JSON.stringify(aus));
"""

PR_SAVE_FAELLE = [
    {"name": "Regeln nicht lesbar", "markiert": True, "roles": [], "vals": {},
     "defVal": "30"},
    {"name": "wirklich keine Rollen", "markiert": False, "roles": [],
     "vals": {}, "defVal": "30"},
    {"name": "Normalfall", "markiert": False, "roles": ["monteur", "buero"],
     "vals": {"monteur": "45", "buero": "0"}, "defVal": "30"},
]


def test_pausenregeln_die_marke_kommt_im_zustand_an(tmp_path):
    schnitt = _schnitt(_quelle(), PR_LADEN_ANFANG, PR_LADEN_ENDE)
    aus = _node(PR_LADEN_KOPF + schnitt + PR_LADEN_FUSS, tmp_path, "pr_load.js",
                {"faelle": PR_FAELLE})

    assert aus["Rollen nicht lesbar"]["markiert"] is True, (
        "Die Rollenliste muss die Marke in den Zustand mitnehmen - sonst kann "
        "der Speichern-Knopf sie nicht mehr sehen.")
    assert aus["Regeln nicht lesbar"]["markiert"] is True, (
        "Auch der unlesbare Regelsatz muss durchschlagen: sonst wird der "
        "Standardwert stillschweigend durch den Festwert im Code ersetzt.")

    # DER WICHTIGERE FALL
    assert aus["wirklich leer"]["markiert"] is False, (
        "Eine WIRKLICH leere, gelesene Antwort darf NICHT markiert werden - "
        "sonst blockte der Riegel jede frische Datenbank.")
    assert aus["alles gelesen"]["markiert"] is False
    assert aus["alles gelesen"]["rollen"] == 2, (
        "Der Normalfall muss zwei verschiedene Rollen finden. Gefunden: %d"
        % aus["alles gelesen"]["rollen"])


def test_pausenregeln_der_speichern_knopf_verweigert_bei_nichtwissen(tmp_path):
    schnitt = _schnitt(_quelle(), PR_SAVE_ANFANG, PR_SAVE_ENDE)
    aus = _node(PR_SAVE_KOPF + schnitt + PR_SAVE_FUSS, tmp_path, "pr_save.js",
                {"faelle": PR_SAVE_FAELLE})

    assert aus["Regeln nicht lesbar"]["gespeichert"] is False, (
        "Bei Nichtwissen darf NICHTS gespeichert werden - das Formular baut "
        "sein Objekt aus dem Nichts neu auf und wuerde jede rollenbezogene "
        "Pausenregel durch den Standardwert ersetzen. Das ist lohnrelevant.")

    # DER WICHTIGERE FALL
    assert aus["wirklich keine Rollen"]["gespeichert"] is True, (
        "Eine WIRKLICH leere, gelesene Rollenliste muss weiterhin speichern - "
        "eine frische Datenbank muss ihren Standardwert setzen koennen.")
    assert aus["Normalfall"]["schluessel"] == 3, (
        "Der Normalfall muss default + zwei Rollen schreiben. Geschrieben: %d"
        % aus["Normalfall"]["schluessel"])


def test_gegenprobe_pausenregeln_ohne_riegel_wird_die_regel_ersetzt(tmp_path):
    quelle = _quelle()

    laden = _schnitt(quelle, PR_LADEN_ANFANG, PR_LADEN_ENDE)
    laden_alt = laden.replace(
        "if(_unlesbar){try{rs.__rlsFehler=-1;}catch(_m){}}", "", 1)
    assert laden_alt != laden, "Die Umkehr hat nichts entfernt"
    aus = _node(PR_LADEN_KOPF + laden_alt + PR_LADEN_FUSS, tmp_path,
                "pr_load_alt.js", {"faelle": PR_FAELLE})
    assert aus["Rollen nicht lesbar"]["markiert"] is False, (
        "Die alte Fassung MUSS die Marke verlieren - sonst misst dieser "
        "Riegel nichts.")

    speichern = _schnitt(quelle, PR_SAVE_ANFANG, PR_SAVE_ENDE)
    speichern_alt = speichern.replace("if(_rlsLeer(roles)){", "if(false){", 1)
    assert speichern_alt != speichern, "Die Umkehr hat nichts entfernt"
    aus2 = _node(PR_SAVE_KOPF + speichern_alt + PR_SAVE_FUSS, tmp_path,
                 "pr_save_alt.js", {"faelle": PR_SAVE_FAELLE})
    assert aus2["Regeln nicht lesbar"]["gespeichert"] is True, (
        "Die alte Fassung MUSS speichern - das ist der Schaden.")
    assert aus2["Regeln nicht lesbar"]["schluessel"] == 1, (
        "Und sie MUSS genau EINEN Schluessel schreiben (nur default) - jede "
        "rollenbezogene Regel waere damit weg.")


# ══════════════════════════════════════════════════════════════════════════
# 6. PERSONALZEIT-NACHWEIS - ein Monat ohne Stempelzeiten ist ein Beleg
# ══════════════════════════════════════════════════════════════════════════

ST_ANFANG = "var evs=[];"
ST_ENDE = ('damit kein leerer Monat als Beleg hinausgeht","error",9000);'
           "return;}")

ST_KOPF = """
"use strict";
function _rlsLeer(l){ try{ return !!(l && l.__rlsFehler); }catch(e){ return false; } }
var _rowsFuerLauf = null;
async function _sbGet(){ if (_rowsFuerLauf === "wirft") throw new Error("HTTP500"); return _rowsFuerLauf; }
var _gewarnt = null;
var window = { __toast: function(t){ _gewarnt = t; } };
async function _lauf(vomServer){
  _rowsFuerLauf = vomServer; _gewarnt = null;
  var von = "2026-08-01", bis = "2026-08-31";
"""

ST_FUSS = """
  return {evs: evs.length};
}
var f = JSON.parse(process.argv[2]);
var aus = [];
(async function(){
  for (const fall of f.faelle) {
    var vom = fall.wirft ? "wirft" : (fall.zeilen || []).slice();
    if (fall.markiert) { vom.__rlsFehler = 403; }
    var r = await _lauf(vom);
    aus.push({name: fall.name, gedruckt: r !== undefined,
              evs: r ? r.evs : -1, gewarnt: _gewarnt !== null});
  }
  console.log(JSON.stringify(aus));
})();
"""

ST_FAELLE = [
    {"name": "Rechtefehler (403)", "markiert": True, "zeilen": []},
    {"name": "wirklich leerer Monat", "markiert": False, "zeilen": []},
    {"name": "Stempelzeiten da", "markiert": False,
     "zeilen": [{"ts": "2026-08-03T06:00:00Z"}, {"ts": "2026-08-03T16:00:00Z"}]},
    {"name": "harter Fehler (wirft)", "markiert": False, "wirft": True},
]


def test_stempelnachweis_kein_leerer_monat_als_beleg(tmp_path):
    schnitt = _schnitt(_quelle(), ST_ANFANG, ST_ENDE)
    aus = _node(ST_KOPF + schnitt + ST_FUSS, tmp_path, "st.js",
                {"faelle": ST_FAELLE})

    assert aus["Rechtefehler (403)"]["gedruckt"] is False, (
        "Bei einem Rechtefehler darf der Nachweis NICHT erstellt werden - er "
        "zeigte sonst einen Monat ohne Stempelzeiten samt Soll/Ist-Saldo, "
        "obwohl die Zeiten in der Datenbank liegen.")
    assert aus["Rechtefehler (403)"]["gewarnt"] is True, (
        "Und der Abbruch muss sichtbar sein - ein stiller Abbruch sieht aus "
        "wie ein kaputter Knopf.")
    assert aus["harter Fehler (wirft)"]["gedruckt"] is False, (
        "Der geworfene Fehler (Netz/5xx) ist derselbe Fall - der Auffangzweig "
        "markiert seine leere Liste selbst (Hausmuster v3.9.914).")

    # DER WICHTIGERE FALL
    assert aus["wirklich leerer Monat"]["gedruckt"] is True, (
        "Ein WIRKLICH leerer Monat (Urlaub, Eintritt spaeter) muss weiterhin "
        "gedruckt werden - sonst waere der Riegel schlimmer als der Fehler.")
    assert aus["Stempelzeiten da"]["evs"] == 2, (
        "Der Normalfall muss die zwei Stempelereignisse behalten.")


def test_gegenprobe_stempelnachweis_ohne_riegel_geht_der_leere_monat_hinaus(tmp_path):
    schnitt = _schnitt(_quelle(), ST_ANFANG, ST_ENDE)
    alt = schnitt.replace("if(_rlsLeer(evs)){", "if(false){", 1)
    assert alt != schnitt, "Die Umkehr hat nichts entfernt"

    aus = _node(ST_KOPF + alt + ST_FUSS, tmp_path, "st_alt.js",
                {"faelle": ST_FAELLE})
    assert aus["Rechtefehler (403)"]["gedruckt"] is True, (
        "Die alte Fassung MUSS drucken - sonst misst dieser Riegel nichts.")
    assert aus["Rechtefehler (403)"]["evs"] == 0, (
        "Und sie MUSS einen Monat mit NULL Stempelereignissen drucken - das "
        "ist der Beleg aus einem Rechtefehler.")
