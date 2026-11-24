# -*- coding: utf-8 -*-
"""Kameras Phase 2 (19.11.2026) - Adressarten je Kamera, Token-Pruefer fuer den Reverse-Proxy, Pilot-Seed.

TEIL A: Edge Function (logic.ts) gibt je kamera_backend.stream_typ die passende Adresse aus
        (webrtc | llhls | mjpeg | snapshot) - erst NACH der vollen Pruefung, mit demselben Token.
        Jede ausgegebene Adresse wird vom Proxy-Pruefer (tools/kamera-proxy-auth/verify.mjs) angenommen.
TEIL B: Proxy-Pruefer gegen dieselben Vektoren wie logic.ts (vektoren.json), kreuzweise signiert,
        Dienst-Rauchprobe (kein Token im Protokoll), Umkehrproben.
TEIL C: App-Kachel: MJPEG ueber Bild-Element, Einzelbild mit Takt, "Kamera nicht erreichbar".
TEIL D: SQL-Seed-Entwurf (statisch, nichts wird eingespielt).
"""
import io
import json
import os
import re
import socket
import subprocess
import tempfile
import time
import urllib.request
import urllib.error

import pytest

from conftest import EPK_TEST_TIMEOUT
from test_kameras_phase1_v1055 import RENDER_PRELUDE, _block, _render_lauf

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FN_DIR = os.path.join(WURZEL, "supabase", "functions", "kamera-stream")
LOGIC = os.path.join(FN_DIR, "logic.ts")
INDEX_TS = os.path.join(FN_DIR, "index.ts")
FN_README = os.path.join(FN_DIR, "README.md")
AUTH_DIR = os.path.join(WURZEL, "tools", "kamera-proxy-auth")
VERIFY = os.path.join(AUTH_DIR, "verify.mjs")
TOKEN_MJS = os.path.join(AUTH_DIR, "token.mjs")
VEKTOREN = os.path.join(AUTH_DIR, "vektoren.json")
AUTH_README = os.path.join(AUTH_DIR, "README.md")
SEED = os.path.join(WURZEL, "sql", "KAMERAS_PILOT_SEED_ENTWURF.sql")
SQL = os.path.join(WURZEL, "sql", "KAMERAS_v1_ENTWURF.sql")
DOKU2 = os.path.join(WURZEL, "docs", "kameras", "PHASE2_2026-11-19.md")

BASE = "https://kamera.example.test"
SECRET = "s" * 40
IP_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")


def _lies(p):
    return io.open(p, encoding="utf-8", newline="").read()


def _url(p):
    return "file:///" + p.replace("\\", "/").lstrip("/")


