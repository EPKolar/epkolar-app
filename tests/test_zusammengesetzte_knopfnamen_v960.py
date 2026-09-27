# -*- coding: utf-8 -*-
"""v3.9.960 - ein Knopf, dessen Text WEGFALLEN kann, braucht trotzdem einen Namen.

DER BLINDE FLECK, DEN DIESE DATEI SCHLIESST
───────────────────────────────────────────
Die Riegel aus v3.9.957 und v3.9.958 lasen einen Knopf nur dann als
Symbolknopf, wenn sein GANZER Inhalt EIN Zeichenketten-Literal ist. Damit haben
sie eine ganze Klasse uebersprungen: Knoepfe mit ZWEI Kindern, deren zweites
verschwinden kann.

    "\U0001F5D1️ ", isMob ? "Löschen" : ""      (VBautag, Eintragskarte)
    "◀ ", h('span',{className:"sb-text"},"Alle Projekte")   (ProjectShell)

Im ersten Fall bleibt ab 600 px nur das Symbol. Im zweiten gilt fuer
`.sb-text` ein `display:none` in `@media(max-width:768px)` - in der
eingeklappten 56-px-Leiste liest der Knopf nur das Dreieck.

Gefunden hat das keiner meiner Zaehler, sondern eine Messung am gerenderten
Baum: 3 Loeschknoepfe ohne Namen bei 640 px, wo vorher „Löschen" stand. Der
Nachbar in derselben Karte traegt seinen `title` seit laengerem - die Stelle war
also nicht ausgenommen, sondern vergessen.

🔴 UND BEIDE WAREN AELTER ALS DER LAUF. Am Schreibtisch (1440 px) war der
Loeschknopf schon vor v3.9.955 namenlos; die Mobilschwellen-Umstellung hat den
Mangel nur auf das Fenster 600-767 px ausgeweitet, wo der Text vorher noch da
war. Ein Befund, der durch eine Aenderung SICHTBARER wird, ist nicht durch sie
entstanden.

WAS GEPRUEFT WIRD - die Eigenschaft, nicht die zwei Stellen
───────────────────────────────────────────────────────────
Jeder Knopf, dessen erstes Kind ein reines Symbol-/Emoji-Literal ist und der
weitere Kinder hat, faellt in die Klasse. Verlangt wird ein Name nur dort, wo
der Rest WEGFALLEN kann:

  * ein Zweig mit leerem Ast:  `bedingung ? "Text" : ""`
  * ein Element mit einer Klasse, fuer die irgendwo `display:none` gilt

Nicht verlangt wird er, wo der Rest immer Text traegt - `editId ?
"Aktualisieren" : "Speichern"` ist in beiden Zustaenden lesbar. Neun solche
Knoepfe gibt es; sie stehen unten namentlich, damit die Zahl nicht als
Obergrenze missverstanden wird.

WAS DIESE DATEI NICHT MISST
───────────────────────────
Ob eine Vorlesehilfe den Namen ansagt. Und nicht den Fall, dass der Rest eine
Variable ist, die zur Laufzeit leer wird (`x.t` in VOffa zieht seinen Text aus
einer festen Liste im Code - dort kann nichts wegfallen). Ein Rest, der aus der
Datenbank kommt, ist mit Quelltext nicht entscheidbar; das gehoert an den Schirm.
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import code_scan  # noqa: E402

PFAD = os.path.join(os.path.dirname(__file__), "..", "index.html")

SYMBOL = re.compile(
    r"^[\U0001F000-\U0001FAFF←-⇿⌀-➿⬀-⯿"
    r"☰⊞✕✗️‍\s]+$")

# Knoepfe dieser Klasse, deren Rest IMMER Text traegt - namentlich, mit dem
# Zweig, der das belegt. Keine Obergrenze: eine Zahl allein unterscheidet
# nicht, ob eine bekannte Stelle verschwindet und eine neue dazukommt.
REST_IMMER_TEXT = {
    "sharePdf": 'editId?"Aktualisieren":"Speichern"',
    "ProjList": 'editP?"Aktualisieren":"Anlegen"',
    "FormActions": 'editIdx!==null?"Aktualisieren":"Speichern"',
    "FRegie": 'editIdx!==null?"Aktualisieren":"Speichern"',
    "VPlan": 'placing?"Abbrechen":"Ticket platzieren"',
    "VMaterial": "Anzahl plus festen Text",
    "VOffa": "x.t aus einer festen Liste im Code",
    "WerkzeugView": 'editId?"Aktualisieren":"Speichern"',
}


def _lies():
    roh = io.open(PFAD, encoding="utf-8", newline="").read()
    if len(roh) < 3_000_000:
        raise AssertionError("index.html hat nur %d Bytes - Datenverlust."
                             % len(roh))
    return roh


def _ansicht(text, p):
    tr = list(re.finditer(r"function\s+([A-Za-z_]\w*)\s*\(", text[:p]))
    return tr[-1].group(1) if tr else "?"


def _props_ende(text, start):
    """Hinter der schliessenden Klammer der Eigenschaften. Ueberspringt
    Zeichenketten - ohne das laeuft die Klammerzaehlung an jedem { in einem
    Text aus dem Tritt, und das erste Kind danach zeigt irgendwohin."""
    i = text.find("{", start)
    if i < 0 or i - start > 40:
        return None
    tiefe, n = 0, len(text)
    while i < n:
        c = text[i]
        if c in "\"'`":
            q = c
            i += 1
            while i < n and text[i] != q:
                i += 2 if text[i] == "\\" else 1
            i += 1
            continue
        if c == "{":
            tiefe += 1
        elif c == "}":
            tiefe -= 1
            if tiefe == 0:
                return i + 1
        elif c == "\n" and tiefe == 0:
            return None
        i += 1
    return None


def _klasse(text):
    """(Ansicht, Zeile, Symbol, Rest, hat_namen, rest_kann_wegfallen)."""
    feld = code_scan.ist_code(text)
    aus = []
    for m in re.finditer(r"createElement\('button'\s*,", text):
        if not feld[m.start()]:
            continue
        a = m.end()
        pe = _props_ende(text, a)
        if pe is None:
            continue
        props = text[a:pe]
        rest = text[pe:pe + 600]
        rest = re.sub(r"^\s*,\s*", "", rest, count=1)
        rest = re.sub(r"^/\*.*?\*/\s*", "", rest, count=1, flags=re.S)
        mk = re.match(r'"((?:[^"\\]|\\.)*)"\s*,', rest)   # Literal, dann KOMMA
        if not mk:
            continue
        sym = mk.group(1)
        if not sym.strip() or not SYMBOL.match(sym):
            continue
        weiter = rest[mk.end():mk.end() + 160]
        hat = bool(re.search(r"\btitle\s*:", props)) or "aria-label" in props
        # Kann der Rest wegfallen? Zwei Formen, beide gemessen:
        leerer_ast = bool(re.search(r"\?\s*(?:\"[^\"]*\"|'[^']*')\s*:\s*(?:\"\"|'')",
                                    weiter))
        versteckbar = False
        for km in re.finditer(r"className:\s*\"([\w-]+)\"", weiter):
            if re.search(r"\." + re.escape(km.group(1)) + r"\s*\{[^}]*display:\s*none",
                         text):
                versteckbar = True
        aus.append((_ansicht(text, a), text.count("\n", 0, a) + 1, sym.strip(),
                    re.sub(r"\s+", " ", weiter)[:60], hat,
                    leerer_ast or versteckbar))
    return aus


def test_wer_seinen_text_verlieren_kann_hat_einen_namen():
    """Die Aussage. Gemessen an der Eigenschaft, nicht an zwei Zeilen."""
    roh = _lies()
    alle = _klasse(roh)
    assert alle, (
        "Kein einziger Knopf dieser Klasse gefunden. Das ist kein gruenes "
        "Ergebnis - es gibt um 15. Entweder ist der Zaehler blind, oder die "
        "Knoepfe sind anders geschrieben.")
    fehlt = [(a, z, s, w) for a, z, s, w, hat, weg in alle if weg and not hat]
    assert not fehlt, (
        "%d Knopf/Knoepfe koennen ihren Text verlieren und haben dann keinen "
        "Namen:\n%s\n\n"
        "Bei diesen Knoepfen ist der Text ein zweites Kind, das wegfallen "
        "kann - ueber einen Zweig mit leerem Ast oder ueber ein display:none "
        "auf seiner Klasse. In diesem Zustand liest eine Vorlesehilfe nur das "
        "Symbol.\n"
        "Den Namen ABLESEN: aus dem onClick oder aus dem Text, der im anderen "
        "Zustand dasteht. Nicht formulieren."
        % (len(fehlt),
           "\n".join("  %-20s Z%-7d %-4s Rest: %s" % f for f in fehlt)))


def test_die_zwei_behobenen_stellen_bleiben_benannt():
    """Namentlich, damit ein Ruecksturz nicht in einer Zahl untergeht."""
    roh = _lies()
    for ansicht, name in (("VBautag", "Eintrag löschen"),
                          ("ProjectShell", "Alle Projekte")):
        treffer = [t for t in _klasse(roh) if t[0] == ansicht and t[4]]
        assert treffer, (
            "%s fuehrt keinen benannten Knopf dieser Klasse mehr. In v3.9.960 "
            "hat er %r bekommen - ist der Name weg, ist der Mangel zurueck."
            % (ansicht, name))
        assert ('title: "%s"' % name) in roh, (
            "Der Name %r steht nicht mehr im Quelltext. Gemessen wird hier "
            "der Wortlaut, weil er ABGELESEN ist: bei VBautag aus dem Text, "
            "den derselbe Knopf am Telefon zeigt, bei ProjectShell aus dem "
            "span, das die Leiste ausblendet." % name)


def test_wer_immer_text_traegt_braucht_keinen(  ):
    """Die Gegenseite - und sie ist der Grund, warum hier nicht einfach
    ueberall ein title gefordert wird.

    `editId?"Aktualisieren":"Speichern"` ist in beiden Zustaenden lesbar. Ein
    Riegel, der auch dort einen Namen verlangt, erzeugt Arbeit ohne Wirkung -
    und wird dann gelockert, womit er auch die echten Faelle verliert.
    """
    roh = _lies()
    ohne_grund = [(a, z) for a, z, s, w, hat, weg in _klasse(roh)
                  if not weg and not hat and a not in REST_IMMER_TEXT]
    assert not ohne_grund, (
        "%d Knopf/Knoepfe dieser Klasse tragen keinen Namen und stehen nicht "
        "in REST_IMMER_TEXT:\n%s\n"
        "Entweder kann ihr Rest doch wegfallen - dann fehlt oben eine Form -, "
        "oder sie gehoeren mit Begruendung in die Liste."
        % (len(ohne_grund), "\n".join("  %-20s Z%d" % o for o in ohne_grund)))


def test_der_riegel_wird_bei_einem_leeren_ast_rot():
    """KOEDER 1: ein Knopf mit leerem Ast und ohne Namen MUSS auffallen."""
    roh = _lies()
    anker = "createElement('button', { title: \"Alle Projekte\""
    assert anker in roh, "Anker fuer den Koeder fehlt."
    kaputt = roh.replace(
        anker,
        "createElement('button', {onClick:()=>0}, \"\U0001F5D1️ \", "
        "istDa?\"Weg\":\"\"), React." + anker, 1)
    fehlt = [t for t in _klasse(kaputt) if t[5] and not t[4]]
    assert fehlt, (
        "KOEDER NICHT GEFUNDEN: ein eingesetzter Knopf mit Symbol, leerem Ast "
        "und ohne Namen wird nicht erkannt. Der Zaehler ist blind.")


def test_der_riegel_erkennt_auch_den_versteckbaren_text():
    """KOEDER 2, die zweite Form - und die schwerere.

    Ein Text, der ueber `display:none` verschwindet, sieht im Quelltext
    vorhanden aus. Genau daran ist der ProjectShell-Fall vorbeigelaufen: kein
    Zaehler hat ihn gesehen, sondern erst eine Messung am gerenderten Baum.
    """
    roh = _lies()
    treffer = [t for t in _klasse(roh) if t[0] == "ProjectShell"]
    assert treffer, "Der ProjectShell-Knopf faellt nicht mehr in die Klasse."
    assert any(t[5] for t in treffer), (
        "Der ProjectShell-Knopf wird nicht mehr als 'Rest kann wegfallen' "
        "erkannt. Dann sieht der Riegel die display:none-Form nicht - und die "
        "ist die schwerere der beiden, weil sie im Quelltext vorhanden "
        "aussieht.")
    # Und die Erkennung haengt wirklich an der CSS-Regel, nicht am Namen.
    ohne_regel = roh.replace(".sb-text{display:none}", ".sb-text{display:inline}")
    t2 = [t for t in _klasse(ohne_regel) if t[0] == "ProjectShell"]
    assert t2 and not any(t[5] for t in t2), (
        "Auch ohne die display:none-Regel gilt der Rest als wegfallbar. Dann "
        "raet der Riegel statt zu messen.")
