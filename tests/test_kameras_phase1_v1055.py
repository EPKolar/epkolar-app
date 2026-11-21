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
const AUFBEWAHRUNG = {cam1: 3, cam3: 5};

async function lauf(f) {
  const o = Object.assign({wer: "admin", body: {kamera_id: "cam1"}, env: ENV_OK, now: MO_10,
                           origin: "https://epkolar.github.io", method: "POST", auth: undefined}, f);
  const calls = {auth: 0, nutzer: 0, darf: 0, bereich: 0, bereichArgs: null, backend: 0, log: []};
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
    // Attrappe von kamera_darf_sehen_bereich: der ausfuehrbare Spiegel entscheideBereich() aus logic.ts
    darfSehenBereich: async (jwt, k, vonIso, bisIso) => {
      calls.bereich++;
      calls.bereichArgs = [k, vonIso, bisIso];
      const wer = /^jwt_([a-z0-9]+)_/.exec(jwt)[1];
      const u = USERS[wer];
      return L.entscheideBereich(REGELN[k] || [], {id: u.id, role: String(u.role || "").trim()},
                                 Date.parse(vonIso), Date.parse(bisIso), o.now, AUFBEWAHRUNG[k] || 3);
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


# Aufzeichnungsbereiche (Wiener Ortszeit, November = CET = UTC+1). Abfragezeit ist immer MO_10 = Mo 23.11.2026 10:00.
# Regel buero auf cam1: Mo-Fr 07:00-17:00 (bis exklusiv); Aufbewahrung cam1 = 3 Tage.
def _rec(von, bis, **mehr):
    b = {"kamera_id": "cam1", "scope": "aufzeichnung", "geraet": "pc", "von": von, "bis": bis}
    b.update(mehr)
    return b


MO_08_09 = ("2026-11-23T07:00:00Z", "2026-11-23T08:00:00Z")      # Mo 08:00-09:00 - Regel gilt durchgehend
REC_GUT = _rec(*MO_08_09)

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
    "rec_buero_pc": {"wer": "buero", "body": REC_GUT},
    "rec_buero_mobil": {"wer": "buero", "body": _rec(*MO_08_09, geraet="mobil")},
    "rec_buero_ohne_geraet": {"wer": "buero", "body": {k: v for k, v in REC_GUT.items() if k != "geraet"}},
    "rec_lager_pc": {"wer": "lager", "body": REC_GUT},
    "rec_env_lager": {"wer": "lager", "body": REC_GUT,
                      "env": {"KAMERA_TOKEN_SECRET": SECRET, "KAMERA_BACKEND_BASE": BASE,
                              "KAMERA_AUFZEICHNUNG_ROLLEN": "lagerleitung,monteur"}},
    "rec_env_admin": {"body": REC_GUT,
                      "env": {"KAMERA_TOKEN_SECRET": SECRET, "KAMERA_BACKEND_BASE": BASE,
                              "KAMERA_AUFZEICHNUNG_ROLLEN": "lagerleitung,monteur"}},
    "rec_monteur_env": {"wer": "monteur", "body": REC_GUT,
                        "env": {"KAMERA_TOKEN_SECRET": SECRET, "KAMERA_BACKEND_BASE": BASE,
                                "KAMERA_AUFZEICHNUNG_ROLLEN": "lagerleitung,monteur"}},
    "rec_ohne_quelle": {"body": dict(REC_GUT, kamera_id="cam3")},
    # ── Befund 19.11.: Aufzeichnungsbereich (Angriffe) ──
    # Samstag 21.11. 10-11 unter der Mo-Fr-Regel, abgefragt am Montag 10:00 (Regel gilt JETZT) -> 403
    "rec_buero_samstag": {"wer": "buero", "body": _rec("2026-11-21T09:00:00Z", "2026-11-21T10:00:00Z")},
    # teils ausserhalb: Mo 06:30-07:30 (Beginn vor 07:00) und Fr 16:30-17:01 (eine Minute nach 17:00)
    "rec_buero_teils_morgens": {"wer": "buero", "body": _rec("2026-11-23T05:30:00Z", "2026-11-23T06:30:00Z")},
    "rec_buero_teils_abends": {"wer": "buero", "body": _rec("2026-11-20T15:30:00Z", "2026-11-20T16:01:00Z")},
    # Grenzfall erlaubt: Fr 16:00-17:00 (bis exklusiv) und Zeitzonen-Schreibweise +01:00
    "rec_buero_bis_genau_17": {"wer": "buero", "body": _rec("2026-11-20T16:00:00+01:00", "2026-11-20T17:00:00+01:00")},
    # ausserhalb der Aufbewahrung (cam1 = 3 Tage): Do 19.11. 10-11 (Werktag im Fenster) -> 403 aus der DB-Pruefung
    "rec_buero_aufbewahrung": {"wer": "buero", "body": _rec("2026-11-19T09:00:00Z", "2026-11-19T10:00:00Z")},
    # admin hat eine Regel ohne Fenster: Samstag ist fuer ihn erlaubt (Gegenprobe: Regel, nicht Wochentag, entscheidet)
    "rec_admin_samstag": {"body": _rec("2026-11-21T09:00:00Z", "2026-11-21T10:00:00Z")},
    # ungueltige Bereiche -> 400, ohne jede DB-Abfrage
    "rec_aelter_als_30_tage": {"wer": "buero", "body": _rec("2026-10-01T08:00:00Z", "2026-10-01T09:00:00Z")},
    "rec_zukunft": {"wer": "buero", "body": _rec("2026-11-23T08:30:00Z", "2026-11-23T09:30:00Z")},
    "rec_spanne_zu_lang": {"wer": "buero", "body": _rec("2026-11-23T06:59:00Z", "2026-11-23T09:00:00Z")},
    "rec_von_gleich_bis": {"wer": "buero", "body": _rec("2026-11-23T07:00:00Z", "2026-11-23T07:00:00Z")},
    "rec_umgekehrt": {"wer": "buero", "body": _rec("2026-11-23T08:00:00Z", "2026-11-23T07:00:00Z")},
    "rec_ohne_bereich": {"wer": "buero", "body": {"kamera_id": "cam1", "scope": "aufzeichnung", "geraet": "pc"}},
    "rec_ohne_zone": {"wer": "buero", "body": _rec("2026-11-23T07:00:00", "2026-11-23T08:00:00")},
    "rec_bruchteil": {"wer": "buero", "body": _rec("2026-11-23T07:00:00.5Z", "2026-11-23T08:00:00Z")},
    "rec_zahl": {"wer": "buero", "body": _rec(1795417200, 1795420800)},
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


# ── Befund 19.11.: Aufzeichnung nur fuer den freigegebenen BEREICH (nicht nur "Regel gilt jetzt") ──────────
def test_aufzeichnung_bereich_signiert_in_token_und_adresse(R):
    a = R["rec_buero_pc"]
    assert a["status"] == 200, a["text"]
    p = a["payload"]
    # Mo 23.11.2026 08:00 Wien = 07:00Z
    assert p["von"] == 1795417200 and p["bis"] == 1795420800, p
    assert a["json"]["von"] == p["von"] and a["json"]["bis"] == p["bis"]
    assert a["json"]["aufzeichnungUrl"].endswith("&von=1795417200&bis=1795420800")
    assert a["calls"]["darf"] == 1 and a["calls"]["bereich"] == 1
    # an die DB geht der normalisierte Bereich (ISO, UTC) - dieselben Augenblicke wie im Token
    assert a["calls"]["bereichArgs"] == ["cam1", "2026-11-23T07:00:00.000Z", "2026-11-23T08:00:00.000Z"]
    assert "von" not in R["admin"]["payload"] and "bis" not in R["admin"]["payload"], "Live-Token ohne Bereich"


@pytest.mark.parametrize("k", ["rec_buero_samstag", "rec_buero_teils_morgens", "rec_buero_teils_abends",
                               "rec_buero_aufbewahrung"])
def test_angriff_aufzeichnung_ausserhalb_des_bereichs_403(R, k):
    """Die Regel gilt JETZT (Mo 10:00) - das darf keine Aufnahmen ausserhalb des Fensters freigeben."""
    f = R[k]
    assert f["status"] == 403, (k, f["status"], f["text"])
    assert json.loads(f["text"]) == {"error": "kein_zugriff"}
    _kein_geheimnis(f)
    assert f["calls"]["darf"] == 1, "Regel jetzt erfuellt - abgewiesen wird erst durch die Bereichspruefung"
    assert f["calls"]["bereich"] == 1 and f["calls"]["backend"] == 0
    assert [e["grund"] for e in f["calls"]["log"]] == ["bereich"]


def test_aufzeichnung_bereich_grenzfaelle_erlaubt(R):
    assert R["rec_buero_bis_genau_17"]["status"] == 200, "bis 17:00 exklusiv - 16:00-17:00 liegt ganz im Fenster"
    assert R["rec_buero_bis_genau_17"]["payload"]["von"] == 1795186800
    assert R["rec_admin_samstag"]["status"] == 200, "Regel ohne Fenster deckt auch den Samstag"


@pytest.mark.parametrize("k", ["rec_aelter_als_30_tage", "rec_zukunft", "rec_spanne_zu_lang", "rec_von_gleich_bis",
                               "rec_umgekehrt", "rec_ohne_bereich", "rec_ohne_zone", "rec_bruchteil", "rec_zahl"])
def test_aufzeichnung_ungueltiger_bereich_400_ohne_abfrage(R, k):
    f = R[k]
    assert f["status"] == 400 and json.loads(f["text"]) == {"error": "ungueltig"}, (k, f["status"], f["text"])
    assert f["calls"]["darf"] == 0 and f["calls"]["bereich"] == 0 and f["calls"]["backend"] == 0


def test_geraet_ist_keine_sicherheitsgrenze_dokumentiert():
    s = _lies(LOGIC)
    assert "KEINE Sicherheitsgrenze" in s
    i = s.index("export async function bearbeite(")
    t = s[i:]
    # die Bereichspruefung haengt NICHT an geraet und steht vor dem Backend
    assert t.index("deps.darfSehenBereich(") < t.index("deps.ladeBackend(")
    zeile = [z for z in t.split("\n") if "deps.darfSehenBereich(" in z][0]
    assert "geraet" not in zeile
    r = _lies(README)
    assert "NOT a security control" in r


def test_live_bleibt_bei_jetzt(R):
    a = R["admin"]
    assert a["calls"]["bereich"] == 0, "Live fragt keinen Bereich ab"
    assert R["buero_mo10"]["status"] == 200 and R["buero_sa10"]["status"] == 403


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
                 # Pin angepasst 20.11.2026 (feature/kamera-gateway): Funktion ist deployt ("NOT deployed" -> "Deployed"),
                 # Basisadresse heisst bevorzugt KAMERA_GATEWAY_BASE (alter Name bleibt dokumentiert, siehe oben).
                 "Deployed", "KAMERA_GATEWAY_BASE", "verify_jwt", "kamera_darf_sehen"):
        assert teil in r, teil


# ── index.ts: Verdrahtung ─────────────────────────────────────────────────────
def test_index_ts_verdrahtet_mit_dem_jwt_des_aufrufers():
    s = _lies(INDEX_TS)
    assert 'from "./logic.ts"' in s
    assert "auth.getUser(jwt)" in s
    assert '.rpc("kamera_darf_sehen", { p_kamera: kameraId })' in s
    assert '.rpc("kamera_darf_sehen_bereich", { p_kamera: kameraId, p_von: vonIso, p_bis: bisIso })' in s
    i = s.index("darfSehenBereich: async")
    assert "aufruferClient(jwt).rpc(" in s[i:s.index("},", i)], "Bereichspruefung mit dem JWT des Aufrufers"
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
    # geraet ist nur Bedienkomfort: ohne den Abgleich kaeme ein Handy mit ERLAUBTEM Bereich durch (das ist ok),
    # die Angriffe auf den Bereich bleiben trotzdem 403 - die Kontrolle sitzt in Rolle + Bereichspruefung.
    R2 = _lauf(node_exe, _mutiert('(geraet !== "pc" || ', "(false || "))
    assert R2["rec_buero_mobil"]["status"] == 200
    assert R2["rec_buero_samstag"]["status"] == 403 and R2["rec_lager_pc"]["status"] == 403


def test_umkehrprobe_alte_logik_ohne_bereichspruefung(node_exe):
    """Stand vor dem Fix: Aufzeichnung nur ueber darfSehen(jetzt). Dann kaemen alle Bereichs-Angriffe durch."""
    R2 = _lauf(node_exe, _mutiert("if (darfBereich !== true) {", "if (false) {"))
    for k in ("rec_buero_samstag", "rec_buero_teils_morgens", "rec_buero_teils_abends", "rec_buero_aufbewahrung"):
        assert R2[k]["status"] == 200, (k, R2[k]["status"])


def test_umkehrprobe_nur_der_anfang_statt_jeder_minute(node_exe):
    R2 = _lauf(node_exe, _mutiert("for (let t = Math.floor(vonMs / 60000) * 60000 + 60000; t < bisMs; t += 60000) {",
                                  "for (let t = bisMs; t < bisMs; t += 60000) {"))
    assert R2["rec_buero_teils_abends"]["status"] == 200, "Umkehrprobe: Minutenpruefung waere blind"
    assert R2["rec_buero_samstag"]["status"] == 403


def test_umkehrprobe_aufbewahrung_im_spiegel(node_exe):
    R2 = _lauf(node_exe, _mutiert("if (!(aufbewahrungTage > 0) || vonMs < nowMs - aufbewahrungTage * 24 * 60 * 60 * 1000) return false;", ""))
    assert R2["rec_buero_aufbewahrung"]["status"] == 200


# ══════════════════════════════════════════════════════════════════════════════
# TEIL B: App-Bereich "Kameras" (index.html) - reine Helfer + Ansicht in Node.
# Der Block //@KAMERAS-START..END laeuft gegen eine Mini-React-Attrappe (Hooks,
# Effekte, erneutes Zeichnen) und gezaehlte Attrappen fuer _sbGet/fetch. So wird
# JEDER Zweig der Ansicht wirklich ausgefuehrt - ein falscher Name faellt als
# ReferenceError auf, nicht erst im Browser.
# ══════════════════════════════════════════════════════════════════════════════
INDEX = os.path.join(WURZEL, "index.html")
SQL = os.path.join(WURZEL, "sql", "KAMERAS_v1_ENTWURF.sql")
SQL_RUECK = os.path.join(WURZEL, "sql", "KAMERAS_v1_RUECKNAHME.sql")
DOKU = os.path.join(WURZEL, "docs", "kameras", "PHASE1_2026-11-19.md")


def _index():
    return _lies(INDEX)


def _block(s=None):
    s = s if s is not None else _index()
    i = s.index("//@KAMERAS-START")
    j = s.index("//@KAMERAS-END", i)
    return s[i:j]


RENDER_PRELUDE = r"""
const FRAG = Symbol('frag');
const React = {Fragment: FRAG, createElement(type, props) {
  const kinder = Array.prototype.slice.call(arguments, 2);
  return {type, props: props || {}, children: kinder};
}};
const store = new Map(); let cur = null; let dirty = false; let effects = [];
function useState(init) {
  const st = cur; const i = st.i++;
  if (!(i in st.vals)) st.vals[i] = typeof init === 'function' ? init() : init;
  return [st.vals[i], function (v) { const nv = typeof v === 'function' ? v(st.vals[i]) : v; if (nv !== st.vals[i]) { st.vals[i] = nv; dirty = true; } }];
}
function useEffect(fn, deps) {
  const st = cur; const i = st.i++; const prev = st.vals[i];
  const changed = !prev || !deps || deps.length !== prev.deps.length || deps.some(function (d, k) { return d !== prev.deps[k]; });
  if (!changed) return;
  const alt = prev ? prev.cleanup : null;
  st.vals[i] = {deps: deps || [], cleanup: null};
  effects.push(function () { if (alt) alt(); const c = fn(); st.vals[i].cleanup = typeof c === 'function' ? c : null; });
}
function useRef(x) { const st = cur; const i = st.i++; if (!(i in st.vals)) st.vals[i] = {current: x === undefined ? null : x}; return st.vals[i]; }
const _react = {useState: {call: function (_, x) { return useState(x); }}, useEffect: {call: function (_, f, d) { return useEffect(f, d); }},
                useRef: {call: function (_, x) { return useRef(x); }}};
function rend(el, pfad) {
  if (el === null || el === undefined || el === false || el === true || el === '') return null;
  if (typeof el === 'string' || typeof el === 'number') return String(el);
  if (Array.isArray(el)) return el.map(function (x, i) { return rend(x, pfad + '.' + i); });
  if (el.type === FRAG) return rend(el.children, pfad + '~' + (el.props.key || ''));
  if (typeof el.type === 'function') {
    const key = pfad + '/' + el.type.name + ':' + (el.props.key === undefined ? '' : el.props.key);
    let st = store.get(key); if (!st) { st = {vals: {}}; store.set(key, st); }
    st.i = 0; cur = st;
    const out = el.type(Object.assign({}, el.props, {children: el.children}));
    return rend(out, key);
  }
  return {tag: el.type, props: el.props, kinder: rend(el.children, pfad + '>' + el.type)};
}
let baum = null;
async function ruhe(wurzel) {
  for (let n = 0; n < 40; n++) {
    dirty = false; effects = [];
    baum = rend(wurzel, 'r');
    const ef = effects; effects = [];
    ef.forEach(function (f) { f(); });
    for (let k = 0; k < 6; k++) await new Promise(function (r) { setTimeout(r, 0); });
    if (!dirty && !ef.length) return baum;
  }
  throw new Error('keine Ruhe');
}
function text(t) { if (t === null) return ''; if (typeof t === 'string') return t; if (Array.isArray(t)) return t.map(text).join(' '); return text(t.kinder); }
function alle(t, pred, out) { out = out || []; if (!t || typeof t === 'string') return out; if (Array.isArray(t)) { t.forEach(function (x) { alle(x, pred, out); }); return out; } if (pred(t)) out.push(t); alle(t.kinder, pred, out); return out; }
function knopf(t, wort) { const k = alle(t, function (n) { return n.tag === 'button' && text(n).trim() === wort; }); if (!k.length) throw new Error('Knopf fehlt: ' + wort); return k[0]; }
function knopfHat(t, wort) { return alle(t, function (n) { return n.tag === 'button' && text(n).trim() === wort; }).length > 0; }
async function klick(wurzel, wort) { knopf(baum, wort).props.onClick({}); return await ruhe(wurzel); }

// Attrappen der App-Umgebung
const NIX = function () {};
const UI = new Proxy({}, {get: function (_, k) { if (k === 'zahlen') return {fontVariantNumeric: 'tabular-nums'}; if (typeof k === 'string' && /^f[A-Z]/.test(k)) return 14; if (typeof k === 'string' && /^r[A-Z]/.test(k)) return 8; return '#123456'; }});
const V = new Proxy({}, {get: function () { return '#654321'; }});
const bsS = function () { return {minHeight: 44}; }; const bpS = {minHeight: 44}; const bdS = {minHeight: 44};
const BP_MOB = 600; const TIME_DAY = 24 * 3600 * 1000; const SUPABASE_URL = 'https://sb.example.test';
function _ik(n) { return React.createElement('svg', {ik: n}); }
function _ikT(n, t) { return React.createElement('span', {ik: n}, t); }
function _fT(i) { return i; }
function _sbH() { return {apikey: 'k', Authorization: 'Bearer t'}; }
function _rlsLeer(l) { return !!(l && l.__rlsFehler); }
const LS = {};
const localStorage = {getItem: function (k) { return k in LS ? LS[k] : null; }, setItem: function (k, v) { LS[k] = String(v); }, removeItem: function (k) { delete LS[k]; }};
const ZAEHL = {get: [], post: [], upsert: [], del: [], fetch: [], pruef: []};
let SZENE = {};
async function _sbGet(tab, f) { ZAEHL.get.push(tab + '?' + f); const d = SZENE.db || {}; if (d[tab] instanceof Error) throw d[tab]; return JSON.parse(JSON.stringify(d[tab] || [])); }
async function _sbPost(tab, row) { ZAEHL.post.push({tab: tab, row: row}); return [row]; }
async function _sbUpsert(tab, row) { ZAEHL.upsert.push({tab: tab, row: row}); return [row]; }
async function _sbDelete(tab, id) { ZAEHL.del.push({tab: tab, id: id}); return {ok: 1}; }
// Seit v1060 (Einrichtung, nur Admin): die Einrichtungsabfrage an kamera-stream und der Gesundheitsabruf des
// Video-Hosts laufen getrennt in ZAEHL.pruef - ZAEHL.fetch zaehlt weiter NUR Stream-Anfragen. Ohne Vorgabe
// meldet die Attrappe "alles eingerichtet", damit die Phase-1-Szenarien die Live-Kacheln wie bisher sehen.
async function fetch(url, init) {
  const _b = init && init.body ? JSON.parse(init.body) : null;
  if (_b && _b.pruefen === 'einrichtung') { ZAEHL.pruef.push('fn'); const e = SZENE.einrichtung || {status: 200, json: {einrichtung: true, secret: true, basis: 'https://video.example.test'}};
    if (e.wirft) throw new Error('netz'); return {status: e.status, ok: e.status === 200, json: async function () { return e.json; }}; }
  if (/\/gesund$/.test(url)) { ZAEHL.pruef.push('gesund:' + url); const g = SZENE.gesund || {status: 200};
    if (g.wirft) throw new Error('netz'); return {status: g.status, ok: g.status === 200, json: async function () { return null; }}; }
  return _fetchStream(url, init); }
async function _fetchStream(url, init) { ZAEHL.fetch.push({url: url, body: init && init.body ? JSON.parse(init.body) : null}); const a = SZENE.fetch || {status: 503, json: {error: 'nicht_konfiguriert'}}; return {status: a.status, ok: a.status === 200, json: async function () { return a.json; }}; }
const window = {innerWidth: 1440, location: {search: ''}, matchMedia: function () { return {matches: !!SZENE.fein}; }, confirm: function () { return true; }, __toast: NIX};
"""


def _layout_echt():
    """Die ECHTE _layoutStufe aus index.html (samt BP_BREIT/BP_QUER) - seit 20.11.2026 waehlt KameraView die Spalten
    daraus. Keine Attrappe: die Kachel-Spalten haengen an genau dieser Funktion."""
    m = re.search(r"const BP_BREIT=\d+;const BP_QUER=\d+;function _layoutStufe\(w,h\)\{.*?return \"mittel\";\}", _index(), re.S)
    assert m, "_layoutStufe nicht gefunden"
    return "\n" + m.group(0).replace("const ", "var ") + "\n"


def _render_lauf(node_exe, block, szenen_js):
    js = RENDER_PRELUDE + _layout_echt() + block + "\n(async function(){\nconst OUT={};\n" + szenen_js + \
        "\nconsole.log(JSON.stringify(OUT));process.exit(0);\n})().catch(function(e){console.error(e&&e.stack||e);process.exit(3);});\n"
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "render.cjs")
        with io.open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(js)
        r = subprocess.run([node_exe, p], capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=EPK_TEST_TIMEOUT)
    assert r.returncode == 0, r.stderr[-3000:]
    return json.loads(r.stdout.strip().splitlines()[-1])


