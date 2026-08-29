# -*- coding: utf-8 -*-
"""v3.9.899 - Ein Rueckruf-Parameter hatte zwei Namen. Live-Absturz der Dispo.

    _fx.map(function(tf){ ... kunde:(f.bvh||"") ... })
                     ^^^                ^

Deklariert als `tf`, gelesen als `f`. Die Datei laeuft unter "use strict", `f`
gibt es im ganzen Sichtbereich von DispoPanel nicht -> ReferenceError, geworfen
im Render und ausserhalb jedes try. Die App reisst auf die Fehlerseite.

WARUM ER SICH ALS "NAECHSTE WOCHE" GEZEIGT HAT
──────────────────────────────────────────────
`_fx` ist `fixMap[monteur][tag]`, und `fixMap` nimmt nur Termine ab HEUTE auf:

    if(!iso||iso<_heute)return;   /* ueberfaellig -> kein fixer Kapazitaets-Block */

Gemeldet wurde der Absturz an einem Samstag. Die angezeigte Startwoche
(Mo 24.08. - Fr 28.08.) lag damit vollstaendig in der Vergangenheit, `_fx` war in
jeder Zelle leer, und `.map` ruft seinen Rueckruf dann nie auf - `f` wurde nie
ausgewertet. Erst ein Klick auf die Folgewoche, in der die bestaetigten
Kundentermine liegen, fuehrt den Rueckruf aus.

**Das war ein Kalender-Zufall, keine Wochen-Eigenschaft.** Ab dem folgenden
Montag haette dieselbe Zelle auch in der LAUFENDEN Woche geworfen.

WIE ER DURCH ALLE TORE KAM
──────────────────────────
1. `node_check` parst nur - ein freier Name ist syntaktisch fehlerfrei.
2. Der Tab-Durchlauf gegen die Live-App war GRUEN: er meldet sich ohne echte
   Zugangsdaten an, alle Datenabrufe laufen in 401, `fixMap` bleibt ueberall
   leer. Ein Renderpfad, der Daten braucht, ist damit unerreichbar.
3. Und der bitterste Teil: `test_dispo_tagesplan_v894` prueft, dass das
   Erkennungsmuster `_fx.map(function(f` genau EINMAL vorkommt - es hat also
   die SCHREIBWEISE gezaehlt und den Block nie AUSGEFUEHRT. Der Kommentar
   daneben erklaert sogar, warum der Parameter `tf` heissen muss. Die
   Umbenennung wurde an einer von vier Verwendungen vergessen, und der Riegel
   daneben konnte das prinzipiell nicht sehen.

Deshalb misst dieser Riegel nicht die Schreibweise, sondern die Eigenschaft: der
echte Block wird woertlich aus index.html geschnitten und mit Daten AUSGEFUEHRT.
"""
import subprocess

START = '_tagesplan[m.id+"_"+t.key]=[].concat('
ENDE = 'geschaetzt:(!!tc.dauerGeschaetzt&&_dauerOv[tc.scheinId]==null)};}));'

KOPF = """
function _zelleAusschnitt(_fx, chips){
  var _tagesplan={};
  var m={id:"M1"}, t={key:"2026-09-02"};
  var _scheinById=function(id){return {nummer:"AS-"+id,arbeitsort:"Krems",kundOrt:"Krems",arbeitsanweisungen:"Schalter tauschen",telefon:"06641234567"};};
  var _fxSlot={}; var _ab=[]; var _dauerOv={};
  var DISPO_TAG_START_MIN=420;
  var _dispoMinToHHMM=function(mn){return String(Math.floor(mn/60)).padStart(2,"0")+":"+String(mn%60).padStart(2,"0");};
  var _telOf=function(x){return String((x&&x.telefon)||"").trim();};
  var _effDauer=function(c){return c.dauerMin||0;};
"""

FUSS = """
  return _tagesplan[m.id+"_"+t.key];
}
try{
  var r=_zelleAusschnitt([{scheinId:7,bvh:"Kunde Huber",terminZeit:"08:30",dauerMin:90}],
                         [{scheinId:9,bvh:"Muster",dauerMin:120}]);
  console.log("OK "+JSON.stringify(r));
}catch(e){ console.log("WIRFT "+e.name+": "+e.message); }
"""


def _block(index_html):
    a = index_html.index(START)
    b = index_html.index(ENDE, a) + len(ENDE)
    return index_html[a:b]


def _lauf(node_exe, tmp_path, block):
    p = tmp_path / "tagesplan.js"
    p.write_text(KOPF + "  " + block + FUSS, encoding="utf-8")
    r = subprocess.run([node_exe, str(p)], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return (r.stdout or "") + (r.stderr or "")


def test_die_sammelmappe_wirft_nicht_bei_einem_fixen_termin(index_html, node_exe, tmp_path):
    """DIE MARKE: ein Tag mit einem fixen Termin UND einem Vorschlag muss
    durchlaufen. Genau dieser Fall hat live die App zerrissen."""
    ist = _lauf(node_exe, tmp_path, _block(index_html))
    assert ist.startswith("OK"), (
        "Die Sammelmappe wirft, sobald ein fixer Termin im Tag liegt - das ist "
        "der Live-Absturz vom 29.08.:" + chr(10) + ist.strip()[:400]
    )
    assert '"kunde":"Kunde Huber"' in ist, (
        "Der Kundenname kommt nicht aus dem Fixtermin-Eintrag - dann steht auf "
        "dem Tagesplan des Monteurs eine leere Kundenspalte:" + chr(10)
        + ist.strip()[:400]
    )


def test_umkehrprobe_der_riegel_kann_rot_werden(index_html, node_exe, tmp_path):
    """DIE GEGENPROBE, und hier ist sie der eigentliche Punkt: mit dem alten,
    falschen Namen MUSS derselbe Block werfen.

    Ohne sie waere der Riegel oben gruen, ohne je etwas gemessen zu haben -
    genau der Zustand, in dem `test_dispo_tagesplan_v894` seit v894 war."""
    block = _block(index_html)
    kaputt = block.replace("tf.bvh", "f.bvh")
    assert kaputt != block, (
        "Die Umkehrprobe konnte nichts zurueckbauen - dann misst der Riegel "
        "darueber nichts."
    )
    ist = _lauf(node_exe, tmp_path, kaputt)
    assert "ReferenceError" in ist, (
        "Der Riegel kann nicht rot werden und ist damit wertlos:" + chr(10)
        + ist.strip()[:400]
    )


def test_kein_zweiter_freier_name_im_selben_block(index_html):
    """Die Schwesterzeile las von Anfang an richtig (`tc.bvh`). Beide Namen
    muessen genau einmal vorkommen - taucht `f.bvh` wieder auf, ist die
    Umbenennung erneut unvollstaendig."""
    assert index_html.count(',kunde:(tf.bvh||""),ort:') == 1, (
        "Der Fixtermin-Zweig liest den Kundennamen nicht mehr ueber tf."
    )
    assert index_html.count(',kunde:(f.bvh||""),ort:') == 0, (
        "Der freie Name f ist zurueck - das ist wieder ein ReferenceError im "
        "Render, sobald ein fixer Termin in der gezeigten Woche liegt."
    )
