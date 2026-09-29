# -*- coding: utf-8 -*-
"""Welche Container mit Tastenbehandler enthalten ein INTERAKTIVES Kind?

🔴 WOZU DIESE MESSUNG DA IST.
v3.9.975 gab Containern `role="button"`, `tabIndex` und einen Tastenbehandler
mit `preventDefault()`. Sitzt darin ein echter `<button>`, erzeugt dessen
Enter den Klick aus der VORGABEHANDLUNG des keydown - der steigt zum
Container auf, `preventDefault()` faellt, und der Klick des inneren Knopfes
fällt aus, waehrend die Container-Aktion laeuft.

v3.9.985 hat allen gebauten Behandlern den Waechter

    if(e.target!==e.currentTarget)return;

vorangestellt. Damit ist die Klasse geschlossen - aber eine offene Frage
blieb: **welche Container waren ueberhaupt gefaehrlich?** Mein
Browser-Melder (`tastenkapern_messen.py`) erreicht die betroffenen Zustaende
nicht (Kundenansicht, geoeffnete Lightbox, aufgeklappte Karte) und meldet das
ausdruecklich als misslungenen Griff. Diese Messung beantwortet die Frage am
Quelltext.

🔴 STRUKTURELL, NICHT PER ZEILEN-GREP. Die Kinder eines Elements stehen auf
Folgezeilen; ein flaches Muster unterschaetzt systematisch. Der Kindteil wird
per Klammerabgleich bestimmt - vom oeffnenden `(` des Erzeugers bis zur
passenden schliessenden Klammer, abzueglich des Eigenschaftenobjekts.

🔴 UND ES WIRD NICHT GERATEN. Ein Kind, das ueber eine Variable oder einen
Spread hereinkommt, ist von hier aus nicht entscheidbar. Solche Faelle
kommen in den Topf PRUEFEN, nicht in GEFAEHRLICH und nicht in OK.
"""
import io
import os
import re
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
WURZEL = os.path.dirname(HIER)

import code_scan  # noqa: E402

WACHT = "if(e.target!==e.currentTarget)return;"

ERZEUGER = re.compile(
    r"(?:React\.createElement|createElement|(?<![A-Za-z0-9_$.])h)\(\s*"
    r"(['\"])(\w+)\1\s*,")

# Was als interaktives Kind zaehlt.
INTERAKTIV = ("button", "a", "input", "select", "textarea", "summary")

# Ein Kind, dessen Herkunft von hier aus nicht entscheidbar ist.
UNKLAR = re.compile(r"\.\.\.[A-Za-z_$]|React\.createElement\(\s*[A-Z]"
                    r"|(?<![A-Za-z0-9_$.])h\(\s*[A-Z]")


def _props_und_kinder(text, m):
    """(Eigenschaftentext, Kindtext) eines Erzeugeraufrufs."""
    auf = text.rfind("(", m.start(), m.end())
    ende = code_scan._klammer_zu(text, auf, "(", ")")
    if ende <= 0:
        return None, None
    i = m.end()
    while i < len(text) and text[i] in " \t\r\n":
        i += 1
    if i < len(text) and text[i] == "{":
        pe = code_scan._klammer_zu(text, i, "{", "}")
        if pe <= 0:
            return None, None
        return text[i:pe], text[pe:ende - 1]
    return "", text[i:ende - 1]


def _interaktive_kinder(kinder):
    """Liste der interaktiven Kind-Tags im Teilbaum."""
    aus = []
    for m in ERZEUGER.finditer(kinder):
        tag = m.group(2)
        if tag not in INTERAKTIV:
            continue
        if tag == "a":
            # Nur ein Link MIT Ziel ist ein Bedienelement.
            p, _k = _props_und_kinder(kinder, m)
            if not p or "href" not in p:
                continue
        aus.append(tag)
    # Ein weiteres role="button" im Teilbaum zaehlt ebenfalls.
    for m in re.finditer(r'role\s*:\s*[\'"]button[\'"]', kinder):
        aus.append('role="button"')
    return aus