SZENEN = r"""
// Pin angepasst 20.11.2026 (feature/kamera-gateway): der Aufzeichnungs-Bereich ist in der App aus (Owner: Aufnahmen
// ueber die Surveillance Station). Diese Szenarien pruefen die vorhandene Aufzeichnungs-Oberflaeche weiter -> Schalter an.
KAMERA_REC_UI = true;
function reset(s) { SZENE = s; store.clear(); _kamBackend.fehlt = false; ['get','post','upsert','del','fetch'].forEach(function (k) { ZAEHL[k].length = 0; }); }
const KAMS = [{id: 'cam1', name: 'Kamera 1', standort: 'Hof', aktiv: true, aufbewahrung_tage: 3},
              {id: 'cam2', name: 'Kamera 2', standort: 'Lager', aktiv: false, aufbewahrung_tage: 3},
              {id: 'cam3', name: 'Kamera 3', standort: 'Tor', aktiv: true, aufbewahrung_tage: 5}];
const USERS = [{id: 'u1', name: 'Anna Admin', role: 'admin', active: 1}, {id: 'u2', name: 'Paul PL', role: 'projektleiter', active: 1},
               {id: 'u4', name: 'Max Monteur', role: 'monteur', active: 1}, {id: 'u7', name: 'Lea Lager', role: 'lagerleitung', active: 1}];
const REGELN = [{id: 'z1', kamera_id: 'cam1', rolle: 'projektleiter', user_id: null, wochentage: [1,2,3,4,5,6,7], von: null, bis: null, erlaubt: true},
                {id: 'z2', kamera_id: 'cam1', rolle: null, user_id: 'u2', wochentage: [1,2,3,4,5,6,7], von: null, bis: null, erlaubt: false, bemerkung: 'gesperrt'},
                {id: 'z3', kamera_id: 'cam1', rolle: 'buero', user_id: null, wochentage: [1,2,3,4,5], von: '07:00:00', bis: '17:00:00', erlaubt: true}];
function wurzel(rolle, ww) { return React.createElement(KameraView, {curUser: {id: 'x', role: rolle}, ww: ww, users: USERS}); }

// 1) Admin am PC, Backend fehlt (503)
reset({db: {kameras: KAMS, kamera_zugriff: REGELN}, fein: true});
let w = wurzel('admin', 1440); await ruhe(w);
OUT.admin_pc = {text: text(baum), fetch: ZAEHL.fetch.slice(), get: ZAEHL.get.slice(),
  kacheln: alle(baum, function (n) { return n.tag === 'video'; }).length,
  raster: alle(baum, function (n) { return n.props && n.props.style && n.props.style.gridTemplateColumns; }).map(function (n) { return n.props.style.gridTemplateColumns; })};
await klick(w, '3×3');
OUT.admin_3x3 = alle(baum, function (n) { return n.props && n.props.style && n.props.style.gridTemplateColumns; }).map(function (n) { return n.props.style.gridTemplateColumns; });
await klick(w, 'Einzeln');
OUT.admin_einzeln = {kacheln: alle(baum, function (n) { return n.tag === 'video'; }).length, text: text(baum)};
await klick(w, 'Verwaltung');
OUT.verw = text(baum);
await klick(w, 'Neue Kamera');
await klick(w, 'Speichern');
OUT.verw_leer = {text: text(baum), upsert: ZAEHL.upsert.length};
const namefeld = alle(baum, function (n) { return n.tag === 'input' && n.props.maxLength === 80; })[0];
namefeld.props.onChange({target: {value: 'Hof Nord'}}); await ruhe(w);
await klick(w, 'Speichern');
OUT.verw_neu = ZAEHL.upsert.slice();
const zeile = alle(baum, function (n) { return n.tag === 'button' && text(n).indexOf('Kamera 1') === 0; })[0];
zeile.props.onClick({}); await ruhe(w);
OUT.editor = text(baum);
await klick(w, 'Sperre'); await klick(w, 'Person');
const sel = alle(baum, function (n) { return n.tag === 'select'; })[0];
OUT.personen = alle(sel, function (n) { return n.tag === 'option'; }).map(function (n) { return text(n); });
await klick(w, 'Regel speichern');
OUT.ohne_person = {text: text(baum), post: ZAEHL.post.length};
sel.props.onChange({target: {value: 'u2'}}); await ruhe(w);
await klick(w, 'Regel speichern');
OUT.regel_neu = ZAEHL.post.slice();
await klick(w, 'Aufzeichnungen');
_kamBackend.fehlt = false;
// Vortag waehlen (heute 08:00 laege je nach Uhrzeit des Testlaufs noch in der Zukunft)
const tagKnoepfe = alle(baum, function (n) { return n.tag === 'button' && /^[A-Z][a-z] \d\d\.\d\d\.$/.test(text(n).trim()); });
OUT.rec_tage = tagKnoepfe.length;
tagKnoepfe[1].props.onClick({}); await ruhe(w);
await klick(w, 'Aufzeichnung laden');
OUT.rec = {text: text(baum), fetch: ZAEHL.fetch.slice()};
// Server lehnt den Zeitraum ab (403) -> eigener Hinweis
SZENE.fetch = {status: 403, json: {error: 'kein_zugriff'}};
_kamBackend.fehlt = false;
await klick(w, 'Aufzeichnung laden');
OUT.rec_403 = text(baum);
// Zeitpunkt in der Zukunft (heute 23:45): kein Abruf, Hinweis
tagKnoepfe[0].props.onClick({}); await ruhe(w);
const zeitfeld = alle(baum, function (n) { return n.tag === 'input' && n.props.type === 'time'; })[0];
zeitfeld.props.onChange({target: {value: '23:45'}}); await ruhe(w);
const vorher = ZAEHL.fetch.length;
const jetztStd = new Date().getHours() * 60 + new Date().getMinutes();
await klick(w, 'Aufzeichnung laden');
OUT.rec_zukunft = {text: text(baum), neu: ZAEHL.fetch.length - vorher, spaet: jetztStd >= 23 * 60 + 45};

// 2) Monteur: nichts, kein einziger Abruf
reset({db: {kameras: KAMS}, fein: true});
w = wurzel('monteur', 1440); await ruhe(w);
OUT.monteur = {baum: baum, get: ZAEHL.get.length, fetch: ZAEHL.fetch.length};
reset({db: {kameras: KAMS}, fein: true});
w = wurzel('helfer', 390); await ruhe(w);
OUT.helfer = {baum: baum, get: ZAEHL.get.length, fetch: ZAEHL.fetch.length};

// 3) Projektleiter am Handy: nur Live
reset({db: {kameras: KAMS}, fein: false});
w = wurzel('projektleiter', 390); await ruhe(w);
OUT.pl_handy = {text: text(baum), fetch: ZAEHL.fetch.slice(), knoepfe: alle(baum, function (n) { return n.tag === 'button'; }).map(text),
  raster: alle(baum, function (n) { return n.props && n.props.style && n.props.style.gridTemplateColumns; }).map(function (n) { return n.props.style.gridTemplateColumns; })};
// Tablet quer (1280 px, Touch) bleibt "Handy/Tablet"
reset({db: {kameras: KAMS}, fein: false});
w = wurzel('admin', 1280); await ruhe(w);
OUT.tablet = {knoepfe: alle(baum, function (n) { return n.tag === 'button'; }).map(text), fetch: ZAEHL.fetch.map(function (f) { return f.body.geraet; })};

// 4) Tabellen fehlen (404)
reset({db: {kameras: new Error('HTTP404 {"code":"PGRST205"}')}, fein: true});
w = wurzel('admin', 1440); await ruhe(w);
OUT.fehlt = {text: text(baum), fetch: ZAEHL.fetch.length};

// 5) Lagerleitung am PC: Live ja, Aufzeichnung/Verwaltung nein
reset({db: {kameras: KAMS}, fein: true});
w = wurzel('lagerleitung', 1440); await ruhe(w);
OUT.lager = {knoepfe: alle(baum, function (n) { return n.tag === 'button'; }).map(text)};
reset({db: {kameras: KAMS}, fein: true});
w = wurzel('buero', 1440); await ruhe(w);
OUT.buero = {knoepfe: alle(baum, function (n) { return n.tag === 'button'; }).map(text)};

// 6) Server sagt 403 / 200
reset({db: {kameras: KAMS}, fein: true, fetch: {status: 403, json: {error: 'kein_zugriff'}}});
w = wurzel('projektleiter', 1440); await ruhe(w);
OUT.verboten = text(baum);
reset({db: {kameras: KAMS}, fein: true, fetch: {status: 200, json: {liveUrl: 'http://unsicher.example/x.m3u8', exp: 1}}});
w = wurzel('projektleiter', 1440); await ruhe(w);
OUT.unsicher = text(baum);
reset({db: {kameras: []}, fein: true});
w = wurzel('projektleiter', 1440); await ruhe(w);
OUT.leer_pl = text(baum);

// 7) reine Helfer
const H = {};
// Phase-1-Semantik OHNE die Admin-Freigabe (KAMERAS_ADMIN, seit v1060) - die Admin-Faelle stehen in
// tests/test_kameras_einrichtung_v1060.py. Hier bleibt belegt: PL/Buero/Lager/Monteur bleiben ohne Schalter aus.
KAMERAS_ADMIN = false;
KAMERAS_PROD = false;/* v1087: Produktionsstand ist true - hier bewusst die Phase-1-Semantik ohne Produktionsweg */
H.schalter = [
  _kamSchalter({role: 'admin'}, {kameras_testumgebung: true}, true),
  _kamSchalter({role: 'admin'}, {kameras_testumgebung: 'true'}, true),
  _kamSchalter({role: 'admin'}, {kameras_testumgebung: '"true"'}, true),
  _kamSchalter({role: 'admin'}, {kameras_testumgebung: false}, true),
  _kamSchalter({role: 'admin'}, {kameras_testumgebung: true}, false),
  _kamSchalter({role: 'admin'}, {}, true),
  _kamSchalter({role: 'projektleiter'}, {kameras_testumgebung: true}, true),
  _kamSchalter({role: 'monteur'}, {kameras_testumgebung: true, kameras_aktiv: true}, true),
  _kamSchalter({role: 'admin'}, {kameras_aktiv: true}, false),
  _kamSchalter(null, {kameras_testumgebung: true}, true)];
H.abruf = [_kamSchalterAbruf({role: 'admin'}, true), _kamSchalterAbruf({role: 'admin'}, false),
           _kamSchalterAbruf({role: 'projektleiter'}, true), _kamSchalterAbruf({role: 'monteur'}, true)];
KAMERAS_PROD = true;
H.prod = [_kamSchalter({role: 'projektleiter'}, {kameras_aktiv: true}, false), _kamSchalter({role: 'lagerleitung'}, {kameras_aktiv: 'true'}, false),
          _kamSchalter({role: 'monteur'}, {kameras_aktiv: true}, false), _kamSchalter({role: 'buero'}, {}, false),
          _kamSchalterAbruf({role: 'buero'}, false), _kamSchalterAbruf({role: 'monteur'}, true)];
KAMERAS_PROD = true;/* v1087: Produktionsstand */
KAMERAS_ADMIN = true;
H.url = [_kamUrlSchalter({role: 'monteur'}, '?kameras_test=1'), LS.epk_kameras_test || null,
         _kamUrlSchalter({role: 'admin'}, '?a=b&kameras_test=1'), LS.epk_kameras_test || null, _kamLokalTest(),
         _kamUrlSchalter({role: 'admin'}, '?kameras_test=0'), LS.epk_kameras_test || null,
         _kamUrlSchalter({role: 'admin'}, '?kameras_test=10'), _kamUrlSchalter({role: 'admin'}, '?xkameras_test=1')];
H.raster = [_kamRaster('einzel', 5, false), _kamRaster('2x2', 5, false), _kamRaster('3x3', 12, false), _kamRaster('3x3', 12, true),
            _kamRaster('alle', 7, false), _kamRaster('alle', 16, false), _kamRaster('alle', 3, true)];
H.refresh = [_kamRefreshIn(1000 + 90, 1000 * 1000), _kamRefreshIn(1000, 1000 * 1000), _kamRefreshIn(NaN, 0), _kamRefreshIn(1e9, 0)];
H.antwort = [_kamStreamAntwort(200, {liveUrl: 'https://p/live/a/index.m3u8?token=x', webrtcUrl: 'https://p/live/a/whep?token=x', exp: 5}, 'live'),
             _kamStreamAntwort(200, {liveUrl: 'http://p/x'}, 'live'), _kamStreamAntwort(200, {liveUrl: 'https://p/x', webrtcUrl: 'javascript:1'}, 'live'),
             _kamStreamAntwort(503, {error: 'nicht_konfiguriert'}, 'live'), _kamStreamAntwort(404, null, 'live'),
             _kamStreamAntwort(403, {error: 'kein_zugriff'}, 'live'), _kamStreamAntwort(401, null, 'live'), _kamStreamAntwort(500, null, 'live'),
             _kamStreamAntwort(200, {aufzeichnungUrl: 'https://p/aufzeichnung/a?token=x', exp: 9}, 'aufzeichnung')];
const R0 = {kamera_id: 'c', rolle: 'buero', user_id: null, wochentage: [1, 2], von: null, bis: null, erlaubt: true};
function mit(o) { return _kamRegelPruefen(Object.assign({}, R0, o)); }
H.regel = {ok: mit({}), beides: mit({user_id: 'u2'}), keins: mit({rolle: null}), monteur: mit({rolle: 'monteur'}), tageLeer: mit({wochentage: []}),
  tag8: mit({wochentage: [8]}), doppelt: mit({wochentage: [1, 1]}), nurVon: mit({von: '07:00'}), umgekehrt: mit({von: '17:00', bis: '07:00'}),
  gleich: mit({von: '07:00', bis: '07:00'}), fenster: mit({von: '07:00', bis: '17:00'}), person: mit({rolle: null, user_id: 'u2', erlaubt: false}),
  lang: mit({bemerkung: 'x'.repeat(201)})};
H.rang = [_kamRegelRang({user_id: 'u', erlaubt: false}), _kamRegelRang({user_id: 'u', erlaubt: true}), _kamRegelRang({rolle: 'admin', erlaubt: false}), _kamRegelRang({rolle: 'admin', erlaubt: true})];
H.tage = [_kamTageText([1, 2, 3, 4, 5, 6, 7]), _kamTageText([5, 4, 3, 2, 1]), _kamTageText([6, 7]), _kamTageText([1, 3])];
H.tagesliste = [_kamTagesListe(3, Date.UTC(2026, 10, 23, 12)).length, _kamTagesListe(99, 0).length, _kamTagesListe(0, 0).length];
H.bereich = [_kamBereichIso(Date.UTC(2026, 10, 23, 7), Date.UTC(2026, 10, 23, 9)),
             _kamBereichIso(Date.UTC(2026, 10, 23, 8, 30), Date.UTC(2026, 10, 23, 9, 0, 30, 500)),
             _kamBereichIso(Date.UTC(2026, 10, 23, 9), Date.UTC(2026, 10, 23, 9)),
             _kamBereichIso(NaN, 0)];
H.pc = [_kamIstPC(1440, true), _kamIstPC(1440, false), _kamIstPC(1199, true), _kamIstPC(1200, true)];
H.modus = [_kamPlayerModus(true, false, {webrtcUrl: 'https://a', liveUrl: 'https://b'}), _kamPlayerModus(false, true, {webrtcUrl: 'https://a', liveUrl: 'https://b'}),
           _kamPlayerModus(false, false, {webrtcUrl: 'https://a', liveUrl: 'https://b'})];
OUT.H = H;
"""