HARNESS = r"""
import * as L from "./logic.ts";
import * as TM from "./token.mjs";
import * as VF from "./verify.mjs";
const SECRET = %(secret)s;
const BASE = %(base)s;
const VEK = %(vek)s;
const MO_10 = Date.UTC(2026, 10, 23, 9, 0, 0);
const CADDY = VF.ladeKopfConfig({KAMERA_AUTH_URI_HEADER: "x-forwarded-uri", KAMERA_AUTH_METHOD_HEADER: "x-forwarded-method"});
const NGINX = VF.ladeKopfConfig({KAMERA_AUTH_URI_HEADER: "x-original-uri", KAMERA_AUTH_METHOD_HEADER: "x-original-method"});
const USERS = {
  admin: {id: "u1", role: "admin", active: 1, locked: false},
  monteur: {id: "u4", role: "monteur", active: 1, locked: false},
  pl: {id: "u2", role: "projektleiter", active: 1, locked: false},
};
const BACKEND = {
  k_webrtc: {stream_name: "g3_37", aufzeichnung_quelle: "g3_37", stream_typ: "webrtc"},
  k_llhls: {stream_name: "g3_38", aufzeichnung_quelle: null, stream_typ: "llhls"},
  k_mjpeg: {stream_name: "mx_32", aufzeichnung_quelle: null, stream_typ: "mjpeg"},
  k_snap: {stream_name: "mx_33", aufzeichnung_quelle: null, stream_typ: "snapshot"},
  k_alt: {stream_name: "g3_39", aufzeichnung_quelle: null},
  k_leer: {stream_name: "g3_61", aufzeichnung_quelle: null, stream_typ: ""},
  k_gross: {stream_name: "g3_62", aufzeichnung_quelle: null, stream_typ: " MJPEG "},
  k_rtsp: {stream_name: "mx_36", aufzeichnung_quelle: null, stream_typ: "rtsp"},
};
async function lauf(wer, kamera, scope, darf) {
  const calls = {darf: 0, bereich: 0, backend: 0};
  const deps = {
    env: (n) => ({KAMERA_TOKEN_SECRET: SECRET, KAMERA_BACKEND_BASE: BASE})[n],
    now: () => MO_10, nonce: () => "n1",
    authUser: async (jwt) => "auth-" + /^jwt_([a-z]+)_/.exec(jwt)[1],
    ladeNutzer: async (uid) => USERS[uid.slice(5)] || null,
    darfSehen: async () => { calls.darf++; return darf !== false; },
    darfSehenBereich: async () => { calls.bereich++; return darf !== false; },
    ladeBackend: async (k) => { calls.backend++; return BACKEND[k] || null; },
  };
  const body = {kamera_id: kamera};
  if (scope) { body.scope = scope; body.geraet = "pc"; }
  if (scope === "aufzeichnung") { body.von = new Date(MO_10 - 3600 * 1000).toISOString(); body.bis = new Date(MO_10).toISOString(); }
  const res = await L.bearbeite(new Request("https://fn.example.test/kamera-stream", {method: "POST",
    headers: {"content-type": "application/json", origin: "https://epkolar.github.io",
              authorization: "Bearer jwt_" + wer + "_0123456789abcdef"}, body: JSON.stringify(body)}), deps);
  const text = await res.text();
  const out = {status: res.status, text, calls};
  if (res.status === 200) {
    out.json = JSON.parse(text);
    // jede Adresse muss der Proxy-Pruefer annehmen (Pfadform, Stream, Art, Methode)
    out.proxy = {};
    for (const key of Object.keys(out.json)) {
      if (!/Url$/.test(key)) continue;
      const u = new URL(out.json[key]);
      let uri = u.pathname + u.search;
      // seit 19.11.: von/bis stehen bereits (signiert) in der Adresse der Edge Function - nichts anhaengen
      const methode = key === "webrtcUrl" ? "POST" : "GET";
      const e = await VF.entscheide({method: "GET", url: "/pruefen", headers: {"x-forwarded-uri": uri, "x-forwarded-method": methode}}, SECRET, MO_10, CADDY);
      out.proxy[key] = {status: e.status, art: (VF.pfadArt(u.pathname) || {}).art || null};
      if (e.headers["X-Kamera-Von"]) { out.proxy[key].von = e.headers["X-Kamera-Von"]; out.proxy[key].bis = e.headers["X-Kamera-Bis"]; }
    }
  }
  return out;
}
const R = {edge: {}};
for (const [name, args] of Object.entries({
  webrtc: ["admin", "k_webrtc"], llhls: ["admin", "k_llhls"], mjpeg: ["admin", "k_mjpeg"], snap: ["admin", "k_snap"],
  alt: ["admin", "k_alt"], leer: ["admin", "k_leer"], gross: ["admin", "k_gross"], rtsp: ["admin", "k_rtsp"],
  rec: ["admin", "k_webrtc", "aufzeichnung"], rec_mjpeg: ["admin", "k_mjpeg", "aufzeichnung"],
  monteur_mjpeg: ["monteur", "k_mjpeg"], monteur_snap: ["monteur", "k_snap"],
  pl_ohne_regel_mjpeg: ["pl", "k_mjpeg", null, false],
})) R.edge[name] = await lauf(args[0], args[1], args[2], args[3]);

// Vektoren: beide Umsetzungen, dieselben Erwartungen
R.vek = {token: [], anfragen: []};
for (const v of VEK.token) {
  const a = (await L.pruefeToken(VEK.secret, v.token, v.now_ms, v.erwartet)) !== null;
  const b = (await TM.pruefeToken(VEK.secret, v.token, v.now_ms, v.erwartet)) !== null;
  R.vek.token.push({name: v.name, soll: v.ok, logic: a, mjs: b});
}
for (const v of VEK.anfragen) {
  const h = Object.assign({"x-forwarded-uri": v.uri, "x-forwarded-method": v.method}, v.headers || {});
  const e = await VF.entscheide({method: "GET", url: "/pruefen", headers: h}, VEK.secret, v.now_ms || VEK.now_ms, CADDY);
  R.vek.anfragen.push({name: v.name, soll: v.status, ist: e.status, cookie: !!e.headers["Set-Cookie"], sollCookie: !!v.cookie,
    cookieText: e.headers["Set-Cookie"] || "", info: JSON.stringify(e.info), kopf: e.headers});
}
// nginx-Weg: X-Original-URI / X-Original-Method statt X-Forwarded-*
const g = VEK.token[0].token;
const E = async (h, cfg) => (await VF.entscheide({method: "GET", url: "/live/g3_37/mjpeg?token=" + g, headers: h}, VEK.secret, VEK.now_ms, cfg)).status;
const A = "/live/g3_37/mjpeg?token=" + g;   // Token gilt fuer g3_37
const B = "/live/g3_38/mjpeg?token=" + g;   // tatsaechlich angefragt: g3_38
R.nginx = await E({"x-original-uri": "/live/g3_37/whep?token=" + g, "x-original-method": "POST"}, NGINX);
R.direkt = await E({}, CADDY);
R.doppelkopf = await E({"x-forwarded-uri": [A, "/a"], "x-forwarded-method": "GET"}, CADDY);
R.spoof = {
  // Angriff unter nginx: nginx setzt X-Original-URI = B (echt), Client schleust X-Forwarded-Uri = A ein
  nginx_angriff: await E({"x-original-uri": B, "x-original-method": "GET", "x-forwarded-uri": A, "x-forwarded-method": "GET"}, NGINX),
  nginx_angriff_nur_uri: await E({"x-original-uri": B, "x-original-method": "GET", "x-forwarded-uri": A}, NGINX),
  nginx_fremde_methode: await E({"x-original-uri": A, "x-original-method": "GET", "x-forwarded-method": "GET"}, NGINX),
  nginx_leerer_fremdkopf: await E({"x-original-uri": A, "x-original-method": "GET", "x-forwarded-uri": ""}, NGINX),
  nginx_echt_b: await E({"x-original-uri": B, "x-original-method": "GET"}, NGINX),
  nginx_echt_a: await E({"x-original-uri": A, "x-original-method": "GET"}, NGINX),
  // Angriff unter Caddy: Caddy setzt X-Forwarded-Uri = B, Client schleust X-Original-URI = A ein
  caddy_angriff: await E({"x-forwarded-uri": B, "x-forwarded-method": "GET", "x-original-uri": A, "x-original-method": "GET"}, CADDY),
  caddy_fremd_bei_gutem_pfad: await E({"x-forwarded-uri": A, "x-forwarded-method": "GET", "x-original-uri": A}, CADDY),
  caddy_echt_a: await E({"x-forwarded-uri": A, "x-forwarded-method": "GET"}, CADDY),
  // nur der nicht konfigurierte Kopf / ohne Konfiguration / ohne Methode
  caddy_cfg_nur_original: await E({"x-original-uri": A, "x-original-method": "GET"}, CADDY),
  ohne_cfg: await E({"x-forwarded-uri": A, "x-forwarded-method": "GET"}, undefined),
  ohne_methode: await E({"x-forwarded-uri": A}, CADDY),
};
R.cfg = {
  leer: VF.ladeKopfConfig({}),
  nurUri: VF.ladeKopfConfig({KAMERA_AUTH_URI_HEADER: "x-forwarded-uri"}),
  gemischt: VF.ladeKopfConfig({KAMERA_AUTH_URI_HEADER: "x-forwarded-uri", KAMERA_AUTH_METHOD_HEADER: "x-original-method"}),
  fremd: VF.ladeKopfConfig({KAMERA_AUTH_URI_HEADER: "host", KAMERA_AUTH_METHOD_HEADER: "x-forwarded-method"}),
  gross: VF.ladeKopfConfig({KAMERA_AUTH_URI_HEADER: "X-Original-URI", KAMERA_AUTH_METHOD_HEADER: "X-Original-Method"}),
  caddy: CADDY,
};
// kreuzweise signiert: gleiche Payload -> byte-gleiches Token
const p = {v: 1, k: "kam_01", s: "g3_37", u: "u1", sc: "live", iat: 1795424400, exp: 1795424490, n: "x"};
const t1 = await L.signiere(SECRET, p), t2 = await TM.signiere(SECRET, p);
R.kreuz = {gleich: t1 === t2, aufMjs: (await TM.pruefeToken(SECRET, t1, 1795424400000)) !== null, aufLogic: (await L.pruefeToken(SECRET, t2, 1795424400000)) !== null};
R.secret = {kurz: VF.ladeSecret({KAMERA_TOKEN_SECRET: "kurz"}), leer: VF.ladeSecret({}), gut: VF.ladeSecret({KAMERA_TOKEN_SECRET: SECRET}) === SECRET};
console.log(JSON.stringify(R));
"""


