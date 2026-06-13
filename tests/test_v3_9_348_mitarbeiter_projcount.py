"""Regression-Tests fuer v3.9.348 MitarbeiterView projCount Phantom-Fix.

Sebastian-Befund: '6 Proj.'-Badge obwohl nur 2 Projekte existieren.
Ursache:
  - Z.5052 hartcodierter useState-Default von monteurProjekte mit
    Phantom-Projekt-IDs (p1,p2,p3,p5,pmn71cjss) — Projekte existieren
    laengst nicht mehr.
  - Z.6465 projCount zaehlt ALLE Eintraege ohne Filterung gegen
    tatsaechlich existierende projects[].

Fix:
  - useState-Default auf {} setzen — echte Zuweisungen kommen aus
    ODB.load('monteurProjekte') + _sbGet.
  - projCount filtert gegen Set(projects.map(p=>p.id)) — nur existierende
    Projekt-IDs werden gezaehlt.

NICHT angetastet:
  - monteurStats (VBueroExport) — andere Quelle (time_entries.project_id).
  - toggleProj / Zuweisungs-Logik.
  - Zuweisungs-Checkboxen (filtern bereits auf status==='aktiv').
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")


def test_app_version_at_least_348():
    m = re.search(r'APP_VERSION="3\.9\.(\d+)-supabase"', INDEX)
    assert m and int(m.group(1)) >= 348, f"APP_VERSION unter 3.9.348: {m.group(0) if m else 'fehlt'}"


def test_sw_ver_at_least_348():
    m = re.search(r"SW_VER\s*=\s*'epkolar-v3\.9\.(\d+)'", INDEX)
    assert m and int(m.group(1)) >= 348


def test_cache_name_at_least_348():
    sw_js = (ROOT / "sw.js").read_text(encoding="utf-8")
    m = re.search(r'CACHE_NAME\s*=\s*"epkolar-v3\.9\.(\d+)"', sw_js)
    assert m and int(m.group(1)) >= 348


def test_sw_header_at_least_348():
    sw_js = (ROOT / "sw.js").read_text(encoding="utf-8")
    m = re.match(r"//\s*EP Kolar Service Worker v3\.9\.(\d+)", sw_js)
    assert m and int(m.group(1)) >= 348


def test_monteurprojekte_default_is_empty_object():
    """Phantom-Default {w1:['p1','p4'],...} muss raus."""
    m = re.search(
        r"const \[monteurProjekte,setMonteurProjekte\]=_react\.useState\.call\(void 0,\s*(\{[^}]*\})\s*\)",
        INDEX,
    )
    assert m, "monteurProjekte useState-Default nicht gefunden"
    default = m.group(1).strip()
    assert default == "{}", (
        f"Phantom-Default noch da: {default!r} — muss auf leeres Objekt {{}} reduziert sein"
    )


def test_no_phantom_p1_in_default():
    """Spezifischer Anker: 'w1:[\"p1\",\"p4\"]' darf nicht mehr im useState-Default stehen."""
    # Suche im useState-Pattern (nur das, nicht andere Stellen wo 'p1' echt sein koennte)
    m = re.search(
        r"const \[monteurProjekte,setMonteurProjekte\]=_react\.useState\.call\(void 0,\s*([^)]*)\)",
        INDEX,
    )
    assert m, "useState-Aufruf nicht gefunden"
    block = m.group(1)
    assert 'w1:["p1"' not in block, "Phantom-w1-Zuweisung noch im Default"
    assert 'w2:["p1","p2","p4","p5"]' not in block, "Phantom-w2-Zuweisung noch im Default"


def test_projcount_filters_against_valid_proj_ids():
    """projCount muss gegen Set(projects.map(p=>p.id)) filtern."""
    # Anker auf das filter-Pattern im MitarbeiterView
    pattern = re.compile(
        r"monteurProjekte\[m\.id\]\|\|\[\]\)\.filter\([^)]*_validProjIds\.has",
    )
    assert pattern.search(INDEX), (
        "projCount filtert nicht via _validProjIds.has(pid) gegen die Projekt-IDs"
    )


def test_valid_proj_ids_set_built_from_projects():
    """_validProjIds wird als Set aus projects.map(p=>p.id) gebaut."""
    pattern = re.compile(
        r"const\s+_validProjIds\s*=\s*new\s+Set\(\s*\(\s*projects\s*\|\|\s*\[\]\s*\)\.map\(\s*p\s*=>\s*p\.id\s*\)\s*\)"
    )
    assert pattern.search(INDEX), "_validProjIds-Set wird nicht korrekt aus projects gebaut"


def test_monteurstats_buero_export_unchanged():
    """monteurStats in VBueroExport (andere Quelle, time_entries) UNVERAENDERT."""
    # Anker auf das projSet.size-Pattern (oder Aequivalent) im VBueroExport
    assert "projSet" in INDEX, (
        "monteurStats-projSet-Pattern in VBueroExport fehlt — sollte UNVERAENDERT bleiben"
    )


def test_zuweisungs_checkboxes_still_filter_aktiv():
    """Die Zuweisungs-Checkboxen in MitarbeiterView filtern weiter auf status==='aktiv'."""
    assert 'status==="aktiv"' in INDEX or "status==='aktiv'" in INDEX, (
        "status==='aktiv'-Filter in Zuweisungs-Checkboxen fehlt"
    )


def test_juprowa_push_call_unchanged():
    """_juprowaPush HART-unangetastet (Phase-2-sensitiv)."""
    anchor = "_juprowaPush(editId).then(r=>{if(!r||(!r.ok&&r.error))console.warn"
    assert anchor in INDEX, "_juprowaPush-Anker veraendert"
