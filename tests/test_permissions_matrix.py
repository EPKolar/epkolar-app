"""canDo() Permissions-Matrix Behavior Tests.

Tag 4 / Theme 3. canDo extrahiert + via Node mit Mock-Usern getestet.
Spiegelt sql/CANDO_MATRIX.md.
"""
import json
import pytest
from conftest import _extract_fn, run_node_snippet


@pytest.fixture(scope="session")
def fn_canDo(index_html):
    fn = _extract_fn(index_html, "canDo")
    assert fn, "canDo function not found"
    return fn


def _check(node_exe, fn, action, user, ownerId="null"):
    user_js = json.dumps(user)
    snippet = (
        f"{fn};process.stdout.write(JSON.stringify("
        f"canDo({json.dumps(action)},{user_js},{ownerId})))"
    )
    return json.loads(run_node_snippet(node_exe, snippet))


# ----- Admin can do everything in matrix -----
def test_admin_proj_create(node_exe, fn_canDo):
    assert _check(node_exe, fn_canDo, "proj_create", {"role": "admin"}) is True


def test_admin_user_manage(node_exe, fn_canDo):
    assert _check(node_exe, fn_canDo, "user_manage", {"role": "admin"}) is True


def test_admin_proj_delete(node_exe, fn_canDo):
    assert _check(node_exe, fn_canDo, "proj_delete", {"role": "admin"}) is True


# ----- Projektleiter -----
def test_pl_proj_create(node_exe, fn_canDo):
    assert _check(node_exe, fn_canDo, "proj_create", {"role": "projektleiter"}) is True


def test_pl_cannot_user_manage(node_exe, fn_canDo):
    assert _check(node_exe, fn_canDo, "user_manage", {"role": "projektleiter"}) is False


def test_pl_cannot_admin_panel(node_exe, fn_canDo):
    # Bekanntes "I1": admin_panel checkt raw rolle, nicht isLager
    assert _check(node_exe, fn_canDo, "admin_panel", {"role": "projektleiter"}) is False


# ----- Buero -----
def test_buero_as_create(node_exe, fn_canDo):
    assert _check(node_exe, fn_canDo, "as_create", {"role": "buero"}) is True


def test_buero_cannot_form_create(node_exe, fn_canDo):
    # Forms sind Field-only (admin/PL/Field), nicht Buero
    assert _check(node_exe, fn_canDo, "form_create", {"role": "buero"}) is False


# ----- Monteur -----
def test_monteur_as_create(node_exe, fn_canDo):
    # v3.9.125 Sebastian 04.06.2026: Monteur darf GAR KEINE Scheine anlegen (vorher True via isField)
    assert _check(node_exe, fn_canDo, "as_create", {"role": "monteur"}) is False


def test_obermonteur_as_create_still_allowed(node_exe, fn_canDo):
    # Obermonteur/Techniker behalten as_create (nur Monteur/Helfer raus)
    assert _check(node_exe, fn_canDo, "as_create", {"role": "obermonteur"}) is True
    assert _check(node_exe, fn_canDo, "as_create", {"role": "techniker"}) is True


def test_monteur_cannot_proj_create(node_exe, fn_canDo):
    assert _check(node_exe, fn_canDo, "proj_create", {"role": "monteur"}) is False


def test_monteur_cannot_user_manage(node_exe, fn_canDo):
    assert _check(node_exe, fn_canDo, "user_manage", {"role": "monteur"}) is False


def test_monteur_doc_upload(node_exe, fn_canDo):
    assert _check(node_exe, fn_canDo, "doc_upload", {"role": "monteur"}) is True


# ----- Owner-branches (zeit_delete, form_delete) -----
def test_monteur_zeit_delete_own(node_exe, fn_canDo):
    user = {"role": "monteur", "id": "u1", "monteurId": "m1"}
    assert _check(node_exe, fn_canDo, "zeit_delete", user, '"m1"') is True


def test_monteur_zeit_delete_foreign(node_exe, fn_canDo):
    user = {"role": "monteur", "id": "u1", "monteurId": "m1"}
    assert _check(node_exe, fn_canDo, "zeit_delete", user, '"m2"') is False


# ----- Lager (raw rolle field) -----
def test_lager_admin_panel(node_exe, fn_canDo):
    # admin_panel = isA || (rolle==='lagerleitung')
    user = {"role": "monteur", "rolle": "Lagerleitung"}
    assert _check(node_exe, fn_canDo, "admin_panel", user) is True


def test_lager_view_ek_price(node_exe, fn_canDo):
    user = {"role": "monteur", "rolle": "Lagerleitung"}
    assert _check(node_exe, fn_canDo, "view_ek_price", user) is True


# ----- Falsy guards -----
def test_no_user_returns_false(node_exe, fn_canDo):
    snippet = fn_canDo + ';process.stdout.write(JSON.stringify(canDo("as_create",null)))'
    assert json.loads(run_node_snippet(node_exe, snippet)) is False
