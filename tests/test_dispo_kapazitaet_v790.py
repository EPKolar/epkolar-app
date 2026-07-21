# -*- coding: utf-8 -*-
"""v3.9.790 — Dispo-Kapazitaet: Belegungs-Doppelabzug in der Hand-Wand behoben (Sebastian, live).

Bug: data-norm = normMin - kapAbzug (kapAbzug enthaelt die Belegung schon), dann frei = data-norm - usedMin
zog die Belegung NOCHMAL ab. w1 06.08. (Do): 510 - 360 = 150, frei = 150 - 360 = -210 -> 0 ("0h frei / passt
nicht"), obwohl korrekt 510 - 360 = 150 (2,5h frei) -> 1,5h passt. Fix: neues abwAbzug (Abwesenheit+Vorab+Sperre
OHNE Belegung); frei = _dispoNormFrei(normMin, abwAbz, usedMin) — Belegung EINMAL via usedMin. _dispoPlan-Kern
(nutzt kapAbzug inkl. Belegung) byte-identisch.
"""
import re
import subprocess


def _pure(index_html, name):
    i = index_html.index("function " + name + "(")
    j = index_html.index("\n}", i) + 2
    return index_html[i:j]


def test_dispo_normfrei_pins(index_html, node_exe, tmp_path):
    """Die 3 Freigabe-Zahlen-Pins + Hart-Regel (frei in [0,Norm]) + kein Doppel-Abzug."""
    puf = re.search(r"var PUFFER_JE_STOPP=\d+", index_html).group(0)
    js = puf + ";\n" + _pure(index_html, "_dispoNormFrei") + "\n" + _pure(index_html, "_dispoDropOk") + u"""
function ok(c,n){ if(!c){ console.error('FAIL '+n); process.exit(1);} }
// Pin 1 (Freigabe): Do norm 510 (8,5h), Abwesenheit 0, Belegung 360 (6h) -> frei 150 (2,5h)
var f1=_dispoNormFrei(510,0,360);
ok(f1===150,'Do 510-0-360=150');
ok(_dispoDropOk('a','a',false,f1,90)===true,'1,5h(90)+Puffer passt in 150');
// Pin 2: Fr norm 270 (4,5h), Belegung 180 -> frei 90
ok(_dispoNormFrei(270,0,180)===90,'Fr 270-0-180=90');
// Pin 3: Halbtag ZA (abwAbz 240) + belegt 120 -> frei 150
ok(_dispoNormFrei(510,240,120)===150,'Halbtag 510-240-120=150');
// Hart-Regel (15.07.): frei nie > Norm, nie negativ
ok(_dispoNormFrei(510,0,0)===510,'leer=Norm');
ok(_dispoNormFrei(510,0,600)===0,'ueberbucht=0');
// alter Doppel-Abzug (510-360)-360=-210->0 waere falsch; jetzt 150
ok(_dispoNormFrei(510,0,360)===150,'kein Doppel-Abzug');
console.log('ALL-OK');
"""
    f = tmp_path / "d790.js"; f.write_text(js, encoding="utf-8")
    r = subprocess.run([node_exe, str(f)], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")
    assert "ALL-OK" in r.stdout


def test_abwabzug_gebaut_ohne_belegung(index_html):
    """abwAbzug wird parallel zu kapAbzug gefuellt, aber OHNE die Belegung (die += d fliesst NUR in kapAbzug)."""
    assert "var kapAbzug={}, blockGrund={}, tagArt={}, abwAbzug={};" in index_html
    assert "abwAbzug[m.id]={};" in index_html
    assert 'abwAbzug[m.id][t.key]=abz;' in index_html, "abwAbzug = Abwesenheit+Vorab (Wert abz vor der Belegung)"
    # die Belegung += d landet NUR in kapAbzug, NICHT in abwAbzug
    assert "kapAbzug[s.monteur][iso]=(kapAbzug[s.monteur][iso]||0)+d;" in index_html
    assert "abwAbzug[s.monteur][iso]=(abwAbzug[s.monteur][iso]||0)+d;" not in index_html, "Belegung darf NICHT in abwAbzug"
    # cfg reicht abwAbzug durch
    assert "kapAbzug:kapAbzug, abwAbzug:abwAbzug," in index_html


def test_handwand_nutzt_abwabz(index_html):
    """Die Zelle/Hand-Wand rechnet data-norm + frei gegen abwAbz (nicht kapAbzug) -> Belegung nur einmal."""
    assert "var _abwAbz=((((_built.cfg||{}).abwAbzug)||{})[m.id]||{})[t.key];" in index_html
    assert "var _normFrei=_dispoNormFrei(t.normMin,_abwAbz,usedMin);" in index_html
    assert "'data-norm':(t.normMin-_abwAbz)" in index_html
    # der alte Doppel-Abzug in der Anzeige ist weg
    assert "'data-norm':(t.normMin-_abz)" not in index_html


def test_dispoplan_kern_byte_identisch(index_html):
    """GRENZE: der _dispoPlan-Greedy/Score-Kern nutzt weiter cfg.kapAbzug (inkl. Belegung) — unveraendert."""
    # der Kern liest kapAbzug byte-gleich
    assert "var abz=(kapAbzug[mon[mi].id]&&kapAbzug[mon[mi].id][tage[ti].key])||0;" in index_html
    assert "kap[mon[mi].id][tage[ti].key]=_dispoKapazitaet(tage[ti].normMin,abz);" in index_html
    # _hard/_kapReal der Zelle bleiben auf kapAbzug (voll-belegt = harte Wand korrekt)
    assert "var _kapReal=_dispoKapazitaet(t.normMin,_abz);" in index_html
    assert "var _hard=((t.normMin-_abz)<=0);" in index_html
