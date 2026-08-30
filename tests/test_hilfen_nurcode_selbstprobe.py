# -*- coding: utf-8 -*-
"""Selbstprobe fuer das MESSGERAET `nur_code()` - es hatte selber keine.

Zweimal in Folge hat `nur_code()` echten Code verschluckt und damit jeden
`assert "x" not in nur_code(...)` fuer diesen Bereich STILL GRUEN gestellt:

  1. v3.9.913: `accept: "image/*"` als Kommentarbeginn -> 33 Stellen,
     49.857 Zeichen unsichtbar (darunter der Tabellenzeilen-Reader
     `layers.find(x=>x.id===(t.gewerk||t.layer))`).
  2. 30.08.2026: `https://*.tile.openstreetmap.org` in der CSP (index.html:8)
     -> weitere 1.049 Zeichen Kopf unsichtbar: Rest der CSP (connect-src,
     font-src, worker-src, manifest-src, frame-src, object-src), `<title>`,
     beide Icon-Links.

Beide Male fiel es nur zufaellig auf, weil jemand eine ZAHL nachgerechnet hat.
Ab jetzt wird es bei jedem Lauf nachgerechnet - mit BENANNTEN Stellen statt
einem Gesamtzaehler, und mit einer Umkehrprobe je Richtung.

Verglichen werden ausschliesslich ZAHLEN, nie Strings: ein `assert "x" in
index_html` liesse pytest den 3,5-MB-String als Fehlermeldung aufbereiten -
der Test faellt dann nicht um, er STEHT und blockiert die Suite (siehe
_hilfen.py, Tuecke 2).
"""
import re

from _hilfen import nur_code

# Benannte Stellen aus dem Kopf, die der zweite Fehler verschluckt hat.
# Alle vier kommen roh GENAU EINMAL vor (gemessen 30.08.2026) - deshalb ist
# "mindestens einmal sichtbar" hier gleichbedeutend mit "der Kopf ist da".
_KOPF = [
    "manifest-src 'self' blob:",
    "object-src 'self' blob: data:",
    "worker-src 'self' blob:;",
    "<title>EP: Kolar",
]
# Benannte Stelle aus dem Bereich, den der erste Fehler verschluckt hat.
# Roh 3x, davon lag genau EINE im verschluckten Bereich - deshalb wird hier
# die ZAHL verglichen und nicht die Anwesenheit.
_MIME_BEREICH = "layers.find(x=>x.id===(t.gewerk||t.layer))"
# Ein ECHTER Blockkommentar - der MUSS verschwinden, sonst maskiert die
# Reparatur zu viel und die Riegel zaehlen wieder Prosa mit.
_ECHTER_KOMMENTAR = "EP KOLAR SELF-HEAL v1: Nuke stale SW cache"


def _nur_code_ohne_maske(index_html):
    """Der Zustand VOR beiden Reparaturen - nur fuer die Umkehrprobe."""
    ohne = re.sub(r"/\*[\s\S]*?\*/", "", index_html)
    return chr(10).join(l for l in ohne.splitlines()
                        if not l.startswith("const APP_VERSION="))


def test_kopf_bleibt_sichtbar(index_html):
    code = nur_code(index_html)
    for stelle in _KOPF:
        assert index_html.count(stelle) == 1, (
            "Vorbedingung weg: %r kommt roh %d mal vor statt einmal - Anker "
            "anpassen." % (stelle, index_html.count(stelle))
        )
        assert code.count(stelle) == 1, (
            "nur_code() verschluckt den Kopf von index.html wieder. Damit ist "
            "jeder `not in nur_code(...)`-Riegel ueber CSP-Direktiven, Titel "
            "oder Icons still gruen. Unsichtbare Stelle: %r" % (stelle,)
        )


def test_mime_bereich_bleibt_sichtbar(index_html):
    roh, code = index_html.count(_MIME_BEREICH), nur_code(index_html).count(_MIME_BEREICH)
    assert roh == 3, "Vorbedingung geaendert: roh %d statt 3 Reader" % roh
    assert code == roh, (
        "nur_code() verschluckt wieder Teile des `accept:\"image/*\"`-Bereichs "
        "(49.857 Zeichen echter Code): sichtbar %d von %d Readern." % (code, roh)
    )


def test_echte_kommentare_verschwinden_weiterhin(index_html):
    assert index_html.count(_ECHTER_KOMMENTAR) == 1, "Vorbedingung weg - Anker anpassen"
    assert nur_code(index_html).count(_ECHTER_KOMMENTAR) == 0, (
        "Ein echter Blockkommentar ueberlebt nur_code() - die Maskierung ist "
        "zu weit gefasst, alle Riegel zaehlen wieder den Erklaertext mit."
    )


def test_umkehrprobe_ohne_maske_wird_der_riegel_rot(index_html):
    """DIE GEGENPROBE. Ohne die Maskierung MUESSEN beide Riegel oben rot
    werden - sonst messen sie nichts."""
    kaputt = _nur_code_ohne_maske(index_html)
    stumpf = [s for s in _KOPF if kaputt.count(s) == index_html.count(s)]
    assert not stumpf, (
        "Die Umkehrprobe traegt nicht: ohne Maskierung muesste jede Kopf-"
        "Stelle ihren Treffer verlieren. Unveraendert geblieben: %r" % (stumpf,)
    )
    assert kaputt.count(_MIME_BEREICH) < index_html.count(_MIME_BEREICH), (
        "Die Umkehrprobe traegt nicht: ohne Maskierung muesste auch mindestens "
        "ein image/*-Reader verschwinden (gefunden: %d von %d)."
        % (kaputt.count(_MIME_BEREICH), index_html.count(_MIME_BEREICH))
    )