def _kind_beschriftung(kinder):
    """Die Beschriftung des ersten interaktiven Kindes.

    🔴 Sie steht AM KNOPF, nicht im Kindtext des Containers. Der erste
    Entwurf nahm das erste Zeichenkettenliteral im Teilbaum - das ist fast
    immer ein Stilwert ("flex", "ellipsis", "4px 10px"), und die Tabelle war
    dadurch unlesbar. Ein Bericht, den niemand lesen kann, ist kein Bericht.

    Gesucht wird in dieser Reihenfolge: `aria-label` des Kindes, sein
    `title`, und zuletzt sein Textinhalt - also das, was hinter dem
    Eigenschaftenobjekt steht.
    """
    for m in ERZEUGER.finditer(kinder):
        if m.group(2) not in INTERAKTIV:
            continue
        props, text = _props_und_kinder(kinder, m)
        if props is None:
            continue
        for muster in (r"""['"]?aria-label['"]?\s*:\s*['"]([^'"]{2,46})""",
                       r"""title\s*:\s*['"]([^'"]{2,46})"""):
            t = re.search(muster, props)
            if t:
                return t.group(1)
        t = re.search(r"""['"]([^'"]{2,46})['"]""", (text or "")[:200])
        if t:
            return t.group(1)
    return ""


def messen(text):
    ist = code_scan.ist_code(text)
    faelle = []
    for m in ERZEUGER.finditer(text):
        if not ist[m.start()]:
            continue
        props, kinder = _props_und_kinder(text, m)
        if props is None:
            continue
        if "onKeyDown" not in props or "preventDefault" not in props:
            continue
        geschuetzt = WACHT in props
        kids = _interaktive_kinder(kinder or "")
        unklar = bool(UNKLAR.search(kinder or ""))
        if geschuetzt:
            klasse = "OK"
        elif kids:
            klasse = "GEFAEHRLICH"
        elif unklar:
            klasse = "PRUEFEN"
        else:
            klasse = "OK"
        # 🔴 Die zweite Spalte ist der Punkt dieser Messung: WAERE der
        #    Container ohne den Waechter gefaehrlich? Sie sagt, was die Kur
        #    aus v3.9.985 tatsaechlich gerettet hat.
        ohne_waechter = ("GEFAEHRLICH" if kids
                         else ("PRUEFEN" if unklar else "OK"))
        zweck = ""
        a = re.search(r'[\'"]?aria-label[\'"]?\s*:\s*"([^"]{0,50})"', props)
        t = re.search(r'title\s*:\s*"([^"]{0,50})"', props)
        if a:
            zweck = a.group(1)
        elif t:
            zweck = t.group(1)
        else:
            # 🔴 Die Beschriftung steht nicht im Kindtext, sondern AM
            #    INNEREN KNOPF. Der erste Entwurf nahm das erste Literal
            #    im Kindteil - das ist fast immer ein Stilwert ("flex",
            #    "ellipsis", "4px 10px"), und die Tabelle war unlesbar.
            #    Ein Bericht, den niemand lesen kann, ist kein Bericht.
            zweck = _kind_beschriftung(kinder or "")
        faelle.append({
            "zeile": text.count("\n", 0, m.start()) + 1,
            "tag": m.group(2), "zweck": zweck[:46],
            "geschuetzt": geschuetzt, "kinder": sorted(set(kids)),
            "unklar": unklar, "klasse": klasse,
            "ohne_waechter": ohne_waechter})
    return faelle


