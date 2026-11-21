# -*- coding: utf-8 -*-
"""Kamera v3.9.1088 - Diagnose der Browser-Freigabe fuer das lokale Netz (Chrome Local Network Access).

Gemessen am Buero-PC (21.11.2026): /gesund am Gateway antwortet 200 "ok", Zertifikat vertraut, PC im Buero-Netz -
trotzdem stand in der Einrichtung "Kamera-Server im Büro: nicht erreichbar". Die Freigabe stand auf 'prompt', der Abruf
scheiterte SOFORT mit TypeError, ohne dass eine Frage erschien. Vorher: jeder Fehler (und jeder Ablauf nach 8 s) ->
'nicht_erreichbar' mit Zertifikats-/Netz-Hinweis.

Jetzt liefert _kamBueroPruefen {stand, berechtigung, fehler}:
  denied                      -> 'lna_gesperrt' (KEIN Abruf)
  prompt + sofortiger Fehler  -> 'lna_freigabe' (Anleitung: Website-Einstellungen / Einstellungsseite, Strg+F5)
  prompt/unbekannt + Ablauf   -> 'zeitueberschreitung' (Frage beantworten); Wartezeit 45 s statt 8 s
  nach dem Fehler denied      -> 'lna_gesperrt'
  granted + Fehler            -> 'nicht_erreichbar' (alter 3-Punkte-Hinweis)
  unbekannt + Fehler          -> 'nicht_erreichbar'
Die Einrichtung zeigt je Zustand einen eigenen Text und (zugeklappt) "Technische Details: Berechtigung · Fehler".
Echter Code aus index.html in Node mit Attrappen (navigator.permissions, fetch); Umkehrproben belegen die Zaehne.
"""
import io
import json
import os
import re
import subprocess
import tempfile

import pytest

from conftest import EPK_TEST_TIMEOUT
from test_kameras_phase1_v1055 import RENDER_PRELUDE, _block, _layout_echt
from test_kameras_einrichtung_v1060 import VERBOTEN_IN_EINRICHTUNG

ALT_PRUEFEN = (
    "async function _kamBueroPruefen(basis){\n"
    "  if(!_kamIstHttps(basis))return 'keine_adresse';\n"
    "  try{\n"
    "    var r=await fetch(basis+KAMERA_GESUND,_fT({method:'GET',cache:'no-store',credentials:'omit',referrerPolicy:'no-referrer'},8000));\n"
    "    return r.status===200?'ok':'antwort';\n"
    "  }catch(e){return 'nicht_erreichbar';}\n"
    "}\n"
)

HARNESS = r"""
const LOG = {fetch: [], ms: [], namen: []};
_fT = function (init, ms) { LOG.ms.push(ms); return init; };
function setzeNav(o) {
  const perm = o.perm;
  const nav = {userAgent: o.ua || 'Mozilla/5.0 Chrome/146.0.0.0 Safari/537.36', userAgentData: o.uad};
  if (perm !== 'keins') nav.permissions = {query: async function (q) {
    LOG.namen.push(q.name);
    if (o.nurAlt && q.name !== 'local-network-access') throw new TypeError('unbekannter Name');
    if (o.wirft) throw new TypeError('unbekannter Name');
    return {state: typeof perm === 'function' ? perm() : perm};
  }};
  Object.defineProperty(globalThis, 'navigator', {value: nav, configurable: true, writable: true});
}
function setzeFetch(art, nachher) {
  fetch = function (url) {
    LOG.fetch.push(url);
    if (nachher) nachher();
    if (art === 200 || art === 500) return Promise.resolve({status: art, ok: art === 200});
    if (art === 'type') return Promise.reject(new TypeError('Failed to fetch'));
    if (art === 'abort') return new Promise(function (_, rej) { setTimeout(function () { const e = new Error('abgebrochen'); e.name = 'AbortError'; rej(e); }, 30); });
    if (art === 'timeout') return new Promise(function (_, rej) { setTimeout(function () { const e = new Error('Zeit'); e.name = 'TimeoutError'; rej(e); }, 30); });
    throw new Error('art?');
  };
}
async function fall(o) {
  LOG.fetch = []; LOG.ms = []; LOG.namen = [];
  let st = o.perm;
  setzeNav(Object.assign({}, o, {perm: typeof st === 'string' ? function () { return st; } : st}));
  setzeFetch(o.fetch, o.nachher ? function () { st = o.nachher; } : null);
  const t0 = Date.now();
  const d = await _kamBueroPruefen('https://g.example.test:8443');
  const fn = {stufe: 'ok', secret: true, basis: 'https://g.example.test:8443'};
  const e = _kamEinrichtung({status: 'ok', rows: [{id: 'a', aktiv: true}]}, fn, d).zeilen.filter(function (z) { return z.id === 'buero'; })[0];
  return {d: d, fetch: LOG.fetch.length, ms: LOG.ms.slice(), namen: LOG.namen.slice(), titel: e.titel, text: e.text, technik: e.technik || '', dauer: Date.now() - t0,
          kachel: (typeof _kamGatewayGrund === 'function') ? _kamGatewayGrund(d) : null};
}
"""

