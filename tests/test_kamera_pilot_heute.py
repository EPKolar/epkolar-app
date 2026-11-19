# -*- coding: utf-8 -*-
"""Kamera-Pilot heute (19.11.2026) - statische Pruefung des SQL-Entwurfs, der Ruecknahme und der Doku.

Nichts wird eingespielt. Jede Pruefung ist eine Funktion, die eine Liste von Befunden liefert; die Tests verlangen
fuer die echten Dateien eine LEERE Liste und fuer gezielt verdorbene Abschriften eine NICHT leere (Umkehrproben).
Ausserdem: Nachweis, dass die deployte Edge Function (Version 1, Stand 64fdb53) dem Repo entspricht - index.ts
unterscheidet sich nur in der Kopfzeile "NICHT DEPLOYT" -> "DEPLOYT ...", logic.ts gar nicht.
"""
import hashlib
import io
import os
import re

import pytest

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENTWURF = os.path.join(WURZEL, "sql", "KAMERA_PILOT_HEUTE_ENTWURF.sql")
RUECKNAHME = os.path.join(WURZEL, "sql", "KAMERA_PILOT_HEUTE_RUECKNAHME.sql")
DOKU = os.path.join(WURZEL, "docs", "kameras", "PILOT_HEUTE.md")
TESTLISTE = os.path.join(WURZEL, "docs", "kameras", "PILOT_TESTLISTE.md")
FN_DIR = os.path.join(WURZEL, "supabase", "functions", "kamera-stream")
# Vorlagen des Video-Hosts liegen bewusst AUSSERHALB des Repos (Geschwisterordner); fehlen sie -> Test uebersprungen
PILOT_HOST = os.path.join(os.path.dirname(WURZEL), "epk-kamera-pilot", "pilot-heute")

PILOT_IDS = ("kam_g3_01", "kam_g3_lager03")
PILOT_STREAMS = ("g3_01", "g3_lager03")
IP_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")

# Deployter Stand: seit 20.11.2026 (feature/kamera-gateway) wird EXAKT der Repo-Stand deployt (keine Kopfzeilen-
# Abweichung mehr). Die sha256-Werte und die Version stehen an EINER Stelle: tests/test_kamera_gateway.py.
from test_kamera_gateway import DEPLOYT_INDEX_SHA, DEPLOYT_LOGIC_SHA


def _lies(p):
    with open(p, encoding="utf-8") as fh:
        return fh.read().replace("\r\n", "\n")


def _code(sql):
    """SQL ohne Kommentare (-- bis Zeilenende), damit Kommentare wie 'KEIN CASCADE' nicht zaehlen."""
    return "\n".join(l.split("--", 1)[0] for l in sql.split("\n"))


def _anweisungen(sql, wort):
    return [m.group(0) for m in re.finditer(r"\b" + wort + r"\b[^;]*;", _code(sql), re.I | re.S)]


