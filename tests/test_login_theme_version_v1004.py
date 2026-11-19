# -*- coding: utf-8 -*-
"""v3.9.1004 (Frage 34/35): Hell/Dunkel-Umschalter + Versionsnummer auf der Anmeldemaske.

Wer mit vollem Speicher dunkel feststeckt, sieht zuerst die ANMELDEMASKE. Der in
v3.9.1003 reparierte Schalter lag nur im eingeloggten Zustand. Die Maske bekommt
DENSELBEN setThemeMode (als Prop aus App), keinen zweiten Mechanismus.
"""
import hashlib
import json
import pathlib
import shutil
import subprocess

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = (ROOT / "index.html").read_text(encoding="utf-8").replace("\r\n", "\n")


def _login_screen():
    i = SRC.find("function LoginScreen(")
    assert i > 0, "LoginScreen nicht gefunden"
    j = SRC.find("\nfunction ", i + 10)
    return SRC[i:j]


def _set_theme_mode():
    a = SRC.find("const setThemeMode=(mode)=>{")
    assert a > 0, "setThemeMode nicht gefunden"
    b = SRC.find("\n  };", a)
    return SRC[a:b + 5]


# 1. Umschalter existiert auf der Maske und nutzt DEN setThemeMode aus App.
def test_umschalter_auf_der_anmeldemaske_ruft_setThemeMode():
    ls = _login_screen()
    assert "function LoginScreen({onLogin,onPortal,projects,isDark,setThemeMode})" in ls
    assert "'data-login-theme'" in ls
    assert "setThemeMode(o[0])" in ls
    assert '["light",' in ls and '["dark",' in ls
    assert "minHeight:44" in ls and "minWidth:44" in ls
    # Kein zweiter Mechanismus in der Maske: kein eigenes Speichern/Anwenden.
    assert 'localStorage.setItem("epk_theme"' not in ls
    assert "applyTheme(" not in ls
    # App reicht genau diese Funktion herein.
    assert "projects: projects, isDark: isDark, setThemeMode: setThemeMode} ));" in SRC


def test_setThemeMode_reihenfolge_anzeige_vor_speicher_getrennte_catches():
    f = _set_theme_mode()
    anz = f.find("applyTheme(d)")
    spe = f.find('localStorage.setItem("epk_theme",mode)')
    assert 0 < anz < spe, "Anzeige muss VOR dem Speichern laufen (v3.9.1003)"
    zwischen = f[anz:spe]
    assert "catch" in zwischen and "try{" in zwischen, "Anzeige und Speicher brauchen getrennte try/catch"


# 2. Speicher wirft -> Anzeige wechselt trotzdem (Pin gegen den v1003-Rueckfall), am echten Code ausgefuehrt.
@pytest.mark.skipif(shutil.which("node") is None, reason="node fehlt")
def test_speicher_fehlschlag_auf_der_maske_wechselt_trotzdem():
    js = (
        "var applied=[],dark=[],toasts=[];"
        "var window={__toast:function(m,k){toasts.push(k);}};"
        "var localStorage={setItem:function(){throw new Error('QuotaExceeded');}};"
        "function resolveTheme(m,s){return m==='dark'?true:m==='light'?false:s;}"
        "function _systemDark(){return true;}"
        "function setIsDark(d){dark.push(d);}"
        "function setThemeWahl(m){}"
        "function applyTheme(d){applied.push(d);}"
        "var _themeToast=function(){toasts.push('ok');};"
        + _set_theme_mode()
        + "setThemeMode('light');"
        "console.log(JSON.stringify({applied:applied,dark:dark,toasts:toasts}));"
    )
    out = subprocess.run(["node", "-e", js], capture_output=True, text=True, timeout=30)
    assert out.returncode == 0, out.stderr
    r = json.loads(out.stdout.strip().splitlines()[-1])
    assert r["applied"] == [False], r
    assert r["dark"] == [False], r
    assert r["toasts"] == ["warn"], "Bei Speicher-Fehlschlag muss der Hinweis kommen, nicht der Erfolgs-Toast"


# 3. Versionsnummer auf der Maske = dieselbe Konstante wie App-Info.
def test_version_auf_der_maske_ist_APP_VERSION():
    ls = _login_screen()
    assert "'data-login-version'" in ls
    i = ls.find("'data-login-version'")
    assert "APP_VERSION)" in ls[i:i + 300], "Maske muss die Konstante zeigen, keine abgeschriebene Zahl"
    assert "opacity:.6" not in ls[i:i + 300], "Version war mit Deckkraft 0,6 kaum lesbar"
    # Dieselbe Konstante speist Einstellungen -> App-Info.
    assert SRC.count("const APP_VERSION=") == 1


# 4. Auth-Pfad strukturell unveraendert (Pin, gemessen gegen v3.9.1003).
def test_auth_pfad_unveraendert():
    # v3.9.1056 Auth-Haertung: Summe BEWUSST neu gesetzt - die Anmeldelogik der Maske wurde in diesem Auftrag
    # geaendert (neutrale Meldung, Offline-Weg bei schwachem Netz, ehrliche Passwort-Hilfe). Der Riegel bleibt:
    # jede weitere Aenderung ausserhalb eines Auth-Auftrags faellt hier wieder auf.
    ls = _login_screen()
    k = ls.find("){") + 2
    j = ls.find("  return (")
    assert hashlib.sha256(ls[k:j].encode("utf-8")).hexdigest() == \
        "8b5c9c3bdf6002c657dc94078536168e6bc3b3ac3acd735c3ee0d2a190144338", \
        "Login-Logik (Zustand, Anmeldefunktion) hat sich geaendert - Auth war fuer v3.9.1004 tabu"
    a = SRC.find("React.createElement(LoginScreen, { onLogin:")
    b = SRC.find(", onPortal:", a)
    assert hashlib.sha256(SRC[a:b].encode("utf-8")).hexdigest() == \
        "73a570368f0cdc1ec262cba3e2472d2d785fd2f311fd4a6a854c94caa9a5b3ce", \
        "onLogin-Handler in App hat sich geaendert - Auth war fuer v3.9.1004 tabu"