@pytest.fixture(scope="module")
def UIR(node_exe):
    return _render_lauf(node_exe, _block(), SZENEN)


def test_admin_pc_live_raster_mit_stub_kacheln(UIR):
    a = UIR["admin_pc"]
    t = a["text"]
    assert "Testbetrieb" not in t, "v1087: Testbetrieb-Chip entfaellt mit KAMERAS_PROD=true"
    for teil in ("Kameras", "Nur Admin", "Live", "Aufzeichnungen", "Verwaltung", "Einzel", "2×2", "3×3", "Alle",
                 "Kein Video-Backend verbunden", "Kamera 1", "Kamera 3"):
        assert teil in t, teil
    assert "Kamera 2" not in t, "inaktive Kamera darf nicht im Live-Raster stehen"
    assert a["kacheln"] == 2
    assert "repeat(2,minmax(0,1fr))" in a["raster"]
    assert 1 <= len(a["fetch"]) <= 2
    for f in a["fetch"]:
        assert f["url"] == "https://sb.example.test/functions/v1/kamera-stream"
        assert f["body"]["scope"] == "live" and f["body"]["geraet"] == "pc"
    assert "repeat(3,minmax(0,1fr))" in UIR["admin_3x3"]
    assert UIR["admin_einzeln"]["kacheln"] == 1


