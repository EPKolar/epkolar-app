# -*- coding: utf-8 -*-
"""v3.9.797 -> v3.9.799 VERTRAGSAENDERUNG (Sebastian-Entscheid 21.07.2026): scheinart Push RAUS.

BEFUND (Chat-Claude + Sebastian, DB-Zeitstempel + OFFA-Live-Test): OFFA importiert AK_AUFART
NICHT aus der ServicePad-Cloud und stellt es bei jedem OFFA-seitigen Save auf seinen Stand
zurueck (S075361: App-Push 5 -> OFFA-Save -> Cloud 0 -> App-Pull zurueck auf "kein"; auch am
OFFENEN Schein). Gegenprobe S075381: AK_MONTEUR + AK_PRIOR kommen in OFFA an -> der Import
laeuft generell, NUR AK_AUFART ist Einbahnstrasse OFFA->App. Ein App-Push des Auftragstyps war
also eine Datenillusion (stiller Revert).

Deshalb wurde der in v3.9.797 gebaute scheinart-Push in v3.9.799 zurueckgebaut: scheinart ist
wieder PULL-ONLY, OFFA = Wurzel. Die Liste zeigt den Auftragstyp read-only (Icon+Label), das
Formular disabled mit OFFA-Badge. Das PRIO-Inline-Select bleibt editierbar (AK_PRIOR ist
doppelt live-bewiesen). Diese Datei pinnt den NEUEN Vertrag (kein stilles Anpassen).
"""


def test_scheinart_nicht_mehr_push_feld(index_html):
    start = index_html.index("const JUPROWA_PUSH_FIELDS={")
    block = index_html[start:index_html.index("};", start)]
    assert "scheinart:'AK_AUFART'" not in block, "scheinart darf NICHT mehr in JUPROWA_PUSH_FIELDS stehen"
    # Die 8 Original-Push-Keys bleiben unveraendert.
    for feld in ("durchgefuehrte:'AK_ARBEITEN'", "notizen:'AK_NOTIZ'", "monteur:'AK_MONTEUR'",
                 "terminBestaetigt:'AK_TERMIN'", "dauer:'AK_DAUER'", "prioritaet:'AK_PRIOR'",
                 "arbeitsanweisungen:'AK_DURCHZUFUEHREN'", "scheinstatus:'AK_AUFSTATUS'",
                 "sachbearbeiter:null", "bearbeitetVon:null"):
        assert feld in block, "Push-Feld fehlt/veraendert: " + feld


def test_kein_ak_aufart_im_builder(index_html):
    assert "json.AK_AUFART=" not in index_html, "AK_AUFART-Dirty-Check muss aus dem Builder raus sein"
    # Definition entfernt (die Version-/Rueckbau-KOMMENTARE duerfen den Namen weiter nennen).
    assert "const JUPROWA_ART_REV=" not in index_html, "JUPROWA_ART_REV-Definition ist toter Code -> entfernt"


def test_scheinart_pull_ohne_isPending_guard(index_html):
    # Pull folgt scheinart wieder bedingungslos (OFFA=Wurzel), KEIN !isPending-Guard.
    assert "if(mapped.scheinart&&mapped.scheinart!==existing.scheinart)upd.scheinart=mapped.scheinart;" in index_html
    assert "if(!isPending&&mapped.scheinart" not in index_html, "der v797-!isPending-Guard muss raus sein"


def test_liste_auftragstyp_read_only(index_html):
    # In der Liste darf am Auftragstyp KEIN Schreibweg mehr haengen.
    assert "updAs(a.id,{scheinart:e.target.value})" not in index_html, \
        "Auftragstyp-Liste ist read-only -> kein updAs/onChange am scheinart-Feld"
    # Read-only Anzeige mit OFFA-Tooltip vorhanden.
    assert 'title: "Auftragstyp wird in OFFA gepflegt"' in index_html, "OFFA-Tooltip/read-only Anzeige fehlt"


def test_formular_scheinart_readonly_offa_badge(index_html):
    # v3.9.803 (Kein-Dropdown-Grundsatz): das Formular-Auftragstyp-Feld ist kein disabled-SELECT mehr,
    # sondern reine Text-Anzeige (Icon+Label) + OFFA-Badge. Read-only + OFFA=Wurzel bleibt der Vertrag.
    assert "value: form.scheinart, disabled: true" not in index_html, "Auftragstyp im Formular noch als Select"
    assert '(AS_ART[form.scheinart]?(AS_ART[form.scheinart].i+" "+AS_ART[form.scheinart].l):"—")' in index_html, \
        "Formular-Auftragstyp muss reine Text-Anzeige (Icon+Label) + OFFA-Badge sein"


def test_prio_inline_bleibt_editierbar(index_html):
    # Prio-Inline-Select bleibt WOERTLICH editierbar (AK_PRIOR ist Push-Feld, live-bewiesen).
    assert "updAs(a.id,{prioritaet:e.target.value})" in index_html, "Prio-Inline-Select darf NICHT read-only werden"


def test_juprowa_push_signatur_byte_identisch(index_html):
    # Push-Kern unangetastet.
    assert "async function _juprowaPush(scheinId){" in index_html
    assert "editId&&_finalForm.juprowa_id&&Object.keys(JUPROWA_PUSH_FIELDS).some(k=>k in _diff)" in index_html
