# -*- coding: utf-8 -*-
"""Kameras: Bereich fuer den Admin in Produktion + ehrliche Einrichtungsansicht (19.11.2026).

Auftrag Inhaber: "Kamera ist noch nicht in der App, alles bauen was fehlt". Der Bereich erscheint jetzt fuer den
ADMIN (KAMERAS_ADMIN=true), alle anderen Rollen bleiben unveraendert aus. Solange eine Voraussetzung fehlt, zeigt
der Bereich die Ansicht "Einrichtung" mit vier live geprueften Zeilen - kein Video, kein Platzhalterbild:
  (a) Kamera-Tabellen   (b) Edge Function kamera-stream   (c) Video-Host im Buero   (d) Zahl der Kameras
TEIL A: App-Ansicht (Block //@KAMERAS-START..END gegen die Attrappen aus test_kameras_phase1_v1055).
TEIL B: Edge Function - Einrichtungsabfrage nur fuer den Admin, NACH der Rollensperre, ohne Kamera/Backend/Token.
TEIL C: Proxy-Vorlagen kennen /gesund (nur "ok"), und nirgends steht eine echte Adresse.
"""
import io
import json
import os
import re
import subprocess
import tempfile

import pytest

from conftest import EPK_TEST_TIMEOUT
from test_kameras_phase1_v1055 import RENDER_PRELUDE, _block, _render_lauf, _js_code, _index

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGIC = os.path.join(WURZEL, "supabase", "functions", "kamera-stream", "logic.ts")
VORLAGEN = os.path.join(WURZEL, "tools", "kamera-proxy-auth", "vorlagen")
IP_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")


def _lies(p):
    return io.open(p, encoding="utf-8", newline="").read()


