# -*- coding: utf-8 -*-
"""v3.9.931 - Ausgetretene standen im Team und hatten einen Urlaubsanspruch.

Das Praedikat `_maIstEhemalig` (v3.9.866) und die Auswahlliste `_maWaehlbar`
(v3.9.874) gibt es seit langem und sie sind an vielen Stellen angewandt. Zwei
Stellen zogen NICHT mit, obwohl sie unter keine der beiden dokumentierten
Ausnahmen fallen:

  1. HomeView, Block "Team". `monteure.map(...)` voellig ungefiltert - der
     Ausgetretene stand als aktuelles Teammitglied auf dem Schirm, samt
     Fahrzeug-Chip, und die Kachel daneben zaehlte ihn in "... gesamt" mit.
     Die Ueberschrift heisst "Team aktiv / heute aktiv": das ist eine
     LIVE-BELEGSCHAFTSANZEIGE, keine Filter- und keine Reportliste.

  2. AbsView, Urlaubskontingent. `const names=monteure.map(m=>m.n)` speiste
     Kompaktliste, Detailtabelle UND das Excel-Blatt. Fuer jemanden, der nicht
     mehr da ist, stand dort ein Jahresanspruch 2026 mit Resturlaub - und die
     Gesamt-Zeile des Blattes summierte ihn mit.
     Ein Anspruch fuer jemanden, der nicht mehr da ist, ist keine Historie.

WAS DIESER RIEGEL MISST
-----------------------
Nicht die Schreibweise. Die echten Ausdruecke werden woertlich aus index.html
geschnitten und mit Node AUSGEFUEHRT - die Bausteine `_ezHeuteISO`,
`_maIstEhemalig` und `_maWaehlbar` ebenso, damit kein nachgebautes Datum
mitmisst. Gemessen wird, WELCHE NAMEN die Bausteine zurueckgeben.

Vier Riegel:
  1. Der Team-Block enthaelt keinen Ausgetretenen, und der Zaehler
     "... gesamt" passt zur gezeigten Liste.
  2. Das Urlaubskontingent listet keinen Ausgetretenen, und die Gesamt-Zeile
     des Blattes passt zur gefilterten Liste.
  3. HISTORIEN-PIN: ein Arbeitsschein und ein Zeiteintrag eines Ausgetretenen
     loesen den Namen WEITERHIN auf, und die Kalender-/Reportliste in AbsView
     fuehrt ihn weiter.
  4. Eine BESTEHENDE Zuweisung an einen Ausgetretenen verschwindet NICHT aus
     ihrem eigenen Auswahlfeld.

Riegel 3 und 4 sind die wichtigeren. Ein Filter, der zu viel wegnimmt, ist
schlimmer als der Fehler: an Ausgetretenen haengen Zeiteintraege, Scheine und
Abwesenheiten, und die Worker-Zeile ist die einzige Namensaufloesung.

KOEDER
------
Ein Riegel, der ZAEHLT, wird beim eigenen Ausfall gruen: nichts gefunden heisst
"keine Fehler". Darum belegt `test_00_der_aufbau_sieht_den_ausgetretenen`
ZUERST, dass der Messaufbau ueberhaupt etwas sehen KANN - das echte Praedikat
muss den Testmann als ehemalig erkennen, und eine absichtlich UNGEFILTERTE
Liste muss ihn zurueckgeben. Faellt der Aufbau aus, ist dieser Test rot, bevor
irgendeine leere Fundmenge als Erfolg durchgeht.

GEGENPROBE
----------
Die Tests `test_5*` bauen den alten Zustand IM SPEICHER zurueck und verlangen,
dass die Riegel dann ROT werden.
"""
import json
import subprocess

from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]
INDEX = WURZEL / "index.html"

EHEMALIG = "Ehemalig Erna"
AKTIV = "Aktiv Anton"
KUENDIGT = "Kuendigt Karl"
LETZTER_TAG = "Letzter Tag Hanna"

# ------------------------------------------------------------------ Schnitte
# name -> (anfang, ende); Ende inklusive. Jeder Anfang muss GENAU EINMAL
# vorkommen, sonst misst der Riegel etwas anderes als gemeint.
GRUND = {
    "ezHeute": ("function _ezHeuteISO(){", "\n}"),
    "istEhemalig": ("function _maIstEhemalig(m,heute){", "\n}"),
    "waehlbar": ("function _maWaehlbar(liste,aktuell){", "\n}"),
}

