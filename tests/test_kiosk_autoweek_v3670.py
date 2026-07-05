"""v3.9.670 Lager-Display Auto-Sprung auf Folgewoche ab Fr 09:00 Europe/Vienna.

Pure Function kioskDisplayWeekOffset(now) -> 0|1 (Wiener Zeit via Intl, DST-sicher);
isoWof/isoWYof = argumentnehmende ISO-KW/-Jahr-Klone fuer das verschobene Datum.
Nur Kiosk (?screen=monteure|planung), normale WeekPlan-Ansicht unveraendert.
Heute (05.07.2026) ist Sonntag -> Offset 1 -> Kiosk zeigt KW28.
"""
import re
import json
from conftest import run_node_snippet


def _block(index_html):
    m = re.search(r"//@KIOSK-WEEK-START(.*?)//@KIOSK-WEEK-END", index_html, re.S)
    assert m, "KIOSK-WEEK-Block nicht gefunden"
    return m.group(1)


def _eval(node_exe, index_html, expr):
    snippet = _block(index_html) + "\nprocess.stdout.write(JSON.stringify((" + expr + ")))"
    return json.loads(run_node_snippet(node_exe, snippet))


def _off(node_exe, index_html, utc_args):
    return _eval(node_exe, index_html, "kioskDisplayWeekOffset(new Date(Date.UTC(" + utc_args + ")))")


# ── DST Juli (Wien = UTC+2) ──
def test_juli_freitag_grenze(node_exe, index_html):
    # Fr 03.07.2026: 09:00 Wien = 07:00 UTC -> 1 ; 08:59 Wien = 06:59 UTC -> 0 ; 09:01 -> 1
    assert _off(node_exe, index_html, "2026,6,3,7,0") == 1
    assert _off(node_exe, index_html, "2026,6,3,6,59") == 0
    assert _off(node_exe, index_html, "2026,6,3,7,1") == 1


# ── DST Jaenner (Wien = UTC+1) ──
def test_jaenner_freitag_grenze(node_exe, index_html):
    # Fr 02.01.2026: 09:00 Wien = 08:00 UTC -> 1 ; 08:59 Wien = 07:59 UTC -> 0
    assert _off(node_exe, index_html, "2026,0,2,8,0") == 1
    assert _off(node_exe, index_html, "2026,0,2,7,59") == 0


def test_wochentage(node_exe, index_html):
    # Do 02.07. 23:59 Wien = 21:59 UTC -> 0
    assert _off(node_exe, index_html, "2026,6,2,21,59") == 0
    # Sa 04.07. 12:00 Wien = 10:00 UTC -> 1
    assert _off(node_exe, index_html, "2026,6,4,10,0") == 1
    # So 05.07. 23:59 Wien = 21:59 UTC -> 1
    assert _off(node_exe, index_html, "2026,6,5,21,59") == 1
    # Mo 06.07. 00:00 Wien = So 22:00 UTC -> 0
    assert _off(node_exe, index_html, "2026,6,5,22,0") == 0


def test_isowof_jahres_rollover(node_exe, index_html):
    # today 28.12.2026 + 7 Tage = 04.01.2027 -> KW1 / 2027
    expr = "(function(){var d=new Date(2026,11,28);d.setDate(d.getDate()+7);return [isoWof(d),isoWYof(d)];})()"
    assert _eval(node_exe, index_html, expr) == [1, 2027]


# ── Wiring (String-Asserts) ──
def test_wiring_kOff_both_kiosks(index_html):
    assert index_html.count("const _kOff=kioskDisplayWeekOffset(new Date());") == 2  # WochenplanTafel + MonteurTafel


def test_wiring_label_from_shifted_date(index_html):
    assert "const kw=isoWof(today);const yr=isoWYof(today);" in index_html


def test_wiring_fetch_ranges_shifted(index_html):
    # Abwesenheits-RPC (WochenplanTafel) + globaler _kioskWeekRange (MonteurTafel-AS)
    assert index_html.count("x.setDate(x.getDate()+7*kioskDisplayWeekOffset(new Date()));") == 2


def test_wiring_badges(index_html):
    assert '"📋 Wochenplan · KW "+kw+(_kOff?"  ▶ nächste Woche":"")' in index_html
    assert '_kOff?h(\'span\',{style:{marginLeft:8,fontSize:14,fontWeight:800,color:\'#0ea5e9\'' in index_html
