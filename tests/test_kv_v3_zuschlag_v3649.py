"""v3.9.649 KV-V3 — Zuschlagslogik (Metallgewerbe), pure Funktionen (Node-eval).

Taegliche Naeherung + Kumulationssperre: Ue = Std ueber Tagesnorm; Mehrarbeit = erste
1,5h (Mehrarbeit-Faktor); Rest 50% ODER 100% (Nacht/So/Feiertag/3.Ue-nach-19), nur
hoechster Zuschlag. NUR Auswertung/Anspruchsfuehrung — Lohnverrechner massgeblich.
"""
import re
import json
from conftest import run_node_snippet

_RULES = "{mehrarbeitStd:1.5,zuschlagMehrarbeit:0.5,zuschlagUeStd:0.5,zuschlagUeStd100:1.0}"


def _block(index_html):
    m = re.search(r"//@KV-ZUSCHLAG-START(.*?)//@KV-ZUSCHLAG-END", index_html, re.S)
    assert m, "KV-ZUSCHLAG-Block nicht gefunden"
    return m.group(1)


def _eval(node_exe, index_html, expr):
    snippet = _block(index_html) + "\nprocess.stdout.write(JSON.stringify((" + expr + ")))"
    return json.loads(run_node_snippet(node_exe, snippet))


# ── Tagesnorm ──
def test_tagesnorm(node_exe, index_html):
    expr = ("_kvTagesnorm(1,false)===8.5 && _kvTagesnorm(4,false)===8.5 && _kvTagesnorm(5,false)===4.5"
            " && _kvTagesnorm(6,false)===0 && _kvTagesnorm(0,false)===0 && _kvTagesnorm(2,true)===0")
    assert _eval(node_exe, index_html, expr) is True


# ── Zuschlag: Werktag ohne 100% ──
def test_werktag_mehrarbeit(node_exe, index_html):
    # Mo 10h, Norm 8,5: 8,5 normal + 1,5 Mehrarbeit -> zuschlagStd 0,75
    r = _eval(node_exe, index_html, "_kvTagZuschlag(10,8.5,false," + _RULES + ")")
    assert r["normal"] == 8.5 and r["mehrarbeit"] == 1.5 and r["ue50"] == 0 and r["ue100"] == 0
    assert abs(r["zuschlagStd"] - 0.75) < 1e-9


def test_werktag_ue50(node_exe, index_html):
    # Mo 12h: 8,5 normal + 1,5 Mehrarbeit + 2 Ue50 -> 0,75 + 1,0 = 1,75
    r = _eval(node_exe, index_html, "_kvTagZuschlag(12,8.5,false," + _RULES + ")")
    assert r["mehrarbeit"] == 1.5 and r["ue50"] == 2 and r["ue100"] == 0
    assert abs(r["zuschlagStd"] - 1.75) < 1e-9


# ── Kumulationssperre: 100%-Tag ──
def test_hundert_kumulationssperre(node_exe, index_html):
    # Sa/So 6h, Norm 0, hundert=true: 1,5 Mehrarbeit(50%) + 4,5 Ue100 -> 0,75 + 4,5 = 5,25
    r = _eval(node_exe, index_html, "_kvTagZuschlag(6,0,true," + _RULES + ")")
    assert r["ue100"] == 4.5 and r["ue50"] == 0  # nur hoechster Zuschlag, nicht additiv
    assert abs(r["zuschlagStd"] - 5.25) < 1e-9


def test_hundert_false_gleiche_std(node_exe, index_html):
    # Gleiche 6h ohne 100%: 1,5 Mehrarbeit + 4,5 Ue50 -> 3,0
    r = _eval(node_exe, index_html, "_kvTagZuschlag(6,0,false," + _RULES + ")")
    assert r["ue50"] == 4.5 and r["ue100"] == 0
    assert abs(r["zuschlagStd"] - 3.0) < 1e-9


def test_keine_ueberstunden(node_exe, index_html):
    # 8h an Norm 8,5: kein Ue, kein Zuschlag
    r = _eval(node_exe, index_html, "_kvTagZuschlag(8,8.5,false," + _RULES + ")")
    assert r["normal"] == 8 and r["mehrarbeit"] == 0 and r["zuschlagStd"] == 0


# ── 100%-Trigger ──
def test_hundert_trigger(node_exe, index_html):
    expr = ("_kvHundert100(0,false,'','',0)===true"          # Sonntag
            " && _kvHundert100(2,true,'','',0)===true"        # Feiertag
            " && _kvHundert100(2,false,'','',5)===false"      # Di ohne Uhrzeit -> nicht ableitbar
            " && _kvHundert100(2,false,'22:00','23:30',1)===true"   # Nacht (>20:00)
            " && _kvHundert100(2,false,'04:00','08:00',1)===true"   # Nacht (<06:00)
            " && _kvHundert100(2,false,'19:30','23:00',3)===true"   # ab 3. Ue nach 19h
            " && _kvHundert100(2,false,'08:00','16:00',5)===false") # Tag ohne Nacht/19h
    assert _eval(node_exe, index_html, expr) is True


# ── UI-Wiring ──
def test_report_component(index_html):
    assert "function KVZuschlagReport(props)" in index_html


def test_report_gated(index_html):
    # v3.9.804: KVZuschlagReport (lohnsensibel) aus der staff-sichtbaren Auswertung ENTFERNT und ins
    # Chef-Portal/Personal verschoben (Chef-Portal-Gate = role admin ODER Geschaeftsfuehrer, Z.8517 ->
    # Monteure/Angestellte/Buero/PL sehen ihn NICHT). Strengeres Gate als vorher.
    assert "_canSeeVolume && React.createElement(KVZuschlagReport" not in index_html, \
        "KVZuschlagReport haengt noch in der staff-sichtbaren Auswertung"
    assert "_cdTab==='personal' && React.createElement(KVZuschlagReport, { entries: entries, monteure: monteure, ww: ww} )" in index_html, \
        "KVZuschlagReport nicht im admin/GF-gegateten Chef-Personal-Tab"


def test_report_lohnverrechner_hinweis(index_html):
    assert "Lohnverrechner maßgeblich" in index_html
