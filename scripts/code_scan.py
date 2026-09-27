# -*- coding: utf-8 -*-
"""Trennt CODE von KOMMENTAR und ZEICHENKETTE - richtig, nicht ungefaehr.

WARUM ES DIESES MODUL GIBT (26.09.2026)
──────────────────────────────────────
Ich habe Sebastian berichtet, im Code stehe kein `ww<600` mehr. Das war
FALSCH, und er hat es gefunden, indem er eine dieser Zeilen hereinkopiert:

    function WerkzeugView(...){ const isMob=ww<600; ...

Die Ursache war mein Zaehler, nicht der Code. Er suchte Blockkommentare mit

    re.finditer(r"/\\*[\\s\\S]*?\\*/", s)

und hielt damit jedes `/*` fuer einen Kommentaranfang - auch das in

    accept:"application/pdf,image/*"

Dieses `/*` wird nie geschlossen. Alles dahinter galt meinem Zaehler als
Kommentar, also die letzten ~80 kB der Datei mitsamt WerkzeugView. Er meldete
0 statt 1 - und ein Zaehler, der zu WENIG findet, meldet ein gruenes Ergebnis.

Drei Verfahren hatten mir vorher schon drei verschiedene Zahlen geliefert
(31 roh, 28 ueber nur_code, 13 ueber Zitatpaarung). Dass keine davon stimmte,
haette mir das Auseinanderlaufen sagen muessen.

WAS DIESES MODUL ANDERS MACHT
─────────────────────────────
Es laeuft EINMAL durch den Text und fuehrt einen Zustand mit: Code,
einfache/doppelte Zeichenkette, Vorlagenliteral, Zeilenkommentar,
Blockkommentar. Ein `/*` in einer Zeichenkette kann damit keinen Kommentar
eroeffnen, und ein `"` in einem Kommentar keine Zeichenkette.

Regulaere Ausdruecke (`/.../`) werden NICHT als eigener Zustand gefuehrt -
das braeuchte einen Parser, weil `/` auch Division ist. Stattdessen wird eine
vermutete Regex-Literal-Stelle als Code behandelt; das ist die sichere
Richtung, denn ein Fund zu viel laesst sich ansehen, ein Fund zu wenig nicht.

BENUTZUNG
─────────
    from code_scan import nur_code_stellen, ist_code

    for pos in nur_code_stellen(text, "ww<600"):
        ...                      # nur echte Code-Treffer

    ist_code(text)[i]            # True, wenn Zeichen i Code ist

AUFRUF VON HAND
───────────────
    python scripts/code_scan.py "ww<600"
    python scripts/code_scan.py "ww<600" --alle
"""
import io
import os
import re
import sys

CODE, EINF, DOPP, VORL, ZEILE, BLOCK = range(6)


# v3.9.959 ZWISCHENSPEICHER, mit Begruendung und mit Grenze.
# `ist_code` laeuft zeichenweise ueber 3,6 MB. Riegel, die mehrere Namen
# nachsehen, riefen es mehrfach: eine Datei mit zehn Abfragen brauchte 23 s.
# Ein Riegel, der die Kette messbar bremst, wird irgendwann uebersprungen -
# und ein uebersprungener Riegel meldet gruen, ohne zu messen.
#
# Der Schluessel ist Laenge UND md5, nicht die Laenge allein: Koeder-Faelle
# unterscheiden sich oft nur um wenige Zeichen, und ein Zwischenspeicher, der
# dem kaputten Text das Feld des heilen gibt, macht jede Probe gruen. Das waere
# schlimmer als der langsame Lauf.
# Hoechstens drei Eintraege (je ~3,6 MB), aelteste fallen heraus.
# Die Rueckgabe ist ein bytearray - wer es AENDERT, verdirbt den Speicher.
# Kein Aufrufer tut das; sie lesen nur.
_CODEFELD = {}
_CODEFELD_MAX = 3


