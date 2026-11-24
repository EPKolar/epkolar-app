# -*- coding: utf-8 -*-
"""v3.9.1107 Entfernungszulage laut Stempeluhr (GF 24.11.2026: "auf Stempeluhr umstellen jetzt", nur Stempeluhr ab sofort).

Alle vier Stellen, die die Zulage zeigen oder abrechnen, holen die Tagesstunden aus der Stempeluhr (_ezTageAusStempel bzw.
den Stempel-Zeilen des PZE-PDF) statt aus der Summe der Zeiteintraege. _ezEffTage selbst bleibt unveraendert (md5-Tor).
Im Browser gemessen 24.11. (Testdaten): Projektzeit an allen Werktagen, Stempelungen nur 3./4./5.11. ->
Zaehler 1 klein / 1 mittel (Kalender-Stufen) statt vorher 19 klein / 1 mittel; Tabelle 41,94 EUR.
"""
import io
import os
import re

HIER = os.path.dirname(os.path.abspath(__file__))
HTML = os.path.join(HIER, "..", "index.html")


def _src():
    return io.open(HTML, encoding="utf-8", newline="").read()


def _fn(s, name):
    i = s.index("function " + name + "(")
    j = s.index("\nfunction ", i + 10)
    k = s.find("\nasync function ", i + 10)
    if 0 <= k < j:
        j = k
    return s[i:j]


def _ohne(t):
    return re.sub(r"/\*.*?\*/", "", t, flags=re.S)


def _quellen(s):
    kv = _ohne(_fn(s, "KVZulagenReport"))
    pdf = _ohne(_fn(s, "_pzePdf"))
    sz = _ohne(_fn(s, "StundenzettelView"))
    st = _ohne(_fn(s, "_bxMaStand"))
    return {
        "kv_tage": "const _ezDaysFor=(wid)=>wid?_ezTageAusStempel(stz.evs,_ezWorker(monteure,wid),stz.rules,ym):{};" in kv,
        "kv_tabelle": "var d=_ezTageAusStempel(stz.evs,_ezWorker(monteure,wid),stz.rules,ym);" in kv,
        "kv_laden": "Promise.all([_ezFetch(ym),_ezLadeStempel(ym)])" in kv,
        "pdf": "rows.forEach(function(r){if(r&&r.stempelAnzahl>0&&r.nettoMin>0)daysMap[r.datum]=Math.round(r.nettoMin/60*100)/100;});" in pdf
               and "(entries||[]).forEach(function(e){if(!e)return;var iso=String(e.date||e.datum||'').slice(0,10);if(iso.slice(0,7)!==ym)return;var ew=" not in pdf,
        "eigen": "_ezEffTage(_ezDays,ezFlags,_myWid," in sz and "_ezLadeStempel(_ymSel,_w)" in sz,
        "abschluss": "_ezEffTage(_ezTageAusStempel(stz&&stz.evs," in st,
    }


def test_alle_vier_stellen_lesen_die_stempeluhr():
    q = _quellen(_src())
    assert all(q.values()), q


def test_umkehrprobe_alter_weg_faellt_auf():
    s = _src()
    alt = s.replace("const _ezDaysFor=(wid)=>wid?_ezTageAusStempel(stz.evs,_ezWorker(monteure,wid),stz.rules,ym):{};",
                    "const _ezDaysFor=(wid)=>{var d={};return d;};", 1)
    assert alt != s and not _quellen(alt)["kv_tage"]
    alt2 = s.replace("_ezEffTage(_ezDays,ezFlags,_myWid,", "_ezEffTage(days,ezFlags,_myWid,", 1)
    assert alt2 != s and not _quellen(alt2)["eigen"]


def test_helfer_rechnet_in_stunden_und_nur_gestempelte_tage():
    f = _ohne(_fn(_src(), "_ezTageAusStempel"))
    assert "_pzeBuildRows(worker,ym+\"-01\",bis,evs||[],rules||STEMPEL_PAUSE_FALLBACK,[],{},[])" in f
    assert "if(r&&r.stempelAnzahl>0&&r.nettoMin>0)out[r.datum]=Math.round(r.nettoMin/60*100)/100;" in f


def test_pdf_und_kalender_gesperrt_bis_stempel_geladen():
    kv = _ohne(_fn(_src(), "KVZulagenReport"))
    assert "setEzStand((r&&(r.ok||r.missing))&&s.status==='ok'?'ok':'fehler');" in kv
    assert "disabled:!ezWid||ezStand!=='ok'" in kv


def test_beschriftungen_umbenannt():
    s = _src()
    for alt in ('"Monatsliste (Lohn):")', '"Lohn-Monatsliste · "+', '"Stunden und Lohn-Monatsliste")', '"Ist-Stunden")'):
        assert alt not in s, alt
    for neu in ('"Monatsliste Projektzeit:")', '"Monatsliste Projektzeit · "+', '"Projektstunden und Monatsliste")', '"Projektstunden")'):
        assert neu in s, neu
