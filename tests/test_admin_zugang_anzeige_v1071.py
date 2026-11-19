# -*- coding: utf-8 -*-
"""v3.9.1071 - Administration > Juprowa: Kopf zeigte UID "—" und Passport "Nicht gesetzt" (rot),
obwohl der Sync mit gueltigen Zugangsdaten lief (Tablet 19.11., Pull 16:08, Letzter Sync 17:15).

Gemessen (read-only, nur Booleans): juprowa_get_config() liefert
{configured, sync_enabled, auto_sync_interval_seconds, last_sync_at, last_sync_result, has_passport}
und absichtlich KEINE Werte. Die Kachel las jupCfg.passport / jupCfg.uid - Felder, die die RPC nie
liefert -> immer "Nicht gesetzt". Reiner Anzeigefehler.

Fix: _zugangAnzeige(cfg, feld) liest has_<feld>. true -> "hinterlegt", false -> "nicht hinterlegt",
fehlt das Feld oder scheiterte das Lesen -> "nicht lesbar" (neutral, nie rot, nie eine Behauptung).
Der Geheimwert selbst wird nie angezeigt.

Gerechnet mit dem echten Code aus index.html in node (Helfer + Kachel-Renderer mit Attrappe fuer
React.createElement). Umkehrprobe eingebaut: falscher Feldschluessel -> nicht mehr "hinterlegt".
"""
import io
import json
import os
import subprocess
import tempfile
from pathlib import Path

from conftest import EPK_TEST_TIMEOUT

WURZEL = Path(__file__).resolve().parents[1]


def _roh():
    return io.open(str(WURZEL / "index.html"), encoding="utf-8", newline="").read()


def _zeile(src, anfang):
    assert src.count(anfang) == 1, anfang
    i = src.index(anfang)
    return src[i:src.index("\n", i)].rstrip("\r")


def _helfer(src):
    return _zeile(src, "function _zugangAnzeige(cfg,feld){")


def _kachel(src):
    z = _zeile(src, "  const _zgKachel=(titel,feld)=>{")
    return z.strip()


PROG = r"""
const React = {createElement: function(t, p) { return {t: t, p: p || {}, c: Array.prototype.slice.call(arguments, 2)}; }};
const V = {bg: 'BG', bd: 'BD', dm: 'DM', tx: 'TX'};
const UI = {fMeta: 12, achtung: 'ACHTUNG', achtungTxt: 'ACHTUNGTXT', neutralTxt: 'NEUTRAL', markeTxt: 'MARKE'};
const _ik = function(n) { return {ik: n}; };
function text(k) { if (k == null || k === false) return ''; if (typeof k === 'string') return k;
  if (k.ik) return '[' + k.ik + ']'; return (k.c || []).map(text).join(''); }
function rahmen(k) { return k.p.style.border; }
function farbe(k) { return k.c[1].p.style.color; }
__HELFER__
const ergebnis = {};
const faelle = {
  live: {configured: true, sync_enabled: true, auto_sync_interval_seconds: 300, last_sync_at: '2026-11-19T16:15:43Z', last_sync_result: {}, has_passport: true},
  ohne: {configured: true, has_passport: false},
  nicht_konfiguriert: {configured: false},
  lesefehler: {_lesefehler: true},
  null_: null,
};
for (const name in faelle) {
  let jupCfg = faelle[name];
  __KACHEL__
  const pp = _zgKachel('Passport', 'passport');
  const uid = _zgKachel('UID', 'uid');
  ergebnis[name] = {
    pp: text(pp.c[1]), pp_rahmen: rahmen(pp), pp_farbe: farbe(pp), pp_titel: text(pp.c[0]),
    uid: text(uid.c[1]), uid_rahmen: rahmen(uid), uid_farbe: farbe(uid),
    roh_pp: _zugangAnzeige(faelle[name], 'passport'),
  };
}
console.log(JSON.stringify(ergebnis));
"""


def _rechne(node_exe, helfer, kachel):
    prog = PROG.replace("__HELFER__", helfer).replace("__KACHEL__", kachel)
    fd, p = tempfile.mkstemp(suffix=".js")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(prog)
    try:
        r = subprocess.run([node_exe, p], capture_output=True, text=True, encoding="utf-8",
                           timeout=EPK_TEST_TIMEOUT)
    finally:
        os.unlink(p)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout.strip().splitlines()[-1])


def test_zugang_hinterlegt_bei_echter_antwort(node_exe):
    src = _roh()
    e = _rechne(node_exe, _helfer(src), _kachel(src))
    live = e["live"]
    assert live["pp"] == "[schild]hinterlegt", live
    assert "Nicht gesetzt" not in live["pp"] and "nicht" not in live["pp"]
    assert live["pp_rahmen"] == "1px solid BD", "Rahmen neutral, nicht rot/gruen"
    # Die RPC liefert fuer die UID kein has_uid -> ehrlich "nicht lesbar", neutral, nie ein Strich
    assert live["uid"] == "nicht lesbar", live
    assert live["uid_farbe"] == "NEUTRAL" and live["uid_rahmen"] == "1px solid BD"


def test_nicht_hinterlegt_nur_bei_ausdruecklichem_false(node_exe):
    src = _roh()
    e = _rechne(node_exe, _helfer(src), _kachel(src))
    for name in ("ohne", "nicht_konfiguriert"):
        assert e[name]["pp"] == "[warnung]nicht hinterlegt", (name, e[name])
        assert e[name]["pp_rahmen"] == "1px solid ACHTUNG", "ruhige Warnung, kein Rot"


def test_lesefehler_ist_nicht_lesbar_und_neutral(node_exe):
    src = _roh()
    e = _rechne(node_exe, _helfer(src), _kachel(src))
    for name in ("lesefehler", "null_"):
        for k in ("pp", "uid"):
            assert e[name][k] == "nicht lesbar", (name, k, e[name])
            assert e[name][k + "_farbe"] == "NEUTRAL"
            assert e[name][k + "_rahmen"] == "1px solid BD"


def test_umkehrprobe_falscher_feldschluessel_wird_rot(node_exe):
    """Mutation: liest der Helfer den falschen Schluessel, darf 'hinterlegt' nicht mehr erscheinen."""
    src = _roh()
    helfer = _helfer(src)
    assert helfer.count('cfg["has_"+feld]') == 1
    kaputt = helfer.replace('cfg["has_"+feld]', 'cfg["hat_"+feld]')
    e = _rechne(node_exe, kaputt, _kachel(src))
    assert e["live"]["pp"] != "[schild]hinterlegt", "Umkehrprobe stumm - der Test misst nichts"


def test_kein_geheimwert_und_kein_alter_lesepfad():
    src = _roh()
    for alt in ("jupCfg.passport", "jupCfg.uid", "Nicht gesetzt"):
        assert alt not in src, alt
    assert src.count('_zgKachel("UID","uid")') == 1
    assert src.count('_zgKachel("Passport","passport")') == 1
    # Lesefehler wird gemerkt, statt 'Keine Konfiguration gefunden' / 'Noch nie' zu behaupten
    assert src.count("setJupCfg({_lesefehler:true})") == 2
    assert 'jupCfg._lesefehler?"nicht lesbar":' in src
