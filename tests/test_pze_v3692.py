"""v3.9.692 PZE — Personalzeiterfassung fuers Buero (Rechenkern, Node-Eval).

Testet den Sentinel-Block //@PZE-START..END aus index.html. Der Block ist reine JS-Logik
(window-scope, kein optional chaining) und haengt fuer die Auswertung von zwei fremden
Bloecken ab:
  - //@STEMPEL-HELPERS-START..END liefert _stPairEvents/_stTagNetto/_stRoundKommen/_stRoundGehen
    (Rundung 5-min-Raster: Kommen AUF, Gehen AB; Pausenabzug einmal/Tag, nie negativ).
  - die Zeilen `const isoWof=...`/`const isoWYof=...` (ISO-Kalenderwoche) fuer _pzeKW.
Alle drei Fragmente werden per Regex extrahiert und gemeinsam in Node evaluiert.

DOMAENEN-REGEL (Sebastian, verbindlich): stempel_log = Anwesenheit = Wahrheit dieser Ansicht;
time_entries = Projektzeit = neutrale Info-Spalte. Rueckgaben in Minuten.
"""
import re
import json
import pytest
from conftest import run_node_snippet


def _stempel_block(index_html):
    m = re.search(r"//@STEMPEL-HELPERS-START(.*?)//@STEMPEL-HELPERS-END", index_html, re.S)
    assert m, "STEMPEL-HELPERS-Block nicht gefunden"
    return m.group(1)


def _pze_block(index_html):
    m = re.search(r"//@PZE-START(.*?)//@PZE-END", index_html, re.S)
    assert m, "PZE-Block nicht gefunden"
    return m.group(1)


def _iso_wof_lines(index_html):
    m1 = re.search(r"^const isoWof=.*$", index_html, re.M)
    m2 = re.search(r"^const isoWYof=.*$", index_html, re.M)
    assert m1 and m2, "isoWof/isoWYof-Zeilen nicht gefunden"
    return m1.group(0) + "\n" + m2.group(0)


def _bundle(index_html):
    return (
        _stempel_block(index_html)
        + "\n"
        + _iso_wof_lines(index_html)
        + "\n"
        + _pze_block(index_html)
    )


def _eval(node_exe, index_html, expr):
    snippet = _bundle(index_html) + "\nprocess.stdout.write(JSON.stringify((" + expr + ")))"
    return json.loads(run_node_snippet(node_exe, snippet))


_RULES = "{Backoffice:0,default:60}"


# ═══════════════════════════════════════════════════════════════════
# 1) _pzeGroupByDay — LOKALER Kalendertag, nicht UTC
# ═══════════════════════════════════════════════════════════════════
def test_group_by_day_23_30_ortszeit_bleibt_am_selben_tag(node_exe, index_html):
    # 23:30 Wien-Ortszeit (Winter, UTC+1) am 15.01.2026 -> muss unter '2026-01-15' landen,
    # NICHT unter '2026-01-16' (waere der Fehler, wenn man faelschlich einen Tag draufschlaegt).
    events = "[{direction:'gehen',ts:'2026-01-15T23:30:00+01:00'}]"
    out = _eval(node_exe, index_html, "_pzeGroupByDay(" + events + ")")
    assert list(out.keys()) == ["2026-01-15"]
    assert len(out["2026-01-15"]) == 1


def test_group_by_day_utc_rollover_wird_lokal_korrigiert(node_exe, index_html, monkeypatch):
    # 23:45 UTC am 14.01. entspricht 00:45 Wien am 15.01. (Winter, UTC+1) -> gehoert LOKAL
    # zum 15., waere bei naiver getUTCDate()-Gruppierung faelschlich noch am 14.
    # _pzeGroupByDay nutzt LOKALE Date-Methoden -> das Ergebnis haengt an der TZ des Node-Prozesses.
    # Ohne Pin gruen nur auf UTC+-Maschinen (Wien), rot auf UTC/US (CI). TZ hart auf Wien pinnen:
    # run_node_snippet erbt os.environ; Node liest process.env.TZ (auch unter Windows).
    monkeypatch.setenv("TZ", "Europe/Vienna")
    events = (
        "[{direction:'kommen',ts:'2026-01-14T23:45:00Z'},"
        "{direction:'gehen',ts:'2026-01-15T08:00:00Z'}]"
    )
    out = _eval(node_exe, index_html, "_pzeGroupByDay(" + events + ")")
    assert list(out.keys()) == ["2026-01-15"]
    assert len(out["2026-01-15"]) == 2


