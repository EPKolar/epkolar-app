# -*- coding: utf-8 -*-
"""Aus den Rohdaten der beiden Laeufe die Tabellen des Berichts erzeugen.

Zwei Rohdateien, beide von DEMSELBEN Messskript an DERSELBEN index.html:
  scripts/_echtmengen_rohdaten.json      - neue Saat (Echtmengen)
  scripts/_echtmengen_rohdaten_alt.json  - alte, duenne Saat (v3.9.954-Stand)

Nur so trennt der Vergleich „die Saat war zu duenn" von „der Umbau hat nichts
geaendert": ein Vergleich gegen die Zahlen eines ANDEREN Skripts vergleicht
zwei Dinge auf einmal.

    python scripts/echtmengen_tabellen.py
"""
import io
import json
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)


def _lesen(name):
    p = os.path.join(HIER, name)
    if not os.path.exists(p):
        return None
    return json.loads(io.open(p, encoding="utf-8", newline="").read())


def _stempel(a):
    if a.get("abbruch"):
        return "ABBRUCH"
    if a.get("nicht_erreicht"):
        return "nicht erreicht"
    if a.get("tor_a") or a.get("tor_b"):
        return "**nicht aussagekraeftig**"
    return "gemessen"


def _z(a):
    return a.get("zahlen") or {}


