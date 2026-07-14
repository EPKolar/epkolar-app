"""Jedes `window._x = _y` muss ein _y referenzieren, das es auch gibt.

WARUM ES DIESEN TEST GIBT (v3.9.695, teuer gelernt):
In v3.9.691 wurde die Hilfsfunktion `_stUuid` wieder entfernt (das globale `_uuid` war die
richtige Quelle). Die Export-Zeile `window._stUuid=_stUuid;` blieb stehen. Ergebnis:

    ReferenceError: _stUuid is not defined   (index.html:2084)

Der Fehler fliegt auf TOP-LEVEL. Alles, was im Script-Body danach kommt — also die komplette
App — wurde nie definiert. Die Live-App zeigte nur noch den Ladebildschirm.

Warum keiner der bestehenden Gates das gefunden hat:
  - `node_check.py` PARST die Datei, es FUEHRT sie nicht aus. Syntaktisch war alles korrekt.
  - Die pytest-Suite ist statisch (String-/Regex-Asserts).
  - Die Node-Eval-Tests evaluieren den Sentinel-Block, aber die Export-Zeile steht hinter
    `if(typeof window!=='undefined')` — und in Node gibt es kein `window`. Der Zweig wurde
    also uebersprungen und der ReferenceError trat dort NIE auf.
Gefunden hat es erst ein Browser (Playwright, 0 Console-Errors als Abnahmekriterium).

Dieser Test schliesst die Luecke statisch: er sammelt alle window-Exporte und prueft, dass
das exportierte Symbol in der Datei ueberhaupt deklariert ist.
"""
import re


# window._foo=_bar  /  window._foo = _bar
_EXPORT = re.compile(r"window\.(_\w+)\s*=\s*(_\w+)\s*;")


def _deklariert(index_html, symbol):
    """Wird `symbol` irgendwo als function/const/let/var deklariert?"""
    muster = [
        rf"function\s+{re.escape(symbol)}\s*\(",
        rf"(?:const|let|var)\s+{re.escape(symbol)}\s*=",
    ]
    return any(re.search(m, index_html) for m in muster)


def test_alle_window_exporte_zeigen_auf_existierende_symbole(index_html):
    exporte = _EXPORT.findall(index_html)
    assert exporte, "Keine window-Exporte gefunden — Regex kaputt?"

    kaputt = []
    for name, symbol in exporte:
        # Selbst-Zuweisung wie window._x = _x ist der Normalfall; geprueft wird das RECHTE Symbol.
        if not _deklariert(index_html, symbol):
            kaputt.append(f"window.{name} = {symbol}  →  '{symbol}' ist nirgends deklariert")

    assert not kaputt, (
        "Ein window-Export zeigt auf ein Symbol, das es nicht (mehr) gibt. Das ist KEIN "
        "Schoenheitsfehler: der ReferenceError fliegt auf Top-Level und killt den gesamten "
        "restlichen Script-Body — die App startet nicht mehr.\n  " + "\n  ".join(kaputt)
    )


def test_stuuid_ist_und_bleibt_weg(index_html):
    """Die konkrete Regression: _stUuid wurde entfernt, das globale _uuid ist die Quelle.

    Block-Kommentare werden vorher entfernt — die Datei ERKLAERT den Vorfall an der Fundstelle,
    und dieser Test soll nicht ueber die Warntafel stolpern statt ueber das Loch.
    """
    code = re.sub(r"/\*.*?\*/", "", index_html, flags=re.S)
    assert "window._stUuid" not in code
    assert not re.search(r"function\s+_stUuid\s*\(", code)
