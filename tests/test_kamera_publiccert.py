# -*- coding: utf-8 -*-
r"""Riegel 21.11.2026: Kamera-Gateway, Variante OEFFENTLICHES ZERTIFIKAT (https://kameras.ep-kolar.at:8443).

Dateien unter tools/kamera-proxy-auth/qnap/: Caddyfile.publiccert, acme_start.sh, caddy_start.sh und die erzeugte
qnap-gateway-publiccert-inline.compose.yml (qnap/inline_bauen.py). Statische Pruefung mit Umkehrproben:
  - Caddyfile.publiccert: tls aus /certs (kein tls internal), Site {$KAMERA_HOST}:{$GATEWAY_PORT}, ab "Protokoll OHNE Tokens"
    Zeichen fuer Zeichen gleich qnap/Caddyfile, und jede Sicherheitsregel von pruefe_caddy (forward_auth vor rewrite,
    Kopf-Ueberschreibung, /gesund, 404 zuletzt, Protokoll ohne Token, CORS nur epkolar.github.io) gilt weiter
  - Compose: Dienste kamera-auth + acme + caddy; DEDYN_TOKEN nur als Pflicht-Umgebung im acme-Dienst; kein Docker-Socket,
    kein Port am acme-Dienst; caddy liest /certs nur; alle Blobs = Repo-Dateien; Datei = heutige Generator-Ausgabe
  - acme_start.sh / caddy_start.sh: DNS-Alias-Modus (beide Arten), install-cert-Pfade = tls-Pfade, Neustart ueber die Marke
    /certs/.erneuert statt Docker-Socket oder admin-API; Shell-Syntax (sh -n)
"""
import base64
import importlib.util
import io
import os
import re
import shutil
import subprocess

import pytest

from test_kamera_qnap_gateway import pruefe_caddy

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUTH = os.path.join(WURZEL, "tools", "kamera-proxy-auth")
Q = os.path.join(AUTH, "qnap")
CADDY_PUB = os.path.join(Q, "Caddyfile.publiccert")
INLINE_PUB = os.path.join(Q, "qnap-gateway-publiccert-inline.compose.yml")
ACME_SH = os.path.join(Q, "acme_start.sh")
CADDY_SH = os.path.join(Q, "caddy_start.sh")
MARKE = "\t# ── Protokoll OHNE Tokens"
TLS_ZEILE = "\ttls /certs/kameras.pem /certs/kameras-key.pem"

BLOBS = {"KA_VERIFY_B64": os.path.join(AUTH, "verify.mjs"),
         "KA_TOKEN_B64": os.path.join(AUTH, "token.mjs"),
         "CADDYFILE_B64": CADDY_PUB,
         "CADDY_START_B64": CADDY_SH,
         "ACME_START_B64": ACME_SH}

# pruefe_caddy ist fuer die tls-internal-Datei geschrieben; GENAU diese vier Meldungen sind hier gewollt anders.
GEWOLLT_ANDERS = {"tls internal fehlt", "default_sni fehlt", "Zertifikat-Datei aktiv (nur auskommentiert erlaubt)",
                  "Site ohne {$QNAP_LAN_IP}:{$GATEWAY_PORT}"}


def _lf(pfad):
    return io.open(pfad, encoding="utf-8", newline="").read().replace("\r\n", "\n")


def _ohne_kommentare(text):
    return "\n".join(l for l in text.split("\n") if not l.strip().startswith("#"))


# ── Caddyfile.publiccert ────────────────────────────────────────────────────
def pruefe_caddy_public(text):
    b = [x for x in pruefe_caddy(text) if x not in GEWOLLT_ANDERS]
    c = _ohne_kommentare(text)
    if re.search(r"^\s*tls internal\b", c, re.M):
        b.append("tls internal in der oeffentlichen Variante")
    if TLS_ZEILE not in c.split("\n"):
        b.append("tls-Dateipfade fehlen")
    sites = re.findall(r"^(\S[^\n]*) \{$", c, re.M)
    if sites != ["https://{$KAMERA_HOST}:{$GATEWAY_PORT}"]:
        b.append("Site != https://{$KAMERA_HOST}:{$GATEWAY_PORT}: %s" % sites)
    if not re.search(r"^\tadmin off$", c, re.M):
        b.append("admin nicht aus")
    if not re.search(r"^\tdefault_sni \{\$KAMERA_HOST\}$", c, re.M):
        b.append("default_sni {$KAMERA_HOST} fehlt")
    quelle = _lf(os.path.join(Q, "Caddyfile"))
    if MARKE not in text or text[text.index(MARKE):] != quelle[quelle.index(MARKE):]:
        b.append("Routen weichen von qnap/Caddyfile ab")
    return b


