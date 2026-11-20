# -*- coding: utf-8 -*-
"""Kamera-Gateway auf der QNAP (20.11.2026): Einsatzdateien unter tools/kamera-proxy-auth/qnap/.

TEIL A: Token-Nachweis - die Edge Function (logic.ts) signiert, der UNVERAENDERTE Pruefer (verify.mjs + token.mjs)
        mit der Kopf-Konfiguration aus qnap/docker-compose.yml nimmt jede ausgegebene Adresse an (Live WHEP/HLS/
        Einzelbild, MJPEG, Aufzeichnungsbereich); falsches Secret -> 401, verfaelschter Bereich -> 403.
TEIL B: Statische Pruefung von Caddyfile, Dockerfile, package.json, docker-compose.yml, ENV.md mit Umkehrproben.
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
Q = os.path.join(AUTH, "qnap")
LOGIC = os.path.join(WURZEL, "supabase", "functions", "kamera-stream", "logic.ts")
IP_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")


def _lies(p):
    with open(p, encoding="utf-8") as fh:
        return fh.read().replace("\r\n", "\n")


def _mut(text, alt, neu):
    assert text.count(alt) >= 1, alt
    return text.replace(alt, neu, 1)


def _compose_env(dienst):
    c = _lies(os.path.join(Q, "docker-compose.yml"))
    i = c.index("  " + dienst + ":\n")
    j = c.find("\n  ", i + 3)
    teil = c[i:]
    nxt = re.search(r"\n  [a-z][a-z0-9_-]*:\n", teil[3:])
    teil = teil[: nxt.start() + 3] if nxt else teil
    return dict(re.findall(r"^\s+- ([A-Z_]+)=(.*)$", teil, re.M))


# ── TEIL A: Token-Nachweis ──────────────────────────────────────────────────
HARNESS = r"""
import * as L from "./logic.ts";
import * as TM from "./token.mjs";
import * as VF from "./verify.mjs";
const SECRET = "t".repeat(40);
const FALSCH = "f".repeat(40);
const CFG = VF.ladeKopfConfig(%(env)s);
const JETZT = Date.UTC(2026, 10, 23, 9, 0, 0);
const BE = {hochregal01: {stream_name: "hochregal01", aufzeichnung_quelle: "hochregal01", stream_typ: "webrtc"},
            mob32: {stream_name: "mob32", aufzeichnung_quelle: null, stream_typ: "mjpeg"}};
async function ruf(body) {
  const deps = {
    env: (n) => ({KAMERA_TOKEN_SECRET: SECRET, KAMERA_GATEWAY_BASE: "https://gateway.example.test"})[n],
    now: () => JETZT, nonce: () => "n1",
    authUser: async () => "auth-admin",
    ladeNutzer: async () => ({id: "u1", role: "admin", active: 1, locked: false}),
    darfSehen: async () => true, darfSehenBereich: async () => true,
    ladeBackend: async (k) => BE[k] || null,
  };
  const res = await L.bearbeite(new Request("https://fn.example.test/kamera-stream", {method: "POST",
    headers: {"content-type": "application/json", origin: "https://epkolar.github.io",
              authorization: "Bearer jwt_admin_0123456789abcdef"}, body: JSON.stringify(body)}), deps);
  return await res.json();
}
async function pruef(url, methode, secret, extra) {
  const u = new URL(url);
  const h = Object.assign({"x-forwarded-uri": u.pathname + u.search, "x-forwarded-method": methode}, extra || {});
  const e = await VF.entscheide({method: "GET", url: "/pruefen", headers: h}, secret, JETZT, CFG);
  return {status: e.status, von: e.headers["X-Kamera-Von"] || "", stream: e.headers["X-Kamera-Stream"] || ""};
}
const OUT = {cfg: !!CFG};
const w = await ruf({kamera_id: "hochregal01"});
const m = await ruf({kamera_id: "mob32"});
const r = await ruf({kamera_id: "hochregal01", scope: "aufzeichnung", geraet: "pc",
  von: new Date(JETZT - 3600 * 1000).toISOString(), bis: new Date(JETZT).toISOString()});
