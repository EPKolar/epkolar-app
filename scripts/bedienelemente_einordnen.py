# -*- coding: utf-8 -*-
"""Die 124 anklickbaren Nicht-Knoepfe einzeln einordnen.

DREI KLASSEN, wie im Auftrag:
  BEDIENELEMENT — loest eine Handlung aus, die es sonst nirgends gibt.
  DOPPELWEG     — loest etwas aus, das auch ueber einen echten Knopf
                  erreichbar ist.
  KEIN ELEMENT  — der onClick tut etwas Nebensaechliches (Aufklappen, Fokus)
                  oder ist ein Ueberbleibsel.

🔴 UND EINE VIERTE, die der Auftrag ausdruecklich zulaesst: UNSICHER. „Lieber
ein fehlender Zugang als ein Phantom in der Tab-Reihenfolge." Was hier landet,
wird NICHT angefasst.

Dieses Skript ordnet nicht abschliessend ein - es sammelt die ENTSCHEIDUNGS-
GRUNDLAGE: Ansicht, Tag, der Rumpf des onClick, und ob im selben Elternelement
ein echter Knopf steht, der dieselbe Funktion ruft. Die Einordnung selbst steht
in `docs/befunde/BEDIENELEMENTE_124.md` und ist von Hand nachgelesen.
"""
import io
import json
import os
import re
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import code_scan  # noqa: E402

WURZEL = os.path.dirname(HIER)
PFAD = os.path.join(WURZEL, "index.html")

ERZEUGER = re.compile(
    r"(?:createElement|(?<![A-Za-z0-9_$.])h)\(\s*['\"](\w+)['\"]\s*,")
NATIV = {"a", "input", "select", "textarea", "button", "option"}
# 🔴 Am 28.09.2026 erweitert. Das Muster verlangte vorher den
# Parameter OHNE Klammern und ein Komma direkt hinter dem Aufruf. Zwei
# reine Sperren fielen deshalb durch und standen als BEDIENELEMENT im
# Bericht:  (e)=>e.stopPropagation()  und  e=>e.stopPropagation()/*...*/
# Nach ihnen zu bauen haette zwei Phantome in die Tab-Reihenfolge
# gesetzt - die teurere Richtung dieses Fehlers.
NUR_STOP = re.compile(
    r"onClick\s*:\s*\(?\s*(?:e|ev|evt|_e)\s*\)?\s*=>\s*\{?\s*"
    r"(?:e|ev|evt|_e)\.stopPropagation\(\)\s*;?\s*\}?"
    r"(?:\s*/\*.*?\*/)?\s*[,}]", re.S)

# Handlungen, die nichts ausloesen, was es nicht auch anders gaebe:
# ein Aufklappen, ein Fokus, eine reine Auswahl im selben Bild.
NEBENSAECHLICH = re.compile(
    r"^\s*(?:e\s*=>\s*)?\{?\s*(?:"
    r"set(?:Open|Offen|Expand\w*|Show\w*|Auf\w*|Zu\w*|Collapsed?|Details?)\w*"
    r"|[\w.]*focus\(\)"
    r")", re.I)


def _props(text, m):
    i = m.end()
    while i < len(text) and text[i] in " \t\r\n":
        i += 1
    if i >= len(text) or text[i] != "{":
        return None, None
    pe = code_scan._klammer_zu(text, i, "{", "}")
    if pe <= 0:
        return None, None
    return text[i:pe], pe


def _onclick_rumpf(props):
    """Der Ausdruck hinter onClick:, bis zum Komma auf Tiefe 0."""
    i = props.find("onClick")
    if i < 0:
        return ""
    i = props.index(":", i) + 1
    tiefe, j, n = 0, i, len(props)
    while j < n:
        c = props[j]
        if c in "\"'`":
            j = code_scan._zeichenkette_ueberspringen(props, j)
            continue
        if c in "({[":
            tiefe += 1
        elif c in ")}]":
            if tiefe == 0:
                break
            tiefe -= 1
        elif c == "," and tiefe == 0:
            break
        j += 1
    return props[i:j].strip()


def _gerufene(rumpf):
    """Die Namen, die der Rumpf aufruft - ohne die Sprachmittel."""
    roh = re.findall(r"(?<![.\w])([A-Za-z_$][\w$]*)\s*\(", rumpf)
    return [x for x in roh
            if x not in ("if", "for", "while", "return", "typeof", "e",
                         "function", "switch", "catch")]