def _lauf(node_exe, logic_src=None, token_src=None, verify_src=None):
    with tempfile.TemporaryDirectory() as d:
        for name, quelle, src in (("logic.ts", LOGIC, logic_src), ("token.mjs", TOKEN_MJS, token_src),
                                  ("verify.mjs", VERIFY, verify_src)):
            with io.open(os.path.join(d, name), "w", encoding="utf-8", newline="\n") as f:
                f.write(src if src is not None else _lies(quelle))
        with io.open(os.path.join(d, "h.mjs"), "w", encoding="utf-8", newline="\n") as f:
            f.write(HARNESS % {"secret": json.dumps(SECRET), "base": json.dumps(BASE), "vek": _lies(VEKTOREN)})
        r = subprocess.run([node_exe, "--experimental-strip-types", "--no-warnings", "h.mjs"], cwd=d,
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=EPK_TEST_TIMEOUT)
    assert r.returncode == 0, r.stderr[-3000:]
    return json.loads(r.stdout.strip().splitlines()[-1])


@pytest.fixture(scope="module")
def R(node_exe):
    return _lauf(node_exe)


# ── TEIL A: Adressarten aus der Edge Function ─────────────────────────────────
def test_webrtc_wie_phase1_mit_typ(R):
    e = R["edge"]["webrtc"]
    assert e["status"] == 200
    j = e["json"]
    assert j["typ"] == "webrtc"
    assert j["webrtcUrl"].startswith(BASE + "/live/g3_37/whep?token=")
    assert j["liveUrl"].startswith(BASE + "/live/g3_37/index.m3u8?token=")
    # Pin angepasst 20.11.2026 (feature/kamera-gateway): webrtc liefert zusaetzlich snapshotUrl als Einzelbild-
    # Rueckfall (QNAP-Gateway hat HLS aus). Gleiches Token, Proxy-Pruefer nimmt auch diese Adresse an (204).
    assert set(j) == {"typ", "webrtcUrl", "liveUrl", "snapshotUrl", "exp", "ttl"}
    assert j["snapshotUrl"].startswith(BASE + "/live/g3_37/snapshot.jpg?token=")
    assert e["proxy"] == {"webrtcUrl": {"status": 204, "art": "whep"}, "liveUrl": {"status": 204, "art": "hls"},
                          "snapshotUrl": {"status": 204, "art": "snapshot"}}


@pytest.mark.parametrize("fall,typ,schluessel,art", [
    ("llhls", "llhls", "liveUrl", "hls"),
    ("mjpeg", "mjpeg", "mjpegUrl", "mjpeg"),
    ("snap", "snapshot", "snapshotUrl", "snapshot"),
])
def test_jede_art_genau_ihre_adresse(R, fall, typ, schluessel, art):
    e = R["edge"][fall]
    assert e["status"] == 200
    j = e["json"]
    assert j["typ"] == typ and set(j) == {"typ", schluessel, "exp", "ttl"}
    assert e["proxy"] == {schluessel: {"status": 204, "art": art}}


def test_mjpeg_und_snapshot_pfade(R):
    assert re.match(re.escape(BASE) + r"/live/mx_32/mjpeg\?token=[A-Za-z0-9_.-]+$", R["edge"]["mjpeg"]["json"]["mjpegUrl"])
    assert re.match(re.escape(BASE) + r"/live/mx_33/snapshot\.jpg\?token=[A-Za-z0-9_.-]+$", R["edge"]["snap"]["json"]["snapshotUrl"])


def test_ohne_oder_leerer_typ_ist_webrtc_und_gross_klein_egal(R):
    assert R["edge"]["alt"]["json"]["typ"] == "webrtc"
    assert R["edge"]["leer"]["json"]["typ"] == "webrtc"
    assert R["edge"]["gross"]["json"]["typ"] == "mjpeg"


def test_unbekannter_typ_503_ohne_adresse(R):
    e = R["edge"]["rtsp"]
    assert e["status"] == 503 and json.loads(e["text"]) == {"error": "nicht_konfiguriert"}


def test_aufzeichnung_unveraendert_und_vom_proxy_angenommen(R):
    e = R["edge"]["rec"]
    assert e["status"] == 200 and set(e["json"]) == {"aufzeichnungUrl", "von", "bis", "exp", "ttl"}
    assert e["proxy"]["aufzeichnungUrl"]["status"] == 204
    # der Proxy bekommt den signierten Bereich als Kopf (daraus baut er die Frigate-Adresse)
    assert e["proxy"]["aufzeichnungUrl"]["von"] == str(e["json"]["von"]) and e["proxy"]["aufzeichnungUrl"]["bis"] == str(e["json"]["bis"])
    assert e["calls"]["bereich"] == 1
    assert R["edge"]["rec_mjpeg"]["status"] == 503, "Mobotix ohne Aufzeichnungsquelle"


@pytest.mark.parametrize("fall", ["monteur_mjpeg", "monteur_snap", "pl_ohne_regel_mjpeg"])
def test_typ_erst_nach_voller_pruefung(R, fall):
    e = R["edge"][fall]
    assert e["status"] == 403 and json.loads(e["text"]) == {"error": "kein_zugriff"}
    for verboten in ("typ", "mjpeg", "snapshot", "mx_3", "http", "token"):
        assert verboten not in e["text"], verboten
    assert e["calls"]["backend"] == 0, "Backend (und damit der Typ) wird vor der Freigabe nie gelesen"
    if fall.startswith("monteur"):
        assert e["calls"]["darf"] == 0


def test_index_ts_liest_stream_typ():
    s = _lies(INDEX_TS)
    assert 'select("stream_name, aufzeichnung_quelle, stream_typ")' in s
    assert "stream_typ: r.stream_typ === null" in s


def test_sql_entwurf_kennt_stream_typ():
    s = _lies(SQL)
    assert "stream_typ          text not null default 'webrtc'," in s
    assert "check (stream_typ in ('webrtc','llhls','mjpeg','snapshot'))" in s


def test_fn_readme_beschreibt_arten():
    r = _lies(FN_README)
    for teil in ("stream_typ", '"typ"', "mjpegUrl", "snapshotUrl", "/live/<s>/mjpeg", "/live/<s>/snapshot.jpg",
                 "tools/kamera-proxy-auth"):
        assert teil in r, teil