SZENEN = r"""
OUT.ok = await fall({perm: 'granted', fetch: 200});
OUT.antwort = await fall({perm: 'granted', fetch: 500});
OUT.granted_type = await fall({perm: 'granted', fetch: 'type'});
OUT.granted_abort = await fall({perm: 'granted', fetch: 'abort'});
OUT.prompt_type = await fall({perm: 'prompt', fetch: 'type'});
OUT.prompt_abort = await fall({perm: 'prompt', fetch: 'abort'});
OUT.prompt_timeout = await fall({perm: 'prompt', fetch: 'timeout'});
OUT.prompt_ok = await fall({perm: 'prompt', fetch: 200});
OUT.denied = await fall({perm: 'denied', fetch: 200});
OUT.prompt_dann_denied = await fall({perm: 'prompt', fetch: 'type', nachher: 'denied'});
OUT.keins_type = await fall({perm: 'keins', fetch: 'type'});
OUT.keins_abort = await fall({perm: 'keins', fetch: 'abort'});
OUT.wirft_type = await fall({perm: 'prompt', wirft: true, fetch: 'type'});
OUT.alt143 = await fall({perm: 'prompt', nurAlt: true, ua: 'Mozilla/5.0 Chrome/143.0.0.0', fetch: 'type'});
OUT.alt120 = await fall({perm: 'prompt', nurAlt: true, ua: 'Mozilla/5.0 Chrome/120.0.0.0', fetch: 'type'});
OUT.uad144 = await fall({perm: 'prompt', nurAlt: true, ua: 'x', uad: {brands: [{brand: 'Not A Brand', version: '99'}, {brand: 'Chromium', version: '144'}]}, fetch: 'type'});
OUT.ohne_adresse = await _kamBueroPruefen('http://g.example.test');
OUT.alt_string = _kamEinrichtung({status: 'ok', rows: []}, {stufe: 'ok', secret: true, basis: 'https://g'}, 'nicht_erreichbar').zeilen.filter(function (z) { return z.id === 'buero'; })[0];
// Liste der Einrichtung rendern: "Technische Details" nur bei Zeilen mit technik
setzeNav({perm: function () { return 'prompt'; }}); setzeFetch('type');
const dg = await _kamBueroPruefen('https://g.example.test:8443');
const zeilen = _kamEinrichtung({status: 'ok', rows: [{id: 'a', aktiv: true}]}, {stufe: 'ok', secret: true, basis: 'https://g'}, dg).zeilen;
const b1 = rend(React.createElement(KameraEinrichtung, {zeilen: zeilen, onNeu: function () {}}), 'e1');
const det = alle(b1, function (n) { return n.tag === 'details'; });
OUT.render = {details: det.length, text: text(b1), detText: det.length ? text(det[0]) : ''};
const zOk = _kamEinrichtung({status: 'ok', rows: [{id: 'a', aktiv: true}]}, {stufe: 'ok', secret: true, basis: 'https://g'}, {stand: 'ok', berechtigung: 'granted', fehler: ''}).zeilen;
OUT.renderOk = alle(rend(React.createElement(KameraEinrichtung, {zeilen: zOk, onNeu: function () {}}), 'e2'), function (n) { return n.tag === 'details'; }).length;
"""


def _lauf(node_exe, block=None):
    b = block if block is not None else _block()
    js = RENDER_PRELUDE + _layout_echt() + b + "\n" + HARNESS + "\n(async function(){\nconst OUT={};\n" + SZENEN + \
        "\nconsole.log(JSON.stringify(OUT));process.exit(0);\n})().catch(function(e){console.error(e&&e.stack||e);process.exit(3);});\n"
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "lna.cjs")
        with io.open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(js)
        r = subprocess.run([node_exe, p], capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=EPK_TEST_TIMEOUT)
    assert r.returncode == 0, r.stderr[-3000:]
    return json.loads(r.stdout.strip().splitlines()[-1])


