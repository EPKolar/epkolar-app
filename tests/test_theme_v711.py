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
// v3.9.1016 GF-Entscheidung: nur die App-Wahl zaehlt, ohne Wahl hell.
eq(resolveTheme('light', true),  false, 'light schlaegt OS-dunkel');
eq(resolveTheme('dark',  false), true,  'dark schlaegt OS-hell');
eq(resolveTheme('system',true),  false, 'altes system = hell, OS egal');
eq(resolveTheme('system',false), false, 'altes system = hell');
eq(resolveTheme(null,    true),  false, 'fehlend = hell, auch bei OS-dunkel');
eq(resolveTheme(undefined,false),false, 'fehlend = hell');
console.log('OK');
"""
    f = tmp_path / "theme.js"
    f.write_text(js, encoding="utf-8")
    r = subprocess.run([node_exe, str(f)], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")
    assert "OK" in r.stdout


def test_global_key_and_default_system(index_html):
    # GLOBALER Key epk_theme (nicht mehr per-user epk_theme_<username> in der Aufloesung)
    assert 'resolveTheme(localStorage.getItem("epk_theme"))' in index_html
    assert 'localStorage.setItem("epk_theme",mode)' in index_html


def test_hard_choice_ignores_matchmedia(index_html):
    # v3.9.1016 GF: die App liest und beobachtet die OS-Einstellung GAR NICHT mehr.
    # Nur Code zaehlt (Kommentare duerfen den alten Weg erklaeren).
    import re as _re
    code = _re.sub(r"/\*.*?\*/", "", index_html, flags=_re.S)
    assert "prefers-color-scheme" not in code, "die App liest wieder die OS-Einstellung"
    assert "_systemDark" not in code
    # Umkehrprobe: der alte Lauscher wuerde erkannt
    alt = code + 'const mq=window.matchMedia("(prefers-color-scheme: dark)");'
    assert "prefers-color-scheme" in alt


def test_colorscheme_follows_app(index_html):
    # native Inputs/Scrollbars folgen der App-Wahl (color-scheme am <html>).
    # 14.11.2026: `only` dazu - verbietet dem Browser das eigenmaechtige Umfaerben
    # (Samsung Internet/Chrome Dunkelmodus fuer Webseiten). Die Eigenschaft bleibt:
    # das Schema folgt der App-Wahl.
    assert 'document.documentElement.style.colorScheme=dark?"only dark":"only light"' in index_html
