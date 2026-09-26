# -*- coding: utf-8 -*-
"""v3.9.958 - kein Emoji-Knopf ohne Namen.

DIE ZWEITE HAELFTE VON S-1
──────────────────────────
v3.9.957 hat 33 Knoepfe benannt, deren Inhalt ein SYMBOLZEICHEN ist (✕, ☰, ⊞),
und dabei die Knoepfe mit EMOJI-Inhalt (🖨️, ✏️, 🗑️, ✅) ausdruecklich
ausgeschlossen - mit der Begruendung, sie seien eine eigene Menge. Diese Datei
schliesst sie.

Ein Emoji ist fuer eine Vorlesehilfe nicht ganz dasselbe wie ein Symbolzeichen:
viele Emoji tragen einen Unicode-Namen, den ein Schirmleser ansagt („Drucker",
„Papierkorb"). Das ist aber der Name des BILDES und nicht der Name der
HANDLUNG - „Drucker" sagt nicht, dass dieser Knopf den Arbeitsschein druckt,
und „Papierkorb" sagt nicht, WAS geloescht wird. Deshalb gilt hier dieselbe
Hausregel: `title` UND `aria-label`.

Gemessen: **150** Knoepfe, deren ganzer Inhalt ein Emoji-Literal ist. 118
trugen einen Namen, **32 nicht**. Seit v3.9.958 alle 150.

🔴 WARUM DIESE DATEI EINE EICHUNG HAT - mein Abtaster hat zuerst GELOGEN
────────────────────────────────────────────────────────────────────────
Die erste Fassung der Messung suchte im Umfeld jedes Knopfes mit `re.search`
nach `}, "..."` und nahm das als Inhalt. Wenn der Inhalt aber eine VARIABLE
ist, findet dieses Muster ein SPAETERES Literal - irgendwo im naechsten
Argument oder im naechsten Element. Drei Stellen wurden so als „namenloser
Emoji-Knopf" gemeldet, bei denen der Inhalt Text war:

    Z10166  `_navBtn=(tab,text,color)` -> Inhalt ist `text`
    Z20541  Reiterzeile Materialbestellung -> Inhalt ist `f.l` („Offen")
    Z20867  Reiterzeile Lieferantenbestellung -> Inhalt ist `f.l`

Sie standen mit Zeile und Emoji in der Liste, und die Liste sah vollstaendig
und glaubwuerdig aus. Aufgefallen ist es nur, weil ich vor dem Bauen die drei
unklarsten Stellen im Zusammenhang gelesen habe - und dort stand kein Emoji.

Diese Datei klammert das Eigenschaftenobjekt deshalb mit einer ZAEHLUNG aus
(Zeichenketten werden dabei uebersprungen) und sieht nur das erste Argument
DANACH an. Und `test_der_abtaster_meldet_die_drei_alten_fehlmeldungen_nicht`
haelt genau diese drei Zeilen fest: taucht eine wieder auf, ist der Abtaster
in den alten Fehler zurueckgefallen.

WAS DIESE DATEI NICHT MISST
───────────────────────────
Ob die Vorlesehilfe den Namen wirklich ansagt. Und nicht die 546 Knoepfe, deren
Inhalt etwas anderes ist (Text, eine Variable, mehrere Kinder) - die tragen
ihren Namen im Text selbst oder brauchen eine eigene Messung.
"""
import io
import os
import re

PFAD = os.path.join(os.path.dirname(__file__), "..", "index.html")

EMOJI = re.compile(
    r"^[\U0001F000-\U0001FAFF←-⇿⌀-➿⬀-⯿"
    r"️‍\s]+$")

# Die drei Zeilen, die die erste Fassung des Abtasters falsch gemeldet hat.
# Ihr Knopfinhalt ist eine Variable mit TEXT, kein Emoji.
ALTE_FEHLMELDUNGEN = [10166, 20541, 20867]


def _lies():
    roh = io.open(PFAD, encoding="utf-8", newline="").read()
    if len(roh) < 3_000_000:
        raise AssertionError(
            "index.html hat nur %d Bytes - Datenverlust. Eine leere Datei hat "
            "null namenlose Knoepfe." % len(roh))
    return roh


def _ansicht(text, p):
    tr = list(re.finditer(r"function\s+([A-Za-z_]\w*)\s*\(", text[:p]))
    return tr[-1].group(1) if tr else "?"


def _props_ende(text, start):
    """Position hinter der schliessenden Klammer des Eigenschaftenobjekts.

    Zaehlt Klammern und ueberspringt Zeichenketten. Ohne das Ueberspringen
    laeuft die Zaehlung an jedem `{` in einem Text aus dem Tritt - und dann
    zeigt das „erste Argument danach" irgendwohin.
    """
    i = text.find("{", start)
    if i < 0 or i - start > 40:
        return None            # keine Objektliteral-Props (z.B. `null`)
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


def _emojiknoepfe(text):
    """(Ansicht, Zeile, Emoji, hat_namen) je Knopf mit reinem Emoji-Inhalt."""
    aus = []
    for m in re.finditer(r"createElement\('button'\s*,", text):
        a = m.end()
        pe = _props_ende(text, a)
        if pe is None:
            continue
        props = text[a:pe]
        rest = text[pe:pe + 400]
        rest = re.sub(r"^\s*,\s*", "", rest, count=1)
        rest = re.sub(r"^/\*.*?\*/\s*", "", rest, count=1, flags=re.S)
        mk = re.match(r'"((?:[^"\\]|\\.)*)"\s*\)', rest)
        if not mk:
            continue
        inhalt = mk.group(1)
        if not inhalt or not EMOJI.match(inhalt):
            continue
        hat = (bool(re.search(r"\btitle\s*:", props))
               or "aria-label" in props)
        aus.append((_ansicht(text, a), text.count("\n", 0, a) + 1, inhalt, hat))
    return aus


