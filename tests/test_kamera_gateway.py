# -*- coding: utf-8 -*-
"""Kamera-Gateway (QNAP, 20.11.2026) - App-Seite fuer go2rtc hinter Caddy + kamera-auth.

TEIL A: Edge Function: EINE Gateway-Adresse. KAMERA_GATEWAY_BASE bevorzugt, KAMERA_BACKEND_BASE als Rueckfall,
        nur https, fehlend -> 503 (fail closed). webrtc liefert zusaetzlich snapshotUrl (gleiches Token).
TEIL B: App-Kachel: WHEP zuerst, Einzelbild-Rueckfall bei WHEP-/ICE-Fehler oder ohne WebRTC/HLS, nie bei 401/403;
        keine RTSP-Adresse im Browser-Code.
TEIL C: SQL-Seed fuer die 4 LIVE-Kameras (+ Mobotix-Block AUS): Probe, Anwendung, Ruecknahme - statisch, nichts
        wird eingespielt. Pilot-Seed als SUPERSEDED markiert.
TEIL D: Doku-Reihenfolge, Vorlagen ausserhalb des Repos (falls vorhanden), Deploy-Nachweis (sha256 == Repo).
Jede Pruefung liefert Befunde; echte Dateien -> leer, verdorbene Abschriften -> nicht leer (Umkehrproben).
"""
import hashlib
import io
import json
import os
import re
import subprocess
import tempfile

import pytest

from conftest import EPK_TEST_TIMEOUT
from test_kameras_phase1_v1055 import _block, _render_lauf

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FN_DIR = os.path.join(WURZEL, "supabase", "functions", "kamera-stream")
LOGIC = os.path.join(FN_DIR, "logic.ts")
INDEX_TS = os.path.join(FN_DIR, "index.ts")
SQL_DIR = os.path.join(WURZEL, "sql")
SEED = os.path.join(SQL_DIR, "KAMERA_GATEWAY_SEED_ENTWURF.sql")
PROBE = os.path.join(SQL_DIR, "KAMERA_GATEWAY_SEED_PROBE.sql")
RUECK = os.path.join(SQL_DIR, "KAMERA_GATEWAY_SEED_RUECKNAHME.sql")
DOKU = os.path.join(WURZEL, "docs", "kameras", "PILOT_HEUTE.md")
TESTLISTE = os.path.join(WURZEL, "docs", "kameras", "PILOT_TESTLISTE.md")
VORLAGE = os.path.join(os.path.dirname(WURZEL), "epk-kamera-pilot", "pilot-heute")

# Deploy-Nachweis (MCP deploy_edge_function aus dem committeten Stand, danach get_edge_function verglichen):
# sha256 der Dateien mit LF-Zeilenenden. Aendert sich index.ts/logic.ts -> Redeploy + diese Werte nachziehen.
DEPLOYT_VERSION = 3
DEPLOYT_INDEX_SHA = "ef5b7b6ad56c1df9e3af40acc9b9a03ee569c06ea53b541a0b72988a4b366a47"
DEPLOYT_LOGIC_SHA = "eae7dde449fae598df03f7d1acc18fd478a4548fd23439576e41a6180dc5ec75"

# Streamnamen = go2rtc auf der QNAP (Entscheid GF 20.11.2026) = kameras.id = kamera_backend.stream_name
G3 = ("hochregal01", "verkauf02", "elektrolager03", "cam39")
MOB = ("mob32", "mob33", "mob34", "mob35", "mob36")
IP_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")


def _lies(p):
    with open(p, encoding="utf-8") as fh:
        return fh.read().replace("\r\n", "\n")


def _mut(text, alt, neu):
    assert text.count(alt) == 1, alt
    return text.replace(alt, neu, 1)


# ── TEIL A: Edge Function ───────────────────────────────────────────────────
HARNESS = r"""
import * as L from "./logic.ts";
const FAELLE = %(faelle)s;
const SECRET = "s".repeat(40);
const OUT = {basis: {}, live: {}, einr: {}};
for (const [name, env] of Object.entries(FAELLE)) {
  OUT.basis[name] = L.backendBasis((n) => env[n]);
  const deps = (body) => ({
    env: (n) => Object.assign({KAMERA_TOKEN_SECRET: SECRET}, env)[n],
    now: () => Date.UTC(2026, 10, 23, 9, 0, 0), nonce: () => "n1",
    authUser: async () => "auth-admin",
    ladeNutzer: async () => ({id: "u1", role: "admin", active: 1, locked: false}),
    darfSehen: async () => true, darfSehenBereich: async () => true,
    ladeBackend: async (k) => ({stream_name: k, aufzeichnung_quelle: null, stream_typ: "webrtc"}),
  });
  const ruf = async (body) => {
    const res = await L.bearbeite(new Request("https://fn.example.test/kamera-stream", {method: "POST",
      headers: {"content-type": "application/json", origin: "https://epkolar.github.io",
                authorization: "Bearer jwt_admin_0123456789abcdef"}, body: JSON.stringify(body)}), deps(body));
    return {status: res.status, json: JSON.parse(await res.text())};
  };
  OUT.live[name] = await ruf({kamera_id: "hochregal01"});
  OUT.einr[name] = await ruf({pruefen: "einrichtung"});
}
console.log(JSON.stringify(OUT));
"""

