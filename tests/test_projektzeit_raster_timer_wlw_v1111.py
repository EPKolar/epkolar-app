# -*- coding: utf-8 -*-
"""v3.9.1111 - Timer und "Wie letzte Woche" ENTFERNT (GF Sebastian 24.11.2026, Fundstellen 7 und 8).

Vorher (gemessen): "Wie letzte Woche" buchte ueber addEntry (krumme Alt-Zeilen wurden abgelehnt), der Timer buchte direkt
per SQ.push im 5-min-Stempel-Raster und umging damit die 15-min-Pruefung. GF: beides entfernen, damit kein Stand live geht,
in dem der Timer das Raster umgeht. Bestehende Eintraege bleiben unveraendert (keine Datenaenderung).
Einziger Anlegeweg fuer Projektzeit ist damit addEntry mit _zeitPflichtFehler/_zeitEingabeFehler.
"""
import io
import os

HTML = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "index.html")

WEG = ("_wieLetzteWoche", "_wlwOeffnen", "_wlwUebernehmen", "wlwModal", "data-wlw-knopf", "\"Wie letzte Woche\")",
       "window._epkTimer", "_epkTimer.stop(", "function TimerBanner(", "React.createElement(TimerBanner",
       "Timer-Lauf unter 5 Minuten")


def _src():
    return io.open(HTML, encoding="utf-8", newline="").read()


def _reste(s):
    return [w for w in WEG if w in s]


def test_timer_und_wie_letzte_woche_sind_weg():
    assert _reste(_src()) == []


def test_einziger_anlegeweg_prueft_das_raster():
    s = _src()
    i = s.index("function ZeiterfassungView(")
    a = s.index("  const addEntry=async()=>{", i)
    ae = s[a:s.index("  // Totals", a)]
    assert "_zeitPflichtFehler(_rVon,_rBis,addPause,addHours,(editEntry&&editEntry.orig)||null)" in ae
    assert "_zeitEingabeFehler(_rVon,_rBis,h,(editEntry&&editEntry.orig)||null)" in ae
    assert "_wl" not in ae


def test_abmelden_verwirft_nur_alte_timer_reste():
    s = _src()
    assert "try{localStorage.removeItem('epk_timer');}catch(_){}/* v3.9.1111: Timer entfernt" in s


def test_umkehrprobe():
    s = _src()
    for zurueck in ("window._epkTimer={start:function(){}}", "React.createElement('button',{onClick:_wlwOeffnen},\"Wie letzte Woche\")"):
        assert _reste(s + zurueck), zurueck
