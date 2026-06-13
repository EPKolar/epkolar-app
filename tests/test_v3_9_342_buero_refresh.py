"""Regression-Tests fuer v3.9.342 VBueroExport Auto-Refresh:
  - Manueller "Daten aktualisieren"-Button (Onclick: loadAll) ENTFERNT aus VBueroExport.
  - editMonteurEntries: setTimeout(loadAll(true),1000) nach SQ.push (Sebastian-Vorgabe 1000ms).
  - useEffect haengt visibilitychange + focus Event-Listener an (silent reload bei Tab-Refokus).
  - Cleanup-Callback entfernt beide Listener + clearInterval.
  - TIME_HOUR-Intervall bleibt erhalten (kein Komplettverlust).
  - loadAll-Funktion selbst unveraendert (Snapshot-Assert auf Anker-String).
  - Version-Sync auf 3.9.342.
"""
import re


# Helpers ---------------------------------------------------------------------

def _vbuero_block(index_html):
    """Extrahiert den VBueroExport-Funktions-Block (function VBueroExport(...) {...})
    bis zur naechsten function V...-Definition. Die Tests pruefen Refresh-Logik
    nur in DIESEM Bereich, nicht in anderen Views (z.B. LiveKpi-Refresh in VDash)."""
    start_m = re.search(r"function\s+VBueroExport\s*\(", index_html)
    assert start_m, "VBueroExport-Funktion nicht gefunden"
    end_m = re.search(r"\nfunction\s+V[A-Z]\w*\s*\(", index_html[start_m.end():])
    assert end_m, "Naechste V-Funktion nach VBueroExport nicht gefunden"
    return index_html[start_m.start(): start_m.end() + end_m.start()]


def _edit_monteur_block(index_html):
    """Extrahiert den editMonteurEntries-Save-Pfad."""
    m = re.search(
        r"const\s+editMonteurEntries\s*=[\s\S]+?\n  \};",
        index_html,
    )
    assert m, "editMonteurEntries-Block nicht gefunden"
    return m.group(0)


# 1) Manueller "Daten aktualisieren"-Button entfernt --------------------------

def test_daten_aktualisieren_button_label_removed(index_html):
    """Das ButtonChild-Label '🔄 Daten aktualisieren' (=Button-Text) darf NICHT mehr
    im VBueroExport-Block stehen. (LiveKpi-Tooltip im Dashboard nutzt 'Daten aktualisieren'
    als title-Attribut — der ist in VDash und nicht betroffen.)"""
    block = _vbuero_block(index_html)
    assert "🔄 Daten aktualisieren" not in block, (
        "ButtonChild '🔄 Daten aktualisieren' ist noch in VBueroExport — "
        "v3.9.342 sollte ihn entfernt haben (wurde von Buero-Damen vergessen)."
    )


def test_no_button_onclick_loadall_in_vbuero(index_html):
    """Es darf KEIN React-Button mehr mit onClick: loadAll (ohne args) im VBueroExport
    geben. loadAll laeuft jetzt automatisch via setTimeout + visibilitychange/focus."""
    block = _vbuero_block(index_html)
    m = re.search(
        r"createElement\(\s*['\"]button['\"]\s*,\s*\{[^}]*?onClick\s*:\s*loadAll\b",
        block,
    )
    assert not m, (
        "VBueroExport hat noch einen Button mit onClick:loadAll — v3.9.342 "
        "sollte den 'Daten aktualisieren'-Knopf komplett entfernt haben."
    )


# 2) setTimeout(loadAll(true), 1000) im editMonteurEntries-Save-Pfad ----------

def test_edit_monteur_entries_settimeout_1000ms(index_html):
    """Im editMonteurEntries-Save-Pfad muss nach dem SQ.push ein
    setTimeout(()=>loadAll(true), 1000) (oder _=>) stehen. Sebastian-Vorgabe:
    1000ms, sicher dass Server-Write durch ist."""
    block = _edit_monteur_block(index_html)
    m = re.search(
        r"setTimeout\(\s*(?:\(\s*\)|_)\s*=>\s*loadAll\(\s*true\s*\)\s*,\s*1000\s*\)",
        block,
    )
    assert m, (
        "editMonteurEntries hat kein setTimeout(()=>loadAll(true),1000) nach SQ.push "
        "— Sebastian-Vorgabe 1000ms (war vorher 800ms), Regression v3.9.342."
    )


def test_edit_monteur_entries_no_800ms(index_html):
    """Der alte 800ms-Wert darf nicht mehr im Block stehen — sonst wurde nicht
    auf 1000ms gehoben."""
    block = _edit_monteur_block(index_html)
    m = re.search(
        r"setTimeout\([^)]*loadAll\(\s*true\s*\)[^)]*,\s*800\s*\)",
        block,
    )
    assert not m, (
        "editMonteurEntries hat noch setTimeout(...,800) — sollte auf 1000ms gehoben sein."
    )


# 3) visibilitychange + focus Listener im VBueroExport-useEffect --------------

def test_vbuero_useeffect_has_visibilitychange_listener(index_html):
    """VBueroExport-useEffect muss einen visibilitychange Event-Listener anhaengen."""
    block = _vbuero_block(index_html)
    m = re.search(
        r"addEventListener\(\s*['\"]visibilitychange['\"]",
        block,
    )
    assert m, (
        "VBueroExport-useEffect haengt keinen visibilitychange-Listener an — "
        "Regression v3.9.342."
    )


def test_vbuero_useeffect_has_focus_listener(index_html):
    """VBueroExport-useEffect muss einen focus Event-Listener auf window anhaengen
    (oder kombinierten visibilitychange-Handler, der focus-Equivalent leistet)."""
    block = _vbuero_block(index_html)
    m = re.search(
        r"addEventListener\(\s*['\"]focus['\"]",
        block,
    )
    assert m, (
        "VBueroExport-useEffect haengt keinen focus-Listener an — Regression v3.9.342."
    )