GW = "https://gateway.example.test"
ALT = "https://alt.example.test"
IP4 = ".".join(("192", "168", "33", "95"))
FAELLE = {
    "nur_gateway": {"KAMERA_GATEWAY_BASE": GW},
    "beide": {"KAMERA_GATEWAY_BASE": GW, "KAMERA_BACKEND_BASE": ALT},
    "nur_alt": {"KAMERA_BACKEND_BASE": ALT},
    "gateway_leer": {"KAMERA_GATEWAY_BASE": "", "KAMERA_BACKEND_BASE": ALT},
    "gateway_blank": {"KAMERA_GATEWAY_BASE": "   ", "KAMERA_BACKEND_BASE": ALT},
    "gateway_http": {"KAMERA_GATEWAY_BASE": "http://gateway.example.test", "KAMERA_BACKEND_BASE": ALT},
    "gateway_kaputt": {"KAMERA_GATEWAY_BASE": "https://gate way.example.test", "KAMERA_BACKEND_BASE": ALT},
    "alt_http": {"KAMERA_BACKEND_BASE": "http://alt.example.test"},
    "gateway_schraeg": {"KAMERA_GATEWAY_BASE": GW + "//"},
    "gateway_port_pfad": {"KAMERA_GATEWAY_BASE": GW + ":8443/kam"},
    "keins": {},
    # Variante ohne DNS (Caddy tls internal, IP-Zertifikat): IPv4-Host mit/ohne Port. IP zusammengesetzt (keine IP im Repo).
    "ip": {"KAMERA_GATEWAY_BASE": "https://" + IP4},
    "ip_port": {"KAMERA_GATEWAY_BASE": "https://" + IP4 + ":8443"},
    "ip_http": {"KAMERA_GATEWAY_BASE": "http://" + IP4},
    "ip_zugang": {"KAMERA_GATEWAY_BASE": "https://user:pw@" + IP4},
    "ip_query": {"KAMERA_GATEWAY_BASE": "https://" + IP4 + "/?x=1"},
    "ip_fragment": {"KAMERA_GATEWAY_BASE": "https://" + IP4 + "#x"},
}


def _edge(node_exe, logic_src=None):
    with tempfile.TemporaryDirectory() as d:
        with io.open(os.path.join(d, "logic.ts"), "w", encoding="utf-8", newline="\n") as f:
            f.write(logic_src if logic_src is not None else _lies(LOGIC))
        with io.open(os.path.join(d, "h.mjs"), "w", encoding="utf-8", newline="\n") as f:
            f.write(HARNESS % {"faelle": json.dumps(FAELLE)})
        r = subprocess.run([node_exe, "--experimental-strip-types", "--no-warnings", "h.mjs"], cwd=d,
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=EPK_TEST_TIMEOUT)
    assert r.returncode == 0, r.stderr[-3000:]
    return json.loads(r.stdout.strip().splitlines()[-1])


@pytest.fixture(scope="module")
def E(node_exe):
    return _edge(node_exe)


def test_gateway_wird_bevorzugt(E):
    assert E["basis"]["nur_gateway"] == GW
    assert E["basis"]["beide"] == GW
    assert E["live"]["beide"]["json"]["webrtcUrl"].startswith(GW + "/live/hochregal01/whep?token=")
    assert E["einr"]["beide"]["json"]["basis"] == GW


def test_alter_name_als_rueckfall(E):
    assert E["basis"]["nur_alt"] == ALT
    assert E["basis"]["gateway_leer"] == ALT and E["basis"]["gateway_blank"] == ALT
    assert E["live"]["nur_alt"]["status"] == 200


def test_http_und_kaputt_abgelehnt_ohne_stillen_rueckfall(E):
    for f in ("gateway_http", "gateway_kaputt", "alt_http"):
        assert E["basis"][f] is None, f
        assert E["live"][f] == {"status": 503, "json": {"error": "nicht_konfiguriert"}}, f
        assert E["einr"][f]["json"]["basis"] == "", f


def test_fehlend_fail_closed(E):
    assert E["basis"]["keins"] is None
    assert E["live"]["keins"] == {"status": 503, "json": {"error": "nicht_konfiguriert"}}
    assert E["einr"]["keins"]["json"] == {"einrichtung": True, "secret": True, "basis": ""}


def test_ip_gateway_ohne_dns(E):
    assert E["basis"]["ip"] == "https://" + IP4
    assert E["basis"]["ip_port"] == "https://" + IP4 + ":8443"
    assert E["live"]["ip"]["json"]["webrtcUrl"].startswith("https://" + IP4 + "/live/hochregal01/whep?token=")
    assert E["einr"]["ip_port"]["json"]["basis"] == "https://" + IP4 + ":8443"
    for f in ("ip_http", "ip_zugang", "ip_query", "ip_fragment"):
        assert E["basis"][f] is None, f
        assert E["live"][f] == {"status": 503, "json": {"error": "nicht_konfiguriert"}}, f


