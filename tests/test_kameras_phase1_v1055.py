# -*- coding: utf-8 -*-
"""Kameras Phase 1 (19.11.2026) - Serverpruefung, Token-Vertrag, Datenmodell, App-Schalter.

TEIL A (dieser Abschnitt): die Edge Function `supabase/functions/kamera-stream`.
Ihre gesamte Entscheidung steht in `logic.ts` (rein, ohne Importe). Hier laeuft
GENAU diese Datei in Node (Typ-Abstreifung, Node >= 22.6) gegen Attrappen fuer
Auth, Nutzerzeile, Regel-Abfrage und Backend-Zuordnung. Die Attrappe der
Regel-Abfrage ist `entscheide()` aus derselben Datei - der ausfuehrbare Spiegel
von `public.kamera_pruefen`.

Kern (Lehre fz_finanzen): ein Monteur bekommt NIE eine Adresse, und die
Rollensperre sitzt VOR jeder Kamera-/Backend-Abfrage. Jeder Riegel hat eine
Umkehrprobe am mutierten Quelltext.
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
FN_DIR = os.path.join(WURZEL, "supabase", "functions", "kamera-stream")
LOGIC = os.path.join(FN_DIR, "logic.ts")
INDEX_TS = os.path.join(FN_DIR, "index.ts")
README = os.path.join(FN_DIR, "README.md")

BASE = "https://kamera.example.test"
SECRET = "s" * 40

# Montag 23.11.2026 10:00 Wien (CET = UTC+1) -> 09:00 UTC
HARNESS = r"""
import * as L from "./logic.ts";
const SECRET = %(secret)s;
const BASE = %(base)s;
const MO_10 = Date.UTC(2026, 10, 23, 9, 0, 0);
const MO_0659 = Date.UTC(2026, 10, 23, 5, 59, 0);
const MO_17 = Date.UTC(2026, 10, 23, 16, 0, 0);
const SA_10 = Date.UTC(2026, 10, 21, 9, 0, 0);
const USERS = {
  "admin":       {id: "u1", role: "admin", active: 1, locked: false},
  "pl":          {id: "u2", role: "projektleiter", active: 1, locked: 0},
  "plgesperrt":  {id: "u3", role: "projektleiter", active: "1", locked: "false"},
  "monteur":     {id: "u4", role: "monteur", active: 1, locked: false},
  "helfer":      {id: "u5", role: "helfer", active: 1, locked: false},
  "buero":       {id: "u6", role: "buero", active: 1, locked: false},
  "lager":       {id: "u7", role: "lagerleitung", active: 1, locked: false},
  "inaktiv":     {id: "u8", role: "admin", active: 0, locked: false},
  "gesperrt":    {id: "u9", role: "admin", active: 1, locked: true},
  "gesperrt1":   {id: "u10", role: "admin", active: 1, locked: 1},
  "techniker":   {id: "u11", role: "techniker", active: 1, locked: false},
  "obermonteur": {id: "u12", role: "obermonteur", active: 1, locked: false},
  "display":     {id: "u13", role: "lager_display", active: 1, locked: false},
  "terminal":    {id: "u14", role: "stempel_terminal", active: 1, locked: false},
  "ohnerolle":   {id: "u15", role: null, active: 1, locked: false},
  "grossadmin":  {id: "u16", role: " ADMIN ", active: true, locked: null},
};
const REGELN = {
  cam1: [
    {rolle: "admin", erlaubt: true},
    {rolle: "projektleiter", erlaubt: true},
    {user_id: "u3", erlaubt: false},
    {user_id: "u4", erlaubt: true},
    {user_id: "u5", erlaubt: true},
    {rolle: "buero", wochentage: [1, 2, 3, 4, 5], von: "07:00", bis: "17:00", erlaubt: true},
    {rolle: "lagerleitung", erlaubt: true},
  ],
  cam2: [{rolle: "admin", erlaubt: true}],
  cam3: [{rolle: "admin", erlaubt: true}],
  cam4: [],
};
const BACKEND = {
  cam1: {stream_name: "hof_nord", aufzeichnung_quelle: "hof_nord_rec"},
  cam3: {stream_name: "lager_ost", aufzeichnung_quelle: null},
  cam4: {stream_name: "lager_west", aufzeichnung_quelle: null},
};
const ENV_OK = {KAMERA_TOKEN_SECRET: SECRET, KAMERA_BACKEND_BASE: BASE};

