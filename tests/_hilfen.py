# -*- coding: utf-8 -*-
"""Gemeinsame Helfer fuer Riegel der Form "Begriff kommt NICHT mehr vor".

WARUM ES DAS GIBT (v3.9.896): Ein `assert "x" not in index_html` hat zwei
Tuecken, die beide in dieser Sitzung zugeschnappt sind.

1. ER MISST DEN KOMMENTAR MIT. Wer etwas ausbaut, schreibt daneben, WAS er
   ausgebaut hat - und nennt den Begriff damit erneut. Der Riegel schlaegt an,
   obwohl der Code sauber ist. Das ist im Repo inzwischen zum zehnten Mal
   passiert, zuletzt beim Ausbau von `wocheKm`: der Erklaerkommentar zur
   Entfernung enthielt das Wort.

2. ER LAESST DEN LAUF HAENGEN STATT FEHLZUSCHLAGEN. Schlaegt er an, bereitet
   pytest den 3,5-MB-String als Fehlermeldung auf. Der Test faellt dann nicht
   um, er steht - und blockiert die ganze Suite.

Deshalb EINE Definition an EINER Stelle, statt sie je Testdatei nachzubauen -
zwei Kopien waeren die naechste Groesse mit zwei Rechnungen.
"""
import re


# `accept: "image/*"` ist KEIN Kommentarbeginn - aber der naive Regex hat den
# Stern-Schraegstrich als Oeffner genommen und bis zum naechsten ECHTEN `*/`
# alles verschluckt. Gemessen am Bestand (v3.9.913): 33 solcher Stellen, und
# der geloeschte Bereich war 49.857 Zeichen ECHTER CODE gross - darunter der
# Tabellenzeilen-Reader `layers.find(x=>x.id===(t.gewerk||t.layer))` (:18180).
#
# Das ist dieselbe Krankheit wie oben, nur in der gefaehrlicheren Richtung:
# `assert "x" not in nur_code(...)` war fuer alles in diesen 49.857 Zeichen
# STILL GRUEN. Ein Riegel, der Code gar nicht erst sieht, misst nichts.
#
# Eng gefasst: nur ein `/*`, das direkt hinter einem Buchstaben steht UND
# direkt von Anfuehrungszeichen/Komma gefolgt wird - am Bestand exakt die 33
# `image/*`-Stellen und keine einzige echte Kommentarklammer.
_MIME_STERN = re.compile(r"(?<=[A-Za-z])/\*(?=[\"',])")
_MASKE = chr(1)  # index.html nutzt chr(1) zwar als Map-Schluessel-Trenner (1x),
#                  aber NIE hinter einem "/" - und nur diese Folge wird
#                  zurueckgetauscht (gemessen: "/"+chr(1) kommt 0x vor).


def nur_code(index_html):
    """index.html ohne Blockkommentare und ohne die APP_VERSION-Changelogzeile."""
    maskiert = _MIME_STERN.sub("/" + _MASKE, index_html)
    ohne = re.sub(r"/\*[\s\S]*?\*/", "", maskiert).replace("/" + _MASKE, "/*")
    return chr(10).join(l for l in ohne.splitlines()
                        if not l.startswith("const APP_VERSION="))


def fundstellen(text, begriff, umfeld=60, max_treffer=3):
    """Kurze Ausschnitte statt der ganzen Datei - damit die Meldung lesbar ist."""
    aus, i = [], text.find(begriff)
    while i != -1 and len(aus) < max_treffer:
        aus.append(text[max(0, i - umfeld):i + len(begriff) + umfeld].replace(chr(10), " "))
        i = text.find(begriff, i + 1)
    return (chr(10) + "  ...").join(aus) if aus else "(keine)"

