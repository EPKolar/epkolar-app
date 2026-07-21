# -*- coding: utf-8 -*-
"""v3.9.787 — AS-Eskalation prueft den Termin (live-Bug S075377, Sebastian 21.07.2026).

Bug: S075377 (FIXTERMIN, terminBestaetigt=heute) zeigte "Eskalation: dringend, seit 4 Tagen unbearbeitet",
obwohl heute terminiert. Der Eskalations-Filter (_checkAutoNotifs) prueft nur AS_GRP_OFFEN + _asIsUrgentPrio +
Alter seit aufgenommen, NICHT terminBestaetigt. Fix: PURE _asEskalierbar spiegelt die Dispo-v727-offen-Logik —
nur kein-Termin ODER ueberfaelliger Termin (<heute Wien) eskaliert; terminBestaetigt>=heute = eingeplant;
aufgeschoben ausgenommen; Sentinel 0001-01-01 zaehlt nicht als Termin.
"""
import re
import subprocess


def _extract(index_html):
    ht = re.search(r"const _hasTermin = t => [^;]+;", index_html).group(0)
    i = index_html.index("function _asEskalierbar(a,heuteISO){")
    j = index_html.index("\n}", i) + 2
    return ht + "\n" + index_html[i:j]


def _run(node_exe, tmp_path, js):
    f = tmp_path / "esk787.js"
    f.write_text(js, encoding="utf-8")
    r = subprocess.run([node_exe, str(f)], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")
    assert "ALL-OK" in r.stdout


def test_aseskalierbar_pure(index_html, node_exe, tmp_path):
    js = _extract(index_html) + u"""
function ok(c,n){ if(!c){ console.error('FAIL '+n); process.exit(1);} }
var H='2026-07-21';
ok(_asEskalierbar({scheinstatus:'in_bearbeitung',terminBestaetigt:'2026-07-21'},H)===false,'Heute-Termin -> keine Eskalation (S075377)');
ok(_asEskalierbar({scheinstatus:'freigegeben',terminBestaetigt:'2026-07-25'},H)===false,'Zukunfts-Termin -> keine Eskalation');
ok(_asEskalierbar({scheinstatus:'in_bearbeitung',terminBestaetigt:'2026-07-18'},H)===true,'ueberfaelliger Termin -> Eskalation bleibt');
ok(_asEskalierbar({scheinstatus:'aufgenommen',terminBestaetigt:''},H)===true,'kein Termin -> eskalierbar (alter-basiert)');
ok(_asEskalierbar({scheinstatus:'aufgenommen',terminBestaetigt:'0001-01-01'},H)===true,'Sentinel 0001-01-01 = kein Termin');
ok(_asEskalierbar({scheinstatus:'aufgeschoben',terminBestaetigt:''},H)===false,'aufgeschoben ausgenommen');
ok(_asEskalierbar({scheinstatus:'aufgeschoben',terminBestaetigt:'2026-07-18'},H)===false,'aufgeschoben auch ueberfaellig ausgenommen');
ok(_asEskalierbar({scheinstatus:'in_bearbeitung',termin_bestaetigt:'2026-07-21'},H)===false,'snake termin_bestaetigt=heute');
console.log('ALL-OK');
"""
    _run(node_exe, tmp_path, js)


def test_filter_nutzt_aseskalierbar(index_html):
    """Der AS-Eskalations-Filter reicht die Termin-Pruefung durch (_asEskalierbar), Wiener Heute via _ezHeuteISO."""
    assert "var _eskHeute=_ezHeuteISO();" in index_html, "Wiener Heute-Datum als Eskalations-Referenz"
    assert "AS_GRP_OFFEN.includes(a.scheinstatus)&&(_asIsUrgentPrio(a.prioritaet))&&_asEskalierbar(a,_eskHeute)" in index_html, \
        "Eskalations-Filter muss _asEskalierbar einbeziehen"


def test_sentinel_und_aufgeschoben_im_helfer(index_html):
    """_asEskalierbar nutzt den Sentinel-Guard _hasTermin und nimmt aufgeschoben aus (Dispo-Parity)."""
    i = index_html.index("function _asEskalierbar(a,heuteISO){")
    body = index_html[i:index_html.index("\n}", i)]
    assert "if(a.scheinstatus==='aufgeschoben')return false;" in body
    assert "_hasTermin(tb)?String(tb).slice(0,10):" in body
    assert "(!tb)||(tb<String(heuteISO||\"\"))" in body


def test_window_export(index_html):
    assert "window._asEskalierbar=_asEskalierbar" in index_html


def test_eskalationsschwelle_vereinheitlicht(index_html):
    """v3.9.787 (Sebastian): _eskTage IMMER 14 (Erinnerung davor, Eskalation ab 14). Der v3.9.564-Sonderfall
    FIXTERMIN/sehr hoch = 3 Tage faellt weg — FIXTERMIN wird jetzt ueber _asEskalierbar (Termin) gesteuert."""
    assert "const _eskTage=14;" in index_html, "Eskalations-Schwelle nicht auf einheitlich 14 Tage"
    assert '["sehr hoch","fixtermin"].includes(String(a.prioritaet||"").toLowerCase())?3:14' not in index_html, \
        "alter v564-Sonderfall (3/14) muss weg sein"
    # beide Zweige (Eskalation dAlt>=_eskTage UND Reminder hAlt>=24) sind durch den Filter (_asEskalierbar) gegated
    esk = index_html[index_html.index("_arbeitsscheine.filter(a=>AS_GRP_OFFEN.includes(a.scheinstatus)"):]
    esk = esk[:esk.index("});")]
    assert "_asEskalierbar(a,_eskHeute)" in esk and "dAlt>=_eskTage" in esk and "hAlt>=24" in esk, \
        "Filter muss VOR beiden Zweigen (Eskalation+Reminder) greifen"