def test_umkehrprobe_zugangsdaten_in_der_adresse(node_exe):
    R = _edge(node_exe, _mut(_lies(LOGIC), "if (!/^https:\\/\\/[A-Za-z0-9.-]+", "if (!/^https:\\/\\/[A-Za-z0-9.:@-]+"))
    assert R["basis"]["ip_zugang"] is not None, "Umkehrprobe: Zugangsdaten-Sperre waere blind"


def test_schraegstrich_und_pfad_wie_bisher(E):
    assert E["basis"]["gateway_schraeg"] == GW
    assert E["basis"]["gateway_port_pfad"] == GW + ":8443/kam"


def test_webrtc_antwort_mit_einzelbild_rueckfall_gleiches_token(E):
    j = E["live"]["nur_gateway"]["json"]
    assert set(j) == {"typ", "webrtcUrl", "liveUrl", "snapshotUrl", "exp", "ttl"}
    t = [re.search(r"\?token=(.+)$", j[k]).group(1) for k in ("webrtcUrl", "liveUrl", "snapshotUrl")]
    assert len(set(t)) == 1
    assert j["snapshotUrl"] == GW + "/live/hochregal01/snapshot.jpg?token=" + t[0]
    for k in ("webrtcUrl", "liveUrl", "snapshotUrl"):
        assert not re.search(r"rtsp|:554|/api/", j[k]), "Browser bekommt nur Proxy-Pfade"


def test_umkehrprobe_reihenfolge_vertauscht(node_exe):
    s = _mut(_lies(LOGIC), 'const gw = env("KAMERA_GATEWAY_BASE");', 'const gw = env("KAMERA_BACKEND_BASE");')
    s = _mut(s, '(env("KAMERA_BACKEND_BASE") ?? "")).trim();', '(env("KAMERA_GATEWAY_BASE") ?? "")).trim();')
    assert _edge(node_exe, s)["basis"]["beide"] == ALT, "Umkehrprobe: Vorrang waere blind"


def test_umkehrprobe_stiller_rueckfall(node_exe):
    alt = '  const roh = (gw !== undefined && gw.trim() !== "" ? gw : (env("KAMERA_BACKEND_BASE") ?? "")).trim();'
    neu = ('  const okGw = gw !== undefined && /^https:\\/\\//.test(gw.trim());\n'
           '  const roh = (okGw ? gw : (env("KAMERA_BACKEND_BASE") ?? "")).trim();')
    R = _edge(node_exe, _mut(_lies(LOGIC), alt, neu))
    assert R["basis"]["gateway_http"] == ALT, "Umkehrprobe: stiller Rueckfall waere unentdeckt"


def test_umkehrprobe_http_erlaubt(node_exe):
    R = _edge(node_exe, _mut(_lies(LOGIC), "if (!/^https:\\/\\/[A-Za-z0-9.-]+", "if (!/^https?:\\/\\/[A-Za-z0-9.-]+"))
    assert R["basis"]["gateway_http"] is not None


def test_umkehrprobe_gateway_ignoriert(node_exe):
    R = _edge(node_exe, _mut(_lies(LOGIC), 'const gw = env("KAMERA_GATEWAY_BASE");', "const gw = undefined as string | undefined;"))
    assert R["basis"]["nur_gateway"] is None


# ── TEIL B: App-Kachel ──────────────────────────────────────────────────────
SZENEN = r"""
function reset(s) { SZENE = s; store.clear(); _kamBackend.fehlt = false; ['get','post','upsert','del','fetch'].forEach(function (k) { ZAEHL[k].length = 0; }); }
const KAMS = [{id: 'hochregal01', name: 'Kamera .61 (Name folgt)', standort: 'Standort folgt', aktiv: true, aufbewahrung_tage: 3}];
function wurzel(rolle) { return React.createElement(KameraView, {curUser: {id: 'x', role: rolle}, ww: 1440, users: []}); }
function bilder() { return alle(baum, function (n) { return n.tag === 'img'; }); }
const W = {typ: 'webrtc', liveUrl: 'https://g/live/hochregal01/index.m3u8?token=T', webrtcUrl: 'https://g/live/hochregal01/whep?token=T',
           snapshotUrl: 'https://g/live/hochregal01/snapshot.jpg?token=T', exp: 1e12, ttl: 90};
reset({db: {kameras: KAMS}, fein: true, fetch: {status: 200, json: W}});
let w = wurzel('admin'); await ruhe(w);
let b = bilder();
OUT.rueckfall = {n: b.length, src: b.length ? b[0].props.src : '', text: text(baum)};
reset({db: {kameras: KAMS}, fein: true, fetch: {status: 200, json: Object.assign({}, W, {snapshotUrl: undefined})}});
w = wurzel('admin'); await ruhe(w);
OUT.ohne = {n: bilder().length};
reset({db: {kameras: KAMS}, fein: true, fetch: {status: 200, json: Object.assign({}, W, {snapshotUrl: 'http://g/live/hochregal01/snapshot.jpg?token=T'})}});
w = wurzel('admin'); await ruhe(w);
OUT.http = {n: bilder().length};
const aw = _kamStreamAntwort(200, W, 'live');
const ah = _kamStreamAntwort(200, Object.assign({}, W, {typ: 'llhls'}), 'live');
const aj = _kamStreamAntwort(200, Object.assign({}, W, {snapshotUrl: 'javascript:alert(1)'}), 'live');
OUT.H = {aw: aw.snapshotUrl, ah: ah.snapshotUrl, aj: aj.snapshotUrl,
  ersatz: [404, 500, 502, 503, undefined, 0, 401, 403].map(function (s) { return _kamErsatzBild(s, aw); }),
  ohneSnap: _kamErsatzBild(404, Object.assign({}, aw, {snapshotUrl: ''})),
  snapTyp: _kamErsatzBild(404, {typ: 'snapshot', snapshotUrl: 'https://g/x'}),
  mjpeg: _kamPlayerModus(true, false, _kamStreamAntwort(200, {typ: 'mjpeg', mjpegUrl: 'https://g/live/mob32/mjpeg?token=T', exp: 3}, 'live'))};
"""


