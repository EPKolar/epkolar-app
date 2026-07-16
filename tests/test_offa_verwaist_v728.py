# -*- coding: utf-8 -*-
"""v3.9.728 — Register #18a: OFFA-verwaiste Scheine erkennen (kein DDL, kein Push).

Befund (Chat-Claude): ServicePad/OFFA liefert abgeschlossene Scheine NICHT mehr im Feed -> die App
erfaehrt vom Statusende nie, ein offener Schein haengt wochenlang. Mapping ist korrekt (1:1 JUPROWA_STATUS_MAP).

Erkennung (kein Auto-Status): juprowa_id gesetzt + scheinstatus in AS_GRP_OFFEN + juprowa_sync_at aelter als
OFFA_VERWAIST_TAGE (=7) OBWOHL Pull-Laeufe stattfanden (letzter erfolgreicher Pull juenger als der sync_at des
Scheins -> er haette aktualisiert werden koennen, wurde aber nicht -> wahrscheinlich in OFFA abgeschlossen).

18b (Einzel-GET je juprowa_id): NICHT gebaut — der Client pullt nur bulk (RPC juprowa_fetch_worksheets), es
gibt kein Worksheet-Einzel-GET client-seitig; ein GET braeuchte eine neue Server-RPC (out of scope). Befund im Report.
"""
import subprocess


def _run(node_exe, tmp_path, js):
    f = tmp_path / "verwaist.js"
    f.write_text(js, encoding="utf-8")
    r = subprocess.run([node_exe, str(f)], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")
    assert "OK" in r.stdout


def _fn(index_html):
    a = index_html.index("var OFFA_VERWAIST_TAGE=")
    b = index_html.index("function _isOffaVerwaist", a)
    c = index_html.index("}", index_html.index("{", b)) + 1
    return index_html[a:c]


def test_konstante(index_html):
    assert "var OFFA_VERWAIST_TAGE=7;" in index_html


def test_verwaist_erkennung(index_html, node_exe, tmp_path):
    js = u'var AS_GRP_OFFEN=["aufgenommen","freigegeben","in_bearbeitung","aufgeschoben"];\n' + _fn(index_html) + u"""
function ok(c,n){ if(!c){ console.error('FAIL '+n); process.exit(1);} }
var DAY=864e5;
var now=1000*DAY;              // heute (ms)
var pullFrisch=now-1*DAY;      // letzter Pull gestern
var sync10=now-10*DAY;         // Schein 10 Tage nicht mehr gesynct
var sync1=now-1*DAY;           // frisch
// offen + 10 Tage alt + Pull juenger als sync -> verwaist
ok(_isOffaVerwaist({juprowa_id:'X1',scheinstatus:'in_bearbeitung',juprowa_sync_at:new Date(sync10).toISOString()},pullFrisch,now)===true,'offen+alt+Pull juenger -> verwaist');
// frisch gesynct -> nicht verwaist
ok(_isOffaVerwaist({juprowa_id:'X1',scheinstatus:'in_bearbeitung',juprowa_sync_at:new Date(sync1).toISOString()},pullFrisch,now)===false,'frisch -> nicht verwaist');
// kein juprowa_id -> nie verwaist
ok(_isOffaVerwaist({juprowa_id:'',scheinstatus:'in_bearbeitung',juprowa_sync_at:new Date(sync10).toISOString()},pullFrisch,now)===false,'ohne juprowa_id nie verwaist');
// Status nicht offen (erledigt) -> nicht verwaist
ok(_isOffaVerwaist({juprowa_id:'X1',scheinstatus:'erledigt',juprowa_sync_at:new Date(sync10).toISOString()},pullFrisch,now)===false,'nicht-offener Status nie verwaist');
// kein Pull seit dem sync (Pull aelter als sync) -> kein Rueckschluss
ok(_isOffaVerwaist({juprowa_id:'X1',scheinstatus:'in_bearbeitung',juprowa_sync_at:new Date(sync10).toISOString()},now-20*DAY,now)===false,'ohne Pull seit sync -> nicht verwaist');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_exported(index_html):
    assert "window._isOffaVerwaist=_isOffaVerwaist" in index_html


def test_pull_timestamp_gemerkt(index_html):
    # Letzter erfolgreicher Pull wird global gemerkt (localStorage/State), damit die Erkennung "Pull lief" pruefen kann.
    assert "epk_last_juprowa_pull" in index_html


def test_badge_am_schein(index_html):
    assert "in OFFA prüfen" in index_html, "Badge-Text fehlt"
