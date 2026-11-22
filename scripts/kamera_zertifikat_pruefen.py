# -*- coding: utf-8 -*-
r"""Abnahme Kamera-Gateway mit oeffentlichem Zertifikat (21.11.2026) - laeuft beim Inhaber auf einem Buero-PC.

    python scripts\kamera_zertifikat_pruefen.py [--host kameras.ep-kolar.at] [--port 8443] [--erwartet-ip <QNAP-LAN-IP>]

Prueft mit dem SYSTEM-Vertrauensspeicher (ssl.create_default_context, KEIN eigenes Stammzertifikat):
  1. TLS-Handschlag + Zertifikatspruefung (Name + Kette) gelingt
  2. Aussteller ist NICHT "Caddy Local Authority" (sonst waere es die tls-internal-Variante; die kann auf diesem PC
     nur deshalb gruen sein, weil das Caddy-Stammzertifikat hier installiert ist)
  3. GET /gesund mit Origin https://epkolar.github.io -> 200, Text "ok", Access-Control-Allow-Origin passt
     (= was der App-Abruf von epkolar.github.io braucht)
Rueckgabe 0 nur wenn 1-3 gruen, 1 wenn rot, 2 wenn die Selbstprobe scheitert (eichen(): vor jeder Messung muss
entscheide() erfundene Befunde - Caddy-Aussteller, Pruefung gescheitert, kein Zertifikat, /gesund falsch, CORS "*" -
ROT nennen und einen Let's-Encrypt-Befund GRUEN; sonst ist ein "GRUEN" von einem blinden Pruefer nicht zu
unterscheiden). Nur die Probe: --eichen. Zusaetzlich (nur Bericht, kein Ausschlag): DNS-Antwort des Systemresolvers und eines
oeffentlichen DoH-Resolvers (Cloudflare) - erwartet ist in beiden die QNAP-LAN-Adresse (ENV.md Schritte 3+4).
Abnahmekriterium wortgleich in tools/kamera-proxy-auth/qnap/ENV.md; das A55 (mit/ohne "Privates DNS") prueft ein Mensch.
"""
import argparse
import http.client
import json
import socket
import ssl
import sys
import urllib.request

ORIGIN_APP = "https://epkolar.github.io"
CADDY_LOKAL = "Caddy Local Authority"
DOH = "https://cloudflare-dns.com/dns-query"


def _name(rdn_folge):
    """getpeercert()-Feld (Tupel von RDN-Tupeln) -> dict."""
    out = {}
    for rdn in rdn_folge or ():
        for k, v in rdn:
            out[k] = v
    return out


def entscheide(befund):
    """befund: {"verify_ok": bool, "verify_fehler": str, "cert": getpeercert()-dict|None,
                "gesund_status": int|None, "gesund_text": str|None, "cors": str|None}
    -> (ok: bool, gruende: [str]) - gruende nennt jede rote Stelle."""
    g = []
    if not befund.get("verify_ok"):
        g.append("Zertifikatspruefung mit Systemvertrauen fehlgeschlagen: " + (befund.get("verify_fehler") or "?"))
    cert = befund.get("cert") or {}
    aus = _name(cert.get("issuer"))
    aus_text = " ".join(str(v) for v in aus.values())
    if not cert:
        g.append("kein Zertifikat gelesen")
    elif CADDY_LOKAL in aus_text:
        g.append("Aussteller ist " + CADDY_LOKAL + " (tls internal) - keine oeffentliche CA")
    if befund.get("gesund_status") != 200 or (befund.get("gesund_text") or "").strip() != "ok":
        g.append("/gesund nicht 200 'ok' (Status %s)" % befund.get("gesund_status"))
    if befund.get("gesund_status") == 200 and befund.get("cors") != ORIGIN_APP:
        g.append("CORS fuer %s fehlt (Access-Control-Allow-Origin: %s)" % (ORIGIN_APP, befund.get("cors")))
    return (not g), g


def ist_lets_encrypt(cert):
    return _name((cert or {}).get("issuer")).get("organizationName") == "Let's Encrypt"


def messen(host, port, timeout=10):
    befund = {"verify_ok": False, "verify_fehler": "", "cert": None, "kette": [],
              "gesund_status": None, "gesund_text": None, "cors": None}
    ctx = ssl.create_default_context()   # Systemvertrauen (Windows: Zertifikatspeicher ROOT/CA)
    try:
        with socket.create_connection((host, port), timeout=timeout) as roh:
            with ctx.wrap_socket(roh, server_hostname=host) as s:
                befund["verify_ok"] = True
                befund["cert"] = s.getpeercert()
                if hasattr(s, "get_verified_chain"):   # Python >= 3.13
                    try:
                        for c in s.get_verified_chain():
                            d = c.get_info() if hasattr(c, "get_info") else {}
                            befund["kette"].append(_name(d.get("subject")).get("commonName", "?"))
                    except Exception:
                        pass
    except ssl.SSLCertVerificationError as e:
        befund["verify_fehler"] = "%s (%s)" % (e.verify_message, e.reason)
    except (OSError, ssl.SSLError) as e:
        befund["verify_fehler"] = repr(e)
    if befund["verify_ok"]:
        try:
            k = http.client.HTTPSConnection(host, port, timeout=timeout, context=ctx)
            k.request("GET", "/gesund", headers={"Origin": ORIGIN_APP})
            r = k.getresponse()
            befund["gesund_status"] = r.status
            befund["gesund_text"] = r.read(64).decode("utf-8", "replace")
            befund["cors"] = r.getheader("Access-Control-Allow-Origin")
            k.close()
        except (OSError, http.client.HTTPException) as e:
            befund["gesund_text"] = repr(e)
    return befund