# ══════════════════════════════════════════════════════════════════════════════
# TEIL A: App
# ══════════════════════════════════════════════════════════════════════════════
SZENEN = r"""
// Pin angepasst 20.11.2026 (feature/kamera-gateway): der Aufzeichnungs-Bereich ist in der App aus (Owner: Aufnahmen
// ueber die Surveillance Station). Diese Szenarien pruefen die vorhandene Aufzeichnungs-Oberflaeche weiter -> Schalter an.
KAMERA_REC_UI = true;
function reset(s) { SZENE = s; store.clear(); _kamBackend.fehlt = false; ['get','post','upsert','del','fetch','pruef'].forEach(function (k) { ZAEHL[k].length = 0; }); }
const KAMS = [{id: 'cam1', name: 'Kamera 1', standort: 'Hof', aktiv: true, aufbewahrung_tage: 3},
              {id: 'cam2', name: 'Kamera 2', standort: 'Lager', aktiv: false, aufbewahrung_tage: 3}];
const FEHLT = new Error('HTTP404 {"code":"PGRST205"}');
const FN_OK = {status: 200, json: {einrichtung: true, secret: true, basis: 'https://video.example.test/'}};
function wurzel(rolle, ww) { return React.createElement(KameraView, {curUser: {id: 'x', role: rolle}, ww: ww || 1440, users: []}); }
function knoepfe() { return alle(baum, function (n) { return n.tag === 'button'; }).map(text); }
function bild() { return {text: text(baum), knoepfe: knoepfe(), videos: alle(baum, function (n) { return n.tag === 'video' || n.tag === 'img'; }).length,
  stream: ZAEHL.fetch.length, pruef: ZAEHL.pruef.slice(), get: ZAEHL.get.slice(),
  zeilen: alle(baum, function (n) { return n.tag === 'li'; }).length}; }
let w;

// 1) Nichts da: Tabellen fehlen, Funktion nicht deployt (404)
reset({db: {kameras: FEHLT}, fein: true, einrichtung: {status: 404, json: {code: 'NOT_FOUND'}}});
w = wurzel('admin'); await ruhe(w); OUT.nichts = bild();
// 1b) Funktion antwortet gar nicht (fetch wirft, z. B. fehlende CORS-Antwort beim 404)
reset({db: {kameras: FEHLT}, fein: true, einrichtung: {wirft: true}});
w = wurzel('admin'); await ruhe(w); OUT.wirft = bild();
// 2) Tabellen da, leer; Funktion aktiv ohne Secret und ohne Adresse
reset({db: {kameras: []}, fein: true, einrichtung: {status: 200, json: {einrichtung: true, secret: false, basis: ''}}});
w = wurzel('admin'); await ruhe(w); OUT.leer = bild();
// 3) alte Fassung der Funktion (400)
reset({db: {kameras: KAMS}, fein: true, einrichtung: {status: 400, json: {error: 'ungueltig'}}});
w = wurzel('admin'); await ruhe(w); OUT.alt = bild();
// 4) alles da, aber Video-Host nicht erreichbar
reset({db: {kameras: KAMS}, fein: true, einrichtung: FN_OK, gesund: {wirft: true}});
w = wurzel('admin'); await ruhe(w); OUT.buero_weg = bild();
// 4b) Video-Host antwortet, aber nicht auf /gesund
reset({db: {kameras: KAMS}, fein: true, einrichtung: FN_OK, gesund: {status: 404}});
w = wurzel('admin'); await ruhe(w); OUT.buero_404 = bild();
// 4c) Adresse ohne https wird nie angefragt
reset({db: {kameras: KAMS}, fein: true, einrichtung: {status: 200, json: {einrichtung: true, secret: true, basis: 'http://video.example.test'}}});
w = wurzel('admin'); await ruhe(w); OUT.http = bild();
// 4d) Kameras angelegt, keine aktiv
reset({db: {kameras: [KAMS[1]]}, fein: true, einrichtung: FN_OK});
w = wurzel('admin'); await ruhe(w); OUT.inaktiv = bild();
// 5) alles da -> Live-Kacheln; Einrichtung bleibt als Reiter
reset({db: {kameras: KAMS}, fein: true, einrichtung: FN_OK});
w = wurzel('admin'); await ruhe(w); OUT.fertig = bild();
await klick(w, 'Einrichtung'); OUT.fertig_einr = bild();
const vorher = ZAEHL.pruef.length;
await klick(w, 'Erneut prüfen'); OUT.erneut = {pruef: ZAEHL.pruef.length - vorher, liste: ZAEHL.pruef.slice(vorher), text: text(baum)};
await klick(w, 'Live'); OUT.zurueck = bild();
// 6) Admin am Handy, nichts da: Einrichtung auch am Handy, ohne Verwaltung
reset({db: {kameras: FEHLT}, fein: false, einrichtung: {status: 404, json: {}}});
w = wurzel('admin', 390); await ruhe(w); OUT.handy = bild();
// 7) Tabellen da (leer), Verwaltung erreichbar trotz fehlender Voraussetzungen
reset({db: {kameras: []}, fein: true, einrichtung: {status: 404, json: {}}});
w = wurzel('admin'); await ruhe(w);
await klick(w, 'Verwaltung'); OUT.verw = bild();
// 8) andere Rollen: keine Einrichtungspruefung
reset({db: {kameras: KAMS}, fein: true});
w = wurzel('projektleiter'); await ruhe(w); OUT.pl = bild();
reset({db: {kameras: KAMS}, fein: true});
w = wurzel('monteur'); await ruhe(w); OUT.monteur = {baum: baum, get: ZAEHL.get.length, fetch: ZAEHL.fetch.length, pruef: ZAEHL.pruef.length};
reset({db: {kameras: KAMS}, fein: true});
w = wurzel('helfer', 390); await ruhe(w); OUT.helfer = {baum: baum, get: ZAEHL.get.length, fetch: ZAEHL.fetch.length, pruef: ZAEHL.pruef.length};

// 9) Schalter mit Admin-Freigabe
// v1087: KAMERAS_PROD steht in Produktion auf true (Auftrag Inhaber 21.11.2026). Diese Faelle belegen die
// Admin-Freigabe OHNE Produktionsweg (Notbremse KAMERAS_PROD=false) - der Produktionsweg steht in test_kameras_prod_v1087.py.
KAMERAS_PROD = false;
OUT.S = {
  admin_ohne_alles: _kamSchalter({role: 'admin'}, {}, false),
  admin_gross: _kamSchalter({role: ' Admin '}, {}, false),
  pl: _kamSchalter({role: 'projektleiter'}, {kameras_testumgebung: true}, true),
  buero: _kamSchalter({role: 'buero'}, {}, false),
  lager: _kamSchalter({role: 'lagerleitung'}, {kameras_aktiv: true}, true),
  monteur: _kamSchalter({role: 'monteur'}, {kameras_testumgebung: true, kameras_aktiv: true}, true),
  techniker: _kamSchalter({role: 'techniker'}, {}, true),
  niemand: _kamSchalter(null, {}, true),
  abruf_admin: _kamSchalterAbruf({role: 'admin'}, false),
  abruf_pl: _kamSchalterAbruf({role: 'projektleiter'}, false),
  abruf_monteur: _kamSchalterAbruf({role: 'monteur'}, true)};
KAMERAS_ADMIN = false;
OUT.S.aus_admin = _kamSchalter({role: 'admin'}, {}, false);
OUT.S.aus_abruf = _kamSchalterAbruf({role: 'admin'}, false);
KAMERAS_ADMIN = true;
KAMERAS_PROD = true;
OUT.F = [_kamFnAntwort(404, null), _kamFnAntwort(400, {}), _kamFnAntwort(401, null), _kamFnAntwort(403, null), _kamFnAntwort(500, null),
         _kamFnAntwort(200, {einrichtung: true, secret: true, basis: 'https://v.example.test//'}),
         _kamFnAntwort(200, {einrichtung: true, secret: 'true', basis: 'javascript:alert(1)'}),
         _kamFnAntwort(200, {liveUrl: 'https://x'})];
"""