S_TEAM = {
    "hvDef": ("  const _hkHV=_ezHeuteISO();",
              "  const _teamAktiv=(monteure||[]).filter(m=>!_maIstEhemalig(m,_hkHV));"),
    "hvTeam": ("            , _teamAktiv.map(m=>{",
               "              ));\n            })"),
    "hvZaehler": ("          , React.createElement('div', { style: {fontSize:11,color:V.dm}}, "
                  "\"heute aktiv · \" , _teamAktiv.length, \" gesamt\" )",
                  "\" gesamt\" )"),
}

S_KONT = {
    "absDef": ("  const _hkAK=_ezHeuteISO();",
               "  const _kontNames=monteure.filter(m=>!_maIstEhemalig(m,_hkAK)).map(m=>m.n);"),
    "kontKompakt": ("        , !kontExpanded&&(React.createElement('div', { style: "
                    "{display:\"flex\",flexDirection:\"column\",gap:6}}, (isAdmin?_kontNames",
                    "        })))"),
    "kontBlatt": ("const hdrs=[\"Nr\",\"Mitarbeiter\",\"Std/Wo\"", "sumCol:9});"),
}

S_HIST = {
    "histSchein": ("(((monteure||[]).find(_m=>_m.id===a.monteur)||{}).n)||\"kein Monteur\"",
                   "||\"kein Monteur\""),
    "histZeit": ("const workers=[...workerIds].map(wid=>{const m=(monteure||MONT)"
                 ".find(x=>x.id===wid);",
                 "a.name.localeCompare(b.name));"),
    "kalenderListe": ("(isAdmin?names:names.filter(m=>m===myMonteurName))",
                      "m===myMonteurName))"),
}

S_ZUW = {
    "zuwSchein": ("_maWaehlbar(monteure,a.monteur||\"\")", "a.monteur||\"\")"),
    "zuwWerkzeug": ("_maWaehlbar(monteure,scannedWz.zugewiesen)"
                    ".filter(m=>m.id!==scannedWz.zugewiesen)",
                    ".filter(m=>m.id!==scannedWz.zugewiesen)"),
    "zuwFahrer": ("_maWaehlbar(monteure.filter(m=>(m.fs||\"\").includes(\"C\")),"
                  "((monteure||[]).find(x=>x.n===beschForm.fahrer)||{}).id||\"\")",
                  ").id||\"\")"),
    "zuwMention": ("_maWaehlbar(monteure,null).filter(", "includes(mentionFilter))"),
}

# --------------------------------------------------- Umkehr fuer die Gegenprobe
UMKEHR_TEAM = [("_teamAktiv.map(m=>{", "monteure.map(m=>{"),
               ("_teamAktiv.length", "monteure.length")]
S_TEAM_ALT = {
    "hvTeam": ("            , monteure.map(m=>{",
               "              ));\n            })"),
    "hvZaehler": ("          , React.createElement('div', { style: {fontSize:11,color:V.dm}}, "
                  "\"heute aktiv · \" , monteure.length, \" gesamt\" )",
                  "\" gesamt\" )"),
}

UMKEHR_KONT = [("(isAdmin?_kontNames:_kontNames.filter(n=>n===myMonteurName))",
                "(isAdmin?names:names.filter(n=>n===myMonteurName))"),
               ("const data=[];_kontNames.forEach(", "const data=[];names.forEach("),
               ('"+_kontNames.length+" Mitarbeiter', '"+names.length+" Mitarbeiter')]
S_KONT_ALT = {
    "kontKompakt": ("        , !kontExpanded&&(React.createElement('div', { style: "
                    "{display:\"flex\",flexDirection:\"column\",gap:6}}, (isAdmin?names",
                    "        })))"),
    "kontBlatt": ("const hdrs=[\"Nr\",\"Mitarbeiter\",\"Std/Wo\"", "sumCol:9});"),
}