async function lauf(f) {
  const o = Object.assign({wer: "admin", body: {kamera_id: "cam1"}, env: ENV_OK, now: MO_10,
                           origin: "https://epkolar.github.io", method: "POST", auth: undefined}, f);
  const calls = {auth: 0, nutzer: 0, darf: 0, backend: 0, log: []};
  const deps = {
    env: (n) => o.env[n],
    now: () => o.now,
    nonce: () => "nonce-1",
    authUser: async (jwt) => { calls.auth++; const m = /^jwt_([a-z0-9]+)_0123456789abcdef$/.exec(jwt); return m && USERS[m[1]] ? "auth-" + m[1] : null; },
    ladeNutzer: async (uid) => { calls.nutzer++; return USERS[uid.slice(5)] || null; },
    darfSehen: async (jwt, k) => {
      calls.darf++;
      if (o.darfWirft) throw new Error("db down");
      const wer = /^jwt_([a-z0-9]+)_/.exec(jwt)[1];
      const u = USERS[wer];
      return L.entscheide(REGELN[k] || [], {id: u.id, role: String(u.role || "").trim()}, o.now);
    },
    ladeBackend: async (k) => { calls.backend++; return BACKEND[k] || null; },
    protokoll: async (e) => { calls.log.push(e); if (o.logWirft) throw new Error("log down"); },
  };
  const h = {"content-type": "application/json"};
  if (o.origin !== null) h["origin"] = o.origin;
  const auth = o.auth !== undefined ? o.auth : "Bearer jwt_" + o.wer + "_0123456789abcdef";
  if (auth !== null) h["authorization"] = auth;
  const init = {method: o.method, headers: h};
  if (o.method === "POST") init.body = typeof o.body === "string" ? o.body : JSON.stringify(o.body);
  const res = await L.bearbeite(new Request("https://fn.example.test/kamera-stream", init), deps);
  const text = res.status === 204 ? "" : await res.text();
  const out = {status: res.status, text, acao: res.headers.get("access-control-allow-origin"),
               cache: res.headers.get("cache-control"), calls};
  if (res.status === 200) {
    const j = JSON.parse(text);
    const url = j.liveUrl || j.aufzeichnungUrl;
    const tok = decodeURIComponent(/[?&]token=([^&]+)/.exec(url)[1]);
    out.json = j;
    out.tok = tok;
    out.payload = JSON.parse(Buffer.from(tok.split(".")[0].replace(/-/g, "+").replace(/_/g, "/"), "base64").toString("utf8"));
    out.okLive = await L.pruefeToken(SECRET, tok, o.now, {s: out.payload.s, sc: out.payload.sc}) !== null;
  }
  return out;
}

const F = %(faelle)s;
const R = {};
for (const k of Object.keys(F)) R[k] = await lauf(F[k]);

