# -*- coding: utf-8 -*-
"""Riegel 1090 (Zusammenfuehrung Let's-Encrypt- + Mobotix-Zweig): BEIDE Gateway-Varianten melden Caddy bei go2rtc an.
Jede Caddyfile, die mit header_up Authorization "Basic {$GO2RTC_BASIC}" zu go2rtc weiterleitet, braucht in ihrer
Compose-Datei GO2RTC_BASIC als Pflicht-Umgebung im caddy-Dienst - sonst sendet Caddy eine leere Anmeldung und
go2rtc (api.username/password) antwortet 401: kein Live-Bild. Beim Merge fehlte das in der publiccert-Compose."""
import io
import os
import re

import pytest

Q = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools", "kamera-proxy-auth", "qnap")
PAARE = [("Caddyfile", "qnap-gateway-inline.compose.yml"),
         ("Caddyfile", "docker-compose.yml"),
         ("Caddyfile.publiccert", "qnap-gateway-publiccert-inline.compose.yml")]
PFLICHT = re.compile(r"^\s+- GO2RTC_BASIC=\$\{GO2RTC_BASIC:\?", re.M)


def _lies(n):
    return io.open(os.path.join(Q, n), encoding="utf-8").read()


def _caddy_dienst(compose):
    i = compose.index("\n  caddy:\n")
    m = re.search(r"\n  [a-z][a-z0-9_-]*:\n", compose[i + 3:])
    return compose[i:i + 3 + m.start()] if m else compose[i:]


def pruefe(caddyfile, compose):
    if 'header_up Authorization "Basic {$GO2RTC_BASIC}"' not in caddyfile:
        return ["Caddyfile ohne go2rtc-Anmeldung"]
    return [] if PFLICHT.search(_caddy_dienst(compose)) else ["caddy-Dienst ohne GO2RTC_BASIC"]


@pytest.mark.parametrize("caddy,compose", PAARE)
def test_go2rtc_basic_in_caddy_umgebung(caddy, compose):
    assert pruefe(_lies(caddy), _lies(compose)) == []


def test_umkehrprobe_ohne_env():
    c = _lies("qnap-gateway-publiccert-inline.compose.yml")
    kaputt = re.sub(r"^\s+- GO2RTC_BASIC=.*\n", "", c, flags=re.M)
    assert kaputt != c
    assert pruefe(_lies("Caddyfile.publiccert"), kaputt) == ["caddy-Dienst ohne GO2RTC_BASIC"]
