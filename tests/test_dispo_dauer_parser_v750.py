# -*- coding: utf-8 -*-
"""v3.9.750 — Register #29a (P1, live-verifiziert): Dauer-Parser robust — HH:MM:SS aus OFFA/DB.

Sebastian/Chat-Claude: _dispoDauer parste '02:30' (->150) aber NICHT '02:30:00' (->90/geschätzt). OFFA/DB
liefert HH:MM:SS. Fix: EIN Parser _dispoParseDauer für 'HH:MM:SS'/'HH:MM'/'H:MM' (Sekunden ignorieren,
führende Nullen egal); Unparsbares -> null -> Keyword/Default mit geschaetzt:true. Damit stimmen Chip-Dauer
UND alle kumulierten Endzeiten (07:00–09:30 statt –08:30). Eine gesetzte dauer schlägt IMMER jede Schätzung.
"""
import subprocess


def _block(index_html):
    start = index_html.index("var DISPO_RESERVE_MIN=60;")
    end = index_html.index("if(typeof window!=='undefined'){window._dispoAdrKey", start)
    return index_html[start:end]


_OK = u"\nfunction ok(c,n){ if(!c){ console.error('FAIL '+n); process.exit(1);} }\n"


def _run(node_exe, tmp_path, js):
    f = tmp_path / "dauer750.js"
    f.write_text(js, encoding="utf-8")
    r = subprocess.run([node_exe, str(f)], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")
    assert "OK" in r.stdout


def test_parse_hhmmss(index_html, node_exe, tmp_path):
    js = _block(index_html) + _OK + u"""
ok(_dispoParseDauer('02:30:00')===150,'HH:MM:SS -> 150 (Sekunden ignoriert)');
ok(_dispoParseDauer('02:30')===150,'HH:MM -> 150');
ok(_dispoParseDauer('2:30')===150,'H:MM -> 150');
ok(_dispoParseDauer('01:00:00')===60,'01:00:00 -> 60');
ok(_dispoParseDauer('')===null,'leer -> null');
ok(_dispoParseDauer('Unfug')===null,'unparsbar -> null');
ok(_dispoParseDauer('00:00:00')===null,'00:00:00 -> null (keine echte Dauer)');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_dispodauer_gesetzt_schlaegt_schaetzung(index_html, node_exe, tmp_path):
    js = _block(index_html) + _OK + u"""
var r=_dispoDauer({dauer:'02:30:00',arbeitsanweisungen:'Steckdose'});
ok(r.min===150,'gesetzte Dauer 02:30:00 -> 150 (nicht 60 Keyword)');
ok(r.geschaetzt===false,'gesetzte Dauer ist NICHT geschaetzt');
var r2=_dispoDauer({dauer:'',arbeitsanweisungen:'Steckdose tauschen'});
ok(r2.geschaetzt===true,'leere Dauer -> Keyword/Default, geschaetzt');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_ein_parser_keine_kopien(index_html):
    # 29c: _dispoDauer nutzt _dispoParseDauer (kein eigenes HH:MM-Regex mehr im Body).
    i = index_html.index("function _dispoDauer(")
    body = index_html[i:i + 400]
    assert "_dispoParseDauer(" in body, "_dispoDauer nutzt den zentralen Parser nicht"