UMKEHR_ZUW = [
    ("_maWaehlbar(monteure,scannedWz.zugewiesen).filter(m=>m.id!==scannedWz.zugewiesen)",
     "monteure.filter(m=>m.id!==scannedWz.zugewiesen)"),
    ("_maWaehlbar(monteure.filter(m=>(m.fs||\"\").includes(\"C\")),"
     "((monteure||[]).find(x=>x.n===beschForm.fahrer)||{}).id||\"\")",
     "monteure.filter(m=>(m.fs||\"\").includes(\"C\"))"),
    ("_maWaehlbar(monteure,null).filter(m=>(m.n||'').toLowerCase().includes(mentionFilter))",
     "(monteure||[]).filter(m=>(m.n||'').toLowerCase().includes(mentionFilter))"),
]
S_ZUW_ALT = dict(S_ZUW)
S_ZUW_ALT["zuwWerkzeug"] = ("monteure.filter(m=>m.id!==scannedWz.zugewiesen)",
                            ".filter(m=>m.id!==scannedWz.zugewiesen)")
S_ZUW_ALT["zuwFahrer"] = ("monteure.filter(m=>(m.fs||\"\").includes(\"C\"))",
                          ".includes(\"C\"))")
S_ZUW_ALT["zuwMention"] = ("(monteure||[]).filter(m=>(m.n||'').toLowerCase()",
                           "includes(mentionFilter))")

# ------------------------------------------------------------------ Node-Kopf
KOPF = """
"use strict";
%(ezHeute)s
%(istEhemalig)s
%(waehlbar)s

function _tag(off){
  var d = new Date(_ezHeuteISO() + "T12:00:00Z");
  d.setUTCDate(d.getUTCDate() + off);
  return d.toISOString().slice(0,10);
}
var monteure = [
  {id:"w1", n:"%(AKTIV)s",       r:"Monteur",   fs:"B C"},
  {id:"w2", n:"%(EHEMALIG)s",    r:"Monteur",   fs:"B C", austritt:_tag(-1)},
  {id:"w3", n:"%(KUENDIGT)s",    r:"Techniker", fs:"C",   austritt:_tag(1)},
  {id:"w4", n:"%(LETZTER_TAG)s", r:"Helfer",    fs:"B",   austritt:_ezHeuteISO()}
];
var MONT = [];
var names = monteure.map(function(m){ return m.n; });

/* Attrappen so schmal wie moeglich - sie entscheiden, was der Riegel NICHT
   mehr sehen kann. createElement gibt nur zurueck, womit es gerufen wurde. */
var React = { createElement: function(t,p){
  return { t:t, p:p||{}, k:Array.prototype.slice.call(arguments,2) };
} };
function _optionalChain(){ return undefined; }
function _okG(c){ return c; }
function _n(v,d){ return Number(v).toFixed(d).replace(".",","); }
var COLORS = { ERROR:"#ef4444" };
var V = { tx:"#000", dm:"#666", bd:"#ccc", cd:"#fff" };
var isMob = false;
var isAdmin = true;
var myMonteurName = "%(AKTIV)s";

/* HomeView-Umgebung */
var abs = {};
var AT_T = {};
var fahrzeuge = [{fahrer:"w2", kennzeichen:"EP-EHEM1"}];
function td2(){ return _ezHeuteISO(); }

/* AbsView-Umgebung */
var yr = 2026;
var kontExpanded = false;
var sel = "";
function setSel(){}
function setSubView(){}
var COMPANY_FOOTER = { name:"EP Kolar" };
var kontingent = {};
monteure.forEach(function(m){
  kontingent[m.n] = {urlaub:25, stunden:192.5, vorjahr:0, woche:38.5, ueberstunden:0};
});
function yearSt(){
  return {urlaubStd:8, urlaubStdGen:8, urlaubStdAusstehend:0, krankenstandStd:0,
          zeitausgleichStd:0, sonderStdGes:0, pflegeStdGes:0,
          urlaub:1, krankenstand:0, zeitausgleich:0};
}
/* Jeder bekommt einen EIGENEN Resturlaub: die Gesamt-Zeile ist damit ein
   Fingerabdruck der Zeilen und nicht nur eine Zeilenzahl mal Konstante.
   Ganze Zahlen, weil genXls die deutsche Kommaschreibweise mit parseFloat
   liest und ab dem Komma abschneidet. */
var _REST = {"%(AKTIV)s":100, "%(EHEMALIG)s":200, "%(KUENDIGT)s":300,
             "%(LETZTER_TAG)s":400};
function resturlaub(nm){ return _REST[nm] || 0; }
var _blatt = null;
function genXls(titel, untertitel, hdrs, rows, datei, opts){
  /* Die Gesamt-Zeile WOERTLICH so gerechnet wie genXls sie baut (~index.html:4877). */
  var sc = opts.sumCol;
  var summe = rows.reduce(function(s,r){ return s + (parseFloat(r[sc])||0); }, 0);
  _blatt = { untertitel:untertitel, zeilen:rows.map(function(r){ return r[1]; }),
             gesamt:summe };
}

var AUS = {};
"""

