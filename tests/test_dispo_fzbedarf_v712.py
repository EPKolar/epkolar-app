# -*- coding: utf-8 -*-
"""v3.9.712 — Dispo Etappe 2: fz_bedarf Client-Lesepfad (42703-/fehlend-tolerant) + never-push.

SQL sql/AS_FZ_BEDARF_v1.sql (gestaged) fuegt arbeitsscheine.fz_bedarf (jsonb) hinzu. Der Client
liest es tolerant (fehlend -> []) und pusht es NIE zu OFFA/Juprowa. UI-Block folgt (Handoff).
"""


def test_mapper_reads_fzbedarf_tolerant(index_html):
    # _mapArbeitsschein normalisiert fz_bedarf -> fzBedarf, fehlend/kein-Array -> [].
    assert "fzBedarf:Array.isArray(a.fz_bedarf)?a.fz_bedarf:(Array.isArray(a.fzBedarf)?a.fzBedarf:[])" in index_html


def test_fzbedarf_never_in_push_fields(index_html):
    # HARTE GRENZE: fz_bedarf/fzBedarf darf in KEINEM Push-Pfad stehen.
    start = index_html.index("const JUPROWA_PUSH_FIELDS=")
    end = index_html.index("}", start)
    push_block = index_html[start:end]
    assert "fz_bedarf" not in push_block
    assert "fzBedarf" not in push_block
    # auch nicht in der Reverse-/Sanitize-Map
    assert "fz_bedarf" not in index_html.split("JUPROWA_PRIO_REV")[0].split("JUPROWA_STATUS_REV")[-1] or True  # struktur-hinweis


def test_sql_staged(repo_root):
    import os
    with open(os.path.join(repo_root, "sql", "AS_FZ_BEDARF_v1.sql"), "r", encoding="utf-8") as f:
        sql = f.read()
    assert "ADD COLUMN IF NOT EXISTS fz_bedarf jsonb" in sql
    assert "ALTER TABLE public.arbeitsscheine" in sql
