# -*- coding: utf-8 -*-
"""v3.9.791 — Navigation-Neubau ETAPPE 1 (Fundament, Sebastian: Neubau etappiert).

Hash-erhaltender History-Core _navMerge/_navPush/_navReplace, State-Schema {kat,sub,projId,projView,detailId?}.
KEINE Verhaltensaenderung (App laeuft exakt wie v790): nur Infrastruktur, alt-Pfade + der EINE popstate-Handler
unveraendert. HARTES Kiosk-Tabu (v784): _navPush/_navReplace schreiben via 2-ARG pushState/replaceState -> nie
ein url-Argument -> location.hash (Kiosk-Pin) bleibt erhalten.
"""
import hashlib
import subprocess


def test_navmerge_pure(index_html, node_exe, tmp_path):
    """_navMerge(prev,patch): patch gewinnt, non-object-sicher, mischt in den bestehenden State."""
    i = index_html.index("function _navMerge(")
    j = index_html.index("\n}", i) + 2
    js = index_html[i:j] + u"""
function ok(c,n){ if(!c){ console.error('FAIL '+n); process.exit(1);} }
ok(JSON.stringify(_navMerge({kat:2},{sub:'zulagen'}))===JSON.stringify({kat:2,sub:'zulagen'}),'merge fuegt hinzu');
ok(_navMerge({kat:2,sub:'a'},{sub:'b'}).sub==='b','patch gewinnt');
ok(_navMerge({kat:2},{sub:'x'}).kat===2,'bestehende Keys bleiben');
ok(JSON.stringify(_navMerge(null,{kat:1}))===JSON.stringify({kat:1}),'prev null -> patch');
ok(JSON.stringify(_navMerge({kat:1},null))===JSON.stringify({kat:1}),'patch null -> prev');
ok(JSON.stringify(_navMerge(null,null))==='{}','beide null -> {}');
// keine Referenz-Mutation von prev
var _p={kat:1};_navMerge(_p,{sub:'z'});ok(_p.sub===undefined,'prev nicht mutiert');
console.log('OK');
"""
    f = tmp_path / "nav791.js"; f.write_text(js, encoding="utf-8")
    r = subprocess.run([node_exe, str(f)], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")
    assert "OK" in r.stdout


def test_navpush_hash_erhaltend(index_html):
    """_navPush/_navReplace nutzen 2-ARG pushState/replaceState (kein url-Argument) -> location.hash bleibt."""
    assert "function _navPush(patch){try{history.pushState(_navMerge(history.state,patch),'');}" in index_html
    assert "function _navReplace(patch){try{history.replaceState(_navMerge(history.state,patch),'');}" in index_html
    assert "window._navMerge=_navMerge;window._navPush=_navPush;window._navReplace=_navReplace;" in index_html


def test_genau_ein_popstate_handler(index_html):
    """Es gibt GENAU EINEN popstate-Handler (kein zweites Navigations-System danebengestellt)."""
    assert index_html.count("addEventListener('popstate'") == 1


def test_keine_verhaltensaenderung_altpfade(index_html):
    """Etappe 1 aendert die bestehenden Push-Pfade NICHT (Regressionsschutz)."""
    # die alten kat/Projekt-Pushes stehen unveraendert
    assert "history.pushState({kat,projId:openP.id,projView:'dashboard'},'');" in index_html
    assert "if(curUser)history.replaceState({kat},'');" in index_html
    # noch KEIN View ruft _navPush (Umstellung erst Etappe 2+) -> nur die Definition + window-Export existieren
    assert index_html.count("_navPush(") == 1  # nur die Funktionsdefinition selbst (window._navPush=_navPush zaehlt nicht als Call)


def test_kiosk_byte_identisch(index_html):
    """HARTES Kiosk-Tabu (v784): _kioskScreenPick byte-identisch (md5-Pin) — der History-Core fasst den hash nicht an."""
    i = index_html.index("function _kioskScreenPick(")
    j = index_html.index("\n}", i) + 2
    md5 = hashlib.md5(index_html[i:j].encode("utf-8")).hexdigest()
    assert md5 == "0b07d04383a1ce5d2190ae0e969fc4b2", "_kioskScreenPick veraendert! md5=" + md5
