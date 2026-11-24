"""Tausender-Nachtrag zu Paket 13 (GF-Entscheidung 24.11.2026 abends).

Die Stunden-ANZEIGE gruppiert Tausender wieder so wie die App vor Paket 13:
toLocaleString("de-AT") lieferte "1 126,8" (Monteur-Uebersicht) - das Gruppenzeichen ist das
geschuetzte Leerzeichen U+00A0 (NO-BREAK SPACE), gemessen mit node (ICU) an dfc369b/_projStdDE.
fmtStd(1234.5) -> "1 234,50", 5 -> "5,00", 8.1666 -> "8,17", leer -> "".

Eingabefelder (ZahlEingabe stunden:true) zeigen KEINE Gruppierung ("1234,50"), bleiben type=text,
inputMode=decimal und lesen Komma oder Punkt. Exporte sind in 3.9.1115 unveraendert (Paket 13a).
Summen/gespeicherte Werte unveraendert.

Umkehrprobe: gegen 3ba544b (Paket 13 ohne Tausender) sind die Gruppierungs-Tests rot.
"""
import json
import shutil
import subprocess

import pytest

NODE = shutil.which("node")
needs_node = pytest.mark.skipif(not NODE, reason="node fehlt")
NBSP = " "


def _fn(src, kopf):
    i = src.index(kopf)
    return src[i:src.index("\n}", i) + 2]


def _node(js):
    r = subprocess.run([NODE, "-e", js], capture_output=True, text=True, encoding="utf-8", timeout=60)
    assert r.returncode == 0, r.stderr[-2000:]
    return r.stdout


def _fmt_js(src):
    ein = (_fn(src, "function fmtStdEingabe(v){") + "\n") if "function fmtStdEingabe(v){" in src else ""
    return _fn(src, "function _fzZahl(v){") + "\n" + _fn(src, "function fmtStd(v){") + "\n" + ein


@needs_node
def test_anzeige_gruppiert_mit_geschuetztem_leerzeichen(index_html):
    js = _fmt_js(index_html) + r"""
const out=[fmtStd(1234.5),fmtStd(5),fmtStd(8.1666),fmtStd(""),fmtStd(null),fmtStd(999.99),fmtStd(999.999),
           fmtStd(1126.8),fmtStd(1234567.891),fmtStd(-1234.5),fmtStd("1234,5"),fmtStd("1.234,5")];
console.log(JSON.stringify(out));"""
    r = json.loads(_node(js))
    assert r == ["1" + NBSP + "234,50", "5,00", "8,17", "", "", "999,99", "1" + NBSP + "000,00",
                 "1" + NBSP + "126,80", "1" + NBSP + "234" + NBSP + "567,89", "-1" + NBSP + "234,50",
                 "1" + NBSP + "234,50", "1" + NBSP + "234,50"]


@needs_node
def test_gruppenzeichen_wie_frueher_de_at(index_html):
    """Gleiches Zeichen wie die alte Anzeige toLocaleString("de-AT") (ICU in node) - 2000 Zufallswerte."""
    js = _fmt_js(index_html) + r"""
let bad=[];let x=7;for(let i=0;i<2000;i++){x=(x*48271)%2147483647;const v=(x%100000000)/100*(i%5===0?-1:1);
const r=Math.round(Math.abs(v)*100)/100;const soll=(v<0&&r>0?"-":"")+r.toLocaleString("de-AT",{minimumFractionDigits:2,maximumFractionDigits:2});
if(fmtStd(v)!==soll)bad.push([v,fmtStd(v),soll]);}
console.log(JSON.stringify({bad:bad.slice(0,5),n:bad.length,alt:(1126.8).toLocaleString("de-AT",{minimumFractionDigits:1,maximumFractionDigits:1})}));"""
    r = json.loads(_node(js))
    assert r["alt"] == "1" + NBSP + "126,8", "Messung: altes Format de-AT"
    assert r["n"] == 0, r["bad"]


@needs_node
def test_anzeige_wird_zurueck_gelesen(index_html):
    """Bautagesbericht-PDF liest die angezeigten Stunden zurueck (_fzZahl) - die Gruppierung darf die Summe nicht aendern."""
    js = _fmt_js(index_html) + r"""
console.log(JSON.stringify([_fzZahl(fmtStd(1234.5)),_fzZahl(fmtStd(1234567.891)),_fzZahl(fmtStd(8.1666))]));"""
    assert json.loads(_node(js)) == [1234.5, 1234567.89, 8.17]


@needs_node
def test_eingabefeld_ohne_gruppierung(index_html):
    js = _fmt_js(index_html) + _fn(index_html, "function _tankEinDE(v){") + "\n" + _fn(index_html, "function ZahlEingabe(props){") + r"""
let st=[null];const React={useState:(v)=>[st[0],x=>{st[0]=x;}],createElement:(t,p)=>p};
const a=ZahlEingabe({stunden:true,value:1234.5,onChange:()=>{}});
a.onFocus({});const fokus=st[0];st[0]=null;
const b=ZahlEingabe({stunden:true,value:5,onChange:()=>{}});
const c=ZahlEingabe({stunden:true,value:"",onChange:()=>{}});
st[0]="1234.5";const d=ZahlEingabe({stunden:true,value:1234.5,onChange:()=>{}});
console.log(JSON.stringify([a.value,fokus,a.type,a.inputMode,b.value,c.value,d.value,_fzZahl("1234,50"),_fzZahl("1234.5")]));"""
    assert json.loads(_node(js)) == ["1234,50", "1234,50", "text", "decimal", "5,00", "", "1234.5", 1234.5, 1234.5]


def test_stundenfeld_ruft_eingabeformat(index_html):
    assert "_std?fmtStdEingabe(aussen):_tankEinDE(aussen)" in index_html