def ist_code(text):
    """Bytefeld gleicher Laenge: True, wo das Zeichen CODE ist."""
    import hashlib
    _k = (len(text), hashlib.md5(text.encode("utf-8", "replace")).hexdigest())
    if _k in _CODEFELD:
        return _CODEFELD[_k]
    _feld = _ist_code_roh(text)
    if len(_CODEFELD) >= _CODEFELD_MAX:
        _CODEFELD.pop(next(iter(_CODEFELD)))
    _CODEFELD[_k] = _feld
    return _feld


def _ist_code_roh(text):
    """Die eigentliche Abtastung, ohne Zwischenspeicher."""
    n = len(text)
    aus = bytearray(n)
    zustand = CODE
    i = 0
    while i < n:
        c = text[i]
        if zustand == CODE:
            # REGEX-LITERAL. Ohne diesen Zweig reisst ein Ausdruck wie
            # /['"]/ oder /`/ den Abtaster aus dem Tritt: das
            # Anfuehrungszeichen darin eroeffnet eine Zeichenkette, die nie
            # geschlossen wird, und alles dahinter gilt als Zeichenkette.
            # Genau daran ist die erste Fassung gescheitert (7 von 22).
            # Ob ein / eine Division oder ein Regex-Anfang ist, entscheidet
            # das letzte bedeutsame Zeichen davor - nach ( , = : [ ! & | ? {
            # } ; oder einem Schluesselwort kann kein Divisor stehen.
            if c == "/" and i + 1 < n and text[i + 1] not in "*/":
                k = i - 1
                while k >= 0 and text[k] in " \t\r\n":
                    k -= 1
                davor = text[k] if k >= 0 else "("
                wort = text[max(0, k - 9):k + 1]
                if davor in "(,=:[!&|?{};+-~^%<>" or wort.endswith(
                        ("return", "typeof", "case", "in", "of", "new",
                         "delete", "void", "instanceof")):
                    # Das Ende suchen, DANN entscheiden - der erste Anlauf
                    # hat die Entscheidung in die Schleife gemischt und sich
                    # dabei aufgehaengt.
                    j = i + 1
                    in_klasse = False
                    ende = -1
                    while j < n:
                        d = text[j]
                        if d == "\\":
                            j += 2
                            continue
                        if d == "\n":
                            break          # unbeendet -> war doch keine Regex
                        if d == "[":
                            in_klasse = True
                        elif d == "]":
                            in_klasse = False
                        elif d == "/" and not in_klasse:
                            ende = j
                            break
                        j += 1
                    if ende >= 0:
                        for x in range(i, ende + 1):
                            aus[x] = 1
                        i = ende + 1
                        continue
                    # Doch kein Regex-Literal: das / ist eine Division.
                    aus[i] = 1
                    i += 1
                    continue
            if c == "/" and i + 1 < n and text[i + 1] == "*":
                zustand = BLOCK
                i += 2
                continue
            if c == "/" and i + 1 < n and text[i + 1] == "/":
                zustand = ZEILE
                i += 2
                continue
            if c == "'":
                zustand = EINF
            elif c == '"':
                zustand = DOPP
            elif c == "`":
                zustand = VORL
            else:
                aus[i] = 1
            i += 1
            continue
        if zustand == BLOCK:
            if c == "*" and i + 1 < n and text[i + 1] == "/":
                zustand = CODE
                i += 2
                continue
            i += 1
            continue
        if zustand == ZEILE:
            if c == "\n":
                zustand = CODE
                aus[i] = 1
            i += 1
            continue
        # in einer Zeichenkette
        if c == "\\":
            i += 2
            continue
        if (zustand == EINF and c == "'") or (zustand == DOPP and c == '"') \
                or (zustand == VORL and c == "`"):
            zustand = CODE
        elif zustand == VORL and c == "$" and i + 1 < n and text[i + 1] == "{":
            # Vorlagenliteral mit eingebettetem Ausdruck: der Inhalt IST Code.
            # Vereinfachung: bis zur passenden schliessenden Klammer als Code
            # markieren. Verschachtelte Vorlagen darin sind selten und werden
            # dann konservativ als Code gelesen - die sichere Richtung.
            tiefe = 0
            j = i + 1
            while j < n:
                if text[j] == "{":
                    tiefe += 1
                elif text[j] == "}":
                    tiefe -= 1
                    if tiefe == 0:
                        break
                aus[j] = 1
                j += 1
            i = j + 1
            continue
        i += 1
    return aus


