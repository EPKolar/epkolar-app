# -*- coding: utf-8 -*-
"""Gemeinsame Hilfen fuer die Nebenwirkungs-Messung v3.9.991..996.

WARUM ES DAS GIBT
─────────────────
Die Kur-Kommentare in index.html ZITIEREN die alten Formen woertlich
("HIER STAND `limit=5000`", "HIER STAND `if(_d>0)`"). Wer rohen Dateitext
durchsucht, findet seine eigene Begruendung und haelt sie fuer Code.
Deshalb laeuft JEDE Suche hier ueber code_scan.ist_code().

Die Konsole ist cp1252 - ohne die Umstellung ganz oben stirbt ein Skript an
seiner EIGENEN Ausgabe, und ein Absturz ist am Rueckgabewert von einem Befund
nicht zu unterscheiden.
"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from code_scan import ist_code  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(REPO, "index.html")


def lies(pfad=None):
    """Datei roh lesen - newline='' , damit CRLF/LF unangetastet bleiben."""
    with io.open(pfad or INDEX, "r", encoding="utf-8", newline="") as f:
        return f.read()


def codemaske(text):
    return ist_code(text)


def nur_code_text(text, maske=None):
    """Kommentar- und Zeichenkettenzeichen durch Leerzeichen ersetzen.

    Laenge und damit JEDE Position bleibt erhalten - eine Fundstelle laesst
    sich also direkt auf den Originaltext beziehen.
    """
    m = maske if maske is not None else ist_code(text)
    return "".join(c if m[i] else " " for i, c in enumerate(text))


def zeile_von(text, pos):
    return text.count("\n", 0, pos) + 1


def ausschnitt(text, pos, vor=0, nach=160):
    a = max(0, pos - vor)
    return text[a:pos + nach].replace("\n", "\\n")