# ── Pruefungen (liefern Befunde) ────────────────────────────────────────────────
def pruefe_entwurf(sql):
    b = []
    code = _code(sql)
    if not sql.startswith("-- IDEMPOTENT"):
        b.append("IDEMPOTENT-Kopf fehlt (erste Zeile)")
    if re.search(r"\bcascade\b", code, re.I):
        b.append("CASCADE im Code")
    if not re.search(r"ERSETZT[\s\S]{0,120}KAMERAS_PILOT_SEED_ENTWURF\.sql", sql.split("\nbegin;")[0]):
        b.append("Kopf nennt den ersetzten Seed nicht")
    for verboten in ("delete", "drop", "truncate", "alter", "update", "grant", "revoke"):
        if re.search(r"\b" + verboten + r"\b", code, re.I):
            b.append("Entwurf enthaelt " + verboten)
    if not re.search(r"^begin;", code, re.M) or not re.search(r"^commit;", code, re.M):
        b.append("keine Transaktion begin/commit")
    # Vorpruefung VOR dem ersten insert: Tabellen vorhanden + IDs/Streams nicht anders belegt
    i_ins = code.lower().find("insert into")
    vor = code[:i_ins]
    if "to_regclass('public.kameras')" not in vor or "to_regclass('public.kamera_zugriff')" not in vor:
        b.append("Vorpruefung Tabellen fehlt vor dem ersten insert")
    if "anderen Streamnamen" not in vor or "anderen Kamera" not in vor:
        b.append("Vorpruefung belegte IDs/Streamnamen fehlt")
    if not re.search(r"raise notice 'VORHER", code) or not re.search(r"raise notice 'NACHHER", code):
        b.append("Vorher/Nachher-Zahlen fehlen")
    # nur Pilot-IDs, nur Pilot-Streams
    ids = set(re.findall(r"'(kam_[A-Za-z0-9_]+)'", code))
    if ids != set(PILOT_IDS):
        b.append("fremde/fehlende Kamera-IDs: %s" % sorted(ids))
    be = re.search(r"insert into public\.kamera_backend[^;]*;", code, re.S)
    if not be:
        b.append("kein insert kamera_backend")
    else:
        zeilen = re.findall(r"\('(kam_[^']+)',\s*'([^']+)',\s*'([^']+)',\s*'([^']+)'\)", be.group(0))
        if sorted(z[1] for z in zeilen) != sorted(PILOT_STREAMS):
            b.append("Streamnamen != go2rtc: %s" % zeilen)
        for kid, s, q, typ in zeilen:
            if typ != "webrtc":
                b.append("stream_typ nicht webrtc: " + kid)
            if s != q or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", s):
                b.append("Stream/Quelle ungueltig: " + kid)
            if kid.replace("kam_", "", 1) != s:
                b.append("ID passt nicht zum Stream: " + kid)
    if not re.search(r"on conflict \(id\) do nothing", code) or not re.search(r"on conflict \(kamera_id\) do nothing", code):
        b.append("insert nicht idempotent (on conflict)")
    # Zeiten: alle Zeitliterale ganze Minuten; Buero Mo-Fr 07:00-17:00; Admin immer
    for t in re.findall(r"time\s+'([^']*)'", code):
        if not re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d(:00)?", t):
            b.append("Zeit nicht auf ganzer Minute: " + t)
    zug = re.findall(r"insert into public\.kamera_zugriff[^;]*;", code, re.S)
    admin = [z for z in zug if "'admin'" in z]
    buero = [z for z in zug if "'buero'" in z]
    if len(zug) != 2 or len(admin) != 1 or len(buero) != 1:
        b.append("erwartet genau eine admin- und eine buero-Regel")
    else:
        if not re.search(r"'admin',\s*'\{1,2,3,4,5,6,7\}',\s*null,\s*null,\s*true", admin[0]):
            b.append("admin nicht 'immer'")
        if not re.search(r"'buero',\s*'\{1,2,3,4,5\}',\s*time '07:00',\s*time '17:00',\s*true", buero[0]):
            b.append("buero nicht Mo-Fr 07:00-17:00")
        for z in zug:
            if "not exists" not in z or "'PILOT_HEUTE" not in z:
                b.append("Regel ohne Doppelschutz/Kennzeichen")
    for wort in ("monteur", "helfer", "techniker", "projektleiter", "lagerleitung"):
        if re.search(r"'" + wort + r"'", code):
            b.append("weitere Rolle im Entwurf: " + wort)
    # Probe-Block auskommentiert vorhanden
    if not re.search(r"^-- begin;", sql, re.M) or not re.search(r"^-- rollback;", sql, re.M):
        b.append("auskommentierter Probe-Block BEGIN...ROLLBACK fehlt")
    return b


def pruefe_ruecknahme(sql):
    b = []
    code = _code(sql)
    if not sql.startswith("-- IDEMPOTENT"):
        b.append("IDEMPOTENT-Kopf fehlt")
    if re.search(r"\bcascade\b", code, re.I):
        b.append("CASCADE im Code")
    for verboten in ("drop", "truncate", "alter", "update", "insert"):
        if re.search(r"\b" + verboten + r"\b", code, re.I):
            b.append("Ruecknahme enthaelt " + verboten)
    dels = _anweisungen(sql, "delete")
    tabellen = [re.search(r"from\s+public\.(\w+)", d, re.I).group(1) for d in dels]
    if tabellen != ["kamera_zugriff", "kamera_backend", "kameras"]:
        b.append("Reihenfolge der deletes falsch: %s" % tabellen)
    for d in dels:
        if not re.search(r"in \('kam_g3_01', 'kam_g3_lager03'\)", d):
            b.append("delete nicht auf die Pilot-IDs begrenzt: " + " ".join(d.split()))
        if "kamera_abruf_log" in d:
            b.append("Protokoll wird geloescht")
    if dels and "PILOT\\_HEUTE" not in dels[0]:
        b.append("Regel-delete nicht auf PILOT_HEUTE-Regeln begrenzt")
    i_fremd = code.find("raise exception 'Es gibt %")
    if i_fremd < 0 or (dels and i_fremd > code.find(dels[0][:30])):
        b.append("Abbruch bei fremden Regeln fehlt oder steht nach dem ersten delete")
    if not re.search(r"^begin;", code, re.M) or not re.search(r"^commit;", code, re.M):
        b.append("keine Transaktion")
    return b


