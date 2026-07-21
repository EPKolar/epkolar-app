# -*- coding: utf-8 -*-
"""v3.9.797 — Auftragstyp/scheinart: Inline-Edit in der AS-Liste + Push nach OFFA.

TEIL A: zwei Inline-Selects (Prioritaet, Auftragstyp=scheinart) in der Liste nach dem
        woertlichen SB/Monteur/Status-Muster; Mobile-Chips in der Karte.
TEIL B: scheinart wird push-faehig (AK_AUFART in JUPROWA_PUSH_FIELDS) + Reverse-Map +
        Dirty-Check im Builder nach WOERTLICHEM v3.9.615/v3.9.570-Muster (Roundtrip-stabil).
        Pull-Update-Block (Z.~3555) bekommt den !isPending-Guard (uebersteht den Pull).

PUSH-SCHUTZ: der Push-Pfad aendert sich AUSSCHLIESSLICH um (a) EINEN PUSH_FIELDS-Eintrag +
(b) EINEN Dirty-Check-Block. _juprowaPush-Signatur byte-identisch. ROUNDTRIP-BEWEIS unten:
ein Edit eines ANDEREN Felds (notizen) bei AK_AUFART=3 echot die 3 (kein stilles 3->1).
"""
import json
import pytest
from conftest import run_node_snippet


def _call(node_exe, fn_bundle, schein_js):
    snippet = fn_bundle + f";process.stdout.write(JSON.stringify(_juprowaReversMap({schein_js})))"
    return json.loads(run_node_snippet(node_exe, snippet))


# ── ROUNDTRIP-BEWEIS (Pflicht, v583/v615-Testtyp) ──────────────────────────────
def test_roundtrip_kein_stilles_umschreiben(node_exe, fn_juprowa_reverse_map):
    # Regie-/Reparatur-Schein: gepullter Roh-AK_AUFART=3, App-scheinart='reparatur' (roundtrip-stabil).
    # Ein Push wegen eines ANDEREN Feld-Edits (notizen) darf die 3 NICHT auf 1 umschreiben.
    schein = ("{juprowa_id:'5',nummer:'S1',notizen:'geaendert',scheinart:'reparatur',"
              "juprowa_raw:{AK_AUFART:'3'}}")
    out = _call(node_exe, fn_juprowa_reverse_map, schein)
    assert out["AK_AUFART"] == "3", "stilles Umschreiben des gepullten AK_AUFART (soll Roh-Echo 3 sein)"


def test_echte_aenderung_sendet_reverse(node_exe, fn_juprowa_reverse_map):
    # Roh war 3 (reparatur), lokal auf 'garantie' geaendert -> nicht roundtrip-stabil -> Reverse 6.
    schein = ("{juprowa_id:'5',nummer:'S1',scheinart:'garantie',juprowa_raw:{AK_AUFART:'3'}}")
    out = _call(node_exe, fn_juprowa_reverse_map, schein)
    assert out["AK_AUFART"] == "6", "echte scheinart-Aenderung muss den kanonischen Reverse senden"


def test_ohne_raw_kanonischer_reverse(node_exe, fn_juprowa_reverse_map):
    schein = ("{juprowa_id:'5',nummer:'S1',scheinart:'montage'}")
    out = _call(node_exe, fn_juprowa_reverse_map, schein)
    assert out["AK_AUFART"] == "4", "ohne juprowa_raw -> kanonischer Reverse (montage->4)"


def test_ohne_scheinart_kein_ak_aufart(node_exe, fn_juprowa_reverse_map):
    # Kein scheinart gesetzt -> AK_AUFART wird NICHT gesendet (Payload-Groesse bleibt stabil).
    schein = ("{juprowa_id:'5',nummer:'S1',notizen:'x'}")
    out = _call(node_exe, fn_juprowa_reverse_map, schein)
    assert "AK_AUFART" not in out


