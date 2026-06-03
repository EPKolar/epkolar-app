"""v3.9.104 — A1: 'urlaub_edit' Permission (per-User Urlaub/ZA-Bearbeitung).

Sebastian-Anforderung: Admin entscheidet PRO USER (nicht an Rolle gekoppelt), wer Urlaub/ZA-
Kontingente bearbeiten + genehmigen darf. 'urlaub' = Tab sehen (bleibt). 'urlaub_edit' =
Verwaltungs-Surface (Bearbeiten-Modus, "Alle genehmigen", Approvals, Alle-MA-Sicht).
Ohne Recht: Urlaub-Tab read-only / eigene Sicht.
"""
import re


def test_urlaub_edit_in_perms_catalog(index_html):
    # PERMS_DESC ist die Quelle der zuweisbaren Admin-Checkboxen (Object.entries(PERMS_DESC).map).
    m = re.search(r"const PERMS_DESC=\{([^;]+)\};", index_html)
    assert m, "PERMS_DESC nicht gefunden"
    assert "urlaub_edit:" in m.group(1), (
        "urlaub_edit muss in PERMS_DESC stehen → erscheint als zuweisbare Checkbox in Admin-Rechteverwaltung"
    )


def test_absview_gate_includes_urlaub_edit(index_html):
    # AbsView.isAdmin (Verwaltungs-Surface-Gate) muss hasPerm('urlaub_edit') einschließen.
    start = index_html.index("function AbsView(")
    body = index_html[start:start + 4500]
    m = re.search(r"const isAdmin=\(([^;]+?)\)\|\|hasPerm\(curUser,'urlaub_edit'\);", body)
    assert m, "AbsView.isAdmin muss admin/PL ODER hasPerm(curUser,'urlaub_edit') sein"
    # Admin/PL-Basis bleibt erhalten (kein Regress)
    assert '==="admin"' in m.group(1) and '==="projektleiter"' in m.group(1), (
        "Admin/PL-Basisrecht muss erhalten bleiben"
    )


def test_urlaub_edit_not_glued_to_role_modules(index_html):
    # 'urlaub_edit' darf NICHT in role.modules stehen (nicht an Rolle koppeln — per-User via perms_override).
    # Prüfe die ROLES-Modullisten (admin/buero etc.): kein "urlaub_edit" als Modul.
    for m in re.finditer(r"modules:\[([^\]]*)\]", index_html):
        assert '"urlaub_edit"' not in m.group(1), (
            "urlaub_edit darf nicht an eine Rolle gekoppelt sein (nur per-User-Zuweisung)"
        )
