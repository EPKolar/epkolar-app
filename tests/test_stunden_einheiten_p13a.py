"""Paket 13a (GF 24.11.2026 abends): fmtStd (zwei Nachkommastellen) NUR fuer echte Stunden.

Gemessen am Stand 3.9.1115: alle 140 Aufrufe von fmtStd, _absH und _hK (die beiden Helfer rufen seit Paket 13
fmtStd und ignorieren ihr Stellen-Argument) zeigen STUNDEN (Suffix "h"/"Std." oder Stunden-Spalte/-Kachel).
Kein Aufruf zeigt Tage, km, Prozent, Stueckzahlen oder Euro. Tabelle mit Zeile, Einheit, Stellen vorher/nachher
im Bericht C:/repos/epk-paket13-15-report.md.

Dieser Riegel listet die Aufrufe ABSCHLIESSEND: ein neuer Aufruf (z. B. fmtStd(km)) macht ihn rot und muss
bewusst als Stunden-Aufruf eingetragen werden. Daneben bleiben die anderen Einheiten bei ihren alten Formatierern
(Beispiele unten, gleiche Anzeige wie 3.9.1114).
"""
import collections
import json
import re
import shutil
import subprocess

import pytest

NODE = shutil.which("node")
needs_node = pytest.mark.skipif(not NODE, reason="node fehlt")

# Aufruf -> Anzahl. Alle sind Stunden.
STUNDEN_AUFRUFE = {
    "_absH((_ktgStd(_optionalChain([kontingent, 'access', _576 => _576[sel], 'optionalAccess', _577 => _577.stunden]))+(_optionalChain([kontingent, 'access', _578 => _578[sel], 'optionalAccess', _579 => _579.vorjahr])||0)),1)": 1,
    '_absH((e.hours||0),1)': 1,
    '_absH((ys.krankenstandStd||0),1)': 1,
    '_absH(_apTeH,1)': 1,
    '_absH(_cth,1)': 1,
    '_absH(_ktgStd(ks.stunden),1)': 2,
    '_absH(_teH,1)': 1,
    '_absH(d.hours,1)': 1,
    '_absH(ks.ueberstunden,1)': 2,
    '_absH(ks.vorjahr||0,1)': 2,
    '_absH(ks.woche||38.5,1)': 2,
    '_absH(mRest,1)': 1,
    '_absH(rest,1)': 4,
    '_absH(resturlaub(m),1)': 1,
    '_absH(resturlaub(sel),1)': 2,
    '_absH(stdVonTag(d,_wocheOf(sel)),1)': 2,
    '_absH(total,1)': 2,
    '_absH(valH,1)': 1,
    '_absH(ys.krankenstandStd,1)': 2,
    '_absH(ys.krankenstandStd||0,1)': 1,
    '_absH(ys.pflegeStdGes,1)': 2,
    '_absH(ys.sonderStdGes,1)': 2,
    '_absH(ys.urlaubStd,1)': 2,
    '_absH(ys.urlaubStdAusstehend,1)': 3,
    '_absH(ys.urlaubStdGen,1)': 1,
    '_absH(ys.urlaubStdGen||ys.urlaubStd,1)': 1,
    '_absH(ys.zeitausgleichStd,1)': 2,
    '_hK(_gesZE,2)': 2,
    '_hK(_h,2)': 2,
    '_hK(_plz.sum,2)': 1,
    '_hK(dt,2)': 2,
    '_hK(entry.hours,2)': 1,
    '_hK(h,2)': 1,
    '_hK(m.total,2)': 2,
    '_hK(t,2)': 2,
    '_hK(weekTotal,2)': 4,
    'fmtStd((entry.stunden||entry.hours||0))': 1,
    'fmtStd((parseFloat(x.hours||x.stunden)||0))': 1,
    # Paket 14 (3.9.1115): Summe der Stunden in der KW-Vorschau 'Berichte bearbeiten' - Stunden
    'fmtStd((rs||[]).reduce((a,r)=>{const _d=String(r.datum||"").slice(0,10);if(!(_d>=_kwVon&&_d<=_kwBis))return a;const _x=_fzZahl(r.stunden);return a+(isFinite(_x)?_x:0);},0))': 1,
    'fmtStd(Math.abs(diff))': 1,
    'fmtStd(_beMaSumme+_beOhneMa)': 2,
    'fmtStd(_beOhneMa)': 1,
    'fmtStd(_hA)': 1,
    'fmtStd(_hP)': 1,
    'fmtStd(_hR)': 1,
    'fmtStd(_kapSel.sollPer)': 1,
    'fmtStd(_kz.std)': 1,
    'fmtStd(_mySummary.ist)': 1,
    "fmtStd(_optionalChain([ab, 'optionalAccess', _588 => _588.hours])||0)": 1,
    'fmtStd(_zeitStats.lastWeekH)': 1,
    'fmtStd(_zeitStats.thisWeekH)': 1,
    'fmtStd(_zeitStats.totalH)': 1,
    'fmtStd(_zeitStats.totalH/_wkVerstrichen)': 1,
    'fmtStd(b.h)': 2,
    'fmtStd(byDate[dt])': 1,
    'fmtStd(diff)': 2,
    'fmtStd(dt)': 2,
    'fmtStd(epH)': 2,
    'fmtStd(fH)': 1,
    'fmtStd(h)': 7,
    'fmtStd(hrs)': 2,
    'fmtStd(kapIst)': 1,
    'fmtStd(kapSoll)': 1,
    'fmtStd(kwTotal)': 2,
    'fmtStd(lastWH.reduce((a,b)=>a+b,0))': 1,
    'fmtStd(moHours.reduce((a,b)=>a+b,0))': 1,
    'fmtStd(ms.hrs)': 2,
    'fmtStd(pe.reduce((s,x)=>s+_h(x),0))': 2,
    'fmtStd(pp[1])': 1,
    'fmtStd(prH)': 1,
    'fmtStd(ps.hrs)': 1,
    'fmtStd(r.hours)': 2,
    'fmtStd(r.rest)': 2,
    'fmtStd(r.zuschlagStd)': 1,
    'fmtStd(rest)': 1,
    'fmtStd(rowSum)': 1,
    'fmtStd(std)': 2,
    'fmtStd(sum)': 1,
    'fmtStd(tE.reduce((s,x)=>s+_h(x),0))': 1,
    'fmtStd(thisWH.reduce((a,b)=>a+b,0))': 1,
    'fmtStd(todayH)': 1,
    'fmtStd(total)': 1,
    'fmtStd(totalH)': 4,
    'fmtStd(v)': 4,
    'fmtStd(w.hours)': 1,
    'fmtStd(wSum)': 1,
    'fmtStd(we.reduce((s,x)=>s+_h(x),0))': 1,
    'fmtStd(weekH)': 1,
    'fmtStd(weekTotal)': 1,
    'fmtStd(ys.krankenstandStd)': 1,
    'fmtStd(ys.urlaubStd)': 1,
    'fmtStd(ys.zeitausgleichStd)': 1,
}


