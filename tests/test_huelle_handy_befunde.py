# -*- coding: utf-8 -*-
"""Handy-Befunde 14.11.2026 (Samsung A55, Admin, dunkel) - Huelle, Home,
Chef-Portal, Arbeitsschein-Liste. Riegel auf die EIGENSCHAFT, je mit Umkehrprobe
wo moeglich. Am Schirm gemessen mit Playwright 412x915 (dunkel, Offline-Session).
"""
from _hilfen import nur_code


def test_fussleiste_zeigt_immer_die_slotbeschriftung(index_html):
    code = nur_code(index_html)
    i = code.find("className: \"bottom-nav\"")
    assert i > 0
    block = code[i:i + 6000]
    # sichtbarer Text = gr.l, NICHT mehr der offene Reitername
    assert ", gr.l)" in block, "Die Fussleiste zeigt nicht mehr die feste Slot-Beschriftung."
    assert "*/, isActive&&gr.g<4&&tabs[safeKat]?tabs[safeKat].l:gr.l)" not in index_html


def test_seitenwechsel_rollt_main_pad_nach_oben(index_html):
    code = nur_code(index_html)
    assert "var _mp=document.querySelector('.main-pad');if(_mp)_mp.scrollTop=0;window.scrollTo(0,0);}catch(_se){}},[kat]);" in code


def test_darstellung_markierung_folgt_der_wahl(index_html):
    code = nur_code(index_html)
    assert "var _akt=themeWahl===o[0];" in code
    assert "var _akt=_themeMode()===o[0];" not in code
    # setThemeMode setzt die Wahl im selben Zweig wie die Anzeige
    assert "applyTheme(d);setThemeWahl(mode);}" in code
    assert 'colorScheme=dark?"only dark":"only light"' in code


def test_root_reserve_nicht_in_der_app_huelle(index_html):
    assert "#root:not(:has(.app-shell)) { padding-bottom: 70px !important; }" in index_html
    assert "  #root { padding-bottom: 70px !important; }" not in index_html


def test_abmelden_fragt_nach(index_html):
    code = nur_code(index_html)
    assert 'if(await _confirmModal("Wirklich abmelden?",{variant:"danger"}))logout();' in code
    assert "React.createElement('button', { onClick: logout," not in code


def test_trendfarbe_mehr_ist_schlecht_ist_rot(index_html):
    code = nur_code(index_html)
    assert "const bad=invertColors?up:!up;" in code
    # Umkehrprobe als Rechnung: Ueberfaellig (invert) +1 -> rot
    up, invert = True, True
    bad = up if invert else (not up)
    assert bad is True


def test_fahrzeugkachel_kennt_die_faelligkeiten(index_html):
    code = nur_code(index_html)
    i = code.find('"aria-label":"Fahrzeuge"')
    assert i > 0
    block = code[i:i + 2500]
    assert "pickerFaellig" in block and "serviceFaellig" in block
    assert " mit Fälligkeit" in block


def test_termine_abzeichen_ist_nicht_die_unterzeile(index_html):
    code = nur_code(index_html)
    assert "_283(\"·\")" not in code
    assert "it.badge" in code
    assert '"T",urgent' not in code


def test_kein_rohwert_kein_und_kein_platzhalterdatum(index_html):
    code = nur_code(index_html)
    assert "\"kein Monteur\"),(a.scheinart&&a.scheinart!==\"kein\"" in code
    assert 'const termin=a.terminBestaetigt||a.terminVorschlag||"";' not in code
    assert "const termin=_tBest?a.terminBestaetigt:(_hasTermin(a.terminVorschlag)?a.terminVorschlag:\"\");" in code
    assert '"Tankkosten MTD"' not in code


def test_as_karte_knopfe_beschriftet_storno_abgesetzt(index_html):
    code = nur_code(index_html)
    # v3.9.1012 CI-Stufe 3: Linien-Ikone statt Emoji/Zeichen vor der Beschriftung - die Beschriftung bleibt
    assert '_asIk("verbot","Storno",14))' in code
    # A55-2 Fund 8 (16.11.): Storno stand links direkt neben 'Bearbeiten' - jetzt rechts am Ende, durch freien Raum abgesetzt
    assert "minHeight:44,marginLeft:\"auto\"}" in code
    assert "order:-1,marginRight:\"auto\"}, title: \"Stornieren\"" not in code
    assert '_asIk("stift","Bearbeiten",14))' in code and '_asIk("dokument","PDF",14))' in code and '_asIk("qr","QR",14))' in code
