"""v3.9.646 Kiosk-Auto-Update — strukturelle Verifikation.

Nur Kiosk-Pfade (?screen=planung/monteure/stempel) reloaden bei SW-Wechsel;
Haupt-App-Update-Flow (doSwUpdate/Banner) bleibt unveraendert.
"""
import re


def test_kiosk_path_gate(index_html):
    # Gate auf die drei Kiosk-Screens
    assert "_isKioskPath=_kScreen==='planung'||_kScreen==='monteure'||_kScreen==='stempel'" in index_html


def test_controllerchange_reload(index_html):
    # controllerchange -> location.reload(); Handler wird NUR im _isKioskPath-Zweig registriert
    assert 'navigator.serviceWorker.addEventListener("controllerchange",_kioskCtrlHandler)' in index_html
    assert '_kioskCtrlHandler=function(){if(_kioskRefreshing)return;_kioskRefreshing=true;try{location.reload();' in index_html
    # der Handler-Setup steht im if(_isKioskPath)-Block
    m = re.search(r"if\(_isKioskPath\)\{\s*var _kioskRefreshing=false;", index_html)
    assert m, "controllerchange-Setup nicht im _isKioskPath-Gate"


def test_hourly_skip_waiting(index_html):
    # stuendlich SKIP_WAITING an reg.waiting
    assert 'if(_isKioskPath){_kioskWaitTimer=setInterval(' in index_html
    assert 'reg.waiting.postMessage({type:"SKIP_WAITING"})' in index_html


def test_main_app_flow_untouched(index_html):
    # Der bestehende User-Update-Pfad (doSwUpdate) existiert weiterhin
    assert "const doSwUpdate=async()=>" in index_html


def test_cleanup_present(index_html):
    assert 'removeEventListener("controllerchange",_kioskCtrlHandler)' in index_html
    assert "clearInterval(_kioskWaitTimer)" in index_html
