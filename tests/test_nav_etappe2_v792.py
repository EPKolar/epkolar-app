# -*- coding: utf-8 -*-
"""v3.9.792 — Navigation-Neubau ETAPPE 2 (Sub-Tabs in die History, Symptom 3).

Buero-Portal/ChefDashboard/AS-Sub-Tabs pushen {sub}; der EINE popstate-Handler stellt den aktiven Sub-Tab
wieder her (Init history.state.sub > localStorage > Default; gleicher Haupt-Tab via registriertem Setter).
localStorage bleibt Fallback, history gewinnt beim Zurueck. ProjectShell-Reopen restauriert projView. Kiosk
byte-identisch, hash-erhaltend. Cores unberuehrt.
"""
import hashlib
import subprocess


def test_navsubresolve_pure(index_html, node_exe, tmp_path):
    """_navSubResolve(stateSub,stored,valids,def): history gewinnt, dann localStorage, dann Default; nur gueltige."""
    i = index_html.index("function _navSubResolve(")
    j = index_html.index("\n}", i) + 2
    js = index_html[i:j] + u"""
function ok(c,n){ if(!c){ console.error('FAIL '+n); process.exit(1);} }
var V=['projekte','zulagen','stempel'];
ok(_navSubResolve('zulagen','projekte',V,'projekte')==='zulagen','history gewinnt');
ok(_navSubResolve('',    'zulagen', V,'projekte')==='zulagen','localStorage-Fallback');
ok(_navSubResolve('',    '',        V,'projekte')==='projekte','Default');
ok(_navSubResolve('kaputt','zulagen',V,'projekte')==='zulagen','ungueltige history ignoriert');
ok(_navSubResolve('zulagen','kaputt',V,'projekte')==='zulagen','history vor localStorage');
ok(_navSubResolve(undefined,undefined,V,'projekte')==='projekte','undef -> Default');
ok(_navSubResolve('form','',['liste','kalender'],'liste')==='liste','form nicht in AS-Nav-Subs -> Default');
console.log('OK');
"""
    f = tmp_path / "nav792.js"; f.write_text(js, encoding="utf-8")
    r = subprocess.run([node_exe, str(f)], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")
    assert "OK" in r.stdout


def test_buero_portal_sub_history(index_html):
    """Buero-Portal: Sub-Tab-Wechsel pusht {sub}, Init history-first, Setter registriert."""
    assert "const _bxValid=BX_TABS.map(function(x){return x[0];});" in index_html
    assert "return _navSubResolve(_st,_ls,_bxValid,'projekte');" in index_html
    assert "try{localStorage.setItem('epk_bueroexport_tab',_t);}catch(_e){}_navPush({sub:_t});" in index_html
    assert "_regSubView(_setBxTabRaw,function(t){return _bxValid.indexOf(t)>=0;});" in index_html


def test_chef_sub_history(index_html):
    """ChefDashboard: analog."""
    assert "const _cdValid=CD_TABS.map(function(x){return x[0];});" in index_html
    assert "return _navSubResolve(_st,_ls,_cdValid,'ueberblick');" in index_html
    assert "try{localStorage.setItem('epk_chefdashboard_tab',_t);}catch(_e){}_navPush({sub:_t});" in index_html
    assert "_regSubView(_setCdTabRaw,function(t){return _cdValid.indexOf(t)>=0;});" in index_html


def test_as_sub_history_nur_nav(index_html):
    """AS: nur die Nav-Subs (liste/kalender/dispo/qrscan) in die History — 'form' bleibt Detail (Etappe 3)."""
    assert 'const _asSubValid=["liste","kalender","dispo","qrscan"];' in index_html
    assert "return _navSubResolve(_st,'',_asSubValid,'liste');" in index_html
    # Nav-Bar-Klick pusht die Tab-id
    assert 'else{asStopScan();setSub(t.id);}_navPush({sub:t.id});' in index_html
    assert "_regSubView(setSub,function(t){return _asSubValid.indexOf(t)>=0;});" in index_html


def test_popstate_restore_und_projview(index_html):
    """popstate stellt sub wieder her (gleicher Haupt-Tab via Setter); ProjectShell-Reopen restauriert projView."""
    assert "else if(s.sub&&_subViewRef.current&&_subViewRef.current.valid&&_subViewRef.current.valid(s.sub)){_subViewRef.current.set(s.sub);}" in index_html
    assert "if(s.projView)pr._initView=s.projView;" in index_html
    # App reicht die Registrierung an alle 3 Views durch
    assert index_html.count("_regSubView: _regSubView, _unregSubView: _unregSubView") == 3
    assert "const _regSubView=_react.useCallback.call(void 0, (setter,isValid)=>" in index_html


def test_genau_ein_popstate_kein_doppelsystem(index_html):
    assert index_html.count("addEventListener('popstate'") == 1


def test_kiosk_byte_identisch(index_html):
    """HARTES Kiosk-Tabu (v784): _kioskScreenPick byte-identisch (md5-Pin)."""
    i = index_html.index("function _kioskScreenPick(")
    j = index_html.index("\n}", i) + 2
    md5 = hashlib.md5(index_html[i:j].encode("utf-8")).hexdigest()
    assert md5 == "0b07d04383a1ce5d2190ae0e969fc4b2", "_kioskScreenPick veraendert! md5=" + md5