def _ui(node_exe, block=None):
    return _render_lauf(node_exe, block if block is not None else _block(), SZENEN)


@pytest.fixture(scope="module")
def U(node_exe):
    return _ui(node_exe)


def test_einzelbild_rueckfall_wenn_kein_videoweg(U):
    r = U["rueckfall"]
    assert r["n"] == 1 and r["src"] == "https://g/live/hochregal01/snapshot.jpg?token=T&_=0"


def test_ohne_oder_mit_http_einzelbild_kein_bild(U):
    assert U["ohne"]["n"] == 0 and U["http"]["n"] == 0


def test_helfer_rueckfall_nie_bei_401_403(U):
    H = U["H"]
    assert H["aw"] == "https://g/live/hochregal01/snapshot.jpg?token=T"
    assert H["ah"] == "" and H["aj"] == ""
    assert H["ersatz"] == [True, True, True, True, True, True, False, False]
    assert H["ohneSnap"] is False and H["snapTyp"] is False
    assert H["mjpeg"] == "mjpeg"


def test_whep_fehler_und_ice_abbruch_nutzen_den_rueckfall():
    b = _block()
    i = b.index("function KameraKachel(")
    k = b[i:b.index("function KameraAufzeichnung(", i)]
    assert "if(modus==='webrtc'&&_kamErsatzBild(e&&e.status,a)){ersatz(a);return;}" in k
    assert "pc.connectionState==='failed'&&_kamErsatzBild(0,a)){ersatz(a);return;}" in k
    assert "if(modus==='keiner'){if(_kamErsatzBild(0,a)){ersatz(a);return;}" in k
    w = b[b.index("async function _kamWhep("):b.index("function _kamDbFehlt(")]
    assert "'Content-Type':'application/sdp'" in w and "method:'POST'" in w and "if(!r.ok)" in w


def test_kein_rtsp_im_browser_code():
    b = _block()
    assert not re.search(r"rtsps?:|:554\b|/api/(webrtc|stream|frame)", b), "Browser spricht nur den Pruef-Proxy an"


def test_umkehrprobe_rueckfall_auch_bei_403(node_exe):
    alt = "_kamFehlerGrund(st)!=='kein_zugriff'"
    b = _mut(_block(), alt, "true")
    assert _ui(node_exe, b)["H"]["ersatz"][-1] is True


def test_umkehrprobe_http_einzelbild(node_exe):
    b = _mut(_block(), "o.snapshotUrl=(typ==='webrtc'&&_kamIstHttps(j.snapshotUrl))?j.snapshotUrl:'';",
             "o.snapshotUrl=j.snapshotUrl||'';")
    assert _ui(node_exe, b)["http"]["n"] == 1


# ── TEIL C: SQL ─────────────────────────────────────────────────────────────
def _code(sql):
    return "\n".join(l.split("--", 1)[0] for l in sql.split("\n"))


def _gemeinsam(name, sql):
    b = []
    code = _code(sql)
    if not sql.startswith("-- IDEMPOTENT"):
        b.append(name + ": IDEMPOTENT-Kopf fehlt")
    if re.search(r"\bcascade\b", code, re.I):
        b.append(name + ": CASCADE")
    if IP_RE.search(sql):
        b.append(name + ": IP-Adresse")
    if re.search(r"(rtsp|https?)://", sql):
        b.append(name + ": Adresse")
    if re.search(r"(passwort|kennwort|password|KAM_PW|KAM_PASS|KAM_USER)", sql, re.I):
        b.append(name + ": Zugangsdaten")
    for t in re.findall(r"time\s+'([^']*)'", code):
        if not re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d(:00)?", t):
            b.append(name + ": Zeit nicht ganze Minute " + t)
    for wort in ("monteur", "helfer", "techniker", "projektleiter", "lagerleitung"):
        if name != "PROBE" and re.search(r"'" + wort + r"'", code):
            b.append(name + ": weitere Rolle " + wort)
    return b


