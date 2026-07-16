# -*- coding: utf-8 -*-
"""v3.9.757 — #31a Monteur-Guard + #31b Pull-Echo-Schutz (Monteur-Feld, Abrechnungs-Lebensader).

#31a: updAs validiert eine `monteur`-Zuweisung gegen den public.workers-Mirror `monteure` (Array.some
id-Match), NIE per ID-Muster (Random-IDs = Buerger erster Klasse). Leer-Guard (nur bei geladenem Mirror)
verhindert Cold-Boot-False-Reject. Unbekannte ID -> verworfen + Toast, nie nach OFFA gepusht. users/Auth TABU.

#31b: der Pull ueberschreibt `monteur` NUR wenn der lokale Monteur uebertragbar ist
(_dispoMonteurUebertragbar: leer / hat Juprowa-Code). Ein lokal zugewiesener CODE-LOSER Monteur
(Barger/Cracana — nie nach OFFA pushbar) wird feldweise + dauerhaft vor dem stale Cloud-Echo geschuetzt.
"""
import re
import subprocess


# ---------------------------------------------------------------- static wiring

def test_31a_guard_gegen_workers_mirror(index_html):
    start = index_html.index("const updAs=")
    seg = index_html[start:start + 1600]
    assert "#31a Monteur-Guard" in seg, "31a-Guard-Kommentar fehlt in updAs"
    # Membership-Check gegen `monteure` (der Mirror), per some(id-Match) — NICHT per Muster.
    assert "monteure.some(function(m){return m&&m.id===_u.monteur;})" in seg, \
        "31a prueft nicht per Array.some(id===) gegen den monteure-Mirror"
    # Leer-Guard gegen Cold-Boot-False-Reject.
    assert "monteure.length>0" in seg, "31a fehlt der Leer-Guard (monteure.length>0)"
    # KEIN ID-Muster (kein Regex/startsWith auf die monteur-ID im Guard).
    guard = seg[seg.index("#31a Monteur-Guard"):seg.index("#31a Monteur-Guard") + 500]
    assert ".test(" not in guard and "startsWith" not in guard and "/^" not in guard, \
        "31a nutzt ein ID-Muster statt der workers-Tabelle"


def test_31b_pull_echo_schutz(index_html):
    # Die monteur-Pull-Ueberschreibung ist an _dispoMonteurUebertragbar(existing.monteur) gebunden.
    assert "mapped.monteur!==existing.monteur&&_dispoMonteurUebertragbar(existing.monteur))upd.monteur=mapped.monteur;" in index_html, \
        "31b: Pull-monteur-Overwrite nicht an _dispoMonteurUebertragbar(existing.monteur) gebunden"
    assert "#31b Pull-Echo-Schutz" in index_html, "31b-Kommentar fehlt"


def test_uebertragbar_fn_unveraendert(index_html):
    # Der Guard baut auf _dispoMonteurUebertragbar (kein Monteur -> true; mit Code -> true; ohne Code -> false).
    assert "function _dispoMonteurUebertragbar(monteurId){return !monteurId||!!_juprowaWorkerToCode(monteurId);}" in index_html, \
        "_dispoMonteurUebertragbar veraendert/fehlt — 31b-Semantik nicht garantiert"


# ---------------------------------------------------------------- node-eval

_OK = u"""
function ok(c,n){ if(!c){ console.error('FAIL '+n); process.exit(1);} }
"""


def _run(node_exe, tmp_path, js, name):
    f = tmp_path / name
    f.write_text(js, encoding="utf-8")
    r = subprocess.run([node_exe, str(f)], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")
    assert "OK" in r.stdout, (r.stdout or "") + (r.stderr or "")


def test_31a_membership_predikat(index_html, node_exe, tmp_path):
    """Der 31a-Guard verwirft NUR eine ID, die im geladenen Mirror fehlt; leerer Mirror -> nie verwerfen."""
    js = _OK + u"""
// exakt das Praedikat aus updAs (Verwerfen wenn geladen UND nicht enthalten):
function verwirft(monteurId, monteure){
  return !!(monteurId && Array.isArray(monteure) && monteure.length>0 &&
    !monteure.some(function(m){return m&&m.id===monteurId;}));
}
var mirror=[{id:'w2'},{id:'mpxpwdhrht1b'}];  // Random-IDs sind Buerger erster Klasse
ok(verwirft('w2',mirror)===false,'bekannte ID (w2) bleibt');
ok(verwirft('mpxpwdhrht1b',mirror)===false,'bekannte Random-ID bleibt (kein ID-Muster)');
ok(verwirft('BOGUS_ID',mirror)===true,'unbekannte ID wird verworfen');
ok(verwirft('w2',[])===false,'leerer Mirror -> nie verwerfen (Cold-Boot-Schutz)');
ok(verwirft('',mirror)===false,'leere Zuweisung -> kein Verwerfen');
console.log('OK');
"""
    _run(node_exe, tmp_path, js, "guard31a_757.js")


def test_31b_pull_echo_predikat(index_html, node_exe, tmp_path):
    """Der 31b-Overwrite passiert NUR fuer uebertragbare (leer/hat-Code) lokale Monteure."""
    js = _OK + u"""
// _dispoMonteurUebertragbar-Semantik: kein Monteur -> true; mit Code -> true; ohne Code -> false.
var CODE={ 'w6':'P011' };  // nur w6 hat einen Juprowa-Code
function uebertragbar(id){ return !id || !!CODE[id]; }
// Pull-Overwrite-Bedingung aus _juprowaSync (isPending ausgeklammert = false hier):
function overwrite(existingMonteur, mappedMonteur){
  return !!(mappedMonteur && mappedMonteur!==existingMonteur && uebertragbar(existingMonteur));
}
ok(overwrite('', 'w6')===true,'leerer lokaler Monteur -> Cloud darf setzen');
ok(overwrite('w6','w2')===true,'lokaler Monteur MIT Code -> roundtrip-safe Overwrite ok');
ok(overwrite('w2','w6')===false,'lokaler CODE-LOSER Monteur (w2) -> NICHT vom Cloud-Echo ueberschrieben');
ok(overwrite('w2','w2')===false,'gleicher Wert -> kein Overwrite');
console.log('OK');
"""
    _run(node_exe, tmp_path, js, "guard31b_757.js")
