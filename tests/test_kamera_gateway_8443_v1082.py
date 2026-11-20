# -*- coding: utf-8 -*-
"""Riegel 20.11.2026: Gateway-Adresse MIT Port (QNAP: Caddy auf 8443, QTS belegt 443).

Ende-zu-Ende ohne Netz: die echte Edge-Logik (logic.ts bearbeite) gibt mit KAMERA_GATEWAY_BASE="https://<host>:8443"
Adressen aus, die mit genau dieser Basis beginnen (Port bleibt erhalten); der unveraenderte Pruefer (verify.mjs +
token.mjs, Kopf-Konfiguration aus qnap/docker-compose.yml) nimmt das Token fuer DIESE Kamera an, lehnt es fuer eine
andere Kamera und nach Ablauf ab; ein Monteur bekommt gar keine Adresse. Kein echter Host, keine IP im Repo.
Umkehrproben: Basis-Pruefung ohne Port-Erlaubnis -> keine Adresse; Pruefer ohne Ablaufpruefung -> abgelaufen gilt.
"""
import io
import json
import os
import re
import subprocess
import tempfile

import pytest

from conftest import EPK_TEST_TIMEOUT

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUTH = os.path.join(WURZEL, "tools", "kamera-proxy-auth")
LOGIC = os.path.join(WURZEL, "supabase", "functions", "kamera-stream", "logic.ts")
BASIS = "https://gateway.example.test:8443"

HARNESS = r"""
import * as L from "./logic.ts";
import * as VF from "./verify.mjs";
const SECRET = "t".repeat(48);
const CFG = VF.ladeKopfConfig({KAMERA_AUTH_URI_HEADER: "x-forwarded-uri", KAMERA_AUTH_METHOD_HEADER: "x-forwarded-method"});
const JETZT = Date.UTC(2026, 10, 23, 9, 0, 0);
async function ruf(rolle, kamera) {
  const deps = {
    env: (n) => ({KAMERA_TOKEN_SECRET: SECRET, KAMERA_GATEWAY_BASE: %(basis)s})[n],
    now: () => JETZT, nonce: () => "n1",
    authUser: async () => "auth-x",
    ladeNutzer: async () => ({id: "u1", role: rolle, active: 1, locked: false}),
    darfSehen: async () => true, darfSehenBereich: async () => true,
    ladeBackend: async (k) => ({stream_name: k, aufzeichnung_quelle: null, stream_typ: "webrtc"}),
  };
  const res = await L.bearbeite(new Request("https://fn.example.test/kamera-stream", {method: "POST",
    headers: {"content-type": "application/json", origin: "https://epkolar.github.io",
              authorization: "Bearer jwt_0123456789abcdef"}, body: JSON.stringify({kamera_id: kamera})}), deps);
  return {status: res.status, body: await res.json()};
}
async function pruef(url, methode, jetztMs) {
  const u = new URL(url);
  const e = await VF.entscheide({method: "GET", url: "/pruefen",
    headers: {"x-forwarded-uri": u.pathname + u.search, "x-forwarded-method": methode}}, SECRET, jetztMs, CFG);
  return e.status;
}
const OUT = {};
const a = await ruf("admin", "hochregal01");
OUT.status = a.status;
OUT.urls = [a.body.webrtcUrl || "", a.body.liveUrl || "", a.body.snapshotUrl || ""];
OUT.ttl = a.body.ttl;
if (a.body.webrtcUrl) {
  OUT.ok = await pruef(a.body.webrtcUrl, "POST", JETZT);
  OUT.andere_kamera = await pruef(a.body.snapshotUrl.replace("/hochregal01/", "/verkauf02/"), "GET", JETZT);
  OUT.abgelaufen = await pruef(a.body.snapshotUrl, "GET", JETZT + (a.body.ttl + 10) * 1000);
}
const m = await ruf("monteur", "hochregal01");
OUT.monteur_status = m.status;
OUT.monteur_body = JSON.stringify(m.body);
console.log(JSON.stringify(OUT));
"""