EICHPROBE = [
    # (Muster, Anzahl, die im CODE stehen MUSS)
    # Grundgesamtheit, die sich nachrechnen laesst: jede ww<BP_MOB-Stelle ist
    # Code - in Kommentaren steht BP_MOB nur als Wort, nie als Vergleich.
    ("const isMob=ww<BP_MOB", None),
]


def eichen(text):
    """Prueft den Abtaster an einer Menge, deren Antwort bekannt ist.

    WARUM DAS HIER STEHT
    ────────────────────
    Die erste Fassung dieses Moduls hat 8 von 27 ww<BP_MOB-Stellen als Code
    erkannt und 19 als Zeichenkette - und dabei nicht gemeldet, dass etwas
    faul ist. Ein Abtaster, der zu WENIG findet, liefert ein gruenes
    Ergebnis: "kommt im Code nicht vor" sieht genauso aus wie "ist
    aufgeraeumt".

    Die Probe ist einfach: `const isMob=ww<...` ist immer eine Deklaration,
    also immer Code. Findet der Abtaster eine davon NICHT im Code, irrt er
    sich - und dann verweigert er die Auskunft, statt eine Zahl zu nennen,
    der man nicht trauen kann.

    Gibt (bestanden, gefunden, erwartet) zurueck.
    """
    feld = ist_code(text)
    stellen = [m.start() for m in re.finditer(r"const isMob\s*=\s*ww\s*<", text)]
    # Von diesen sind die in Changelog-Kommentaren abzuziehen. Statt sie zu
    # erraten: eine Deklaration steht IMMER hinter einem { oder ; oder einer
    # Zeilengrenze - im Kommentar steht davor Prosa.
    echte = [p for p in stellen
             if re.search(r"[{};]\s*$", text[max(0, p - 60):p])]
    gefunden = sum(1 for p in echte if feld[p])
    # EINE LEERE GRUNDGESAMTHEIT BESTEHT KEINE PROBE.
    # Der Koeder in tests/test_code_scan_v936.py hat genau das gefunden: mit
    # einem blind gemachten Abtaster war `echte` leer, und 0 == 0 galt als
    # bestanden. Eine Probe, die bei ausgefallener Messung gruen wird, ist
    # dieselbe Fehlerform, gegen die dieses Modul ueberhaupt gebaut wurde.
    if len(echte) < 5:
        return (False, gefunden, len(echte))
    return (gefunden == len(echte), gefunden, len(echte))


def nur_code_stellen(text, muster, regex=False):
    """Positionen, an denen `muster` im CODE steht - nach bestandener Eichung.

    Schlaegt die Eichung fehl, wird GEWORFEN statt gezaehlt. Eine Zahl aus
    einem nachweislich irrenden Abtaster ist schlimmer als keine.
    """
    ok, gef, erw = eichen(text)
    if not ok:
        raise SystemExit(
            "code_scan: EICHUNG GESCHEITERT - %d von %d isMob-Deklarationen "
            "als Code erkannt.\n"
            "  Der Abtaster irrt sich und nennt deshalb keine Zahl. Ein "
            "Abtaster, der zu wenig\n"
            "  findet, meldet ein gruenes Ergebnis - genau daran ist die "
            "erste Fassung dieses\n"
            "  Moduls gescheitert (8 von 27)." % (gef, erw))
    feld = ist_code(text)
    pat = re.compile(muster if regex else re.escape(muster))
    return [m.start() for m in pat.finditer(text) if feld[m.start()]]