def dns_bericht(host, timeout=5):
    out = {}
    try:
        out["system"] = sorted({a[4][0] for a in socket.getaddrinfo(host, None, socket.AF_INET)})
    except OSError as e:
        out["system"] = "Fehler: %r" % (e,)
    try:
        req = urllib.request.Request(DOH + "?name=" + host + "&type=A", headers={"accept": "application/dns-json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            j = json.loads(r.read().decode("utf-8"))
        out["oeffentlich"] = [a["data"] for a in j.get("Answer", []) if a.get("type") == 1]
    except Exception as e:  # Netz sperrt externes DNS/DoH -> nur berichten
        out["oeffentlich"] = "nicht erreichbar: %r" % (e,)
    return out


_LE_PROBE = {"issuer": ((("organizationName", "Let's Encrypt"),), (("commonName", "E6"),)),
             "subject": ((("commonName", "kameras.ep-kolar.at"),),)}
_CADDY_PROBE = {"issuer": ((("organizationName", CADDY_LOKAL),), (("commonName", CADDY_LOKAL + " - ECC Intermediate"),)),
                "subject": ((("commonName", "kameras.ep-kolar.at"),),)}


def eichen(_entscheide=entscheide):
    """Koeder (muessen ROT werden, mit dem passenden Grund) und eine Gegenprobe (muss GRUEN bleiben) - ohne Netz.
    entscheide() ist beim Laden gebunden: geprueft wird die echte Entscheidung. Rueckgabe: Liste schiefer Proben."""
    schief = []
    gesund = {"verify_ok": True, "verify_fehler": "", "cert": _LE_PROBE, "gesund_status": 200, "gesund_text": "ok",
              "cors": ORIGIN_APP}
    ok, g = _entscheide(dict(gesund))
    if not ok or g:
        schief.append("Gegenprobe Let's Encrypt + /gesund ok wird ROT gemeldet: %s" % g)
    koeder = (
        ("Caddy-Aussteller (tls internal)", {"cert": _CADDY_PROBE}, CADDY_LOKAL),
        ("Pruefung mit Systemvertrauen gescheitert", {"verify_ok": False, "verify_fehler": "probe"}, "Systemvertrauen"),
        ("kein Zertifikat gelesen", {"cert": None}, "kein Zertifikat"),
        ("/gesund 404", {"gesund_status": 404}, "/gesund"),
        ("/gesund Text falsch", {"gesund_text": "nicht ok"}, "/gesund"),
        ("CORS *", {"cors": "*"}, "CORS"),
        ("CORS fehlt", {"cors": None}, "CORS"),
    )
    for name, aenderung, grund in koeder:
        b = dict(gesund)
        b.update(aenderung)
        ok, g = _entscheide(b)
        if ok or not any(grund in x for x in g):
            schief.append("Koeder '%s' nicht erkannt (ok=%s, Gruende=%s)" % (name, ok, g))
    return schief


def main(argv=None):
    p = argparse.ArgumentParser(description="Abnahme Kamera-Gateway (oeffentliches Zertifikat)")
    p.add_argument("--host", default="kameras.ep-kolar.at")
    p.add_argument("--port", type=int, default=8443)
    p.add_argument("--erwartet-ip", default="", help="QNAP-LAN-Adresse (nur fuer den DNS-Bericht)")
    p.add_argument("--eichen", action="store_true", help="nur die Selbstprobe (ohne Netz)")
    a = p.parse_args(argv)

    schief = eichen()
    if schief:
        for x in schief:
            print("SELBSTPROBE ROT:", x)
        print("NICHT GEMESSEN - die Entscheidung erkennt ein falsches Zertifikat nicht mehr")
        return 2
    if a.eichen:
        print("SELBSTPROBE GRUEN - 7 Koeder rot, Gegenprobe gruen")
        return 0

    d = dns_bericht(a.host)
    print("DNS Systemresolver :", d["system"])
    print("DNS oeffentlich DoH:", d["oeffentlich"], "(nur Bericht)")
    if a.erwartet_ip:
        for k in ("system", "oeffentlich"):
            if isinstance(d[k], list):
                print("  %-11s %s" % (k, "passt" if d[k] == [a.erwartet_ip] else "WEICHT AB von " + a.erwartet_ip))

    b = messen(a.host, a.port)
    c = b["cert"] or {}
    print("Aussteller :", _name(c.get("issuer")))
    print("Inhaber    :", _name(c.get("subject")))
    print("SAN        :", c.get("subjectAltName"))
    print("gueltig bis:", c.get("notAfter"))
    print("Kette      :", " <- ".join(b["kette"]) if b["kette"] else "(erst ab Python 3.13 lesbar)")
    print("/gesund    :", b["gesund_status"], repr(b["gesund_text"]), "CORS:", b["cors"])
    ok, gruende = entscheide(b)
    if ok and not ist_lets_encrypt(c):
        print("HINWEIS: oeffentliche CA, aber nicht Let's Encrypt - Aussteller pruefen")
    for x in gruende:
        print("ROT:", x)
    print("GRUEN - oeffentliches Zertifikat, /gesund ok" if ok else "ROT - Abnahme nicht erfuellt")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