def test_group_by_day_sortiert_je_tag_zeitlich(node_exe, index_html):
    events = (
        "[{direction:'gehen',ts:'2026-01-15T16:00:00+01:00'},"
        "{direction:'kommen',ts:'2026-01-15T07:00:00+01:00'}]"
    )
    out = _eval(node_exe, index_html, "_pzeGroupByDay(" + events + ")")
    day = out["2026-01-15"]
    assert [e["direction"] for e in day] == ["kommen", "gehen"]


# ═══════════════════════════════════════════════════════════════════
# 2) _pzeUngerade — 0 Stempel ist KEIN Fehler (Abwesenheit)
# ═══════════════════════════════════════════════════════════════════
def test_ungerade_zwei_stempel_false(node_exe, index_html):
    evs = "[{direction:'kommen',ts:'x'},{direction:'gehen',ts:'y'}]"
    assert _eval(node_exe, index_html, "_pzeUngerade(" + evs + ")") is False


def test_ungerade_drei_stempel_true(node_exe, index_html):
    evs = "[{direction:'kommen',ts:'x'},{direction:'gehen',ts:'y'},{direction:'kommen',ts:'z'}]"
    assert _eval(node_exe, index_html, "_pzeUngerade(" + evs + ")") is True


def test_ungerade_null_stempel_false_abwesenheit_kein_fehler(node_exe, index_html):
    assert _eval(node_exe, index_html, "_pzeUngerade([])") is False
    assert _eval(node_exe, index_html, "_pzeUngerade(null)") is False


# ═══════════════════════════════════════════════════════════════════
# 3) _pzeTagRow — Tages-Saldo
# ═══════════════════════════════════════════════════════════════════
def test_tagrow_montag_normaler_tag_saldo_minus_30(node_exe, index_html):
    evs = (
        "[{direction:'kommen',ts:'2026-01-12T07:00:00+01:00'},"
        "{direction:'gehen',ts:'2026-01-12T16:00:00+01:00'}]"
    )
    row = _eval(
        node_exe, index_html,
        "_pzeTagRow(" + evs + ",'monteur'," + _RULES + ",8.5,0)"
    )
    assert row["bruttoMin"] == 540  # 9h
    assert row["pauseMin"] == 60
    assert row["nettoMin"] == 480
    assert row["sollMin"] == 510  # 8.5*60
    assert row["saldoMin"] == -30
    assert row["ungerade"] is False
    assert row["stempelAnzahl"] == 2


def test_tagrow_freitag_soll_270(node_exe, index_html):
    evs = (
        "[{direction:'kommen',ts:'2026-01-16T07:00:00+01:00'},"
        "{direction:'gehen',ts:'2026-01-16T11:30:00+01:00'}]"
    )
    row = _eval(
        node_exe, index_html,
        "_pzeTagRow(" + evs + ",'monteur'," + _RULES + ",4.5,0)"
    )
    assert row["sollMin"] == 270


def test_tagrow_feiertag_soll_0_saldo_gleich_netto(node_exe, index_html):
    evs = (
        "[{direction:'kommen',ts:'2026-01-06T08:00:00+01:00'},"
        "{direction:'gehen',ts:'2026-01-06T09:00:00+01:00'}]"
    )
    row = _eval(
        node_exe, index_html,
        "_pzeTagRow(" + evs + ",'Backoffice'," + _RULES + ",0,0)"
    )
    assert row["sollMin"] == 0
    assert row["saldoMin"] == row["nettoMin"]
    assert row["nettoMin"] == 60  # 1h, Backoffice-Pause=0


