# -*- coding: utf-8 -*-
"""Riegel fuer scripts/suche_beleg.py (25.11.2026): eine Suche, die Zeilen still weglaesst, ist kein Beleg."""
import os
import re
import subprocess
import sys

import pytest

HIER = os.path.dirname(os.path.abspath(__file__))
SKRIPT = os.path.join(HIER, "..", "scripts", "suche_beleg.py")
sys.path.insert(0, os.path.join(HIER, "..", "scripts"))
import suche_beleg as sb  # noqa: E402

LANG = "login_lookup" + "x" * 5000                      # Treffer am ANFANG einer langen Zeile
TEXT = "\n".join([
    "kurz",
    "  login_lookup(",                                    # kurze, eingerueckte Zeile (wie index.html:3848)
    LANG,
    "y" * 3000 + "login_lookup",                          # Treffer am ENDE einer langen Zeile
    "nichts hier",
])


def test_lange_zeile_mit_treffer_am_anfang_wird_gefunden():
    t = sb.suche(TEXT, "login_lookup")
    assert (3, 1) in [(z, s) for z, s, _ in t]


def test_jede_zeile_wird_gefunden_auch_kurze_und_ende():
    zeilen = sorted({z for z, _, _ in sb.suche(TEXT, "login_lookup")})
    soll = [i for i, l in enumerate(TEXT.splitlines(), 1) if "login_lookup" in l]
    assert zeilen == soll == [2, 3, 4]


def test_gegenprobe_feste_breite_verliert_genau_diese_zeilen():
    """Zeigt den Fehler, den das Werkzeug verhindert: .{40}X.{40} findet die Anfangs- und Endtreffer nicht."""
    fest = [i for i, l in enumerate(TEXT.splitlines(), 1) if re.search(r".{40}login_lookup.{40}", l)]
    assert fest == []  # alle drei Zeilen fallen still heraus
    assert len(sb.suche(TEXT, "login_lookup")) == 3


@pytest.mark.parametrize("muster", [r".\{100\}login_lookup.\{140\}", r".{40}x", r"a.\{40,\}", r".{40,200}b"])
def test_feste_breite_wird_abgelehnt(muster, tmp_path):
    f = tmp_path / "d.txt"
    f.write_text(TEXT, encoding="utf-8")
    r = subprocess.run([sys.executable, SKRIPT, muster, str(f), "--kontrolle", "kurz"], capture_output=True, text=True)
    assert r.returncode == 3


@pytest.mark.parametrize("muster", ["login_lookup", r".\{0,100\}x", "a.b"])
def test_offene_grenzen_sind_erlaubt(muster):
    assert not sb.ist_feste_breite(muster)


def test_ohne_positivkontrolle_kein_beleg(tmp_path):
    f = tmp_path / "d.txt"
    f.write_text(TEXT, encoding="utf-8")
    ohne = subprocess.run([sys.executable, SKRIPT, "login_lookup", str(f)], capture_output=True, text=True)
    falsch = subprocess.run([sys.executable, SKRIPT, "login_lookup", str(f), "--kontrolle", "GIBTESNICHT"],
                            capture_output=True, text=True)
    assert ohne.returncode == 2 and falsch.returncode == 2
    assert "TREFFER" not in ohne.stdout + falsch.stdout   # ohne Eichung wird gar kein Ergebnis gemeldet


def test_geeichte_suche_meldet_alle_treffer(tmp_path):
    f = tmp_path / "d.txt"
    f.write_text(TEXT, encoding="utf-8")
    r = subprocess.run([sys.executable, SKRIPT, "login_lookup", str(f), "--kontrolle", "kurz"],
                       capture_output=True, text=True)
    assert r.returncode == 0
    assert "TREFFER 3 in 3 Zeilen" in r.stdout
    assert re.search(r"^3:1: login_lookup", r.stdout, re.M)


def test_null_treffer_mit_kontrolle_ist_ein_beleg(tmp_path):
    f = tmp_path / "d.txt"
    f.write_text(TEXT, encoding="utf-8")
    r = subprocess.run([sys.executable, SKRIPT, "password_hash", str(f), "--kontrolle", "kurz"],
                       capture_output=True, text=True)
    assert r.returncode == 0 and "TREFFER 0 in 0 Zeilen" in r.stdout


def test_sonderzeichen_in_der_ausgabe_bricht_nicht_ab(tmp_path):
    """25.11.: erster Lauf gegen index.html brach an einem Pfeil ab (cp1252) - die Treffer danach fehlten."""
    f = tmp_path / "d.txt"
    f.write_text("kurz\nlogin_lookup → Umlaut ä\nlogin_lookup zwei\n", encoding="utf-8")
    env = dict(os.environ)
    env.pop("PYTHONIOENCODING", None)
    env.pop("PYTHONUTF8", None)
    r = subprocess.run([sys.executable, SKRIPT, "login_lookup", str(f), "--kontrolle", "kurz"],
                       capture_output=True, env=env)
    assert r.returncode == 0, r.stderr.decode("utf-8", "replace")[-500:]
    assert b"TREFFER 2 in 2 Zeilen" in r.stdout
