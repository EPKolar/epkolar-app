# -*- coding: utf-8 -*-
"""Der Gedaechtnis-Index bleibt lesbar und verliert keine Erinnerung.

🔴 WARUM. `MEMORY.md` wird zu Beginn JEDER Sitzung geladen. Drei Dinge koennen
schiefgehen, und keines davon macht irgendwo sonst etwas rot:

  * **zu gross** - der Index wird abgeschnitten oder gar nicht gelesen, und
    dann sind alle Regeln darin wirkungslos. Am 29.09.2026 stand er bei
    24.883 Bytes, die Grenze liegt bei 17.510.
  * **Waisen** - eine Erinnerung, auf die nichts zeigt, wird nie wieder
    gelesen. Am 29.09. waren es ZWEI an einem Tag, beide von anderen
    Sitzungen geschrieben (Frage 25: mehrere Schreiber, keine Sperre).
  * **Zeiger ins Leere** - die Gegenrichtung.

Gefunden wurden beide Waisen nicht durch Nachdenken, sondern durch eine
Zaehlung, die nicht auf null ging.

🔴 DIESER RIEGEL WIRD NICHT ROT, WENN ES DEN ORDNER NICHT GIBT. Auf einer
anderen Maschine ist er nicht anwendbar. Ein Riegel, der dort grundlos rot
wird, wird uebersprungen - und dann misst er nie wieder etwas.
"""
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HIER, "..", "scripts"))

import gedaechtnis_pruefen as G  # noqa: E402


def test_der_sucher_besteht_seine_eigene_eichung():
    """🔴 Fuenf Proben an einem gebauten Ordner mit bekannten Antworten -
    darunter die Gegenprobe, dass eine nur im ARCHIV verlinkte Datei KEINE
    Waise ist. Ohne die meldete das Werkzeug 60 Fehlalarme."""
    schief = G.eichen()
    assert not schief, (
        "Der Sucher besteht seine eigene Eichung nicht:\n%s"
        % "\n".join("   " + s for s in schief))


def test_der_index_ist_in_ordnung():
    ordner = G._ordner()
    if ordner is None:
        return                     # nicht anwendbar, siehe Kopftext
    befunde = G.pruefe(ordner)
    assert not befunde, (
        "%d Befunde am Gedaechtnis-Index:\n\n%s"
        % (len(befunde), "\n\n".join(m for _a, m in befunde)))