def _regeln_ok(name, code):
    b = []
    zug = re.findall(r"insert into public\.kamera_zugriff[^;]*;", code, re.S)
    for z in zug:
        if "'admin'" in z and not re.search(r"'admin',\s*'\{1,2,3,4,5,6,7\}',\s*null,\s*null,\s*true", z):
            b.append(name + ": admin nicht immer")
        if "'buero'" in z and not re.search(r"'buero',\s*'\{1,2,3,4,5\}',\s*time '07:00',\s*time '17:00',\s*true", z):
            b.append(name + ": buero nicht Mo-Fr 07-17")
        if "'GATEWAY_SEED" not in z:
            b.append(name + ": Regel ohne Kennzeichen")
    if len([z for z in zug if "'admin'" in z]) < 1 or len([z for z in zug if "'buero'" in z]) < 1:
        b.append(name + ": admin/buero-Regel fehlt")
    return b, zug


SCHALTER = "set local epk.mobotix_aktiv = 'false';"
SCHALTER_PRUEF = "coalesce(current_setting('epk.mobotix_aktiv', true), 'false') = 'true'"


def pruefe_seed(sql):
    b = _gemeinsam("SEED", sql)
    code = _code(sql)
    for verboten in ("delete", "drop", "truncate", "alter", "update", "grant", "revoke"):
        if re.search(r"\b" + verboten + r"\b", code, re.I):
            b.append("SEED enthaelt " + verboten)
    if not re.search(r"^begin;", code, re.M) or not re.search(r"^commit;", code, re.M):
        b.append("SEED ohne begin/commit")
    i_ins = code.lower().find("insert into")
    vor = code[:i_ins]
    if "to_regclass('public.kameras')" not in vor:
        b.append("Vorpruefung Tabellen fehlt")
    if not re.search(r"'kam_g3_01'[\s\S]*raise exception 'Pilot-Seed[^']*KAMERA_PILOT_HEUTE_RUECKNAHME\.sql", vor):
        b.append("Abbruch bei Pilot-IDs fehlt (vor dem ersten insert)")
    if "anderen Streamnamen" not in vor or "anderen Kamera" not in vor:
        b.append("Vorpruefung belegte IDs/Streams fehlt")
    if code.count(SCHALTER) != 1 or code.find(SCHALTER) > i_ins:
        b.append("Mobotix-Schalter fehlt/nicht AUS/nicht oben")
    if re.search(r"set local epk\.mobotix_aktiv = 'true'", code):
        b.append("Mobotix-Schalter steht auf true")
    # G3: ID == Stream, webrtc, keine Aufzeichnungsquelle
    be = re.findall(r"insert into public\.kamera_backend[^;]*;", code, re.S)
    g3 = [x for x in be if "'elektrolager03'" in x]
    if len(g3) != 1:
        b.append("G3-kamera_backend-insert fehlt")
    else:
        zeilen = re.findall(r"\('([^']+)',\s*'([^']+)',\s*null,\s*'([^']+)'\)", g3[0])
        if sorted(z[0] for z in zeilen) != sorted(G3):
            b.append("G3-IDs falsch: %s" % zeilen)
        for kid, s, typ in zeilen:
            if kid != s:
                b.append("ID != Streamname: " + kid)
            if typ != "webrtc":
                b.append("G3 nicht webrtc: " + kid)
    if set(re.findall(r"'(cam\d+|hochregal\d+|verkauf\d+|elektrolager\d+)'", code)) != set(G3):
        b.append("fremde G3-IDs")
    # Mobotix: jeder insert mit mob-IDs nur hinter dem Schalter; ID == Stream; webrtc
    for ins in re.findall(r"insert into[^;]*;", code, re.S):
        if "'mob3" in ins and SCHALTER_PRUEF not in ins:
            b.append("Mobotix-insert ohne Schalter")
    mob_be = [x for x in be if "'mob3" in x]
    if len(mob_be) != 1 or not re.search(r"select k\.id, k\.id, null, 'mjpeg'", mob_be[0]):
        b.append("Mobotix-Zuordnung nicht ID=Stream/mjpeg")
    if set(re.findall(r"'(mob\d+)'", code)) != set(MOB):
        b.append("Mobotix-IDs falsch")
    # mjpeg NUR im Mobotix-Block (Entscheid GF 20.11.: MJPEG durchgereicht, keine Umwandlung auf der QNAP)
    for ins in re.findall(r"insert into[^;]*;", code, re.S):
        if "'mjpeg'" in ins and "'mob3" not in ins and "'mob" not in ins and "k.id, k.id" not in ins:
            b.append("mjpeg ausserhalb des Mobotix-Blocks")
    for kid, name in (("hochregal01", "Hochregal 01"), ("verkauf02", "Verkauf 02"), ("elektrolager03", "Elektrolager 03")):
        if not re.search(r"'" + kid + r"',\s*'" + name + r"'", code):
            b.append("Anzeigename fehlt: " + kid)
    if not re.search(r"'cam39',\s*'Kamera \.39 \(Name folgt\)',\s*'offen'", code):
        b.append("cam39 nicht vorlaeufig/offen")
    if not re.search(r"'UVC G3 Dome', true, 3\)", code) or "NICHTS aufgezeichnet" not in sql:
        b.append("aufbewahrung 3 / Hinweis keine Aufzeichnung fehlt")
    rb, _ = _regeln_ok("SEED", code)
    b += rb
    if not re.search(r"on conflict \(id\) do nothing", code) or not re.search(r"on conflict \(kamera_id\) do nothing", code):
        b.append("insert nicht idempotent")
    for zz in re.findall(r"insert into public\.kamera_zugriff[^;]*;", code, re.S):
        if "not exists" not in zz:
            b.append("Regel ohne Doppelschutz")
    return b