def _aufrufe(src):
    pat = re.compile(r"(?<![\w.])(fmtStd|_absH|_hK)\(")
    c = collections.Counter()
    for l in src.split("\n"):
        for mm in pat.finditer(l):
            st = l.lstrip()
            if st.startswith(("function fmtStd", "function fmtStdEingabe")) or (
                    re.match(r"\s*const (_absH|_hK)=", l) and mm.start() < l.index("=>") + 3):
                continue
            p = mm.end()
            d = 1
            q = p
            while q < len(l) and d:
                if l[q] == "(":
                    d += 1
                elif l[q] == ")":
                    d -= 1
                q += 1
            c[mm.group(0) + l[p:q]] += 1
    return c


def test_nur_stunden_aufrufe(index_html):
    ist = _aufrufe(index_html.replace("\r\n", "\n"))
    neu = {k: v for k, v in ist.items() if STUNDEN_AUFRUFE.get(k) != v}
    weg = {k: v for k, v in STUNDEN_AUFRUFE.items() if ist.get(k) != v}
    assert not neu and not weg, ("neu/geaendert", neu, "fehlt", weg)
    assert sum(ist.values()) == 141  # 140 aus Paket 13a + 1 Summe aus Paket 14


def test_umkehrprobe_km_waere_rot(index_html):
    kaputt = index_html.replace("_fzKmDe(s.km,2)+' km'", "fmtStd(s.km)+' km'", 1)
    assert kaputt != index_html
    ist = _aufrufe(kaputt.replace("\r\n", "\n"))
    assert ist != collections.Counter(STUNDEN_AUFRUFE)


def test_andere_einheiten_bleiben_beim_alten_formatierer(index_html):
    # km (Fahrtenbuch/Flotte), Prozent (Auslastung), Tage (Abwesenheit), Liter, Euro - unveraendert seit 3.9.1114
    for stelle in ("_fzKmDe(s.km,2)+' km'", "'Spitze: '+_fzKmDe(bestTag.km,1)+' km'", "+' h · '+w.pct+' %')",
                   'var _bTage=b.count+(b.count===1?" Tag":" Tage");', "_projStdDE(it.value,1)",
                   'unit==="€"?_eurKachel(v):fmtStd(v)'):
        assert stelle in index_html, stelle


@needs_node
def test_alte_formatierer_zeigen_wie_1114(index_html):
    s = index_html.replace("\r\n", "\n")
    def zeile(k):
        i = s.index(k)
        return s[i:s.index("\n", i)]
    def fn(k):
        i = s.index(k)
        return s[i:s.index("\n}", i) + 2]
    js = (zeile("function _projStdDE(v,d){") + "\n" + fn("function _fzKmDe(v,d){") + "\n"
          + "console.log(JSON.stringify([_projStdDE(2.5,1),_projStdDE(1126.8,1),_projStdDE(40,0),_fzKmDe(12.345,2),_fzKmDe(1234.5,1)]));")
    r = subprocess.run([NODE, "-e", js], capture_output=True, text=True, encoding="utf-8", timeout=60)
    assert r.returncode == 0, r.stderr[-1500:]
    out = json.loads(r.stdout)
    assert out[:3] == ["2,5", "1\u00a0126,8", "40"], out  # Liter/Tage-Werte wie 3.9.1114 (de-AT, U+00A0)
    assert out[3].startswith("12,3"), out
