# -*- coding: utf-8 -*-
"""Elemente mit `role="button"`, die KEINEN Namen tragen.

🔴 WARUM ES DIESEN MELDER GIBT - und warum der vorhandene ihn nicht ersetzt.

`code_scan.knopf_stellen` findet jedes `<button>` und `hat_namen` prueft, ob es
einen zugaenglichen Namen traegt. Beides ist geeicht und hat 17 namenlose
Knoepfe gefunden. Und beides ist fuer den Fall vom 28.09.2026 **prinzipiell
blind**: seine Grundgesamtheit ist `button`.

Der Fall war ein `<span role="button">` mit dem Inhalt `★`. Fuenf davon, eine
Bewertungsanzeige. Sie sind erst durch v3.9.975 zu Knoepfen geworden: das
Bauwerkzeug gab jeder Flaeche mit einem `onClick` die Rolle - und keinen Namen
dazu. Vorher war es vorlesbarer Text, danach fuenf "Schaltflaechen" ohne
Inhalt. **Eine Rolle ohne Namen ist schlechter als gar keine Rolle.**

Gefunden hat es eine MESSUNG, die einen Bereich geoeffnet hat
(`inline_bereiche_messen.py`), nicht ein Riegel. Dieser Melder schliesst die
Luecke im Quelltext, damit der naechste Fall nicht erst beim Oeffnen auffaellt.

🔴 WAS ER SICHER SAGT UND WAS NICHT
Ein Element traegt einen Namen, wenn es `aria-label` oder `title` hat ODER
wenn sein INHALT Buchstaben oder Ziffern enthaelt. Das Erste ist sicher
messbar, das Zweite nur, solange der Inhalt ein LITERAL ist. Steht dort eine
Variable (`x.t`, `label`), kann dieser Melder nichts beweisen - genau an
dieser Stelle hat mich am 27.09. ein eigener Befund zweimal getaeuscht: zwei
von drei "namenlosen Emoji-Knoepfen" waren falsch, der Name stand in einer
Variablen.

Deshalb drei Toepfe statt zwei:
    NAMENLOS   - Inhalt ist ein Literal OHNE Buchstaben/Ziffern, kein
                 aria-label, kein title. Das ist ein Befund.
    UNSICHER   - Inhalt ist keine auswertbare Zeichenkette. KEIN Befund,
                 sondern eine Stelle, die ein Mensch ansehen muss.
    BENANNT    - alles andere.

Die Trennung ist der ganze Punkt: ein Melder, der UNSICHER zu NAMENLOS
schlaegt, meldet Phantome; einer, der es zu BENANNT schlaegt, verschweigt
Befunde. Beide Zahlen stehen im Bericht.
"""
import io
import json
import os
import re
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
WURZEL = os.path.dirname(HIER)

import code_scan  # noqa: E402

# Erzeuger mit einem Tag in Anfuehrungszeichen - beide Schreibweisen, beide
# Anfuehrungszeichen. Dasselbe Alphabet wie code_scan; siehe dort, warum.
ERZEUGER = re.compile(
    r"(?:createElement|(?<![A-Za-z0-9_$.])h)\(\s*['\"](\w+)['\"]\s*,")

