# -*- coding: utf-8 -*-
"""v3.9.1049 - "Aliti und Cracana gibt es nicht mehr, die wurden gekuendigt."

Beide tragen in `workers` ein Austrittsdatum (22.07.2026) und standen trotzdem
noch in Listen der App. `_maIstEhemalig` / `_maWaehlbar` gibt es seit v866/v874;
diese Stellen zogen nicht mit:

  FILTER-Listen (neu: `_maFilterliste` - Ausgetretener nur mit eigenen Daten
  oder als aktueller Filterwert):
    * Arbeitsscheine "Alle Monteure" (Filter) und "Monteur im Kalender"
    * Maengel "Alle Verantwortlichen"
  AUSWAHL:
    * VZeit: Vorbelegung (_defW) nie ein Ausgetretener; Monteur im Modal
      waehlbar, wenn er AM GEBUCHTEN TAG noch da war (_wpMaSichtbarAmTag)
  ZEITRAUM-Listen (Ausgetretener nur, wenn der Zeitraum am/vor dem Austritt
  beginnt):
    * Entfernungszulage Mitarbeiter-Wahl (Monat)
    * Buero-Export Abwesenheits-Jahrestabelle (_absRows, Jahr)
    * Stundenzettel/FinkZeit Mitarbeiter-Wahl (Monat)
    * AbsView: Team-Zeitleiste, Monat "ALLE", Jahresuebersicht, Export
    * Zeiterfassung: Wochenuebersicht, Bauwochenbericht, MA-Wahl
      (fieldMAWo statt fieldMA - fieldMA filterte nach HEUTE und liess die
      Juli-Stunden eines Ausgetretenen aus dem Bauwochenbericht fallen)

Gemessen wird mit Node: die echten Funktionen (`_ezHeuteISO`,
`_maIstEhemalig`, `_maWaehlbar`, `_maFilterliste`, `_wpMaSichtbarAmTag`,
`_mtMitGetragenem`) werden aus index.html GESCHNITTEN, die Ausdruecke
woertlich (mit Zaehl-Assert) aus index.html uebernommen und ausgefuehrt.
Gegenprobe: die alten Ausdruecke zeigen den Ausgetretenen.
"""
import json
import subprocess
from pathlib import Path

import pytest

WURZEL = Path(__file__).resolve().parents[1]
INDEX = WURZEL / "index.html"

FUNKTIONEN = [
    ("function _ezHeuteISO(){", "\n}"),
    ("function _maIstEhemalig(m,heute){", "\n}"),
    ("function _maWaehlbar(liste,aktuell){", "\n}"),
    ("function _maFilterliste(liste,aktuell,hatDaten){", "\n}"),
    ("function _wpMaSichtbarAmTag(worker, isoTag){", "\n}"),
    ("function _mtMitGetragenem(vorrat,alle,wert){", "concat(l);}"),
]

# name -> (Ausdruck woertlich aus index.html, erwartete Anzahl)
X = {
    "as_filter": ("_maFilterliste(monteure,filterMonteur,m=>arbeitsscheine.some(a=>a.monteur===m.id))", 1),
    "as_kal": ("_maFilterliste(monteure,calMonteur,m=>arbeitsscheine.some(a=>a.monteur===m.id))", 1),
    "mg_filter": ("_maFilterliste((monteure||MONT),fWorker,w=>ms.some(m=>m.worker===w.id||m.zugewiesen===w.id||m.assignee===w.id))", 1),
    "ez": ("monteure.filter(function(m){return !_maIstEhemalig(m,ym+'-01')||m.id===ezWid;})", 1),
    "abs_rows": ("(monteure||[]).filter(m=>!_maIstEhemalig(m,_abYr+\"-01-01\"))", 1),
    "vz_def": ("((_maWaehlbar(allWorkers,null)[0]||{}).id)", 1),
    "vz_modal": ("_mtMitGetragenem(allWorkers.filter(w=>_wpMaSichtbarAmTag(w,addDay)),(monteure||MONT),", 1),
    "sz": ("const _szAb=selJahr+\"-\"+(typeof selMonat===\"number\"?String(selMonat+1).padStart(2,\"0\"):\"01\")+\"-01\";"
           "const _szWaehlbar=allMA.filter(m=>{const w=(monteure||[]).find(x=>x.id===m.id||x.id===m.monteurId||x.id===m.monteur_id);"
           "return !_maIstEhemalig(w,_szAb)||m.id===selMA;});", 1),
    "abs_ab": ("const _absAb=(nm,ab)=>{const o=(monteure||[]).find(x=>x.n===nm);return !(o&&_maIstEhemalig(o,ab));};", 1),
    "abs_tl": ("names.filter(m=>_absAb(m,dk(days[0])))", 1),
    "abs_immonat": ("const _absMonAb=yr+\"-\"+String(mo+1).padStart(2,\"0\");const _absImMonat=nm=>_absAb(nm,_absMonAb+\"-01\")||Object.keys(abs||{}).some(k=>k.startsWith(nm+\"_\"+_absMonAb));", 1),
    "abs_mo": ("names.filter(m=>_absImMonat(m))", 1),
    # Kalender-Personenpillen (Sebastian 19.11.: Aliti/Cracana standen dort als "ausgetreten")
    "abs_kal": ("(isAdmin?names.filter(m=>_absImMonat(m)||m===sel):names.filter(m=>m===myMonteurName))", 1),
    "abs_jahr": ("names.filter(m=>_absAb(m,yr+\"-01-01\"))", 2),
    "ze_wo": ("const fieldMAWo=monteure.filter(m=>m.r!==\"Backoffice\"&&m.r!==\"Verkauf/Buchhaltung\"&&!_maIstEhemalig(m,isoDate(0)));", 1),
    "ze_sel": ("fieldMAWo.concat(monteure.filter(m=>m.id===selWorker&&fieldMAWo.indexOf(m)<0))", 1),
    # Historie: bleibt UNGEFILTERT
    "hist_names": ("const names=monteure.map(m=>m.n);", 1),
    "hist_allma": ("const allMA=[...(users||[]).filter(u=>u.active!==false),...(monteure||[]).filter(m=>!(users||[]).find(u=>u.monteurId===m.id||u.monteur_id===m.id))];", 1),
}

