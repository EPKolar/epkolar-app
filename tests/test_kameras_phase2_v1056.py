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
  const calls = {darf: 0, backend: 0};
  const deps = {
    env: (n) => ({KAMERA_TOKEN_SECRET: SECRET, KAMERA_BACKEND_BASE: BASE})[n],
    now: () => MO_10, nonce: () => "n1",
    authUser: async (jwt) => "auth-" + /^jwt_([a-z]+)_/.exec(jwt)[1],
    ladeNutzer: async (uid) => USERS[uid.slice(5)] || null,
    darfSehen: async () => { calls.darf++; return darf !== false; },
    ladeBackend: async (k) => { calls.backend++; return BACKEND[k] || null; },
  };
  const body = {kamera_id: kamera};
  if (scope) { body.scope = scope; body.geraet = "pc"; }
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
      if (key === "aufzeichnungUrl") uri += "&von=" + (Math.floor(MO_10 / 1000) - 3600) + "&bis=" + Math.floor(MO_10 / 1000);
      const methode = key === "webrtcUrl" ? "POST" : "GET";
      const e = await VF.entscheide({method: "GET", url: "/pruefen", headers: {"x-forwarded-uri": uri, "x-forwarded-method": methode}}, SECRET, MO_10);
      out.proxy[key] = {status: e.status, art: (VF.pfadArt(u.pathname) || {}).art || null};
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
  const e = await VF.entscheide({method: "GET", url: "/pruefen", headers: h}, VEK.secret, v.now_ms || VEK.now_ms);
  R.vek.anfragen.push({name: v.name, soll: v.status, ist: e.status, cookie: !!e.headers["Set-Cookie"], sollCookie: !!v.cookie,
    cookieText: e.headers["Set-Cookie"] || "", info: JSON.stringify(e.info), kopf: e.headers});
}
// nginx-Weg: X-Original-URI / X-Original-Method statt X-Forwarded-*
const g = VEK.token[0].token;
R.nginx = (await VF.entscheide({method: "GET", url: "/pruefen", headers: {"x-original-uri": "/live/g3_37/whep?token=" + g, "x-original-method": "POST"}}, VEK.secret, VEK.now_ms)).status;
R.direkt = (await VF.entscheide({method: "GET", url: "/live/g3_37/mjpeg?token=" + g, headers: {}}, VEK.secret, VEK.now_ms)).status;
R.doppelkopf = (await VF.entscheide({method: "GET", url: "/x", headers: {"x-forwarded-uri": ["/live/g3_37/mjpeg?token=" + g, "/a"]}}, VEK.secret, VEK.now_ms)).status;
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
    assert set(j) == {"typ", "webrtcUrl", "liveUrl", "exp", "ttl"}
    assert e["proxy"] == {"webrtcUrl": {"status": 204, "art": "whep"}, "liveUrl": {"status": 204, "art": "hls"}}


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
    assert e["status"] == 200 and set(e["json"]) == {"aufzeichnungUrl", "exp", "ttl"}
    assert e["proxy"]["aufzeichnungUrl"]["status"] == 204
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
                    "fremdes_secret", "payload_getauscht", "punktpunkt"):
        assert pflicht in namen, pflicht


def test_hls_cookie_eng_gebunden(R):
    c = [v for v in R["vek"]["anfragen"] if v["name"] == "hls_index"][0]["cookieText"]
    assert c.startswith("kam_t=") and "Path=/live/g3_37/;" in c and "HttpOnly" in c and "Secure" in c
    assert re.search(r"Max-Age=(\d+);", c) and 0 < int(re.search(r"Max-Age=(\d+);", c).group(1)) <= 120


def test_nginx_kopf_direktaufruf_und_doppelter_kopf(R):
    assert R["nginx"] == 204
    assert R["direkt"] == 204
    assert R["doppelkopf"] == 403


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
    env = dict(os.environ, KAMERA_TOKEN_SECRET=vek["secret"], KAMERA_AUTH_PORT=str(port), KAMERA_AUTH_LOG="1")
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
        assert _hole("http://127.0.0.1:%d/pruefen" % port, {"X-Forwarded-Uri": "/live/g3_37/mjpeg?token=" + tok}) == 401
        assert _hole("http://127.0.0.1:%d/pruefen" % port, {"X-Forwarded-Uri": "/api/streams"}) == 403
    finally:
        pr.terminate()
        out, err = pr.communicate(timeout=10)
    assert tok not in out and tok not in err
    assert tok.split(".")[0] not in out
    assert '"status":401' in out and '"status":403' in out


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

reset({db: {kameras: KAMS}, fein: true, fetch: {status: 200, json: {typ: 'mjpeg', mjpegUrl: 'https://p/live/mx_32/mjpeg?token=T1', exp: 1e12, ttl: 90}}});
let w = wurzel('projektleiter'); await ruhe(w);
let b = bilder();
OUT.mjpeg = {n: b.length, src: b.length ? b[0].props.src : '', ref: b.length ? b[0].props.referrerPolicy : '', text: text(baum),
             videoSichtbar: videos().map(function (v) { return v.props.style.display; })};
b[0].props.onError({}); await ruhe(w);
OUT.mjpeg_weg = {n: bilder().length, text: text(baum), neu: knopfHat(baum, 'Neu verbinden')};

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
