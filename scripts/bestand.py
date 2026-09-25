# -*- coding: utf-8 -*-
"""Bestandspruefung: was der Nutzer heute TUN kann, muss er morgen TUN koennen.

WOZU
────
Ein Design-Umbau darf das Aussehen aendern und sonst nichts. Der teuerste
Fehler dabei ist nicht ein haesslicher Knopf, sondern ein VERSCHWUNDENER:
eine Auswahloption mit Zaehler 0, ein Filter, ein Sortierkriterium, eine
Unterseite. Der faellt niemandem auf, weil nichts kaputt aussieht - bis
jemand ihn braucht.

Grundlage ist der Live-Stand v3.9.930, aufgenommen im 390px-Viewport
(docs/GRUNDSTAND_UI_v3.9.930.md).

WAS DIESE PRUEFUNG IST - UND WAS NICHT
──────────────────────────────────────
Sie prueft, ob die Zeichenkette im Quelltext STEHT. Das ist schwaecher als
"der Knopf ist erreichbar" und staerker als gar nichts. Sie faengt genau den
Fehler, um den es geht: etwas beim Umbauen wegzulassen. Sie faengt NICHT,
wenn etwas dasteht, aber nicht mehr gerendert wird - dagegen laufen die
Riegel in tests/.

UMLAUTE
───────
Die Begriffe stehen hier in ASCII (Verfuegbar, Maengel, Plaene), im Quelltext
aber meist mit echtem Umlaut, teils als HTML-Entity oder \\u-Escape. Gesucht
wird deshalb in mehreren Schreibweisen - aber nur in solchen, die denselben
Begriff meinen. Nicht so tolerant, dass ein Treffer entsteht, wo keiner ist.

LEERE GRUNDGESAMTHEIT
─────────────────────
Findet die Pruefung keine einzige Gruppe vor (etwa weil der Pfad falsch ist),
meldet sie ROT, nicht gruen. Nichts gemessen ist kein Ergebnis - das ist die
Regel aus scripts/messen.py und sie gilt hier genauso.

AUFRUF
──────
    python scripts/bestand.py            prueft index.html
    python scripts/bestand.py --selbst   Selbstprobe: entfernt eine Option
                                         aus einer KOPIE und verlangt ROT
"""
import io
import os
import sys

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZIEL = os.path.join(WURZEL, "index.html")

# ── Der Bestand, Gruppe fuer Gruppe ────────────────────────────────────────
# Quelle: docs/GRUNDSTAND_UI_v3.9.930.md, gemessen an der Live-App.

BESTAND = {
    "Arbeitsscheine: elf Statuswerte": [
        "aufgenommen", "freigegeben", "in Bearbeitung", "aufgeschoben",
        "erledigt", "abgerechnet", "bar bezahlt", "storniert",
        "Gesamt", "Offen (alle)", "Fertig (alle)",
    ],
    "Arbeitsscheine: sieben Sortierkriterien": [
        "Nummer", "Erf.-Datum", "Termin (best.)", "Termin (vorg.)",
        "Status", "Kunde", "Monteur",
    ],
    "Arbeitsscheine: acht Filter": [
        "Alle", "Offen", "In Arbeit", "Erledigt", "Meine", "Heute",
        "Ueberfaellig", "Kein Monteur",
    ],
    "Werkzeuge: sechs Status": [
        "Verfuegbar", "Ausgegeben", "In Reparatur", "Kalibrierung faellig",
        "Verloren/Defekt", "Stillgelegt",
    ],
    "Werkzeuge: neun Kategorien": [
        "Elektrowerkzeug", "Messgeraete", "Handwerkzeug", "Maschinen",
        "Sicherheit/PSA", "Verbrauchsmaterial", "Kabelwerkzeug",
        "Leiter/Geruest", "Sonstiges",
    ],
    "Projektakte: dreizehn Unterseiten": [
        "Dashboard", "Zeiterfassung", "Berichte", "Plaene", "Formulare",
        "Checklisten", "Maengel", "Bautagebuch", "Fotos", "Material",
        "Dokumente", "OFFA", "Export",
    ],
    "Home: sieben Schnellzugriffe": [
        "Neues Projekt", "Arbeitsscheine", "Wochenplanung",
        "Urlaub beantragen", "Fahrzeuge", "Auswertungen", "Tanken",
    ],
    "Home: acht Kachelwerte": [
        "Projekte aktiv", "Scheine offen", "Fahrzeuge", "Werkzeugwert",
        "Abwesenheiten", "Monatsabrechnung", "Material", "Bautagebuch",
    ],
    "Projekte: vier Filter": [
        "Aktiv", "Abgeschlossen", "Archiv", "Alle",
    ],
    "Abwesenheiten": [
        "Urlaub beantragen", "Krankmeldung", "Zeitausgleich",
        "Antraege pruefen", "Excel", "Server (SRVDC02)",
    ],
    "Fahrzeuge": [
        "Scan", "Batch", "Labels", "Excel", "PDF", "Fahrzeug",
    ],
    "Mitarbeiter": [
        "Mein Profil", "Nur Aktive", "Neuer Mitarbeiter",
        "Stempel-Pausenregeln", "KV-Konstanten",
    ],
}

