# Riegel (20.11.2026): die image-freie Compose fuer die QNAP (tools/kamera-proxy-auth/qnap/qnap-gateway-inline.compose.yml)
# traegt verify.mjs, token.mjs und die Caddyfile als base64. Die eingebetteten Kopien duerfen NIE still von den Repo-Dateien
# abweichen (wie der vektoren-Kreuztest fuer Edge <-> Pruefer). Vergleich gegen den Inhalt mit LF-Zeilenenden (= Git-Blob;
# die Windows-Arbeitskopie hat CRLF). Neu erzeugen: python tools/kamera-proxy-auth/qnap/inline_bauen.py
import base64
import io
import os
import re

import pytest

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUTH = os.path.join(WURZEL, "tools", "kamera-proxy-auth")
Q = os.path.join(AUTH, "qnap")
INLINE = os.path.join(Q, "qnap-gateway-inline.compose.yml")

BLOBS = {"KA_VERIFY_B64": os.path.join(AUTH, "verify.mjs"),
         "KA_TOKEN_B64": os.path.join(AUTH, "token.mjs"),
         "CADDYFILE_B64": os.path.join(Q, "Caddyfile")}


def _lf(pfad):
    return io.open(pfad, encoding="utf-8", newline="").read().replace("\r\n", "\n")


def _blobs(text):
    return dict(re.findall(r"^      - ([A-Z_]+_B64)=([A-Za-z0-9+/=]+)$", text, re.M))


def pruefe_blobs(text):
    """-> Liste der Abweichungen (leer = jede Kopie dekodiert Zeichen fuer Zeichen zur Repo-Datei)."""
    b = []
    gefunden = _blobs(text)
    for name, pfad in BLOBS.items():
        if name not in gefunden:
            b.append("Blob fehlt: " + name)
            continue
        try:
            inhalt = base64.b64decode(gefunden[name], validate=True).decode("utf-8")
        except Exception as e:  # kaputtes base64 / kein UTF-8
            b.append("Blob unlesbar: %s (%s)" % (name, e))
            continue
        if inhalt != _lf(pfad):
            b.append("Blob weicht ab: " + name)
    return b


def pruefe_inline(text):
    b = pruefe_blobs(text)
    c = "\n".join(l for l in text.split("\n") if not l.strip().startswith("#"))
    if re.search(r"^\s*build:", c, re.M):
        b.append("build statt Image")
    if "image: node:22.11.0-alpine3.20" not in c:
        b.append("kamera-auth-Image nicht gepinnt")
    if "image: caddy:2.8.4-alpine" not in c:
        b.append("caddy-Image nicht gepinnt")
    if c.count("cap_drop: [ALL]") != 2 or c.count('security_opt: ["no-new-privileges:true"]') != 2:
        b.append("cap_drop/no-new-privileges nicht an beiden Diensten")
    if "    user: node\n" not in c:
        b.append("kamera-auth nicht als node")
    if "depends_on: [kamera-auth]" not in c:
        b.append("depends_on fehlt")
    if not re.search(r"KAMERA_TOKEN_SECRET=\$\{KAMERA_TOKEN_SECRET:\?", c):
        b.append("Secret nicht Pflicht aus der .env")
    if '"${QNAP_LAN_IP:?QNAP_LAN_IP fehlt}:${GATEWAY_PORT:-8443}:${GATEWAY_PORT:-8443}"' not in c:
        b.append("Port nicht konfigurierbar (Standard 8443)")
    ka = c.split("  kamera-auth:")[1].split("  caddy:")[0]
    if "ports:" in ka:
        b.append("kamera-auth veroeffentlicht")
    if [x for x in re.findall(r"\b\d{1,3}(?:\.\d{1,3}){3}\b", text) if x not in ("0.0.0.0", "127.0.0.1")]:
        b.append("IP-Adresse")
    # die Startbefehle dekodieren genau diese Blobs ($$ = compose-Escape fuer ein $)
    for name in BLOBS:
        if '\\"$$%s\\" | base64 -d' % name not in c:
            b.append("Start dekodiert nicht " + name)
    return b


def _inline():
    return io.open(INLINE, encoding="utf-8").read()


def test_inline_blobs_gleich_repo():
    assert pruefe_blobs(_inline()) == []


def test_inline_sauber():
    assert pruefe_inline(_inline()) == []


def test_inline_ist_aktuell_erzeugt():
    """Die Datei ist genau das, was inline_bauen.py heute erzeugt (kein Handeingriff)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("inline_bauen", os.path.join(Q, "inline_bauen.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    assert m.bauen() == _inline().replace("\r\n", "\n")


def _ein_zeichen_anders(text, name):
    roh = _lf(BLOBS[name])
    i = roh.index("export") if "export" in roh else 10
    falsch = roh[:i] + ("X" if roh[i] != "X" else "Y") + roh[i + 1:]
    neu = base64.b64encode(falsch.encode("utf-8")).decode("ascii")
    return text.replace(name + "=" + _blobs(text)[name], name + "=" + neu)


# Mutationsproben: der Riegel muss jede Abweichung als rot melden
@pytest.mark.parametrize("name", sorted(BLOBS))
def test_umkehrprobe_ein_zeichen(name):
    assert any(name in x and "weicht ab" in x for x in pruefe_blobs(_ein_zeichen_anders(_inline(), name)))


@pytest.mark.parametrize("name", sorted(BLOBS))
def test_umkehrprobe_blob_fehlt(name):
    t = _inline()
    t = t.replace("      - " + name + "=" + _blobs(t)[name] + "\n", "")
    assert any("Blob fehlt: " + name == x for x in pruefe_blobs(t))


def test_umkehrprobe_zeilenende_crlf():
    t = _inline()
    roh = _lf(BLOBS["KA_VERIFY_B64"]).replace("\n", "\r\n")
    t = t.replace("KA_VERIFY_B64=" + _blobs(t)["KA_VERIFY_B64"], "KA_VERIFY_B64=" + base64.b64encode(roh.encode()).decode())
    assert any("weicht ab" in x for x in pruefe_blobs(t))


@pytest.mark.parametrize("alt,neu,erwartet", [
    ("    user: node\n", "", "als node"),
    ("image: caddy:2.8.4-alpine", "image: caddy:latest", "caddy-Image"),
    ("${GATEWAY_PORT:-8443}:${GATEWAY_PORT:-8443}", "443:443", "Port"),
    ("    depends_on: [kamera-auth]\n", "", "depends_on"),
    ("${KAMERA_TOKEN_SECRET:?", "${KAMERA_TOKEN_SECRET:-", "Secret"),
])
def test_umkehrprobe_inline(alt, neu, erwartet):
    t = _inline()
    assert alt in t
    assert any(erwartet in x for x in pruefe_inline(t.replace(alt, neu, 1)))
