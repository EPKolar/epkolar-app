"""v3.9.1120 - Startdaten ohne Personendaten (Platzhalter).

Die fest eingebauten Startdaten (INIT_USERS = Benutzer-Startzustand vor dem
Server-Laden, MONT = Mitarbeiter-Startzustand + Seed einer WIRKLICH leeren
workers-Tabelle) trugen echte Namen, Firmen-E-Mails, Geburtsdaten,
Fuehrerscheinnummern und Eintrittsdaten. Seit 1120 stehen dort nur
Platzhalter. Struktur, ids (u1-u8, w1-w8), Verknuepfung monteurId, Rollen,
Fuehrerscheinklassen und Anzahl bleiben gleich - Leser greifen nur ueber id
und Rolle zu (MONT.find(m=>m.id===...).r).

Pin:
  - keine '@'-Adresse ausserhalb von example.invalid in beiden Bloecken
  - kein nicht-leeres gebDat / svnr / reisepass / fsNr / eintritt in MONT
  - Anzahl, ids, Schluessel, Rollen, monteurId gleich wie 05cfb99 (3.9.1119)
Umkehrprobe: dieselbe Pruefung gegen den Text von 05cfb99 MUSS anschlagen.
"""
import io
import os
import re
import subprocess

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASIS = "05cfb99"


def _jetzt():
    return io.open(os.path.join(ROOT, "index.html"), encoding="utf-8", newline="").read()


def _basis():
    try:
        out = subprocess.run(["git", "-C", ROOT, "show", BASIS + ":index.html"],
                             capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        pytest.skip("Basis %s nicht im Repo lesbar" % BASIS)
    return out.stdout.decode("utf-8")


def _block(src, kopf):
    a = src.index(kopf)
    b = src.index("];", a) + 2
    return src[a:b]


def _eintraege(block):
    return re.findall(r"\{id:\"[uw]\d+\"[^{}]*\}", block)


def _felder(eintrag):
    return dict(re.findall(r"(\w+):(\"[^\"]*\"|null|true|false)", eintrag))


def _personendaten_funde(src):
    """Liefert eine Liste von Funden; leer = sauber."""
    funde = []
    for kopf in ("const INIT_USERS=[", "const MONT=["):
        blk = _block(src, kopf)
        for adr in re.findall(r"[\w.+-]+@[\w.-]+", blk):
            if not adr.endswith("@example.invalid"):
                funde.append("%s: Adresse %s" % (kopf, adr))
    for e in _eintraege(_block(src, "const MONT=[")):
        f = _felder(e)
        for k in ("gebDat", "svnr", "reisepass", "fsNr", "eintritt"):
            if f.get(k, '""') != '""':
                funde.append("MONT %s: %s nicht leer" % (f.get("id"), k))
    return funde


def _struktur(src):
    res = {}
    for kopf in ("const INIT_USERS=[", "const MONT=["):
        rows = []
        for e in _eintraege(_block(src, kopf)):
            f = _felder(e)
            rows.append((f.get("id"), tuple(f.keys()), f.get("role"), f.get("r"),
                         f.get("monteurId"), f.get("fs"), f.get("austritt")))
        res[kopf] = rows
    return res


def test_startdaten_ohne_personendaten():
    funde = _personendaten_funde(_jetzt())
    assert funde == [], funde


def test_umkehrprobe_basis_hat_personendaten():
    # Schutz nie ausgeloest = kein Schutz: gegen 3.9.1119 muss die Pruefung anschlagen.
    funde = _personendaten_funde(_basis())
    assert any("Adresse" in x for x in funde), funde
    assert any("gebDat" in x for x in funde), funde


def test_struktur_gleich_wie_basis():
    jetzt, basis = _struktur(_jetzt()), _struktur(_basis())
    for kopf in basis:
        assert len(basis[kopf]) == 8, (kopf, len(basis[kopf]))
        assert jetzt[kopf] == basis[kopf], kopf


def test_platzhalter_sichtbar():
    blk = _block(_jetzt(), "const INIT_USERS=[")
    assert blk.count("@example.invalid") == 8
    assert _block(_jetzt(), "const MONT=[").count('vorname:"Muster"') == 8
