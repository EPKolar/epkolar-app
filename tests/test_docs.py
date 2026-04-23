"""Audit / handoff docs are present."""
import os


def _has(repo_root, relpath):
    return os.path.isfile(os.path.join(repo_root, relpath))


def test_smoke_tests_present(repo_root):
    assert _has(repo_root, "sql/SMOKE_TESTS_v3.8.33.md")


def test_cando_matrix_doc_present(repo_root):
    assert _has(repo_root, "sql/CANDO_MATRIX.md")


def test_authretry_gaps_present(repo_root):
    assert _has(repo_root, "sql/_authretry_gaps.md")


def test_handoff_nacht_present(repo_root):
    assert _has(repo_root, "HANDOFF_SESSION_2026-04-23.md")


def test_b007_final_sql_archived(repo_root):
    # B006b/B007 wurden nach Deploy archiviert (2026-04-23 Aufraeum-Welle).
    assert _has(repo_root, "_archiv/sql/B006b_B007_FINAL.sql")


def test_check_version_helper(repo_root):
    assert _has(repo_root, "sql/_check_version.js")


def test_check_syntax_helper(repo_root):
    assert _has(repo_root, "sql/_check_syntax.js")
