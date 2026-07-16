# -*- coding: utf-8 -*-
"""v3.9.721 — Theme-Hotfix Mobil (Sebastian, live gemeldet): Dark am Handy nicht fixierbar.

Diagnose: (a) toggleTheme ohne Re-Entry-Schutz -> Touch-Ghost-Click (Doppelfeuer je Tap) sprang 2
Schritte und uebersprang Dunkel systematisch (Hell->[dark->system]=Auto); (b) Auto und Dunkel am
OS-dunklen Handy optisch ununterscheidbar, keine Rueckmeldung.

Fix: (1) Re-Entry-Guard 350ms in toggleTheme (PURE _themeTapAllowed). (2) Segmented Control
[Hell|Dunkel|Auto] in den Einstellungen -> setzt den Modus DIREKT (kein Verzaehlen). (3) Toast bei
jedem Wechsel. Zyklus-Reihenfolge des Header-Buttons unveraendert gepinnt.
"""
import subprocess


def _guard_block(index_html):
    start = index_html.index("var THEME_TAP_GUARD_MS=350;")
    end = index_html.index("if(typeof window!=='undefined'){window.resolveTheme", start)
    return index_html[start:end]


def test_theme_tap_allowed_350_fenster(index_html, node_exe, tmp_path):
    js = _guard_block(index_html) + u"""
function ok(c,n){ if(!c){ console.error('FAIL '+n); process.exit(1);} }
ok(_themeTapAllowed(1000,700)===false,'300ms < 350 -> blockiert (Ghost-Click)');
ok(_themeTapAllowed(1000,650)===true,'genau 350ms -> erlaubt');
ok(_themeTapAllowed(1000,500)===true,'500ms -> erlaubt');
ok(_themeTapAllowed(1000,990)===false,'10ms -> blockiert');
console.log('OK');
"""
    f = tmp_path / "themeguard.js"
    f.write_text(js, encoding="utf-8")
    r = subprocess.run([node_exe, str(f)], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")
    assert "OK" in r.stdout


def test_guard_exportiert(index_html):
    assert "window._themeTapAllowed=_themeTapAllowed" in index_html


def test_toggle_hat_reentry_guard(index_html):
    assert "_themeTapAllowed(now,_themeLastTapMs)" in index_html


def test_zyklus_reihenfolge_unveraendert(index_html):
    # Header-Button bleibt Zyklus Hell->Dunkel->Auto->Hell
    assert 'cur==="light"?"dark":cur==="dark"?"system":"light"' in index_html


def test_setthememode_direkt(index_html):
    assert "const setThemeMode=(mode)=>" in index_html
    # Segmented Control ruft setThemeMode direkt (kein toggleTheme)
    assert '[["light","☀️ Hell"],["dark","🌙 Dunkel"],["system","🅰️ Auto"]]' in index_html
    assert "setThemeMode(o[0])" in index_html


def test_verbindungview_bekommt_setthememode(index_html):
    assert "function VerbindungView({ww,curUser,isDark,toggleTheme,setThemeMode})" in index_html


def test_toast_bei_wechsel(index_html):
    assert "Hell aktiv" in index_html
    assert "Dunkel aktiv — bleibt auch bei OS-Wechsel" in index_html
    assert "Auto: folgt dem Gerät" in index_html