// Token-Pruefer (Referenz fuer den Reverse-Proxy)
const p0 = {v: 1, k: "cam1", s: "hof_nord", u: "u1", sc: "live", iat: Math.floor(MO_10 / 1000), exp: Math.floor(MO_10 / 1000) + 90, n: "x"};
const t0 = await L.signiere(SECRET, p0);
const kipp = t0.slice(0, -2) + (t0.slice(-2, -1) === "A" ? "B" : "A") + t0.slice(-1);
const lang = await L.signiere(SECRET, Object.assign({}, p0, {exp: p0.iat + 600}));
const v2 = await L.signiere(SECRET, Object.assign({}, p0, {v: 2}));
const zukunft = await L.signiere(SECRET, Object.assign({}, p0, {iat: p0.iat + 60, exp: p0.iat + 120}));
R.token = {
  gut: (await L.pruefeToken(SECRET, t0, MO_10, {s: "hof_nord", sc: "live"})) !== null,
  gekippt: (await L.pruefeToken(SECRET, kipp, MO_10)) !== null,
  falschesSecret: (await L.pruefeToken("t".repeat(40), t0, MO_10)) !== null,
  abgelaufen: (await L.pruefeToken(SECRET, t0, MO_10 + 91000)) !== null,
  genauAblauf: (await L.pruefeToken(SECRET, t0, MO_10 + 90000)) !== null,
  andererStream: (await L.pruefeToken(SECRET, t0, MO_10, {s: "hof_sued"})) !== null,
  andererScope: (await L.pruefeToken(SECRET, t0, MO_10, {sc: "aufzeichnung"})) !== null,
  zuLang: (await L.pruefeToken(SECRET, lang, MO_10)) !== null,
  version2: (await L.pruefeToken(SECRET, v2, MO_10)) !== null,
  ausDerZukunft: (await L.pruefeToken(SECRET, zukunft, MO_10)) !== null,
  dreiTeile: (await L.pruefeToken(SECRET, t0 + ".x", MO_10)) !== null,
  nichtB64: (await L.pruefeToken(SECRET, "a+b.c/d", MO_10)) !== null,
};
R.wien = {
  winter: L.wienerZeit(MO_10),
  sommer: L.wienerZeit(Date.UTC(2026, 6, 6, 8, 0, 0)),
  sa: L.wienerZeit(SA_10),
};
R.ttl = {
  standard: L.ttlSekunden(() => undefined),
  gross: L.ttlSekunden((n) => n === "KAMERA_TOKEN_TTL" ? "600" : undefined),
  klein: L.ttlSekunden((n) => n === "KAMERA_TOKEN_TTL" ? "5" : undefined),
  muell: L.ttlSekunden((n) => n === "KAMERA_TOKEN_TTL" ? "abc" : undefined),
};
R.rec = {
  standard: L.aufzeichnungsRollen(() => undefined),
  tippfehler: L.aufzeichnungsRollen((n) => n === "KAMERA_AUFZEICHNUNG_ROLLEN" ? "monteur, Lagerleitung,helfer" : undefined),
};
console.log(JSON.stringify(R));
"""

MO_17 = "MO_17"

FAELLE = {
    "admin": {},
    "admin_ohne_origin": {"origin": None},
    "pl": {"wer": "pl"},
    "plgesperrt": {"wer": "plgesperrt"},
    "monteur": {"wer": "monteur"},
    "monteur_ohne_env": {"wer": "monteur", "env": {}},
    "helfer": {"wer": "helfer"},
    "techniker": {"wer": "techniker"},
    "obermonteur": {"wer": "obermonteur"},
    "display": {"wer": "display"},
    "terminal": {"wer": "terminal"},
    "ohnerolle": {"wer": "ohnerolle"},
    "grossadmin": {"wer": "grossadmin"},
    "buero_mo10": {"wer": "buero"},
    "lager": {"wer": "lager"},
    "inaktiv": {"wer": "inaktiv"},
    "gesperrt": {"wer": "gesperrt"},
    "gesperrt1": {"wer": "gesperrt1"},
    "env_leer": {"env": {}},
    "env_secret_kurz": {"env": {"KAMERA_TOKEN_SECRET": "kurz", "KAMERA_BACKEND_BASE": BASE}},
    "env_base_http": {"env": {"KAMERA_TOKEN_SECRET": SECRET, "KAMERA_BACKEND_BASE": "http://kamera.example.test"}},
    "env_base_fehlt": {"env": {"KAMERA_TOKEN_SECRET": SECRET}},
    "env_ttl_600": {"env": {"KAMERA_TOKEN_SECRET": SECRET, "KAMERA_BACKEND_BASE": BASE, "KAMERA_TOKEN_TTL": "600"}},
    "ohne_auth": {"auth": None},
    "falsches_jwt": {"auth": "Bearer jwt_niemand_0123456789abcdef"},
    "kein_bearer": {"auth": "Basic abc"},
    "fremder_origin": {"origin": "https://evil.example"},
    "null_origin": {"origin": "null"},
    "options": {"method": "OPTIONS", "auth": None},
    "get": {"method": "GET"},
    "rec_buero_pc": {"wer": "buero", "body": {"kamera_id": "cam1", "scope": "aufzeichnung", "geraet": "pc"}},
    "rec_buero_mobil": {"wer": "buero", "body": {"kamera_id": "cam1", "scope": "aufzeichnung", "geraet": "mobil"}},
    "rec_buero_ohne_geraet": {"wer": "buero", "body": {"kamera_id": "cam1", "scope": "aufzeichnung"}},
    "rec_lager_pc": {"wer": "lager", "body": {"kamera_id": "cam1", "scope": "aufzeichnung", "geraet": "pc"}},
    "rec_env_lager": {"wer": "lager", "body": {"kamera_id": "cam1", "scope": "aufzeichnung", "geraet": "pc"},
                      "env": {"KAMERA_TOKEN_SECRET": SECRET, "KAMERA_BACKEND_BASE": BASE,
                              "KAMERA_AUFZEICHNUNG_ROLLEN": "lagerleitung,monteur"}},
    "rec_env_admin": {"body": {"kamera_id": "cam1", "scope": "aufzeichnung", "geraet": "pc"},
                      "env": {"KAMERA_TOKEN_SECRET": SECRET, "KAMERA_BACKEND_BASE": BASE,
                              "KAMERA_AUFZEICHNUNG_ROLLEN": "lagerleitung,monteur"}},
    "rec_monteur_env": {"wer": "monteur", "body": {"kamera_id": "cam1", "scope": "aufzeichnung", "geraet": "pc"},
                        "env": {"KAMERA_TOKEN_SECRET": SECRET, "KAMERA_BACKEND_BASE": BASE,
                                "KAMERA_AUFZEICHNUNG_ROLLEN": "lagerleitung,monteur"}},
    "rec_ohne_quelle": {"body": {"kamera_id": "cam3", "scope": "aufzeichnung", "geraet": "pc"}},
    "darf_wirft": {"darfWirft": True},
    "log_wirft": {"logWirft": True},
    "kamera_ohne_regel": {"body": {"kamera_id": "cam4"}},
    "kamera_ohne_backend": {"body": {"kamera_id": "cam2"}},
    "kamera_unbekannt": {"body": {"kamera_id": "gibtsnicht"}},
    "id_pfad": {"body": {"kamera_id": "../etc"}},
    "id_leer": {"body": {}},
    "scope_falsch": {"body": {"kamera_id": "cam1", "scope": "admin"}},
    "kein_json": {"body": "kein json"},
    "array_body": {"body": "[1,2]"},
    "zu_gross": {"body": {"kamera_id": "cam1", "x": "y" * 3000}},
}

# Zeitfenster-Faelle brauchen die Zeitkonstanten aus dem Harness
ZEIT_FAELLE = {
    "buero_sa10": ("buero", "SA_10"),
    "buero_mo17": ("buero", "MO_17"),
    "buero_mo0659": ("buero", "MO_0659"),
}


def _faelle_js():
    teile = []
    for k, v in FAELLE.items():
        teile.append("%s: %s" % (json.dumps(k), json.dumps(v)))
    for k, (wer, zeit) in ZEIT_FAELLE.items():
        teile.append('%s: {"wer": %s, "now": %s}' % (json.dumps(k), json.dumps(wer), zeit))
    return "{" + ", ".join(teile) + "}"


def _lies(p):
    return io.open(p, encoding="utf-8", newline="").read()


def _lauf(node_exe, logic_src):
    with tempfile.TemporaryDirectory() as d:
        with io.open(os.path.join(d, "logic.ts"), "w", encoding="utf-8", newline="\n") as f:
            f.write(logic_src)
        with io.open(os.path.join(d, "harness.mjs"), "w", encoding="utf-8", newline="\n") as f:
            f.write(HARNESS % {"secret": json.dumps(SECRET), "base": json.dumps(BASE), "faelle": _faelle_js()})
        r = subprocess.run([node_exe, "--experimental-strip-types", "--no-warnings", "harness.mjs"], cwd=d,
                           capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=EPK_TEST_TIMEOUT)
    assert r.returncode == 0, r.stderr[-3000:]
    return json.loads(r.stdout.strip().splitlines()[-1])


@pytest.fixture(scope="module")
def R(node_exe):
    return _lauf(node_exe, _lies(LOGIC))


def _kein_geheimnis(fall):
    t = fall["text"]
    for verboten in ("http", "token", "hof_nord", "lager_ost", "m3u8", "whep", "u1", "stream"):
        assert verboten not in t, "Fehlerantwort verraet %r: %s" % (verboten, t)


# ── Erlaubt ────────────────────────────────────────────────────────────────────
def test_admin_bekommt_live_und_webrtc_adresse(R):
    a = R["admin"]
    assert a["status"] == 200, a
    j = a["json"]
    assert j["liveUrl"].startswith(BASE + "/live/hof_nord/index.m3u8?token=")
    assert j["webrtcUrl"].startswith(BASE + "/live/hof_nord/whep?token=")
    assert "aufzeichnungUrl" not in j
    assert a["okLive"] is True
    p = a["payload"]
    assert p["v"] == 1 and p["k"] == "cam1" and p["s"] == "hof_nord" and p["u"] == "u1" and p["sc"] == "live"
    assert a["cache"] == "no-store"
    assert a["acao"] == "https://epkolar.github.io"
    assert [e["ergebnis"] for e in a["calls"]["log"]] == ["erteilt"]


def test_token_lebt_hoechstens_120_sekunden(R):
    for k in ("admin", "pl", "buero_mo10", "lager", "rec_buero_pc", "env_ttl_600"):
        p = R[k]["payload"]
        assert 0 < p["exp"] - p["iat"] <= 120, (k, p)
        assert R[k]["json"]["ttl"] == p["exp"] - p["iat"]
    assert R["admin"]["json"]["ttl"] == 90
    assert R["env_ttl_600"]["json"]["ttl"] == 120
    assert R["ttl"] == {"standard": 90, "gross": 120, "klein": 30, "muell": 90}


def test_ohne_origin_serveraufruf_geht_aber_ohne_cors(R):
    a = R["admin_ohne_origin"]
    assert a["status"] == 200 and a["acao"] is None


def test_alle_vier_rollen_mit_regel_kommen_durch(R):
    for k in ("admin", "pl", "buero_mo10", "lager", "grossadmin"):
        assert R[k]["status"] == 200, (k, R[k]["status"], R[k]["text"])


# ── Monteur & Co.: nie, und VOR jeder Abfrage ─────────────────────────────────
@pytest.mark.parametrize("k", ["monteur", "helfer", "techniker", "obermonteur", "display", "terminal",
                               "ohnerolle", "monteur_ohne_env"])
def test_andere_rollen_403_ohne_adresse_und_ohne_abfrage(R, k):
    f = R[k]
    assert f["status"] == 403, (k, f)
    assert json.loads(f["text"]) == {"error": "kein_zugriff"}
    _kein_geheimnis(f)
    assert f["calls"]["darf"] == 0, "%s: Regelabfrage trotz falscher Rolle" % k
    assert f["calls"]["backend"] == 0, "%s: Backend-Zuordnung trotz falscher Rolle" % k


def test_monteur_mit_eigener_nutzerfreigabe_bleibt_draussen(R):
    """REGELN.cam1 enthaelt {user_id:'u4', erlaubt:true} - die Rollenliste ist trotzdem hart."""
    assert R["monteur"]["status"] == 403
    assert R["helfer"]["status"] == 403
    assert [e["grund"] for e in R["monteur"]["calls"]["log"]] == ["rolle"]


def test_monteur_auch_bei_aufzeichnung_und_tippfehler_in_der_konfig(R):
    f = R["rec_monteur_env"]
    assert f["status"] == 403 and f["calls"]["darf"] == 0
    _kein_geheimnis(f)
    assert R["rec"]["standard"] == ["admin", "projektleiter", "buero"]
    assert R["rec"]["tippfehler"] == ["lagerleitung"], "Konfig darf nie eine Nicht-Kamerarolle freischalten"


# ── Regeln: Sperre einzelner PL, Zeitfenster ───────────────────────────────────
def test_ausgesperrter_projektleiter_403(R):
    f = R["plgesperrt"]
    assert f["status"] == 403
    _kein_geheimnis(f)
    assert f["calls"]["darf"] == 1 and f["calls"]["backend"] == 0
    assert R["pl"]["status"] == 200, "der andere PL (gleiche Rolle) muss weiter durchkommen"


@pytest.mark.parametrize("k", ["buero_sa10", "buero_mo17", "buero_mo0659"])
def test_ausserhalb_des_zeitfensters_403(R, k):
    f = R[k]
    assert f["status"] == 403, (k, f["text"])
    _kein_geheimnis(f)
    assert R["buero_mo10"]["status"] == 200


def test_wiener_ortszeit_auch_in_der_sommerzeit(R):
    assert R["wien"]["winter"] == {"dow": 1, "minuten": 600}
    assert R["wien"]["sommer"] == {"dow": 1, "minuten": 600}
    assert R["wien"]["sa"] == {"dow": 6, "minuten": 600}


def test_kamera_ohne_regel_oder_unbekannt_403_ohne_backend(R):
    for k in ("kamera_ohne_regel", "kamera_unbekannt"):
        assert R[k]["status"] == 403, k
        assert R[k]["calls"]["backend"] == 0
        _kein_geheimnis(R[k])


def test_kamera_ohne_backend_zuordnung_503(R):
    f = R["kamera_ohne_backend"]
    assert f["status"] == 503 and json.loads(f["text"]) == {"error": "nicht_konfiguriert"}
    _kein_geheimnis(f)


# ── Konfiguration ─────────────────────────────────────────────────────────────
@pytest.mark.parametrize("k", ["env_leer", "env_secret_kurz", "env_base_http", "env_base_fehlt"])
def test_fehlende_konfiguration_503(R, k):
    f = R[k]
    assert f["status"] == 503, (k, f["text"])
    assert json.loads(f["text"]) == {"error": "nicht_konfiguriert"}
    assert f["calls"]["darf"] == 0
    _kein_geheimnis(f)


# ── Anmeldung, Nutzerzustand, Herkunft, Methode ───────────────────────────────
@pytest.mark.parametrize("k", ["ohne_auth", "falsches_jwt", "kein_bearer"])
def test_ohne_gueltige_anmeldung_401(R, k):
    f = R[k]
    assert f["status"] == 401 and json.loads(f["text"]) == {"error": "nicht_angemeldet"}
    assert f["calls"]["nutzer"] == 0
    _kein_geheimnis(f)


@pytest.mark.parametrize("k", ["inaktiv", "gesperrt", "gesperrt1"])
def test_inaktiv_oder_gesperrt_403(R, k):
    f = R[k]
    assert f["status"] == 403 and f["calls"]["darf"] == 0
    _kein_geheimnis(f)


def test_fremde_herkunft_wird_abgewiesen_ohne_cors(R):
    for k in ("fremder_origin", "null_origin"):
        f = R[k]
        assert f["status"] == 403 and f["acao"] is None, k
        assert f["calls"]["auth"] == 0
        _kein_geheimnis(f)


def test_preflight_und_methode(R):
    assert R["options"]["status"] == 204 and R["options"]["acao"] == "https://epkolar.github.io"
    assert R["get"]["status"] == 405


@pytest.mark.parametrize("k", ["id_pfad", "id_leer", "scope_falsch", "kein_json", "array_body", "zu_gross"])
def test_ungueltige_anfrage_400(R, k):
    f = R[k]
    assert f["status"] == 400 and json.loads(f["text"]) == {"error": "ungueltig"}, (k, f)
    assert f["calls"]["darf"] == 0


def test_datenbankfehler_ist_500_ohne_details(R):
    f = R["darf_wirft"]
    assert f["status"] == 500 and json.loads(f["text"]) == {"error": "intern"}
    _kein_geheimnis(f)


def test_protokollfehler_aendert_die_entscheidung_nicht(R):
    assert R["log_wirft"]["status"] == 200


# ── Aufzeichnung ──────────────────────────────────────────────────────────────
def test_aufzeichnung_nur_am_pc_und_nur_fuer_aufzeichnungsrollen(R):
    a = R["rec_buero_pc"]
    assert a["status"] == 200
    assert a["json"]["aufzeichnungUrl"].startswith(BASE + "/aufzeichnung/hof_nord_rec?token=")
    assert "liveUrl" not in a["json"] and "webrtcUrl" not in a["json"]
    assert a["payload"]["sc"] == "aufzeichnung" and a["payload"]["s"] == "hof_nord_rec"
    for k in ("rec_buero_mobil", "rec_buero_ohne_geraet", "rec_lager_pc", "rec_env_admin"):
        assert R[k]["status"] == 403, k
        assert R[k]["calls"]["darf"] == 0, k
        _kein_geheimnis(R[k])
    assert R["rec_env_lager"]["status"] == 200, "Konfig KAMERA_AUFZEICHNUNG_ROLLEN wirkt"
    assert R["rec_ohne_quelle"]["status"] == 503


# ── Token-Vertrag (Referenz-Pruefer fuer den Reverse-Proxy) ───────────────────
def test_token_pruefer_vertrag(R):
    t = R["token"]
    assert t["gut"] is True
    for k in ("gekippt", "falschesSecret", "abgelaufen", "genauAblauf", "andererStream", "andererScope",
              "zuLang", "version2", "ausDerZukunft", "dreiTeile", "nichtB64"):
        assert t[k] is False, k


def test_readme_beschreibt_den_vertrag():
    r = _lies(README)
    for teil in ("base64url", "HMAC-SHA256", "KAMERA_TOKEN_SECRET", "KAMERA_BACKEND_BASE", "constant-time",
                 '"v": 1', "exp - iat <= 120", "/live/<s>/index.m3u8", "/live/<s>/whep", "/aufzeichnung/<s>",
                 "NOT deployed", "verify_jwt", "kamera_darf_sehen"):
        assert teil in r, teil


# ── index.ts: Verdrahtung ─────────────────────────────────────────────────────
def test_index_ts_verdrahtet_mit_dem_jwt_des_aufrufers():
    s = _lies(INDEX_TS)
    assert 'from "./logic.ts"' in s
    assert "auth.getUser(jwt)" in s
    assert '.rpc("kamera_darf_sehen", { p_kamera: kameraId })' in s
    assert "p_zeitpunkt:" not in s, "Zeitpunkt darf nie vom Aufrufer kommen"
    assert 'Authorization: "Bearer " + jwt' in s
    assert 'select("id, role, active, locked")' in s
    assert 'Deno.env.get("KAMERA' not in s, "Kamera-Secrets nur ueber logic.ts/deps.env"


def test_kein_geheimnis_im_quelltext():
    for p in (LOGIC, INDEX_TS, README):
        s = _lies(p)
        assert not re.search(r"rtsp://", s, re.I), p
        assert not re.search(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", s), "IP-Adresse in %s" % p
        assert not re.search(r"(password|passwort)\s*[:=]\s*\S", s, re.I), p


# ── Umkehrproben: die Riegel haben Zaehne ─────────────────────────────────────
def _mutiert(alt, neu):
    s = _lies(LOGIC)
    assert s.count(alt) == 1, alt
    return s.replace(alt, neu, 1)


def test_umkehrprobe_ohne_rollensperre_fragt_monteur_die_db(node_exe):
    R2 = _lauf(node_exe, _mutiert("if (ERLAUBTE_ROLLEN.indexOf(rolle) < 0) {", "if (false) {"))
    assert R2["monteur"]["calls"]["darf"] == 1, "Umkehrprobe: Rollensperre-Riegel blind"


def test_umkehrprobe_ohne_regelpruefung_kaeme_der_gesperrte_pl_durch(node_exe):
    R2 = _lauf(node_exe, _mutiert("if (darf !== true) {", "if (false) {"))
    assert R2["plgesperrt"]["status"] == 200
    assert R2["buero_sa10"]["status"] == 200


def test_umkehrprobe_ttl_obergrenze(node_exe):
    R2 = _lauf(node_exe, _mutiert("export const TTL_MAX = 120;", "export const TTL_MAX = 600;"))
    assert R2["env_ttl_600"]["json"]["ttl"] == 600


def test_umkehrprobe_ablauf_im_pruefer(node_exe):
    R2 = _lauf(node_exe, _mutiert("if (p.exp <= jetzt) return null;", ""))
    assert R2["token"]["abgelaufen"] is True


def test_umkehrprobe_aufzeichnung_am_handy(node_exe):
    R2 = _lauf(node_exe, _mutiert('(geraet !== "pc" || ', "(false || "))
    assert R2["rec_buero_mobil"]["status"] == 200
