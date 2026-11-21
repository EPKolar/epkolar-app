# -*- coding: utf-8 -*-
"""Mobotix am QNAP-Gateway (21.11.2026) - EIN Weg, EINE Quelle.

Kanonisch: tools/kamera-proxy-auth/qnap/go2rtc.yaml (Streamnamen + Quellen, nur ${VAR}) und
sql/KAMERA_MOBOTIX_SEED_*.sql (App-Seite). Pruefskript scripts/go2rtc_streams_pruefen.py.
(a) Mobotix-Quellen nur mit ${MOBOTIX_USER}/${MOBOTIX_PASS}, keine echten Zugangsdaten, keine IP-Adressen
(b) go2rtc-Vorlage == SQL-Streamnamen == Pruefskript; Namen passen auf die Caddy-mjpeg-Route
(c) stream_typ mjpeg fuer genau die 5 Mobotix, nativer HTTP-Erzeuger (kein ffmpeg/Umwandlung)
(d) genau die 5 Mobotix (Endungen .32-.36), alter mob32..mob36-Block bleibt aus
Jede Pruefung liefert Befunde; echte Dateien -> leer, verdorbene Abschriften -> nicht leer (Umkehrproben).
"""
import importlib.util
import io
import json
import os
import re

import pytest

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QNAP = os.path.join(WURZEL, "tools", "kamera-proxy-auth", "qnap")
GO2RTC = os.path.join(QNAP, "go2rtc.yaml")
CADDY = os.path.join(QNAP, "Caddyfile")
SQL = os.path.join(WURZEL, "sql")
SEED = os.path.join(SQL, "KAMERA_MOBOTIX_SEED_ENTWURF.sql")
PROBE = os.path.join(SQL, "KAMERA_MOBOTIX_SEED_PROBE.sql")
RUECK = os.path.join(SQL, "KAMERA_MOBOTIX_SEED_RUECKNAHME.sql")
GW_SEED = os.path.join(SQL, "KAMERA_GATEWAY_SEED_ENTWURF.sql")
DOKU = os.path.join(WURZEL, "docs", "kameras", "MOBOTIX.md")
SKRIPT = os.path.join(WURZEL, "scripts", "go2rtc_streams_pruefen.py")

MOB = ("hof01", "hochregal03", "hochregal02", "elektrolager01", "elektrolager02")
G3 = ("hochregal01", "verkauf02", "elektrolager03", "cam39")
ALT = ("mob32", "mob33", "mob34", "mob35", "mob36")
ENDUNG = {"hof01": "32", "hochregal03": "33", "hochregal02": "34", "elektrolager01": "35", "elektrolager02": "36"}
IP_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
NAME_RE = re.compile(r"[a-z0-9]{1,64}")