def _mut(text, alt, neu):
    assert text.count(alt) == 1, alt
    return text.replace(alt, neu, 1)


@pytest.fixture(scope="module")
def R(node_exe):
    return _lauf(node_exe)


def _sauber(t, mit_erledigt=True):
    for wort in VERBOTEN_IN_EINRICHTUNG + ((("erledigt",) if mit_erledigt else ()) + (":8443", "g.example.test")):
        assert wort not in t, wort


def test_granted_ok_und_antwort(R):
    assert R["ok"]["d"] == {"stand": "ok", "berechtigung": "granted", "fehler": ""}
    assert R["ok"]["ms"] == [8000] and R["ok"]["titel"] == "Kamera-Server im Büro: erreichbar"
    assert R["antwort"]["d"]["stand"] == "antwort"
    assert R["prompt_ok"]["d"]["stand"] == "ok" and R["prompt_ok"]["ms"] == [45000]


def test_denied_ruft_nicht_ab(R):
    d = R["denied"]
    assert d["d"]["stand"] == "lna_gesperrt" and d["fetch"] == 0
    assert d["titel"] == "Kamera-Server im Büro: vom Browser blockiert"
    assert "blockiert den Zugriff auf Geräte im lokalen Netzwerk" in d["text"]
    assert "Schloss-Symbol links neben der Adresse" in d["text"] and "„Zulassen“" in d["text"] and "„Erneut prüfen“" in d["text"]
    assert "Stammzertifikat" not in d["text"]
    assert d["kachel"] == "lna"
    _sauber(d["text"])


def test_prompt_sofortiger_typeerror_zeigt_freigabe_anleitung(R):
    """Der gemessene Fall am Buero-PC: 'prompt' + sofort 'Failed to fetch' -> Anleitung statt Zertifikats-Hinweis."""
    d = R["prompt_type"]
    assert d["d"] == {"stand": "lna_freigabe", "berechtigung": "prompt", "fehler": "TypeError"}
    t = d["text"]
    assert "Schloss-Symbol links neben der Adresse → Website-Einstellungen → „Lokales Netzwerk“" in t
    assert "chrome://settings/content/localNetworkAccess" in t and "diese App (epkolar.github.io) zulassen" in t
    assert "Strg+F5" in t and "„Erneut prüfen“" in t
    assert "Stammzertifikat" not in t and "Büro-WLAN" not in t
    assert d["kachel"] == "lna"
    _sauber(t)


def test_prompt_ablauf_wartet_45s_und_bittet_um_antwort(R):
    for k in ("prompt_abort", "prompt_timeout"):
        d = R[k]
        assert d["d"]["stand"] == "zeitueberschreitung", k
        assert d["ms"] == [45000], k
        assert "Browser-Frage „Auf Geräte im lokalen Netzwerk zugreifen“ mit „Zulassen“" in d["text"]
        assert d["kachel"] == "lna_frage"
        _sauber(d["text"])
    assert R["prompt_abort"]["d"]["fehler"] == "AbortError" and R["prompt_timeout"]["d"]["fehler"] == "TimeoutError"


def test_waehrend_des_wartens_blockiert(R):
    assert R["prompt_dann_denied"]["d"]["stand"] == "lna_gesperrt"
    assert R["prompt_dann_denied"]["fetch"] == 1


def test_granted_fehler_behaelt_drei_punkte_hinweis(R):
    for k in ("granted_type", "granted_abort"):
        d = R[k]
        assert d["d"]["stand"] == "nicht_erreichbar", k
        assert d["titel"] == "Kamera-Server im Büro: nicht erreichbar"
        assert "Stammzertifikat des Kamera-Servers" in d["text"] and "Büro-WLAN" in d["text"]
        assert d["kachel"] == "gateway"
    assert R["granted_type"]["ms"] == [8000]


def test_ohne_permissions_api(R):
    assert R["keins_type"]["d"] == {"stand": "nicht_erreichbar", "berechtigung": "unbekannt", "fehler": "TypeError"}
    assert R["keins_type"]["ms"] == [45000], "Frage evtl. moeglich -> lange Wartezeit"
    assert R["keins_abort"]["d"]["stand"] == "zeitueberschreitung"
    assert R["wirft_type"]["d"]["berechtigung"] == "unbekannt" and R["wirft_type"]["d"]["stand"] == "nicht_erreichbar"


