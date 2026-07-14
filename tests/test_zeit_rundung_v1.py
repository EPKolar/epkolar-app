"""v3.9.688 — 5-Minuten-Raster für die MANUELLE Zeiterfassung. LOHNRELEVANT.

Betriebsregel, von Sebastian am 14.07.2026 fixiert und vereinbart:

    von (Kommen) wird AUFgerundet, bis (Gehen) wird ABgerundet.

Die Rundung geht damit bewusst ZULASTEN der Monteure. Das ist gewollt und bestätigt — kein
Versehen, kein offener Punkt. Wer sie je symmetrisch machen will, ändert eine Zeile in
`_zeitRundVon`; diese Tests fangen es dann sofort.

Die Stempeluhr hatte die Regel längst (`_stRoundKommen`/`_stRoundGehen`, ms-basiert). Die
manuelle Erfassung arbeitet mit HH:MM-Strings aus `<input type="time">` — daher eine eigene
String-Variante. Die Stempel-Helper bleiben unangetastet.
"""
import json

from conftest import run_node_snippet, _extract_fn

RASTER = "const ZEIT_RASTER_MIN=5;"


def _harness(index_html):
    teile = [RASTER]
    for n in ("_zeitParse", "_zeitFmt", "_zeitRundVon", "_zeitRundBis"):
        fn = _extract_fn(index_html, n)
        assert fn, f"{n} nicht gefunden"
        teile.append(fn)
    return "\n".join(teile) + "\n"


def _eval(node_exe, index_html, ausdruck):
    snip = _harness(index_html) + f"process.stdout.write(JSON.stringify({ausdruck}));"
    return json.loads(run_node_snippet(node_exe, snip))


# ── Kommen: AUFrunden ───────────────────────────────────────────────────────

def test_von_rundet_auf(node_exe, index_html):
    faelle = {
        "7:03": "07:05",
        "07:01": "07:05",
        "07:04": "07:05",
        "16:47": "16:50",
        "06:58": "07:00",
    }
    for ein, soll in faelle.items():
        r = _eval(node_exe, index_html, f"_zeitRundVon('{ein}')")
        assert r == soll, f"von {ein} -> {r}, erwartet {soll}"


def test_von_rasterwert_bleibt(node_exe, index_html):
    """Idempotenz: ein Wert, der schon im Raster liegt, darf sich NICHT bewegen."""
    for t in ("07:00", "07:05", "16:45", "00:00", "23:55"):
        r = _eval(node_exe, index_html, f"_zeitRundVon('{t}')")
        assert r == t, f"{t} wurde zu {r} verschoben"
        assert _eval(node_exe, index_html, f"_zeitRundVon(_zeitRundVon('{t}'))") == t


# ── Gehen: ABrunden ─────────────────────────────────────────────────────────

def test_bis_rundet_ab(node_exe, index_html):
    faelle = {
        "16:47": "16:45",
        "16:04": "16:00",
        "16:01": "16:00",
        "16:49": "16:45",
        "00:02": "00:00",
    }
    for ein, soll in faelle.items():
        r = _eval(node_exe, index_html, f"_zeitRundBis('{ein}')")
        assert r == soll, f"bis {ein} -> {r}, erwartet {soll}"


def test_bis_rasterwert_bleibt(node_exe, index_html):
    for t in ("16:00", "16:45", "00:00", "23:55"):
        r = _eval(node_exe, index_html, f"_zeitRundBis('{t}')")
        assert r == t
        assert _eval(node_exe, index_html, f"_zeitRundBis(_zeitRundBis('{t}'))") == t


def test_die_regel_geht_zulasten_des_monteurs(node_exe, index_html):
    """Der Kern der Betriebsregel, explizit festgenagelt.

    von wird NIE früher, bis wird NIE später. Wer das dreht, dreht die Lohnrichtung —
    und dieser Test fällt.
    """
    r = _eval(node_exe, index_html, "[_zeitRundVon('07:01'), _zeitRundBis('16:59')]")
    assert r[0] == "07:05", "Kommen muss nach hinten wandern (zulasten des Monteurs)"
    assert r[1] == "16:55", "Gehen muss nach vorne wandern (zulasten des Monteurs)"


# ── Mitternachts-Kanten ─────────────────────────────────────────────────────

def test_bis_um_mitternacht(node_exe, index_html):
    assert _eval(node_exe, index_html, "_zeitRundBis('00:02')") == "00:00"
    assert _eval(node_exe, index_html, "_zeitRundBis('00:04')") == "00:00"