def main(argv):
    text = io.open(os.path.join(WURZEL, "index.html"),
                   encoding="utf-8", newline="").read()
    faelle = messen(text)
    von = {"OK": 0, "PRUEFEN": 0, "GEFAEHRLICH": 0}
    ohne = dict(von)
    for f in faelle:
        von[f["klasse"]] += 1
        ohne[f["ohne_waechter"]] += 1

    zeilen = []
    zeilen.append("# Container mit Tastenbehandler und `preventDefault()`\n")
    zeilen.append("> Messlauf, keine Aenderung. Erzeugt von "
                  "`scripts/keydown_container_audit.py`.\n")
    zeilen.append("")
    zeilen.append("**%d Container** mit `onKeyDown` + `preventDefault()` im "
                  "Code.\n" % len(faelle))
    zeilen.append("")
    zeilen.append("| | mit Waechter (heute) | ohne Waechter (vor v3.9.985) |")
    zeilen.append("|---|---:|---:|")
    for k, sym in (("GEFAEHRLICH", "🔴"), ("PRUEFEN", "🟡"), ("OK", "🟢")):
        zeilen.append("| %s %s | %d | %d |" % (sym, k, von[k], ohne[k]))
    zeilen.append("")
    zeilen.append("🔴 **Die rechte Spalte ist der eigentliche Befund**: sie "
                  "sagt, wie viele Container\nvor v3.9.985 den Tastendruck "
                  "eines inneren Bedienelements gefressen haetten.\n")
    zeilen.append("")
    heikel = [f for f in faelle if f["ohne_waechter"] == "GEFAEHRLICH"]
    zeilen.append("## Die %d Container mit interaktivem Kind\n" % len(heikel))
    zeilen.append("| Zeile | Tag | Zweck | innere Bedienelemente | heute |")
    zeilen.append("|---|---|---|---|---|")
    for f in sorted(heikel, key=lambda x: x["zeile"]):
        zeilen.append("| %d | `%s` | %s | %s | %s |"
                      % (f["zeile"], f["tag"], f["zweck"] or "—",
                         ", ".join("`%s`" % k for k in f["kinder"]),
                         "🟢 geschuetzt" if f["geschuetzt"] else "🔴 OFFEN"))
    pruefen = [f for f in faelle if f["ohne_waechter"] == "PRUEFEN"]
    if pruefen:
        zeilen.append("\n## %d Faelle, die von hier aus nicht entscheidbar "
                      "sind\n" % len(pruefen))
        zeilen.append("Ein Kind ueber eine Variable, einen Spread oder eine "
                      "Komponente ist im Quelltext\nnicht aufloesbar. Diese "
                      "Faelle stehen bewusst NICHT in einer der beiden "
                      "anderen\nSpalten - raten waere hier schlimmer als "
                      "nicht wissen.\n")
        zeilen.append("| Zeile | Tag | Zweck | heute |")
        zeilen.append("|---|---|---|---|")
        for f in sorted(pruefen, key=lambda x: x["zeile"])[:40]:
            zeilen.append("| %d | `%s` | %s | %s |"
                          % (f["zeile"], f["tag"], f["zweck"] or "—",
                             "🟢 geschuetzt" if f["geschuetzt"] else "🔴 OFFEN"))
    # 🔴 ZWEI ORTE, UND DAS IST ABSICHT. `build/` ist git-ignoriert - ein
    #    Bericht, der nur dort liegt, ist beim naechsten frischen Arbeitsbaum
    #    weg. Die dauerhafte Fassung gehoert zu den anderen Befunden.
    inhalt = "\n".join(zeilen) + "\n"
    ziele = []
    for ordner, name in ((os.path.join(WURZEL, "build"),
                          "keydown_container_audit.md"),
                         (os.path.join(WURZEL, "docs", "befunde"),
                          "KEYDOWN_CONTAINER.md")):
        if not os.path.isdir(ordner):
            os.makedirs(ordner)
        pfad = os.path.join(ordner, name)
        io.open(pfad, "w", encoding="utf-8", newline="").write(inhalt)
        ziele.append(pfad)
    ziel = " und ".join(ziele)

    print("%d Container mit onKeyDown + preventDefault" % len(faelle))
    print("   heute          : \U0001F534 %d  \U0001F7E1 %d  \U0001F7E2 %d"
          % (von["GEFAEHRLICH"], von["PRUEFEN"], von["OK"]))
    print("   ohne Waechter  : \U0001F534 %d  \U0001F7E1 %d  \U0001F7E2 %d"
          % (ohne["GEFAEHRLICH"], ohne["PRUEFEN"], ohne["OK"]))
    print("\ngeschrieben:", ziel)
    if von["GEFAEHRLICH"]:
        print("\U0001F534 %d Container sind HEUTE noch offen." % von["GEFAEHRLICH"])
        for f in sorted(faelle, key=lambda x: x["zeile"]):
            if f["klasse"] == "GEFAEHRLICH":
                print("      Zeile %-6d %s  -> %s"
                      % (f["zeile"], f["zweck"][:40], ", ".join(f["kinder"])))
    return 1 if von["GEFAEHRLICH"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
