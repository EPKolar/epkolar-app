# -*- coding: utf-8 -*-
"""Riegel 21.11.2026 (gemessen Chat-Claude, Chrome-DevTools): Die App-eigene CSP (meta http-equiv in index.html)
blockte den Abruf aufs Kamera-Gateway VOR dem Netz (securitypolicyviolation, directive connect-src,
blockedURI https://<gateway>:8443/gesund) - LNA, Zertifikat, CORS und Gateway waren gruen.

Die CSP ist statisch (ein per Skript nachgeschobenes CSP-Meta kann nur weiter EINSCHRAENKEN, nie erweitern),
deshalb steht der Gateway-Origin fest darin. Er muss dem Supabase-Secret KAMERA_GATEWAY_BASE entsprechen
(https://<NAS>:8443, ohne Pfad). Wechselt die Adresse: Secret UND diese drei Direktiven zusammen aendern.

  connect-src  Gesundheitsabruf /gesund + WHEP-POST
  img-src      Einzelbild (snapshot.jpg) + MJPEG-Bild-Element
  media-src    HLS-Rueckfall im Video-Element (vorher ueber default-src gesperrt)
"""
import io
import os
import re

import pytest

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GATEWAY = "https://192.168.33.95:8443"   # = KAMERA_GATEWAY_BASE (Supabase-Secret), nur Origin
DIREKTIVEN = ("connect-src", "img-src", "media-src")


def _html():
    return io.open(os.path.join(WURZEL, "index.html"), encoding="utf-8").read()


def _csp(html):
    m = re.search(r'<meta http-equiv="Content-Security-Policy" content="([^"]*)"', html)
    assert m, "CSP-Meta nicht gefunden"
    out = {}
    for teil in m.group(1).split(";"):
        w = teil.split()
        if w:
            out[w[0]] = w[1:]
    return out


def pruefe(html):
    c = _csp(html)
    fehler = []
    for d in DIREKTIVEN:
        if d not in c:
            fehler.append(d + " fehlt")
        elif GATEWAY not in c[d]:
            fehler.append(d + " ohne Gateway-Origin")
    # nur Origin, kein Pfad, kein Platzhalter-Host
    for d, werte in c.items():
        for w in werte:
            if w.startswith(GATEWAY) and w != GATEWAY:
                fehler.append(d + ": Gateway mit Pfad/Zusatz " + w)
            if w in ("https:", "*", "https://*", "https://*:8443"):
                fehler.append(d + ": zu weit offen " + w)
    # media-src darf nicht weniger erlauben als vorher die default-src fuer Medien
    for w in c.get("default-src", []):
        if "media-src" in c and w not in c["media-src"]:
            fehler.append("media-src ohne " + w + " aus default-src")
    return fehler


def test_gateway_in_csp():
    assert pruefe(_html()) == []


def test_ausgelieferte_quelle_bleibt_eng():
    c = _csp(_html())
    assert "'self'" in c["connect-src"] and "https://jiggujpruejkaomgxarp.supabase.co" in c["connect-src"]


@pytest.mark.parametrize("d", DIREKTIVEN)
def test_umkehrprobe_origin_entfernt(d):
    h = _html()
    i = h.index('<meta http-equiv="Content-Security-Policy"')
    j = h.index(">", i)
    meta = h[i:j]
    neu = re.sub(r"(" + re.escape(d) + r"[^;]*?) " + re.escape(GATEWAY), r"\1", meta, count=1)
    assert neu != meta
    assert any(d in x for x in pruefe(h[:i] + neu + h[j:]))


def test_umkehrprobe_zu_weit():
    h = _html().replace("connect-src 'self'", "connect-src https: 'self'", 1)
    assert any("zu weit" in x for x in pruefe(h))