def test_verwaltung_kamera_anlegen_nur_mit_name_und_ohne_streamdaten(UIR):
    assert "Neue Kamera" in UIR["verw"] and "Zugriff je Kamera" in UIR["verw"]
    assert UIR["verw_leer"]["upsert"] == 0 and "Name fehlt" in UIR["verw_leer"]["text"]
    neu = UIR["verw_neu"]
    assert len(neu) == 1 and neu[0]["tab"] == "kameras"
    row = neu[0]["row"]
    assert row["name"] == "Hof Nord" and row["aufbewahrung_tage"] == 3 and row["aktiv"] is True
    assert set(row) <= {"id", "name", "standort", "hersteller", "modell", "aufbewahrung_tage", "aktiv"}


def test_zugriffseditor_zeigt_vorrang_und_sperrt_einzelnen_pl(UIR):
    e = UIR["editor"]
    for teil in ("Zugriff je Kamera: Kamera 1", "1 · Person gesperrt", "4 · Rolle frei", "Paul PL", "Projektleitung",
                 "Mo–Fr · 07:00–17:00", "täglich · ganzer Tag", "Monteure und alle anderen Rollen sehen nie eine Kamera"):
        assert teil in e, teil
    assert e.index("1 · Person gesperrt") < e.index("4 · Rolle frei"), "Liste nach Vorrang sortiert"
    p = UIR["personen"]
    assert any("Paul PL" in x for x in p) and any("Lea Lager" in x for x in p)
    assert not any("Max Monteur" in x for x in p), "Monteur darf nicht als Person waehlbar sein"
    assert UIR["ohne_person"]["post"] == 0 and "Genau eines" in UIR["ohne_person"]["text"]
    r = UIR["regel_neu"]
    assert len(r) == 1 and r[0]["tab"] == "kamera_zugriff"
    assert r[0]["row"] == {"kamera_id": "cam1", "rolle": None, "user_id": "u2", "wochentage": [1, 2, 3, 4, 5, 6, 7],
                           "von": None, "bis": None, "erlaubt": False, "bemerkung": None}