# Der KOEDER steht VOR allem anderen: er belegt, dass der Aufbau sehen kann.
R_KOEDER = """
AUS.praedikat = monteure.map(function(m){ return [m.n, !!_maIstEhemalig(m)]; });
AUS.koeder_ungefiltert = monteure.map(function(m){ return m.n; });
"""

R_TEAM = """
%(hvDef)s
var _teamEl = [null
%(hvTeam)s
];
AUS.team = _teamEl[1].map(function(e){ return e.p.key; });
var _zEl = [null
%(hvZaehler)s
];
AUS.team_gesamt = _zEl[1].k[1];
"""

R_TEAM_ALT = R_TEAM.replace("%(hvDef)s\n", "")

R_KONT = """
%(absDef)s
var _kontEl = [null
%(kontKompakt)s
];
AUS.kont_liste = _kontEl[1].k[0].map(function(e){ return e.p.key; });
(function(){
%(kontBlatt)s
})();
AUS.blatt_zeilen = _blatt.zeilen;
AUS.blatt_untertitel = _blatt.untertitel;
AUS.blatt_gesamt = _blatt.gesamt;
"""

R_KONT_ALT = R_KONT.replace("%(absDef)s\n", "")

R_HIST = """
AUS.hist_schein = (function(a){ return %(histSchein)s; })({monteur:"w2"});
AUS.hist_zeit = (function(workerIds){
%(histZeit)s
  return workers.map(function(w){ return w.name; });
})(["w2","w1"]);
AUS.kalender_liste = %(kalenderListe)s;
"""

R_ZUW = """
function _namen(l){ return l.map(function(m){ return m.n; }); }
AUS.zuw_eigene = _namen((function(a){ return %(zuwSchein)s; })({monteur:"w2"}));
AUS.zuw_fremde = _namen((function(a){ return %(zuwSchein)s; })({monteur:"w1"}));
AUS.wz_traeger = _namen((function(scannedWz){ return %(zuwWerkzeug)s; })({zugewiesen:"w2"}));
AUS.wz_fremd   = _namen((function(scannedWz){ return %(zuwWerkzeug)s; })({zugewiesen:"w1"}));
AUS.fahrer_alt = _namen((function(beschForm){ return %(zuwFahrer)s; })({fahrer:"%(EHEMALIG)s"}));
AUS.fahrer_neu = _namen((function(beschForm){ return %(zuwFahrer)s; })({fahrer:""}));
AUS.mention    = _namen((function(mentionFilter){ return %(zuwMention)s; })(""));
"""

FUSS = """
console.log(JSON.stringify(AUS));
"""


def _schnitt(quelle, name, anfang, ende):
    treffer = quelle.count(anfang)
    assert treffer == 1, (
        "Der Anker fuer '%s' kommt %d-mal vor (erwartet: genau 1). Dieser Riegel "
        "misst dann nicht die gemeinte Stelle.\n  %r" % (name, treffer, anfang[:140]))
    i = quelle.index(anfang)
    j = quelle.index(ende, i) + len(ende)
    return quelle[i:j]


def _teile(quelle, *schnittsaetze):
    t = {"AKTIV": AKTIV, "EHEMALIG": EHEMALIG, "KUENDIGT": KUENDIGT,
         "LETZTER_TAG": LETZTER_TAG}
    for satz in (GRUND,) + schnittsaetze:
        for name, (a, e) in satz.items():
            t[name] = _schnitt(quelle, name, a, e)
    return t


def _node(programm, tmp_path, name):
    p = tmp_path / name
    p.write_text(programm, encoding="utf-8")
    r = subprocess.run(["node", str(p)], capture_output=True, text=True,
                       encoding="utf-8")
    assert r.returncode == 0, (
        "Der aus index.html geschnittene Code ist mit Node nicht gelaufen:\n"
        + (r.stderr or ""))
    return json.loads(r.stdout)


def _lauf(quelle, tmp_path, dateiname, rumpfe, schnittsaetze):
    t = _teile(quelle, *schnittsaetze)
    programm = (KOPF % t) + R_KOEDER + "".join(r % t for r in rumpfe) + FUSS
    return _node(programm, tmp_path, dateiname)


