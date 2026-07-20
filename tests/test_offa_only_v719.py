# -*- coding: utf-8 -*-
"""v3.9.719 — Dispo P1-c (Sebastian): AS-Anlage NUR in OFFA.

Arbeitsscheine entstehen ausschliesslich in OFFA und kommen via Juprowa-Pull in die App.
(Der manuelle OFFA-PDF-Import wurde in v3.9.780 als toter Code entfernt.)
Kein Mensch legt in der App einen Schein an. Vorlagen gibt es in der App nicht.

- Sub-Tab "📑 Vorlagen" + ASVorlagenPanel + vorlagenFill-Bus (window._vorlagenBus) komplett raus
  (v698-Muster: nur entfernen, 0 Rest-Referenzen). Boot-Selbsttest as_vorlagen mit raus.
- Menschliche Neuanlage bleibt gesperrt (saveAs bail-out fuer !editId); der letzte Neu-Modus-Einstieg
  (vorlagenFill-Bus -> setEditId(null)+setSub("form")) ist weg.
- Juprowa-Pull-Mapper bleibt unberuehrt (maschinelle OFFA-Quelle).
- as_vorlagen-Tabelle NICHT gedroppt -> nur S4-Kandidat im CLEANUP.
"""
import re


def _as_view(index_html):
    s = re.search(r"function\s+ArbeitsscheinView\s*\(", index_html)
    e = re.search(r"\nfunction\s+[A-Z]\w*\s*\(", index_html[s.end():])
    return index_html[s.start(): s.end() + e.start()]


def test_boot_selbsttest_as_vorlagen_raus(index_html):
    assert "Tabelle as_vorlagen" not in index_html, "Boot-Selbsttest as_vorlagen noch da"


def test_vorlagen_tab_raus(index_html):
    assert '{id:"vorlagen"' not in index_html, "Sub-Tab 'Vorlagen' noch in der AS-Tab-Leiste"
    # Die anderen Tabs bleiben
    assert '{id:"liste"' in index_html and '{id:"kalender"' in index_html


def test_vorlagenpanel_komplett_raus(index_html):
    assert "ASVorlagenPanel" not in index_html, "ASVorlagenPanel (Komponente/Render) noch referenziert"
    assert "_vorlagenBus" not in index_html, "vorlagenFill-Bus (_vorlagenBus) noch im Code"


def test_as_vorlagen_null_referenzen(index_html):
    assert "as_vorlagen" not in index_html, "as_vorlagen wird in index.html noch referenziert"


def test_kein_neu_modus_einstieg_mehr(index_html):
    """Der einzige verbliebene Neu-Modus-Einstieg (Bus -> setEditId(null)+setSub form) ist weg;
    openEdit (editId gesetzt) bleibt der einzige Weg ins Formular."""
    block = _as_view(index_html)
    assert re.search(r'setEditId\(null\)\s*;\s*setSub\(\s*["\']form["\']\s*\)', block) is None, \
        "Neu-Modus-Einstieg (setEditId(null)+setSub('form')) noch in ArbeitsscheinView"


def test_saveas_neuanlage_bleibt_gesperrt(index_html):
    assert "Arbeitsscheine koennen nicht in der App angelegt werden" in index_html, \
        "saveAs-Bail-out fuer Neuanlage fehlt"


def test_offa_pdf_import_removed_v780(index_html):
    """v3.9.780: Der manuelle OFFA-PDF-Import (Button/Input/Handler/Vorschau) wurde
    als toter Code entfernt. Arbeitsscheine kommen jetzt ausschliesslich via
    Juprowa-Pull (siehe test_juprowa_pull_mapper_bleibt) in die App."""
    block = _as_view(index_html)
    assert "const commitImport=" not in block, "v3.9.780: commitImport muss entfernt bleiben"
    import re as _re
    assert _re.search(r'const\s+importOffa\s*=', block) is None, \
        "v3.9.780: importOffa-Handler muss entfernt bleiben"


def test_juprowa_pull_mapper_bleibt(index_html):
    # Der Juprowa-Pull-Mapper (maschinelle OFFA-Quelle) bleibt unangetastet.
    assert "_juprowaSync" in index_html, "Juprowa-Pull-Pfad fehlt"
