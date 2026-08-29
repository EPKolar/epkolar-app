# -*- coding: utf-8 -*-
"""Die Selbstpruefung des Laufzeit-Messgeraets (29.08.2026).

Ohne Versionsnummer im Namen: dieser Riegel sichert ein SKRIPT, keine
App-Version - index.html ist dafuer unveraendert geblieben.

WORUM ES GEHT
-------------
`scripts/perf_live.py` misst Speicher, DOM-Groesse und Umschaltzeit der
Live-App. Es ist an EINEM Nachmittag DREIMAL an sich selbst gescheitert, und
jedes Mal sahen die Zahlen brauchbar aus:

  1. Achtzehn Ansichten, achtzehn identische Heap-Werte (12,8 MB). Ursache:
     Chromium rundet `performance.memory` grob, solange
     `--enable-precise-memory-info` fehlt.
  2. Achtzehn Umschaltzeiten zwischen 460 und 468 ms - bei einem eigenen
     `wait_for_timeout(450)` im Ablauf. Das war nicht die App, das war die
     eigene Wartezeit.
  3. Danach vierzehn von achtzehn Zeiten auf -1 ("nichts hat sich geruehrt"),
     weil ab der zweiten Messrunde auf den BEREITS OFFENEN Tab geklickt wurde.

Keiner dieser drei Fehler haette einen Absturz erzeugt. Alle drei haetten eine
Tabelle geliefert, die man in einen Handoff schreiben kann. **Ein Messwert, der
nicht auseinandergehen KANN, ist dasselbe wie ein Riegel, der nicht rot werden
kann** - und davon hat dieses Repo schon zu viele gesehen.

Deshalb prueft das Skript sich selbst: eine Spalte, die ueber achtzehn sehr
unterschiedliche Ansichten kaum streut, wird als UNGUELTIG gemeldet statt still
als Befund ausgegeben. Diese Datei prueft genau diese Selbstpruefung - in beide
Richtungen.
"""
import os
import sys

import pytest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if os.path.join(REPO, "scripts") not in sys.path:
    sys.path.insert(0, os.path.join(REPO, "scripts"))

perf_live = pytest.importorskip("perf_live")


def _zeilen(werte_heap, werte_zeit):
    """Baut Ergebniszeilen im Format (name, heapKum, domNodes, umschaltMs)."""
    return [("A%d" % i, h, 200, z)
            for i, (h, z) in enumerate(zip(werte_heap, werte_zeit))]


# ══ Die Selbstpruefung schlaegt an, wenn eine Spalte tot ist ════════════════

def test_identische_heapwerte_gelten_als_ungueltig():
    """Fall 1 der echten Historie: ohne die praezise Speicher-Fahne lieferte
    Chromium fuer alle achtzehn Ansichten denselben Wert."""
    zeilen = _zeilen([12.8] * 18, [10, 200, 15, 30, 5, 120, 8, 44, 17, 9,
                                   250, 3, 60, 22, 11, 90, 7, 33])
    meldungen = perf_live.ungueltige_spalten(zeilen)
    assert any("heapKum" in m for m in meldungen), (
        "Achtzehn identische Heap-Werte gelten als gueltige Messung - dann "
        "landet eine tote Spalte als Befund im Handoff."
    )
    assert not any("umschaltMs" in m for m in meldungen), (
        "Die Zeit-Spalte streut deutlich und darf nicht mitverworfen werden."
    )