# ── Schreibweisen ──────────────────────────────────────────────────────────

_UML = [("ae", "ä"), ("oe", "ö"), ("ue", "ü"),
        ("Ae", "Ä"), ("Oe", "Ö"), ("Ue", "Ü")]
_ENT = {"ä": "&auml;", "ö": "&ouml;", "ü": "&uuml;",
        "Ä": "&Auml;", "Ö": "&Ouml;", "Ü": "&Uuml;",
        "ß": "&szlig;"}


def schreibweisen(begriff):
    """Alle Schreibweisen EINES Begriffs - nie die eines anderen.

    Der ASCII-Ersatz wird VOLLSTAENDIG angewandt oder gar nicht. Teilweise
    zu ersetzen wuerde Kunstwoerter erzeugen, die zufaellig irgendwo treffen
    koennten.
    """
    kandidaten = [begriff]
    mit_umlaut = begriff
    for a, u in _UML:
        mit_umlaut = mit_umlaut.replace(a, u)
    if mit_umlaut != begriff:
        kandidaten.append(mit_umlaut)

    weitere = []
    for k in list(kandidaten):
        # HTML-Entities
        e = k
        for u, ent in _ENT.items():
            e = e.replace(u, ent)
        if e != k:
            weitere.append(e)
        # \u-Escape, wie Sucrase es schreibt
        x = "".join("\\u%04x" % ord(c) if ord(c) > 127 else c for c in k)
        if x != k:
            weitere.append(x)
    return kandidaten + weitere


def pruefe(quelle):
    """Gibt die Liste der FEHLENDEN (Gruppe, Begriff) zurueck."""
    fehlt = []
    gruppen = 0
    for gruppe, begriffe in BESTAND.items():
        gruppen += 1
        for b in begriffe:
            if not any(k in quelle for k in schreibweisen(b)):
                fehlt.append((gruppe, b))
    if gruppen == 0:
        raise SystemExit(
            "bestand.py: KEINE Gruppe geprueft. Das ist kein gruenes "
            "Ergebnis, sondern eine ausgefallene Messung.")
    return fehlt


def _lies(pfad):
    s = io.open(pfad, encoding="utf-8", newline="").read()
    if len(s) < 1_000_000:
        raise SystemExit(
            "bestand.py: %s ist nur %d Bytes gross. Das ist Datenverlust, "
            "keine Bestandsfrage." % (pfad, len(s)))
    return s


def selbstprobe():
    """Belegt, dass die Pruefung ueberhaupt ROT werden kann.

    Ohne diesen Nachweis waere ein gruener Lauf wertlos: eine Pruefung, die
    nie anschlaegt, ist von einer erfuellten nicht zu unterscheiden.
    """
    s = _lies(ZIEL)
    fehlt = pruefe(s)
    if fehlt:
        print("Selbstprobe unmoeglich: der Bestand ist schon jetzt rot.")
        for g, b in fehlt:
            print("   %s -> %r" % (g, b))
        return 1

    schlimm = 0
    for gruppe, begriff in (("Werkzeuge: sechs Status", "Stillgelegt"),
                            ("Arbeitsscheine: elf Statuswerte", "bar bezahlt"),
                            ("Projektakte: dreizehn Unterseiten", "Checklisten")):
        # Jede Schreibweise aus der KOPIE entfernen, dann muss es rot werden.
        kopie = s
        for k in schreibweisen(begriff):
            kopie = kopie.replace(k, "___WEG___")
        neu = pruefe(kopie)
        traf = [(g, b) for g, b in neu if b == begriff]
        if traf:
            print("  OK   %-38s entfernt -> rot (%s)" % (repr(begriff), gruppe))
        else:
            print("  ROT  %-38s entfernt -> BLIEB GRUEN. Die Pruefung sieht "
                  "diesen Begriff nicht." % repr(begriff))
            schlimm += 1
    if schlimm:
        print("\nSelbstprobe GESCHEITERT: %d von 3 Entfernungen blieben "
              "unbemerkt." % schlimm)
        return 1
    print("\nSelbstprobe bestanden: die Pruefung kann rot werden.")
    return 0


def main(argv):
    if "--selbst" in argv:
        return selbstprobe()
    s = _lies(ZIEL)
    fehlt = pruefe(s)
    gesamt = sum(len(v) for v in BESTAND.values())
    if not fehlt:
        print("BESTAND GRUEN - %d Begriffe in %d Gruppen gefunden."
              % (gesamt, len(BESTAND)))
        return 0
    print("BESTAND ROT - %d von %d Begriffen fehlen:" % (len(fehlt), gesamt))
    for g, b in fehlt:
        print("   %-42s %r" % (g, b))
    print("\nEin fehlender Begriff heisst: eine Handlung, die der Nutzer "
          "vorher hatte,\nist im Quelltext nicht mehr da. Zurueckrollen, "
          "nicht nachbessern.")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
