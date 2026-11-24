"""Paket 13 (GF 24.11.2026): Stunden-ANZEIGE ueberall genau zwei Nachkommastellen mit Komma.

Eine gemeinsame Funktion fmtStd: 5 -> "5,00", 9.5 -> "9,50", 4.75 -> "4,75", 8.1666 -> "8,17",
leer -> "" (nicht "0,00"). Nur Anzeige: der gespeicherte Wert bleibt unveraendert. Stempelzeit bleibt H:MM.
Excel: Stunden-Spalten bleiben ZAHL (x:num) und bekommen das Zahlenformat 0,00 (mso-number-format "0\\.00").
Stunden-Eingaben (ZahlEingabe stunden:true) zeigen ohne Fokus fmtStd, mit Fokus den getippten Text.

Jeder Test hat eine Umkehrprobe gegen den Altstand (git show 2a736fe:index.html) - siehe
C:/repos/epk-paket13-15-report.md.
"""
import json
import re
import shutil
import subprocess

import pytest

NODE = shutil.which("node")
needs_node = pytest.mark.skipif(not NODE, reason="node fehlt")


def _fn(src, kopf):
    i = src.index(kopf)
    return src[i:src.index("\n}", i) + 2]


def _node(js):
    r = subprocess.run([NODE, "-e", js], capture_output=True, text=True, encoding="utf-8", timeout=60)
    assert r.returncode == 0, r.stderr[-2000:]
    return r.stdout


def _fmt_js(src):
    return _fn(src, "function _fzZahl(v){") + "\n" + _fn(src, "function fmtStd(v){") + "\n"


# ── 1 der Formatierer ───────────────────────────────────────────────────────
@needs_node
def test_fmtstd_zwei_stellen_komma_leer_bleibt_leer(index_html):
    js = _fmt_js(index_html) + r"""
const e={stunden:8.1666};const vorher=e.stunden;
const out=[fmtStd(5),fmtStd(9.5),fmtStd(4.75),fmtStd(e.stunden),fmtStd(""),fmtStd(null),fmtStd(undefined),
           fmtStd("9,5"),fmtStd("9.5"),fmtStd(0),fmtStd(844.6),fmtStd(1.005),fmtStd(-1.5),fmtStd("abc")];
console.log(JSON.stringify({out,gleich:e.stunden===vorher&&e.stunden===8.1666}));"""
    r = json.loads(_node(js))
    assert r["out"] == ["5,00", "9,50", "4,75", "8,17", "", "", "", "9,50", "9,50", "0,00", "844,60", "1,01", "-1,50", ""]
    assert r["gleich"], "fmtStd darf den gespeicherten Wert nicht veraendern"


# ── 2 Anzeigestellen laufen ueber fmtStd ────────────────────────────────────
ANZEIGE = [
    # Monteur-Uebersicht (zeigte 844,6)
    "fmtStd(ms.hrs)",
    # Zeiterfassung: Statistik-Kacheln
    'fmtStd(_zeitStats.totalH)+" h"', 'fmtStd(_zeitStats.thisWeekH)+" h"', 'fmtStd(_zeitStats.lastWeekH)+" h"',
    # Projekt-Wochenraster / Wochenbericht
    'fmtStd(kwTotal), " h")', "fmtStd(totalH)", "fmtStd(sum)",
    # Buero-Portal: Abwesenheiten-Tabelle, Krankenstand
    'fmtStd(r.rest)+" h"', "fmtStd(b.h)",
    # Abwesenheiten-Kopf
    "fmtStd(ys.urlaubStd)", "fmtStd(rest)",
    # Ueberstunden-Uebersicht (KV)
    "fmtStd(r.zuschlagStd)+' h'",
    # FinkZeit-Abgleich (Druck)
    "${fmtStd(epH)}h",
    # Bautagesbericht (Druck + PDF)
    "${fmtStd(totalStd)}", 'doc.text(_pdfStr(fmtStd(sum)+" h"),M+100,y);',
]


@pytest.mark.parametrize("stelle", ANZEIGE)
def test_anzeigestelle_ueber_fmtstd(index_html, stelle):
    assert stelle in index_html, stelle


def test_hilfsformatierer_rufen_fmtstd(index_html):
    assert "const _absH=(v,d)=>fmtStd(v);" in index_html
    assert "const _hK=(v,d)=>fmtStd(v);" in index_html


def test_keine_stunden_anzeige_mit_einer_stelle_mehr(index_html):
    """_projStdDE bleibt nur fuer Liter; Stunden mit einer Stelle (Statistik-Kacheln, Abwesenheiten-Kopf) sind weg."""
    rest = re.findall(r"_projStdDE\([^)]*\)", index_html)
    assert sorted(rest) == ["_projStdDE(it.value,1)", "_projStdDE(v,d)"], rest
    for alt in ['(Math.round(_zeitStats.totalH*10)/10).toLocaleString("de-AT")+" h"',
                '_n(ys.urlaubStd,1).replace(".",",")', "var titel=iso+' · '+_n(std,1)+' h';", "String(_n(_kapSel.sollPer,1)).replace('.',',')"]:
        assert alt not in index_html, alt


