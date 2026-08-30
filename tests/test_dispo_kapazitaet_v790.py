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


def test_handwand_pins_auf_dem_laufenden_code(index_html, node_exe, tmp_path):
    """Die 3 Freigabe-Zahlen-Pins + Hart-Regel + kein Doppel-Abzug - jetzt an dem
    Code, der wirklich rechnet.

    v3.9.899 NACHGEZOGEN, nicht abgeschwaecht: bis hierher standen sieben ok()
    auf _dispoNormFrei. Diese Funktion hatte genau EINEN Aufrufer - eine Zuweisung
    ohne Leser - und wurde von der Hand-Wand nie gerufen, obwohl ihr Kopf genau das
    behauptete. Der Drop rechnet frei=(norm-used)+eigen im Drag-Handler und reicht
    es an _dispoDropOk; dieselbe Groesse bildet _dispoAblehnGrund fuer den Toast.
    Beide sind pur und node-testbar - die Pins wandern also auf sie um, mit
    denselben Freigabe-Zahlen. Von den alten sieben Zusicherungen sicherte genau
    EINE eine Eigenschaft des laufenden Codes (die _dispoDropOk-Zeile); sie steht
    unveraendert wieder da, mit 150 statt der Variablen f1.
    """
    puf = re.search(r"var PUFFER_JE_STOPP=\d+", index_html).group(0)
    js = puf + ";\n" + _pure(index_html, "_dispoDropOk") + "\n" + _pure(index_html, "_dispoAblehnGrund") + u"""
function ok(c,n){ if(!c){ console.error('FAIL '+n); process.exit(1);} }
// Pin 1 (Freigabe): Do norm 510 (8,5h), Abwesenheit 0, Belegung 360 (6h) -> frei 150 (2,5h)
ok(_dispoDropOk('a','a',false,150,90)===true,'1,5h(90)+Puffer passt in 150');
ok(_dispoAblehnGrund('',510,360,90,0)===null,'510-360=150 frei -> kein Ablehn-Grund');
// Pin 2: Fr norm 270 (4,5h), Belegung 180 -> frei 90; 1,5h+Puffer passt NICHT
ok(_dispoDropOk('a','a',false,90,90)===false,'90+Puffer passt nicht in 90');
ok(String(_dispoAblehnGrund('',270,180,90,0)).indexOf('1,5h frei')>0,'Ablehn-Text beziffert 1,5h frei');
// Pin 3: Halbtag ZA -> data-norm ist 510-240=270, belegt 120 -> frei 150
ok(_dispoAblehnGrund('',270,120,90,0)===null,'Halbtag 270-120=150, 1,5h passt');
// KEIN Doppel-Abzug: die Belegung geht genau EINMAL ab. Gegenprobe mit dem alten
// Fehler von v790: (510-360)-360 = -210 haette denselben Drop abgelehnt.
ok(_dispoDropOk('a','a',false,-210,90)===false,'alter Doppel-Abzug haette abgelehnt');
// eigen: liegt der gezogene Chip schon auf dem Tag, zaehlt seine Dauer nicht doppelt.
// Gleicher Tag, gleicher Chip - nur eigen entscheidet ueber passt / passt nicht.
ok(_dispoAblehnGrund('',510,420,90,90)===null,'eigene Dauer wird herausgerechnet');
ok(_dispoAblehnGrund('',510,420,90,0)!==null,'ohne eigen waere derselbe Tag zu voll');
// harte Waende der Hand
ok(_dispoDropOk('a','a',true,510,60)===false,'hardBlock schlaegt jede Kapazitaet');
ok(_dispoDropOk('a','b',false,510,60)===false,'fremde Monteurszeile');
ok(String(_dispoAblehnGrund('Urlaub',510,0,60,0))==='Urlaub','hardLabel dominiert');
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
    #
    # v3.9.899 NACHGEZOGEN - nicht abgeschwaecht: die Zeile
    #     assert "var _normFrei=_dispoNormFrei(t.normMin,_abwAbz,usedMin);" in index_html
    # ist ersatzlos entfallen. Sie sicherte die blosse EXISTENZ einer Zuweisung mit
    # NULL Lesern - derselbe Fall wie _kapReal in v3.9.896, und derselbe Schaden: sie
    # hat den Ausbau toten Codes verhindert, ohne eine Eigenschaft zu sichern.
    # Die Aussage dieses Tests (die Zelle reicht abwAbz durch, nicht kapAbzug) haengt
    # an den data-Attributen darunter - und die liest der Drag-Handler wirklich.
    assert "'data-norm':(t.normMin-_abwAbz)" in index_html
    assert "'data-used':usedMin" in index_html, (
        "Ohne data-used hat der Drag-Handler keine Belegung - frei=(norm-used) "
        "wuerde NaN."
    )
    # v3.9.916 NACHGEZOGEN - nicht abgeschwaecht: hier stand
    #     assert index_html.count("frei=(norm-used)+eigen;") == 2
    # Der Zaehler mass die SCHREIBWEISE von ZWEI der DREI Stellen, die diese
    # Groesse rechnen. Die dritte steht in _dispoAblehnGrund (:5576) und ist
    # anders geschrieben, kommt in der Zaehlung also gar nicht vor. Belegt:
    # verstellt man NUR sie, bleibt dieser Riegel gruen - der Benutzer bekaeme
    # dann eine falsche Restzeit im Ablehn-Text, und nichts haette angeschlagen.
    #
    # Die Aussage bleibt und wird jetzt AUSGEFUEHRT statt gezaehlt:
    # tests/test_dispo_handwand_eine_rechnung_v916.py schneidet alle DREI
    # Ausdruecke aus index.html und vergleicht ueber die erreichbare Domaene
    # Entscheidung UND bezifferte Restzeit (227.700 Faelle, 0 Abweichungen),
    # mit einer Mutations-Batterie als Gegenprobe.
    # der alte Doppel-Abzug in der Anzeige ist weg
    assert "'data-norm':(t.normMin-_abz)" not in index_html


def test_dispoplan_kern_byte_identisch(index_html):
    """GRENZE: der _dispoPlan-Greedy/Score-Kern nutzt weiter cfg.kapAbzug (inkl. Belegung) — unveraendert."""
    # der Kern liest kapAbzug byte-gleich
    assert "var abz=(kapAbzug[mon[mi].id]&&kapAbzug[mon[mi].id][tage[ti].key])||0;" in index_html
    assert "kap[mon[mi].id][tage[ti].key]=_dispoKapazitaet(tage[ti].normMin,abz);" in index_html
    # _hard der Zelle bleibt auf kapAbzug (voll-belegt = harte Wand korrekt)
    #
    # v3.9.896 NACHGEZOGEN - nicht abgeschwaecht: die Zeile
    #     assert "var _kapReal=_dispoKapazitaet(t.normMin,_abz);" in index_html
    # ist ersatzlos entfallen. _kapReal war eine Zuweisung mit NULL Lesern - dieser
    # Riegel sicherte also keine Eigenschaft, sondern die blosse EXISTENZ toten
    # Codes, und hat damit dessen Ausbau verhindert. Die eigentliche Aussage des
    # Tests ("die harte Wand der Zelle rechnet auf kapAbzug") haengt an der Zeile
    # darunter und wird unveraendert geprueft.
    assert "var _hard=((t.normMin-_abz)<=0);" in index_html, (
        "Die harte Wand der Zelle rechnet nicht mehr auf kapAbzug - ein voll "
        "belegter Tag waere dann nicht mehr als harte Wand erkennbar."
    )