def test_caddy_public_sauber():
    assert pruefe_caddy_public(_lf(CADDY_PUB)) == []


def test_caddy_public_meldet_nur_gewollte_abweichungen():
    """Gegenprobe: pruefe_caddy meldet an der oeffentlichen Datei genau die vier gewollten Unterschiede (nicht 0 = blind)."""
    assert set(pruefe_caddy(_lf(CADDY_PUB))) == GEWOLLT_ANDERS


def _mut(text, alt, neu):
    assert alt in text, alt
    return text.replace(alt, neu, 1)


@pytest.mark.parametrize("alt,neu,erwartet", [
    (TLS_ZEILE + "\n", "\ttls internal\n", "tls internal"),
    (TLS_ZEILE + "\n", "", "tls-Dateipfade"),
    ("\tadmin off\n", "", "admin"),
    ("https://{$KAMERA_HOST}:{$GATEWAY_PORT} {", "https://{$QNAP_LAN_IP}:{$GATEWAY_PORT} {", "Site"),
    ("\thandle {\n\t\trespond 404\n\t}", "", "Catch-all"),
    ("\t\t\t\theader_up -X-Original-URI\n", "", "Kopf-Regel"),
    ("\t\t\t\t\tdelete token\n", "", "Token im Protokoll"),
    ("Access-Control-Allow-Origin \"https://epkolar.github.io\"", "Access-Control-Allow-Origin \"*\"", "CORS fremd"),
    ("\trespond \"ok\" 200", "\trespond \"OK\" 200", "Routen weichen"),
    ("{$KAMERA_HOST}:{$GATEWAY_PORT} {", "{$KAMERA_HOST}:{$GATEWAY_PORT} {\n}\nhttps://" + ".".join(("10", "0", "0", "9")) + " {", "IP-Adresse"),
])
def test_umkehrprobe_caddy_public(alt, neu, erwartet):
    b = pruefe_caddy_public(_mut(_lf(CADDY_PUB), alt, neu))
    assert any(erwartet in x for x in b), b


def test_umkehrprobe_forward_auth_entfernt():
    s = _lf(CADDY_PUB)
    i = s.index("handle @mjpeg {")
    j = s.index("forward_auth", i)
    k = s.index("}", j)
    assert any("forward_auth nicht vor" in x for x in pruefe_caddy_public(s[:j] + s[k + 1:]))


# ── Compose (image-frei, erzeugt) ───────────────────────────────────────────
def _blobs(text):
    return dict(re.findall(r"^      - ([A-Z_]+_B64)=([A-Za-z0-9+/=]+)$", text, re.M))


def _dienste(c):
    return dict((m.group(1), m.group(2)) for m in re.finditer(r"^  ([a-z0-9_-]+):\n((?:    .*\n|\n)*)", c + "\n", re.M))