# 🔴 `role` WIRD KLAMMERSICHER GELESEN, NICHT PER REGEX GESUCHT.
#    Die erste Fassung benutzte
#        role\s*:\s*(?:\([^()]{0,300}\)\s*\?\s*)?['"]button['"]
#    und war damit blind fuer genau die Form, um die es geht - das
#    Bauwerkzeug aus v3.9.975 erzeugt
#        role: (onChange?()=>onChange(i):undefined)?"button":undefined
#    mit GESCHACHTELTEN Klammern, die `[^()]` nicht durchlaesst. Der Koeder
#    hat es gemeldet, bevor eine einzige Zahl entstanden ist.
#    Gelesen wird jetzt der Wert bis zum Komma auf oberster Ebene.
def _eigenschaft(props, name):
    """Der Werttext von `name` auf der OBERSTEN Ebene, oder None."""
    i, n, tiefe = 0, len(props), 0
    while i < n:
        c = props[i]
        if c in "\"'`":
            i = code_scan._zeichenkette_ueberspringen(props, i)
            continue
        if c in "({[":
            tiefe += 1
        elif c in ")}]":
            tiefe -= 1
        elif tiefe == 1 and props.startswith(name, i):
            vor = props[i - 1] if i else "{"
            nach = props[i + len(name):i + len(name) + 2].lstrip()
            if vor in "{,\"' \t\r\n" and nach[:1] == ":":
                j = props.index(":", i + len(name)) + 1
                t, k = 0, j
                while k < n:
                    d = props[k]
                    if d in "\"'`":
                        k = code_scan._zeichenkette_ueberspringen(props, k)
                        continue
                    if d in "({[":
                        t += 1
                    elif d in ")}]":
                        if t == 0:
                            break
                        t -= 1
                    elif d == "," and t == 0:
                        break
                    k += 1
                return props[j:k].strip()
        i += 1
    return None

# Ein Zeichen, das einen Namen traegt: Buchstabe oder Ziffer, in JEDER
# Schrift. `\w` reicht nicht - es schliesst den Unterstrich ein und haengt
# von der Spracheinstellung ab.
WORTZEICHEN = re.compile(r"[^\W\d_]|\d", re.UNICODE)


def _teile(ausdruck, trenner):
    """Zerlegt auf der OBERSTEN Ebene an `trenner` (ein Zeichen)."""
    aus, letzt, t, i, n = [], 0, 0, 0, len(ausdruck)
    while i < n:
        c = ausdruck[i]
        if c in "\"'`":
            i = code_scan._zeichenkette_ueberspringen(ausdruck, i)
            continue
        if c in "({[":
            t += 1
        elif c in ")}]":
            t -= 1
        elif c == trenner and t == 0:
            aus.append(ausdruck[letzt:i])
            letzt = i + 1
        i += 1
    aus.append(ausdruck[letzt:])
    return aus


def _werte(ausdruck):
    """Die MOEGLICHEN Werte eines Ausdrucks als Liste, oder None (unbekannt).

    🔴 DIESE FUNKTION IST DIE KORREKTUR EINES EIGENEN FEHLALARMS.
    Die erste Fassung sammelte einfach alle Zeichenketten-Literale im
    Kindteil. Damit meldete sie eine Sortier-Kopfzeile als NAMENLOS:

        , h.l, h.c?sortArrow(h.c):""

    Der Name steht in `h.l` - einer VARIABLEN. Das einzige Literal ist das
    leere `""` aus dem anderen Zweig, und weil es keine Buchstaben traegt,
    galt das Element als namenlos. Genau die Form, an der ich am 27.09. schon
    zweimal falsch lag: zwei von drei "namenlosen Emoji-Knoepfen" waren
    keine, der Name stand in einer Variablen.

    Gezaehlt werden deshalb die moeglichen WERTE, nicht die vorkommenden
    Literale: ein Bedingungsausdruck `a ? X : Y` hat die Werte von X und Y -
    die Bedingung selbst ist kein Wert. Alles andere ist UNBEKANNT, und
    unbekannt heisst hier: ein Mensch muss hinsehen.
    """
    a = ausdruck.strip()
    if not a:
        return []
    frage = _teile(a, "?")
    if len(frage) > 1:
        rest = "?".join(frage[1:])
        zweige = _teile(rest, ":")
        if len(zweige) >= 2:
            links = _werte(zweige[0])
            rechts = _werte(":".join(zweige[1:]))
            if links is None or rechts is None:
                return None
            return links + rechts
        return None
    if (a[0] in "\"'"
            and code_scan._zeichenkette_ueberspringen(a, 0) == len(a)):
        return [a[1:-1]]
    return None          # Variable, Aufruf, Ausdruck - unbekannt


