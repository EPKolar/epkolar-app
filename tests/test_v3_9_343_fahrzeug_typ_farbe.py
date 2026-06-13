"""Regression-Tests fuer v3.9.343 Fahrzeug-Detail Typ + Farbe editierbar:
  - Im Detail-View (selFz) ist Typ jetzt ein Dropdown aus FZ_TYPEN (statt read-only Text).
  - Im Detail-View (selFz) ist Farbe jetzt ein Text-Input (statt read-only Text).
  - Beide Felder schreiben via upd(sel,f=>...,{...}) sofort in die DB
    (gleiches Pattern wie Pickerl/Vignette/Fahrer).
  - isVAdmin-Gate: nur Admin/Buero/PL/Lagerleitung sieht die Eingabefelder;
    sonst weiterhin read-only Text.
  - Listen-Kachel-Render (NICHT Detail) ist unveraendert — Anker-Snapshot auf
    das alte Read-Only-Pattern dort.
  - Version-Sync auf 3.9.343.
"""
import re


# Helpers ---------------------------------------------------------------------

def _detail_block(index_html):
    """Extrahiert den Detail-View-Kopf-Block (selFz). Startet bei '/* Vehicle Detail */'
    und endet beim '/* km Modal */'-Marker. Tests nur in DIESEM Bereich pruefen,
    sonst fangen wir Listen-Kachel oder NewVehicle-Form-Treffer mit ein."""
    start = index_html.find("/* Vehicle Detail */")
    assert start >= 0, "/* Vehicle Detail */ Marker nicht gefunden"
    end = index_html.find("/* km Modal */", start)
    assert end >= 0, "/* km Modal */ Marker nicht gefunden"
    return index_html[start:end]


def _listing_block(index_html):
    """Extrahiert den Listen-Kachel-Render-Block (Map ueber fahrzeuge VOR
    '/* Vehicle Detail */'). Beginnt sicherheitshalber 4000 Zeichen vor dem
    Vehicle-Detail-Marker — gross genug fuer die Kachel-Render-Logik."""
    end = index_html.find("/* Vehicle Detail */")
    assert end >= 0, "/* Vehicle Detail */ Marker nicht gefunden"
    start = max(0, end - 4000)
    return index_html[start:end]


# 1) Typ ist Dropdown aus FZ_TYPEN.map im Detail-View -------------------------

def test_detail_typ_is_select_with_fz_typen(index_html):
    """Im Detail-View muss ein <select>-Element auftauchen, das value:selFz.typ
    setzt UND FZ_TYPEN.map fuer die <option>s verwendet."""
    block = _detail_block(index_html)
    m = re.search(
        r"createElement\(\s*['\"]select['\"]\s*,\s*\{[^}]*?value\s*:\s*selFz\.typ"
        r"[\s\S]{0,400}?FZ_TYPEN\.map",
        block,
    )
    assert m, (
        "Im Detail-View fehlt der Typ-Select mit value:selFz.typ + FZ_TYPEN.map — "
        "v3.9.343 sollte Typ als Dropdown editierbar machen."
    )


# 2) Farbe ist Input im Detail-View -------------------------------------------

def test_detail_farbe_is_input(index_html):
    """Im Detail-View muss ein <input>-Element auftauchen, das value:selFz.farbe
    bindet (freie Text-Eingabe)."""
    block = _detail_block(index_html)
    m = re.search(
        r"createElement\(\s*['\"]input['\"]\s*,\s*\{[^}]*?value\s*:\s*selFz\.farbe"
        r"(?:\s*\|\|\s*['\"]{2})?",
        block,
    )
    assert m, (
        "Im Detail-View fehlt der Farbe-Input mit value:selFz.farbe — "
        "v3.9.343 sollte Farbe als Text-Input editierbar machen."
    )


# 3) Beide Felder nutzen upd(...) Helper ---------------------------------------

def test_detail_typ_uses_upd_helper(index_html):
    """Der Typ-onChange muss upd(sel,f=>({...f,typ:...}),{typ:...}) verwenden —
    gleiches Pattern wie Pickerl/Vignette/Fahrer."""
    block = _detail_block(index_html)
    m = re.search(
        r"upd\(\s*sel\s*,\s*f\s*=>\s*\(\s*\{\s*\.\.\.f\s*,\s*typ\s*:\s*e\.target\.value\s*\}\s*\)"
        r"\s*,\s*\{\s*typ\s*:\s*e\.target\.value\s*\}\s*\)",
        block,
    )
    assert m, (
        "Typ-onChange im Detail-View nutzt nicht den upd(sel,f=>({...f,typ:...}),{typ:...})"
        "-Helper — v3.9.343 muss gleiches Pattern wie Pickerl/Vignette verwenden."
    )


def test_detail_farbe_uses_upd_helper(index_html):
    """Der Farbe-onChange muss upd(sel,f=>({...f,farbe:...}),{farbe:...}) verwenden."""
    block = _detail_block(index_html)
    m = re.search(
        r"upd\(\s*sel\s*,\s*f\s*=>\s*\(\s*\{\s*\.\.\.f\s*,\s*farbe\s*:\s*e\.target\.value\s*\}\s*\)"
        r"\s*,\s*\{\s*farbe\s*:\s*e\.target\.value\s*\}\s*\)",
        block,
    )
    assert m, (
        "Farbe-onChange im Detail-View nutzt nicht den upd(sel,f=>({...f,farbe:...}),"
        "{farbe:...})-Helper — v3.9.343 muss gleiches Pattern wie Pickerl/Vignette verwenden."
    )