# ── TEIL B: Proxy-Pruefer ─────────────────────────────────────────────────────
def test_beide_umsetzungen_erfuellen_alle_tokenvektoren(R):
    for v in R["vek"]["token"]:
        assert v["logic"] == v["soll"], ("logic.ts", v["name"])
        assert v["mjs"] == v["soll"], ("token.mjs", v["name"])
    assert len(R["vek"]["token"]) >= 20


def test_pruefer_anfragevektoren(R):
    for v in R["vek"]["anfragen"]:
        assert v["ist"] == v["soll"], (v["name"], v["ist"], v["soll"])
        assert v["cookie"] == v["sollCookie"], v["name"]
        assert "token" not in v["info"] and "." not in v["info"].replace("\"", ""), v["name"]
        if v["ist"] == 204:
            assert v["kopf"]["X-Kamera-Stream"] and v["kopf"]["Cache-Control"] == "no-store"
    namen = {v["name"] for v in R["vek"]["anfragen"]}
    for pflicht in ("gekippt", "abgelaufen", "anderer_stream_im_pfad", "live_token_fuer_aufzeichnung", "go2rtc_api",
                    "fremdes_secret", "payload_getauscht", "punktpunkt") + AUFZ_ANGRIFFE:
        assert pflicht in namen, pflicht


AUFZ_ANGRIFFE = ("aufzeichnung_von_manipuliert", "aufzeichnung_bis_manipuliert", "aufzeichnung_fenster_verschoben",
                 "aufzeichnung_von_doppelt", "aufzeichnung_von_kodiert", "aufzeichnung_name_kodiert",
                 "aufzeichnung_fuehrende_null", "aufzeichnung_teil_falsches_von", "aufzeichnung_ohne_zeit")


def test_angriff_aufzeichnung_query_bereich_ungleich_token_403(R):
    """Befund 19.11.: von/bis stehen signiert im Token; jede Abweichung in der Query (verschoben, doppelt,
    kodiert, fuehrende Null, fehlend) -> 403 am Pruefer. Der passende Bereich -> 204."""
    v = {x["name"]: x for x in R["vek"]["anfragen"]}
    for k in AUFZ_ANGRIFFE:
        assert v[k]["ist"] == 403, (k, v[k]["ist"])
    assert v["aufzeichnung_gut"]["ist"] == 204
    assert v["aufzeichnung_alter_token_ohne_bereich"]["ist"] == 401, "Token ohne signierten Bereich gilt nicht mehr"
    assert v["aufzeichnung_teil_mit_cookie"]["ist"] == 204


def test_aufzeichnung_bereich_als_kopf_fuer_den_proxy(R):
    v = {x["name"]: x for x in R["vek"]["anfragen"]}
    for k in ("aufzeichnung_gut", "aufzeichnung_teil_mit_cookie"):
        assert v[k]["kopf"]["X-Kamera-Von"] == "1795420800" and v[k]["kopf"]["X-Kamera-Bis"] == "1795424400", k
    assert "X-Kamera-Von" not in v["mjpeg"]["kopf"], "Live ohne Bereichskopf"


def test_tokenvektoren_bereich(R):
    t = {x["name"]: x for x in R["vek"]["token"]}
    assert t["aufzeichnung_mit_bereich"]["soll"] is True
    for k in ("aufzeichnung_ohne_bereich", "aufzeichnung_bereich_umgekehrt", "aufzeichnung_bereich_als_text", "live_mit_bereich"):
        assert t[k]["soll"] is False and t[k]["logic"] is False and t[k]["mjs"] is False, k


def test_umkehrprobe_ohne_bereichsbindung_im_pruefer(node_exe):
    # Stand vor dem Fix: von/bis aus der Query nur auf Form geprueft, nicht gegen das Token -> Fenster verschiebbar
    R2 = _lauf(node_exe, verify_src=_mut(VERIFY, "if (!ok(\"von\", gv) || !ok(\"bis\", gb)) return nein(403,", "if (false) return nein(403,"))
    v = {x["name"]: x for x in R2["vek"]["anfragen"]}
    for k in ("aufzeichnung_von_manipuliert", "aufzeichnung_fenster_verschoben", "aufzeichnung_bis_manipuliert"):
        assert v[k]["ist"] == 204, (k, v[k]["ist"])


def test_umkehrprobe_token_ohne_bereichsregel(node_exe):
    regel = "if (p.sc === \"aufzeichnung\" && !(Number.isInteger(p.von) && Number.isInteger(p.bis) && Number(p.von) < Number(p.bis))) return null;"
    R2 = _lauf(node_exe, token_src=_mut(TOKEN_MJS, regel, ""))
    t = {x["name"]: x for x in R2["vek"]["token"]}
    assert t["aufzeichnung_ohne_bereich"]["mjs"] is True


def test_hls_cookie_eng_gebunden(R):
    c = [v for v in R["vek"]["anfragen"] if v["name"] == "hls_index"][0]["cookieText"]
    assert c.startswith("kam_t=") and "Path=/live/g3_37/;" in c and "HttpOnly" in c and "Secure" in c
    assert re.search(r"Max-Age=(\d+);", c) and 0 < int(re.search(r"Max-Age=(\d+);", c).group(1)) <= 120


def test_nginx_kopf_direktaufruf_und_doppelter_kopf(R):
    assert R["nginx"] == 204
    assert R["direkt"] == 403, "kein Rueckfall auf die eigene Anfrage-URL"
    assert R["doppelkopf"] == 403


def test_nur_der_konfigurierte_kopf_zaehlt(R):
    sp = R["spoof"]
    for k in ("nginx_angriff", "nginx_angriff_nur_uri", "nginx_fremde_methode", "nginx_leerer_fremdkopf", "nginx_echt_b",
              "caddy_angriff", "caddy_fremd_bei_gutem_pfad", "caddy_cfg_nur_original", "ohne_cfg", "ohne_methode"):
        assert sp[k] == 403, (k, sp[k])
    assert sp["nginx_echt_a"] == 204 and sp["caddy_echt_a"] == 204


def test_angriff_gueltiges_a_token_mit_gefaelschtem_b_kopf(R):
    # Token gilt fuer g3_37 (A). Tatsaechlich angefragt: g3_38 (B). Der Proxy setzt den echten Pfad B in seinen
    # Kopf; der Client schleust den Kopf des ANDEREN Proxys mit Pfad A ein. Darf nie 204 werden.
    sp = R["spoof"]
    assert sp["nginx_angriff"] == 403, sp["nginx_angriff"]
    assert sp["nginx_angriff_nur_uri"] == 403, sp["nginx_angriff_nur_uri"]
    assert sp["caddy_angriff"] == 403, sp["caddy_angriff"]
    assert sp["nginx_echt_b"] == 403