def pruefe_probe(sql):
    b = _gemeinsam("PROBE", sql)
    code = _code(sql)
    zeilen = [z.strip().lower() for z in code.splitlines() if z.strip()]
    if not zeilen or zeilen[0] != "begin;" or zeilen[-1] != "rollback;":
        b.append("PROBE nicht begin ... rollback")
    if [z for z in zeilen if z.startswith("commit")]:
        b.append("PROBE committet")
    if code.count("raise exception 'PROBE_ERGEBNIS %', r;") != 1:
        b.append("PROBE_ERGEBNIS-Abbruch fehlt")
    for rolle in ("admin", "buero", "monteur"):
        if "lower(role::text)='" + rolle + "'" not in code:
            b.append("Konto je Rolle fehlt: " + rolle)
    if "kam_g3_01" not in code or "PROBE_ERGEBNIS ABBRUCH: Pilot-Seed" not in code:
        b.append("PROBE bricht bei Pilot-IDs nicht ab")
    if code.count(SCHALTER) != 1:
        b.append("PROBE ohne Mobotix-Schalter (AUS)")
    for teil in ("buero_mo0659", "buero_mo1700", "buero_mo1659", "buero_samstag", "monteur_darf", "admin_backend",
                 "zuordnungen_id_gleich_stream"):
        if teil not in code:
            b.append("PROBE-Zeile fehlt: " + teil)
    if code.count("' OK; ' else ' ABWEICHUNG; '") < 10:
        b.append("OK/ABWEICHUNG je Zeile fehlt")
    if not re.search(r"\('mob32','mob32',null,'mjpeg'\)", code):
        b.append("Mobotix in der Probe nicht mjpeg")
    rb, _ = _regeln_ok("PROBE", code)
    return b + rb


ALLE_IDS = "('elektrolager03', 'verkauf02', 'cam39', 'hochregal01', 'mob32', 'mob33', 'mob34', 'mob35', 'mob36')"


def pruefe_ruecknahme(sql):
    b = _gemeinsam("RUECK", sql)
    code = _code(sql)
    for verboten in ("drop", "truncate", "alter", "update", "insert"):
        if re.search(r"\b" + verboten + r"\b", code, re.I):
            b.append("RUECK enthaelt " + verboten)
    dels = [m.group(0) for m in re.finditer(r"\bdelete\b[^;]*;", code, re.I | re.S)]
    tab = [re.search(r"from\s+public\.(\w+)", d).group(1) for d in dels]
    if tab != ["kamera_zugriff", "kamera_backend", "kameras"]:
        b.append("Reihenfolge der deletes falsch: %s" % tab)
    for d in dels:
        if ALLE_IDS not in d:
            b.append("delete nicht auf die Gateway-IDs begrenzt")
    if dels and "GATEWAY\\_SEED" not in dels[0]:
        b.append("Regel-delete nicht auf GATEWAY_SEED begrenzt")
    i_f = code.find("raise exception 'Es gibt %")
    if i_f < 0 or (dels and i_f > code.find(dels[0][:25])):
        b.append("Abbruch bei fremden Regeln fehlt/zu spaet")
    if "kamera_abruf_log" in code:
        b.append("Protokoll beruehrt")
    if not re.search(r"^begin;", code, re.M) or not re.search(r"^commit;", code, re.M):
        b.append("RUECK ohne Transaktion")
    return b


def test_seed_sauber():
    assert pruefe_seed(_lies(SEED)) == []


def test_probe_sauber():
    assert pruefe_probe(_lies(PROBE)) == []


def test_ruecknahme_sauber():
    assert pruefe_ruecknahme(_lies(RUECK)) == []


def test_pilot_seed_als_superseded_markiert():
    for n in ("ENTWURF", "PROBE", "RUECKNAHME"):
        kopf = "\n".join(_lies(os.path.join(SQL_DIR, "KAMERA_PILOT_HEUTE_" + n + ".sql")).split("\n")[:5])
        assert kopf.startswith("-- IDEMPOTENT") and "SUPERSEDED" in kopf and "KAMERA_GATEWAY_SEED_ENTWURF.sql" in kopf, n