def _lies(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read().replace("\r\n", "\n")


def _mut(text, alt, neu):
    assert text.count(alt) >= 1, alt
    return text.replace(alt, neu, 1)


def _skript():
    spec = importlib.util.spec_from_file_location("go2rtc_streams_pruefen", SKRIPT)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ── go2rtc-Vorlage ──────────────────────────────────────────────────────────
def streams_der_vorlage(text):
    """{name: [quellen]} aus dem streams:-Abschnitt (zeilenweise, ohne YAML-Bibliothek)."""
    teil = text.split("\nstreams:\n", 1)
    if len(teil) != 2:
        return {}
    out, akt = {}, None
    for z in teil[1].split("\n"):
        m = re.match(r"^  ([A-Za-z0-9_-]+):\s*(#.*)?$", z)
        if m:
            akt = m.group(1)
            out[akt] = []
            continue
        m = re.match(r"^    - (\S+)", z)
        if m and akt:
            out[akt].append(m.group(1))
        elif re.match(r"^\S", z):
            break
    return out


def pruefe_vorlage(text):
    b = []
    if IP_RE.search(text):
        b.append("IP-Adresse in der Vorlage")
    st = streams_der_vorlage(text)
    if sorted(st) != sorted(G3 + MOB):
        b.append("Streams != 4 G3 + 5 Mobotix: %s" % sorted(st))
    for n in st:
        if not NAME_RE.fullmatch(n):
            b.append("Streamname ausserhalb a-z0-9: " + n)
    for n in MOB:
        q = st.get(n, [])
        if len(q) != 1:
            b.append(n + ": nicht genau eine Quelle")
            continue
        if not q[0].startswith("http://${MOBOTIX_USER}:${MOBOTIX_PASS}@${CAM_" + n.upper() + "_IP}/"):
            b.append(n + ": nicht http://${MOBOTIX_USER}:${MOBOTIX_PASS}@${CAM_" + n.upper() + "_IP}/")
        if not re.search(r"/(cgi-bin|control)/faststream\.jpg\?stream=full&needlength&fps=\d+$", q[0]):
            b.append(n + ": nicht faststream.jpg?stream=full&needlength&fps=")
    for n in G3:
        q = st.get(n, [])
        if len(q) != 1 or not q[0].startswith("rtsp://${KAM_USER}:${KAM_PASS}@${CAM_" + n.upper() + "_IP}:554/"):
            b.append(n + ": G3-Quelle nicht rtsp://${KAM_USER}:${KAM_PASS}@${CAM_..._IP}:554/")
    # Zugangsdaten nur als Platzhalter: jedes user:pass@ muss ${..}:${..}@ sein
    for m in re.finditer(r"://([^@\s/]*)@", text):
        if not re.fullmatch(r"\$\{[A-Z_]+\}:\$\{[A-Z_]+\}", m.group(1)):
            b.append("Zugangsdaten nicht als Platzhalter: " + m.group(1)[:3] + "...")
    c = "\n".join(z.split(" #", 1)[0] for z in text.split("\n") if not z.lstrip().startswith("#"))
    if re.search(r"ffmpeg:|exec:|#video=|#hardware|preload", c):
        b.append("Umwandlung/Dauerabruf statt nativem Durchreichen")
    if "${QNAP_LAN_IP}:8555" not in c:
        b.append("webrtc candidate ${QNAP_LAN_IP}:8555 fehlt")
    # go2rtc-API: lauscht auf allen Schnittstellen (Caddy kommt aus der Docker-Bruecke) -> Anmeldung Pflicht
    api = re.search(r"^api:\n((?:[ \t]+.*\n|\n)*)", c + "\n", re.M)
    api = api.group(1) if api else ""
    if not re.search(r'^  listen: "127\.0\.0\.1:', api, re.M):
        if not re.search(r"^  username: \$\{GO2RTC_USER\}$", api, re.M) or not re.search(r"^  password: \$\{GO2RTC_PASS\}$", api, re.M):
            b.append("go2rtc-API auf allen Schnittstellen ohne Anmeldung (username/password ${GO2RTC_USER}/${GO2RTC_PASS})")
    if re.search(r"^\s+(username|password):[ \t]*(?![ \t]|\$\{)", c, re.M):
        b.append("API-Zugangsdaten nicht als Platzhalter")
    if re.search(r"local_auth:\s*false|origin:", c):
        b.append("API-Schutz gelockert")
    if not re.search(r'^rtsp:\n  listen: ""', c, re.M):
        b.append("RTSP-Server nicht aus")
    for alt in ALT:
        if re.search(r"\b" + alt + r"\b", text):
            b.append("alter Name " + alt)
    for n, e in ENDUNG.items():
        if not re.search(r"^  " + n + r":\s+# Endung \." + e + r"\b", text, re.M):
            b.append(n + ": Endung ." + e + " nicht vermerkt")
    return b


def test_vorlage_sauber():
    assert pruefe_vorlage(_lies(GO2RTC)) == []


GELD = "http://${MOBOTIX_USER}:${MOBOTIX_PASS}@${CAM_HOF01_IP}/"


@pytest.mark.parametrize("alt,neu,erwartet", [
    (GELD, "http://epk_live:Geheim123@${CAM_HOF01_IP}/", "Platzhalter"),
    (GELD, "http://${MOBOTIX_USER}:${MOBOTIX_PASS}@" + ".".join(("192", "168", "33", "32")) + "/", "IP-Adresse"),
    (GELD, "http://${KAM_USER}:${KAM_PASS}@${CAM_HOF01_IP}/", "nicht http://${MOBOTIX_USER}"),
    ("  hochregal02:   ", "  hochregal_02:  ", "Streams != "),
    ("  hof01:  ", "  Hof01:  ", "Streams != "),
    ("    - " + GELD, "    - ffmpeg:" + GELD, "Umwandlung"),
    ("&needlength&fps=12\n  hochregal03", "&needlength&fps=12#video=h264\n  hochregal03", "Umwandlung"),
    ("  elektrolager02:              # Endung .36 (SurvStation: Elektrolager02)\n",
     "  elektrolager02:              # Endung .36 (SurvStation: Elektrolager02)\n  mob33:\n    - http://${MOBOTIX_USER}:${MOBOTIX_PASS}@${CAM_X_IP}/cgi-bin/faststream.jpg?stream=full&needlength&fps=12\n",
     "Streams != "),
    ("# Endung .34", "# Endung .33", "Endung .34"),
    ("faststream.jpg?stream=full&needlength&fps=12\n  hochregal02", "faststream.jpg\n  hochregal02", "needlength"),
    ("  username: ${GO2RTC_USER}\n", "", "ohne Anmeldung"),
    ("  username: ${GO2RTC_USER}\n  password: ${GO2RTC_PASS}\n", "", "ohne Anmeldung"),
    ("  password: ${GO2RTC_PASS}\n", "  password: geheim\n", "Platzhalter"),
    ('rtsp:\n  listen: ""', 'rtsp:\n  listen: ":8554"', "RTSP-Server nicht aus"),
    ("  username: ${GO2RTC_USER}\n", "  username: ${GO2RTC_USER}\n  local_auth: false\n", "gelockert"),
])
def test_umkehrprobe_vorlage(alt, neu, erwartet):
    befunde = pruefe_vorlage(_mut(_lies(GO2RTC), alt, neu))
    assert any(erwartet in x for x in befunde), befunde


def test_vorlage_variablen_in_doku():
    """Jede ${VAR} der Vorlage steht in MOBOTIX.md (kam.env-Liste) - gemessen, nicht abgeschrieben."""
    d = _lies(DOKU)
    code = "\n".join(z for z in _lies(GO2RTC).split("\n") if not z.lstrip().startswith("#"))
    gefunden = sorted(set(re.findall(r"\$\{([A-Z0-9_]+)\}", code)))
    assert len(gefunden) == 16, gefunden   # 9 Adressen + 2 Mobotix + 2 G3 + 2 API + QNAP_LAN_IP
    for v in gefunden:
        assert "`" + v + "`" in d, v


# ── Caddy-Route ─────────────────────────────────────────────────────────────
def test_namen_passen_auf_caddy_mjpeg_route():
    c = _lies(CADDY)
    m = re.search(r"@mjpeg path_regexp mjpeg (\S+)", c)
    assert m, "mjpeg-Route fehlt"
    for n in MOB:
        assert re.match(m.group(1), "/live/%s/mjpeg" % n), n
    assert "rewrite * /api/stream.mjpeg?src={re.mjpeg.1}" in c


def test_umkehrprobe_caddy_namen():
    m = re.search(r"@mjpeg path_regexp mjpeg (\S+)", _lies(CADDY))
    assert not re.match(m.group(1), "/live/hof 01/mjpeg")


UPSTREAM_KOPF = 'header_up Authorization "Basic {$GO2RTC_BASIC}"'


def pruefe_caddy_anmeldung(text):
    """Jedes reverse_proxy zu go2rtc meldet sich an (Basic aus der Umgebung), keine woertlichen Zugangsdaten."""
    b = []
    c = "\n".join(z for z in text.split("\n") if not z.lstrip().startswith("#"))
    alle = re.findall(r"reverse_proxy (\S+)", c)
    mit = re.findall(r"reverse_proxy \{\$QNAP_LAN_IP\}:1984 \{\n\s*" + re.escape(UPSTREAM_KOPF) + r"\n", c)
    if len(alle) < 5:
        b.append("weniger als 5 Weiterleitungen (whep, mjpeg, bild, hls, hlsteil): %d" % len(alle))
    if len(mit) != len(alle):
        b.append("reverse_proxy ohne go2rtc-Anmeldung: %d von %d" % (len(alle) - len(mit), len(alle)))
    for m in re.findall(r"Basic ([^\s\"]+)", c):
        if m != "{$GO2RTC_BASIC}":
            b.append("woertliche Zugangsdaten im Caddyfile")
    return b


def test_caddy_meldet_sich_bei_go2rtc_an():
    assert pruefe_caddy_anmeldung(_lies(CADDY)) == []


@pytest.mark.parametrize("alt,neu,erwartet", [
    ("\t\t\t\t" + UPSTREAM_KOPF + "\n\t\t\t\tflush_interval -1", "\t\t\t\tflush_interval -1", "ohne go2rtc-Anmeldung"),
    ("\t\t\treverse_proxy {$QNAP_LAN_IP}:1984 {\n\t\t\t\t" + UPSTREAM_KOPF + "\n\t\t\t}\n",
     "\t\t\treverse_proxy {$QNAP_LAN_IP}:1984\n", "ohne go2rtc-Anmeldung"),
    ("Basic {$GO2RTC_BASIC}\"\n\t\t\t\tflush", "Basic ZXBrOmdlaGVpbQ==\"\n\t\t\t\tflush", "woertliche"),
])
def test_umkehrprobe_caddy_anmeldung(alt, neu, erwartet):
    befunde = pruefe_caddy_anmeldung(_mut(_lies(CADDY), alt, neu))
    assert any(erwartet in x for x in befunde), befunde


def test_compose_reicht_go2rtc_anmeldung_durch():
    for f in ("docker-compose.yml", "qnap-gateway-inline.compose.yml"):
        t = _lies(os.path.join(QNAP, f))
        assert re.search(r"^      - GO2RTC_BASIC=\$\{GO2RTC_BASIC:\?", t, re.M), f
    env = _lies(os.path.join(QNAP, "ENV.md"))
    for n in ("GO2RTC_BASIC", "GO2RTC_USER", "GO2RTC_PASS"):
        assert "`" + n + "`" in env, n
    assert "localhost" in env and "Firewall" in env
    d = _lies(DOKU)
    assert "GO2RTC_USER" in d and "GO2RTC_BASIC" in d and "snapshot.jpg?token=" in d


# ── SQL ─────────────────────────────────────────────────────────────────────
def _code(sql):
    return "\n".join(l.split("--", 1)[0] for l in sql.split("\n"))


def pruefe_sql(name, sql):
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
    if re.search(r"(passwort|kennwort\b|password|MOBOTIX_PASS|MOBOTIX_USER|KAM_PASS|KAM_USER)", sql, re.I):
        b.append(name + ": Zugangsdaten")
    for alt in ALT:
        if re.search(r"'" + alt + r"'", code) and name != "RUECK":
            # alte IDs nur in Abbruch-Pruefungen (exists ... in (...)) erlaubt
            for z in code.split(";"):
                if "'" + alt + "'" in z and "insert" in z:
                    b.append(name + ": alter Name " + alt + " wird angelegt")
    for g in G3:
        for z in code.split(";"):
            if "'" + g + "'" in z and ("insert" in z or "delete" in z):
                b.append(name + ": G3 " + g + " wird angefasst")
    return b


def pruefe_seed(sql):
    b = pruefe_sql("SEED", sql)
    code = _code(sql)
    if "begin;" not in code or "commit;" not in code:
        b.append("SEED: nicht BEGIN ... COMMIT")
    be = re.findall(r"insert into public\.kamera_backend[^;]*;", code, re.S)
    paare = re.findall(r"\('([a-z0-9]+)',\s*'([a-z0-9]+)',\s*null,\s*'(\w+)'\)", "".join(be))
    if sorted(p[0] for p in paare) != sorted(MOB):
        b.append("SEED: Zuordnung nicht genau die 5 Mobotix: %s" % sorted(p[0] for p in paare))
    for kid, stream, typ in paare:
        if kid != stream:
            b.append("SEED: ID != Stream " + kid)
        if typ != "mjpeg":
            b.append("SEED: stream_typ nicht mjpeg " + kid)
    kam = re.findall(r"insert into public\.kameras[^;]*;", code, re.S)
    ids = re.findall(r"\('([a-z0-9]+)',\s*'[^']+',\s*'[^']*',\s*'Mobotix'", "".join(kam))
    if sorted(ids) != sorted(MOB):
        b.append("SEED: Kameras nicht genau die 5 Mobotix: %s" % sorted(ids))
    if "on conflict (id) do nothing" not in code or "on conflict (kamera_id) do nothing" not in code:
        b.append("SEED: nicht idempotent (on conflict)")
    zug = re.findall(r"insert into public\.kamera_zugriff[^;]*;", code, re.S)
    if len(zug) != 2:
        b.append("SEED: nicht genau 2 Regel-Inserts")
    for z in zug:
        if "'MOBOTIX_SEED" not in z:
            b.append("SEED: Regel ohne Kennzeichen")
        if "not exists" not in z:
            b.append("SEED: Regel nicht idempotent")
        if "'admin'" in z and not re.search(r"'admin',\s*'\{1,2,3,4,5,6,7\}',\s*null,\s*null,\s*true", z):
            b.append("SEED: admin nicht immer")
        if "'buero'" in z and not re.search(r"'buero',\s*'\{1,2,3,4,5\}',\s*time '07:00',\s*time '17:00',\s*true", z):
            b.append("SEED: buero nicht Mo-Fr 07-17")
    if not [z for z in zug if "'admin'" in z] or not [z for z in zug if "'buero'" in z]:
        b.append("SEED: admin/buero-Regel fehlt")
    for wort in ("monteur", "helfer", "techniker", "projektleiter", "lagerleitung"):
        if re.search(r"'" + wort + r"'", code):
            b.append("SEED: weitere Rolle " + wort)
    if not re.search(r"if exists \(select 1 from public\.kameras where id in \('mob32', 'mob33', 'mob34', 'mob35', 'mob36'\)\)", code) \
            or "raise exception 'Alter Mobotix-Block" not in code:
        b.append("SEED: Sperre gegen alten mob-Block fehlt")
    if not re.search(r"if m_kam <> 5 or m_be <> 5 then\s*raise exception", code):
        b.append("SEED: Nachher-Kontrolle fehlt")
    return b


def test_seed_sauber():
    assert pruefe_seed(_lies(SEED)) == []


@pytest.mark.parametrize("alt,neu,erwartet", [
    ("('hof01',          'hof01',          null, 'mjpeg')", "('hof01',          'hof01',          null, 'webrtc')", "nicht mjpeg"),
    ("('hochregal02',    'hochregal02',    null, 'mjpeg')", "('hochregal02',    'hochregal_02',    null, 'mjpeg')", "nicht genau die 5"),
    ("'MOBOTIX_SEED buero Mo-Fr 07-17'", "'buero Mo-Fr 07-17'", "Kennzeichen"),
    ("time '07:00', time '17:00', true, 'MOBOTIX_SEED", "time '06:00', time '17:00', true, 'MOBOTIX_SEED", "buero nicht"),
    ("'admin', '{1,2,3,4,5,6,7}'", "'admin', '{1,2,3,4,5}'", "admin nicht immer"),
    ("on conflict (kamera_id) do nothing", "", "on conflict"),
    ("raise exception 'Alter Mobotix-Block", "raise notice 'Alter Mobotix-Block", "Sperre"),
    ("  ('elektrolager02', 'Elektrolager 02', 'Standort folgt', 'Mobotix', 'Mobotix (Modell folgt)', true, 3)",
     "  ('elektrolager02', 'Elektrolager 02', 'Standort folgt', 'Mobotix', 'Mobotix (Modell folgt)', true, 3),\n"
     "  ('mob33', 'x', 'Standort folgt', 'Mobotix', 'Mobotix (Modell folgt)', true, 3)", "alter Name mob33"),
    ("begin;", "begin;\ndelete from public.kamera_backend where kamera_id = 'cam39';", "G3 cam39"),
    ("-- 1. Stammdaten", "-- http://user:pw@x\n-- 1. Stammdaten", "Adresse"),
])
def test_umkehrprobe_seed(alt, neu, erwartet):
    befunde = pruefe_seed(_mut(_lies(SEED), alt, neu))
    assert any(erwartet in x for x in befunde), befunde


def pruefe_probe(sql):
    b = pruefe_sql("PROBE", sql)
    code = _code(sql)
    if not re.search(r"\nrollback;\s*$", code.rstrip() + "\n") or "commit;" in code:
        b.append("PROBE: endet nicht mit ROLLBACK / enthaelt COMMIT")
    if "raise exception 'PROBE_ERGEBNIS %', r;" not in code:
        b.append("PROBE: Ergebnis nicht per Abbruch")
    if "array['hof01','hochregal03','hochregal02','elektrolager01','elektrolager02']" not in code:
        b.append("PROBE: ID-Liste nicht die 5 Mobotix")
    for kid in MOB:
        if not re.search(r"\('%s','%s',null,'mjpeg'\)" % (kid, kid), code):
            b.append("PROBE: %s nicht mjpeg" % kid)
    for teil in ("admin_samstag_0300_alle", "buero_mo0700", "buero_mo0659", "buero_mo1659", "buero_mo1700",
                 "buero_samstag_alle", "monteur_darf", "admin_backend", "regeln=", "g3_vorhanden"):
        if teil not in code:
            b.append("PROBE: Pruefzeile fehlt " + teil)
    return b


def test_probe_sauber():
    assert pruefe_probe(_lies(PROBE)) == []


@pytest.mark.parametrize("alt,neu,erwartet", [
    ("\nrollback;", "\ncommit;", "ROLLBACK"),
    ("('hof01','hof01',null,'mjpeg')", "('hof01','hof01',null,'webrtc')", "hof01 nicht mjpeg"),
    ("raise exception 'PROBE_ERGEBNIS %', r;", "raise notice 'PROBE_ERGEBNIS %', r;", "Abbruch"),
    ("buero_mo1700", "buero_mo1800", "buero_mo1700"),
])
def test_umkehrprobe_probe(alt, neu, erwartet):
    befunde = pruefe_probe(_mut(_lies(PROBE), alt, neu))
    assert any(erwartet in x for x in befunde), befunde


MOB_LISTE = "('hof01', 'hochregal03', 'hochregal02', 'elektrolager01', 'elektrolager02')"


def pruefe_ruecknahme(sql):
    b = pruefe_sql("RUECK", sql)
    code = _code(sql)
    dels = re.findall(r"delete from public\.(\w+)\s+where ([^;]*);", code)
    if [t for t, _ in dels] != ["kamera_zugriff", "kamera_backend", "kameras"]:
        b.append("RUECK: Reihenfolge Regeln -> Zuordnung -> Kamera: %s" % [t for t, _ in dels])
    for t, w in dels:
        if MOB_LISTE not in w:
            b.append("RUECK: delete %s nicht auf die 5 Mobotix" % t)
    if dels and "bemerkung like 'MOBOTIX\\_SEED%'" not in dels[0][1]:
        b.append("RUECK: Regeln nicht nur MOBOTIX_SEED")
    if not re.search(r"delete from public\.\w+\s+where", code) or re.search(r"delete from public\.\w+\s*;", code):
        b.append("RUECK: delete ohne where")
    if "raise exception 'Es gibt %" not in code:
        b.append("RUECK: fremde Regeln nicht abgesichert")
    return b


def test_ruecknahme_sauber():
    assert pruefe_ruecknahme(_lies(RUECK)) == []


@pytest.mark.parametrize("alt,neu,erwartet", [
    ("  delete from public.kamera_backend\n   where kamera_id in " + MOB_LISTE + ";",
     "  delete from public.kamera_backend;", "delete"),
    ("\n     and bemerkung like 'MOBOTIX\\_SEED%';", ";", "MOBOTIX_SEED"),
    ("raise exception 'Es gibt %", "raise notice 'Es gibt %", "fremde Regeln"),
    ("   where id in " + MOB_LISTE + ";\n\n", "   where id in " + MOB_LISTE + " cascade;\n\n", "CASCADE"),
])
def test_umkehrprobe_ruecknahme(alt, neu, erwartet):
    befunde = pruefe_ruecknahme(_mut(_lies(RUECK), alt, neu))
    assert any(erwartet in x for x in befunde), befunde


def test_gateway_seed_mobotix_schalter_bleibt_aus():
    g = _lies(GW_SEED)
    assert "set local epk.mobotix_aktiv = 'false';" in g
    assert not re.search(r"set local epk\.mobotix_aktiv = 'true'", _code(g))
    assert "ABGELOEST 21.11.2026" in g and "KAMERA_MOBOTIX_SEED_ENTWURF.sql" in g


# ── Eine Quelle: Vorlage == SQL == Skript ───────────────────────────────────
def test_namen_ueberall_gleich():
    st = streams_der_vorlage(_lies(GO2RTC))
    seed_ids = re.findall(r"\('([a-z0-9]+)',\s*'\1',\s*null,\s*'mjpeg'\)", _lies(SEED))
    sk = _skript()
    assert sorted(seed_ids) == sorted(MOB)
    assert set(st) == set(sk.G3 + sk.MOBOTIX) == set(G3 + MOB)
    assert dict(sk.ERWARTET) == dict([(n, "h264") for n in G3] + [(n, "mjpeg") for n in MOB])
    for n in MOB:
        assert st[n][0].startswith("http://")      # nativer HTTP-Erzeuger -> MJPEG
    for n in G3:
        assert st[n][0].startswith("rtsp://")


# ── Pruefskript mit Attrappen ───────────────────────────────────────────────
class _Antwort(object):
    def __init__(self, daten):
        self._d = daten
        self.zu = False

    def read(self, n=-1):
        return self._d if n < 0 else self._d[:n]

    def close(self):
        self.zu = True


class _Go2rtc(object):
    """Attrappe: Erzeuger nur verbunden, solange ein Zuschauer offen ist (wie go2rtc).
    fehl[name] = Anzahl der ersten Anstoesse, die scheitern (wackelige Kamera); -1 = scheitert immer."""

    def __init__(self, fehl=None, nur_url=()):
        self.fehl = dict(fehl or {})
        self.nur_url = set(nur_url)
        self.offen = {}
        self.aufrufe = []
        self.koepfe = []

    def __call__(self, url, timeout, kopf=None):
        self.aufrufe.append(url)
        self.koepfe.append(dict(kopf or {}))
        pfad, _, q = url.partition("?")
        src = dict(x.split("=", 1) for x in q.split("&") if "=" in x).get("src")
        if pfad.endswith("/api/streams"):
            eintrag = {"producers": [{"url": "http://geheim"}], "consumers": []}
            if self.offen.get(src) and src not in self.nur_url:
                eintrag = {"producers": [{"url": "http://geheim", "remote_addr": "x", "medias": ["video"]}],
                           "consumers": [{"id": 1}]}
            return _Antwort(json.dumps(eintrag).encode())
        f = self.fehl.get(src, 0)
        if f != 0:
            self.fehl[src] = f - 1 if f > 0 else -1
            raise OSError("timeout")
        self.offen[src] = True
        daten = b"--myboundary\r\nContent-Type: image/jpeg\r\n\r\n\xff\xd8\xff" if "mjpeg" in pfad else b"\x00\x00\x00\x1cftyp"
        a = _Antwort(daten)
        orig = a.close

        def zu():
            self.offen[src] = False
            orig()
        a.close = zu
        return a


class _Uhr(object):
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t

    def schlafen(self, s):
        self.t += s


def _lauf(g, fenster=30.0, takt=3.0, kopf=None):
    sk = _skript()
    u = _Uhr()
    zeilen = []
    ok, stand = sk.pruefen("http://127.0.0.1:1984/", fenster=fenster, takt=takt, oeffne=g, schlafen=u.schlafen,
                           uhr=u, ausgabe=zeilen.append, kopf=kopf)
    return ok, stand, zeilen, u


def test_skript_alle_gut():
    g = _Go2rtc()
    ok, _, zeilen, u = _lauf(g)
    assert ok and u.t == 0.0
    assert len([z for z in zeilen if z.startswith("OK")]) == 9
    assert "http://127.0.0.1:1984/api/stream.mjpeg?src=hof01" in g.aufrufe
    assert "http://127.0.0.1:1984/api/stream.mp4?src=cam39" in g.aufrufe
    assert not [a for a in g.aufrufe if "frame.jpeg" in a or "stream.mjpeg?src=cam39" in a], "H.264 nie nach JPEG umwandeln lassen"
    assert not [z for z in zeilen if "geheim" in z], "producer-URL darf nie ausgegeben werden"


def test_skript_wackelig_gelingt_beim_wiederholen():
    g = _Go2rtc(fehl={"hochregal03": 2, "elektrolager02": 4, "cam39": 1})
    ok, _, zeilen, u = _lauf(g)
    assert ok
    assert 0 < u.t <= 30.0
    assert "Runde 5" in [z for z in zeilen if "elektrolager02" in z][0]


def test_skript_nie_erfolgreich_scheitert_nach_fenster():
    g = _Go2rtc(fehl={"hof01": -1})
    ok, stand, zeilen, u = _lauf(g)
    assert not ok
    assert u.t <= 30.0 and u.t >= 27.0
    assert [z for z in zeilen if z.startswith("FEHLT") and "hof01" in z]
    assert len([a for a in g.aufrufe if "src=hof01" in a]) >= 9   # im Takt wiederholt


def test_skript_ohne_zuschauer_nur_url_zaehlt_nicht():
    """Umkehrprobe: konfigurierte Quelle ohne Verbindung ({"url"} allein) ist KEIN Erfolg."""
    g = _Go2rtc(nur_url=("hochregal02",))
    ok, stand, _, _ = _lauf(g, fenster=6.0)
    assert not ok and stand["hochregal02"] == "kein verbundener producer"


def test_skript_verbunden_zaehlt_richtig():
    sk = _skript()
    assert sk.verbunden({"producers": [{"url": "x"}]}) == 0
    assert sk.verbunden({"producers": [{"url": "x", "medias": []}]}) == 1
    assert sk.verbunden(None) == 0


def test_skript_anmeldung_wird_mitgeschickt_nie_ausgegeben():
    sk = _skript()
    kopf = sk.basic_kopf("epk_api", "Sehr-Geheim-1")
    g = _Go2rtc()
    ok, _, zeilen, _ = _lauf(g, kopf=kopf)
    assert ok and g.koepfe and all(k == kopf for k in g.koepfe)
    assert not [z for z in zeilen if "Sehr-Geheim" in z or kopf["Authorization"] in z]
    assert sk.basic_kopf("", "") == {}


class _Api(object):
    """Attrappe der go2rtc-API mit Anmeldung: richtiges Paar -> 200, sonst 401."""

    def __init__(self, gut, offen=False, platzhalter_gilt=False, kaputt=False):
        self.gut, self.offen, self.platzhalter_gilt, self.kaputt = gut, offen, platzhalter_gilt, kaputt

    def __call__(self, url, timeout, kopf=None):
        import base64
        import urllib.error
        a = (kopf or {}).get("Authorization", "")
        klar = base64.b64decode(a[6:]).decode() if a.startswith("Basic ") else ""
        if self.offen or (a == self.gut and not self.kaputt) or (self.platzhalter_gilt and klar.startswith("${")):
            return _Antwort(b"{}")
        raise urllib.error.HTTPError(url, 401, "Unauthorized", {}, None)


def test_skript_anmeldepruefung():
    sk = _skript()
    kopf = sk.basic_kopf("u", "p")
    gut = kopf["Authorization"]
    assert sk.anmeldung_pruefen("http://lan:1984", kopf, oeffne=_Api(gut)) == []
    assert any("wirkt NICHT" in x for x in sk.anmeldung_pruefen("http://lan:1984", kopf, oeffne=_Api(gut, offen=True)))
    assert any("Platzhaltern" in x for x in sk.anmeldung_pruefen("http://lan:1984", kopf, oeffne=_Api(gut, platzhalter_gilt=True)))
    assert any("statt 200" in x for x in sk.anmeldung_pruefen("http://lan:1984", kopf, oeffne=_Api(gut, kaputt=True)))
    assert any("nicht gesetzt" in x for x in sk.anmeldung_pruefen("http://lan:1984", {}, oeffne=_Api(gut)))
    assert sk.ist_localhost("http://127.0.0.1:1984") and not sk.ist_localhost("http://lan:1984")


def test_skript_exitcodes(monkeypatch):
    sk = _skript()
    monkeypatch.delenv("QNAP_LAN_IP", raising=False)
    monkeypatch.setattr(sk, "pruefen", lambda basis, fenster, takt, kopf=None: (True, {}))
    assert sk.main(["--nur-streams"]) == 0
    assert sk.main([]) == 1, "localhost ohne --nur-streams: Anmeldung ungeprueft -> Exit 1"
    monkeypatch.setattr(sk, "anmeldung_pruefen", lambda basis, kopf: [])
    assert sk.main(["http://lan:1984"]) == 0
    monkeypatch.setattr(sk, "anmeldung_pruefen", lambda basis, kopf: ["go2rtc-API antwortet ohne Anmeldung"])
    assert sk.main(["http://lan:1984"]) == 1, "Anmeldung wirkt nicht -> Exit 1"
    monkeypatch.setenv("QNAP_LAN_IP", "lan")
    assert sk.standard_url() == "http://lan:1984"
    monkeypatch.setattr(sk, "anmeldung_pruefen", lambda basis, kopf: [])
    monkeypatch.setattr(sk, "pruefen", lambda basis, fenster, takt, kopf=None: (False, {}))
    assert sk.main(["--fenster", "5"]) == 1
    assert sk.main(["--unbekannt"]) == 2