def test_angriff_eingeschleuster_kopf_und_kein_rueckfall(R):
    # Jeder Kopf des nicht konfigurierten Paares ist eingeschleust -> 403, auch bei sonst gueltiger Anfrage.
    # Ohne konfigurierten Kopf kein Rueckfall auf die eigene Anfrage-URL -> 403.
    sp = R["spoof"]
    for k in ("caddy_fremd_bei_gutem_pfad", "nginx_fremde_methode", "nginx_leerer_fremdkopf", "caddy_cfg_nur_original"):
        assert sp[k] == 403, (k, sp[k])
    assert R["direkt"] == 403, R["direkt"]


def test_kopf_konfiguration_ist_pflicht_und_paarweise(R):
    c = R["cfg"]
    assert c["leer"] is None and c["nurUri"] is None and c["gemischt"] is None and c["fremd"] is None
    assert c["gross"] == {"uriHeader": "x-original-uri", "methodHeader": "x-original-method",
                          "fremd": ["x-forwarded-uri", "x-forwarded-method"]}
    assert c["caddy"]["fremd"] == ["x-original-uri", "x-original-method"]


def test_pruefer_liest_kopfnamen_nie_fest():
    v = _lies(VERIFY)
    code = "\n".join(z for z in v.replace("\r\n", "\n").split("\n") if not z.lstrip().startswith("//"))
    assert "req.url ||" not in code and "String(req.url" not in code, "kein Rueckfall auf req.url"
    assert not re.search(r"kopf\(h, \"x-(forwarded|original)-", code), "Uri/Methode nur ueber cfg"
    assert "kopf(h, cfg.uriHeader)" in code and "kopf(h, cfg.methodHeader)" in code
    assert "for (const k of cfg.fremd) if (h[k] !== undefined) return nein(403);" in code


def test_snippets_raeumen_client_koepfe_ab():
    r = _lies(AUTH_README).replace("\r\n", "\n")
    i = r.index("location = /_kamera_pruefen {")
    ng = r[i:r.index("}", i)]
    assert re.search(r"proxy_set_header\s+X-Original-URI\s+\$request_uri;", ng)
    assert re.search(r"proxy_set_header\s+X-Original-Method\s+\$request_method;", ng)
    assert re.search(r'proxy_set_header\s+X-Forwarded-Uri\s+"";', ng)
    assert re.search(r'proxy_set_header\s+X-Forwarded-Method\s+"";', ng)
    j = r.index("forward_auth kamera-auth:9099 {")
    ca = r[j:r.index("}", j)]
    assert "header_up -X-Original-URI" in ca and "header_up -X-Original-Method" in ca
    for teil in ("KAMERA_AUTH_URI_HEADER=x-forwarded-uri", "KAMERA_AUTH_METHOD_HEADER=x-forwarded-method",
                 "`KAMERA_AUTH_URI_HEADER=x-original-uri`", "**overwrites**", "no fallback"):
        assert teil in r, teil


def test_kreuzweise_signiert_byte_gleich(R):
    assert R["kreuz"] == {"gleich": True, "aufMjs": True, "aufLogic": True}


def test_secret_mindestlaenge(R):
    assert R["secret"] == {"kurz": None, "leer": None, "gut": True}


def _regelzeilen(src):
    i = src.index("export async function pruefeToken(")
    j = src.index("return p;", i)
    return [z.strip() for z in src[i:j].replace("\r\n", "\n").split("\n") if z.strip().startswith("if (")]


def test_regelzeilen_woertlich_gleich():
    a = _regelzeilen(_lies(LOGIC))
    b = _regelzeilen(_lies(TOKEN_MJS))
    assert len(a) >= 12 and a == b


def test_pruefer_ohne_abhaengigkeiten_und_ohne_token_protokoll():
    for p in (VERIFY, TOKEN_MJS):
        s = _lies(p)
        for imp in re.findall(r'^import .* from "([^"]+)";', s, re.M):
            assert imp.startswith("node:") or imp == "./token.mjs", imp
        assert set(IP_RE.findall(s)) <= {"127.0.0.1", "0.0.0.0"}, p
    v = _lies(VERIFY)
    # die einzige Protokollzeile nennt nur status/art/s/u
    zeilen = [z for z in v.split("\n") if "process.stdout.write(JSON.stringify(" in z]
    assert len(zeilen) == 1 and "token" not in zeilen[0] and "query" not in zeilen[0] and "uri" not in zeilen[0]
    assert "console.log" not in v


def _freier_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def _hole(url, headers):
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code