def sammeln():
    text = io.open(PFAD, encoding="utf-8", newline="").read()
    feld = code_scan.ist_code(text)
    dekl = [(m.start(), m.group(1))
            for m in re.finditer(r"function\s+([A-Z]\w+)\s*\(", text)
            if feld[m.start()]]

    def ansicht(p):
        nm = "(ausserhalb)"
        for q, n in dekl:
            if q <= p:
                nm = n
            else:
                break
        return nm

    # Alle Knopf-Rumpfe einmal einsammeln, um DOPPELWEG zu erkennen.
    knopf_ruft = {}
    for start, props, kinder in code_scan.knopf_stellen(text):
        for name in _gerufene(_onclick_rumpf(props or "")):
            knopf_ruft.setdefault(name, []).append(start)

    aus = []
    for m in ERZEUGER.finditer(text):
        if not feld[m.start()]:
            continue
        tag = m.group(1)
        if tag in NATIV or tag in ("img", "canvas"):
            continue
        props, pe = _props(text, m)
        if props is None or "onClick" not in props:
            continue
        if NUR_STOP.search(props):
            continue
        if "tabIndex" in props and ("onKeyDown" in props
                                    or "onKeyPress" in props):
            continue
        rumpf = _onclick_rumpf(props)
        ruft = _gerufene(rumpf)
        # 🔴 Enthaelt das Element SELBST einen Knopf? Dann darf es KEIN
        # role="button" bekommen - ein Knopf in einem Knopf ist ungueltiges
        # ARIA, und eine Vorlesehilfe liest dann Unsinn. Fuer solche Faelle
        # ist `tabIndex` plus Tastenbehandler OHNE `role` die richtige Form;
        # so ist es am 27.09. in ProjList gebaut worden.
        # 🔴 Steht die Stelle in einer WIEDERHOLUNG? Ein `.map(` davor, dessen
        # Klammer bei uns noch offen ist, heisst: dieses Element wird einmal je
        # Datensatz gerendert. Bei 185 Arbeitsscheinen ist ein Tab-Stopp je
        # Zelle kein Zugang mehr, sondern eine Reihenfolge, durch die niemand
        # mehr durchkommt - gemessen hat die Arbeitsscheinliste bei 1440 px
        # schon heute 1882 Stopps.
        wdh = 0
        suche = max(0, m.start() - 12000)
        for mm in re.finditer(r"\.map\s*\(", text[suche:m.start()]):
            p = suche + mm.end() - 1
            tiefe = 0
            for c in text[p:m.start()]:
                if c == "(":
                    tiefe += 1
                elif c == ")":
                    tiefe -= 1
            if tiefe > 0:
                wdh += 1
        klammer = text.find("(", m.start())
        ende = code_scan._klammer_zu(text, klammer, "(", ")") if klammer > 0 else -1
        rumpf_text = text[m.start():ende] if ende > 0 else ""
        enthaelt_knopf = bool(
            re.search(r"(?:createElement|(?<![A-Za-z0-9_$.])h)\(\s*['\"]button"
                      r"['\"]", rumpf_text))
        # Gibt es in der NAEHE einen echten Knopf mit derselben Funktion?
        nah = []
        for name in ruft:
            for kp in knopf_ruft.get(name, []):
                if abs(kp - m.start()) < 4000:
                    nah.append(name)
                    break
        aus.append({
            "pos": m.start(),
            "zeile": text.count("\n", 0, m.start()) + 1,
            "ansicht": ansicht(m.start()),
            "tag": tag,
            "rumpf": rumpf[:160],
            "ruft": ruft[:6],
            "knopf_daneben": sorted(set(nah)),
            "enthaelt_knopf": enthaelt_knopf,
            "in_wiederholung": wdh,
            "laenge": (ende - m.start()) if ende > 0 else -1,
            "nebensaechlich": bool(NEBENSAECHLICH.match(rumpf)),
            "props": props[:120],
        })
    return aus


if __name__ == "__main__":
    a = sammeln()
    print("Anklickbare Nicht-Knoepfe ohne Tastaturzugang: %d" % len(a))
    je = {}
    for x in a:
        je[x["ansicht"]] = je.get(x["ansicht"], 0) + 1
    print("je Ansicht:", dict(sorted(je.items(), key=lambda y: -y[1])))
    print("mit Knopf daneben (DOPPELWEG-Verdacht): %d"
          % len([x for x in a if x["knopf_daneben"]]))
    print("nebensaechlich (KEIN-ELEMENT-Verdacht): %d"
          % len([x for x in a if x["nebensaechlich"]]))
    ziel = os.path.join(HIER, "_bedienelemente_124.json")
    io.open(ziel, "w", encoding="utf-8", newline="").write(
        json.dumps(a, ensure_ascii=False, indent=1))
    print("geschrieben:", ziel)
