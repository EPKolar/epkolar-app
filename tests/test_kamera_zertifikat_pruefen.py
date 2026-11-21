# -*- coding: utf-8 -*-
"""Riegel 21.11.2026: Entscheidung von scripts/kamera_zertifikat_pruefen.py (Abnahme oeffentliches Zertifikat) an
erfundenen getpeercert()-Befunden - ohne Netz. Gruen NUR bei: Pruefung mit Systemvertrauen ok UND Aussteller nicht
"Caddy Local Authority" UND /gesund 200 "ok" mit CORS fuer https://epkolar.github.io."""
import importlib.util
import os

import pytest

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_spec = importlib.util.spec_from_file_location("kamera_zertifikat_pruefen",
                                               os.path.join(WURZEL, "scripts", "kamera_zertifikat_pruefen.py"))
KZ = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(KZ)

LE = {"issuer": ((("countryName", "US"),), (("organizationName", "Let's Encrypt"),), (("commonName", "E6"),)),
      "subject": ((("commonName", "kameras.ep-kolar.at"),),),
      "subjectAltName": (("DNS", "kameras.ep-kolar.at"),), "notAfter": "Feb 19 10:00:00 2027 GMT"}
CADDY = {"issuer": ((("organizationName", "Caddy Local Authority"),),
                    (("commonName", "Caddy Local Authority - ECC Intermediate"),)),
         "subject": ((("commonName", "kameras.ep-kolar.at"),),), "notAfter": "Nov 22 10:00:00 2026 GMT"}


def _befund(**k):
    b = {"verify_ok": True, "verify_fehler": "", "cert": LE, "gesund_status": 200, "gesund_text": "ok",
         "cors": "https://epkolar.github.io"}
    b.update(k)
    return b


def test_oeffentliche_ca_gruen():
    assert KZ.entscheide(_befund()) == (True, [])
    assert KZ.ist_lets_encrypt(LE)


def test_andere_oeffentliche_ca_gruen_aber_kein_le():
    c = dict(LE, issuer=((("organizationName", "Sectigo Limited"),),))
    assert KZ.entscheide(_befund(cert=c))[0] is True
    assert not KZ.ist_lets_encrypt(c)


def test_caddy_local_authority_rot():
    ok, g = KZ.entscheide(_befund(cert=CADDY))
    assert ok is False and any("Caddy Local Authority" in x for x in g)


def test_pruefung_fehlgeschlagen_rot():
    ok, g = KZ.entscheide(_befund(verify_ok=False, verify_fehler="unable to get local issuer certificate", cert=None,
                                  gesund_status=None, gesund_text=None, cors=None))
    assert ok is False and any("Systemvertrauen" in x for x in g)


@pytest.mark.parametrize("k,v,erwartet", [
    ("gesund_text", "nicht ok", "/gesund"),
    ("gesund_status", 404, "/gesund"),
    ("cors", None, "CORS"),
    ("cors", "*", "CORS"),
])
def test_gesund_und_cors_rot(k, v, erwartet):
    ok, g = KZ.entscheide(_befund(**{k: v}))
    assert ok is False and any(erwartet in x for x in g)


def test_skript_nutzt_systemvertrauen():
    """Kein eigenes Stammzertifikat, keine abgeschaltete Pruefung."""
    q = open(os.path.join(WURZEL, "scripts", "kamera_zertifikat_pruefen.py"), encoding="utf-8").read()
    assert "ssl.create_default_context()" in q
    for verboten in ("load_verify_locations", "CERT_NONE", "check_hostname = False", "_create_unverified_context", "cafile"):
        assert verboten not in q, verboten
