# -*- coding: utf-8 -*-
"""v3.9.1111 - Timer und "Wie letzte Woche" unter der neuen 15-min-Pruefung (GF-Frage 24.11.).

Befund (gemessen im Code):
- "Wie letzte Woche" (_wlwUebernehmen) bucht JEDE Zeile ueber addEntry mit editEntry:null - also wie eine neue Buchung.
  Krumme Alt-Werte (z. B. Von 07:05 aus der Vorwoche) werden deshalb ABGELEHNT und als "nicht gespeichert" gezaehlt
  (Sammelmeldung "n uebernommen, m nicht gespeichert"); sie umgehen die Pruefung nicht. Die Vorschau markiert sie vorher
  NICHT - das waere eine Aenderung an Fundstelle 8, die GF 24.11. noch nicht freigegeben hat.
- Timer (TimerBar.onStop) bucht DIREKT per SQ.push, ohne addEntry: er UMGEHT die Raster-Pruefung und bucht weiter im
  5-min-Stempel-Raster (z. B. 1,08 h). GF 24.11.: Fundstelle 7 noch nicht anfassen (0 Timer-Buchungen in 3 Monaten).
  Dieser Test haelt den offenen Punkt ausdruecklich fest - wer den Timer anpasst, aendert ihn bewusst mit.
"""
import json
import re

from conftest import run_node_snippet, _extract_fn


def _ze_addentry(html):
    i = html.index("function ZeiterfassungView(")
    a = html.index("  const addEntry=async()=>{", i)
    return html[a:html.index("  const _wlwAbs=()=>{", a)]


def test_wie_letzte_woche_laeuft_durch_addentry_als_neue_buchung(index_html):
    i = index_html.index("const _wlwUebernehmen=async()=>{")
    w = index_html[i:index_html.index("const wlwModal=()=>{", i)]
    assert "editEntry:null" in w and "ok=await addEntry();" in w
    assert "SQ.push" not in w, "Wie letzte Woche darf nicht an addEntry vorbei schreiben"
    ae = _ze_addentry(index_html)
    assert "_zeitPflichtFehler(_rVon,_rBis,addPause,addHours,(editEntry&&editEntry.orig)||null)" in ae
    assert "_zeitEingabeFehler(_rVon,_rBis,h,(editEntry&&editEntry.orig)||null)" in ae


def test_wie_letzte_woche_krumme_altzeile_wird_abgelehnt(node_exe, index_html):
    """Dieselbe Pruefung, die addEntry fuer eine WLW-Zeile ruft (orig = null): 07:05 aus der Vorwoche -> Ablehnung."""
    teile = [re.search(r"const ZEIT_RASTER_MIN=\d+;", index_html).group(0),
             re.search(r"const ZEIT_EINGABE_RASTER_MIN=\d+;", index_html).group(0)]
    for n in ("_zeitParse", "_zeitFmt", "_zeitImRaster", "_stdImRaster", "_zeit5", "_zeitEingabeFehler"):
        teile.append(_extract_fn(index_html, n))
    r = json.loads(run_node_snippet(node_exe, "\n".join(teile) + "\nprocess.stdout.write(JSON.stringify(["
                                    "_zeitEingabeFehler('07:05','16:00',7.92,null),_zeitEingabeFehler('07:00','16:00',8,null)]));"))
    assert r[0] and "Von" in r[0], "krumme WLW-Zeile wuerde gebucht"
    assert r[1] is None


def test_timer_umgeht_die_raster_pruefung_offener_punkt(index_html):
    i = index_html.index("const onStop=()=>{")
    t = index_html[i:index_html.index("  return React.createElement('div'", i)]
    assert 'SQ.push({url:"/api/entries",method:"POST"' in t, "Timer bucht nicht mehr direkt - Befund pruefen"
    assert "_zeitEingabeFehler" not in t and "addEntry" not in t, "Timer prueft jetzt - Doku oben anpassen"
    assert "const _vonMs=_stRoundKommen(s.startAt);const _bisMs=_stRoundGehen(_endAt);" in index_html, "Timer-Raster geaendert"