def test_aufzeichnung_fragt_den_server_mit_scope_und_pc(UIR):
    r = UIR["rec"]
    assert "Aufzeichnung laden" in r["text"] and "Kein Video-Backend verbunden" in r["text"]
    letzte = r["fetch"][-1]["body"]
    assert letzte["scope"] == "aufzeichnung" and letzte["geraet"] == "pc"


def test_aufzeichnung_schickt_den_zeitraum_an_den_server(UIR):
    """Befund 19.11.: die App schickt von/bis (ISO, UTC) - der Server prueft und signiert genau diesen Zeitraum."""
    assert UIR["rec_tage"] >= 2
    b = UIR["rec"]["fetch"][-1]["body"]
    assert set(b) == {"kamera_id", "scope", "geraet", "von", "bis"}
    for k in ("von", "bis"):
        assert re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:00\.000Z$", b[k]), b[k]
    import datetime
    v = datetime.datetime.fromisoformat(b["von"].replace("Z", "+00:00"))
    w = datetime.datetime.fromisoformat(b["bis"].replace("Z", "+00:00"))
    assert (w - v).total_seconds() == 3600
    assert "Kein Zugriff auf Aufnahmen aus diesem Zeitraum" in UIR["rec_403"]
    z = UIR["rec_zukunft"]
    if not z["spaet"]:
        assert z["neu"] == 0 and "Dieser Zeitpunkt liegt in der Zukunft" in z["text"]


