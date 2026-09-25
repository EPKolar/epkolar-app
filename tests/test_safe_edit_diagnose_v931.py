# -*- coding: utf-8 -*-
"""v3.9.931 - Ein verfehlter Anker muss sagen WARUM.

WOZU
────
Am 25.09.2026 sind in EINER Sitzung rund zehn Anlaeufe daran gescheitert, dass
ein Anker NACHGEBAUT statt GESCHNITTEN wurde. Die Meldung war jedes Mal
dieselbe - "trifft 0 mal statt genau einmal" - und danach folgte jedes Mal
dieselbe Sucherei. Die Ursachen waren in Wahrheit nur vier:

    Zeilenenden      die Datei ist CRLF, der Anker LF
    Leerraum         Einrueckung oder Umbruch weicht ab
    ein Zeichen      `!=` statt `!==`, `\\u2014` statt des Gedankenstrichs
    mehrfach         der Anker trifft zweimal, die unterscheidende Zeile fehlt

WAS DIESER RIEGEL MISST
───────────────────────
Nicht, dass eine Diagnose EXISTIERT, sondern dass sie die RICHTIGE nennt. Jede
der vier Ursachen wird nachgebaut, und die Meldung muss sie beim Namen nennen.

**Eine falsche Diagnose ist schlimmer als keine** - sie schickt den naechsten
in die falsche Richtung. Deshalb pruefen die Faelle nicht nur, dass das richtige
Wort vorkommt, sondern auch, dass die FALSCHEN Woerter fehlen.

DER KOEDER
──────────
`test_ein_richtiger_anker_loest_keine_diagnose_aus`: geht ein sauberer Anker
durch, kann der Aufbau ueberhaupt unterscheiden. Ohne diesen Nachweis waere
"die Diagnose nennt die Ursache" wertlos - sie koennte sie immer nennen.
"""
import io

import pytest

from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]

import sys
sys.path.insert(0, str(WURZEL / "scripts"))
from safe_edit import ersetze, schneide  # noqa: E402

CRLF = chr(13) + chr(10)
LF = chr(10)


def _datei(tmp_path, inhalt, name="probe.txt"):
    p = tmp_path / name
    io.open(str(p), "w", encoding="utf-8", newline="").write(inhalt)
    return str(p)


def _meldung(pfad, alt, neu="X"):
    """Fuehrt den Ersatz aus und gibt die Meldung zurueck - er MUSS scheitern."""
    with pytest.raises(SystemExit) as e:
        ersetze(pfad, [(alt, neu, "Probe")], min_bytes=10)
    return str(e.value)


# ── Der Koeder ──────────────────────────────────────────────────────────────

def test_ein_richtiger_anker_loest_keine_diagnose_aus(tmp_path):
    """KOEDER. Ginge auch ein sauberer Anker schief, saegte jede Diagnose
    darunter nichts aus - sie waere dann immer da."""
    p = _datei(tmp_path, CRLF.join(["erste Zeile", "zweite Zeile", "dritte"]))
    getan = ersetze(p, [("zweite Zeile", "ZWEITE", "sauber")], min_bytes=10)
    assert getan == ["sauber"]
    assert "ZWEITE" in io.open(p, encoding="utf-8", newline="").read()


# ── Die vier Ursachen ───────────────────────────────────────────────────────

def test_zeilenenden_werden_benannt(tmp_path):
    p = _datei(tmp_path, CRLF.join(["alpha", "beta", "gamma"]))
    m = _meldung(p, "alpha" + LF + "beta")          # LF gegen CRLF-Datei
    assert "ZEILENENDEN" in m, m
    assert "CRLF" in m and "LF" in m, m
    # Nicht die falsche Ursache nennen.
    assert "LEERRAUM" not in m, m


def test_leerraum_wird_benannt(tmp_path):
    p = _datei(tmp_path, "der  Wert   steht da")
    m = _meldung(p, "der Wert steht da")            # einfache statt mehrfache Leerzeichen
    assert "LEERRAUM" in m, m
    assert "ZEILENENDEN" not in m, m


def test_ein_zeichen_daneben_wird_gezeigt(tmp_path):
    p = _datei(tmp_path, "if(typeof API!==" + chr(34) + "undefined" + chr(34) + ")")
    m = _meldung(p, "if(typeof API!=" + chr(34) + "undefined" + chr(34) + ")")
    assert "AUSEINANDER" in m, m
    # Die Meldung muss die Stelle ZEIGEN, nicht nur behaupten.
    assert "in der Datei" in m and "in deinem Anker" in m, m


def test_mehrfachtreffer_raet_zur_zeile_davor(tmp_path):
    p = _datei(tmp_path, CRLF.join([
        "/* Fall A */", "gleiche Zeile", "/* Fall B */", "gleiche Zeile"]))
    m = _meldung(p, "gleiche Zeile")
    assert "mehreren Stellen" in m, m
    assert "Zeile DAVOR" in m, m
    # Die Zeilennummern gehoeren dazu, sonst muss man wieder selbst suchen.
    assert "Zeile 2" in m and "Zeile 4" in m, m


# ── Der Ausweg: schneiden statt tippen ─────────────────────────────────────

def test_schneide_liefert_einen_anker_der_traegt(tmp_path):
    """Was aus der Datei GESCHNITTEN ist, kann nicht anders geschrieben sein."""
    inhalt = CRLF.join(["vorher", "function _tuWas(a){", "  return a;", "}", "nachher"])
    p = _datei(tmp_path, inhalt)
    anker = schneide(p, "function _tuWas(", "}")
    assert CRLF in anker, "der Schnitt muss die Zeilenenden der Datei tragen"
    getan = ersetze(p, [(anker, anker + "/* Notiz */", "geschnitten")], min_bytes=10)
    assert getan == ["geschnitten"]


def test_schneide_verweigert_einen_mehrdeutigen_anfang(tmp_path):
    p = _datei(tmp_path, CRLF.join(["marke hier", "marke hier"]))
    with pytest.raises(SystemExit) as e:
        schneide(p, "marke", "hier")
    assert "kommt 2 mal vor" in str(e.value), str(e.value)


def test_schneide_sagt_es_wenn_das_ende_fehlt(tmp_path):
    p = _datei(tmp_path, "nur ein Anfang")
    with pytest.raises(SystemExit) as e:
        schneide(p, "nur", "GIBTESNICHT")
    assert "Ende" in str(e.value), str(e.value)


# ── Die alten Zusicherungen gelten weiter ──────────────────────────────────

def test_die_groessenschranke_haelt_weiterhin(tmp_path):
    """Der urspruengliche Zweck des Moduls: keine Datei auf 0 Bytes."""
    p = _datei(tmp_path, "x" * 50)
    with pytest.raises(SystemExit) as e:
        ersetze(p, [("x" * 50, "", "alles weg")], min_bytes=10)
    assert "Datenverlust" in str(e.value), str(e.value)


def test_ein_einzelnes_surrogat_wird_abgefangen(tmp_path):
    """Die Ursache, die zweimal eine Datei geleert hat."""
    p = _datei(tmp_path, "hier steht Text")
    with pytest.raises(SystemExit) as e:
        ersetze(p, [("Text", "Text" + chr(0xD83D), "Surrogat")], min_bytes=10)
    assert "Surrogat" in str(e.value), str(e.value)
    assert io.open(p, encoding="utf-8", newline="").read() == "hier steht Text", (
        "Das Original muss unberuehrt bleiben.")