def pruefe_compose_public(text):
    b = []
    for name, pfad in BLOBS.items():
        roh = _blobs(text).get(name)
        if roh is None:
            b.append("Blob fehlt: " + name)
            continue
        try:
            inhalt = base64.b64decode(roh, validate=True).decode("utf-8")
        except Exception as e:
            b.append("Blob unlesbar: %s (%s)" % (name, e))
            continue
        if inhalt != _lf(pfad):
            b.append("Blob weicht ab: " + name)
    c = _ohne_kommentare(text)
    if [x for x in re.findall(r"\b\d{1,3}(?:\.\d{1,3}){3}\b", text) if x not in ("0.0.0.0", "127.0.0.1")]:
        b.append("IP-Adresse")
    if re.search(r"^\s*build:", c, re.M):
        b.append("build statt Image")
    d = _dienste(c)
    if sorted(d) != ["acme", "caddy", "kamera-auth"]:
        b.append("Dienste != acme + caddy + kamera-auth: %s" % sorted(d))
    ac, ca, ka = d.get("acme", ""), d.get("caddy", ""), d.get("kamera-auth", "")
    if re.search(r"docker\.sock|/var/run/docker|privileged|network_mode|pid:", c):
        b.append("Docker-Socket/privileged/Host-Netz")
    if "ports:" in ac or "expose:" in ac:
        b.append("acme mit Port")
    if "ports:" in ka:
        b.append("kamera-auth veroeffentlicht")
    if not re.search(r"^    image: neilpang/acme\.sh:\d+\.\d+\.\d+$", ac, re.M):
        b.append("acme-Image nicht fest gepinnt")
    if "image: caddy:2.8.4-alpine" not in ca or "image: node:22.11.0-alpine3.20" not in ka:
        b.append("caddy/node-Image nicht gepinnt")
    # DEDYN_TOKEN: genau einmal, Pflicht aus der .env, nur im acme-Dienst
    vork = re.findall(r"DEDYN_TOKEN[^\n]*", c)
    if len(vork) != 1 or not re.search(r"^      - DEDYN_TOKEN=\$\{DEDYN_TOKEN:\?[^}]*\}$", ac, re.M):
        b.append("DEDYN_TOKEN nicht genau einmal als Pflicht-Umgebung im acme-Dienst: %s" % vork)
    for n in ("ACME_EMAIL", "KAMERA_HOST", "ALIAS_ZONE"):
        if not re.search(r"^      - %s=\$\{%s:\?" % (n, n), ac, re.M):
            b.append(n + " nicht Pflicht im acme-Dienst")
    if not re.search(r"^      - KAMERA_HOST=\$\{KAMERA_HOST:\?", ca, re.M):
        b.append("KAMERA_HOST nicht Pflicht im caddy-Dienst")
    if not re.search(r"KAMERA_TOKEN_SECRET=\$\{KAMERA_TOKEN_SECRET:\?", ka):
        b.append("KAMERA_TOKEN_SECRET nicht Pflicht")
    if "      - kamera_zertifikate:/certs:ro" not in ca:
        b.append("caddy liest /certs nicht nur lesend")
    if "      - kamera_zertifikate:/certs " not in ac and not ac.rstrip().endswith("kamera_zertifikate:/certs"):
        b.append("acme schreibt nicht nach /certs")
    if not re.search(r"      acme:\n        condition: service_healthy", ca):
        b.append("caddy wartet nicht auf das Zertifikat")
    if '"${QNAP_LAN_IP:?QNAP_LAN_IP fehlt}:${GATEWAY_PORT:-8443}:${GATEWAY_PORT:-8443}"' not in ca:
        b.append("Caddy-Port nicht <QNAP_LAN_IP>:<GATEWAY_PORT>")
    if c.count("cap_drop: [ALL]") != 3 or c.count('security_opt: ["no-new-privileges:true"]') != 3:
        b.append("cap_drop/no-new-privileges nicht an allen drei Diensten")
    for dienst, namen in (("kamera-auth", ("KA_TOKEN_B64", "KA_VERIFY_B64")), ("acme", ("ACME_START_B64",)),
                          ("caddy", ("CADDY_START_B64",))):
        for n in namen:
            if '\\"$$%s\\" | base64 -d' % n not in d.get(dienst, ""):
                b.append("Start dekodiert nicht " + n)
    return b


def _inline():
    return io.open(INLINE_PUB, encoding="utf-8").read().replace("\r\n", "\n")


def test_compose_public_sauber():
    assert pruefe_compose_public(_inline()) == []