def test_aufzeichnung_haengt_nichts_an_die_serveradresse():
    b = _block()
    i = b.index("function KameraAufzeichnung(")
    t = b[i:b.index("\nfunction ", i + 10)]
    assert "var url=a.aufzeichnungUrl;" in t
    assert "'&von='" not in t and "'&bis='" not in t, "von/bis nur aus der signierten Serveradresse"


@pytest.mark.parametrize("k", ["monteur", "helfer"])
def test_monteur_und_helfer_sehen_nichts_und_rufen_nichts_ab(UIR, k):
    assert UIR[k]["baum"] is None
    assert UIR[k]["get"] == 0 and UIR[k]["fetch"] == 0


def test_handy_und_tablet_nur_live(UIR):
    p = UIR["pl_handy"]
    assert "Am Handy und Tablet nur Live-Bild" in p["text"]
    for k in ("Aufzeichnungen", "Verwaltung", "Live"):
        assert k not in p["knoepfe"], k
    assert all(f["body"]["geraet"] == "mobil" for f in p["fetch"])
    assert all("repeat(1," in r or "repeat(2," in r for r in p["raster"])
    t = UIR["tablet"]
    assert "Verwaltung" not in t["knoepfe"] and "Aufzeichnungen" not in t["knoepfe"]
    assert set(t["fetch"]) <= {"mobil"}


def test_fehlende_tabellen_hinweis_ohne_streamabruf(UIR):
    assert "Datenmodell noch nicht angelegt" in UIR["fehlt"]["text"]
    assert UIR["fehlt"]["fetch"] == 0