def alle_stellen(text, muster, regex=False):
    """(pos, ist_code) fuer jeden Treffer - auch die in Kommentaren.

    Verweigert ebenfalls bei gescheiterter Eichung: sonst haette die
    Auskunftssperre ein Loch, durch das genau die Zahl kaeme, der man nicht
    trauen darf. Die erste Fassung hatte dieses Loch.
    """
    ok, gef, erw = eichen(text)
    if not ok:
        raise SystemExit(
            "code_scan: EICHUNG GESCHEITERT - %d von %d isMob-Deklarationen "
            "als Code erkannt. Keine Zahl." % (gef, erw))
    feld = ist_code(text)
    pat = re.compile(muster if regex else re.escape(muster))
    return [(m.start(), bool(feld[m.start()])) for m in pat.finditer(text)]


def _komponente(text, pos):
    vor = text[:pos]
    best, name = -1, "?"
    for pat in (r"function\s+([A-Za-z_]\w*)\s*\(",
                r"const\s+([A-Z]\w+)\s*=\s*\("):
        t = list(re.finditer(pat, vor))
        if t and t[-1].start() > best:
            best, name = t[-1].start(), t[-1].group(1)
    return name


# ───────────────────────────────────────────────────────────────────────────
# ELEMENTE FINDEN - und zwar in ALLEN Schreibweisen, die diese Datei benutzt
#
# 🔴 WARUM DAS HIER STEHT UND NICHT IN JEDEM RIEGEL NEU
# Am 27.09.2026 hat mich das Alphabet DREIMAL an einem Tag getaeuscht:
#
#   1. `createElement("h2"` fand 0 Stellen. Die Datei schreibt `'h2'` mit
#      EINFACHEN Anfuehrungszeichen - es sind 28.
#   2. Ein Riegel suchte `createElement('h2'` und meldete eine neu gebaute
#      Ueberschrift als fehlend. Dort steht der lokale Kuerzel `h('h2'`.
#   3. Eine Waisensuche meldete DREI nie gerenderte Komponenten, darunter eine
#      mit 35 kB. ZWEI davon waren falsch: sie werden ueber `h(Name,{...})`
#      erzeugt. Fast waere daraus der Schluss geworden, ein ganzes Overlay
#      erscheine nie.
#
# Ein Muster, das eine Schreibweise nicht kennt, meldet "kommt nicht vor" - und
# das ist von einem echten Befund nicht zu unterscheiden. Deshalb gibt es diese
# Stelle: EIN Ort, der alle Formen kennt, und eine Eichung, die es BELEGT statt
# es zu behaupten.
#
# Die Formen in index.html:
#   React.createElement('div', ...)   Element mit Tag, Tag in Anfuehrungszeichen
#   h('div', ...)                     dasselbe ueber `const h=React.createElement`
#   React.createElement(VView, ...)   Komponente, Name NACKT
#   h(VView, ...)                     dasselbe ueber den Kuerzel
# Das `(?<![A-Za-z0-9_$.])` vor dem h ist noetig, sonst treffen `search(`,
# `_ch(` und `.h(` mit.
# ───────────────────────────────────────────────────────────────────────────

_ERZEUGER = r"(?:createElement|(?<![A-Za-z0-9_$.])h)\(\s*"


def _element_muster(name, als_tag):
    n = re.escape(name)
    if als_tag:
        return _ERZEUGER + r"['\"]" + n + r"['\"]"
    return _ERZEUGER + n + r"\b"