def _umgekehrt(quelle, ersetzungen):
    neu = quelle
    for a, b in ersetzungen:
        assert a in neu, (
            "Die Umkehr findet %r nicht - die Gegenprobe misst dann nichts."
            % (a[:100],))
        neu = neu.replace(a, b)
    return neu


def _jetzt(tmp_path):
    quelle = INDEX.read_text(encoding="utf-8")
    return _lauf(quelle, tmp_path, "jetzt.js",
                 [R_TEAM, R_KONT, R_HIST, R_ZUW],
                 [S_TEAM, S_KONT, S_HIST, S_ZUW])


# ================================================================ KOEDER
def test_00_der_aufbau_sieht_den_ausgetretenen(tmp_path):
    """Belegt, dass dieser Riegel ueberhaupt etwas sehen KANN.

    Ohne ihn waere jede leere Fundmenge ein gruener Riegel - auch dann, wenn die
    Testdaten gar keinen Ausgetretenen enthalten oder das Praedikat nicht mehr
    geschnitten wird.
    """
    quelle = INDEX.read_text(encoding="utf-8")
    aus = _lauf(quelle, tmp_path, "koeder.js", [], [])

    urteil = dict((n, e) for n, e in aus["praedikat"])
    assert urteil[EHEMALIG] is True, (
        "Das ECHTE Praedikat _maIstEhemalig haelt den Testmann nicht fuer "
        "ehemalig - dann misst dieser Riegel nichts. Urteil: %r" % (urteil,))
    assert urteil[AKTIV] is False, "Der aktive Mitarbeiter darf nicht ehemalig sein."
    assert urteil[KUENDIGT] is False, (
        "Ein Austritt in der ZUKUNFT ist noch kein Austritt - sonst faellt "
        "jemand aus dem Team, bevor er geht.")
    assert urteil[LETZTER_TAG] is False, (
        "Am Austrittstag SELBST ist der Mitarbeiter noch da (austritt < heute).")

    assert EHEMALIG in aus["koeder_ungefiltert"], (
        "Eine absichtlich UNGEFILTERTE Liste gibt den Ausgetretenen nicht "
        "zurueck - der Messaufbau ist blind, nicht die App sauber.")


# ================================================================ RIEGEL 1
def test_1_homeview_team_zeigt_keinen_ausgetretenen(tmp_path):
    aus = _jetzt(tmp_path)
    ids = aus["team"]

    assert "w2" not in ids, (
        "Der Block 'Team' zeigt den Ausgetretenen als aktuelles Teammitglied - "
        "samt Fahrzeug-Chip. Gerendert: %r" % (ids,))
    assert "w1" in ids and "w3" in ids and "w4" in ids, (
        "Der Filter nimmt zu viel weg: aktive Mitarbeiter, ein kuenftiger "
        "Austritt und der Austrittstag selbst gehoeren ins Team. Gerendert: %r"
        % (ids,))
    assert len(ids) == 3, "Erwartet drei Kacheln, gerendert: %r" % (ids,)

    assert aus["team_gesamt"] == len(ids), (
        "Die Kachel 'Team aktiv' zaehlt %r, gezeigt werden aber %d Kacheln - "
        "zwei Zahlen auf einem Schirm, die sich widersprechen."
        % (aus["team_gesamt"], len(ids)))


# ================================================================ RIEGEL 2
def test_2_urlaubskontingent_ohne_ausgetretene_und_summe_passt(tmp_path):
    aus = _jetzt(tmp_path)

    assert EHEMALIG not in aus["kont_liste"], (
        "Das Urlaubskontingent fuehrt fuer den Ausgetretenen weiter einen "
        "Jahresanspruch. Liste: %r" % (aus["kont_liste"],))
    assert AKTIV in aus["kont_liste"] and KUENDIGT in aus["kont_liste"], (
        "Der Filter nimmt zu viel weg. Liste: %r" % (aus["kont_liste"],))
    assert LETZTER_TAG in aus["kont_liste"], (
        "Am Austrittstag selbst besteht der Anspruch noch.")

    assert EHEMALIG not in aus["blatt_zeilen"], (
        "Das Excel-Blatt des Kontingents listet den Ausgetretenen. Zeilen: %r"
        % (aus["blatt_zeilen"],))
    assert len(aus["blatt_zeilen"]) == len(aus["kont_liste"]), (
        "Blatt und Bildschirmliste weichen voneinander ab: %r / %r"
        % (aus["blatt_zeilen"], aus["kont_liste"]))

    # DIE SUMMENZEILE: genXls summiert Spalte 9 (Rest h) ueber die Zeilen.
    # 100 + 300 + 400 - ohne die 200 des Ausgetretenen.
    assert aus["blatt_gesamt"] == 800, (
        "Die Gesamt-Zeile des Blattes passt nicht zur gezeigten Liste: %r bei "
        "%r." % (aus["blatt_gesamt"], aus["blatt_zeilen"]))
    assert str(len(aus["blatt_zeilen"])) + " Mitarbeiter" in aus["blatt_untertitel"], (
        "Die Kopfzeile des Blattes nennt eine andere Mitarbeiterzahl als die "
        "Zeilen darunter: %r" % (aus["blatt_untertitel"],))