def test_aufzeichnung_und_verwaltung_nur_fuer_ihre_rollen(UIR):
    assert "Aufzeichnungen" not in UIR["lager"]["knoepfe"] and "Verwaltung" not in UIR["lager"]["knoepfe"]
    assert "Aufzeichnungen" in UIR["buero"]["knoepfe"] and "Verwaltung" not in UIR["buero"]["knoepfe"]


def test_serverantworten_in_der_kachel(UIR):
    assert "Kein Zugriff zu dieser Zeit" in UIR["verboten"]
    assert "Video nicht verfügbar" in UIR["unsicher"], "http-Adresse darf nie geladen werden"
    assert "Für dich ist zu dieser Zeit keine Kamera freigegeben" in UIR["leer_pl"]


def test_schalter_ist_in_produktion_aus(UIR):
    H = UIR["H"]
    assert H["schalter"] == [True, True, True, False, False, False, False, False, False, False]
    assert H["abruf"] == [True, False, False, False]
    assert H["prod"] == [True, True, False, False, True, False]
    assert H["url"] == ["", None, "1", "1", True, "0", None, "", ""]


def test_reine_helfer(UIR):
    H = UIR["H"]
    assert [(r["cols"], r["proSeite"]) for r in H["raster"]] == [(1, 1), (2, 4), (3, 9), (2, 9), (3, 7), (4, 16), (2, 3)]
    assert H["refresh"] == [70000, 5000, 30000, 120000]
    a = H["antwort"]
    assert a[0]["ok"] is True and a[0]["webrtcUrl"].startswith("https://") and a[0]["exp"] == 5
    assert a[1] == {"ok": False, "grund": "fehler"}
    assert a[2]["ok"] is True and a[2]["webrtcUrl"] == ""
    assert [x["grund"] for x in a[3:8]] == ["kein_backend", "kein_backend", "kein_zugriff", "kein_zugriff", "fehler"]
    assert a[8]["ok"] is True and a[8]["aufzeichnungUrl"].startswith("https://") and a[8]["liveUrl"] == ""
    r = H["regel"]
    assert r["ok"] == "" and r["fenster"] == "" and r["person"] == ""
    for k in ("beides", "keins", "monteur", "tageLeer", "tag8", "doppelt", "nurVon", "umgekehrt", "gleich", "lang"):
        assert r[k], k
    assert H["rang"] == [1, 2, 3, 4]
    assert H["tage"] == ["täglich", "Mo–Fr", "Sa–So", "Mo, Mi"]
    assert H["tagesliste"] == [3, 30, 3]
    assert H["pc"] == [True, False, False, True]
    assert H["bereich"][0] == {"von": "2026-11-23T07:00:00.000Z", "bis": "2026-11-23T08:00:00.000Z"}
    assert H["bereich"][1] == {"von": "2026-11-23T08:30:00.000Z", "bis": "2026-11-23T09:00:30.000Z"}, "nie ueber jetzt hinaus"
    assert H["bereich"][2] is None and H["bereich"][3] is None
    assert H["modus"] == ["webrtc", "hls", "keiner"]


def test_umkehrprobe_ohne_rollenpruefung_wuerde_monteur_abrufen(node_exe):
    b = _block()
    alt = "  if(!rolle)return null;\r\n" if "  if(!rolle)return null;\r\n" in b else "  if(!rolle)return null;\n"
    assert b.count(alt) == 1
    kaputt = b.replace(alt, "", 1).replace("if(!rolle)return function(){alive=false;};", "", 1)
    R2 = _render_lauf(node_exe, kaputt, SZENEN)
    assert R2["monteur"]["get"] > 0, "Umkehrprobe: Riegel 'Monteur ruft nichts ab' waere blind"


# ══════════════════════════════════════════════════════════════════════════════
# TEIL C: Verdrahtung in der App (Reiter, Filter, Ansicht, Schalter)
# ══════════════════════════════════════════════════════════════════════════════
def test_reiter_existiert_nur_mit_schalter_und_kamerarolle():
    s = _index()
    assert s.count('...(_kamFlag?[{l:"Kameras",ik:"videokamera",c:"#009640",perm:"kameras",g:3}]:[]),') == 1
    assert s.count('if(t.perm==="kameras")return _kamFlag&&!!_kamRolle(curUser);') == 1
    assert s.count('==="kameras" && _kamFlag && !!_kamRolle(curUser) && React.createElement(_ViewBoundary,{name:"kameras"},React.createElement(KameraView,') == 1
    assert s.count("perm:\"kameras\"") == 1


def test_schalter_hook_fragt_erst_ob_abgerufen_werden_darf():
    s = _index()
    i = s.index("const [_kamFlag,_setKamFlag]=_react.useState.call(void 0, false);")
    teil = s[i:s.index("const _bauproNowYr=", i)]
    assert teil.index("_kamSchalterAbruf(curUser,_lokal)") < teil.index("_kamLadeSchalter()")
    assert "_setKamFlag(false);" in teil
    # Hook steht vor den Early-Returns (stabile Hook-Reihenfolge)
    assert i < s.index("if(appLoading) return (")


def test_produktionsschalter_steht_auf_an():
    # v1087 (Auftrag Inhaber 21.11.2026 "Kameras live in die App"): Produktionsweg an. Die Team-Freigabe haengt
    # weiter an system_config kameras_aktiv (nur Admin schreibt) - Rollenmatrix in test_kameras_prod_v1087.py.
    b = _block()
    assert b.count("var KAMERAS_PROD=true;") == 1
    assert "var KAMERAS_PROD=false;" not in b


def _js_code(b):
    """Block ohne Kommentare - die Begruendungen nennen SyncQueue/OFFA absichtlich beim Namen."""
    b = re.sub(r"/\*.*?\*/", "", b, flags=re.S)
    return "\n".join(z for z in b.replace("\r\n", "\n").split("\n") if not z.lstrip().startswith("//"))


