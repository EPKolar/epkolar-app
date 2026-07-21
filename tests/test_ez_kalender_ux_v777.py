# -*- coding: utf-8 -*-
"""v3.9.777 — Entfernungszulage-Kalender (EZKalender) UX.

REINE ANZEIGE + Heute-Navigation (Sebastian live, v775: "ueberhaupt noch ned schoen",
Heute-Button geht nicht, Kacheln brauchen Infos). Kein neuer Fetch, keine neue Datenquelle.

Gefixt / gebaut:
  1) Heute-Button springt via Wiener Datum (_ezHeuteISO, Intl Europe/Vienna, PURE) auf den
     aktuellen Monat (Monatsansicht) bzw. die aktuelle Woche (Wochenansicht) — setzt ezCursor+ym.
     URSACHE des "geht nicht": raw new Date() (geraetezeit-abhaengig) + KEIN Heute-Marker im
     Kalender -> beim Default-Monat (schon aktueller Monat) aendert der Klick nichts Sichtbares.
  2) Heutige Kachel bekommt einen Akzent-Ring (boxShadow V.ac) + fette Tageszahl.
  3) Kacheln zeigen gebuchte Stunden (_n(std,1)+' h') und ein lesbares Status-Label
     (✓ vergeben / vorbelegt / ✕ abgewählt) statt des unlesbaren Mini-Punkts.
  4) Legende mit Farbchips unter dem Kopf.

BEWEIS ANZEIGE-ONLY: _ezDayEff/_ezEffTage/_ezSet/_ezFetch byte-identisch (test_rechnung_unberuehrt
in test_ez_kalender_v775.py + die eff-Pins hier), Satz 11,71 unveraendert, Riedmann 93,68 bleibt.
"""
import re
import subprocess


def _block(index_html):
    """Modul-Block der pure Helfer (inkl. _ezHeuteISO, bis vor _ezFetch)."""
    start = index_html.index("function _ezWtag(iso){")
    end = index_html.index("async function _ezFetch(ym){", start)
    return index_html[start:end]


_OK = u"\nfunction ok(c,n){ if(!c){ console.error('FAIL '+n); process.exit(1);} }\n"