def test_dienst_rauchprobe_ohne_token_im_protokoll(node_exe):
    vek = json.loads(_lies(VEKTOREN))
    port = _freier_port()
    env = dict(os.environ, KAMERA_TOKEN_SECRET=vek["secret"], KAMERA_AUTH_PORT=str(port), KAMERA_AUTH_LOG="1",
               KAMERA_AUTH_URI_HEADER="x-forwarded-uri", KAMERA_AUTH_METHOD_HEADER="x-forwarded-method")
    pr = subprocess.Popen([node_exe, VERIFY], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        for _ in range(50):
            try:
                if _hole("http://127.0.0.1:%d/gesund" % port, {}) == 200:
                    break
            except Exception:
                time.sleep(0.1)
        else:
            pytest.fail("Dienst startet nicht")
        tok = vek["token"][0]["token"]
        # echte Uhr: das Vektor-Token ist abgelaufen -> 401; ohne Token 401; fremde Pfade 403
        assert _hole("http://127.0.0.1:%d/pruefen" % port, {"X-Forwarded-Uri": "/live/g3_37/mjpeg?token=" + tok,
                                                           "X-Forwarded-Method": "GET"}) == 401
        # eingeschleuster nginx-Kopf bei Caddy-Konfiguration -> 403
        assert _hole("http://127.0.0.1:%d/pruefen" % port, {"X-Forwarded-Uri": "/live/g3_37/mjpeg?token=" + tok,
                                                           "X-Forwarded-Method": "GET", "X-Original-URI": "/x"}) == 403
        assert _hole("http://127.0.0.1:%d/pruefen" % port, {"X-Forwarded-Uri": "/api/streams"}) == 403
    finally:
        pr.terminate()
        out, err = pr.communicate(timeout=10)
    assert tok not in out and tok not in err
    assert tok.split(".")[0] not in out
    assert '"status":401' in out and '"status":403' in out


@pytest.mark.parametrize("uri_kopf,methoden_kopf", [(None, None), ("x-forwarded-uri", None),
                                                    ("x-forwarded-uri", "x-original-method"), ("host", "x-forwarded-method")])
def test_dienst_startet_nicht_ohne_kopfkonfiguration(node_exe, uri_kopf, methoden_kopf):
    env = {k: v for k, v in os.environ.items() if not k.startswith("KAMERA_")}
    env["KAMERA_TOKEN_SECRET"] = "x" * 40
    env["KAMERA_AUTH_PORT"] = str(_freier_port())
    if uri_kopf:
        env["KAMERA_AUTH_URI_HEADER"] = uri_kopf
    if methoden_kopf:
        env["KAMERA_AUTH_METHOD_HEADER"] = methoden_kopf
    r = subprocess.run([node_exe, VERIFY], env=env, capture_output=True, text=True, timeout=EPK_TEST_TIMEOUT)
    assert r.returncode == 1 and "KAMERA_AUTH_URI_HEADER" in r.stderr


def test_dienst_startet_nicht_ohne_secret(node_exe):
    env = {k: v for k, v in os.environ.items() if not k.startswith("KAMERA_")}
    env["KAMERA_TOKEN_SECRET"] = "zu-kurz"
    r = subprocess.run([node_exe, VERIFY], env=env, capture_output=True, text=True, timeout=EPK_TEST_TIMEOUT)
    assert r.returncode == 1 and "zu-kurz" not in r.stderr


def test_auth_readme_mit_caddy_und_nginx():
    r = _lies(AUTH_README)
    for teil in ("forward_auth", "auth_request", "X-Forwarded-Uri", "X-Original-URI", "KAMERA_TOKEN_SECRET",
                 "vektoren.json", "204", "401", "403", "kam_t", "query", "delete token"):
        assert teil in r, teil
    assert set(IP_RE.findall(r)) <= {"0.0.0.0"}


VORLAGEN = os.path.join(AUTH_DIR, "vorlagen")


def test_vorlagen_raeumen_client_koepfe_ab():
    ng = _lies(os.path.join(VORLAGEN, "nginx.conf")).replace("\r\n", "\n")
    ca = _lies(os.path.join(VORLAGEN, "Caddyfile")).replace("\r\n", "\n")
    for t in (ng, ca):
        assert not IP_RE.search(t), "keine echten Adressen in den Vorlagen"
    # nginx: Unterstrich-Koepfe aus, vertrauenswuerdiges Paar ueberschrieben, Client-Kopien geleert
    code = "\n".join(z.split("#", 1)[0] for z in ng.split("\n"))
    assert re.search(r"^\s*underscores_in_headers off;", code, re.M)
    i = code.index("location = /_kamera_pruefen {")
    loc = code[i:code.index("}", i)]
    assert "internal;" in loc and "proxy_pass_request_body off;" in loc
    assert re.search(r"proxy_set_header\s+X-Original-URI\s+\$request_uri;", loc)
    assert re.search(r"proxy_set_header\s+X-Original-Method\s+\$request_method;", loc)
    assert re.search(r'proxy_set_header\s+X-Forwarded-Uri\s+"";', loc)
    assert re.search(r'proxy_set_header\s+X-Forwarded-Method\s+"";', loc)
    assert code.count("auth_request /_kamera_pruefen;") == 3
    assert "$request_uri" not in code.split("log_format", 1)[1].split(";", 1)[0], "kein Token im Protokoll"
    assert re.search(r"location / \{ return 404; \}", code)
    # Caddy: jedes aktive forward_auth setzt das Paar ausdruecklich und entfernt X-Original-*
    aktiv = "\n".join(z for z in ca.split("\n") if not z.lstrip().startswith("#"))
    bloecke = aktiv.split("forward_auth kamera-auth:9099 {")[1:]
    assert len(bloecke) == 3
    for b in bloecke:
        b = b[:b.index("\n\t\t\t}")]
        for zeile in ("uri /pruefen", "header_up -X-Original-URI", "header_up -X-Original-Method",
                      "header_up X-Forwarded-Uri {http.request.orig_uri}",
                      "header_up X-Forwarded-Method {http.request.orig_method}"):
            assert zeile in b, zeile
    # forward_auth steht in jedem Block VOR dem rewrite
    for teil in aktiv.split("route {")[1:]:
        if "rewrite" in teil:
            assert teil.index("forward_auth") < teil.index("rewrite")
    assert "delete token" in aktiv and "respond 404" in aktiv


# Umkehrproben: die Pruefungen haben Zaehne
def _mut(p, alt, neu):
    s = _lies(p)
    assert s.count(alt) == 1, alt
    return s.replace(alt, neu, 1)


def test_umkehrprobe_ablauf_in_token_mjs(node_exe):
    R2 = _lauf(node_exe, token_src=_mut(TOKEN_MJS, "if (p.exp <= jetzt) return null;", ""))
    v = {x["name"]: x for x in R2["vek"]["token"]}
    assert v["abgelaufen"]["mjs"] is True, "Umkehrprobe: Ablauf-Vektor waere blind"


def test_umkehrprobe_pfadbindung_im_pruefer(node_exe):
    R2 = _lauf(node_exe, verify_src=_mut(VERIFY, "{ s: ziel.s, sc: ziel.sc }", "{}"))
    v = {x["name"]: x for x in R2["vek"]["anfragen"]}
    assert v["anderer_stream_im_pfad"]["ist"] != 403


def test_umkehrprobe_fremdkopf_sperre(node_exe):
    R2 = _lauf(node_exe, verify_src=_mut(VERIFY, "for (const k of cfg.fremd) if (h[k] !== undefined) return nein(403);", ""))
    assert R2["spoof"]["caddy_fremd_bei_gutem_pfad"] == 204, "Umkehrprobe: Fremdkopf-Riegel waere blind"


def test_umkehrprobe_altes_verhalten_einer_von_beiden_koepfen(node_exe):
    # Alter Stand: Uri aus X-Forwarded-Uri ODER X-Original-URI, kein Fremdkopf-Riegel -> nginx-Angriff kommt durch
    alt = _mut(VERIFY, "for (const k of cfg.fremd) if (h[k] !== undefined) return nein(403);", "")
    a = "const uri = kopf(h, cfg.uriHeader);"
    assert alt.count(a) == 1
    alt = alt.replace(a, "const uri = kopf(h, \"x-forwarded-uri\") || kopf(h, \"x-original-uri\");", 1)
    R2 = _lauf(node_exe, verify_src=alt)
    assert R2["spoof"]["nginx_angriff"] == 204, "Umkehrprobe: Pfadbindung waere per Kopf umgehbar"


def test_umkehrprobe_typ_vor_pruefung_wuerde_monteur_verraten(node_exe):
    # wuerde der Typ vor der Rollensperre gelesen, faende der Test ladeBackend-Aufrufe beim Monteur
    s = _lies(LOGIC)
    alt = "    // 3. harte Rollenliste"
    assert s.count(alt) == 1
    kaputt = s.replace(alt, "    await deps.ladeBackend(\"k_mjpeg\");\n" + alt, 1)
    R2 = _lauf(node_exe, logic_src=kaputt)
    assert R2["edge"]["monteur_mjpeg"]["calls"]["backend"] > 0


# ── TEIL C: App-Kachel ────────────────────────────────────────────────────────
SZENEN2 = r"""
function reset(s) { SZENE = s; store.clear(); _kamBackend.fehlt = false; ['get','post','upsert','del','fetch'].forEach(function (k) { ZAEHL[k].length = 0; }); }
const KAMS = [{id: 'cam1', name: 'Kamera 1', standort: 'Hof', aktiv: true, aufbewahrung_tage: 3}];
function wurzel(rolle) { return React.createElement(KameraView, {curUser: {id: 'x', role: rolle}, ww: 1440, users: []}); }
function bilder() { return alle(baum, function (n) { return n.tag === 'img'; }); }
function videos() { return alle(baum, function (n) { return n.tag === 'video'; }); }
function warte(ms) { return new Promise(function (r) { setTimeout(r, ms); }); }

reset({db: {kameras: KAMS}, fein: true, fetch: {status: 200, json: {typ: 'mjpeg', mjpegUrl: 'https://p/live/mx_32/mjpeg?token=T1', exp: 1e12, ttl: 90}}});
let w = wurzel('projektleiter'); await ruhe(w);
let b = bilder();
OUT.mjpeg = {n: b.length, src: b.length ? b[0].props.src : '', ref: b.length ? b[0].props.referrerPolicy : '', text: text(baum),
             videoSichtbar: videos().map(function (v) { return v.props.style.display; })};
// Pin angepasst 24.11.2026 (feature/kamera-kachel-reconnect, Owner: Mobotix-Kacheln nur nach "Neu laden"):
// alt = EIN onError -> sofort "Kamera nicht erreichbar". Neu: Anlauf + 3 automatische Wiederholungen (neues Token),
// erst danach der Hinweis. Pausen hier verkuerzt; jeder Versuch scheitert sofort.
KAMERA_MJPEG_RETRY_MS = [5, 5, 5];
for (let i = 0; i < 4; i++) {
  for (let j = 0; j < 100 && !bilder().length; j++) { await warte(5); await ruhe(w); }
  const bi = bilder(); if (bi.length) { bi[bi.length - 1].props.onError({}); await ruhe(w); }
}
for (let j = 0; j < 4; j++) { await warte(5); await ruhe(w); }
KAMERA_MJPEG_RETRY_MS = [2000, 5000, 10000];
// Pin angepasst 20.11.2026: Knopf heisst jetzt 'Neu laden' (Owner-Vorgabe Kamera-Oberflaeche)
OUT.mjpeg_weg = {n: bilder().length, text: text(baum), neu: knopfHat(baum, 'Neu laden'), fetch: ZAEHL.fetch.length};

reset({db: {kameras: KAMS}, fein: true, fetch: {status: 200, json: {typ: 'snapshot', snapshotUrl: 'https://p/live/mx_33/snapshot.jpg?token=T2', exp: 1e12, ttl: 90}}});
w = wurzel('projektleiter'); await ruhe(w);
b = bilder();
OUT.snap = {n: b.length, src: b.length ? b[0].props.src : ''};
b[0].props.onError({}); await ruhe(w); b[0].props.onError({}); await ruhe(w);
OUT.snap_zwei = {n: bilder().length};
var b3 = bilder(); if (b3.length) { b3[0].props.onError({}); await ruhe(w); }
OUT.snap_drei = {n: bilder().length, text: text(baum)};

reset({db: {kameras: KAMS}, fein: true, fetch: {status: 200, json: {typ: 'mjpeg', mjpegUrl: 'http://p/live/mx_32/mjpeg?token=T', exp: 1e12}}});
w = wurzel('projektleiter'); await ruhe(w);
OUT.unsicher = {n: bilder().length, text: text(baum)};

reset({db: {kameras: KAMS}, fein: true, fetch: {status: 200, json: {typ: 'mjpeg', mjpegUrl: 'https://p/x', exp: 1e12}}});
w = wurzel('monteur'); await ruhe(w);
OUT.monteur = {baum: baum, fetch: ZAEHL.fetch.length};

const H = {};
H.antwort = [
  _kamStreamAntwort(200, {typ: 'mjpeg', mjpegUrl: 'https://p/m?token=x', exp: 3}, 'live'),
  _kamStreamAntwort(200, {typ: 'snapshot', snapshotUrl: 'https://p/s.jpg?token=x', exp: 3}, 'live'),
  _kamStreamAntwort(200, {typ: 'llhls', liveUrl: 'https://p/i.m3u8?token=x', webrtcUrl: 'https://p/whep', exp: 3}, 'live'),
  _kamStreamAntwort(200, {typ: 'webrtc', liveUrl: 'https://p/i.m3u8', webrtcUrl: 'https://p/whep', exp: 3}, 'live'),
  _kamStreamAntwort(200, {typ: 'rtsp', liveUrl: 'https://p/i.m3u8'}, 'live'),
  _kamStreamAntwort(200, {typ: 'mjpeg', liveUrl: 'https://p/i.m3u8'}, 'live'),
  _kamStreamAntwort(200, {typ: 'snapshot', snapshotUrl: 'javascript:alert(1)'}, 'live')];
H.modus = [_kamPlayerModus(true, true, H.antwort[0]), _kamPlayerModus(true, true, H.antwort[1]), _kamPlayerModus(true, true, H.antwort[2]),
           _kamPlayerModus(true, true, H.antwort[3]), _kamPlayerModus(false, false, H.antwort[0])];
H.aktiv = [_kamSnapshotAktiv(false, true), _kamSnapshotAktiv(true, true), _kamSnapshotAktiv(false, false), _kamSnapshotAktiv(undefined, null)];
H.surl = [_kamSnapshotUrl('https://p/s.jpg?token=x', 3), _kamSnapshotUrl('https://p/s.jpg', 'x')];
H.grund = [401, 403, 404, 500, 502, 503, 504, 400, undefined].map(_kamFehlerGrund);
H.text = KAMERA_STUB_TXT.offline;
OUT.H = H;
"""


@pytest.fixture(scope="module")
def UI2(node_exe):
    return _render_lauf(node_exe, _block(), SZENEN2)


def test_mjpeg_kachel_ist_bild_am_token_link(UI2):
    m = UI2["mjpeg"]
    assert m["n"] == 1 and m["src"] == "https://p/live/mx_32/mjpeg?token=T1"
    assert m["ref"] == "no-referrer"
    assert all(d == "none" for d in m["videoSichtbar"]), "Videoelement bleibt verborgen"
    assert "Kein Video-Backend verbunden" not in m["text"]


def test_mjpeg_abbruch_zeigt_kamera_nicht_erreichbar(UI2):
    w = UI2["mjpeg_weg"]
    assert w["n"] == 0 and "Kamera nicht erreichbar" in w["text"] and w["neu"] is True
    assert w["fetch"] == 4, "Anlauf + 3 Wiederholungen mit je neuem Token (alt: 1)"


def test_snapshot_mit_zaehler_und_erst_nach_drei_fehlern_offline(UI2):
    s = UI2["snap"]
    assert s["n"] == 1 and s["src"] == "https://p/live/mx_33/snapshot.jpg?token=T2&_=0"
    assert UI2["snap_zwei"]["n"] == 1
    assert UI2["snap_drei"]["n"] == 0 and "Kamera nicht erreichbar" in UI2["snap_drei"]["text"]


def test_http_bild_wird_nie_geladen(UI2):
    assert UI2["unsicher"]["n"] == 0 and "Video nicht verfügbar" in UI2["unsicher"]["text"]


def test_monteur_weiterhin_nichts(UI2):
    assert UI2["monteur"]["baum"] is None and UI2["monteur"]["fetch"] == 0


def test_kachel_helfer(UI2):
    H = UI2["H"]
    a = H["antwort"]
    assert a[0]["ok"] and a[0]["typ"] == "mjpeg" and a[0]["mjpegUrl"] and not a[0]["liveUrl"] and not a[0]["webrtcUrl"]
    assert a[1]["ok"] and a[1]["typ"] == "snapshot" and a[1]["snapshotUrl"]
    assert a[2]["ok"] and a[2]["typ"] == "llhls" and a[2]["webrtcUrl"] == "", "llhls nutzt nie WHEP"
    assert a[3]["ok"] and a[3]["typ"] == "webrtc" and a[3]["webrtcUrl"]
    assert a[4] == {"ok": False, "grund": "fehler"} and a[5] == {"ok": False, "grund": "fehler"} and a[6] == {"ok": False, "grund": "fehler"}
    assert H["modus"] == ["mjpeg", "snapshot", "hls", "webrtc", "mjpeg"]
    assert H["aktiv"] == [True, False, False, True]
    assert H["surl"] == ["https://p/s.jpg?token=x&_=3", "https://p/s.jpg?_=0"]
    assert H["grund"] == ["kein_zugriff", "kein_zugriff", "offline", "offline", "offline", "offline", "offline", "fehler", "fehler"]
    assert H["text"] == "Kamera nicht erreichbar"


def test_snapshot_takt_haelt_an_wenn_verborgen():
    b = _block()
    i = b.index("function takten(){")
    teil = b[i:b.index("function schliessen(){", i)]
    assert "document.hidden===true" in teil and "_kamSnapshotAktiv(versteckt,imBild.current)" in teil
    assert "KAMERA_SNAPSHOT_MS" in teil and "var KAMERA_SNAPSHOT_MS=2000;" in b
    assert "new IntersectionObserver(" in b and "io.disconnect()" in b
    assert "clearInterval(tickRef.current)" in b


def test_umkehrprobe_https_pflicht_fuer_mjpeg(node_exe):
    b = _block()
    alt = "if(typ==='mjpeg'){if(!_kamIstHttps(j.mjpegUrl))return {ok:false,grund:'fehler'};"
    assert b.count(alt) == 1
    R2 = _render_lauf(node_exe, b.replace(alt, "if(typ==='mjpeg'){", 1), SZENEN2)
    assert R2["unsicher"]["n"] == 1, "Umkehrprobe: http-Bild-Riegel waere blind"


def test_umkehrprobe_snapshot_schwelle(node_exe):
    b = _block()
    alt = "fehlerRef.current>=3"
    assert b.count(alt) == 1
    R2 = _render_lauf(node_exe, b.replace(alt, "fehlerRef.current>=1", 1), SZENEN2)
    assert R2["snap_zwei"]["n"] == 0


def test_block_hausregeln_phase2():
    b = _block()
    assert "`" not in b and "86400000" not in b and "?." not in b.replace("'?'", "")
    assert not IP_RE.search(b)
    assert not re.search(r"fontSize:\s*\d", b)


# ── TEIL D: Seed-Entwurf ──────────────────────────────────────────────────────
def _ohne_kommentare(sql):
    return "\n".join(z.split("--", 1)[0] for z in sql.replace("\r\n", "\n").split("\n"))


def test_seed_sieben_kameras_ohne_ip_und_kennwort():
    s = _lies(SEED)
    assert s.startswith("-- IDEMPOTENT")
    assert "ENTWURF" in s and "NICHT eingespielt" in s
    assert not IP_RE.search(s), "keine IP im Seed (Zuordnung nur in go2rtc auf dem Host)"
    assert not re.search(r"(password|passwort|kennwort|rtsp://|http://)\s*[:=]?", _ohne_kommentare(s), re.I)
    code = _ohne_kommentare(s)
    assert "cascade" not in code.lower()
    streams = re.findall(r"\('(kam_0\d)',\s*'(g3_\d+|mx_\d+)',\s*(null|'[a-z0-9_]+'),\s*'(webrtc|mjpeg|snapshot|llhls)'\)", code)
    assert len(streams) == 7, streams
    assert sorted(x[1] for x in streams) == ["g3_37", "g3_38", "g3_39", "g3_61", "mx_32", "mx_33", "mx_36"]
    assert all(x[3] == "webrtc" for x in streams if x[1].startswith("g3_"))
    assert all(x[3] in ("mjpeg", "snapshot") for x in streams if x[1].startswith("mx_"))
    kams = re.findall(r"\('(kam_0\d)',\s*'([^']+)',\s*'([^']+)',\s*'([^']+)',\s*'([^']+)',\s*(true|false),\s*(\d+)\)", code)
    assert len(kams) == 7 and all(k[6] == "3" for k in kams)
    assert "on conflict (id) do nothing" in code and "on conflict (kamera_id) do nothing" in code
    assert "stream_typ" in code and "raise exception" in code


def test_doku_phase2():
    d = _lies(DOKU2)
    for teil in ("stream_typ", "mjpeg", "snapshot", "kamera-proxy-auth", "KAMERAS_PILOT_SEED_ENTWURF.sql",
                 "epk-kamera-pilot", "Monteur", "Offene Fragen"):
        assert teil in d, teil
    assert not IP_RE.search(d)
