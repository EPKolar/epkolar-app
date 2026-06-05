"""v3.9.124 — Hunt-Welle 3 (5 Finder-Agenten, adversarial verifiziert): 9 Fixes."""
import re


def test_fs_chips_border_parenthesized(index_html):
    # P1: `"1px solid "+bool?` war immer truthy → alle FS-Chips blau
    assert 'border:"1px solid "+((nf.fs||"").split(",").map(x=>x.trim()).includes(k)?"#3b82f6":V.bd)' in index_html


def test_whatsapp_only_first_fertig_entry(index_html):
    # v3.9.152: Logik in _maybeNotifyAsDone — nur ERSTER FERTIG-Eintritt + Double-Fire-Guard (notified-Menge)
    assert "if(!AS_GRP_FERTIG.includes(newStatus)||AS_GRP_FERTIG.includes(prevStatus))return;" in index_html
    assert "if(_key&&_waNotifiedAs.has(_key))return;" in index_html


def test_termin_dates_parsed_local(index_html):
    # P2/P3: TZ-Drift — date-only Strings lokal parsen
    assert 'new Date(a.terminBestaetigt+"T00:00:00")-new Date()' in index_html
    assert 'new Date((a.terminBestaetigt||a.terminVorschlag)+"T00:00:00").getTime()' in index_html


def test_add_entry_double_tap_guards(index_html):
    # P2: Doppel-Tap erzeugte doppelte Zeiterfassungs-Records — Guard an BEIDEN addEntry
    assert index_html.count("_addEntryInFlightRef=_react.useRef.call(void 0, 0)") == 2
    assert index_html.count("_addEntryInFlightRef.current<800") == 2


def test_as_card_and_project_row_keyboard(index_html):
    # P2 a11y: Kern-Flow-Karten als role=button + Enter/Space
    assert re.search(r"_openEditGuarded\(a\), role: \"button\", tabIndex: 0", index_html)
    assert re.search(r"onOpenP\(pr\), role: \"button\", tabIndex: 0", index_html)


def test_photoq_backdrop_below_panel(index_html):
    # defensiv: Backdrop 299 < Panel 300 (Antimuster des Glocken-Bugs entschärft)
    assert 'setShowPhotoQ(false);}}, style: {position:"fixed",inset:0,background:"rgba(0,0,0,.3)",zIndex:299}}' in index_html


def test_fabn_grid_mobile(index_html):
    assert 'gridTemplateColumns:window.innerWidth<600?"1fr":"1fr 1fr 1fr"' in index_html


def test_ii_colorscheme_central(index_html):
    # Dark-Mode: native Select-Popups/Date-Picker via colorScheme in II()
    assert 'colorScheme:_dark?"dark":"light"}));' in index_html