def test_tagrow_pause_spalte_zeigt_tatsaechlich_angewandten_abzug(node_exe, index_html):
    """Kurztag Kommen 08:00 / Gehen 08:30 (30min brutto), default-Pause waere 60 —
    _stTagNetto kappt bei max(0,...) auf 0. Die Pause-Spalte muss den TATSAECHLICH
    angewandten Abzug zeigen (30), nicht den Regelwert (60)."""
    evs = (
        "[{direction:'kommen',ts:'2026-01-12T08:00:00+01:00'},"
        "{direction:'gehen',ts:'2026-01-12T08:30:00+01:00'}]"
    )
    row = _eval(
        node_exe, index_html,
        "_pzeTagRow(" + evs + ",'monteur'," + _RULES + ",8.5,0)"
    )
    assert row["bruttoMin"] == 30
    assert row["nettoMin"] == 0
    assert row["pauseMin"] == 30  # nicht 60!


def test_tagrow_rundungsrichtung_fliesst_ein(node_exe, index_html):
    """Kommen 07:02 -> AUF auf 07:05, Gehen 15:58 -> AB auf 15:55 (zulasten des Monteurs).
    Direkt an den Rundungs-Helpern und ueber den Brutto-Wert von _pzeTagRow geprueft."""
    assert _eval(
        node_exe, index_html,
        "_stRoundKommen(Date.UTC(2026,0,12,7,2))===Date.UTC(2026,0,12,7,5)"
    ) is True
    assert _eval(
        node_exe, index_html,
        "_stRoundGehen(Date.UTC(2026,0,12,15,58))===Date.UTC(2026,0,12,15,55)"
    ) is True

    evs = (
        "[{direction:'kommen',ts:'2026-01-12T07:02:00+01:00'},"
        "{direction:'gehen',ts:'2026-01-12T15:58:00+01:00'}]"
    )
    row = _eval(
        node_exe, index_html,
        "_pzeTagRow(" + evs + ",'Backoffice'," + _RULES + ",8.5,0)"
    )
    # 07:05 -> 15:55 = 8h50min = 530min (nicht 8h56min aus den rohen Stempeln)
    assert row["bruttoMin"] == 530


# ═══════════════════════════════════════════════════════════════════
# 4) _pzeSummen
# ═══════════════════════════════════════════════════════════════════
def test_summen_ueber_mehrere_tage(node_exe, index_html):
    rows = (
        "[{nettoMin:480,sollMin:510,saldoMin:-30,projMin:400,pauseMin:60},"
        "{nettoMin:270,sollMin:270,saldoMin:0,projMin:250,pauseMin:0},"
        "{nettoMin:0,sollMin:0,saldoMin:0,projMin:0,pauseMin:0}]"
    )
    s = _eval(node_exe, index_html, "_pzeSummen(" + rows + ")")
    assert s == {
        "nettoMin": 750,
        "sollMin": 780,
        "saldoMin": -30,
        "projMin": 650,
        "pauseMin": 60,
        "krankMin": 0,  # v3.9.770: additives Feld, ohne Krank-Tage 0
    }


def test_summen_leer_ist_alles_null(node_exe, index_html):
    s = _eval(node_exe, index_html, "_pzeSummen([])")
    assert s == {"nettoMin": 0, "sollMin": 0, "saldoMin": 0, "projMin": 0, "pauseMin": 0, "krankMin": 0}  # v3.9.770


# ═══════════════════════════════════════════════════════════════════
# 5) _pzeFmtHm
# ═══════════════════════════════════════════════════════════════════
def test_fmt_hm_negativ_mit_vorzeichen(node_exe, index_html):
    assert _eval(node_exe, index_html, "_pzeFmtHm(-75)") == "-1:15"


def test_fmt_hm_positiv_ohne_vorzeichen(node_exe, index_html):
    assert _eval(node_exe, index_html, "_pzeFmtHm(510)") == "8:30"