def test_von_ueberlauf_wird_gekappt_nicht_umgeklappt(node_exe, index_html):
    """23:56–23:59 aufrunden ergäbe 24:00 — die Uhrzeit gibt es nicht.

    Ein '00:00' wäre hier FALSCH: es würde den Arbeitsbeginn auf den Anfang DESSELBEN Tages
    werfen, also 24 Stunden zu früh, und `_wrapHrs` machte daraus eine Monster-Schicht.
    Deshalb wird auf 23:55 gekappt — der eine Fall, in dem sich die Regel nicht wörtlich
    anwenden lässt. Praktisch irrelevant (niemand beginnt manuell um 23:57), aber definiert.
    """
    for t in ("23:56", "23:57", "23:58", "23:59"):
        r = _eval(node_exe, index_html, f"_zeitRundVon('{t}')")
        assert r == "23:55", f"{t} -> {r}"
        assert r != "00:00", "Umklappen auf 00:00 wäre 24h zu früh"


# ── Müll ────────────────────────────────────────────────────────────────────

def test_leer_und_muell_bleibt_unveraendert(node_exe, index_html):
    """Ungültige Eingabe darf NICHT still zu einer Uhrzeit werden — sie kommt unverändert
    zurück, und die vorhandene Validierung greift wie bisher."""
    for ein in ("", "abc", "25:00", "07:60", "7", "7:3"):
        for fn in ("_zeitRundVon", "_zeitRundBis"):
            r = _eval(node_exe, index_html, f"{fn}('{ein}')")
            assert r == ein, f"{fn}('{ein}') -> {r!r}, erwartet unverändert"
    assert _eval(node_exe, index_html, "[_zeitRundVon(null), _zeitRundBis(undefined)]") == [None, None]


# ── Das Rechenbeispiel aus der Regel ────────────────────────────────────────

def test_beispiel_aus_der_betriebsregel(node_exe, index_html):
    """7:03–16:47 mit 1 h Pause: 8,73 h (alt) -> 8,67 h (neu)."""
    r = _eval(node_exe, index_html, "[_zeitRundVon('07:03'), _zeitRundBis('16:47')]")
    assert r == ["07:05", "16:45"]
    alt = (16 + 47 / 60) - (7 + 3 / 60) - 1
    neu = (16 + 45 / 60) - (7 + 5 / 60) - 1
    assert round(alt, 2) == 8.73
    assert round(neu, 2) == 8.67


# ── Struktur-Guards ─────────────────────────────────────────────────────────

def test_timer_faellt_unter_dieselbe_regel(index_html):
    # Der Timer nutzt die ms-basierten Stempel-Helper — keine dritte Kopie der Logik.
    assert "const _vonMs=_stRoundKommen(s.startAt);const _bisMs=_stRoundGehen(_endAt);" in index_html
    assert "const hours=Math.max(0,(_bisMs-_vonMs)/TIME_HOUR);" in index_html


def test_timer_unter_5min_wird_verworfen(index_html):
    # Eine 0h-Buchung waere ein Geisterdatensatz in der Lohnbasis.
    assert 'window.__toast("⏱ Timer-Lauf unter 5 Minuten — nicht gebucht (5-Minuten-Raster)"' in index_html


def test_beide_erfassungs_komponenten(index_html):
    """VZeit UND ZeiterfassungView — beide erfassen von/bis, beide muessen runden."""
    assert index_html.count("const _rVon=_zeitRundVon(addVon), _rBis=_zeitRundBis(addBis);") == 2
    # Gespeichert werden die GERUNDETEN Werte, nicht die Roh-Eingabe.
    assert "von:addVon" not in index_html
    assert "bis:addBis" not in index_html


def test_sichtbare_normalisierung(index_html):
    # WYSIWYG: das Feld zeigt nach dem Verlassen den Wert, der auch gebucht wird.
    assert index_html.count("onBlur:e=>{const v=_zeitRundVon(e.target.value);setAddVon(v);") == 2
    assert index_html.count("onBlur:e=>{const b2=_zeitRundBis(e.target.value);setAddBis(b2);") == 2


def test_stempeluhr_unangetastet(index_html):
    # Die Stempeluhr hatte die Regel schon — dort wird roh gespeichert und bei der Auswertung
    # gerundet. Das ist ein anderer Vertrag und bleibt, wie er ist.
    assert "function _stRoundKommen(ts){var ms=STEMPEL_ROUND_MIN*60000;return Math.ceil(ts/ms)*ms;}" in index_html
    assert "function _stRoundGehen(ts){var ms=STEMPEL_ROUND_MIN*60000;return Math.floor(ts/ms)*ms;}" in index_html