def pruefe_repo_text(name, text):
    b = []
    if IP_RE.search(text):
        b.append(name + ": IP-Adresse")
    if re.search(r"rtsps?://[^\s`\"]*@\d", text) or re.search(r"rtspx?://\d", text):
        b.append(name + ": Kamera-Adresse")
    if re.search(r"(password|passwort|kennwort|_PW|_PASS)\s*[:=]\s*[^\s<$`\"']", text, re.I):
        b.append(name + ": Kennwort im Klartext?")
    if re.search(r"KAMERA_TOKEN_SECRET\s*=\s*[A-Za-z0-9+/=_-]{20,}", text):
        b.append(name + ": Secret-Wert")
    return b


def pruefe_doku(text):
    b = pruefe_repo_text("PILOT_HEUTE.md", text)
    koepfe = re.findall(r"^## ([a-e])\)", text, re.M)
    if koepfe != list("abcde"):
        b.append("Reihenfolge a-e: %s" % koepfe)
    for teil in ("KAMERA_TOKEN_SECRET", "5c83ca0b", "KAMERA_BACKEND_BASE", "docker compose up", "KAM_USER", "KAM_PW",
                 # GF 19.11. abends: nur Weg A (direkter RTSP), kein Protect -> PROTECT_TOKEN entfaellt;
                 # dafuer muessen Probe-Datei und die Abschottung (VLAN) in der Anleitung stehen.
                 "KAMERA_PILOT_HEUTE_ENTWURF.sql", "KAMERA_PILOT_HEUTE_PROBE.sql", "PILOT_TESTLISTE.md",
                 "KAMERAS_ABSICHERN.md", "kamera_backend"):
        if teil not in text:
            b.append("Doku ohne " + teil)
    if text.find("KAMERA_TOKEN_SECRET") > text.find("## b)"):
        b.append("Secret nicht in Schritt a")
    if len(text.split("\n")) > 70:
        b.append("Doku laenger als eine Seite")
    return b


def pruefe_testliste(text):
    b = pruefe_repo_text("PILOT_TESTLISTE.md", text)
    for teil in ("401", "403", "kein_zugriff", "kamera_abruf_log", "X-Forwarded-Uri", "abgelehnt", "erteilt",
                 "scope\":\"aufzeichnung", "$MONTEUR", "$BUERO", "$ADMIN", "/gesund", "token="):
        if teil not in text:
            b.append("Testliste ohne " + teil)
    return b


# ── Tests: echte Dateien sind sauber ────────────────────────────────────────────
def test_entwurf_sauber():
    assert pruefe_entwurf(_lies(ENTWURF)) == []


def test_ruecknahme_sauber():
    assert pruefe_ruecknahme(_lies(RUECKNAHME)) == []


def test_doku_eine_seite_reihenfolge_ohne_adressen():
    assert pruefe_doku(_lies(DOKU)) == []


def test_testliste_vollstaendig_ohne_adressen():
    assert pruefe_testliste(_lies(TESTLISTE)) == []


def test_keine_adressen_in_den_neuen_sql_dateien():
    assert pruefe_repo_text("ENTWURF", _lies(ENTWURF)) == []
    assert pruefe_repo_text("RUECKNAHME", _lies(RUECKNAHME)) == []


# ── Tests: deployt == Repo ─────────────────────────────────────────────────────
def test_deployte_funktion_entspricht_dem_repo():
    # Pin angepasst 20.11.2026: Redeploy aus genau den committeten Dateien (Gateway-Basis), daher ohne Kopfzeilen-Tausch.
    s = _lies(os.path.join(FN_DIR, "index.ts"))
    assert hashlib.sha256(s.encode("utf-8")).hexdigest() == DEPLOYT_INDEX_SHA
    # Aendert sich logic.ts oder index.ts, ist ein Redeploy noetig -> danach die Werte in test_kamera_gateway.py nachziehen.
    assert hashlib.sha256(_lies(os.path.join(FN_DIR, "logic.ts")).encode("utf-8")).hexdigest() == DEPLOYT_LOGIC_SHA


# ── Gegenstueck auf dem Video-Host (ausserhalb des Repos) ───────────────────────
GATEWAY_SEED = os.path.join(WURZEL, "sql", "KAMERA_GATEWAY_SEED_ENTWURF.sql")