@pytest.fixture(scope="module")
def U(node_exe):
    return _render_lauf(node_exe, _block(), SZENEN)


def test_nichts_da_zeigt_vier_offene_punkte_ohne_video(U):
    a = U["nichts"]
    # v3.9.1069 (Auftrag Inhaber): Klartext-Statuszeilen statt Datei-/Secret-/Netznamen; EINE Zeile zur Anleitung
    for teil in ("Einrichtung", "Datenbank: noch nicht bereit", "Server-Funktion: noch nicht aktiv",
                 "Kamera-Server im Büro: noch nicht in Betrieb", "Kameras angemeldet: 0",
                 "4 von 4 Voraussetzungen fehlen noch", "bewusst kein Video",
                 "macht die Technik - diese Seite zeigt nur, was davon schon fertig ist"):
        assert teil in a["text"], teil
    assert a["zeilen"] == 4 and a["videos"] == 0 and a["stream"] == 0
    assert a["pruef"] == ["fn"], "ohne aktive Funktion keine Adresse -> kein Abruf beim Video-Host"
    assert "Live" not in a["knoepfe"] and "Aufzeichnungen" not in a["knoepfe"] and "Verwaltung" not in a["knoepfe"]
    assert "Erneut prüfen" in a["knoepfe"] and "Einrichtung" in a["knoepfe"]


# v3.9.1069: in KEINER Admin-Szene stehen Entwickler- oder Infrastrukturbegriffe in der Einrichtung
VERBOTEN_IN_EINRICHTUNG = ("KAMERA_TOKEN_SECRET", "KAMERA_BACKEND_BASE", ".sql", ".env", "Sebastian", "SQL-Editor",
                           "QNAP", "WireGuard", "Wer:", "supabase/", "tools/", "go2rtc", "Frigate", "Caddy", "Secret",
                           "docs/", ".md", "PILOT_HEUTE")  # 1077: auch kein Dateipfad zur Anleitung mehr


def test_einrichtung_ohne_entwicklertext(U):
    szenen = ("nichts", "wirft", "leer", "alt", "buero_weg", "buero_404", "http", "inaktiv", "fertig_einr", "handy")
    for s in szenen:
        for wort in VERBOTEN_IN_EINRICHTUNG:
            assert wort not in U[s]["text"], (s, wort)
        assert U[s]["text"].count("macht die Technik - diese Seite zeigt nur") == 1, s


def test_keine_antwort_der_funktion_gilt_als_nicht_aktiv(U):
    assert "Server-Funktion: noch nicht aktiv" in U["wirft"]["text"] and U["wirft"]["videos"] == 0


