"""v3.9.320 — COMPANY_FOOTER-Konstante + Helper + PDF-Button-Wiring."""
import re


# v3.9.320: COMPANY_FOOTER ----------------------------------------------------

def test_company_footer_constant_defined(index_html):
    """COMPANY_FOOTER ist Object.freeze({...}) mit allen Pflichtfeldern."""
    m = re.search(
        r"const\s+COMPANY_FOOTER\s*=\s*Object\.freeze\(\{([^}]+)\}\)",
        index_html,
    )
    assert m, "COMPANY_FOOTER-Konstante fehlt (oder nicht Object.freeze)"
    body = m.group(1)
    # Pflichtfelder fuer alle Footer-Stellen (genXls / genFormPdf / printPdf / exportMonat / exportFinkZeit)
    for field in ("name:", "addr:", "phone:", "email:", "web:", "fn:", "fnCourt:",
                  "uid:", "erfuellungsort:", "gerichtsstand:"):
        assert field in body, f"COMPANY_FOOTER fehlt Feld: {field}"


def test_company_footer_helper_constants(index_html):
    """CF_HTML_NAME / CF_HTML_LINE1 / CF_HTML_LINE2 / CF_HTML_AGB als Helper."""
    for helper in ("CF_HTML_NAME", "CF_HTML_LINE1", "CF_HTML_LINE2", "CF_HTML_AGB"):
        assert re.search(rf"const\s+{helper}\s*=", index_html), f"Helper {helper} fehlt"
    # CF_HTML_NAME muss & → &amp; eskapieren (HTML-Sicherheit fuer XLS-Templates)
    assert 'CF_HTML_NAME=COMPANY_FOOTER.name.replace(/&/g,"&amp;")' in index_html


def test_no_hardcoded_company_name_in_dynamic_outputs(index_html):
    """In den refactored Stellen (genXls-Footer + genFormPdf + exportMonat etc.) darf
    der String "Andreas Kolar & Sohn GesmbH" NICHT mehr als hardcoded HTML stehen.

    Wir zaehlen die "harte" Form innerhalb von <div class="footer"> / <td class="sub"> etc.
    Pflicht-Felder (EU-561) + Logo-Header + AGB-Klauseln duerfen bleiben — wir pruefen
    nur dass nach v3.9.320 die typischen Footer-Zeilen die Konstante nutzen.
    """
    # Eine kurze Whitelist (sichtbare hardcoded Branding-Stellen, bewusst nicht refactored)
    whitelist_count = 8  # genXls MSO-Header, Branded Big-Style-Header, AGB-Long-Form etc.
    # Anzahl Vorkommen — Toleranz fuer kuenftige Edits
    occ = len(re.findall(r"Andreas Kolar &(?:amp;)? Sohn GesmbH", index_html))
    # Nach v3.9.320: 8-13 Vorkommen sind okay (Helfer + Whitelist).
    # Wenn jemand einen NEUEN hardcoded String hinzufuegt waere er bei >13.
    assert occ <= 14, (
        f"Mehr als 14 hardcoded 'Andreas Kolar & Sohn GesmbH'-Strings ({occ}) — "
        "ggf. neue Stelle uebersehen, sollte CF_HTML_* nutzen."
    )


# v3.9.315-319: PDF-Button-Wiring --------------------------------------------

def test_pdf_button_count_after_phase_c(index_html):
    """Phase A (3) + Phase B (3) + Phase C (5) = 11 PDF-Buttons mit xBtn('pdf')."""
    occ = len(re.findall(r'xBtn\("pdf"\)', index_html))
    assert occ >= 11, f"Erwartet >= 11 xBtn('pdf')-Aufrufe (Phase A+B+C), gefunden: {occ}"


def test_pdf_buttons_all_use_window_print(index_html):
    """Jeder xBtn('pdf')-Button MUSS window.print() als onClick haben.
    Wenn jemand einen Custom-PDF-Handler einschiebt ohne Print-CSS-Setup → Bug."""
    # Suche alle React.createElement('button', {...xBtn('pdf')...}) und checke onClick
    pattern = re.compile(
        r"React\.createElement\(\s*['\"]button['\"]\s*,\s*\{[^}]*?xBtn\(\"pdf\"\)[^}]*?\}",
        re.DOTALL,
    )
    matches = pattern.findall(index_html)
    assert matches, "Keine xBtn('pdf')-Buttons gefunden — Pattern-Match-Problem?"
    for blob in matches:
        assert "window.print()" in blob, (
            "PDF-Button ohne window.print()-Handler — Foundation seit v3.9.315 setzt "
            f"globales @media print voraus. Auszug: {blob[:200]}"
        )


# v3.9.322: addTank Doppelklick-Guard ----------------------------------------

def test_add_tank_inflight_guard(index_html):
    """v3.9.322: addTank MUSS __addTankInFlight-Guard haben (analog __addKmInFlight)."""
    assert "window.__addTankInFlight" in index_html, "Guard-Variable fehlt"
    # Pattern: 'if(window.__addTankInFlight)return;' direkt nach addTank-Eintritt
    assert re.search(
        r"const\s+addTank\s*=\s*async\s*\([^)]*\)\s*=>\s*\{[^}]*?if\s*\(\s*window\.__addTankInFlight\s*\)\s*return\s*;",
        index_html,
        re.DOTALL,
    ), "Doppelklick-Guard nicht im addTank-Eintritt"
    # finally-Reset
    assert "window.__addTankInFlight=false" in index_html, "Guard-Reset im finally fehlt"