def eichen_elemente():
    """Belegt, dass das Muster ALLE VIER Formen kennt - und nur die.

    Bewusst an einem SELBSTGEBAUTEN Text und nicht an index.html: eine Eichung,
    die auf bestimmte Bauteilnamen zeigt, geht kaputt, sobald eines umbenannt
    wird - und dann faellt ein Werkzeug aus, das mit der Umbenennung nichts zu
    tun hat. Geprueft wird die Faehigkeit des Musters, nicht der Bestand der App.

    Gibt (bestanden, gefunden, erwartet) zurueck.
    """
    probe = (
        "React.createElement('div', {a:1}, 'x');"          # Tag, createElement
        "h('div', {b:2}, 'y');"                            # Tag, Kuerzel
        "React.createElement(MeineAnsicht, {c:3});"        # Komponente, lang
        "h(MeineAnsicht, {d:4});"                          # Komponente, Kuerzel
        # Diese drei duerfen NICHT mitzaehlen - sonst zaehlt das Muster zu viel,
        # und zu viel ist bei einer Waisensuche genauso falsch wie zu wenig:
        "search('div');"                                   # kein Kuerzel
        "obj.h('div');"                                    # Methode
        "_ch('div');"                                      # anderer Name
    )
    tag = len(re.findall(_element_muster("div", True), probe))
    komp = len(re.findall(_element_muster("MeineAnsicht", False), probe))
    return (tag == 2 and komp == 2, tag + komp, 4)


def element_stellen(text, name, als_tag=False):
    """Positionen im CODE, an denen `name` als Element erzeugt wird.

    `als_tag=True` fuer HTML-Namen ('div', 'h2' - in Anfuehrungszeichen),
    `False` fuer Komponenten (nackter Bezeichner).

    Verweigert die Auskunft, wenn eine der beiden Eichungen scheitert: die
    Zeichenketten-Eichung (`eichen`, ueber `nur_code_stellen`) und die
    Formen-Eichung (`eichen_elemente`). Eine Zahl aus einem nachweislich
    irrenden Abtaster ist schlimmer als keine Zahl.
    """
    ok, gef, erw = eichen_elemente()
    if not ok:
        raise SystemExit(
            "code_scan: FORMEN-EICHUNG GESCHEITERT - %d von %d Formen "
            "erkannt.\n"
            "  Das Muster kennt nicht alle Schreibweisen (oder zaehlt zu viel) "
            "und wuerde\n"
            "  'kommt nicht vor' melden, wo etwas vorkommt. Genau das hat am "
            "27.09.2026\n"
            "  dreimal zu einem falschen Befund gefuehrt, einmal fast zu "
            "'eine 35-kB-Ansicht ist tot'." % (gef, erw))
    return nur_code_stellen(text, _element_muster(name, als_tag), regex=True)


def alle_elementnamen(text, als_tag=False):
    """Alle Namen, die in diesem Text als Element erzeugt werden - EIN Lauf.

    Fuer Fragen der Form "welche Komponente wird nie gerendert?". Ein Lauf je
    Name waere bei 95 Komponenten 95 Durchgaenge ueber 3,6 MB; genau das hat
    einen Riegel von 4 s auf 28 s gebracht - und ein Riegel, der die Kette
    bremst, wird irgendwann uebersprungen. Dann misst er nichts mehr.

    Gibt {Name: [Positionen]} zurueck.
    """
    ok, gef, erw = eichen_elemente()
    if not ok:
        raise SystemExit("code_scan: FORMEN-EICHUNG GESCHEITERT (%d/%d)"
                         % (gef, erw))
    feld = ist_code(text)
    if als_tag:
        muster = _ERZEUGER + r"['\"]([A-Za-z][\w-]*)['\"]"
    else:
        muster = _ERZEUGER + r"([A-Z]\w+)\b"
    aus = {}
    for m in re.finditer(muster, text):
        if feld[m.start()]:
            aus.setdefault(m.group(1), []).append(m.start())
    return aus