def test_kein_emojiknopf_ohne_namen():
    """Jeder Knopf mit reinem Emoji-Inhalt traegt title oder aria-label."""
    roh = _lies()
    alle = _emojiknoepfe(roh)
    assert len(alle) > 100, (
        "Nur %d Emoji-Knoepfe gefunden, erwartet ueber 100. Das ist kein "
        "gruenes Ergebnis: entweder ist der Abtaster blind, oder die Knoepfe "
        "sind anders geschrieben. Eine kleine Grundgesamtheit macht die "
        "Aussage unten wertlos." % len(alle))
    ohne = [(a, z, i) for a, z, i, hat in alle if not hat]
    assert not ohne, (
        "%d Emoji-Knopf/-Knoepfe ohne title und ohne aria-label:\n%s\n\n"
        "Ein Schirmleser sagt dort den Namen des BILDES an, nicht den der "
        "HANDLUNG - \"Papierkorb\" sagt nicht, WAS geloescht wird.\n"
        "Den Namen aus dem onClick ABLESEN und den Wortschatz der schon "
        "benannten Knoepfe benutzen (\"Bearbeiten\", \"Eintrag loeschen\", "
        "\"Drucken / als PDF speichern\"), damit die App nicht zwei Woerter "
        "fuer dieselbe Handlung fuehrt."
        % (len(ohne), "\n".join("  %-20s Z%-6d %s" % o for o in ohne)))


def test_der_abtaster_meldet_die_drei_alten_fehlmeldungen_nicht():
    """EICHUNG gegen den eigenen alten Fehler.

    Die erste Fassung der Messung hielt drei Knoepfe fuer Emoji-Knoepfe, deren
    Inhalt eine Variable mit Text ist. Taucht eine dieser Zeilen hier wieder
    auf, ist der Abtaster in den alten Fehler zurueckgefallen - und dann ist
    auch die Zahl oben nicht zu gebrauchen.
    """
    roh = _lies()
    zeilen = {z for _, z, _, _ in _emojiknoepfe(roh)}
    rueckfall = [z for z in ALTE_FEHLMELDUNGEN if z in zeilen]
    assert not rueckfall, (
        "Der Abtaster meldet die Zeilen %s wieder als Emoji-Knopf, obwohl ihr "
        "Inhalt eine Variable mit TEXT ist (_navBtn: `text`, zwei "
        "Reiterzeilen: `f.l`).\n"
        "Wahrscheinlich sucht er das Inhaltsliteral wieder mit `re.search` im "
        "Umfeld statt direkt hinter den Eigenschaften - dann findet er ein "
        "spaeteres Literal. Genau daran ist die erste Fassung gescheitert."
        % rueckfall)


def test_der_riegel_wird_bei_einem_namenlosen_emojiknopf_rot():
    """KOEDER.

    Der Riegel SUCHT namenlose Knoepfe und meldet gruen, wenn er keinen
    findet. Also wird einer eingesetzt, und er MUSS gefunden werden.
    """
    roh = _lies()
    anker = "createElement('button', { title: \"Genehmigen\""
    assert anker in roh, (
        "Der Anker fuer den Koeder ist weg. Dann gehoert der Koeder an einen "
        "anderen Emoji-Knopf - nicht weggelassen.")
    kaputt = roh.replace(
        anker,
        "createElement('button', {onClick:()=>0}, \"\U0001F5D1️\"), "
        "React.createElement('button', { title: \"Genehmigen\"", 1)
    ohne = [(a, z, i) for a, z, i, hat in _emojiknoepfe(kaputt) if not hat]
    assert ohne, (
        "KOEDER NICHT GEFUNDEN: ein eingesetzter Emoji-Knopf ohne Namen wird "
        "nicht erkannt. Der Zaehler ist blind, nicht die Datei ist sauber.")


def test_der_wortschatz_bleibt_einer():
    """Zwei Woerter fuer dieselbe Handlung sind schlimmer als eines.

    Gemessen wird nicht, dass bestimmte Namen VORKOMMEN - das waere
    Anwesenheit. Gemessen wird, dass keine zweite Schreibweise derselben
    Handlung dazugekommen ist. Sonst sagt die App an einer Stelle
    \"Loeschen\" und daneben \"Entfernen\" fuer dasselbe.
    """
    roh = _lies()
    # Paare, die dasselbe meinen wuerden. Links die Hausform, rechts die
    # Formen, die es NICHT geben soll.
    VERBOTEN = {
        '"Drucken"': '"Drucken / als PDF speichern"',
        '"Editieren"': '"Bearbeiten"',
        '"Aendern"': '"Bearbeiten"',
        '"Zu"': '"Schließen"',
        '"OK"': 'ein Name, der die Handlung nennt',
    }
    gefunden = []
    for schlecht, gut in VERBOTEN.items():
        if re.search(r"title:\s*" + re.escape(schlecht), roh):
            gefunden.append((schlecht, gut))
    assert not gefunden, (
        "%d Name(n) weichen von der Hausform ab:\n%s\n"
        "Die App fuehrt dann zwei Woerter fuer dieselbe Handlung, und ein "
        "Benutzer, der sich das erste gemerkt hat, findet das zweite nicht."
        % (len(gefunden),
           "\n".join("  %s  ->  %s" % g for g in gefunden)))