# ── STATIC PINS: Push-Pfad ──────────────────────────────────────────────────────
def test_push_field_und_reverse_map(index_html):
    assert "scheinart:'AK_AUFART'," in index_html, "scheinart nicht in JUPROWA_PUSH_FIELDS"
    assert ("const JUPROWA_ART_REV={kein:'0',stoerung:'1',lieferung:'2',reparatur:'3',"
            "montage:'4',mangelbehebung:'5',garantie:'6'};" in index_html), "JUPROWA_ART_REV falsch/fehlt"


def test_dirty_check_block_v583_muster(index_html):
    # WOERTLICH analog Status/Prio: Roh-Echo bei roundtrip-stabil, sonst Reverse.
    assert "if(schein.scheinart&&JUPROWA_ART_REV[schein.scheinart]!=null){" in index_html
    assert ("json.AK_AUFART=(_rawArt!=null&&JUPROWA_ART_MAP[_rawArt]===schein.scheinart)"
            "?_rawArt:JUPROWA_ART_REV[schein.scheinart];" in index_html)


def test_pull_guard_isPending(index_html):
    # scheinart-Pull darf lokale Aenderung bei push_pending NICHT clobbern.
    assert "if(!isPending&&mapped.scheinart&&mapped.scheinart!==existing.scheinart)" in index_html, \
        "!isPending-Guard fehlt an der scheinart-Pull-Zeile"


def test_scope_guard_push_fields_unveraendert(index_html):
    # Scope-Guard: die 8 Original-Push-Keys + sachbearbeiter/bearbeitetVon=null bleiben; nur scheinart neu.
    start = index_html.index("const JUPROWA_PUSH_FIELDS={")
    block = index_html[start:index_html.index("};", start)]
    for feld in ("durchgefuehrte:'AK_ARBEITEN'", "notizen:'AK_NOTIZ'", "monteur:'AK_MONTEUR'",
                 "terminBestaetigt:'AK_TERMIN'", "dauer:'AK_DAUER'", "prioritaet:'AK_PRIOR'",
                 "arbeitsanweisungen:'AK_DURCHZUFUEHREN'", "scheinstatus:'AK_AUFSTATUS'",
                 "scheinart:'AK_AUFART'", "sachbearbeiter:null", "bearbeitetVon:null"):
        assert feld in block, "PUSH_FIELDS-Eintrag fehlt/veraendert: " + feld
    # _isPush-Trigger byte-identisch (v546) — scheinart greift nun automatisch, weil Push-Feld.
    assert "editId&&_finalForm.juprowa_id&&Object.keys(JUPROWA_PUSH_FIELDS).some(k=>k in _diff)" in index_html
    # _juprowaPush-Signatur unangetastet.
    assert "async function _juprowaPush(scheinId){" in index_html


# ── STATIC PINS: Liste + Mobile (TEIL A) ────────────────────────────────────────
def test_liste_inline_selects(index_html):
    assert "updAs(a.id,{prioritaet:e.target.value})" in index_html, "Prio-Inline-Select fehlt in der Liste"
    assert "updAs(a.id,{scheinart:e.target.value})" in index_html, "Auftragstyp-Inline-Select fehlt in der Liste"
    # Auftragstyp: 7 Werte aus JUPROWA_ART_MAP, Label aus AS_ART.l, Wert=Code.
    assert "Object.keys(JUPROWA_ART_MAP).map(function(_c){var _k=JUPROWA_ART_MAP[_c];" in index_html
    # Spaltenkoepfe.
    assert '"Priorität", sortArrow("prioritaet")' in index_html
    assert '"Auftragstyp", sortArrow("scheinart")' in index_html


def test_mobile_chips(index_html):
    assert 'a.prioritaet&&a.prioritaet!=="keine"&&React.createElement' in index_html, "Prio-Chip mobil fehlt"
    assert 'a.scheinart&&a.scheinart!=="kein"&&React.createElement' in index_html, "Auftragstyp-Chip mobil fehlt"
