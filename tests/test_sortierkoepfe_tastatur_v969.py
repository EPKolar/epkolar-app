# -*- coding: utf-8 -*-
"""Jeder Sortierkopf ist mit der Tastatur erreichbar - vollstaendig.

🔴 WARUM GERADE DIESE
Sortieren ist in dieser App NIRGENDS sonst erreichbar: kein Menue, kein Knopf,
kein Tastenkuerzel. Wer die Maus nicht benutzt, konnte bis v3.9.969 keine
einzige Tabelle sortieren. Das ist der klarste Fall aus den 124 anklickbaren
Nicht-Knoepfen - und der dichteste, den man gefahrlos bauen kann: ein Stopp je
SPALTE, nicht je Zeile.

🔴 EIN HALBER ZUGANG IST SCHLECHTER ALS KEINER. `tabIndex` ohne
Tastenbehandler heisst: der Fokus steht auf etwas, das nicht reagiert. Dieser
Riegel verlangt deshalb ALLE VIER Stuecke zusammen - `role="button"`,
`tabIndex`, Enter UND Leertaste - und zwar je Stelle, nicht als Gesamtzahl.

🔴 UND ZWEI TRAGEN EINEN BEDINGTEN BEHANDLER. Bei `WerkzeugView` entscheidet
`h.c`, ob eine Spalte ueberhaupt sortierbar ist. Rolle, Tab-Stopp und
Tastenbehandler tragen dort DIESELBE Bedingung. Ein unbedingter Tab-Stopp auf
einer nicht sortierbaren Spalte waere genau das Phantom, das der Auftrag
ausschliesst.
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import code_scan  # noqa: E402

PFAD = os.path.join(os.path.dirname(__file__), "..", "index.html")

AS_SPALTEN = ["nummer", "arbeitsanweisungen", "aufgenommen", "terminVorschlag",
              "terminBestaetigt", "scheinstatus", "prioritaet", "scheinart",
              "sachbearbeiter", "monteur", "kundName", "projektnr"]


def _lies():
    return io.open(PFAD, encoding="utf-8", newline="").read()


def _kopf(text, ruf):
    """Das Eigenschaftenobjekt des th, dessen onClick `ruf` enthaelt."""
    i = text.find(ruf)
    if i < 0:
        return None
    # Rueckwaerts bis zum erzeugenden Aufruf, dann dessen Objektliteral.
    j = max(text.rfind("createElement('th'", 0, i),
            text.rfind('createElement("th"', 0, i),
            text.rfind("h('th'", 0, i))
    if j < 0:
        return None
    k = text.index("{", text.index(",", j))
    ende = code_scan._klammer_zu(text, k, "{", "}")
    return text[k:ende] if ende > 0 else None


def test_jeder_AS_sortierkopf_hat_den_vollen_zugang():
    text = _lies()
    fehlt = []
    for sp in AS_SPALTEN:
        props = _kopf(text, 'toggleSort("%s")' % sp)
        if props is None:
            fehlt.append((sp, "Stelle nicht gefunden"))
            continue
        for stueck, wofuer in (('role: "button"', "die Rolle"),
                               ("tabIndex: 0", "der Tab-Stopp"),
                               ('e.key==="Enter"', "die Eingabetaste"),
                               ('e.key===" "', "die Leertaste"),
                               ("e.preventDefault()", "das Abfangen")):
            if stueck not in props:
                fehlt.append((sp, wofuer))
    assert not fehlt, (
        "\U0001F534 An diesen Sortierkoepfen fehlt der Tastaturzugang:\n    %s\n"
        "  Ein halber Zugang ist schlechter als keiner: der Fokus stuende auf "
        "etwas,\n  das nicht reagiert." % fehlt)


def test_die_zwoelf_sind_auch_wirklich_zwoelf():
    """Gegenprobe auf die Grundgesamtheit.

    Findet der Sucher die Stellen nicht mehr, meldet die Probe oben eine
    makellose Null ueber eine leere Menge.
    """
    text = _lies()
    n = len([sp for sp in AS_SPALTEN if _kopf(text, 'toggleSort("%s")' % sp)])
    assert n == 12, (
        "\U0001F534 Nur %d von 12 Sortierkoepfen der Arbeitsscheinliste "
        "gefunden. Die Tabelle\n  ist umgebaut worden, oder der Sucher trifft "
        "nicht mehr." % n)


def test_der_bedingte_kopf_traegt_die_bedingung_ueberall():
    """\U0001F534 Das Phantom, das hier verhindert wird.

    In `WerkzeugView` entscheidet `h.c`, ob eine Spalte sortierbar ist. Haette
    nur der Klick diese Bedingung und der Tab-Stopp nicht, bekaeme jede NICHT
    sortierbare Spalte einen Fokus ohne Wirkung.
    """
    text = _lies()
    props = _kopf(text, "toggleSort(h.c)")
    assert props, "\U0001F534 Der bedingte Sortierkopf ist nicht auffindbar."
    for stueck in ('role: h.c?"button":undefined',
                   "tabIndex: h.c?0:undefined",
                   "onKeyDown: h.c?("):
        assert stueck in props, (
            "\U0001F534 %r fehlt - die Bedingung `h.c` steht nicht ueberall.\n"
            "  Dann bekommt eine nicht sortierbare Spalte einen Tab-Stopp ohne "
            "Wirkung." % stueck)


def test_der_fokusring_ist_da():
    """Der Teil, den ein Quelltextriegel gerade noch pruefen kann.

    Ob der Ring am Schirm SICHTBAR ist, kann er nicht pruefen - das ist am
    28.09.2026 im Browser nachgesehen worden und steht im Commit. Hier wird
    nur festgehalten, dass die Regel ueberhaupt existiert.
    """
    text = _lies()
    assert re.search(r'\[role="button"\]:focus-visible\s*\{[^{}]*outline:',
                     text), (
        "\U0001F534 Die Fokusring-Regel fuer role=button ist weg. Ohne "
        "sichtbaren Ring ist ein\n  Tab-Stopp fuer einen sehenden "
        "Tastaturnutzer wertlos - er weiss nicht, wo er ist.")


def test_koeder_der_sucher_findet_nicht_irgendwas():
    """Gegenprobe: ein erfundener Spaltenname darf NICHTS liefern."""
    text = _lies()
    assert _kopf(text, 'toggleSort("gibtesnicht")') is None, (
        "\U0001F534 Der Sucher liefert auch fuer einen erfundenen Spaltennamen "
        "ein Ergebnis -\n  dann sagt jede Zusicherung oben nichts aus.")