# Die alten Ausdruecke (v3.9.1048) - Gegenprobe, und sie duerfen nicht mehr im Code stehen
ALT = {
    "as_filter": ("\"Alle Monteure\" ), monteure.map(m=>", "monteure"),
    "as_kal": ("\"Alle Monteure\"), monteure.map(m=>", "monteure"),
    "mg_filter": ("\"Alle Verantwortlichen\"), (monteure||MONT).map(", "(monteure||MONT)"),
    "ez": (",monteure.map(function(m){return h('option',{key:m.id,value:m.id},m.n||m.id);}))", "monteure"),
    "abs_rows": ("const _absRows=()=>(monteure||[]).map(", "(monteure||[])"),
    "vz_def": ("((allWorkers[0]||{}).id)", "((allWorkers[0]||{}).id)"),
    "vz_modal": ("_mtMitGetragenem(allWorkers,(monteure||MONT),", None),
    "sz": (", allMA.map(m=>(React.createElement('option'", "allMA"),
    "ze_sel": ("            fieldMA.map(m=>React.createElement('option'", None),
    "abs_kal": ("(isAdmin?names:names.filter(m=>m===myMonteurName))", None),
}

KOPF = r"""
"use strict";
%(funktionen)s
function _tag(off){var d=new Date(_ezHeuteISO()+"T12:00:00Z");d.setUTCDate(d.getUTCDate()+off);return d.toISOString().slice(0,10);}
function dk(d){return d.toISOString().slice(0,10);}
var HEUTE=_ezHeuteISO(), GESTERN=_tag(-1);
var monteure=[
  {id:"w1",n:"Aktiv Anton",r:"Monteur"},
  {id:"w2",n:"Gegangen Gerd",r:"Monteur",austritt:GESTERN},
  {id:"w3",n:"Kuendigt Karl",r:"Monteur",austritt:_tag(1)}
];
var MONT=[];
function ids(l){return l.map(function(m){return m.id;});}
var A={};
"""


def _schnitt(q, a, e):
    assert q.count(a) == 1, "Anker %d-mal: %r" % (q.count(a), a)
    i = q.index(a)
    return q[i:q.index(e, i) + len(e)]


def _quelle():
    return INDEX.read_text(encoding="utf-8")