# ───────────────────────────────────────────────────────────────────────────
# EIN BEDIENELEMENT SAMT EIGENSCHAFTEN UND KINDERN
#
# 🔴 WARUM DAS HIER STEHT: die Riegel aus v3.9.957 und v3.9.958 haben jeder
# seinen eigenen Knopf-Abtaster mitgebracht, und beide hatten dieselben drei
# Luecken. Gemessen am 27.09.2026:
#   * sie suchten nur `createElement('button'`. Die Datei fuehrt 97 Stellen
#     `h('button'` - die wurden NIE angesehen.
#   * sie lasen den Inhalt nur in DOPPELTEN Anfuehrungszeichen; sieben Stellen
#     stehen in einfachen.
#   * die Zeichenklasse von v958 kennt 0x229E (Kachel) und 0x00D7 (Malzeichen)
#     nicht.
# Folge: SIEBZEHN Knoepfe, die nie ein Wort zeigen und keinen Namen tragen,
# waren fuer beide Riegel unsichtbar - trotz der Regel, die genau davor warnt
# und die einen Tag vorher aufgeschrieben wurde.
#
# Deshalb liegt der Abtaster ab v3.9.961 hier, EINMAL, mit Eichung.
# ───────────────────────────────────────────────────────────────────────────

def _zeichenkette_ueberspringen(text, i):
    """Hinter das schliessende Anfuehrungszeichen. i zeigt auf das oeffnende."""
    q, n = text[i], len(text)
    i += 1
    while i < n and text[i] != q:
        i += 2 if text[i] == "\\" else 1
    return i + 1


def _klammer_zu(text, i, auf, zu):
    """Hinter die passende schliessende Klammer. i zeigt auf die oeffnende.

    Ueberspringt Zeichenketten - ohne das laeuft die Zaehlung an jeder Klammer
    in einem Text aus dem Tritt, und alles danach ist verschoben.
    """
    tiefe, n = 0, len(text)
    while i < n:
        c = text[i]
        if c in "\"'`":
            i = _zeichenkette_ueberspringen(text, i)
            continue
        if c == auf:
            tiefe += 1
        elif c == zu:
            tiefe -= 1
            if tiefe == 0:
                return i + 1
        i += 1
    return -1


def eichen_knoepfe():
    """Belegt, dass der Knopf-Abtaster alle Formen dieser Datei kennt.

    An einem selbstgebauten Text: beide Erzeuger, beide Anfuehrungszeichen um
    das Tag, und ein Nicht-Treffer, der nicht mitzaehlen darf.
    Gibt (bestanden, gefunden, erwartet) zurueck.
    """
    probe = (
        "React.createElement('button', {a:1}, \"x\");"
        "h('button',{b:2},'y');"
        "React.createElement(\"button\", {c:3}, 'z');"
        "h(\"button\", {d:4}, \"w\");"
        "search('button');"          # kein Erzeuger
        "obj.h('button');"           # Methode
    )
    n = len(list(_KNOPF.finditer(probe)))
    return (n == 4, n, 4)


_KNOPF = re.compile(
    r"(?:createElement|(?<![A-Za-z0-9_$.])h)\(\s*['\"]button['\"]\s*,")


