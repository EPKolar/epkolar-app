"""v3.9.638 Stempeluhr-Fundament — pure Auswertungs-Helper (Node-eval).

Extrahiert den Sentinel-Block STEMPEL-HELPERS-START..END aus index.html und
evaluiert die reinen Funktionen in Node. Kein DB-/Render-Zugriff.

Regel: stempel_log.ts ist roh; Rundung (5-min-Raster) + Pausenabzug NUR hier.
Rundung: Kommen AUF, Gehen AB. Abzug EINMAL pro Tag, nie negativ.
Pause rollenabhaengig aus rules (system_config 'stempel_pause_rules'),
Fallback {buero:0, default:60}.
"""
import re
import json
import pytest
from conftest import run_node_snippet


def _helpers(index_html):
    m = re.search(r"//@STEMPEL-HELPERS-START(.*?)//@STEMPEL-HELPERS-END", index_html, re.S)
    assert m, "STEMPEL-HELPERS-Block nicht gefunden (Sentinel-Kommentare fehlen)"
    return m.group(1)


def _eval(node_exe, index_html, expr):
    snippet = _helpers(index_html) + "\nprocess.stdout.write(JSON.stringify((" + expr + ")))"
    return json.loads(run_node_snippet(node_exe, snippet))


# ── Rundung beide Richtungen: 07:00 / 07:01 / 07:04 / 07:05 (UTC-basiert, TZ-frei) ──
def test_round_kommen_auf(node_exe, index_html):
    expr = ("_stRoundKommen(Date.UTC(2026,0,15,7,0))===Date.UTC(2026,0,15,7,0)"
            "&&_stRoundKommen(Date.UTC(2026,0,15,7,1))===Date.UTC(2026,0,15,7,5)"
            "&&_stRoundKommen(Date.UTC(2026,0,15,7,4))===Date.UTC(2026,0,15,7,5)"
            "&&_stRoundKommen(Date.UTC(2026,0,15,7,5))===Date.UTC(2026,0,15,7,5)")
    assert _eval(node_exe, index_html, expr) is True


def test_round_gehen_ab(node_exe, index_html):
    expr = ("_stRoundGehen(Date.UTC(2026,0,15,7,0))===Date.UTC(2026,0,15,7,0)"
            "&&_stRoundGehen(Date.UTC(2026,0,15,7,1))===Date.UTC(2026,0,15,7,0)"
            "&&_stRoundGehen(Date.UTC(2026,0,15,7,4))===Date.UTC(2026,0,15,7,0)"
            "&&_stRoundGehen(Date.UTC(2026,0,15,7,5))===Date.UTC(2026,0,15,7,5)")
    assert _eval(node_exe, index_html, expr) is True


# ── Netto: Buero (2 Paare, kein Abzug) vs. Feld (Abzug) ──
_BUERO_2P = ("[{kommen:Date.UTC(2026,0,15,7,0),gehen:Date.UTC(2026,0,15,12,0)},"
             "{kommen:Date.UTC(2026,0,15,13,0),gehen:Date.UTC(2026,0,15,17,0)}]")
_FELD_1P = "[{kommen:Date.UTC(2026,0,15,7,0),gehen:Date.UTC(2026,0,15,17,0)}]"
_FELD_2P = _BUERO_2P
_RULES = "{buero:0,default:60}"


def test_netto_buero_zwei_paare_kein_abzug(node_exe, index_html):
    # 5h + 4h = 9h = 540min, Buero-Abzug 0
    assert _eval(node_exe, index_html, "_stTagNetto(" + _BUERO_2P + ",'buero'," + _RULES + ")") == 540


def test_netto_feld_ein_paar_minus_pause(node_exe, index_html):
    # 10h = 600min - 60 = 540min
    assert _eval(node_exe, index_html, "_stTagNetto(" + _FELD_1P + ",'monteur'," + _RULES + ")") == 540


def test_netto_feld_zwei_paare_abzug_nur_einmal(node_exe, index_html):
    # 9h brutto - 60 (EINMAL) = 480min  (nicht 2x abgezogen)
    assert _eval(node_exe, index_html, "_stTagNetto(" + _FELD_2P + ",'monteur'," + _RULES + ")") == 480


def test_netto_kurztag_unter_pause_wird_null(node_exe, index_html):
    # 30min brutto - 60 -> max(0,...) = 0
    kurz = "[{kommen:Date.UTC(2026,0,15,7,0),gehen:Date.UTC(2026,0,15,7,30)}]"
    assert _eval(node_exe, index_html, "_stTagNetto(" + kurz + ",'monteur'," + _RULES + ")") == 0


# ── Toggle-Richtung ──
def test_toggle_dir(node_exe, index_html):
    expr = ("_stNextDir('kommen')==='gehen'"
            "&&_stNextDir('gehen')==='kommen'"
            "&&_stNextDir(null)==='kommen'"
            "&&_stNextDir(undefined)==='kommen'")
    assert _eval(node_exe, index_html, expr) is True


# ── rules-Lookup (Rolle vorhanden / faellt auf default / rules leer -> 60 / buero=0 via Konfig) ──
def test_pause_lookup_rolle_vorhanden(node_exe, index_html):
    assert _eval(node_exe, index_html, "_stPauseAbzug('monteur',{monteur:60,default:60})") == 60


def test_pause_lookup_faellt_auf_default(node_exe, index_html):
    assert _eval(node_exe, index_html, "_stPauseAbzug('xyz',{default:45})") == 45


def test_pause_lookup_leer_ergibt_60(node_exe, index_html):
    assert _eval(node_exe, index_html, "_stPauseAbzug('monteur',{})") == 60


def test_pause_lookup_buero_null_via_konfig(node_exe, index_html):
    assert _eval(node_exe, index_html, "_stPauseAbzug('buero',{buero:0,default:60})") == 0