def _seed_streams(sql):
    """Live-Streamnamen der G3 aus dem Gateway-Seed (kamera_backend-insert mit festen Werten, ohne Kommentare)."""
    code = _code(sql)
    be = [x for x in re.findall(r"insert into public\.kamera_backend[^;]*;", code, re.S) if "values" in x]
    return {z[1] for x in be for z in re.findall(r"\('([^']+)',\s*'([^']+)',\s*null,\s*'webrtc'\)", x)}


def _vorlage_abgleich(seed_sql, go2rtc_text):
    yaml = pytest.importorskip("yaml")
    g = yaml.safe_load(go2rtc_text)
    s = _seed_streams(seed_sql)
    b = []
    if len(s) != 4:
        b.append("Seed liefert nicht 4 G3-Streams: %s" % sorted(s))
    if set(g["streams"]) != s:
        b.append("Vorlage %s != Seed %s" % (sorted(g["streams"]), sorted(s)))
    return b


def test_streamnamen_gleich_go2rtc():
    # Pin angepasst 20.11.2026: der Pilot-Seed (g3_01/g3_lager03) ist SUPERSEDED. Abgeglichen werden jetzt die
    # Streamnamen des Gateway-Seeds (sql/KAMERA_GATEWAY_SEED_ENTWURF.sql) mit der go2rtc-Vorlage. Frigate ist in der
    # Vorlage abgeschaltet (nur Live) -> frigate.yml wird nicht mehr verlangt.
    if not os.path.isdir(PILOT_HOST):
        pytest.skip("Vorlagen des Video-Hosts nicht auf diesem Rechner")
    assert _vorlage_abgleich(_lies(GATEWAY_SEED), _lies(os.path.join(PILOT_HOST, "go2rtc.yaml"))) == []


def test_umkehrprobe_streamnamen_abgleich():
    # Ohne Vorlage auf dem Rechner: synthetische Vorlage aus dem Seed selbst - umbenannter Stream muss auffallen
    pytest.importorskip("yaml")
    seed = _lies(GATEWAY_SEED)
    s = sorted(_seed_streams(seed))
    gut = "streams:\n" + "".join("  %s:\n    - rtsp://${KAM_USER}:${KAM_PW}@kamera/s0\n" % x for x in s)
    assert _vorlage_abgleich(seed, gut) == []
    assert _vorlage_abgleich(seed, gut.replace("  " + s[0] + ":", "  " + s[0] + "_alt:", 1)) != []
    kaputt = re.sub(r"\('" + s[0] + r"',(\s*)'" + s[0] + "'", r"('" + s[0] + r"',\1'g3_01'", seed, count=1)
    assert kaputt != seed
    assert _vorlage_abgleich(kaputt, gut) != []


# ── Umkehrproben: jede Pruefung schlaegt an, wenn die Datei verdorben wird ─────
def _verdorben(text, alt, neu):
    assert text.count(alt) >= 1, alt
    return text.replace(alt, neu, 1)


@pytest.mark.parametrize("alt,neu,erwartet", [
    ("-- IDEMPOTENT", "-- idempotent?", "IDEMPOTENT-Kopf"),
    ("on conflict (id) do nothing;", "on conflict (id) do nothing;\ndelete from public.kameras where id = 'x' cascade;", "CASCADE"),
    ("time '17:00', true", "time '17:00:30', true", "ganzer Minute"),
    ("'{1,2,3,4,5}', time '07:00'", "'{1,2,3,4,5,6}', time '07:00'", "buero nicht Mo-Fr"),
    ("'g3_lager03', 'g3_lager03', 'webrtc'", "'g3_lager3', 'g3_lager3', 'webrtc'", "Streamnamen"),
    ("'g3_01',      'g3_01',      'webrtc'", "'g3_01',      'g3_01',      'mjpeg'", "stream_typ"),
    ("raise notice 'VORHER", "raise notice 'vorab", "Vorher/Nachher"),
    ("to_regclass('public.kamera_zugriff')", "to_regclass('public.kamera_zugriffX')", "Vorpruefung Tabellen"),
    ("'admin', '{1,2,3,4,5,6,7}', null, null, true", "'admin', '{1,2,3,4,5}', null, null, true", "admin nicht"),
    ("KAMERAS_PILOT_SEED_ENTWURF.sql", "ALTER_SEED.sql", "ersetzten Seed"),
    ("-- rollback;", "-- (fehlt)", "Probe-Block"),
])
def test_umkehrprobe_entwurf(alt, neu, erwartet):
    befunde = pruefe_entwurf(_verdorben(_lies(ENTWURF), alt, neu))
    assert any(erwartet in x for x in befunde), befunde


