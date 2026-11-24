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
    # Tausender-Nachtrag 24.11.2026: Eingabefelder und Excel-Zelltexte rufen fmtStdEingabe (ohne Gruppierung) - mitschneiden, sofern vorhanden.
    ein = (_fn(src, "function fmtStdEingabe(v){") + "\n") if "function fmtStdEingabe(v){" in src else ""
    return _fn(src, "function _fzZahl(v){") + "\n" + _fn(src, "function fmtStd(v){") + "\n" + ein


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
    # Paket 13a (GF 24.11. abends): FinkZeit-Druckblatt, Regiebericht-Druck und Bautagesbericht-PDF bleiben wie 3.9.1114
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


# ── 4 Excel: Paket 13a (GF 24.11.2026 abends) - KEIN Export aendert sich in 3.9.1115; die Excel-Tests liegen mit den
#    Excel-Aenderungen auf feature/excel-stunden-zahl. Ausgabe-Riegel: test_exporte_golden_v1114.py.