# ══════════════════════════════════════════════════════════════════════════════
# v3.9.692 Fink-Semantik (Nachtrag Sebastian 14.07.)
# Gutschrift, Fehltag und Auto-Pause. Das sind KEINE Optik-Themen — sie veraendern
# den Tages-Saldo und damit die Monatssumme.
# ══════════════════════════════════════════════════════════════════════════════
_MO = "Date.UTC(2026,0,12,{h},{m})"  # Montag, 12.01.2026


def test_gutschrift_genehmigte_abwesenheit_erfuellt_das_soll(node_exe, index_html):
    """Fink schreibt einen genehmigten Krank-/Urlaubstag als erfuellt gut:
    Gesamt = Soll, Saldo 0. Ohne diese Regel wuerde jeder Urlaubstag als -8:30 zaehlen
    und der Monatssaldo waere fuer jeden Urlauber tief negativ."""
    expr = ("(function(){var r=_pzeTagRow([],'monteur',{Backoffice:0,default:60},8.5,0,true);"
            "return [r.nettoMin,r.sollMin,r.saldoMin,r.gutschrift,r.fehltag];})()")
    assert _eval(node_exe, index_html, expr) == [510, 510, 0, True, False]


def test_nur_beantragt_bekommt_keine_gutschrift(node_exe, index_html):
    """Ein Antrag ist noch keine Abwesenheit — absGutschrift=false -> Fehltag, voller Minus-Saldo."""
    expr = ("(function(){var r=_pzeTagRow([],'monteur',{Backoffice:0,default:60},8.5,0,false);"
            "return [r.nettoMin,r.saldoMin,r.gutschrift,r.fehltag];})()")
    assert _eval(node_exe, index_html, expr) == [0, -510, False, True]


def test_stempel_schlaegt_gutschrift(node_exe, index_html):
    """Wer trotz genehmigtem Urlaub stempelt, war da. Dann zaehlt der Stempel, nicht die
    Gutschrift — Anwesenheit schlaegt Planung."""
    expr = ("(function(){var evs=[{direction:'kommen',ts:" + _MO.format(h=7, m=0) + "},"
            "{direction:'gehen',ts:" + _MO.format(h=16, m=0) + "}];"
            "var r=_pzeTagRow(evs,'monteur',{Backoffice:0,default:60},8.5,0,true);"
            "return [r.nettoMin,r.gutschrift];})()")
    # 07:00-16:00 = 540 brutto, -60 Pause = 480 netto. NICHT 510 (das waere die Gutschrift).
    assert _eval(node_exe, index_html, expr) == [480, False]


def test_fehltag_nur_an_werktagen(node_exe, index_html):
    """Sa/So/Feiertag haben Soll 0 -> kein Fehltag, kein roter Marker."""
    expr = ("(function(){var r=_pzeTagRow([],'monteur',{Backoffice:0,default:60},0,0,false);"
            "return [r.fehltag,r.saldoMin];})()")
    assert _eval(node_exe, index_html, expr) == [False, 0]


def test_auto_pause_liegt_in_der_tagesmitte(node_exe, index_html):
    """Der Pausenabzug ist eine REGEL, kein Stempel. Wir legen ihn nominal mittig und
    zeigen ihn grau — er darf nie wie eine echte Stempelzeit aussehen."""
    expr = ("(function(){var evs=[{direction:'kommen',ts:" + _MO.format(h=7, m=0) + "},"
            "{direction:'gehen',ts:" + _MO.format(h=17, m=0) + "}];"
            "var r=_pzeTagRow(evs,'monteur',{Backoffice:0,default:60},8.5,0,false);"
            "var p=r.autoPause;"
            "return [(p.bis-p.von)/60000, new Date(p.von).getUTCHours(), new Date(p.bis).getUTCHours()];})()")
    # 07:00-17:00, Mitte 12:00, Pause 60min -> 11:30-12:30
    dauer, von_h, bis_h = _eval(node_exe, index_html, expr)
    assert dauer == 60
    assert von_h == 11 and bis_h == 12