def _lies(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read().replace("\r\n", "\n")


def _lauf(node_exe, logic_src=None, verify_src=None):
    with tempfile.TemporaryDirectory() as d:
        for name, quelle, src in (("logic.ts", LOGIC, logic_src), ("token.mjs", os.path.join(AUTH, "token.mjs"), None),
                                  ("verify.mjs", os.path.join(AUTH, "verify.mjs"), verify_src)):
            with io.open(os.path.join(d, name), "w", encoding="utf-8", newline="\n") as f:
                f.write(src if src is not None else _lies(quelle))
        with io.open(os.path.join(d, "h.mjs"), "w", encoding="utf-8", newline="\n") as f:
            f.write(HARNESS % {"basis": json.dumps(BASIS)})
        r = subprocess.run([node_exe, "--experimental-strip-types", "--no-warnings", "h.mjs"], cwd=d,
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=EPK_TEST_TIMEOUT)
    assert r.returncode == 0, r.stderr[-3000:]
    return json.loads(r.stdout.strip().splitlines()[-1])


@pytest.fixture(scope="module")
def E(node_exe):
    return _lauf(node_exe)


def test_adressen_tragen_den_port(E):
    assert E["status"] == 200
    for u in E["urls"]:
        assert u.startswith(BASIS + "/live/hochregal01/"), u


def test_token_hoechstens_zwei_minuten(E):
    assert 0 < E["ttl"] <= 120


def test_pruefer_nimmt_an_nur_diese_kamera_nur_gueltig(E):
    assert E["ok"] == 204
    assert E["andere_kamera"] == 403
    assert E["abgelaufen"] in (401, 403)


def test_monteur_bekommt_keine_adresse(E):
    assert E["monteur_status"] == 403
    assert "token=" not in E["monteur_body"] and "/live/" not in E["monteur_body"]


def test_umkehrprobe_basis_ohne_port(node_exe):
    s = _lies(LOGIC)
    alt = "(:\\d{1,5})?"
    assert alt in s
    e = _lauf(node_exe, logic_src=s.replace(alt, "", 1))
    assert e["status"] != 200 and not any(e["urls"]), "Umkehrprobe: Port in der Basis waere egal"


def test_umkehrprobe_ablauf_blind(node_exe):
    t = _lies(os.path.join(AUTH, "token.mjs"))
    alt = "  if (p.exp <= jetzt) return null;\n"
    assert alt in t
    # token.mjs ohne Ablaufpruefung: der Pruefer (importiert ./token.mjs) muesste das abgelaufene Token annehmen
    assert "./token.mjs" in _lies(os.path.join(AUTH, "verify.mjs"))
    e = _lauf_mit_token(node_exe, t.replace(alt, "", 1))
    assert e["abgelaufen"] == 204, "Umkehrprobe: Ablauf waere blind"


def _lauf_mit_token(node_exe, token_src):
    with tempfile.TemporaryDirectory() as d:
        for name, quelle, src in (("logic.ts", LOGIC, None), ("token.mjs", os.path.join(AUTH, "token.mjs"), token_src),
                                  ("verify.mjs", os.path.join(AUTH, "verify.mjs"), None)):
            with io.open(os.path.join(d, name), "w", encoding="utf-8", newline="\n") as f:
                f.write(src if src is not None else _lies(quelle))
        with io.open(os.path.join(d, "h.mjs"), "w", encoding="utf-8", newline="\n") as f:
            f.write(HARNESS % {"basis": json.dumps(BASIS)})
        r = subprocess.run([node_exe, "--experimental-strip-types", "--no-warnings", "h.mjs"], cwd=d,
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=EPK_TEST_TIMEOUT)
    assert r.returncode == 0, r.stderr[-3000:]
    return json.loads(r.stdout.strip().splitlines()[-1])