def _run(node_exe, tmp_path, js):
    f = tmp_path / "ez777.js"
    f.write_text(js, encoding="utf-8")
    r = subprocess.run([node_exe, str(f)], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")
    assert "OK" in r.stdout


def _ez_kalender_block(index_html):
    """Der Rumpf von EZKalender (bis zum naechsten Top-Level-Kommentarblock)."""
    start = index_html.index("function EZKalender(props){")
    end = index_html.index("function KVZulagenReport(props){", start)
    return index_html[start:end]


def test_ez_heute_iso_format(index_html, node_exe, tmp_path):
    """_ezHeuteISO() liefert einen gueltigen YYYY-MM-DD-String (Wiener Datum, PURE, node-testbar)."""
    js = _block(index_html) + _OK + u"""
var iso=_ezHeuteISO();
ok(typeof iso==='string','string');
ok(/^\\d{4}-\\d{2}-\\d{2}$/.test(iso),'YYYY-MM-DD: '+iso);
var mo=parseInt(iso.slice(5,7),10), da=parseInt(iso.slice(8,10),10);
ok(mo>=1&&mo<=12,'Monat 1..12');
ok(da>=1&&da<=31,'Tag 1..31');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_ez_heute_sprung_monat_und_woche(index_html, node_exe, tmp_path):
    """Die Heute-Sprung-Logik landet in BEIDEN Ansichten auf dem heutigen Tag.

    Monat: die Monatsansicht wird aus ezCursor=heute gebaut -> Grid enthaelt heute mit inMonth.
    Woche: die Wochenansicht wird aus ezCursor=heute gebaut -> _ezWeekDays enthaelt heute.
    (Beweist, dass ezCursor=_ezHeuteISO() sowohl Monat als auch Woche korrekt auf heute stellt.)
    """
    js = _block(index_html) + _OK + u"""
var iso=_ezHeuteISO();
var p=iso.split('-');
// Monat: Grid aus dem Cursor-Monat enthaelt heute (inMonth)
var g=_ezMonthGrid(parseInt(p[0],10),parseInt(p[1],10)-1);
var inMonat=false;g.forEach(function(w){w.forEach(function(o){if(o.iso===iso&&o.inMonth)inMonat=true;});});
ok(inMonat,'Monatsansicht enthaelt heute mit inMonth');
// Woche: die Woche um heute enthaelt heute
var wd=_ezWeekDays(iso);
ok(wd.length===7,'7 Tage');
var inWoche=wd.some(function(o){return o.iso===iso;});
ok(inWoche,'Wochenansicht enthaelt heute');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_ez_heute_handler_setzt_beide_states(index_html):
    """_ezHeute nutzt das Wiener Datum (_ezHeuteISO) und setzt ezCursor UND ym (Monat+Woche)."""
    m = re.search(r"const _ezHeute=\(\)=>\{[^;]*_ezHeuteISO\(\);setEzCursor\(iso\);setYm\(iso\.slice\(0,7\)\);\};", index_html)
    assert m, "_ezHeute muss iso=_ezHeuteISO() setzen und ezCursor+ym aktualisieren"
    # kein rohes new Date() mehr im Handler
    m2 = re.search(r"const _ezHeute=\(\)=>\{(.*?)\};", index_html)
    assert m2 and "new Date()" not in m2.group(1), "_ezHeute darf kein rohes new Date() mehr nutzen (Wiener Datum via _ezHeuteISO)"


def test_ez_heute_iso_window_export(index_html):
    assert "window._ezHeuteISO=_ezHeuteISO" in index_html
    assert "Intl.DateTimeFormat('en-CA',{timeZone:'Europe/Vienna'})" in index_html


def test_cell_zeigt_stunden(index_html):
    """Struktur-Pin: die Kachel zeigt die gebuchten Stunden des Tages (aus derselben daysMap)."""
    blk = _ez_kalender_block(index_html)
    assert "var stdN=parseFloat(std)||0;" in blk
    assert "_n(std,1)+' h'" in blk, "Stunden-Anzeige in der Kachel fehlt"


def test_cell_status_label_statt_punkt(index_html):
    """Struktur-Pin: lesbares Status-Label je Zustand statt des unlesbaren Mini-Punkts."""
    blk = _ez_kalender_block(index_html)
    assert "'✓ vergeben'" in blk
    assert "'vorbelegt'" in blk
    assert "'✕ abgewählt'" in blk
    # der fruehere Mini-Punkt-Marker ist weg
    assert "mark='•'" not in blk, "Mini-Punkt '•' muss durch lesbares Label ersetzt sein"


def test_cell_heute_ring(index_html):
    """Heute-Ring-Pin: heutiges-Datum-Vergleich + Ring-Style sind im Code."""
    blk = _ez_kalender_block(index_html)
    assert "const _heute=_ezHeuteISO();" in blk, "Heute-Datum wird via _ezHeuteISO ermittelt"
    assert "var isToday=(iso===_heute);" in blk, "Kachel vergleicht ihr Datum mit heute"
    assert "boxShadow:isToday?('0 0 0 2px '+V.ac):'none'" in blk, "Akzent-Ring fuer heute fehlt"


def test_legende_vorhanden(index_html):
    """Optik: Legende-Zeile mit Farbchips (vergeben/vorbelegt/abgewählt/Ring=heute)."""
    start = index_html.index("function KVZulagenReport(props){")
    body = index_html[start:index_html.index("function ", start + 10)]
    assert "'Ring = heute'" in body
    assert "'vorbelegt (Vorschlag)'" in body


def test_toggle_verhalten_v783(index_html):
    """Klick-Toggle (onToggle -> aktiv=!eff). v3.9.783 (LOHNRELEVANT, Sebastian freigegeben): der Toggle reicht
    den Abwesenheits-Ausschluss (!!ad[iso]) an _ezDayEff durch — ein Klick auf einen genehmigten Abwesenheitstag
    zaehlt ihn DAZU (aktiv=true, Override), statt ihn abzuwaehlen. Die Klick-Verdrahtung selbst bleibt gleich."""
    assert "var eff=_ezDayEff(dm[iso]||0,prevEntry,!!ad[iso]);var want=!eff;" in index_html
    blk = _ez_kalender_block(index_html)
    assert "onClick:clickable?function(){onToggle(iso);}:undefined" in blk


def test_riedmann_juli_unveraendert(index_html, node_exe, tmp_path):
    """RUECKWAERTSKOMPAT-BEWEIS (v777): OHNE absSet-Param rechnet _ezEffTage byte-genau wie vor v783 —
    8 Tage = 93,68 €, 2 weggeklickt -> 70,26 €. Der v783-Abwesenheits-Ausschluss greift erst mit absSet
    (siehe test_ez_kalender_v775.test_riedmann_juli_beispiel: mit absSet -> 7/81,97)."""
    js = _block(index_html) + _OK + u"""
var W='R', days={};
['2026-07-01','2026-07-02','2026-07-03','2026-07-06','2026-07-07','2026-07-08','2026-07-09','2026-07-10'].forEach(function(d){days[d]=8;});
var unkorr=_ezEffTage(days,{},W);
ok(unkorr.tage===8 && Math.abs(unkorr.sum-93.68)<1e-9,'8 Tage vorbelegt = 93,68');
var korr=_ezEffTage(days,{'R_2026-07-09':{aktiv:false},'R_2026-07-10':{aktiv:false}},W);
ok(korr.tage===6 && Math.abs(korr.sum-70.26)<1e-9,'2 weggeklickt -> 6 Tage = 70,26');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_rechnung_unberuehrt_pin(index_html):
    """Grenze: Satz 11,71 + _ezEffTage-Struktur (Union, tage*satz, kein Deckel) + _ezSet-Schreibweg bleiben.

    v3.9.783 (LOHNRELEVANT, Sebastian freigegeben): der _ezDayEff-Kern bekommt EINEN 3. Param absGenehmigt —
    an genehmigten Abwesenheitstagen entfaellt die Vorbelegung (LA 2740). Der Flag-Override und der Satz 11,71
    bleiben unveraendert; kein Deckel, kein zweiter Rechenpfad. Der alte byte-Pin (>6 ohne Ausschluss) ist
    bewusst abgeloest.
    """
    assert "taggeldAb6h:11.71" in index_html
    # _ezDayEff-Kern v783: Flag-Override zuerst, sonst (>6h) UND nicht genehmigt-abwesend
    assert ("if(flagEntry!=null&&flagEntry.aktiv!==undefined)return !!flagEntry.aktiv;\n"
            "  return ((parseFloat(std)||0)>6)&&!absGenehmigt;") in index_html
    # _ezEffTage-Kern unveraendert (Union aus daysMap + Flags, tage*satz, kein Deckel)
    ez_start = index_html.index("function _ezEffTage(")
    ez_body = index_html[ez_start:index_html.index("\n}", ez_start)]
    assert "return {tage:tage,sum:tage*s};" in ez_body
    assert "Math.min" not in ez_body
    # _ezSet-Schreibweg unveraendert
    assert "SB_REST+'/entfernungszulage_tage?on_conflict=worker_id,datum'" in index_html
