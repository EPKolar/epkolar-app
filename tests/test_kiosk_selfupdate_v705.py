"""v3.9.705 Kiosk Self-Update — strukturelle Verifikation.

Der Samsung-TV-Kiosk hing wiederholt auf alten Bundles. Fix dreiteilig:
  1. sw.js install ruft self.skipWaiting() (activate hatte clients.claim() schon)
  2. Versions-Poller in index.html (fetch index.html?_v=<ts>, cache:'no-store', RELATIV)
  3. Mismatch -> lager_display stiller Auto-Reload (Loop-Guard), sonst Update-Banner

Die Loop-Guard-LOGIK selbst ist browser-bewiesen (5 Branches, Report 16.07.);
hier werden die strukturellen Eigenschaften gegen stille Regression gepinnt.
"""


def test_sw_skip_waiting_in_install(sw_js):
    # skipWaiting() muss im install-Handler stehen (sonst haengt der neue SW ewig "waiting")
    install = sw_js.split("addEventListener('install'", 1)[1].split("addEventListener('activate'", 1)[0]
    assert "self.skipWaiting()" in install, "self.skipWaiting() fehlt im install-Handler"


def test_sw_clients_claim_in_activate(sw_js):
    # clients.claim() bleibt im activate-Handler (controllerchange feuert -> Kiosk reload)
    activate = sw_js.split("addEventListener('activate'", 1)[1].split("addEventListener('fetch'", 1)[0]
    assert "self.clients.claim()" in activate, "clients.claim() fehlt im activate-Handler"


def test_sw_version_poll_not_cached(sw_js):
    # Der Versions-Poll (index.html?_v=) darf nie durch den SW gecacht werden (Cache-Bloat)
    assert "url.includes('index.html?_v=')" in sw_js


def test_version_poller_present(index_html):
    # Poller holt index.html netzfrisch, RELATIVER Pfad (GitHub-Pages-Unterpfad), no-store
    assert "fetch('index.html?_v='+Date.now(),{cache:'no-store'})" in index_html
    # KEIN absoluter Pfad '/index.html' (der wuerde auf GitHub Pages ins Root zeigen)
    assert "fetch('/index.html?_v=" not in index_html
    # registration.update() im selben Takt
    assert "swReg.current.update()" in index_html
    # APP_VERSION per Regex extrahieren + vergleichen
    assert "_txt.match(" in index_html and "APP_VERSION" in index_html


def test_poll_intervals(index_html):
    # 10 min lager_display, sonst 15 min; einmalig 30 s nach Start
    assert "setInterval(_check,_isLD?600000:900000)" in index_html
    assert "setTimeout(_check,30000)" in index_html
    # zusaetzlich bei window 'focus'
    assert "window.addEventListener('focus',_onFocus)" in index_html


def test_mismatch_behavior_role_split(index_html):
    # lager_display -> stiller Reload; alle anderen -> Banner (setSwUpdate)
    assert "if(_isLD){window._kioskSilentReload(_serverVer);}" in index_html
    assert "else{setSwUpdate(true);}" in index_html


def test_loop_guard_helpers(index_html):
    # Guard + stiller Reload existieren; Guard traegt 20s-Rapid- und 10min-Versions-Sperre
    assert "window._kioskReloadGuard=function(zielVer)" in index_html
    assert "window._kioskSilentReload=function(zielVer)" in index_html
    assert "(now-g.ts)<20000" in index_html      # Rapid-Sperre gegen Doppelfire
    assert "(now-g.ts)<600000" in index_html      # 10-min-Sperre gleiche Zielversion
    # stiller Reload nutzt die bestehende Teardown-Kette (unregister + caches + reload)
    assert "window._forceCacheClear(true)" in index_html


def test_silent_reload_only_via_guard(index_html):
    # _kioskSilentReload reloadet NUR wenn der Guard es erlaubt
    seg = index_html.split("window._kioskSilentReload=function(zielVer)", 1)[1][:400]
    assert "if(!window._kioskReloadGuard(zielVer))return;" in seg
