# -*- coding: utf-8 -*-
"""v3.9.1109 Monteur-Uebersicht (Buero-Portal, Alle Daten): ganze Zeile/Karte oeffnet die letzten 50 Eintraege.

Der Ausdruck monteurStats.map(...) fuer Tabelle (Tablet/PC) und Karten (Handy) wird aus index.html geschnitten und in Node
mit einem Mini-React ausgewertet. Klicks werden mit echtem Hochblubbern (Ziel -> Vorfahren, stopPropagation) nachgestellt.
Erwartung je Fassung: Klick auf Name, auf die Zeile und auf den Stift oeffnet GENAU EINMAL den richtigen Monteur;
Enter auf der Zeile ebenso; Enter auf dem Stift loest nicht zusaetzlich die Zeile aus. Die Summenzeile bleibt ohne Klick.
"""
import io
import json
import os
import re
import shutil
import subprocess

import pytest

HTML = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "index.html")
NODE = shutil.which("node")


def _src():
    return io.open(HTML, encoding="utf-8", newline="").read()


def _ausdruck(s, start):
    """schneidet den Ausdruck ab start bis zur schliessenden Klammer des ersten '(' (Strings werden uebersprungen)."""
    i = s.index("(", start)
    tiefe, q, k = 0, None, i
    while True:
        c = s[k]
        if q:
            if c == "\\":
                k += 2
                continue
            if c == q:
                q = None
        elif c in "'\"`":
            q = c
        elif c == "(":
            tiefe += 1
        elif c == ")":
            tiefe -= 1
            if tiefe == 0:
                return s[start:k + 1]
        k += 1


def _teile(s):
    v = s[s.index("function VBueroExport("):]
    tab = _ausdruck(v, v.index("monteurStats.map(ms=>React.createElement('tr'"))
    karten = _ausdruck(v, v.index("monteurStats.map(function(ms){return React.createElement('div',{key:ms.id"))
    a = v.index("React.createElement('tfoot'")
    summe = v[a:v.index("React.createElement('td'", v.index("Summe\")", a))]
    return tab, karten, summe


SIM = r"""
const React={createElement:(t,p,...c)=>({t,p:p||{},c:[].concat(...c.map(x=>Array.isArray(x)?x.flat(9):[x])).filter(x=>x&&typeof x==='object')})};
const V={bd:'#ccc',bg:'#fff',cd:'#fff',dm:'#777',tx:'#000'},UI={fMeta:12,zahlen:{}};
const _beKleb=()=>({}),_projStdDE=x=>String(x),fmtStd=x=>String(x)/* Paket 13 (GF 24.11.2026): Stunden-Anzeige zentral ueber fmtStd (genau zwei Nachkommastellen, Komma, leer bleibt leer) - Pin bewusst nachgezogen */,_beStiftSt={},_ik=()=>null;
const ruf=[];const editMonteurEntries=ms=>ruf.push(ms.id);
const monteurStats=[{id:'w1',name:'Huber',vorname:'Anton',rolle:'monteur',hrs:1,projCnt:1,btCnt:0,regCnt:0},
                    {id:'w2',name:'Maier',vorname:'Berta',rolle:'monteur',hrs:2,projCnt:1,btCnt:0,regCnt:0}];
const baum=(AUSDRUCK);
function eltern(n,p,out){for(const k of n.c){out.set(k,n);eltern(k,n,out);}return out;}
const wurzel={t:'root',p:{},c:baum};const E=eltern(wurzel,null,new Map());
function finde(n,f){if(f(n))return n;for(const k of n.c){const r=finde(k,f);if(r)return r;}return null;}
function feuer(ziel,art,extra){const ev=Object.assign({stopped:false,defaultPrevented:false,target:ziel,stopPropagation(){this.stopped=true;},preventDefault(){this.defaultPrevented=true;}},extra||{});
  for(let n=ziel;n&&n!==wurzel;n=E.get(n)){const h=n.p[art];if(h){ev.currentTarget=n;h(ev);}if(ev.stopped)break;}return ev;}
const erg={};
for(const ms of monteurStats){
  const zeile=baum.find(z=>z.p.key===ms.id);
  const name=finde(zeile,n=>n.c.length===0&&false)||finde(zeile,n=>n!==zeile&&(n.t==='td'||n.t==='div')&&!n.p.onClick);
  const stift=finde(zeile,n=>n.t==='button');
  const r={};
  ruf.length=0;feuer(name,'onClick');r.name=ruf.slice();
  ruf.length=0;feuer(zeile,'onClick');r.zeile=ruf.slice();
  ruf.length=0;feuer(stift,'onClick');r.stift=ruf.slice();
  ruf.length=0;feuer(zeile,'onKeyDown',{key:'Enter'});r.enter_zeile=ruf.slice();
  ruf.length=0;const ev=feuer(stift,'onKeyDown',{key:'Enter'});if(!ev.defaultPrevented)feuer(stift,'onClick');r.enter_stift=ruf.slice();
  r.tabindex=zeile.p.tabIndex;r.klasse=zeile.p.className;
  erg[ms.id]=r;}
console.log(JSON.stringify(erg));
"""


def _lauf(ausdruck):
    out = subprocess.run([NODE, "-e", SIM.replace("(AUSDRUCK)", "(" + ausdruck + ")")], capture_output=True, text=True, encoding="utf-8")
    assert out.returncode == 0, out.stderr[-800:]
    return json.loads(out.stdout.strip().splitlines()[-1])


def _fehler(erg):
    f = []
    for wid, r in erg.items():
        for k in ("name", "zeile", "stift", "enter_zeile", "enter_stift"):
            if r[k] != [wid]:
                f.append("%s %s -> %s" % (wid, k, r[k]))
        if r["tabindex"] != 0 or r["klasse"] != "epk-zeile-klick":
            f.append(wid + " nicht als klickbar erkennbar")
    return f


@pytest.mark.skipif(not NODE, reason="node fehlt")
@pytest.mark.parametrize("fassung", ["tabelle", "karten"])
def test_klick_oeffnet_genau_einmal_den_richtigen(fassung):
    tab, karten, _ = _teile(_src())
    assert _fehler(_lauf(tab if fassung == "tabelle" else karten)) == []


@pytest.mark.skipif(not NODE, reason="node fehlt")
@pytest.mark.parametrize("fassung", ["tabelle", "karten"])
def test_umkehrprobe_ohne_stopPropagation_doppelt(fassung):
    tab, karten, _ = _teile(_src())
    a = tab if fassung == "tabelle" else karten
    kaputt = a.replace("e.stopPropagation();editMonteurEntries(ms);", "editMonteurEntries(ms);", 1)
    assert kaputt != a
    assert any("stift" in x for x in _fehler(_lauf(kaputt)))


def test_summenzeile_nicht_klickbar_und_hinweis():
    s = _src()
    _, _, summe = _teile(s)
    assert "onClick" not in summe and "epk-zeile-klick" not in summe and "tabIndex" not in summe
    assert '"Klick auf die Zeile oder den Knopf ",_zpIkI("stift")' in s
    assert ".epk-zeile-klick{cursor:pointer}" in s