def test_tabellen_leer_funktion_ohne_secret_und_ohne_adresse(U):
    t = U["leer"]["text"]
    for teil in ("Datenbank: bereit", "Server-Funktion: aktiv, Schlüssel fehlt noch",
                 "Kamera-Server im Büro: noch nicht in Betrieb", "Noch keine Adresse hinterlegt", "Kameras angemeldet: 0",
                 "3 von 4 Voraussetzungen fehlen noch"):
        assert teil in t, teil
    assert U["leer"]["pruef"] == ["fn"], "ohne Adresse kein Gesundheitsabruf"
    assert "Verwaltung" in U["leer"]["knoepfe"], "Tabellen da -> Kameras anlegen moeglich"


def test_alte_fassung_der_funktion(U):
    assert "Server-Funktion: ältere Fassung" in U["alt"]["text"] and "Kameras angemeldet: 2, davon 1 aktiv" in U["alt"]["text"]


def test_video_host_nicht_erreichbar_oder_ohne_gesund(U):
    b = U["buero_weg"]
    assert "Kamera-Server im Büro: nicht erreichbar" in b["text"] and b["videos"] == 0 and b["stream"] == 0
    assert b["pruef"] == ["fn", "gesund:https://video.example.test/gesund"], "Basis ohne Schraegstrich am Ende + /gesund"
    assert "Kamera-Server im Büro: antwortet unerwartet" in U["buero_404"]["text"]


def test_http_adresse_wird_nie_angefragt(U):
    assert U["http"]["pruef"] == ["fn"] and "Noch keine Adresse hinterlegt" in U["http"]["text"]


def test_keine_aktive_kamera(U):
    assert "Kameras angemeldet: 1, keine aktiv" in U["inaktiv"]["text"] and U["inaktiv"]["videos"] == 0


def test_alles_da_zeigt_live_kacheln_und_einrichtung_als_reiter(U):
    f = U["fertig"]
    assert f["videos"] == 1 and f["stream"] >= 1 and "Kamera 1" in f["text"]
    assert "Datenbank:" not in f["text"]  # v3.9.1069: neuer Zeilenanfang der Einrichtung
    for k in ("Live", "Aufzeichnungen", "Verwaltung", "Einrichtung"):
        assert k in f["knoepfe"], k
    e = U["fertig_einr"]
    assert "Alle Voraussetzungen sind erfüllt." in e["text"] and e["text"].count("erledigt") == 4 and e["videos"] == 0
    assert "Kamera-Server im Büro: erreichbar" in e["text"]
    # Pin angepasst v3.9.1088 (Kamera LNA): der Klick stoesst den Gesundheitsabruf zusaetzlich SOFORT an (Nutzergeste,
    # damit Chrome die Frage "Geraete im lokalen Netzwerk" zeigen kann) -> 3 statt 2, Reihenfolge fest.
    assert U["erneut"]["pruef"] == 3, "Erneut pruefen: Anstoss im Klick, dann Funktion und Video-Host neu"
    assert U["erneut"]["liste"] == ["gesund:https://video.example.test/gesund", "fn", "gesund:https://video.example.test/gesund"]
    assert U["zurueck"]["videos"] == 1


def test_admin_am_handy_sieht_einrichtung_ohne_verwaltung(U):
    h = U["handy"]
    assert "Server-Funktion: noch nicht aktiv" in h["text"] and "Einrichtung" in h["knoepfe"]
    assert "Verwaltung" not in h["knoepfe"] and "Live" not in h["knoepfe"]


def test_verwaltung_trotz_offener_punkte(U):
    assert "Neue Kamera" in U["verw"]["text"] and "Einrichtung" in U["verw"]["knoepfe"]


def test_andere_rollen_pruefen_nichts_und_sehen_keine_einrichtung(U):
    p = U["pl"]
    assert p["pruef"] == [] and "Einrichtung" not in p["knoepfe"] and "Datenbank:" not in p["text"]
    for k in ("monteur", "helfer"):
        m = U[k]
        assert m["baum"] is None and m["get"] == 0 and m["fetch"] == 0 and m["pruef"] == 0, k


def test_schalter_nur_admin(U):
    S = U["S"]
    assert S["admin_ohne_alles"] is True and S["admin_gross"] is True and S["abruf_admin"] is True
    for k in ("pl", "buero", "lager", "monteur", "techniker", "niemand", "abruf_pl", "abruf_monteur"):
        assert S[k] is False, k
    assert S["aus_admin"] is False and S["aus_abruf"] is False, "ohne KAMERAS_ADMIN gilt wieder Phase 1"