def knopf_stellen(text):
    """Jedes button-Element im CODE als (start, eigenschaften, kinder).

    `eigenschaften` ist der Text des Objektliterals einschliesslich der
    Klammern, `kinder` alles danach bis zur schliessenden Klammer des Aufrufs.
    Knoepfe ohne Objektliteral als Eigenschaften (z.B. `null`) werden mit
    eigenschaften="" gemeldet - sie tragen dann sicher keinen Namen.
    """
    ok, gef, erw = eichen_knoepfe()
    if not ok:
        raise SystemExit(
            "code_scan: KNOPF-EICHUNG GESCHEITERT - %d von %d Formen erkannt.\n"
            "  Der Abtaster kennt nicht alle Schreibweisen und wuerde Knoepfe "
            "uebersehen.\n"
            "  Genau daran sind v3.9.957 und v3.9.958 vorbeigelaufen: 17 "
            "namenlose Knoepfe\n"
            "  blieben unsichtbar, weil `h('button'` und einfache "
            "Anfuehrungszeichen fehlten." % (gef, erw))
    feld = ist_code(text)
    aus = []
    for m in _KNOPF.finditer(text):
        if not feld[m.start()]:
            continue
        i = m.end()
        while i < len(text) and text[i] in " \t\r\n":
            i += 1
        if i < len(text) and text[i] == "{":
            pe = _klammer_zu(text, i, "{", "}")
            props = text[i:pe] if pe > 0 else ""
        else:
            pe, props = i, ""
        if pe <= 0:
            continue
        # Kinder: ab hinter den Eigenschaften bis zum Ende des Aufrufs.
        auf = text.rfind("(", m.start(), m.end())
        ende = _klammer_zu(text, auf, "(", ")")
        kinder = text[pe:ende - 1] if ende > pe else text[pe:pe + 1500]
        aus.append((m.start(), props, kinder))
    return aus


def hat_namen(eigenschaften):
    """Traegt dieses Element einen zugaenglichen Namen?

    Gemessen auf der OBERSTEN Ebene des Eigenschaftenobjekts. Eine flache
    Suche zaehlt ein `title:` mit, das in einem onClick-Rumpf steht - die
    Abtaster von v957/v958 haben diese Schwaeche, und einmal hat sie dort drei
    Knoepfe falsch als benannt gefuehrt.
    """
    tiefe, i, n = 0, 0, len(eigenschaften)
    while i < n:
        c = eigenschaften[i]
        if c in "\"'`":
            # 🔴 ERST HINEINSEHEN, DANN UEBERSPRINGEN. Die erste Fassung hat
            # jede Zeichenkette uebersprungen - und `'aria-label'` IST eine.
            # Damit galt ein Knopf mit 'aria-label' als namenlos. Gefunden von
            # einem Fall, der es ausdruecklich geprueft hat; ohne den waere
            # der Fehler in die Zaehlung eingegangen und haette dort Knoepfe
            # gemeldet, die einen Namen tragen.
            ende = _zeichenkette_ueberspringen(eigenschaften, i)
            inhalt = eigenschaften[i + 1:ende - 1]
            if tiefe == 1 and inhalt in ("aria-label", "title") and \
                    re.match(r"\s*:", eigenschaften[ende:]):
                return True
            i = ende
            continue
        if c in "{([":
            tiefe += 1
        elif c in "})]":
            tiefe -= 1
        elif tiefe == 1 and re.match(r"(?:title|aria-label)\s*:",
                                     eigenschaften[i:]):
            return True
        i += 1
    return False


def main(argv):
    if not argv:
        raise SystemExit('Aufruf: python scripts/code_scan.py "<muster>" [--alle]')
    muster = argv[0]
    wurzel = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    text = io.open(os.path.join(wurzel, "index.html"),
                   encoding="utf-8", newline="").read()
    treffer = alle_stellen(text, muster)
    if not treffer:
        print("%r kommt nirgends vor. Das ist KEIN gruenes Ergebnis - pruefe "
              "das Muster." % muster)
        return 1
    code = [p for p, k in treffer if k]
    rest = [p for p, k in treffer if not k]
    print("%r: %d Treffer gesamt | %d im CODE | %d in Kommentar/Zeichenkette"
          % (muster, len(treffer), len(code), len(rest)))
    print()
    for p in code:
        u = re.sub(r"\s+", " ", text[max(0, p - 90):p + 60])
        print("  CODE      %-9d %-16s %s"
              % (p, _komponente(text, p), u.encode("ascii", "replace").decode()))
    if "--alle" in argv:
        print()
        for p in rest:
            u = re.sub(r"\s+", " ", text[max(0, p - 70):p + 50])
            print("  sonstiges %-9d %s"
                  % (p, u.encode("ascii", "replace").decode()))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
