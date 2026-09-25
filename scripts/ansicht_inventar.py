# -*- coding: utf-8 -*-
"""Inventar einer Ansicht: was kann der Nutzer hier TUN und SEHEN?

WOZU
────
Der Bestandsschutz des UI-Umbaus verlangt vor und nach jeder Stufe dieselbe
Liste: alle Knoepfe, Felder, Auswahloptionen und angezeigten Werte der
betroffenen Ansicht. Jede Differenz muss begruendet werden, eine
unbegruendete ist ein Fehler.

Von Hand ist diese Liste bei 31.000 Zeichen Quelltext nicht zuverlaessig zu
erstellen - und eine Liste, der man nicht trauen kann, ist schlimmer als
keine, weil sie Sicherheit vortaeuscht.

WAS GEMESSEN WIRD
─────────────────
Aus dem QUELLTEXT der Komponente (nicht aus dem gezeichneten Schirm - dafuer
braeuchte es jeden Datenzustand):

  handler     onClick / onChange / onSubmit - die HANDLUNGEN. Ein Knopf darf
              anders aussehen und woanders stehen; verschwindet ein Handler,
              ist eine Handlung weg.
  texte       sichtbare Zeichenketten in React.createElement-Argumenten
  optionen    <option>-Werte und -Beschriftungen
  felder      input/select/textarea samt type und placeholder
  emoji       was durch Icons ersetzt werden soll
  groessen    fontSize-Werte - 12 ist die Untergrenze

WARUM HANDLER UND NICHT KNOEPFE
───────────────────────────────
"Knopf" ist eine Darstellungsfrage, und genau die darf sich aendern. Die
Handlung dahinter darf es nicht. Gezaehlt wird deshalb, was AUSGELOEST wird.

AUFRUF
──────
    python scripts/ansicht_inventar.py ProjList
    python scripts/ansicht_inventar.py ProjList --json vorher.json
    python scripts/ansicht_inventar.py ProjList --vergleich vorher.json
"""
import io
import json
import os
import re
import sys

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(WURZEL, "tests"))

EMOJI = re.compile(
    "[\U0001F300-\U0001FAFF←-⇿☀-➿⬀-⯿️]")


def _rumpf(name):
    from conftest import _extract_fn
    s = io.open(os.path.join(WURZEL, "index.html"),
                encoding="utf-8", newline="").read()
    b = _extract_fn(s, name)
    if not b:
        raise SystemExit(
            "Komponente %r nicht gefunden. Das ist rot, nicht gruen - ein "
            "leeres Inventar sieht sonst aus wie eine Ansicht ohne Knoepfe."
            % name)
    return b


def inventar(rumpf):
    """Alles, was der Nutzer TUN und SEHEN kann - als vergleichbare Mengen."""
    d = {}

    # Handlungen: die Ziel-Ausdruecke der Handler, nicht die Knoepfe.
    d["handler"] = sorted(set(
        re.findall(r"on(?:Click|Change|Submit|Input)\s*:\s*([^,}]{1,90})", rumpf)))

    # Sichtbare Texte: Zeichenketten, die als Kind uebergeben werden.
    texte = set()
    for t in re.findall(r'"((?:[^"\\]|\\.){2,60})"', rumpf):
        if re.search(r"[A-Za-zÄÖÜäöüß]", t) and not re.match(
                r"^(?:[a-z]+[A-Z]|#|\d|rgba?\(|/|https?:|\.)", t):
            texte.add(t)
    d["texte"] = sorted(texte)

    d["optionen"] = sorted(set(
        re.findall(r"createElement\(\s*'option'\s*,\s*\{[^}]*value:\s*([^,}]{1,40})",
                   rumpf)))
    d["felder"] = sorted(set(
        re.findall(r"createElement\(\s*'(input|select|textarea)'", rumpf)))
    d["platzhalter"] = sorted(set(re.findall(r'placeholder:\s*"([^"]{0,60})"', rumpf)))
    d["emoji"] = sorted(set(EMOJI.findall(rumpf)))
    d["groessen"] = sorted(set(int(x) for x in re.findall(r"fontSize:\s*(\d+)", rumpf)))
    d["ariaLabel"] = sorted(set(re.findall(r'aria-label":\s*"([^"]{0,50})"', rumpf)))
    return d


def zeige(name, d):
    print("=" * 68)
    print("INVENTAR  %s" % name)
    print("=" * 68)
    for schluessel in ("handler", "felder", "platzhalter", "optionen",
                       "emoji", "groessen", "ariaLabel"):
        w = d.get(schluessel, [])
        print("\n%s (%d)" % (schluessel.upper(), len(w)))
        for x in w:
            print("   %s" % (x if isinstance(x, str) else repr(x)))
    print("\nTEXTE (%d) - die ersten 40" % len(d.get("texte", [])))
    for t in d.get("texte", [])[:40]:
        print("   %r" % t)


def vergleiche(alt, neu):
    """Jede Differenz einzeln - unbegruendet ist eine davon ein Fehler."""
    schlimm = 0
    for schluessel in sorted(set(alt) | set(neu)):
        a, b = set(alt.get(schluessel, [])), set(neu.get(schluessel, []))
        weg, dazu = sorted(a - b), sorted(b - a)
        if not weg and not dazu:
            continue
        print("\n%s" % schluessel.upper())
        for x in weg:
            print("   WEG   %r" % (x,))
            if schluessel in ("handler", "optionen", "felder", "platzhalter"):
                schlimm += 1
        for x in dazu:
            print("   NEU   %r" % (x,))
    print()
    if schlimm:
        print("%d Streichungen in den harten Mengen (Handlungen, Optionen, "
              "Felder)." % schlimm)
        print("Jede davon MUSS begruendet sein, sonst ist sie ein Fehler.")
        return 1
    print("Keine Streichung in den harten Mengen.")
    return 0


def main(argv):
    if not argv:
        raise SystemExit("Aufruf: python scripts/ansicht_inventar.py <Komponente>")
    name = argv[0]
    d = inventar(_rumpf(name))

    if "--json" in argv:
        ziel = argv[argv.index("--json") + 1]
        io.open(ziel, "w", encoding="utf-8", newline="\n").write(
            json.dumps(d, indent=1, ensure_ascii=False, sort_keys=True))
        print("Inventar geschrieben: %s" % ziel)
        for k in sorted(d):
            print("   %-12s %d" % (k, len(d[k])))
        return 0

    if "--vergleich" in argv:
        quelle = argv[argv.index("--vergleich") + 1]
        alt = json.loads(io.open(quelle, encoding="utf-8").read())
        print("Vergleich %s  (%s -> jetzt)" % (name, quelle))
        return vergleiche(alt, d)

    zeige(name, d)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