def test_antwort_der_funktion_wird_streng_gelesen(U):
    F = U["F"]
    assert [x["stufe"] for x in F] == ["fehlt", "alt", "anmeldung", "anmeldung", "fehler", "ok", "ok", "fehler"]
    assert F[5]["basis"] == "https://v.example.test" and F[5]["secret"] is True
    assert F[6]["basis"] == "" and F[6]["secret"] is False, "nur https, secret nur bei echtem true"


def test_verdrahtung_und_hausregeln():
    s = _index()
    b = _block(s)
    assert b.count("var KAMERAS_ADMIN=true;") == 1 and b.count("var KAMERAS_PROD=true;") == 1  # v1087: Produktionsweg an (Auftrag Inhaber 21.11.2026)
    assert b.count("if(r==='admin'&&KAMERAS_ADMIN===true)return true;") == 2
    # Reiter/Filter/Ansicht unveraendert: Kamerarolle + Schalter, Monteur nie
    assert s.count('if(t.perm==="kameras")return _kamFlag&&!!_kamRolle(curUser);') == 1
    code = _js_code(b)
    assert not IP_RE.search(code)
    assert not re.search(r"https?://[A-Za-z0-9]", code), "keine fest eingetragene Adresse im Kamerablock"
    assert "noch nicht eingerichtet" not in b and "`" not in b and str(24 * 3600 * 1000) not in b
    assert not re.search(r"fontSize:\s*\d", code)
    i = code.index("function KameraEinrichtung(")
    teil = code[i:code.index("function KameraView(", i)]
    assert "<video" not in teil and "'video'" not in teil and "'img'" not in teil, "Einrichtung zeigt nie ein Bild"
    # Pruefung der Funktion laeuft nur fuer den Admin
    v = code[code.index("function KameraView("):]
    assert "if(!isAdmin)return function(){alive=false;};" in v
    assert v.index("if(!isAdmin)return function(){alive=false;};") < v.index("_kamFnPruefen()")


def test_umkehrprobe_ohne_adminsperre_wuerde_pl_pruefen(node_exe):
    b = _block()
    alt = "if(!isAdmin)return function(){alive=false;};"
    assert b.count(alt) == 1
    kaputt = b.replace(alt, "", 1).replace("var einr=isAdmin?_kamEinrichtung(kd,ep.fn,ep.buero):null;",
                                           "var einr=_kamEinrichtung(kd,ep.fn,ep.buero);", 1)
    R2 = _render_lauf(node_exe, kaputt, SZENEN)
    assert R2["pl"]["pruef"] != [], "Umkehrprobe: Riegel 'nur Admin prueft' waere blind"


def test_umkehrprobe_ohne_fertig_riegel_kaemen_kacheln(node_exe):
    b = _block()
    alt = "if(isAdmin&&!fertig&&!(b==='verwaltung'&&kd.status==='ok'))b='einrichtung';"
    assert b.count(alt) == 1
    kaputt = b.replace(alt, "", 1)
    R2 = _render_lauf(node_exe, kaputt, SZENEN)
    assert R2["buero_weg"]["videos"] > 0, "Umkehrprobe: Riegel 'erst alles da, dann Video' waere blind"