def test_compose_public_ist_aktuell_erzeugt():
    spec = importlib.util.spec_from_file_location("inline_bauen", os.path.join(Q, "inline_bauen.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    assert m.bauen_public() == _inline()


@pytest.mark.parametrize("alt,neu,erwartet", [
    ("    volumes:\n      - acme_daten:/acme.sh", "    volumes:\n      - /var/run/docker.sock:/var/run/docker.sock\n      - acme_daten:/acme.sh", "Docker-Socket"),
    ("${DEDYN_TOKEN:?", "${DEDYN_TOKEN:-", "DEDYN_TOKEN"),
    ("      - KAMERA_HOST=${KAMERA_HOST:?KAMERA_HOST fehlt (kameras.ep-kolar.at)}\n      - GATEWAY_PORT",
     "      - KAMERA_HOST=${KAMERA_HOST:?KAMERA_HOST fehlt (kameras.ep-kolar.at)}\n      - DEDYN_TOKEN=${DEDYN_TOKEN:?x}\n      - GATEWAY_PORT", "DEDYN_TOKEN"),
    ("${ACME_EMAIL:?", "${ACME_EMAIL:-", "ACME_EMAIL"),
    ("      - kamera_zertifikate:/certs:ro", "      - kamera_zertifikate:/certs", "nur lesend"),
    ("    image: neilpang/acme.sh:3.1.5\n", "    image: neilpang/acme.sh:latest\n", "acme-Image"),
    ("    image: neilpang/acme.sh:3.1.5\n", "    image: neilpang/acme.sh:3.1.5\n    ports:\n      - \"80:80\"\n", "acme mit Port"),
    ("        condition: service_healthy", "        condition: service_started", "wartet nicht"),
    ("    cap_drop: [ALL]\n    security_opt: [\"no-new-privileges:true\"]\n    command: [\"sh\", \"-c\", \"printf %s \\\"$$ACME",
     "    command: [\"sh\", \"-c\", \"printf %s \\\"$$ACME", "cap_drop"),
])
def test_umkehrprobe_compose_public(alt, neu, erwartet):
    t = _inline()
    b = pruefe_compose_public(_mut(t, alt, neu))
    assert any(erwartet in x for x in b), b


@pytest.mark.parametrize("name", sorted(BLOBS))
def test_umkehrprobe_blob_ein_zeichen(name):
    t = _inline()
    roh = _lf(BLOBS[name])
    i = len(roh) // 2
    falsch = roh[:i] + ("X" if roh[i] != "X" else "Y") + roh[i + 1:]
    t = t.replace(name + "=" + _blobs(t)[name], name + "=" + base64.b64encode(falsch.encode("utf-8")).decode("ascii"))
    assert any(name in x and "weicht ab" in x for x in pruefe_compose_public(t))


# ── Startskripte ────────────────────────────────────────────────────────────
def pruefe_acme_sh(text):
    b = []
    c = _ohne_kommentare(text)
    for pflicht in ("--dns dns_desec", "--server letsencrypt", "--install-cert", "--fullchain-file /certs/kameras.pem",
                    "--key-file /certs/kameras-key.pem", "--challenge-alias", "--domain-alias", "--reloadcmd",
                    "/certs/.erneuert", "acme.sh --cron ||"):
        if pflicht not in c:
            b.append("acme_start.sh ohne " + pflicht)
    if re.search(r"\bdocker\b|--debug|set -x", c):
        b.append("acme_start.sh: docker/--debug/set -x")
    # das Token nur pruefen (Pflicht), nie ausgeben oder als Argument uebergeben
    if [l for l in c.split("\n") if "DEDYN_TOKEN" in l and not l.startswith(': "${DEDYN_TOKEN:?')]:
        b.append("DEDYN_TOKEN ausserhalb der Pflichtpruefung")
    return b


def pruefe_caddy_sh(text):
    b = []
    c = _ohne_kommentare(text)
    if "/certs/.erneuert" not in c:
        b.append("caddy_start.sh beobachtet die Marke nicht")
    if "caddy run --config /cfg/Caddyfile --adapter caddyfile" not in c:
        b.append("caddy_start.sh startet Caddy nicht mit /cfg/Caddyfile")
    if re.search(r"caddy reload|admin|docker", c):
        b.append("caddy_start.sh: reload/admin/docker")
    if "exit 0" not in c:
        b.append("caddy_start.sh endet nicht nach der Erneuerung")
    return b


def test_startskripte_sauber():
    assert pruefe_acme_sh(_lf(ACME_SH)) == []
    assert pruefe_caddy_sh(_lf(CADDY_SH)) == []


def test_tls_pfade_gleich_install_cert():
    pfade = re.search(r"^\ttls (\S+) (\S+)$", _lf(CADDY_PUB), re.M).groups()
    a = _lf(ACME_SH)
    assert "--fullchain-file " + pfade[0] in a and "--key-file " + pfade[1] in a


@pytest.mark.parametrize("alt,neu,erwartet", [
    ("--key-file /certs/kameras-key.pem", "--key-file /certs/key.pem", "kameras-key.pem"),
    ('ALIAS_OPT="--challenge-alias"', 'ALIAS_OPT="--alias-x"', "--challenge-alias"),
    ("acme.sh --cron ||", "true ||", "acme.sh --cron"),
    ("acme.sh --set-default-ca", "echo \"$DEDYN_TOKEN\"\nacme.sh --set-default-ca", "DEDYN_TOKEN ausserhalb"),
])
def test_umkehrprobe_acme_sh(alt, neu, erwartet):
    assert any(erwartet in x for x in pruefe_acme_sh(_mut(_lf(ACME_SH), alt, neu)))


def test_umkehrprobe_caddy_sh():
    assert any("reload" in x for x in pruefe_caddy_sh(_lf(CADDY_SH) + "\ncaddy reload --force\n"))


@pytest.mark.parametrize("pfad", [ACME_SH, CADDY_SH])
def test_shell_syntax(pfad, tmp_path):
    sh = shutil.which("sh") or shutil.which("bash")
    if not sh:
        pytest.skip("keine Shell")
    f = tmp_path / "s.sh"
    f.write_bytes(_lf(pfad).encode("utf-8"))
    r = subprocess.run([sh, "-n", str(f)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