def _kinder_literale(kinder):
    """(bekannte Werte, ob ein Teil unbekannt ist).

    🔴 DIE ZWEITE KORREKTUR AN DIESER STELLE, UND SIE GEHT IN DIE ANDERE
    RICHTUNG. Die vorige Fassung gab None zurueck, sobald IRGENDEIN Teil
    unbekannt war - und meldete damit eine Sortier-Kopfzeile

        , "Nummer", sortArrow("nummer")

    als "muss ein Mensch ansehen". Sie traegt das Literal "Nummer"; der
    zugaengliche Name eines Elements ist die Verkettung ALLER Kinder, also
    genuegt EIN wortfuehrendes Literal, egal was daneben unbekannt ist.
    Von 7 unsicheren wurden so 55 - eine Liste, die niemand mehr durchsieht,
    ist genauso wertlos wie eine falsche Null.

    Die Einordnung ist deshalb monoton:
        ein bekanntes Wort      -> BENANNT   (sicher)
        sonst etwas Unbekanntes -> UNSICHER  (ansehen)
        sonst                   -> NAMENLOS  (Befund)
    """
    aus, unbekannt = [], False
    for teil in _teile(kinder, ","):
        if not teil.strip():
            continue
        w = _werte(teil)
        if w is None:
            unbekannt = True
        else:
            aus.extend(w)
    return aus, unbekannt


def einordnen(text):
    """(namenlos, unsicher, benannt) je als Liste von (zeile, tag, probe)."""
    feld = code_scan.ist_code(text)
    namenlos, unsicher, benannt = [], [], []
    for m in ERZEUGER.finditer(text):
        if not feld[m.start()]:
            continue
        tag = m.group(1)
        if tag == "button":
            continue          # dafuer gibt es code_scan.knopf_stellen
        i = m.end()
        while i < len(text) and text[i] in " \t\r\n":
            i += 1
        if i >= len(text) or text[i] != "{":
            continue
        pe = code_scan._klammer_zu(text, i, "{", "}")
        if pe <= 0:
            continue
        props = text[i:pe]
        rolle = _eigenschaft(props, "role")
        if rolle is None:
            rolle = _eigenschaft(props, '"role"') or _eigenschaft(props, "'role'")
        if not rolle or '"button"' not in rolle and "'button'" not in rolle:
            continue
        zeile = text.count("\n", 0, m.start()) + 1
        if code_scan.hat_namen(props):
            benannt.append((zeile, tag, "aria-label/title"))
            continue
        auf = text.rfind("(", m.start(), m.end())
        ende = code_scan._klammer_zu(text, auf, "(", ")")
        kinder = text[pe:ende - 1] if ende > pe else ""
        lit, unbekannt = _kinder_literale(kinder)
        if any(WORTZEICHEN.search(s) for s in lit):
            benannt.append((zeile, tag, "Inhalt: " + "/".join(lit)[:40]))
        elif unbekannt:
            unsicher.append((zeile, tag, kinder.strip()[:60]))
        else:
            namenlos.append((zeile, tag, "Inhalt: " + "/".join(lit)[:40]))
    return namenlos, unsicher, benannt