# ══════════════════════════════════════════════════════════════════════════════
# TEIL B: Edge Function
# ══════════════════════════════════════════════════════════════════════════════
HARNESS = r"""
import * as L from "./logic.ts";
const SECRET = "s".repeat(40);
const USERS = {admin: {id: "u1", role: "admin", active: 1, locked: false}, pl: {id: "u2", role: "projektleiter", active: 1, locked: 0},
  buero: {id: "u6", role: "buero", active: 1, locked: false}, monteur: {id: "u4", role: "monteur", active: 1, locked: false},
  helfer: {id: "u5", role: "helfer", active: 1, locked: false}, inaktiv: {id: "u8", role: "admin", active: 0, locked: false}};
async function lauf(f) {
  const o = Object.assign({wer: "admin", body: {pruefen: "einrichtung"}, env: {KAMERA_TOKEN_SECRET: SECRET, KAMERA_BACKEND_BASE: "https://video.example.test"},
                           origin: "https://epkolar.github.io"}, f);
  const calls = {darf: 0, backend: 0, log: 0};
  const deps = {
    env: (n) => o.env[n], now: () => Date.UTC(2026, 10, 23, 9), nonce: () => "n",
    authUser: async (jwt) => { const m = /^jwt_([a-z]+)_0123456789abcdef$/.exec(jwt); return m && USERS[m[1]] ? "auth-" + m[1] : null; },
    ladeNutzer: async (uid) => USERS[uid.slice(5)] || null,
    darfSehen: async () => { calls.darf++; return true; },
    ladeBackend: async () => { calls.backend++; return {stream_name: "hof_nord", aufzeichnung_quelle: null, stream_typ: "webrtc"}; },
    protokoll: async () => { calls.log++; },
  };
  const h = {"content-type": "application/json", authorization: "Bearer jwt_" + o.wer + "_0123456789abcdef"};
  if (o.origin) h.origin = o.origin;
  const res = await L.bearbeite(new Request("https://fn.example.test/kamera-stream",
    {method: "POST", headers: h, body: typeof o.body === "string" ? o.body : JSON.stringify(o.body)}), deps);
  return {status: res.status, text: await res.text(), acao: res.headers.get("access-control-allow-origin"), calls};
}
const F = %(faelle)s;
const R = {};
for (const k of Object.keys(F)) R[k] = await lauf(F[k]);
R.ist = ['{"pruefen":"einrichtung"}', '{"pruefen":"einrichtung","kamera_id":"cam1"}', '{"pruefen":"x"}', '["einrichtung"]', 'kein json',
         '{"kamera_id":"cam1"}', '{"pruefen":"einrichtung","x":"' + "y".repeat(3000) + '"}'].map(L.istEinrichtungsAbfrage);
console.log(JSON.stringify(R));
"""

FAELLE = {
    "admin": {},
    "admin_mit_kamera": {"body": {"pruefen": "einrichtung", "kamera_id": "cam1"}},
    "admin_ohne_env": {"env": {}},
    "admin_http_basis": {"env": {"KAMERA_TOKEN_SECRET": "s" * 40, "KAMERA_BACKEND_BASE": "http://video.example.test"}},
    "admin_basis_ungueltig": {"env": {"KAMERA_TOKEN_SECRET": "kurz", "KAMERA_BACKEND_BASE": "https://video example.test"}},
    "pl": {"wer": "pl"},
    "buero": {"wer": "buero"},
    "monteur": {"wer": "monteur"},
    "helfer": {"wer": "helfer"},
    "inaktiv": {"wer": "inaktiv"},
    "niemand": {"wer": "fremd"},
    "stream_weiter": {"body": {"kamera_id": "cam1"}},
    "zu_gross": {"body": {"pruefen": "einrichtung", "x": "y" * 3000}},
}


def _lauf(node_exe, logic_src):
    with tempfile.TemporaryDirectory() as d:
        with io.open(os.path.join(d, "logic.ts"), "w", encoding="utf-8", newline="\n") as f:
            f.write(logic_src)
        with io.open(os.path.join(d, "h.mjs"), "w", encoding="utf-8", newline="\n") as f:
            f.write(HARNESS % {"faelle": json.dumps(FAELLE)})
        r = subprocess.run([node_exe, "--experimental-strip-types", "--no-warnings", "h.mjs"], cwd=d,
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=EPK_TEST_TIMEOUT)
    assert r.returncode == 0, r.stderr[-3000:]
    return json.loads(r.stdout.strip().splitlines()[-1])


@pytest.fixture(scope="module")
def R(node_exe):
    return _lauf(node_exe, _lies(LOGIC))


def test_admin_bekommt_nur_den_einrichtungsstand(R):
    a = R["admin"]
    assert a["status"] == 200 and a["acao"] == "https://epkolar.github.io"
    assert json.loads(a["text"]) == {"einrichtung": True, "secret": True, "basis": "https://video.example.test"}
    assert a["calls"] == {"darf": 0, "backend": 0, "log": 0}, "keine Regel-, Backend- oder Protokollabfrage"
    m = R["admin_mit_kamera"]
    assert json.loads(m["text"])["einrichtung"] is True and "token" not in m["text"] and m["calls"]["backend"] == 0