# ---------------------------------------------------------------------------
# Der Zellen-Block aus _dispoBuildInput - geschnitten und AUSFUEHRBAR.
#
# Warum nicht einfach ein Textvergleich: genau das haben `test_dispo_asfrische_
# abw_v767` und sechs weitere Riegel getan, und der v767 hat damit die ZEILE
# festgeschrieben, die am Feiertag abstuerzte (v3.9.915). Ein Riegel, der die
# Schreibweise abschreibt, misst die Schreibweise - und haelt im schlimmsten
# Fall einen Fehler fest, statt ihn zu finden.
#
# Dazu kam beim v767 ein festes Zeichenfenster (7500), das schon einmal
# geweitet werden musste. Ein Fenster, dessen Breite man frei waehlt, misst die
# Fensterbreite mit: mein 24-zeiliger Erklaerkommentar aus v915 haette es
# erneut gesprengt, ohne dass am Verhalten irgendetwas anders waere.
#
# Deshalb: die Anker EINMAL hier, der Block wird woertlich geschnitten und mit
# Node ausgefuehrt. Wer die Anker aendert, aendert sie fuer beide Riegel.
# ---------------------------------------------------------------------------
_ZELLE_START = "var gruende=[];"
# Der Schnitt reicht bis EINSCHLIESSLICH der Kapazitaetszuweisung. Ohne sie
# fehlt genau die Groesse, gegen die der v767 die Anzeige vergleicht.
_ZELLE_ENDE = "abwAbzug[m.id][t.key]=abz;"

_ZELLE_KOPF = """
"use strict";
function _zelle(t, absMap){
  var kapAbzug={M1:{}}, blockGrund={M1:{}}, tagArt={M1:{}}, abwAbzug={M1:{}};
  var m={id:"M1", n:"Huber"};
  var rows=[];
  var blocksMap={};
  var _heute="2026-01-01";
  var DISPO_RESERVE_MIN=60, DISPO_VORAB_MIN=120;
  var _dispoBvhNorm=function(s){return String(s||"").toLowerCase();};
  var _g=[];
  (function(){
"""

_ZELLE_FUSS = """
  _g=gruende;
  })();
  return {labels:_g.map(function(x){return x.label;}), kap:kapAbzug.M1[t.key],
          abw:abwAbzug.M1[t.key], art:(tagArt.M1[t.key]||{}).art,
          block:blockGrund.M1[t.key]};
}
var _faelle = JSON.parse(process.argv[2]);
console.log(JSON.stringify(_faelle.map(function(f){
  try { return Object.assign({ok:true}, _zelle(f.t, f.absMap)); }
  catch(e){ return {ok:false, fehler:String((e && e.message) || e)}; }
})));
"""


def schnitt(quelle, start, ende):
    """Woertlicher Ausschnitt von `start` bis EINSCHLIESSLICH `ende`."""
    i = quelle.find(start)
    assert i > 0, "Ankerbeginn nicht gefunden: " + start
    j = quelle.find(ende, i)
    assert j > i, "Ankerende nicht gefunden: " + ende
    return quelle[i:j + len(ende)]


def funktion(quelle, name):
    """Eine ganze `function name(...)` woertlich, ueber die Klammerbilanz."""
    i = quelle.find("function " + name + "(")
    assert i > 0, "Funktion nicht gefunden: " + name
    tiefe = 0
    for p in range(quelle.find("{", i), len(quelle)):
        if quelle[p] == "{":
            tiefe += 1
        elif quelle[p] == "}":
            tiefe -= 1
            if tiefe == 0:
                return quelle[i:p + 1]
    raise AssertionError("Funktionsende nicht gefunden: " + name)


def dispo_zelle_programm(index_html):
    """Node-Programm, das `_zelle(tag, absMap)` aus dem ECHTEN Code bereitstellt."""
    return (_ZELLE_KOPF + schnitt(index_html, _ZELLE_START, _ZELLE_ENDE) + _ZELLE_FUSS
            + funktion(index_html, "_dispoAbwAbzug")
            + funktion(index_html, "_dispoAbwLabel"))


def dispo_zelle_lauf(programm, tmp_path, faelle, name="zelle.js"):
    """Fuehrt das Programm aus und gibt je Fall ein Ergebnis zurueck."""
    import json
    import subprocess
    p = tmp_path / name
    p.write_text(programm, encoding="utf-8")
    r = subprocess.run(["node", str(p), json.dumps(faelle)],
                       capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)