def test_abfragename_neu_dann_alt_nur_ab_chromium_142(R):
    assert R["ok"]["namen"][0] == "local-network"
    assert R["alt143"]["namen"][:2] == ["local-network", "local-network-access"]
    assert R["alt143"]["d"]["stand"] == "lna_freigabe" and R["alt143"]["d"]["berechtigung"] == "prompt"
    assert "local-network-access" not in R["alt120"]["namen"], "alter Name nie in aelteren Renderern (Absturzgefahr)"
    assert R["alt120"]["d"]["berechtigung"] == "unbekannt"
    assert "local-network-access" in R["uad144"]["namen"]


def test_keine_adresse_und_alter_string(R):
    assert R["ohne_adresse"]["stand"] == "keine_adresse"
    assert R["alt_string"]["titel"] == "Kamera-Server im Büro: nicht erreichbar"


def test_technische_details(R):
    assert R["prompt_type"]["technik"] == "Berechtigung: prompt · Fehler: TypeError"
    assert R["denied"]["technik"] == "Berechtigung: denied · Fehler: –"
    assert R["render"]["details"] == 1 and "Technische Details" in R["render"]["detText"]
    assert "Berechtigung: prompt · Fehler: TypeError" in R["render"]["detText"]
    assert R["renderOk"] == 0
    _sauber(R["render"]["text"], mit_erledigt=False)  # Liste: Abzeichen "erledigt" gehoert zum Status, nicht zum Text
    assert "https://g" not in R["render"]["detText"]


def test_quelle_kachel_und_klick():
    b = _block()
    assert "var g=_kamGatewayGrund(r);" in b and "if(gb)_kamBueroPruefen(gb)" in b
    assert "KAMERA_GATEWAY_TIPP[st.grund]" in b
    assert "onNeu:function(){_kamLnaAnstoss(ep.fn&&ep.fn.basis);" in b, "Abruf im Klick (Nutzergeste) anstossen"
    assert "targetAddressSpace" not in re.sub(r"/\*.*?\*/", "", b, flags=re.S), "bei https nicht noetig"


# ── Umkehrproben ──────────────────────────────────────────────────────────
def _alter_block():
    b = _block()
    i = b.index("async function _kamBueroPruefen(basis){")
    j = b.index("\n}\n", i) + 3
    return b[:i] + ALT_PRUEFEN + b[j:]


def test_umkehrprobe_alte_logik(node_exe):
    R = _lauf(node_exe, _alter_block())
    assert R["denied"]["fetch"] == 1, "alt: auch bei gesperrter Freigabe abgerufen"
    assert R["prompt_abort"]["titel"] == "Kamera-Server im Büro: nicht erreichbar", "alt: Ablauf = allgemein nicht erreichbar"
    assert R["prompt_type"]["titel"] == "Kamera-Server im Büro: nicht erreichbar"
    assert R["prompt_abort"]["ms"] == [8000]


def test_umkehrprobe_ohne_vorabfrage(node_exe):
    b = _mut(_block(), "if(lna==='denied')return {stand:'lna_gesperrt',berechtigung:lna,fehler:''};", "")
    R = _lauf(node_exe, b)
    assert R["denied"]["fetch"] == 1


def test_umkehrprobe_ohne_freigabe_zustand(node_exe):
    b = _mut(_block(), "(nach==='prompt'?'lna_freigabe':'nicht_erreichbar')", "'nicht_erreichbar'")
    R = _lauf(node_exe, b)
    assert R["prompt_type"]["d"]["stand"] == "nicht_erreichbar"
    assert "Stammzertifikat" in R["prompt_type"]["text"]


def test_umkehrprobe_ohne_ablauf_unterscheidung(node_exe):
    b = _mut(_block(), "var zeit=name==='AbortError'||name==='TimeoutError';", "var zeit=false;")
    R = _lauf(node_exe, b)
    assert R["prompt_abort"]["d"]["stand"] != "zeitueberschreitung"


def test_umkehrprobe_alter_name_immer(node_exe):
    b = _mut(_block(), "if(_kamChromium()>=142)namen.push", "namen.push")
    R = _lauf(node_exe, b)
    assert "local-network-access" in R["alt120"]["namen"]