# ── Eichung ────────────────────────────────────────────────────────────────
# Ein Koeder JE FORM. Ein Koeder, der die Luecke des Musters teilt,
# bestaetigt nur die Blindheit.
KOEDER = [
    # (Text, erwarteter Topf)
    ("h('span',{role:\"button\",onClick:f},'★')", "namenlos"),
    ("React.createElement('span', { role: \"button\" }, \"✕\")", "namenlos"),
    # Die BEDINGTE Form, die das Bauwerkzeug aus v3.9.975 erzeugt:
    ("h('span',{role: (a?()=>b():undefined)?\"button\":undefined}, '★')",
     "namenlos"),
    # Inhalt als Ausdruck mit zwei Literalen - beide ohne Wortzeichen.
    ("h('span',{role:'button'}, i<=val?\"★\":\"☆\")", "namenlos"),
    # Mit Namen ueber aria-label.
    ("h('span',{role:'button','aria-label':\"Loeschen\"}, '✕')", "benannt"),
    # Mit Namen ueber den Inhalt.
    ("h('div',{role:'button'}, 'Speichern')", "benannt"),
    # Inhalt aus einer Variablen - daraus laesst sich NICHTS schliessen.
    ("h('div',{role:'button'}, x.t)", "unsicher"),
    # Gegenprobe: ein echtes button-Element gehoert NICHT hierher.
    ("h('button',{},'★')", None),
    # Gegenprobe: role=listbox ist kein Knopf.
    ("h('div',{role:'listbox'},'★')", None),
    # 🔴 DER FEHLALARM, den die erste Fassung erzeugt hat. Der Name steht in
    #    der VARIABLEN `h.l`; das einzige Literal ist das leere `""` aus dem
    #    anderen Zweig eines Bedingungsausdrucks. Wer Literale zaehlt statt
    #    moegliche WERTE, meldet hier einen namenlosen Knopf, der keiner ist.
    ("h('th',{role:'button'}, h.l, h.c?pfeil(h.c):\"\")", "unsicher"),
    # Und die Gegenprobe dazu: BEIDE Zweige Literale ohne Wortzeichen -
    #    dann ist es wirklich namenlos.
    ("h('span',{role:'button'}, a?\"▲\":\"▼\")", "namenlos"),
    # 🔴 Der Fehlalarm der ZWEITEN Fassung: ein wortfuehrendes Literal neben
    #    einem unbekannten Teil ist SICHER benannt, nicht unsicher.
    ("h('th',{role:'button'}, \"Nummer\", pfeil(\"nummer\"))", "benannt"),
    # Ein Bedingungsausdruck, dessen einer Zweig Buchstaben traegt: benannt.
    ("h('span',{role:'button'}, a?\"Mehr\":\"▼\")", "benannt"),
]


def eichen():
    schief = []
    for text, soll in KOEDER:
        nl, un, be = einordnen(text)
        ist = ("namenlos" if nl else "unsicher" if un else
               "benannt" if be else None)
        if ist != soll:
            schief.append((text[:52], soll, ist))
    return schief


def main():
    schief = eichen()
    if schief:
        for t, soll, ist in schief:
            print("\U0001F534 Koeder %r: erwartet %s, gemessen %s"
                  % (t, soll, ist))
        print("Der Melder ist nicht geeicht. Die Zahlen unten waeren wertlos.")
        return 2
    print("Koeder: %d von %d richtig (davon %d Gegenproben)"
          % (len(KOEDER), len(KOEDER),
             sum(1 for _, s in KOEDER if s is None)))

    text = io.open(os.path.join(WURZEL, "index.html"),
                   encoding="utf-8", newline="").read()
    nl, un, be = einordnen(text)
    print("\nrole=\"button\" auf Nicht-Knoepfen: %d"
          % (len(nl) + len(un) + len(be)))
    print("   \U0001F534 NAMENLOS : %d" % len(nl))
    print("   ❓ UNSICHER : %d  (Inhalt ist kein Literal - ansehen)"
          % len(un))
    print("   \U0001F7E2 BENANNT  : %d" % len(be))
    for zeile, tag, probe in nl:
        print("      Zeile %-6d %-5s %s" % (zeile, tag, probe))
    for zeile, tag, probe in un[:10]:
        print("      ? Zeile %-6d %-5s %s" % (zeile, tag, probe))

    ziel = os.path.join(WURZEL, "docs", "befunde", "ROLLE_OHNE_NAMEN.json")
    io.open(ziel, "w", encoding="utf-8", newline="").write(
        json.dumps({"namenlos": nl, "unsicher": un, "benannt": len(be)},
                   ensure_ascii=False, indent=1))
    print("\ngeschrieben:", ziel)
    return 1 if nl else 0


if __name__ == "__main__":
    sys.exit(main())