def test_die_eigene_wartezeit_gilt_als_ungueltig():
    """Fall 2: achtzehn Umschaltzeiten zwischen 460 und 468 ms, bei einem
    eigenen wait_for_timeout(450). Das ist der Aufbau, nicht die App."""
    zeiten = [460, 461, 462, 463, 464, 465, 466, 467, 468, 464,
              461, 463, 462, 466, 465, 463, 464, 462]
    zeilen = _zeilen([9.9, 10.2, 10.5, 11.0, 11.4, 12.1, 12.6, 13.0, 13.4,
                      9.9, 10.1, 10.4, 10.9, 11.5, 12.0, 12.4, 12.9, 13.3],
                     zeiten)
    meldungen = perf_live.ungueltige_spalten(zeilen)
    assert any("umschaltMs" in m for m in meldungen), (
        "Achtzehn praktisch gleiche Umschaltzeiten gelten als Messung - genau "
        "die Tabelle, die am 29.08. fast als Ergebnis gemeldet worden waere."
    )


def test_die_meldung_sagt_was_zu_tun_ist():
    zeilen = _zeilen([12.8] * 18, [12.8] * 18)
    meldungen = perf_live.ungueltige_spalten(zeilen)
    assert len(meldungen) == 2, "Beide toten Spalten muessen gemeldet werden"
    for m in meldungen:
        assert "misst den Messaufbau" in m, (
            "Die Meldung sagt nicht, WARUM die Zahl unbrauchbar ist:" + chr(10) + m
        )
        assert "Nicht als Befund verwenden" in m, (
            "Die Meldung sagt nicht, was der Leser tun soll:" + chr(10) + m
        )


# ══ Umkehrprobe: bei echter Streuung darf sie NICHT anschlagen ══════════════

def test_echte_messwerte_gelten_als_gueltig():
    """DIE GEGENPROBE. Ohne sie wuerde ein `return [alles]` die drei Tests
    oben ebenfalls gruen faerben - und das Messgeraet waere immer ungueltig,
    also genauso wertlos wie immer gueltig.

    Die Zahlen hier sind der echte Lauf gegen v3.9.896 (gekuerzt)."""
    heap = [10.2, 10.2, 10.2, 10.5, 10.8, 10.7, 11.2, 11.0, 11.4,
            11.7, 11.8, 11.9, 11.8, 11.9, 12.3, 12.2, 12.5, 12.6]
    zeit = [244, 13, 15, 31, 18, 22, 18, 12, 13, 224, 5, 3, 4, 5, 11, 155, 126, 14]
    assert perf_live.ungueltige_spalten(_zeilen(heap, zeit)) == [], (
        "Der echte Lauf gegen v3.9.896 gilt als ungueltig - dann meldet das "
        "Messgeraet grundsaetzlich alles als tot und ist selbst wertlos."
    )


def test_fehlende_werte_werden_nicht_mitgezaehlt():
    """-1 heisst 'die Ansicht war schon offen, es hat sich nichts geruehrt'.
    Solche Zeilen duerfen die Streuung nicht kuenstlich aufblasen."""
    zeilen = _zeilen([11.0] * 6, [-1, -1, -1, 30, 30, 30])
    meldungen = perf_live.ungueltige_spalten(zeilen)
    assert any("umschaltMs" in m for m in meldungen), (
        "Die -1-Zeilen wurden mitgerechnet - dann taeuscht ein Ausfall eine "
        "Streuung vor, und eine tote Spalte kommt durch."
    )


def test_zu_wenige_werte_werden_nicht_beurteilt():
    """Bei zwei Ansichten sagt die Streuung nichts - dann lieber schweigen als
    eine gute Spalte verwerfen."""
    assert perf_live.ungueltige_spalten(_zeilen([11.0, 11.0], [20, 20])) == []


# ══ Das Modul bleibt folgenlos importierbar ═════════════════════════════════

def test_import_startet_keinen_browser():
    """Der Riegel oben importiert das Modul. Wuerde dabei der Messlauf
    starten, kostete jeder Testlauf Minuten und braeuchte Netz."""
    assert hasattr(perf_live, "main")
    assert hasattr(perf_live, "ungueltige_spalten")
    assert perf_live.LIVE.startswith("https://"), (
        "Der Live-Messpunkt fehlt oder zeigt nicht mehr auf https."
    )
