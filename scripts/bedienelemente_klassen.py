# -*- coding: utf-8 -*-
"""Die 124 anklickbaren Nicht-Knoepfe in vier Klassen, je mit Begruendung.

Der Auftrag nennt drei Klassen. Es sind VIER, weil er die vierte selbst
zulaesst: *„Wenn du bei einem unsicher bist: unveraendert lassen und als
unsicher melden. Lieber ein fehlender Zugang als ein Phantom in der
Tab-Reihenfolge."*

  BEDIENELEMENT  loest eine Handlung aus, die es sonst nirgends gibt.
                 -> bekommt role="button", tabIndex, Enter UND Leertaste
  DOPPELWEG      dieselbe Handlung ist ueber einen echten Knopf erreichbar
                 -> unveraendert
  KEIN ELEMENT   der onClick tut etwas Nebensaechliches oder ist ein
                 Ueberbleibsel -> unveraendert
  UNSICHER       am Quelltext nicht entscheidbar -> unveraendert

🔴 DIE REGELN SIND BENANNT UND EINZELN NACHLESBAR. Eine Einordnung „nach
Gefuehl" waere an 124 Stellen nicht nachpruefbar, und eine falsche Einordnung
in Richtung BEDIENELEMENT setzt ein Phantom in die Tab-Reihenfolge - das ist
schlechter als gar kein Zugang.
"""
import io
import json
import os
import re
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import bedienelemente_einordnen as SAMMLER  # noqa: E402

# ── Die Regeln, jede mit ihrer Begruendung ────────────────────────────────

# K1: Der Hintergrund eines Dialogs. `if(e.target===e.currentTarget)` heisst
#     „nur wenn DIREKT auf mich geklickt wurde" - das ist die Flaeche hinter
#     dem Dialog. Sie ist kein Bedienelement: jeder Dialog hat seinen eigenen
#     Schliessen-Knopf, und die Tastatur hat dafuer die Esc-Taste. Ein
#     role="button" auf einer bildschirmfuellenden Flaeche waere ein Phantom.
K1 = re.compile(r"e\.target\s*===\s*e\.currentTarget")

# K2: Reine Weiterleitungssperre mit einer Kleinigkeit dahinter, die nur die
#     Sperre ergaenzt (ein Fokus, ein Aufklappen).
K2 = re.compile(r"^\s*e\s*=>\s*\{?\s*e\.stopPropagation\(\)\s*;\s*"
                r"(?:set(?:Open|Show|Expand|Sel)\w*|[\w.]*\.focus\(\))")

# K3: Ein Aufklappen oder Zuklappen - dieselbe Angabe steht danebenan, der
#     Klick spart nur einen Weg.
K3 = re.compile(r"^\s*(?:e\s*=>\s*)?\{?\s*set(?:Open|Offen|Expand\w*|Show\w*|"
                r"Collapsed?|Details?|Auf|Zu)\w*\s*\(", re.I)

# U1: Der Behandler ist eine undurchsichtige Angabe - eine Eigenschaft, ein
#     einzelner Buchstabe, eine uebergebene Funktion. Am Quelltext nicht
#     entscheidbar.
U1 = re.compile(r"^\s*(?:[A-Za-z_$][\w$]*(?:\.[\w$]+)*|function\b)\s*$")


def einordnen(x):
    """(Klasse, Begruendung) fuer eine Fundstelle."""
    r = (x["rumpf"] or "").strip()
    if K1.search(r):
        return ("KEIN ELEMENT",
                "Hintergrundflaeche eines Dialogs (e.target===e.currentTarget). "
                "Der Dialog hat einen eigenen Schliessen-Knopf; ein role=button "
                "auf einer bildschirmfuellenden Flaeche waere ein Phantom.")
    if K2.match(r):
        return ("KEIN ELEMENT",
                "Weiterleitungssperre mit einer Kleinigkeit dahinter - sie "
                "ergaenzt die Sperre, sie ist keine eigene Handlung.")
    if K3.match(r):
        return ("KEIN ELEMENT",
                "Auf- oder Zuklappen. Die Angabe steht danebenan; der Klick "
                "spart einen Weg, er eroeffnet keinen.")
    if U1.match(r):
        return ("UNSICHER",
                "Der Behandler ist eine undurchsichtige Angabe (%r) - am "
                "Quelltext nicht entscheidbar. Unveraendert gelassen." % r[:40])
    if x["knopf_daneben"]:
        return ("DOPPELWEG",
                "Ein echter Knopf in der Naehe ruft dieselbe Funktion: %s"
                % ", ".join(x["knopf_daneben"][:3]))
    if not r:
        return ("UNSICHER", "Leerer Rumpf - nicht entscheidbar.")
    return ("BEDIENELEMENT",
            "Loest %s aus; kein Knopf in der Naehe ruft dasselbe."
            % (", ".join(x["ruft"][:3]) or "eine Handlung"))


def alle():
    aus = []
    for x in SAMMLER.sammeln():
        k, warum = einordnen(x)
        y = dict(x)
        y["klasse"], y["begruendung"] = k, warum
        aus.append(y)
    return aus


if __name__ == "__main__":
    a = alle()
    from collections import Counter
    print("Gesamt: %d" % len(a))
    for k, v in Counter(x["klasse"] for x in a).most_common():
        print("  %-14s %3d" % (k, v))
    print("\nBEDIENELEMENT je Ansicht:")
    b = [x for x in a if x["klasse"] == "BEDIENELEMENT"]
    for k, v in Counter(x["ansicht"] for x in b).most_common():
        print("  %-24s %3d" % (k, v))
    ziel = os.path.join(HIER, "_bedienelemente_klassen.json")
    io.open(ziel, "w", encoding="utf-8", newline="").write(
        json.dumps(a, ensure_ascii=False, indent=1))
    print("\ngeschrieben:", ziel)