# ================================================================ RIEGEL 3
def test_3_historie_loest_den_namen_weiterhin_auf(tmp_path):
    """Der wichtigere Riegel: der Filter darf die Vergangenheit nicht loeschen."""
    aus = _jetzt(tmp_path)

    assert aus["hist_schein"] == EHEMALIG, (
        "Der Arbeitsschein eines Ausgetretenen zeigt den Namen nicht mehr "
        "('%s') - die Worker-Zeile ist die EINZIGE Namensaufloesung."
        % aus["hist_schein"])
    assert EHEMALIG in aus["hist_zeit"], (
        "Die Zeiteintraege eines Ausgetretenen verlieren den Namen: %r"
        % (aus["hist_zeit"],))
    assert "?" not in aus["hist_zeit"], (
        "Ein Zeiteintrag loest auf '?' auf - der Name ist weg: %r"
        % (aus["hist_zeit"],))
    assert EHEMALIG in aus["kalender_liste"], (
        "Die Kalender-/Reportliste in AbsView fuehrt den Ausgetretenen nicht "
        "mehr - wer seine alten Krankenstaende sucht, kommt nicht mehr hin: %r"
        % (aus["kalender_liste"],))


# ================================================================ RIEGEL 4
def test_4_bestehende_zuweisung_bleibt_im_eigenen_feld(tmp_path):
    """Ausnahme 1 aus v3.9.874 darf nicht aufgeweicht werden."""
    aus = _jetzt(tmp_path)

    assert EHEMALIG in aus["zuw_eigene"], (
        "Ein Arbeitsschein, der auf einen Ausgetretenen zugewiesen IST, verliert "
        "ihn aus seinem eigenen Auswahlfeld - der naechste Speichern-Klick "
        "loescht die Zuweisung stillschweigend. Vorrat: %r" % (aus["zuw_eigene"],))
    assert EHEMALIG not in aus["zuw_fremde"], (
        "In einem FREMDEN Schein darf der Ausgetretene nicht mehr waehlbar "
        "sein: %r" % (aus["zuw_fremde"],))

    assert EHEMALIG not in aus["wz_fremd"], (
        "Werkzeug-Umbuchen bietet den Ausgetretenen weiter an: %r"
        % (aus["wz_fremd"],))
    assert KUENDIGT in aus["wz_fremd"] and LETZTER_TAG in aus["wz_fremd"], (
        "Werkzeug-Umbuchen nimmt zu viel weg: %r" % (aus["wz_fremd"],))
    assert AKTIV not in aus["wz_fremd"], (
        "Wer das Geraet gerade traegt, steht wie bisher nicht in der "
        "Umbuchen-Liste: %r" % (aus["wz_fremd"],))
    assert EHEMALIG not in aus["wz_traeger"], (
        "Der aktuelle Traeger wird wie bisher aus der Umbuchen-Liste genommen - "
        "das war schon vorher so und darf sich nicht drehen: %r"
        % (aus["wz_traeger"],))

    assert EHEMALIG in aus["fahrer_alt"], (
        "Eine aus der Historie geladene Fahrerbescheinigung verliert ihren "
        "Fahrer aus dem eigenen Feld: %r" % (aus["fahrer_alt"],))
    assert EHEMALIG not in aus["fahrer_neu"], (
        "Eine NEUE Fahrerbescheinigung bietet den Ausgetretenen weiter an: %r"
        % (aus["fahrer_neu"],))
    assert AKTIV in aus["fahrer_neu"] and KUENDIGT in aus["fahrer_neu"], (
        "Die Fahrerliste nimmt zu viel weg - beide haben Klasse C: %r"
        % (aus["fahrer_neu"],))
    assert LETZTER_TAG not in aus["fahrer_neu"], (
        "Ohne Klasse C darf niemand in der Fahrerliste stehen (unveraendert).")

    assert EHEMALIG not in aus["mention"], (
        "Der Erwaehnungs-Vorschlag bietet den Ausgetretenen weiter an: %r"
        % (aus["mention"],))
    assert AKTIV in aus["mention"], "Der Erwaehnungs-Vorschlag nimmt zu viel weg."