def _programm(q, x):
    t = {"funktionen": "\n".join(_schnitt(q, a, e) for a, e in FUNKTIONEN)}
    js = KOPF % t
    js += r"""
var GESTERN_YM=GESTERN.slice(0,7), NACH_YM=_tag(40).slice(0,7);
var JAHR_A=Number(GESTERN.slice(0,4)), JAHR_N=JAHR_A+1;
/* Filterlisten */
A.as_leer=(function(filterMonteur,arbeitsscheine){return ids(%(as_filter)s);})("alle",[]);
A.as_akt=(function(filterMonteur,arbeitsscheine){return ids(%(as_filter)s);})("w2",[]);
A.as_daten=(function(filterMonteur,arbeitsscheine){return ids(%(as_filter)s);})("alle",[{monteur:"w2"}]);
A.kal_leer=(function(calMonteur,arbeitsscheine){return ids(%(as_kal)s);})("__alle__",[{monteur:"w1"}]);
A.kal_daten=(function(calMonteur,arbeitsscheine){return ids(%(as_kal)s);})("__alle__",[{monteur:"w2"}]);
A.mg_leer=(function(fWorker,ms){return ids(%(mg_filter)s);})("",[{worker:"w1"}]);
A.mg_akt=(function(fWorker,ms){return ids(%(mg_filter)s);})("w2",[]);
A.mg_daten=(function(fWorker,ms){return ids(%(mg_filter)s);})("",[{zugewiesen:"w2"}]);
/* Entfernungszulage - Monat */
A.ez_nach=(function(ym,ezWid){return ids(%(ez)s);})(NACH_YM,"");
A.ez_akt=(function(ym,ezWid){return ids(%(ez)s);})(NACH_YM,"w2");
A.ez_monat=(function(ym,ezWid){return ids(%(ez)s);})(GESTERN_YM,"");
/* Buero Abwesenheits-Jahrestabelle */
A.rows_nach=(function(_abYr){return ids(%(abs_rows)s);})(JAHR_N);
A.rows_jahr=(function(_abYr){return ids(%(abs_rows)s);})(JAHR_A);
/* VZeit */
A.vz_def=(function(allWorkers){return %(vz_def)s;})([monteure[1],monteure[0]]);
function _vzm(addDay,addWorker){var allWorkers=monteure;return ids(%(vz_modal)saddWorker));}
A.vz_heute=_vzm(HEUTE,"w1");
A.vz_frueher=_vzm(_tag(-5),"w1");
A.vz_traeger=_vzm(HEUTE,"w2");
/* Stundenzettel */
function _sz(selJahr,selMonat,selMA){var users=[{id:"u1",name:"Chef",active:true}];%(hist_allma)s%(sz)sreturn ids(_szWaehlbar);}
A.sz_nach=_sz(Number(NACH_YM.slice(0,4)),Number(NACH_YM.slice(5,7))-1,"");
A.sz_akt=_sz(Number(NACH_YM.slice(0,4)),Number(NACH_YM.slice(5,7))-1,"w2");
A.sz_monat=_sz(Number(GESTERN_YM.slice(0,4)),Number(GESTERN_YM.slice(5,7))-1,"");
A.sz_alle_mon=_sz(JAHR_N,"alle","");
/* AbsView */
%(hist_names)s
%(abs_ab)s
A.tl_heute=(function(days){return %(abs_tl)s;})([new Date(HEUTE+"T00:00:00Z")]);
A.tl_frueher=(function(days){return %(abs_tl)s;})([new Date(_tag(-14)+"T00:00:00Z")]);
function _mo(ym,abs,sel,welche){var yr=Number(ym.slice(0,4)),mo=Number(ym.slice(5,7))-1;var isAdmin=true,myMonteurName="Aktiv Anton";%(abs_immonat)sreturn welche==="kal"?%(abs_kal)s:%(abs_mo)s;}
var ABS_D={}; ABS_D["Gegangen Gerd_"+NACH_YM+"-05"]={type:"krankenstand"};
A.mo_nach=_mo(NACH_YM,{},"","mo");
A.mo_monat=_mo(GESTERN_YM,{},"","mo");
A.mo_daten=_mo(NACH_YM,ABS_D,"","mo");
A.kal_nach=_mo(NACH_YM,{},"","kal");
A.kal_monat=_mo(GESTERN_YM,{},"","kal");
A.kal_daten=_mo(NACH_YM,ABS_D,"","kal");
A.kal_sel=_mo(NACH_YM,{},"Gegangen Gerd","kal");
A.jahr_nach=(function(yr){return %(abs_jahr)s;})(JAHR_N);
A.jahr_a=(function(yr){return %(abs_jahr)s;})(JAHR_A);
A.hist_names=names;
/* Zeiterfassung */
function _ze(mon,selWorker){var isoDate=function(off){return mon;};%(ze_wo)sreturn ids(%(ze_sel)s);}
A.ze_heute=_ze(HEUTE,"");
A.ze_frueher=_ze(_tag(-7),"");
A.ze_traeger=_ze(HEUTE,"w2");
console.log(JSON.stringify(A));
""" % x
    return js