def test_keine_auto_pause_ohne_abzug(node_exe, index_html):
    """Backoffice hat 0 Minuten Abzug -> keine graue Pausenzeile."""
    expr = ("(function(){var evs=[{direction:'kommen',ts:" + _MO.format(h=8, m=0) + "},"
            "{direction:'gehen',ts:" + _MO.format(h=16, m=0) + "}];"
            "var r=_pzeTagRow(evs,'Backoffice',{Backoffice:0,default:60},8.5,0,false);"
            "return [r.pauseMin,r.autoPause];})()")
    assert _eval(node_exe, index_html, expr) == [0, None]


def test_gutschrift_taucht_nicht_bei_soll_null_auf(node_exe, index_html):
    """Genehmigter Urlaub an einem Feiertag darf keine Stunden gutschreiben."""
    expr = ("(function(){var r=_pzeTagRow([],'monteur',{Backoffice:0,default:60},0,0,true);"
            "return [r.gutschrift,r.nettoMin,r.saldoMin];})()")
    assert _eval(node_exe, index_html, expr) == [False, 0, 0]


# ══════════════════════════════════════════════════════════════════════════════
# v3.9.700 Bug-Hunt Befund 5 — Doppel-Kommen wird erkannt
# Vorher prüfte _pzeUngerade nur die ANZAHL (n%2===1). Zwei gleichgerichtete Stempel
# (2× Kommen, Doppelscan ohne Auschecken) sind GERADE und fielen durch die Fehler-Queue
# UND die Fehltag-Markierung -> stiller -8:30-Tag. Jetzt: paart _stPairEvents nicht alle
# Events sauber weg, ist der Tag inkonsistent.
# ══════════════════════════════════════════════════════════════════════════════
_MO5 = "'2026-01-12T{h}:{m}:00'"  # Montag


def test_zwei_kommen_wird_als_inkonsistent_erkannt(node_exe, index_html):
    expr = ("(function(){var evs=[{direction:'kommen',ts:" + _MO5.format(h='07', m='00') + "},"
            "{direction:'kommen',ts:" + _MO5.format(h='07', m='05') + "}];"
            "return _pzeUngerade(evs);})()")
    assert _eval(node_exe, index_html, expr) is True, \
        "2× Kommen (gerade Anzahl) muss jetzt als inkonsistent geflaggt werden"


def test_sauberes_paar_ist_nicht_inkonsistent(node_exe, index_html):
    expr = ("(function(){var evs=[{direction:'kommen',ts:" + _MO5.format(h='07', m='00') + "},"
            "{direction:'gehen',ts:" + _MO5.format(h='16', m='00') + "}];"
            "return _pzeUngerade(evs);})()")
    assert _eval(node_exe, index_html, expr) is False


def test_ungerade_anzahl_bleibt_inkonsistent(node_exe, index_html):
    expr = ("(function(){var evs=[{direction:'kommen',ts:" + _MO5.format(h='07', m='00') + "},"
            "{direction:'gehen',ts:" + _MO5.format(h='12', m='00') + "},"
            "{direction:'kommen',ts:" + _MO5.format(h='13', m='00') + "}];"
            "return _pzeUngerade(evs);})()")
    assert _eval(node_exe, index_html, expr) is True


def test_null_stempel_ist_kein_fehler(node_exe, index_html):
    """Abwesenheit (0 Stempel) darf NIE als inkonsistent gelten."""
    assert _eval(node_exe, index_html, "_pzeUngerade([])") is False


def test_zwei_saubere_paare_sind_konsistent(node_exe, index_html):
    expr = ("(function(){var evs=[{direction:'kommen',ts:" + _MO5.format(h='07', m='00') + "},"
            "{direction:'gehen',ts:" + _MO5.format(h='12', m='00') + "},"
            "{direction:'kommen',ts:" + _MO5.format(h='13', m='00') + "},"
            "{direction:'gehen',ts:" + _MO5.format(h='16', m='00') + "}];"
            "return _pzeUngerade(evs);})()")
    assert _eval(node_exe, index_html, expr) is False