def test_secret_und_basis_werden_nur_als_stand_gemeldet(R):
    assert json.loads(R["admin_ohne_env"]["text"]) == {"einrichtung": True, "secret": False, "basis": ""}
    assert json.loads(R["admin_http_basis"]["text"])["basis"] == ""
    k = json.loads(R["admin_basis_ungueltig"]["text"])
    assert k == {"einrichtung": True, "secret": False, "basis": ""}, "ungueltige Basis wird nie ausgegeben"
    for f in ("admin", "admin_ohne_env", "admin_basis_ungueltig"):
        assert "s" * 40 not in R[f]["text"] and "kurz" not in R[f]["text"], "Secret selbst nie in der Antwort"


@pytest.mark.parametrize("k", ["pl", "buero", "monteur", "helfer"])
def test_alle_anderen_rollen_403_ohne_jede_abfrage(R, k):
    f = R[k]
    assert f["status"] == 403 and json.loads(f["text"]) == {"error": "kein_zugriff"}, k
    assert f["calls"]["darf"] == 0 and f["calls"]["backend"] == 0
    assert "http" not in f["text"] and "basis" not in f["text"]


def test_inaktiv_und_unbekannt(R):
    assert R["inaktiv"]["status"] == 403 and R["niemand"]["status"] == 401


def test_stream_anfragen_unveraendert(R):
    s = R["stream_weiter"]
    assert s["status"] == 200 and "liveUrl" in s["text"] and s["calls"]["darf"] == 1 and s["calls"]["backend"] == 1
    assert R["zu_gross"]["status"] == 400, "uebergrosse Anfrage bleibt 400"
    assert R["ist"] == [True, True, False, False, False, False, False]


def test_einrichtung_steht_nach_der_rollensperre():
    s = _lies(LOGIC)
    i = s.index("export async function bearbeite(")
    t = s[i:]
    assert t.index("if (ERLAUBTE_ROLLEN.indexOf(rolle) < 0) {") < t.index("if (istEinrichtungsAbfrage(text)) {")
    assert t.index("if (istEinrichtungsAbfrage(text)) {") < t.index("deps.darfSehen(")
    assert t.count("const text = await req.text();") == 1


def _mut(alt, neu):
    s = _lies(LOGIC)
    assert s.count(alt) == 1, alt
    return s.replace(alt, neu, 1)


def test_umkehrprobe_ohne_adminpruefung_bekaeme_der_pl_den_stand(node_exe):
    R2 = _lauf(node_exe, _mut('if (rolle !== "admin") return antwort(origin, 403, { error: "kein_zugriff" });', ""))
    assert R2["pl"]["status"] == 200, "Umkehrprobe: Admin-Riegel der Einrichtungsabfrage waere blind"
    assert R2["monteur"]["status"] == 403, "Monteur endet weiterhin an der Rollensperre davor"


def test_umkehrprobe_ohne_rollensperre_haelt_der_adminriegel(node_exe):
    R2 = _lauf(node_exe, _mut("if (ERLAUBTE_ROLLEN.indexOf(rolle) < 0) {", "if (false) {"))
    assert R2["monteur"]["status"] == 403 and R2["monteur"]["calls"]["backend"] == 0


# ══════════════════════════════════════════════════════════════════════════════
# TEIL C: Proxy-Vorlagen
# ══════════════════════════════════════════════════════════════════════════════
def test_vorlagen_haben_gesund_nur_mit_ok():
    ca = _lies(os.path.join(VORLAGEN, "Caddyfile")).replace("\r\n", "\n")
    ng = _lies(os.path.join(VORLAGEN, "nginx.conf")).replace("\r\n", "\n")
    i = ca.index("handle /gesund {")
    blk = ca[i:ca.index("\n\t}", i)]
    assert 'respond "ok" 200' in blk and "reverse_proxy" not in blk and "forward_auth" not in blk
    assert 'Access-Control-Allow-Origin "https://epkolar.github.io"' in blk
    assert ca.index("handle /gesund {") < ca.rindex("respond 404")
    j = ng.index("location = /gesund {")
    loc = ng[j:ng.index("}", j)]
    assert 'return 200 "ok";' in loc and "proxy_pass" not in loc
    for t in (ca, ng):
        assert not IP_RE.search(t)
