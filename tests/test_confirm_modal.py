"""Static tests for _confirmModal helper (v3.8.46 Bug-Hunt-S7.2).

Verifies:
- Helper definition exists with correct signature
- Returns a Promise (async-compatible API)
- Supports variant:"danger" option for destructive actions
- At least 3 pilot call-sites migrated from native confirm() to _confirmModal
- Specific pilot sites (delMonteur, deletePlan, deleteTicket) are async
  and use `await _confirmModal(...)` instead of bare `confirm(...)`
"""
import re


def test_confirm_modal_helper_defined(index_html):
    assert "window._confirmModal=function(" in index_html, (
        "_confirmModal helper not defined on window"
    )


def test_confirm_modal_returns_promise(index_html):
    start = index_html.index("window._confirmModal=function(")
    body = index_html[start:start + 3000]
    assert "return new Promise" in body, "_confirmModal must return a new Promise"


def test_confirm_modal_supports_variant(index_html):
    start = index_html.index("window._confirmModal=function(")
    body = index_html[start:start + 3000]
    assert "variant" in body, "_confirmModal must honor opts.variant"
    assert "danger" in body, "_confirmModal must support danger variant"


def test_confirm_modal_has_keyboard_handlers(index_html):
    start = index_html.index("window._confirmModal=function(")
    body = index_html[start:start + 3000]
    assert "Escape" in body, "_confirmModal must handle Escape key"
    assert "Enter" in body, "_confirmModal must handle Enter key"


def test_min_three_pilot_migrations_exist(index_html):
    matches = re.findall(r"await\s+_confirmModal\s*\(", index_html)
    assert len(matches) >= 3, (
        f"Expected at least 3 await _confirmModal sites, found {len(matches)}"
    )


def test_del_monteur_migrated(index_html):
    """delMonteur ist async und dialogisiert über _confirmModal, nicht nativ.

    v3.9.824: das alte Fenster `\\{[^}]*await _confirmModal\\([^)]*Mitarbeiter` setzte voraus,
    dass zwischen Funktionsanfang und erstem Dialog KEIN `}` steht. Seit dem Löschschutz läuft
    dort zuerst der Referenz-Check (Arrow-Funktionen, Objektliterale) -> das Fenster matchte
    nicht mehr. Geschnitten wird jetzt auf den echten Funktionsabschluss (Muster wie in
    test_v394_confirm_migration seit v3.9.820); die Absicht ist unverändert und zusätzlich
    verschärft: natives confirm() im Body ist explizit verboten.
    """
    i = index_html.index("const delMonteur=async id=>{")
    body = index_html[i:index_html.index("\n  };", i)]
    assert re.search(r"await\s+_confirmModal\(", body), (
        "delMonteur should be async and use await _confirmModal"
    )
    assert "Mitarbeiter" in body, (
        "delMonteur-Dialog hat keinen Mitarbeiter-Bezug mehr — falscher Funktions-Match?"
    )
    assert not re.search(r"[^_\w]confirm\s*\(", body), (
        "delMonteur still uses native confirm()"
    )


def test_delete_plan_migrated(index_html):
    pat = (
        r"const\s+deletePlan\s*=\s*async\s+id\s*=>\s*\{[^}]*"
        r"await\s+_confirmModal\([^)]*Plan\s+und"
    )
    assert re.search(pat, index_html), (
        "deletePlan should be async and use await _confirmModal"
    )
    assert "deletePlan=id=>{if(!isAdmin)return;if(!confirm(" not in index_html, (
        "deletePlan still uses native confirm()"
    )


def test_delete_ticket_migrated(index_html):
    pat = (
        r"const\s+deleteTicket\s*=\s*async\s+id\s*=>\s*\{[^}]*"
        r"await\s+_confirmModal\([^)]*Ticket\s+wirklich"
    )
    assert re.search(pat, index_html), (
        "deleteTicket should be async and use await _confirmModal"
    )
    assert "deleteTicket=id=>{if(!isAdmin)return;if(!confirm(" not in index_html, (
        "deleteTicket still uses native confirm()"
    )
