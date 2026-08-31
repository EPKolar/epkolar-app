# -*- coding: utf-8 -*-
"""v3.9.926 - Die Zeiterfassung zeigte eine LEERE WOCHE, waehrend die Stunden
im Geraet lagen.

GEMESSEN (Mobil-Durchlauf, 390x900): fuenf Eintraege fuer M1 in dieser Woche im
Zwischenspeicher - auf dem Schirm NULL. Bricht man das Netz ganz ab, erscheinen
sie.

    API.getEntriesForWorker(...).then(data => { buildDayMap(data||[]); })
                                .catch(() => { ...aus dem Cache... })

`_sbGet` gibt bei 401/403 ein leeres Array auf dem ERFOLGSPFAD zurueck (die
Wurzel aus v3.9.910). Der Auffangzweig auf den Geraetespeicher lag im `.catch`
und wird nur erreicht, wenn `fetch` WIRFT. **Ein abgelaufener Zugang bei gutem
Empfang war damit ununterscheidbar von einer Woche ohne Stunden.**

WARUM DAS MEHR IST ALS EINE FALSCHE ANZEIGE
───────────────────────────────────────────
Der Monteur sieht seine eigenen, bereits erfassten Stunden nicht. Die
naheliegende Reaktion ist, sie noch einmal einzutragen - und dann stehen sie
doppelt im Lohnlauf.

Es ist derselbe Befund wie v3.9.912 (Abmelden bei unlesbarer Warteschlange) und
v3.9.913 (Fahrtenbuch): ein leeres Ergebnis auf dem Erfolgspfad, das wie eine
Tatsache aussieht. Nur wurde dieser Verbraucher damals nicht mitgezogen -
gefunden hat ihn erst der Mobil-Durchlauf, weil er mit ECHTEN Daten und
abgelaufenem Zugang gemessen hat.

WAS DIESER RIEGEL MISST
───────────────────────
Nicht die Schreibweise, sondern die Verzweigung: der echte `.then`-Rumpf wird
woertlich aus index.html geschnitten und mit Node AUSGEFUEHRT - einmal mit einer
RLS-markierten leeren Liste, einmal mit einer echt leeren.

    markiert -> der Cache muss gebaut werden
    echt leer -> die leere Woche ist richtig, der Cache darf NICHT einspringen

Der zweite Fall ist der wichtigere: ein Auffangzweig, der immer greift, wuerde
eine wirklich leere Woche mit alten Daten fuellen. Das waere schlimmer als der
Fehler, den er behebt.
"""
import json
import subprocess

from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]
INDEX = WURZEL / "index.html"

ANFANG = "const _wocheAusCache=()=>"
ENDE = "    });"

KOPF = """
"use strict";
var _gebaut = null;
function buildDayMap(x){ _gebaut = x; }
var _lwMounted = {current:true};
var _ladend = true;
function setLoading(v){ _ladend = v; }
function _rlsLeer(liste){ try{ return !!(liste && liste.__rlsFehler); }catch(e){ return false; } }

function _lauf(vomServer, cache, selWorker, from, to){
  _gebaut = null; _ladend = true;
  var entries = cache;
  var API = { getEntriesForWorker: function(){ return Promise.resolve(vomServer); } };
"""

FUSS = """
  return new Promise(function(res){
    setTimeout(function(){ res({gebaut:_gebaut, ladend:_ladend}); }, 0);
  });
}

var f = JSON.parse(process.argv[2]);
var CACHE = f.cache;
var aus = [];
(async function(){
  for (const fall of f.faelle) {
    var vom = fall.markiert ? [] : (fall.server || []);
    if (fall.markiert) { vom.__rlsFehler = 401; }
    var r = await _lauf(vom, CACHE, "M1", "2026-08-31", "2026-09-06");
    aus.push({name: fall.name, anzahl: (r.gebaut||[]).length, ladend: r.ladend});
  }
  console.log(JSON.stringify(aus));
})();
"""

