# -*- coding: utf-8 -*-
"""v3.9.931 - der Rumpf gegen den Fehlalarm aus dem Nichts muss selbst halten.

WOZU
────
`scripts/messen.py` soll genau EINE Verwechslung unmoeglich machen: die
zwischen "nichts gefunden" und "nichts gemessen". Am 24./25.09.2026 sind
daran vier Messungen gescheitert, zuletzt meine eigene Wisch-Probe, die
"alle Flaechen wechseln" meldete, ohne eine einzige Flaeche gemessen zu haben.

DER KOEDER
──────────
`test_eine_saubere_messung_geht_durch`: verweigerte `urteil` immer, sagten die
Verweigerungsfaelle nichts aus.
"""
import sys

import pytest

from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WURZEL / "scripts"))

from messen import urteil, koeder, MessungOhneGrundgesamtheit  # noqa: E402


# ── Der Koeder ──────────────────────────────────────────────────────────────

def test_eine_saubere_messung_geht_durch(capsys):
    """KOEDER. Ohne diesen Fall waere 'er verweigert' wertlos."""
    schlimm = urteil("Probe", [{"ok": True}, {"ok": True}],
                     schlecht=lambda f: not f["ok"])
    assert schlimm == []
    assert "gruen - 2 Faelle" in capsys.readouterr().out


# ── Die eine Verwechslung, um die es geht ──────────────────────────────────

def test_eine_leere_grundgesamtheit_ist_kein_gruenes_ergebnis():
    """Der Kern. Null Funde duerfen NICHT wie null Fehler aussehen."""
    with pytest.raises(MessungOhneGrundgesamtheit) as e:
        urteil("Wisch-Flaechen", [])
    m = str(e.value)
    assert "ausgefallene" in m and "gruenes Ergebnis" in m, m


def test_zu_wenige_faelle_werden_verweigert():
    with pytest.raises(MessungOhneGrundgesamtheit):
        urteil("Reiter", [{"ok": True}] * 3, mindestens=24)


def test_ein_echter_fund_wird_rot(capsys):
    schlimm = urteil("Probe", [{"ok": True}, {"ok": False}],
                     schlecht=lambda f: not f["ok"])
    assert len(schlimm) == 1
    assert "ROT - 1 von 2" in capsys.readouterr().out


# ── Der Koeder als Werkzeug ────────────────────────────────────────────────

def test_ein_stummer_koeder_bricht_den_lauf_ab():
    """Schlaegt der Fall, der anschlagen MUSS, nicht an, sieht das Werkzeug
    nichts - dann ist jedes Ergebnis erfunden, auch ein gruenes."""
    with pytest.raises(SystemExit) as e:
        koeder("Der Reiter wechselt", lambda: False)
    assert "KOEDER GESCHEITERT" in str(e.value)
    assert "erfunden" in str(e.value)


def test_ein_werfender_koeder_bricht_den_lauf_ab():
    with pytest.raises(SystemExit) as e:
        koeder("Der Reiter wechselt", lambda: 1 / 0)
    assert "KOEDER GESCHEITERT" in str(e.value)


def test_ein_anschlagender_koeder_laesst_weiterarbeiten():
    """KOEDER des Koeders."""
    assert koeder("Der Reiter wechselt", lambda: "Reiter 1") == "Reiter 1"