def test_vbuero_listeners_trigger_loadall_true(index_html):
    """Die Listener (visibilitychange/focus) muessen loadAll(true) aufrufen
    (silent reload — sonst spinnt der Toast bei jedem Tab-Wechsel)."""
    block = _vbuero_block(index_html)
    # Im useEffect-Bereich nach dem ersten loadAll() (initial) muessen Listener
    # angehaengt sein, die loadAll(true) triggern.
    # Suche nach _onVis/_onFocus oder Inline-Handlern mit loadAll(true).
    ueff = re.search(
        r"_react\.useEffect\.call\(void 0, \(\)=>\{loadAll\(\);[\s\S]+?\},\s*\[\s*\]\s*\)",
        block,
    )
    assert ueff, "useEffect-Block in VBueroExport nicht gefunden"
    body = ueff.group(0)
    # Muss mind. einmal loadAll(true) im Listener-Setup haben (zusaetzlich zum Intervall)
    cnt = len(re.findall(r"loadAll\(\s*true\s*\)", body))
    assert cnt >= 2, (
        f"useEffect ruft loadAll(true) nur {cnt}x auf — erwartet >=2 "
        "(1x Intervall + mind. 1x Listener-Handler), Regression v3.9.342."
    )


# 4) Cleanup-Callback entfernt beide Listener ---------------------------------

def test_vbuero_cleanup_removes_visibilitychange(index_html):
    """Der Cleanup-return-Callback muss removeEventListener('visibilitychange') haben."""
    block = _vbuero_block(index_html)
    m = re.search(
        r"removeEventListener\(\s*['\"]visibilitychange['\"]",
        block,
    )
    assert m, (
        "VBueroExport-useEffect-Cleanup entfernt visibilitychange-Listener nicht — "
        "Memory-Leak/Doppel-Listener nach Re-Mount, Regression v3.9.342."
    )


def test_vbuero_cleanup_removes_focus(index_html):
    """Der Cleanup-return-Callback muss removeEventListener('focus') haben."""
    block = _vbuero_block(index_html)
    m = re.search(
        r"removeEventListener\(\s*['\"]focus['\"]",
        block,
    )
    assert m, (
        "VBueroExport-useEffect-Cleanup entfernt focus-Listener nicht — "
        "Regression v3.9.342."
    )


# 5) TIME_HOUR-Intervall bleibt erhalten --------------------------------------

def test_vbuero_keeps_interval(index_html):
    """Das setInterval mit TIME_HOUR (oder kuerzerem Wert) muss noch im
    useEffect stehen — Sebastian sagt 'beides kombinieren ist okay'."""
    block = _vbuero_block(index_html)
    m = re.search(
        r"setInterval\(\s*\(\s*\)\s*=>\s*\{?\s*loadAll\(\s*true\s*\)",
        block,
    )
    assert m, (
        "VBueroExport-useEffect hat kein setInterval(loadAll(true),...) mehr — "
        "Sebastian wollte Intervall + Listener KOMBINIEREN, Regression v3.9.342."
    )


# 6) loadAll-Funktion unveraendert (Snapshot-Anker) ---------------------------

def test_loadall_signature_anchor(index_html):
    """Anker-Snapshot: die loadAll-Definition selbst (Signatur + Promise.all-Block)
    muss unveraendert sein. v3.9.342 darf nur Aufrufer/Listener anfassen, nicht
    die Daten-Lade-Logik."""
    expected = (
        'const loadAll=async(silent)=>{\n'
        '    if(!silent)setLoading(true);'
    )
    assert expected in index_html, (
        "loadAll-Definition wurde geaendert — v3.9.342 darf NUR Auto-Refresh-"
        "Pattern anfassen, nicht die loadAll-Funktion selbst."
    )


def test_loadall_promise_all_anchor(index_html):
    """Zweiter Snapshot-Anker: das Promise.all mit den 4 Tabellen
    (time_entries, bautagebuch, forms regie, defects) muss unveraendert sein."""
    expected_tables = [
        '_sbGet("time_entries")',
        '_sbGet("bautagebuch")',
        '_sbGet("forms","type=eq.regie")',
        '_sbGet("defects")',
    ]
    for t in expected_tables:
        assert t in index_html, (
            f"loadAll-Promise.all hat {t} verloren — Daten-Lade-Logik wurde "
            "geaendert, NICHT erlaubt in v3.9.342."
        )


# 7) Version-Sync --------------------------------------------------------------

def test_app_version_at_least_342(app_version):
    """v3.9.342 fuehrte den Test ein — beim Version-Bump auf v3.9.343+ verschiebt
    sich nur die Major-Minor-Patch-Erwartung, der Test bleibt als Forward-Guard
    (gleiches Pattern wie v3.9.341 'at_least'-Tests)."""
    m = re.match(r"3\.9\.(\d+)-supabase", app_version)
    assert m and int(m.group(1)) >= 342, (
        f"APP_VERSION nicht >= 3.9.342 — aktuell: {app_version}"
    )


def test_cache_name_at_least_342(cache_name):
    m = re.match(r"epkolar-v3\.9\.(\d+)", cache_name)
    assert m and int(m.group(1)) >= 342, (
        f"CACHE_NAME nicht >= epkolar-v3.9.342 — aktuell: {cache_name}"
    )


def test_sw_ver_at_least_342(index_html):
    m = re.search(r"SW_VER='epkolar-v3\.9\.(\d+)'", index_html)
    assert m and int(m.group(1)) >= 342, (
        "SW_VER im IIFE nicht >= v3.9.342."
    )
