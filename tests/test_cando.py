"""canDo() permission matrix structural integrity."""
import re


def _extract_cando_matrix_keys(index_html):
    # Locate the m={...} assignment inside canDo
    m = re.search(r"function\s+canDo\([^)]+\)\s*\{[\s\S]*?const\s+m\s*=\s*\{([^}]+)\}", index_html)
    assert m, "canDo matrix object not found"
    body = m.group(1)
    keys = re.findall(r"(\w+)\s*:", body)
    return keys


def test_cando_has_matrix(index_html):
    keys = _extract_cando_matrix_keys(index_html)
    assert len(keys) >= 30, f"canDo matrix has only {len(keys)} actions, expected ≥30"


def test_cando_has_core_actions(index_html):
    keys = set(_extract_cando_matrix_keys(index_html))
    required = {
        "proj_create", "as_create", "as_delete", "doc_upload", "admin_panel",
        "material_view", "view_ek_price", "user_manage", "fz_create", "auswertungen",
    }
    missing = required - keys
    assert not missing, f"canDo missing required actions: {missing}"


def test_cando_has_owner_branches(index_html):
    # zeit_delete and form_delete are handled outside the matrix
    assert 'action==="zeit_delete"' in index_html, "zeit_delete owner branch missing"
    assert 'action==="form_delete"' in index_html, "form_delete owner branch missing"
