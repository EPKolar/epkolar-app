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
    """Struktur-Pin (v3.9.785): lesbares Stufen-Label je Zustand (ausgeschrieben klein/mittel/groß)."""
    blk = _ez_kalender_block(index_html)
    assert "'✓ '+meta.label" in blk, "bestaetigte Stufe ausgeschrieben (✓ klein/mittel/groß)"
    assert "'klein (Vorschlag)'" in blk
    assert "'✕ keine'" in blk
    # der fruehere Mini-Punkt-Marker ist weg
    assert "mark='•'" not in blk, "Mini-Punkt '•' muss durch lesbares Label ersetzt sein"


def test_cell_heute_ring(index_html):
    """Heute-Ring-Pin: heutiges-Datum-Vergleich + Ring-Style sind im Code."""
    blk = _ez_kalender_block(index_html)
    assert "const _heute=_ezHeuteISO();" in blk, "Heute-Datum wird via _ezHeuteISO ermittelt"
    assert "var isToday=(iso===_heute);" in blk, "Kachel vergleicht ihr Datum mit heute"
    assert "boxShadow:isToday?('0 0 0 2px '+V.ac):'none'" in blk, "Akzent-Ring fuer heute fehlt"


def test_legende_vorhanden(index_html):
    """Optik: Legende-Zeile mit Farbchips (v3.9.785: klein/mittel/groß/Vorschlag/keine/Abwesenheit/Ring=heute)."""
    start = index_html.index("function KVZulagenReport(props){")
    body = index_html[start:index_html.index("function ", start + 10)]
    assert "'Ring = heute'" in body
    assert "'klein (Vorschlag)'" in body
    assert "'mittel'" in body and "'groß'" in body


def test_toggle_verhalten_v785(index_html):
    """Klick-Toggle v3.9.785: der Klick berechnet die naechste Stufe (_ezCycleNext), Verdrahtung onToggle bleibt."""
    assert "var next=_ezCycleNext(cur);" in index_html
    blk = _ez_kalender_block(index_html)
    assert "onClick:clickable?function(){onToggle(iso);}:undefined" in blk


def test_riedmann_juli_stufen(index_html, node_exe, tmp_path):
    """v3.9.785 (3-Stufen): 7 Anwesenheitstage klein x 11,94 = 83,58; per Flag mittel/gross hochgeschaltet.
    Die alten byte-Pins (Satz 11,71, {tage}) sind mit dem KV-Satz 11,94 + Stufen-Modell obsolet."""
    js = _block(index_html) + _OK + u"""
var W='R';var SA={klein:11.94,mittel:30.00,gross:62.04};
function days(n){var d={};for(var i=1;i<=n;i++){d['2026-07-'+String(i).padStart(2,'0')]=8;}return d;}
var a=_ezEffTage(days(7),{},W,SA);
ok(a.tageKlein===7 && Math.abs(a.sum-83.58)<1e-9,'7 klein = 83,58');
var b=_ezEffTage(days(7),{'R_2026-07-06':{stufe:'gross'},'R_2026-07-07':{stufe:'gross'}},W,SA);
ok(b.tageKlein===5 && b.tageGross===2 && Math.abs(b.sum-183.78)<1e-9,'5 klein + 2 gross = 183,78');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_rechnung_kern_v785(index_html):
    """Grenze v3.9.785: KV-Satz klein 11,94 + Stufen-Rechenstruktur (je Stufe*Satz, kein Deckel) + _ezSet-Schreibweg.

    Der _ezDayEff-Kern liefert die STUFE (Flag-Override gewinnt, genehmigte Abwesenheit -> kein Vorschlag). Die
    alten byte-Pins (Satz 11,71, bool-Rueckgabe, {tage:tage,sum:tage*s}) sind mit dem 3-Stufen-Umbau obsolet.
    """
    assert "taggeldAb6h:11.94" in index_html
    # _ezDayEff-Kern v785: Flag-Stufe-Override zuerst, sonst (>6h & nicht abwesend) -> Vorschlag 'klein'
    de = index_html[index_html.index("function _ezDayEff("):index_html.index("function _ezEffTage(")]
    assert "if(flagEntry!=null&&flagEntry.stufe!==undefined){" in de
    assert "(((parseFloat(std)||0)>6)&&!absGenehmigt)?'klein':''" in de
    # _ezEffTage: Summe je Stufe, kein Deckel
    ez_start = index_html.index("function _ezEffTage(")
    ez_body = index_html[ez_start:index_html.index("\n}", ez_start)]
    assert "return {tageKlein:tK,tageMittel:tM,tageGross:tG,sum:tK*sK+tM*sM+tG*sG};" in ez_body
    assert "Math.min" not in ez_body
    # _ezSet-Schreibweg (Upsert + Delete-Pfad)
    assert "SB_REST+'/entfernungszulage_tage?on_conflict=worker_id,datum'" in index_html