CACHE = [
    {"worker": "M1", "datum": "2026-09-01", "id": "e1"},
    {"worker": "M1", "datum": "2026-09-02", "id": "e2"},
    {"worker": "M1", "datum": "2026-09-03", "id": "e3"},
    {"worker": "M2", "datum": "2026-09-01", "id": "fremd"},
    {"worker": "M1", "datum": "2026-07-01", "id": "alt"},
]

FAELLE = [
    {"name": "Rechtefehler (401)", "markiert": True},
    {"name": "wirklich leere Woche", "markiert": False, "server": []},
    {"name": "Server hat Daten", "markiert": False,
     "server": [{"worker": "M1", "datum": "2026-09-01", "id": "s1"},
                {"worker": "M1", "datum": "2026-09-02", "id": "s2"}]},
]


def _schnitt(quelle):
    i = quelle.index(ANFANG)
    j = quelle.index(ENDE, i) + len(ENDE)
    return quelle[i:j]


def _lauf(programm, tmp_path, name):
    p = tmp_path / name
    p.write_text(programm, encoding="utf-8")
    r = subprocess.run(["node", str(p), json.dumps({"cache": CACHE, "faelle": FAELLE})],
                       capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, r.stderr
    return {z["name"]: z for z in json.loads(r.stdout)}


def test_der_rechtefehler_greift_auf_den_cache_zurueck(tmp_path):
    quelle = INDEX.read_text(encoding="utf-8")
    assert quelle.count(ANFANG) == 1, (
        "Die Wochen-Ladefunktion ist nicht mehr eindeutig zu finden - "
        "dieser Riegel misst dann nichts. Treffer: %d" % quelle.count(ANFANG))

    aus = _lauf(KOPF + _schnitt(quelle) + FUSS, tmp_path, "jetzt.js")

    assert aus["Rechtefehler (401)"]["anzahl"] == 3, (
        "Bei einem Rechtefehler muessen die drei Eintraege dieser Woche aus dem "
        "Geraetespeicher kommen - der Monteur sieht sonst seine eigenen Stunden "
        "nicht und traegt sie ein zweites Mal ein. Gebaut: %d"
        % aus["Rechtefehler (401)"]["anzahl"])

    # DER WICHTIGERE FALL: ein Auffangzweig, der IMMER greift, wuerde eine
    # wirklich leere Woche mit alten Daten fuellen. Das waere schlimmer als
    # der Fehler, den er behebt.
    assert aus["wirklich leere Woche"]["anzahl"] == 0, (
        "Eine wirklich leere Woche darf NICHT aus dem Cache gefuellt werden - "
        "sonst behauptet die Ansicht Stunden, die es nicht gibt. Gebaut: %d"
        % aus["wirklich leere Woche"]["anzahl"])

    assert aus["Server hat Daten"]["anzahl"] == 2, (
        "Der Normalfall muss die Serverdaten nehmen, nicht den Cache.")

    for name, z in aus.items():
        assert z["ladend"] is False, (
            "Fall '%s' laesst den Ladezustand stehen - die Ansicht dreht dann "
            "ewig." % name)


def test_gegenprobe_der_alte_zweig_liess_die_woche_leer(tmp_path):
    """Ohne diese Umkehr waere nicht belegt, dass der Aufbau den Fehler SIEHT."""
    quelle = INDEX.read_text(encoding="utf-8")
    schnitt = _schnitt(quelle)

    alt = schnitt.replace(
        "if(_rlsLeer(data)){buildDayMap(_wocheAusCache());setLoading(false);return;}",
        "", 1)
    assert alt != schnitt, "Die Umkehr hat nichts entfernt - der Riegel misst nichts"

    aus = _lauf(KOPF + alt + FUSS, tmp_path, "alt.js")
    assert aus["Rechtefehler (401)"]["anzahl"] == 0, (
        "Die alte Fassung MUSS bei einem Rechtefehler eine leere Woche bauen - "
        "sonst misst dieser Riegel nichts.")
    assert aus["Server hat Daten"]["anzahl"] == 2, (
        "Der Normalfall war auch vorher richtig - die Umkehr darf ihn nicht "
        "verfaelschen.")