# 4) isVAdmin-Gate am Typ + Farbe ---------------------------------------------

def test_detail_typ_has_isvadmin_gate(index_html):
    """Der Typ-Eingabepfad muss von isVAdmin? gegated sein (Read-Only-Fallback fuer
    Monteure). Suche isVAdmin?... mit Typ-Select in der Nahbarschaft."""
    block = _detail_block(index_html)
    # Suchstrategie: isVAdmin? ... select ... selFz.typ
    m = re.search(
        r"isVAdmin\s*\?\s*\([\s\S]{0,400}?createElement\(\s*['\"]select['\"]"
        r"[\s\S]{0,200}?selFz\.typ",
        block,
    )
    assert m, (
        "Typ-Select im Detail-View ist nicht durch isVAdmin? gegated — "
        "Monteure sehen sonst editierbaren Typ (Sebastian: nur Admin/Buero/PL/Lagerleitung)."
    )


def test_detail_farbe_has_isvadmin_gate(index_html):
    """Der Farbe-Eingabepfad muss ebenfalls von isVAdmin? gegated sein."""
    block = _detail_block(index_html)
    m = re.search(
        r"isVAdmin\s*\?\s*\([\s\S]{0,400}?createElement\(\s*['\"]input['\"]"
        r"[\s\S]{0,200}?selFz\.farbe",
        block,
    )
    assert m, (
        "Farbe-Input im Detail-View ist nicht durch isVAdmin? gegated — "
        "Monteure sehen sonst editierbares Farbe-Feld."
    )


# 5) Listen-Kachel-Render unveraendert (Snapshot-Anker) -----------------------

def test_listing_kachel_typ_emoji_anchor_unchanged(index_html):
    """Anker-Snapshot: Die Listen-Kachel benutzt weiterhin den read-only
    Emoji-Switch (f.typ==='Transporter'?'🚐'...). v3.9.343 darf NUR den Detail-View
    anfassen, nicht die Listen-Kachel."""
    block = _listing_block(index_html)
    expected = 'f.typ==="Transporter"?"🚐":f.typ==="LKW"?"🚛":f.typ==="Anhänger"?"🔗":"🚗"'
    assert expected in block, (
        "Listen-Kachel-Emoji-Anker (f.typ==='Transporter'?'🚐'...) ist nicht mehr "
        "im Listing-Block — v3.9.343 darf die Listen-Kachel NICHT anfassen."
    )


def test_listing_kachel_farbe_render_anchor_unchanged(index_html):
    """Anker-Snapshot: Die Listen-Kachel zeigt Farbe weiterhin als ' · '+f.farbe
    Suffix im Marke/Modell-Text — nicht als Input."""
    block = _listing_block(index_html)
    expected = 'f.farbe?" · "+f.farbe:""'
    assert expected in block, (
        "Listen-Kachel-Farbe-Anker (f.farbe?' · '+f.farbe:'') ist nicht mehr "
        "im Listing-Block — v3.9.343 darf die Listen-Kachel NICHT anfassen."
    )


def test_listing_kachel_has_no_upd_typ_or_farbe(index_html):
    """Sicherheitsnetz: Die Listen-Kachel darf KEINE upd(...,{typ:...}) oder
    upd(...,{farbe:...}) Aufrufe enthalten — sonst hat Edit in die Listen-Kachel
    geleakt. (Im Detail-View MUSS sie stehen, aber nicht im Listing-Block.)"""
    block = _listing_block(index_html)
    assert "{typ:e.target.value}" not in block, (
        "{typ:e.target.value} ist im Listen-Kachel-Block aufgetaucht — "
        "v3.9.343 hat versehentlich in die Listen-Kachel geschrieben statt nur Detail."
    )
    assert "{farbe:e.target.value}" not in block, (
        "{farbe:e.target.value} ist im Listen-Kachel-Block aufgetaucht — "
        "v3.9.343 hat versehentlich in die Listen-Kachel geschrieben statt nur Detail."
    )


# 6) Version-Sync --------------------------------------------------------------
# v3.9.344: Forward-Guard-Pattern (>= 343) statt Exact-Match, damit weitere
# Version-Bumps die Regression-Tests dieser Datei nicht brechen.

def test_app_version_at_least_343(app_version):
    import re as _re
    m = _re.match(r"3\.9\.(\d+)-supabase", app_version)
    assert m and int(m.group(1)) >= 343, (
        f"APP_VERSION nicht >= 3.9.343 — aktuell: {app_version}"
    )


def test_cache_name_at_least_343(cache_name):
    import re as _re
    m = _re.match(r"epkolar-v3\.9\.(\d+)", cache_name)
    assert m and int(m.group(1)) >= 343, (
        f"CACHE_NAME nicht >= epkolar-v3.9.343 — aktuell: {cache_name}"
    )


def test_sw_ver_at_least_343(index_html):
    import re as _re
    m = _re.search(r"SW_VER='epkolar-v3\.9\.(\d+)'", index_html)
    assert m and int(m.group(1)) >= 343, (
        "SW_VER im IIFE nicht >= v3.9.343."
    )
