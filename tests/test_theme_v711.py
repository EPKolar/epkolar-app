# -*- coding: utf-8 -*-
"""v3.9.711 — Theme-Dreiwert: die IN-APP-Wahl schlaegt IMMER die OS-Einstellung.

epk_theme {light,dark,system} (Default system = kein Bruch). resolveTheme pure, via Node ausgefuehrt.
"""
import re
import subprocess


def test_resolvetheme_behavior_executed(index_html, node_exe, tmp_path):
    m = re.search(r"function resolveTheme\(.*?\n\}", index_html, re.S)
    assert m, "resolveTheme nicht gefunden"
    js = m.group(0) + u"""
function eq(g,e,n){ if(g!==e){ console.error('FAIL '+n+': '+g+' != '+e); process.exit(1);} }
eq(resolveTheme('light', true),  false, 'light schlaegt OS-dunkel');
eq(resolveTheme('dark',  false), true,  'dark schlaegt OS-hell');
eq(resolveTheme('system',true),  true,  'system folgt OS (dunkel)');
eq(resolveTheme('system',false), false, 'system folgt OS (hell)');
eq(resolveTheme(null,    true),  true,  'fehlend = system (dunkel)');
eq(resolveTheme(undefined,false),false, 'fehlend = system (hell)');
console.log('OK');
"""
    f = tmp_path / "theme.js"
    f.write_text(js, encoding="utf-8")
    r = subprocess.run([node_exe, str(f)], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")
    assert "OK" in r.stdout


def test_global_key_and_default_system(index_html):
    # GLOBALER Key epk_theme (nicht mehr per-user epk_theme_<username> in der Aufloesung)
    assert 'resolveTheme(localStorage.getItem("epk_theme"),_systemDark())' in index_html
    assert 'localStorage.setItem("epk_theme",mode)' in index_html


def test_hard_choice_ignores_matchmedia(index_html):
    # Der OS-Wechsel-Listener uebernimmt NUR bei 'system' — harte Wahl ignoriert matchMedia.
    seg = index_html.split('mq=window.matchMedia("(prefers-color-scheme: dark)")', 1)[1][:400]
    assert 'if(v==="light"||v==="dark")return;' in seg


def test_colorscheme_follows_app(index_html):
    # native Inputs/Scrollbars folgen der App-Wahl (color-scheme am <html>).
    assert 'document.documentElement.style.colorScheme=dark?"dark":"light"' in index_html