@pytest.mark.parametrize("alt,neu,erwartet", [
    ("true, 3)\non conflict (id) do nothing;", "true, 3)\non conflict (id) do nothing;\ndelete from public.kameras where id = 'x' cascade;", "CASCADE"),
    ("\n" + SCHALTER, "\nset local epk.mobotix_aktiv = 'true';", "Mobotix-Schalter"),
    ("time '17:00', true, 'GATEWAY_SEED buero Mo-Fr 07-17'\n  from public.kameras k\n where k.id in ('elektrolager03'",
     "time '17:00:30', true, 'GATEWAY_SEED buero Mo-Fr 07-17'\n  from public.kameras k\n where k.id in ('elektrolager03'", "ganze Minute"),
    ("('verkauf02',      'verkauf02',      null, 'webrtc')", "('verkauf02',      'g3_38',          null, 'webrtc')", "ID != Streamname"),
    ("('cam39',          'cam39',          null, 'webrtc')", "('cam39',          'cam39',          null, 'mjpeg')", "nicht webrtc"),
    ("'Kamera .39 (Name folgt)', 'offen'", "'Kamera .39 (Name folgt)', 'Standort folgt'", "cam39 nicht vorlaeufig"),
    ("('hochregal01',    'Hochregal 01'", "('hochregal01',    'Elektrolager 03'", "Anzeigename fehlt"),
    ("raise exception 'Pilot-Seed", "raise notice 'Pilot-Seed", "Pilot-IDs"),
    ("select k.id, k.id, null, 'mjpeg'", "select k.id, k.id, null, 'webrtc'", "Mobotix-Zuordnung"),
    ("'Standort folgt', 'Ubiquiti', 'UVC G3 Dome', true, 3),\n  ('verkauf02'",
     "'" + ".".join(("10", "0", "0", "37")) + "', 'Ubiquiti', 'UVC G3 Dome', true, 3),\n  ('verkauf02'", "IP-Adresse"),
    ("select k.id, 'buero', '{1,2,3,4,5}', time '07:00', time '17:00', true, 'GATEWAY_SEED buero Mo-Fr 07-17'\n"
     "  from public.kameras k\n where k.id in ('elektrolager03'",
     "select k.id, 'monteur', '{1,2,3,4,5}', time '07:00', time '17:00', true, 'GATEWAY_SEED buero Mo-Fr 07-17'\n"
     "  from public.kameras k\n where k.id in ('elektrolager03'", "weitere Rolle"),
])
def test_umkehrprobe_seed(alt, neu, erwartet):
    assert any(erwartet in x for x in pruefe_seed(_mut(_lies(SEED), alt, neu))), erwartet


def test_umkehrprobe_seed_mobotix_ohne_schalter():
    s = _lies(SEED)
    i = s.index("insert into public.kamera_backend (kamera_id, stream_name, aufzeichnung_quelle, stream_typ)\nselect k.id, k.id")
    j = s.index(SCHALTER_PRUEF, i)
    s = s[:j] + "true" + s[j + len(SCHALTER_PRUEF):]
    assert any("ohne Schalter" in x for x in pruefe_seed(s))


@pytest.mark.parametrize("alt,neu,erwartet", [
    ("\nrollback;", "\ncommit;", "committet"),
    ("raise exception 'PROBE_ERGEBNIS %', r;", "raise notice 'PROBE_ERGEBNIS %', r;", "PROBE_ERGEBNIS-Abbruch"),
    ("lower(role::text)='monteur'", "lower(role::text)='helfer'", "Konto je Rolle"),
    ("PROBE_ERGEBNIS ABBRUCH: Pilot-Seed", "PROBE_ERGEBNIS HINWEIS: Pilot-Seed", "Pilot-IDs"),
])
def test_umkehrprobe_probe(alt, neu, erwartet):
    assert any(erwartet in x for x in pruefe_probe(_mut(_lies(PROBE), alt, neu))), erwartet


@pytest.mark.parametrize("alt,neu,erwartet", [
    ("  delete from public.kamera_backend\n   where kamera_id in " + ALLE_IDS + ";\n  -- 3. Kameras\n  delete from public.kameras\n   where id in " + ALLE_IDS + ";",
     "  delete from public.kameras\n   where id in " + ALLE_IDS + ";\n  delete from public.kamera_backend\n   where kamera_id in " + ALLE_IDS + ";",
     "Reihenfolge"),
    ("  delete from public.kamera_backend\n   where kamera_id in " + ALLE_IDS + ";", "  delete from public.kamera_backend;", "nicht auf die Gateway-IDs"),
    ("\n     and bemerkung like 'GATEWAY\\_SEED%';", ";", "GATEWAY_SEED"),
    ("   where id in " + ALLE_IDS + ";", "   where id in " + ALLE_IDS + " cascade;", "CASCADE"),
    ("raise exception 'Es gibt %", "raise notice 'Es gibt %", "fremden Regeln"),
])
def test_umkehrprobe_ruecknahme(alt, neu, erwartet):
    assert any(erwartet in x for x in pruefe_ruecknahme(_mut(_lies(RUECK), alt, neu))), erwartet