def main():
    neu = _lesen("_echtmengen_rohdaten.json")
    alt = _lesen("_echtmengen_rohdaten_alt.json")
    if not neu:
        print("Rohdaten der neuen Saat fehlen.")
        return 2
    A = print

    A("### Tabelle 1 - alle Aufnahmen, neue Saat")
    A("")
    A("| Ansicht | Gruppe | Breite | Urteil | <12 px | Tippziel <44 px | "
      "Ueberlauf verloren | Ueberlauf rollt | Emoji in Knopftext | "
      "Icon ohne Namen | Zeilen | Knoepfe |")
    A("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for a in neu["aufnahmen"]:
        z = _z(a)
        A("| %s | %s | %d | %s | %s | %s | %s | %s | %s | %s | %s | %s |"
          % (a.get("titel") or a["kuerzel"], a.get("gruppe"), a["breite"],
             _stempel(a), z.get("klein12"), z.get("tipp44"),
             z.get("ueberlauf_verloren"), z.get("ueberlauf_roller"),
             z.get("pikto_im_text"), z.get("icon_ohne_namen"),
             z.get("zeilen"), z.get("knoepfe")))
    A("")

    if alt:
        paar = {}
        for a in alt["aufnahmen"]:
            paar[(a["kuerzel"], a["breite"])] = a
        A("### Tabelle 2 - neue Saat gegen die ALTE, duenne Saat")
        A("")
        A("Dasselbe Messskript, dieselbe `index.html`, nur die Saat ist "
          "verschieden.")
        A("")
        A("| Ansicht | Breite | <12 px alt -> neu | Tippziel alt -> neu | "
          "verloren alt -> neu | rollt alt -> neu | Emoji alt -> neu | "
          "Icon alt -> neu | Zeilen alt -> neu |")
        A("|---|---|---|---|---|---|---|---|---|")
        for a in neu["aufnahmen"]:
            b = paar.get((a["kuerzel"], a["breite"]))
            if not b:
                continue
            za, zb = _z(a), _z(b)

            def pf(k):
                x, y = zb.get(k), za.get(k)
                if x is None and y is None:
                    return "—"
                mark = ""
                if isinstance(x, int) and isinstance(y, int) and y != x:
                    mark = " **%+d**" % (y - x)
                return "%s -> %s%s" % (x, y, mark)
            A("| %s | %d | %s | %s | %s | %s | %s | %s | %s |"
              % (a.get("titel") or a["kuerzel"], a["breite"],
                 pf("klein12"), pf("tipp44"), pf("ueberlauf_verloren"),
                 pf("ueberlauf_roller"), pf("pikto_im_text"),
                 pf("icon_ohne_namen"), pf("zeilen")))
        A("")

        A("### Tabelle 3 - Summen")
        A("")
        A("| Groesse | alte Saat | neue Saat | Unterschied |")
        A("|---|---|---|---|")
        for k, label in (("klein12", "Elemente unter 12 px"),
                         ("tipp44", "Tippziele unter 44 px"),
                         ("ueberlauf_verloren", "Ueberlauf, Inhalt verloren"),
                         ("ueberlauf_roller", "Ueberlauf, Behaelter rollt"),
                         ("pikto_im_text", "Emoji in Knopftexten"),
                         ("icon_ohne_namen", "Icon-Knoepfe ohne Namen"),
                         ("zeilen", "Tabellenzeilen"),
                         ("knoepfe", "sichtbare Knoepfe")):
            sa = sum(_z(a).get(k) or 0 for a in neu["aufnahmen"])
            sb = sum(_z(b).get(k) or 0 for b in alt["aufnahmen"])
            A("| %s | %d | %d | **%+d** |" % (label, sb, sa, sa - sb))
        A("")

    A("### Urteile")
    A("")
    n = len(neu["aufnahmen"])
    na = len([a for a in neu["aufnahmen"] if a.get("tor_a")])
    nb = len([a for a in neu["aufnahmen"] if a.get("tor_b")])
    nr = len([a for a in neu["aufnahmen"]
              if a.get("nicht_erreicht") or a.get("abbruch")])
    A("* Aufnahmen: **%d**" % n)
    A("* Tor A (Saatmenge) verletzt: **%d**" % na)
    A("* Tor B (Saatmarken in der Ansicht) verletzt: **%d**" % nb)
    A("* nicht erreicht / abgebrochen: **%d**" % nr)
    A("")
    A("Nicht aussagekraeftige Aufnahmen, je mit Grund:")
    A("")
    for a in neu["aufnahmen"]:
        if a.get("tor_a") or a.get("tor_b") or a.get("nicht_erreicht") \
                or a.get("abbruch"):
            g = (a.get("tor_a") or []) + (a.get("tor_b") or [])
            if a.get("nicht_erreicht"):
                g = g + ["Ansicht nicht erreicht, Weg: %s" % a.get("weg")]
            if a.get("abbruch"):
                g = g + ["ABBRUCH: %s" % a.get("abbruch")]
            A("* **%s @ %d px** — %s"
              % (a.get("titel") or a["kuerzel"], a["breite"], "; ".join(g)))
    A("")
    A("### Die drei offenen Ansichten im Detail")
    A("")
    for kuerzel in ("planung", "fahrzeuge", "as_liste", "home", "zeit",
                    "abwesend"):
        for breite in (390, 1440):
            a = [x for x in neu["aufnahmen"]
                 if x["kuerzel"] == kuerzel and x["breite"] == breite]
            if not a:
                continue
            a = a[0]
            z = _z(a)
            A("**%s @ %d px** — <12px %s · Tippziel %s · verloren %s · "
              "rollt %s · Emoji %s · Icon %s · Zeilen %s · Marken %s"
              % (a.get("titel"), breite, z.get("klein12"), z.get("tipp44"),
                 z.get("ueberlauf_verloren"), z.get("ueberlauf_roller"),
                 z.get("pikto_im_text"), z.get("icon_ohne_namen"),
                 z.get("zeilen"), len(a.get("marken") or [])))
            s = a.get("schrift") or {}
            for x in (s.get("klein") or [])[:6]:
                A("  * %s px  `%s`  %s" % (x["px"], x["text"], x["weg"]))
            q = a.get("quer") or {}
            for x in (q.get("ursache") or [])[:3]:
                A("  * verloren: %s px breit, rechts %s, `%s`"
                  % (x["breite"], x["rechts"], x["weg"]))
            for x in (q.get("waagrechte_roller") or [])[:3]:
                A("  * rollt: +%s px, `%s`, breitestes Kind %s px"
                  % (x["ueberschuss"], x["weg"],
                     (x.get("breitestes_kind") or {}).get("breite")))
            p = a.get("pikto") or {}
            for x in (p.get("mit_text") or [])[:4]:
                A("  * Emoji `%s` in `%s`" % (x["zeichen"], x["text"]))
            i = a.get("icon") or {}
            for x in (i.get("ohne_hilfe") or [])[:4]:
                A("  * Icon ohne Namen `%s` in `%s`" % (x["zeichen"], x["weg"]))
            A("")
    return 0


if __name__ == "__main__":
    sys.exit(main())