def _lauf(tmp_path, q, x, name):
    p = tmp_path / name
    p.write_text(_programm(q, x), encoding="utf-8")
    r = subprocess.run(["node", str(p)], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


@pytest.fixture(scope="module")
def aus(tmp_path_factory):
    q = _quelle()
    x = {}
    for k, (expr, n) in X.items():
        assert q.count(expr) == n, "%s: %d-mal statt %d" % (k, q.count(expr), n)
        x[k] = expr
    return _lauf(tmp_path_factory.mktemp("v1049"), q, x, "jetzt.js")


def test_00_koeder_praedikat_sieht_den_ausgetretenen(aus):
    # Ohne Ausgetretenen in der Grundliste waere jedes "fehlt" wertlos
    assert "w2" in aus["as_akt"] and "Gegangen Gerd" in aus["hist_names"]


@pytest.mark.parametrize("k", ["as_leer", "kal_leer", "mg_leer", "ez_nach", "rows_nach", "vz_heute",
                               "sz_nach", "sz_alle_mon", "tl_heute", "mo_nach", "kal_nach", "jahr_nach", "ze_heute"])
def test_ausgetretener_fehlt_in_live_und_spaeteren_zeitraeumen(aus, k):
    l = aus[k]
    assert "w2" not in l and "Gegangen Gerd" not in l, (k, l)
    # wer bleibt, steht weiter drin
    assert "w1" in l or "Aktiv Anton" in l, (k, l)
    # wer erst MORGEN geht, ist HEUTE noch da (in spaeteren Zeitraeumen zu Recht nicht mehr)
    if k in ("as_leer", "kal_leer", "mg_leer", "vz_heute", "tl_heute", "ze_heute"):
        assert "w3" in l or "Kuendigt Karl" in l, (k, l)
    else:
        assert "w3" not in l and "Kuendigt Karl" not in l, (k, l)


@pytest.mark.parametrize("k", ["as_akt", "mg_akt", "ez_akt", "vz_traeger", "sz_akt", "ze_traeger", "kal_sel"])
def test_aktueller_wert_bleibt_in_seiner_liste(aus, k):
    assert "w2" in aus[k] or "Gegangen Gerd" in aus[k], (k, aus[k])


@pytest.mark.parametrize("k", ["as_daten", "kal_daten", "mg_daten", "ez_monat", "rows_jahr", "vz_frueher",
                               "sz_monat", "tl_frueher", "mo_monat", "mo_daten", "kal_monat", "kal_daten",
                               "jahr_a", "ze_frueher", "hist_names"])
def test_historie_und_zeitraum_vor_austritt_behalten_ihn(aus, k):
    l = aus[k]
    assert "w2" in l or "Gegangen Gerd" in l, (k, l)


def test_vorbelegung_ist_nie_ein_ausgetretener(aus):
    assert aus["vz_def"] == "w1"


def test_alte_ausdruecke_sind_weg():
    q = _quelle()
    for k, (alt, _) in ALT.items():
        assert alt not in q, "%s: alter Ausdruck steht wieder im Code: %r" % (k, alt)


def test_gegenprobe_alte_ausdruecke_zeigen_den_ausgetretenen(tmp_path):
    """Die alten Formen IM SPEICHER zurueckgebaut: dieselben Proben werden rot."""
    q = _quelle()
    x = dict((k, e) for k, (e, _) in X.items())
    x["as_filter"] = "monteure"
    x["as_kal"] = "monteure"
    x["mg_filter"] = "(monteure||MONT)"
    x["ez"] = "monteure"
    x["abs_rows"] = "(monteure||[])"
    x["vz_def"] = "((allWorkers[0]||{}).id)"
    x["vz_modal"] = "_mtMitGetragenem(allWorkers,(monteure||MONT),"
    x["sz"] = "var _szWaehlbar=allMA;"
    x["abs_tl"] = x["abs_mo"] = x["abs_jahr"] = "names"
    x["abs_kal"] = "(isAdmin?names:names.filter(m=>m===myMonteurName))"
    x["ze_wo"] = "var fieldMAWo=monteure.filter(m=>!_maIstEhemalig(m,HEUTE));"
    x["ze_sel"] = "fieldMAWo"
    a = _lauf(tmp_path, q, x, "alt.js")
    for k in ["as_leer", "kal_leer", "mg_leer", "ez_nach", "rows_nach", "vz_heute", "sz_nach", "tl_heute",
              "mo_nach", "kal_nach", "jahr_nach"]:
        assert "w2" in a[k] or "Gegangen Gerd" in a[k], ("Gegenprobe stumm", k, a[k])
    assert a["vz_def"] == "w2"
    # alte Zeiterfassung (Heute-Liste) verlor den Ausgetretenen auch in der Woche VOR dem Austritt
    assert "w2" not in a["ze_frueher"]