OUT.whep = await pruef(w.webrtcUrl, "POST", SECRET);
OUT.hls = await pruef(w.liveUrl, "GET", SECRET);
OUT.bild = await pruef(w.snapshotUrl, "GET", SECRET);
OUT.mjpeg = await pruef(m.mjpegUrl, "GET", SECRET);
OUT.mjpeg_typ = m.typ;
const tok = decodeURIComponent(/token=([^&]+)/.exec(w.liveUrl)[1]);
OUT.hls_teil_cookie = await pruef("https://g/live/hochregal01/hls/segment.ts?id=abc", "GET", SECRET, {cookie: "kam_t=" + tok});
OUT.hls_teil_ohne = await pruef("https://g/live/hochregal01/hls/segment.ts?id=abc", "GET", SECRET);
OUT.rec = await pruef(r.aufzeichnungUrl, "GET", SECRET);
OUT.rec_soll_von = String(r.von);
OUT.rec_verfaelscht = await pruef(r.aufzeichnungUrl.replace("&von=" + r.von, "&von=" + (r.von - 60)), "GET", SECRET);
OUT.falsch_secret = await pruef(w.webrtcUrl, "POST", FALSCH);
OUT.falscher_stream = await pruef(w.snapshotUrl.replace("/hochregal01/", "/verkauf02/"), "GET", SECRET);
OUT.fremdkopf = await pruef(w.snapshotUrl, "GET", SECRET, {"x-original-uri": "/live/hochregal01/snapshot.jpg"});
// token.mjs signiert (gleicher Vertrag) -> verify.mjs nimmt an; mit falschem Secret signiert -> 401
const p = {v: 1, k: "cam39", s: "cam39", u: "u1", sc: "live", iat: Math.floor(JETZT / 1000), exp: Math.floor(JETZT / 1000) + 90, n: "x"};
OUT.tm = await pruef("https://g/live/cam39/whep?token=" + await TM.signiere(SECRET, p), "POST", SECRET);
OUT.tm_falsch = await pruef("https://g/live/cam39/whep?token=" + await TM.signiere(FALSCH, p), "POST", SECRET);
const pr = Object.assign({}, p, {sc: "aufzeichnung", von: Math.floor(JETZT / 1000) - 600, bis: Math.floor(JETZT / 1000) - 60});
OUT.tm_rec = await pruef("https://g/aufzeichnung/cam39?token=" + await TM.signiere(SECRET, pr) + "&von=" + pr.von + "&bis=" + pr.bis, "GET", SECRET);
console.log(JSON.stringify(OUT));
"""


def _token_lauf(node_exe, verify_src=None):
    env = _compose_env("kamera-auth")
    cfg = {"KAMERA_AUTH_URI_HEADER": env["KAMERA_AUTH_URI_HEADER"], "KAMERA_AUTH_METHOD_HEADER": env["KAMERA_AUTH_METHOD_HEADER"]}
    with tempfile.TemporaryDirectory() as d:
        for name, quelle, src in (("logic.ts", LOGIC, None), ("token.mjs", os.path.join(AUTH, "token.mjs"), None),
                                  ("verify.mjs", os.path.join(AUTH, "verify.mjs"), verify_src)):
            with io.open(os.path.join(d, name), "w", encoding="utf-8", newline="\n") as f:
                f.write(src if src is not None else _lies(quelle))
        with io.open(os.path.join(d, "h.mjs"), "w", encoding="utf-8", newline="\n") as f:
            f.write(HARNESS % {"env": json.dumps(cfg)})
        r = subprocess.run([node_exe, "--experimental-strip-types", "--no-warnings", "h.mjs"], cwd=d,
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=EPK_TEST_TIMEOUT)
    assert r.returncode == 0, r.stderr[-3000:]
    return json.loads(r.stdout.strip().splitlines()[-1])


@pytest.fixture(scope="module")
def T(node_exe):
    return _token_lauf(node_exe)


def test_edge_signiert_pruefer_nimmt_an(T):
    assert T["cfg"] is True
    for k in ("whep", "hls", "bild", "mjpeg", "hls_teil_cookie"):
        assert T[k]["status"] == 204, k
    assert T["mjpeg_typ"] == "mjpeg" and T["mjpeg"]["stream"] == "mob32"
    assert T["whep"]["stream"] == "hochregal01"


def test_aufzeichnungsbereich_signiert(T):
    assert T["rec"]["status"] == 204 and T["rec"]["von"] == T["rec_soll_von"]
    assert T["rec_verfaelscht"]["status"] == 403


def test_umkehrproben_token(T):
    assert T["falsch_secret"]["status"] == 401
    assert T["falscher_stream"]["status"] == 403
    assert T["fremdkopf"]["status"] == 403
    assert T["hls_teil_ohne"]["status"] == 401


def test_token_mjs_und_pruefer_gleicher_vertrag(T):
    assert T["tm"]["status"] == 204 and T["tm_rec"]["status"] == 204
    assert T["tm_falsch"]["status"] == 401


def test_umkehrprobe_pruefer_ohne_streambindung(node_exe):
    s = _mut(_lies(os.path.join(AUTH, "verify.mjs")), "{ s: ziel.s, sc: ziel.sc }", "{}")
    assert _token_lauf(node_exe, s)["falscher_stream"]["status"] == 204, "Umkehrprobe: Streambindung waere blind"


def test_pruefer_ohne_abhaengigkeiten():
    for f in ("verify.mjs", "token.mjs"):
        imp = re.findall(r"^import .* from \"([^\"]+)\";", _lies(os.path.join(AUTH, f)), re.M)
        assert all(x.startswith("node:") or x == "./token.mjs" for x in imp), (f, imp)
    pj = json.loads(_lies(os.path.join(Q, "package.json")))
    assert pj["dependencies"] == {} and "devDependencies" not in pj and pj["type"] == "module"


# ── TEIL B: statische Pruefung ──────────────────────────────────────────────
def _ohne_kommentare(text):
    return "\n".join(l for l in text.split("\n") if not l.strip().startswith("#"))


def _bloecke(caddy):
    """handle-Bloecke (Matcher, Inhalt) per Klammerzaehlung."""
    out = []
    for m in re.finditer(r"^\thandle( [^{\n]*)?\{\n", caddy, re.M):
        i = m.end()
        tiefe = 1
        j = i
        while tiefe and j < len(caddy):
            if caddy[j] == "{":
                tiefe += 1
            elif caddy[j] == "}":
                tiefe -= 1
            j += 1
        out.append(((m.group(1) or "").strip(), caddy[i:j - 1]))
    return out


PFLICHT_KOPF = ("header_up -X-Original-URI", "header_up -X-Original-Method",
                "header_up X-Forwarded-Uri {http.request.orig_uri}", "header_up X-Forwarded-Method {http.request.orig_method}")


def pruefe_caddy(text):
    b = []
    c = _ohne_kommentare(text)
    if [x for x in IP_RE.findall(text) if x not in ("127.0.0.1", "0.0.0.0")]:
        b.append("IP-Adresse")
    if not re.search(r"^\ttls internal$", c, re.M):
        b.append("tls internal fehlt")
    if re.search(r"^\s*tls /", c, re.M):
        b.append("Zertifikat-Datei aktiv (nur auskommentiert erlaubt)")
    # Port konfigurierbar (QTS belegt 443): Site = {$QNAP_LAN_IP}:{$GATEWAY_PORT}
    if not re.search(r"^https://\{\$QNAP_LAN_IP\}:\{\$GATEWAY_PORT\} \{$", c, re.M):
        b.append("Site ohne {$QNAP_LAN_IP}:{$GATEWAY_PORT}")
    if "kameras.ep-kolar.at" not in text:
        b.append("DNS-Alternative fehlt")
    if not re.search(r"request>uri query \{\s*delete token\s*\}", c):
        b.append("Token im Protokoll")
    for o in re.findall(r"Access-Control-Allow-Origin \"([^\"]+)\"", c):
        if o != "https://epkolar.github.io":
            b.append("CORS fremd: " + o)
    bl = _bloecke(c)
    if not bl or bl[-1][0] != "" or bl[-1][1].strip() != "respond 404":
        b.append("Catch-all 404 fehlt/nicht zuletzt")
    for matcher, inhalt in bl:
        if "reverse_proxy" not in inhalt:
            continue
        i_fa = inhalt.find("forward_auth kamera-auth:9099 {")
        i_rw = inhalt.find("rewrite")
        i_rp = inhalt.find("reverse_proxy")
        if i_fa < 0 or not (i_fa < i_rp) or (i_rw >= 0 and not i_fa < i_rw) or "route {" not in inhalt:
            b.append("forward_auth nicht vor rewrite/reverse_proxy: " + matcher)
        for k in PFLICHT_KOPF:
            if k not in inhalt:
                b.append("Kopf-Regel fehlt (" + k + "): " + matcher)
        for ziel in re.findall(r"reverse_proxy (\S+)", inhalt):
            if ziel != "{$QNAP_LAN_IP}:1984":
                b.append("reverse_proxy-Ziel: " + ziel)
    if re.search(r"handle /api|path /api|\^/api", c):
        b.append("go2rtc /api offen")
    if re.search(r"handle[^\n]*aufzeichnung|\^/aufzeichnung", c):
        b.append("Aufzeichnung offen")
    # Routen fuer genau die Adressen der Edge Function
    for probe in ("/live/hochregal01/whep", "/live/mob32/mjpeg", "/live/cam39/snapshot.jpg", "/live/verkauf02/index.m3u8",
                  "/live/elektrolager03/hls/segment.ts"):
        treffer = [m for m in re.findall(r"path_regexp \w+ (\S+)", c) if re.match(m, probe)]
        if len(treffer) != 1:
            b.append("keine eindeutige Route fuer " + probe)
    return b


def pruefe_docker(text):
    b = []
    c = _ohne_kommentare(text)
    if not re.search(r"^FROM node:\d+\.\d+\.\d+-alpine\d+\.\d+$", c, re.M):
        b.append("Node-Image nicht fest gepinnt")
    u = re.findall(r"^USER (\S+)$", c, re.M)
    if not u or u[-1] in ("root", "0"):
        b.append("laeuft als root")
    kopien = re.findall(r"^COPY (?:--\S+ )*(\S+) ", c, re.M)
    if sorted(kopien) != sorted(["qnap/package.json", "token.mjs", "verify.mjs"]):
        b.append("kopiert mehr/anderes als den Pruefer: %s" % kopien)
    if re.search(r"npm (install|ci)", c):
        b.append("npm install")
    return b


def pruefe_compose(text):
    b = []
    c = _ohne_kommentare(text)
    if [x for x in IP_RE.findall(text) if x not in ("127.0.0.1", "0.0.0.0")]:
        b.append("IP-Adresse")
    dienste = dict((m.group(1), m.group(2)) for m in re.finditer(r"^  ([a-z0-9_-]+):\n((?:    .*\n|\n)*)", c + "\n", re.M))
    if sorted(dienste) != ["caddy", "kamera-auth"]:
        b.append("Dienste != caddy + kamera-auth: %s" % sorted(dienste))
    if "network_mode" in c:
        b.append("Host-Netz statt Bruecke")
    if "frigate" in c.lower():
        b.append("startet frigate")
    ka = dienste.get("kamera-auth", "")
    if "ports:" in ka:
        b.append("kamera-auth veroeffentlicht")
    if "KAMERA_AUTH_PORT=9099" not in ka:
        b.append("Pruefer-Port nicht 9099")
    ports = re.findall(r"^\s+- \"([^\"]+)\"$", dienste.get("caddy", "").split("environment:")[0], re.M)
    if ports != ["${QNAP_LAN_IP:?QNAP_LAN_IP fehlt}:${GATEWAY_PORT:-8443}:${GATEWAY_PORT:-8443}"]:
        b.append("Caddy-ports nicht genau <QNAP_LAN_IP>:<GATEWAY_PORT>:<GATEWAY_PORT>: %s" % ports)
    if "GATEWAY_PORT=${GATEWAY_PORT:-8443}" not in dienste.get("caddy", ""):
        b.append("GATEWAY_PORT fehlt in der caddy-Umgebung")
    if "KAMERA_AUTH_URI_HEADER=x-forwarded-uri" not in c or "KAMERA_AUTH_METHOD_HEADER=x-forwarded-method" not in c:
        b.append("Kopf-Paar fehlt")
    if not re.search(r"KAMERA_TOKEN_SECRET=\$\{KAMERA_TOKEN_SECRET:\?", c):
        b.append("Secret nicht aus der Umgebung/Pflicht")
    if "read_only: true" not in c:
        b.append("kamera-auth nicht read_only")
    return b


def pruefe_env(text):
    b = []
    if [x for x in IP_RE.findall(text) if x not in ("127.0.0.1", "0.0.0.0")]:
        b.append("IP-Adresse")
    if re.search(r"^[A-Z_]{4,}=\S+", text, re.M):
        b.append("Wert statt Name")
    # jede Umgebungsvariable, die verify.mjs liest, muss in ENV.md stehen (gemessen, nicht abgeschrieben)
    gelesen = sorted(set(re.findall(r"\benv\.([A-Z][A-Z0-9_]+)", _lies(os.path.join(AUTH, "verify.mjs")))))
    for n in gelesen + ["QNAP_LAN_IP", "GATEWAY_PORT", "8443", "8555", "x-forwarded-uri", "x-forwarded-method", "nie auf privaten Handys"]:
        if n not in text:
            b.append("ENV.md ohne " + n)
    return b


def test_env_kennt_alle_namen_aus_verify():
    gelesen = set(re.findall(r"\benv\.([A-Z][A-Z0-9_]+)", _lies(os.path.join(AUTH, "verify.mjs"))))
    assert {"KAMERA_TOKEN_SECRET", "KAMERA_TOKEN_SECRET_FILE", "KAMERA_AUTH_HOST", "KAMERA_AUTH_PORT", "KAMERA_AUTH_LOG",
            "KAMERA_AUTH_URI_HEADER", "KAMERA_AUTH_METHOD_HEADER"} <= gelesen


def test_caddy_sauber():
    assert pruefe_caddy(_lies(os.path.join(Q, "Caddyfile"))) == []


def test_docker_sauber():
    assert pruefe_docker(_lies(os.path.join(Q, "Dockerfile"))) == []


def test_compose_sauber():
    assert pruefe_compose(_lies(os.path.join(Q, "docker-compose.yml"))) == []


def test_env_sauber():
    assert pruefe_env(_lies(os.path.join(Q, "ENV.md"))) == []


def _mjpeg_block_ohne_forward_auth(s):
    i = s.index("handle @mjpeg {")
    j = s.index("forward_auth", i)
    k = s.index("}", j)
    return s[:j] + s[k + 1:]


@pytest.mark.parametrize("verderben,erwartet", [
    (_mjpeg_block_ohne_forward_auth, "forward_auth nicht vor"),
    (lambda s: _mut(s, "\thandle {\n\t\trespond 404\n\t}", ""), "Catch-all"),
    (lambda s: _mut(s, "\ttls internal\n", "\t# tls internal\n"), "tls internal"),
    (lambda s: _mut(s, "\t\t\t\theader_up -X-Original-URI\n", ""), "Kopf-Regel"),
    (lambda s: _mut(s, "reverse_proxy {$QNAP_LAN_IP}:1984 {", "reverse_proxy go2rtc:1984 {"), "reverse_proxy-Ziel"),
    (lambda s: _mut(s, "\t#   tls /zertifikate/kamera.crt", "\ttls /zertifikate/kamera.crt"), "Zertifikat-Datei aktiv"),
    (lambda s: _mut(s, "{$QNAP_LAN_IP}", "." .join(("192", "168", "33", "95"))), "IP-Adresse"),
    (lambda s: _mut(s, "\t\t\t\t\tdelete token\n", ""), "Token im Protokoll"),
    (lambda s: _mut(s, "handle /gesund {", "handle /api/streams {\n\t\trespond 200\n\t}\n\thandle /gesund {"), "/api"),
    (lambda s: _mut(s, "Access-Control-Allow-Origin \"https://epkolar.github.io\"", "Access-Control-Allow-Origin \"*\""), "CORS fremd"),
])
def test_umkehrprobe_caddy(verderben, erwartet):
    assert any(erwartet in x for x in pruefe_caddy(verderben(_lies(os.path.join(Q, "Caddyfile"))))), erwartet


@pytest.mark.parametrize("alt,neu,erwartet", [
    ("USER node", "USER root", "root"),
    ("USER node\n", "", "root"),
    ("FROM node:22.11.0-alpine3.20", "FROM node:lts-alpine", "gepinnt"),
    ("COPY --chown=root:root verify.mjs ./verify.mjs", "COPY --chown=root:root . ./", "kopiert"),
])
def test_umkehrprobe_docker(alt, neu, erwartet):
    assert any(erwartet in x for x in pruefe_docker(_mut(_lies(os.path.join(Q, "Dockerfile")), alt, neu)))


@pytest.mark.parametrize("alt,neu,erwartet", [
    ("    expose: [\"9099\"]\n", "    ports:\n      - \"9099:9099\"\n", "kamera-auth veroeffentlicht"),
    ("      - \"${QNAP_LAN_IP:?QNAP_LAN_IP fehlt}:${GATEWAY_PORT:-8443}:${GATEWAY_PORT:-8443}\"", "      - \"443:443\"", "Caddy-ports"),
    ("      - GATEWAY_PORT=${GATEWAY_PORT:-8443}\n", "", "GATEWAY_PORT fehlt"),
    ("services:\n", "services:\n  go2rtc:\n    image: alexxit/go2rtc\n", "Dienste"),
    ("    restart: unless-stopped\n    read_only", "    network_mode: host\n    restart: unless-stopped\n    read_only", "Host-Netz"),
    ("KAMERA_AUTH_URI_HEADER=x-forwarded-uri", "KAMERA_AUTH_URI_HEADER=x-original-uri", "Kopf-Paar"),
    ("    read_only: true\n", "", "read_only"),
])
def test_umkehrprobe_compose(alt, neu, erwartet):
    assert any(erwartet in x for x in pruefe_compose(_mut(_lies(os.path.join(Q, "docker-compose.yml")), alt, neu)))


def test_umkehrprobe_env():
    e = _lies(os.path.join(Q, "ENV.md"))
    assert any("Wert" in x for x in pruefe_env(e + "\nKAMERA_TOKEN_SECRET=abcdefgh\n"))