def test_stempelzeit_bleibt_hmm(index_html):
    """Stempelzeit bleibt H:MM - die Stempel-Formatierer werden nicht auf fmtStd umgestellt."""
    assert '"Summe "+_msHM(summe)+" h"' in index_html
    assert 'zeile("Stempelstunden gesamt:",_mfHM(sum.min)+" h");' in index_html


def test_bautagesbericht_summe_liest_komma(index_html):
    """Die PDF-Summe liest die angezeigten Stunden zurueck - mit "9,50 h" muss das Komma gelesen werden."""
    assert 'const hv=_fzZahl(String(h).replace(" h",""));if(!isNaN(hv))sum+=hv;' in index_html


# ── 3 Stunden-Eingaben ──────────────────────────────────────────────────────
@needs_node
def test_stundenfeld_zeigt_ohne_fokus_zwei_stellen(index_html):
    js = _fmt_js(index_html) + _fn(index_html, "function _tankEinDE(v){") + "\n" + _fn(index_html, "function ZahlEingabe(props){") + r"""
let st=[null];const React={useState:(v)=>[st[0],x=>{st[0]=x;}],createElement:(t,p)=>p};
const a=ZahlEingabe({stunden:true,value:9.5,onChange:()=>{}});
const b=ZahlEingabe({value:9.5,onChange:()=>{}});
const c=ZahlEingabe({stunden:true,value:"",onChange:()=>{}});
st[0]="9,";const d=ZahlEingabe({stunden:true,value:9.5,onChange:()=>{}});
console.log(JSON.stringify([a.value,'stunden' in a,a.type,a.inputMode,b.value,c.value,d.value]));"""
    assert json.loads(_node(js)) == ["9,50", False, "text", "decimal", "9,5", "", "9,"]


def test_stundenfelder_tragen_stunden_true(index_html):
    assert index_html.count("ZahlEingabe,{stunden:true,inputMode") == 2  # Zeiterfassung Dialog (Projekt + Wochenansicht)
    for feld in ("value: editEntry.hours,", "value: ks.woche||38.5,", "value: _ktgStd(ks.stunden),",
                 "value: ks.vorjahr||0,", "value: ks.ueberstunden||0,", "value: form.budgetStunden==null"):
        assert ('{ stunden:true, inputMode:"decimal", ' + feld) in index_html, feld


# ── 4 Excel: Zahl bleibt Zahl, Format 0,00 ──────────────────────────────────
def _xls_js(src):
    a = src.index("const _XNUM=")
    b = src.index("const genXls=(title,subtitle,headers,rows,filename,opts={})=>{")
    e = src.index("\n};", b) + 3
    return (_fn(src, "function _n(v,d){") + "\n" + _fmt_js(src)
            + "const _nullishCoalesce=(v,f)=>(v!=null?v:f());const CF_HTML_AGB='',CF_HTML_LINE1='',CF_HTML_LINE2='',COMPANY_FOOTER={web:'',name:''};const window={},_optionalChain=()=>undefined;let OUT=null;const _dl=(blob,fn)=>{OUT={blob,fn};};\n"
            + src[a:b] + src[b:e] + "\n")


@needs_node
def test_excel_stundenspalte_bleibt_zahl_mit_format(index_html):
    js = _xls_js(index_html) + r"""
genXls("Test","t",["Name","Stunden"],[["A","9.50"],["B","4.75"],["C",""]],"t.xls",{stdCols:[1],sumCol:1});
OUT.blob.text().then(t=>console.log(JSON.stringify(t)));"""
    t = json.loads(_node(js))
    assert 'td.xs{mso-number-format:"0\\.00";}' in t
    assert 'class="xs" x:num="9.50"' in t and ">9,50</td>" in t
    assert 'class="xs" x:num="4.75"' in t and ">4,75</td>" in t
    assert 'class="xs" x:num="14.25"' in t, "Summenzeile bleibt Zahl mit Format 0,00"


@pytest.mark.parametrize("aufruf", [
    '"Abwesenheiten_"+_abYr+".xls",{leftCols:[0],stdCols:[1,2,3,4,5,6]}',
    '"Krankenstand_"+_abYr+".xls",{leftCols:[0,1,3,4],stdCols:[2]}',
    "boldCols:[2,4],sumCol:5,stdCols:[5]}",
    "boldCols:[1],stdCols:[5,6,7,8],statusMap:",
    "sumCol:9,stdCols:[2,3,4,5,6,7,8,9,10]}",
    "boldCols:[2],sumCol:5,stdCols:[5]}",
    "leftCols:[0,1],boldCols:[1],stdCols:[2,3,4,5,6,7,8]}",
    "boldCols:[2],sumCol:8,stdCols:[7,8]}",
])
def test_stunden_exporte_haben_stdcols(index_html, aufruf):
    assert aufruf in index_html