def test_umkehrprobe_entwurf_monteur_regel():
    s = _lies(ENTWURF).replace("select k.id, 'buero'", "select k.id, 'monteur'", 1)
    assert any("monteur" in x for x in pruefe_entwurf(s))


@pytest.mark.parametrize("alt,neu,erwartet", [
    # Reihenfolge vertauscht: kameras vor kamera_backend
    ("  -- 2. Backend-Zuordnung\n  delete from public.kamera_backend where kamera_id in ('kam_g3_01', 'kam_g3_lager03');\n"
     "  -- 3. Kameras\n  delete from public.kameras        where id in ('kam_g3_01', 'kam_g3_lager03');",
     "  delete from public.kameras        where id in ('kam_g3_01', 'kam_g3_lager03');\n"
     "  delete from public.kamera_backend where kamera_id in ('kam_g3_01', 'kam_g3_lager03');", "Reihenfolge"),
    ("delete from public.kamera_backend where kamera_id in ('kam_g3_01', 'kam_g3_lager03');",
     "delete from public.kamera_backend;", "nicht auf die Pilot-IDs"),
    ("and bemerkung like 'PILOT\\_HEUTE%';", ";", "PILOT_HEUTE"),
    ("delete from public.kameras        where id in ('kam_g3_01', 'kam_g3_lager03');",
     "delete from public.kameras        where id in ('kam_g3_01', 'kam_g3_lager03') cascade;", "CASCADE"),
    ("raise exception 'Es gibt %", "raise notice 'Es gibt %", "fremden Regeln"),
])
def test_umkehrprobe_ruecknahme(alt, neu, erwartet):
    s = _lies(RUECKNAHME)
    # Parameter oben ausgerichtet geschrieben; die echte Datei hat ein Leerzeichen
    alt = alt.replace("public.kameras        where", "public.kameras where")
    neu = neu.replace("public.kameras        where", "public.kameras where")
    befunde = pruefe_ruecknahme(_verdorben(s, alt, neu))
    assert any(erwartet in x for x in befunde), befunde


@pytest.mark.parametrize("text,erwartet", [
    ("Kamera unter 192.168.1.20 erreichbar", "IP-Adresse"),
    ("rtsp://admin:x@10.0.0.5:554/s0", "Kamera-Adresse"),
    ("KAM_PW=geheim123", "Kennwort"),
    ("KAMERA_TOKEN_SECRET=AbCdEfGhIjKlMnOpQrStUvWxYz0123", "Secret-Wert"),
])
def test_umkehrprobe_keine_adressen(text, erwartet):
    befunde = pruefe_repo_text("x", text)
    assert any(erwartet in x for x in befunde), befunde


def test_umkehrprobe_doku_reihenfolge_und_laenge():
    d = _lies(DOKU)
    assert any("Reihenfolge" in x for x in pruefe_doku(d.replace("## c)", "## x)", 1)))
    assert any("eine Seite" in x for x in pruefe_doku(d + "\n" * 80))
    assert any("5c83ca0b" in x for x in pruefe_doku(d.replace("5c83ca0b", "????????")))


def test_umkehrprobe_deploy_nachweis():
    s = _lies(os.path.join(FN_DIR, "index.ts"))
    assert hashlib.sha256((s + " ").encode("utf-8")).hexdigest() != DEPLOYT_INDEX_SHA
    assert hashlib.sha256(s.replace("Deno.serve", "Deno.serveX", 1).encode("utf-8")).hexdigest() != DEPLOYT_INDEX_SHA


def test_weg_a_ohne_protect_und_probe_datei_ausfuehrbar():
    """GF 19.11.: Pilot nur Weg A; Probe als eigene Datei (BEGIN ... ROLLBACK), bricht garantiert ab."""
    doku = io.open(os.path.join(WURZEL, "docs", "kameras", "PILOT_HEUTE.md"), encoding="utf-8").read()
    assert "PROTECT_TOKEN" not in doku and "Weg B" not in doku
    sql = io.open(os.path.join(WURZEL, "sql", "KAMERA_PILOT_HEUTE_PROBE.sql"), encoding="utf-8").read()
    assert sql.count("raise exception 'PROBE_ERGEBNIS %', r;") == 1 and "\nrollback;" in sql
    code = [z.strip().lower() for z in sql.splitlines() if z.strip() and not z.strip().startswith("--")]
    assert not [z for z in code if z.startswith("commit")], "Probe darf nie committen"
    assert not [z for z in code if "cascade" in z] and "192.168" not in sql