def test_block_ist_isoliert_und_haelt_die_hausregeln():
    b = _js_code(_block())
    roh = _block()
    for verboten in ("SQ.push", "ROUTE_MAP", "offa", "OFFA", "juprowa", "Juprowa", "86400000", "rtsp:", "?.",
                     "noch nicht eingerichtet"):
        assert verboten not in b, verboten
    assert "`" not in roh and "86400000" not in roh, "auch in Kommentaren keine Backticks"
    assert not re.search(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", b), "IP-Adresse im Block"
    assert "KAMERA_FN='/functions/v1/kamera-stream'" in b
    assert os.path.isdir(FN_DIR)
    assert "fontSize:" in b and not re.search(r"fontSize:\s*\d", b), "Schrift nur ueber UI-Token"


def test_ikone_videokamera_steht_in_ikon():
    s = _index()
    i = s.index("const IKON={")
    j = s.index("};function _ik(", i)
    assert 'videokamera:["' in s[i:j]


def test_kamerarollen_sind_ueberall_dieselben():
    erwartet = ["admin", "projektleiter", "buero", "lagerleitung"]
    assert "var KAMERA_ROLLEN=['admin','projektleiter','buero','lagerleitung'];" in _block()
    assert 'ERLAUBTE_ROLLEN: readonly string[] = ["admin", "projektleiter", "buero", "lagerleitung"];' in _lies(LOGIC)
    sql = _lies(SQL)
    assert sql.count("('admin','projektleiter','buero','lagerleitung')") >= 2
    assert len(erwartet) == 4


# ══════════════════════════════════════════════════════════════════════════════
# TEIL D: SQL-Entwurf und Ruecknahme (statisch - es laeuft KEIN SQL gegen die DB)
# ══════════════════════════════════════════════════════════════════════════════
def _ohne_kommentare(sql):
    return "\n".join(z.split("--", 1)[0] for z in sql.replace("\r\n", "\n").split("\n"))


def test_sql_kopf_und_kein_cascade():
    for p in (SQL, SQL_RUECK):
        s = _lies(p)
        assert s.startswith("-- IDEMPOTENT"), p
        assert "cascade" not in _ohne_kommentare(s).lower(), p
        assert not re.search(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", s), p
        assert not re.search(r"(password|passwort|kennwort)\s*[:=]", s, re.I), p


def test_sql_rollen_explizit_nicht_is_staff():
    code = _ohne_kommentare(_lies(SQL))
    assert "is_staff" not in code and "is_hr" not in code
    assert "if v_role not in ('admin','projektleiter','buero','lagerleitung') then" in code
    assert "rolle in ('admin','projektleiter','buero','lagerleitung')" in code


def test_sql_vorrang_reihenfolge():
    code = _ohne_kommentare(_lies(SQL))
    f = code[code.index("create or replace function public.kamera_pruefen"):code.index("create or replace function public.kamera_darf_sehen")]
    stellen = [f.index("z.user_id = v_uid and not z.erlaubt"), f.index("z.user_id = v_uid and z.erlaubt"),
               f.index("z.rolle = v_role and not z.erlaubt"), f.index("z.rolle = v_role and z.erlaubt")]
    assert stellen == sorted(stellen)
    assert f.index("v_role not in") < stellen[0], "Rollensperre vor allen Regeln"
    assert "at time zone 'Europe/Vienna'" in f and "isodow" in f
    assert f.rindex("return false;") > stellen[3], "Standard-Nein nach allen Regeln"


def test_sql_funktionen_definer_mit_festem_suchpfad_und_rechten():
    code = _ohne_kommentare(_lies(SQL))
    for fn in ("kamera_ist_verwalter()", "kamera_pruefen(p_auth uuid", "kamera_darf_sehen(p_kamera text, p_zeitpunkt timestamptz default now())"):
        i = code.index("create or replace function public." + fn)
        kopf = code[i:code.index("as $$", i)]
        assert "security definer" in kopf and "set search_path = public, pg_temp" in kopf, fn
    assert "revoke all on function public.kamera_pruefen(uuid, text, timestamptz) from public, anon, authenticated;" in code
    assert "revoke all on function public.kamera_darf_sehen(text, timestamptz) from public, anon;" in code


def test_sql_bereichspruefung_fuer_aufzeichnungen():
    """Befund 19.11.: kamera_darf_sehen_bereich - Regel fuer JEDEN Augenblick in [von, bis), Aufbewahrung, nur authenticated."""
    code = _ohne_kommentare(_lies(SQL))
    k = "create or replace function public.kamera_darf_sehen_bereich(p_kamera text, p_von timestamptz, p_bis timestamptz)"
    assert code.count(k) == 1
    i = code.index(k)
    kopf = code[i:code.index("as $$", i)]
    assert "security definer" in kopf and "set search_path = public, pg_temp" in kopf
    f = code[i:code.index("end $$;", i)]
    assert "v_auth uuid := auth.uid();" in f, "nur der Aufrufer selbst, kein p_auth-Parameter"
    assert "p_von >= p_bis or p_bis > now() or p_bis - p_von > interval '2 hours'" in f
    assert "k.aufbewahrung_tage" in f and "p_von < now() - make_interval(days => v_tage)" in f
    assert "public.kamera_pruefen(v_auth, p_kamera, p_von) is not true" in f
    assert "while v_t < p_bis loop" in f and "public.kamera_pruefen(v_auth, p_kamera, v_t) is not true" in f
    assert "v_t := v_t + interval '1 minute';" in f
    assert "revoke all on function public.kamera_darf_sehen_bereich(text, timestamptz, timestamptz) from public, anon;" in code
    assert "grant execute on function public.kamera_darf_sehen_bereich(text, timestamptz, timestamptz) to authenticated;" in code
    # Exaktheit der Minutenpruefung setzt Regelgrenzen auf ganzen Minuten voraus
    assert "constraint kamera_zugriff_minuten_chk check ((von is null or extract(second from von) = 0) and (bis is null or extract(second from bis) = 0))" in code
    s = _lies(SQL)
    assert "kamera_darf_sehen_bereich('__probe_kam__'" in s and "kamera_zugriff_minuten_chk" in s


def test_sql_backend_nur_service_role():
    code = _ohne_kommentare(_lies(SQL))
    assert "on public.kamera_backend for" not in code, "kamera_backend darf KEINE Policy haben"
    assert "revoke all on public.kamera_backend from authenticated;" in code
    assert "alter table public.kamera_backend   enable row level security;" in code
    k = code[code.index("create table if not exists public.kameras ("):code.index(");", code.index("create table if not exists public.kameras ("))]
    for verboten in ("stream", "url", "passw", "rtsp", "ip"):
        assert not re.search(r"^\s*\w*" + verboten + r"\w*\s", k, re.I | re.M), verboten


def test_sql_rls_lesen_und_schreiben():
    code = _ohne_kommentare(_lies(SQL))
    assert "using (public.kamera_ist_verwalter() or public.kamera_darf_sehen(id));" in code
    for pol in ("kameras_insert", "kameras_update", "kameras_delete", "kamera_zugriff_admin"):
        i = code.index("create policy " + pol)
        assert "kamera_ist_verwalter()" in code[i:code.index(";", i)], pol
    assert "aufbewahrung_tage > 0 and aufbewahrung_tage <= 30" in code
    assert "num_nonnulls(rolle, user_id) = 1" in code
    assert "on delete restrict" in code


def test_sql_probeblock_mit_rollenproben():
    s = _lies(SQL)
    assert "-- begin;" in s and "-- rollback;" in s
    for teil in ("<AUTH_MONTEUR>", "<AUTH_PL>", "<AUTH_ADMIN>", "set local role anon", "set local role authenticated",
                 "kamera_darf_sehen('__probe_kam__')", "erwartet ERROR 42501", "PL ausgesperrt", "savepoint"):
        assert teil in s, teil
    assert s.index("-- begin;") < s.index("-- rollback;")


def test_ruecknahme_raeumt_alles_in_der_richtigen_reihenfolge():
    code = _ohne_kommentare(_lies(SQL_RUECK))
    reihen = [code.index("drop table if exists public." + t + ";") for t in
              ("kamera_abruf_log", "kamera_zugriff", "kamera_backend", "kameras")]
    assert reihen == sorted(reihen)
    assert code.index("drop function if exists public.kamera_darf_sehen_bereich(") < code.index("drop function if exists public.kamera_pruefen(")
    for fn in ("kamera_darf_sehen_bereich(text, timestamptz, timestamptz)", "kamera_darf_sehen(text, timestamptz)",
               "kamera_pruefen(uuid, text, timestamptz)", "kamera_ist_verwalter()",
               "kamera_fenster_trifft(integer[], time, time, integer, time)", "kamera_touch()"):
        assert "drop function if exists public." + fn + ";" in code, fn
    assert code.index("drop policy if exists kameras_select") < reihen[0]


# ══════════════════════════════════════════════════════════════════════════════
# TEIL E: Doku
# ══════════════════════════════════════════════════════════════════════════════
def test_doku_beschreibt_modell_vorrang_vertrag_schalter_und_pilot():
    d = _lies(DOKU)
    for teil in ("Datenmodell", "Vorrang", "Token", "KAMERAS_PROD", "kameras_testumgebung", "?kameras_test=1",
                 "Infrastruktur", "Testplan", "Monteur", "keine Stream-Adresse", "KAMERAS_v1_ENTWURF.sql",
                 "kamera-stream", "Offene Fragen"):
        assert teil in d, teil
