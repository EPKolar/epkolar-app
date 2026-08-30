"""Security invariants — no obvious injection sinks."""
import re

from _hilfen import nur_code


# ---------------------------------------------------------------------------
# DER WEGWERF-FILTER IST RAUS (v3.9.922)
#
# Hier stand vor dem `eval(`-Riegel ein Anfuehrungszeichen-Paritaetsfilter:
# steht links vom Treffer eine UNGERADE Zahl von `"` oder `'`, gilt der
# Treffer als "im String" und wird VERWORFEN. Gedacht war er gegen `eval(` in
# Text; tatsaechlich entscheidet damit ein einzelner Apostroph, ob der
# Sicherheitsriegel einen echten Aufruf ueberhaupt sieht - ein `var s="Sebas-
# tian's Wert"; eval(boese);` reicht schon. Ein SICHERHEITSriegel ist der
# schlechteste denkbare Ort fuer eine Regel, die Treffer WEGWIRFT.
#
# Ersatz: kommentarblind zaehlen (`nur_code()`, siehe tests/_hilfen.py) und
# JEDEN verbleibenden Treffer melden. Gemessen 30.08.2026 am Bestand:
# roh 0 Treffer, kommentarblind 0 Treffer - am Ergebnis aendert sich HEUTE
# nichts (0 = 0). Geaendert hat sich nur, was morgen auffaellt.
#
# Die Zeichenklasse des Lookbehind bleibt unveraendert (`[A-Za-z_]`), damit
# `_eval(`/`myeval(` weiter durchgehen und `.eval(` weiter auffaellt - der
# Umfang des Riegels wird hier NICHT stillschweigend mitverschoben.
# ---------------------------------------------------------------------------
_EVAL = re.compile(r"(?<![A-Za-z_])eval\s*\(")


def _eval_treffer(text):
    """Zeilennummer + kurzer Ausschnitt je Treffer. Nie der ganze Text - ein
    3,5-MB-String als pytest-Fehlermeldung laesst den Lauf haengen statt
    fehlzuschlagen (tests/_hilfen.py, Tuecke 2)."""
    return [(text.count(chr(10), 0, m.start()) + 1,
             text[max(0, m.start() - 60):m.start() + 40].strip())
            for m in _EVAL.finditer(text)]


def _alter_wegwerf_filter(text):
    """Die ENTFERNTE Regel - nur noch fuer die Umkehrprobe nachgebaut: ungerade
    Zahl von `"` oder `'` links im Text -> Treffer wird verworfen."""
    behalten = []
    for m in _EVAL.finditer(text):
        pos = m.start()
        zeilenanfang = text.rfind(chr(10), 0, pos) + 1
        davor = text[zeilenanfang:pos]
        if davor.count('"') % 2 == 1 or davor.count("'") % 2 == 1:
            continue
        behalten.append(pos)
    return behalten


def test_no_eval_calls(index_html):
    treffer = _eval_treffer(nur_code(index_html))
    assert not treffer, "Unerwartete eval()-Aufrufe: %r" % (treffer[:3],)


def test_umkehrprobe_echter_eval_wird_rot(index_html):
    kaputt = nur_code(index_html) + chr(10) + "var _x=eval(boese);"
    assert _eval_treffer(kaputt), "ein blanker eval()-Aufruf bleibt unbemerkt"


def test_umkehrprobe_apostroph_versteckt_nichts_mehr(index_html):
    """DER GRUND DER UMSTELLUNG. Ein einzelner Apostroph links im Text hat den
    Treffer frueher WEGGEWORFEN. Heute nicht mehr."""
    getarnt = "var s=\"Sebastian's Wert\"; eval(boese);"
    kaputt = nur_code(index_html) + chr(10) + getarnt
    assert _alter_wegwerf_filter(getarnt) == [], (
        "Vorbedingung der Probe: der ALTE Filter musste diesen Treffer "
        "verwerfen - sonst zeigt die Probe nicht, was sie zeigen soll"
    )
    assert _eval_treffer(kaputt), (
        "Der Apostroph versteckt den eval()-Aufruf immer noch - der "
        "Wegwerf-Filter ist wieder da"
    )


def test_umkehrprobe_kommentar_bleibt_gruen(index_html):
    """Gegenrichtung: `eval(` in einem Blockkommentar darf NICHT anschlagen -
    dafuer ist der Riegel kommentarblind. Roh WAERE er hier rot."""
    prosa = "/* frueher stand hier eval(x) - ausgebaut v3.8.0 */"
    assert not _eval_treffer(nur_code(index_html + chr(10) + prosa))
    assert _eval_treffer(index_html + chr(10) + prosa), \
        "Umkehrprobe traegt nicht - roh muesste der Kommentar anschlagen"


def test_no_toplevel_document_write(index_html):
    # document.write on the main document is banned (it re-opens and destroys the DOM).
    # But <win>.document.write() on a freshly opened print window is legit (controlled HTML
    # for the print iframe / popup).
    lines = index_html.splitlines()
    bad = []
    for i, line in enumerate(lines, 1):
        # match " document.write" (leading space/tab/semicolon) but not "<var>.document.write"
        stripped = line.lstrip()
        if "document.write" in stripped and ".document.write" not in stripped[:200]:
            # Still could be inside a child-window context if we miss the prefix —
            # the safer filter is: the position right before "document.write" is NOT
            # an identifier char.
            pos = stripped.find("document.write")
            prev = stripped[pos - 1] if pos > 0 else ""
            if prev not in ("." , "_") and not prev.isalnum():
                bad.append((i, stripped[:120]))
    assert not bad, f"top-level document.write calls found: {bad[:3]}"


def test_no_function_constructor(index_html):
    # new Function(...) is as bad as eval
    assert not re.search(r"\bnew\s+Function\s*\(", index_html), "new Function(...) not allowed"


def test_offline_pw_is_not_plain_base64_write(index_html):
    # Regression guard for v3.8.33: make sure we no longer write btoa(user+":"+pw)
    legacy = re.search(r'offlinePwHash",\s*btoa\s*\(', index_html)
    assert not legacy, "Legacy plain-btoa write to offlinePwHash detected (must use _OFFPW.create)"


def test_no_epkolar_gc_setitem(index_html):
    # Regression guard for v3.8.35: epkolar_gc Plaintext-PW-Cache wurde eliminiert.
    # Nur removeItem-Calls (defensive Cleanup) sind erlaubt, kein setItem mehr.
    legacy = re.search(r'localStorage\.setItem\s*\(\s*["\']epkolar_gc', index_html)
    assert not legacy, (
        "localStorage.setItem('epkolar_gc', ...) reappeared — base64 credentials "
        "cache was explicitly removed in v3.8.35 (P2 Security). Use refresh_token-based "
        "re-auth instead of password-cache."
    )