# ── TEIL D: Doku, Vorlagen, Deploy-Nachweis ─────────────────────────────────
def pruefe_doku(text):
    b = []
    if len(text.split("\n")) > 70:
        b.append("PILOT_HEUTE laenger als 70 Zeilen")
    if IP_RE.search(text):
        b.append("IP-Adresse")
    reihe = ["## a) Secret", "## b) Zertifikat + DNS (Sebastian)", "## c) Prüf-Proxy auf der QNAP (Chat-Claude)",
             "Secret `KAMERA_GATEWAY_BASE`", "sql/KAMERA_GATEWAY_SEED_PROBE.sql", "sql/KAMERA_GATEWAY_SEED_ENTWURF.sql",
             "## e) Ende-zu-Ende", "PILOT_TESTLISTE.md"]
    pos = [text.find(x) for x in reihe]
    if -1 in pos or pos != sorted(pos):
        b.append("Reihenfolge Zertifikat -> Proxy -> GATEWAY_BASE -> Probe -> Seed -> Testliste: %s" % pos)
    if "nie auf privaten Handys" not in text:
        b.append("Stammzertifikat-Grenze (nur Firmengeraete) fehlt")
    for teil in ("hochregal01", "verkauf02", "elektrolager03", "cam39", "TABU", "Mensch", "mjpeg",
                 "https://kameras.ep-kolar.at", "DNS-01", "Vorlage – der Kamera-Server ist die QNAP"):
        if teil not in text:
            b.append("Doku ohne " + teil)
    return b


def test_doku_reihenfolge_qnap():
    assert pruefe_doku(_lies(DOKU)) == []


def test_testliste_auf_gateway_ids():
    t = _lies(TESTLISTE)
    assert "KAMERA_GATEWAY_BASE" in t and "hochregal01" in t and "snapshotUrl" in t
    assert not re.search(r"kam_g3_01|g3_lager03|\"kam_g3", t)
    assert not IP_RE.search(t)


def test_umkehrprobe_doku():
    d = _lies(DOKU)
    assert any("70 Zeilen" in x for x in pruefe_doku(d + "\n" * 30))
    tausch = d.replace("## b) Zertifikat + DNS (Sebastian)", "## b) XX", 1).replace(
        "## c) Prüf-Proxy auf der QNAP (Chat-Claude)", "## b) Zertifikat + DNS (Sebastian)", 1).replace(
        "## b) XX", "## c) Prüf-Proxy auf der QNAP (Chat-Claude)", 1)
    assert any("Reihenfolge" in x for x in pruefe_doku(tausch))


def test_vorlage_go2rtc_gateway_streams_und_mobotix_aus():
    if not os.path.isdir(VORLAGE):
        pytest.skip("Vorlagen nicht auf diesem Rechner")
    yaml = pytest.importorskip("yaml")
    roh = _lies(os.path.join(VORLAGE, "go2rtc.yaml"))
    assert set(yaml.safe_load(roh)["streams"]) == set(G3)
    for z in roh.split("\n"):
        if re.search(r"^\s+- rtsp://", z):
            assert "${KAM_USER}:${KAM_PASS}@" in z, z
    for nr in range(32, 37):
        netz = ".".join(("192", "168", "33", str(nr)))
        assert ("  # mob%d: http://${KAM_USER}:${KAM_PASS}@%s/cgi-bin/faststream.jpg?stream=full" % (nr, netz)) in roh
    assert "KAM_PW" not in roh, "Variable heisst auf der QNAP KAM_PASS"
    assert not re.search(r"\.6[23][^\n]*offline", roh), ".62/.63 nicht als offline behaupten (von der QNAP aus pruefen)"
    assert "ffmpeg:" not in roh and "#video=h264" not in roh, "Mobotix: MJPEG durchreichen, keine Umwandlung"
    for f in ("go2rtc.yaml", ".env.beispiel", "docker-compose.yml"):
        assert "MX_USER" not in _lies(os.path.join(VORLAGE, f)) and "MX_PASS" not in _lies(os.path.join(VORLAGE, f)), f
    assert "Vorlage – der Kamera-Server ist die QNAP" in _lies(os.path.join(VORLAGE, "README.md"))


def test_deploy_nachweis_sha_gleich_repo():
    assert hashlib.sha256(_lies(INDEX_TS).encode("utf-8")).hexdigest() == DEPLOYT_INDEX_SHA
    assert hashlib.sha256(_lies(LOGIC).encode("utf-8")).hexdigest() == DEPLOYT_LOGIC_SHA
    assert DEPLOYT_VERSION >= 3


def test_umkehrprobe_deploy_nachweis():
    s = _lies(LOGIC)
    assert hashlib.sha256(s.replace("KAMERA_GATEWAY_BASE", "KAMERA_GATEWAY_BASX", 1).encode("utf-8")).hexdigest() != DEPLOYT_LOGIC_SHA