# ================================================================ GEGENPROBEN
def test_5a_gegenprobe_das_team_zeigte_den_ausgetretenen(tmp_path):
    alt = _umgekehrt(INDEX.read_text(encoding="utf-8"), UMKEHR_TEAM)
    aus = _lauf(alt, tmp_path, "alt_team.js", [R_TEAM_ALT], [S_TEAM_ALT])
    assert "w2" in aus["team"], (
        "Die alte Fassung MUSS den Ausgetretenen im Team zeigen - sonst misst "
        "Riegel 1 nichts. Gerendert: %r" % (aus["team"],))
    assert aus["team_gesamt"] == 4, (
        "Der alte Zaehler MUSS alle vier zaehlen: %r" % (aus["team_gesamt"],))


def test_5b_gegenprobe_das_kontingent_fuehrte_einen_anspruch(tmp_path):
    alt = _umgekehrt(INDEX.read_text(encoding="utf-8"), UMKEHR_KONT)
    aus = _lauf(alt, tmp_path, "alt_kont.js", [R_KONT_ALT], [S_KONT_ALT])
    assert EHEMALIG in aus["kont_liste"], (
        "Die alte Fassung MUSS den Ausgetretenen im Kontingent listen - sonst "
        "misst Riegel 2 nichts. Liste: %r" % (aus["kont_liste"],))
    assert EHEMALIG in aus["blatt_zeilen"]
    assert aus["blatt_gesamt"] == 1000, (
        "Die alte Gesamt-Zeile MUSS den Anspruch des Ausgetretenen mitsummiert "
        "haben (800 + 200): %r" % (aus["blatt_gesamt"],))


def test_5c_gegenprobe_werkzeug_fahrer_und_erwaehnung_boten_ihn_an(tmp_path):
    alt = _umgekehrt(INDEX.read_text(encoding="utf-8"), UMKEHR_ZUW)
    aus = _lauf(alt, tmp_path, "alt_zuw.js", [R_ZUW], [S_ZUW_ALT])
    assert EHEMALIG in aus["wz_fremd"], (
        "Die alte Umbuchen-Liste MUSS den Ausgetretenen angeboten haben.")
    assert EHEMALIG in aus["fahrer_neu"], (
        "Die alte Fahrerliste MUSS den Ausgetretenen angeboten haben.")
    assert EHEMALIG in aus["mention"], (
        "Der alte Erwaehnungs-Vorschlag MUSS den Ausgetretenen angeboten haben.")
    # Was schon vorher richtig war, darf die Umkehr nicht verfaelschen.
    assert EHEMALIG in aus["zuw_eigene"], (
        "Ausnahme 1 galt auch vorher schon - die Umkehr darf sie nicht drehen.")


def test_6_die_beiden_praedikate_stehen_unveraendert_im_code():
    """_maIstEhemalig und _maWaehlbar bleiben BYTE-IDENTISCH.

    Kein Ersatz fuer eine Messung, sondern eine Zusicherung: diese Reparatur
    baut keine zweite Datumslogik und kein zweites Praedikat.
    """
    quelle = INDEX.read_text(encoding="utf-8")
    assert quelle.count("function _maIstEhemalig(m,heute){") == 1
    assert quelle.count("function _maWaehlbar(liste,aktuell){") == 1
    assert quelle.count(
        "return !!(m&&m.austritt&&String(m.austritt).slice(0,10)<h);") == 1, (
        "Der Rumpf von _maIstEhemalig wurde veraendert oder dupliziert.")
    assert quelle.count(
        "return !_maIstEhemalig(m,h) || (aktuell && m && "
        "String(m.id)===String(aktuell));") == 1, (
        "Der Rumpf von _maWaehlbar wurde veraendert oder dupliziert.")
