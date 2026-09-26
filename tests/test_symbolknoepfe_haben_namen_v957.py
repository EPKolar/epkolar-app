# -*- coding: utf-8 -*-
"""v3.9.957 - kein Symbol-Knopf ohne Namen.

WORUM ES GEHT
─────────────
Ein Knopf, dessen ganzer Inhalt ein Symbolzeichen ist, hat fuer eine
Vorlesehilfe keinen Namen. Sie sagt dann „Schaltflaeche" und sonst nichts - der
Benutzer erfaehrt nicht, dass dieser Knopf ein Foto entfernt oder ein Fenster
schliesst. Die Hausregel dagegen ist `title` UND `aria-label`.

WIE VIELE ES WAREN - und warum der Befund zu klein war
──────────────────────────────────────────────────────
Die Schlussmessung an v3.9.954 nannte ZWEI: die Umschalter `☰`/`⊞` in der
Fahrzeugverwaltung. Gemessen ueber die ganze Datei waren es **33**:

    4   Ansichtsumschalter  ☰ / ⊞   (Fahrzeugverwaltung UND Fotos)
   27   Schliessen/Entfernen ✕      (Fotos, Zeilen, Termine, Fenster)
    2   Abbrechen ✕                 (Tank- und Schadensdialog)

Die Sonde hatte die Fotos-Ansicht in einer anderen Gruppe gemessen und dort
nicht gemeldet; v3.9.942 („sieben Symbol-Knoepfe beschriftet") und v3.9.946
(„acht Pfeile") hatten diese Menge nie erfasst. Wieder ein Schluss aus einer
Menge, die den Fall nicht enthaelt.

JEDER NAME IST ABGELESEN, KEINER FORMULIERT
───────────────────────────────────────────
Die Namen kommen aus dem `onClick` (`delWzPhoto` -> „Foto entfernen",
`delTermin` -> „Termin loeschen", `setShowTank(null)` neben „💾 Speichern" ->
„Abbrechen") oder aus dem Text, den derselbe Knopf im anderen Zustand traegt.

🔴 SECHS KNOEPFE SIND UMSCHALTER, und dort waere ein FESTER Name falsch.
Ihr Inhalt wechselt zwischen dem Symbol und sichtbarem Text:

    showUp        ? "✕" : "📤 Hochladen"
    sa            ? "✕" : "+ Zeile"
    showAdd       ? "✕" : "+ Fahrzeug"
    showNewFolder ? "✕" : "+ Neu"
    showAddTermin ? "✕" : "+ Termin"
    isRemoved     ? "↩" : "✕"          (beide Zustaende sind Symbole)

Ein fester `title:"Abbrechen"` haette im geschlossenen Zustand „Abbrechen"
angesagt, wo „Hochladen" steht. Der Name haengt deshalb an derselben Bedingung
wie der Inhalt. Das ist der Unterschied zwischen einem abgelesenen und einem
erfundenen Namen - und er war nur zu sehen, weil der Inhalt jedes Knopfes
gemessen wurde und nicht nur seine Anwesenheit.

🔴 EINE STELLE IST GAR KEIN KNOPF
─────────────────────────────────
`SmokeTestPanel` fuehrt `(x.pass||x.ok)?"✓":"✗"` - eine STATUSANZEIGE in einer
Ergebniszeile, kein Bedienelement. Mein erster Zaehler hat sie einem
benachbarten Knopf zugeschlagen und als 34. Fund gemeldet. Sie steht unten
namentlich als Ausnahme, mit diesem Grund. Ein `title` dort waere ein Name fuer
etwas, das man nicht bedienen kann.

WAS DIESE DATEI NICHT MISST
───────────────────────────
Ob die Vorlesehilfe den Namen wirklich ansagt - das kann nur ein Schirmleser.
Und sie misst nicht die Knoepfe, deren Inhalt ein EMOJI ist (🖨️, ✏️, 💾): die
tragen teils einen Namen, teils nicht, und sie sind eine eigene Menge. Sie hier
mitzuzaehlen haette die Zahl vergroessert und die Aussage verwaessert.
"""
import io
import os
import re

PFAD = os.path.join(os.path.dirname(__file__), "..", "index.html")

# Symbolzeichen, die in dieser Datei als GANZER Knopfinhalt vorkommen.
# Bewusst eine Liste und keine Unicode-Klasse: eine Klasse traefe auch Pfeile
# in Prosa, und dann waere die Zahl groesser als die Aussage.
SYMBOLE = ["☰", "⊞", "☷", "▦", "≡", "⋮",
           "✕", "✗", "×"]

# Namentliche Ausnahmen mit Grund. KEINE Obergrenze - eine Zahl allein
# unterscheidet nicht, ob eine Ausnahme wegfiel und eine neue dazukam.
AUSNAHMEN = {
    ("SmokeTestPanel", "✗"):
        "Statusanzeige (x.pass||x.ok)?'✓':'✗' in einer "
        "Ergebniszeile - kein Bedienelement. Ein Name dafuer waere ein Name "
        "fuer etwas, das man nicht bedienen kann.",
}


def _lies():
    roh = io.open(PFAD, encoding="utf-8", newline="").read()
    if len(roh) < 3_000_000:
        raise AssertionError(
            "index.html hat nur %d Bytes - Datenverlust, keine Namensfrage. "
            "Eine leere Datei hat uebrigens null namenlose Knoepfe." % len(roh))
    return roh


def _ansicht(text, p):
    tr = list(re.finditer(r"function\s+([A-Za-z_]\w*)\s*\(", text[:p]))
    return tr[-1].group(1) if tr else "?"


def _symbolknoepfe(text):
    """(Ansicht, Zeile, Symbol, hat_namen) je Symbol in Knopfstellung."""
    aus = []
    for sym in SYMBOLE:
        for m in re.finditer(r'"' + re.escape(sym) + r'"', text):
            p = m.start()
            # Der Knopf, zu dem das Zeichen gehoert: die letzte
            # createElement('button' davor, hoechstens 900 Zeichen entfernt.
            # Weiter weg heisst: das Zeichen gehoert nicht zu einem Knopf.
            vor = text[max(0, p - 900):p]
            k = vor.rfind("createElement('button'")
            if k < 0:
                continue
            props = vor[k:]
            hat = bool(re.search(r"\btitle\s*:", props)) or "aria-label" in props
            aus.append((_ansicht(text, p), text.count("\n", 0, p) + 1, sym, hat))
    return aus


def test_kein_symbolknopf_ohne_namen():
    """Die Aussage: jeder Symbol-Knopf traegt title oder aria-label.

    Gemessen wird die EIGENSCHAFT am einzelnen Knopf, nicht eine Gesamtzahl.
    Eine Gesamtzahl waere gruen geblieben, wenn ein benannter Knopf
    verschwindet und ein namenloser dazukommt.
    """
    roh = _lies()
    alle = _symbolknoepfe(roh)
    assert alle, (
        "Kein einziger Symbol-Knopf gefunden. Das ist kein gruenes Ergebnis: "
        "die Datei fuehrt Dutzende. Entweder ist der Zaehler blind, oder die "
        "Knoepfe sind anders geschrieben - dann muss SYMBOLE nachgezogen "
        "werden, und zwar mit einer Selbstprobe.")
    ohne = [(a, z, s) for a, z, s, hat in alle
            if not hat and (a, s) not in AUSNAHMEN]
    assert not ohne, (
        "%d Symbol-Knopf/-Knoepfe ohne title und ohne aria-label:\n%s\n\n"
        "Fuer eine Vorlesehilfe ist das ein Knopf ohne Namen - sie sagt nur "
        "\"Schaltflaeche\".\n"
        "Den Namen aus dem onClick ABLESEN, nicht formulieren. Und wenn der "
        "Knopf ein UMSCHALTER ist (Inhalt wechselt zwischen Symbol und Text), "
        "muss der Name an derselben Bedingung haengen - ein fester Name sagt "
        "sonst in einem der zwei Zustaende das Falsche.\n"
        "Ist es gar kein Bedienelement, gehoert es mit Grund in AUSNAHMEN."
        % (len(ohne), "\n".join("  %-20s Z%-6d %s" % o for o in ohne)))


def test_die_sechs_umschalter_haben_einen_bedingten_namen():
    """Ein fester Name an einem Umschalter ist in einem Zustand falsch.

    Diese Pruefung ist der Grund, warum der Umbau nicht einfach 33 mal
    denselben `title:"Abbrechen"` gesetzt hat. Sie haelt fest, dass die sechs
    Umschalter ihren Namen an derselben Bedingung tragen wie ihren Inhalt.
    """
    roh = _lies()
    # (Bedingung, der Text des anderen Zustands) - beides aus dem Code.
    UMSCHALTER = [
        ("showUp", "Hochladen"),
        ("sa", "Zeile hinzufügen"),
        ("showAdd", "Fahrzeug hinzufügen"),
        ("showNewFolder", "Neuen Ordner anlegen"),
        ("showAddTermin", "Termin hinzufügen"),
        ("isRemoved", "Position entfernen"),
    ]
    fehlt = []
    for bed, text in UMSCHALTER:
        # Der Name muss die Bedingung UND den Text des anderen Zustands
        # fuehren. Nur den Text zu pruefen liesse einen festen Namen durch.
        muster = re.compile(
            r"title:\s*" + re.escape(bed) + r"\s*\?\s*\"[^\"]*\"\s*:\s*\""
            + re.escape(text) + r"\"")
        if not muster.search(roh):
            fehlt.append((bed, text))
    assert not fehlt, (
        "%d Umschalter tragen keinen BEDINGTEN Namen:\n%s\n"
        "Ihr Inhalt wechselt zwischen dem Symbol und sichtbarem Text. Ein "
        "fester title sagt im anderen Zustand das Falsche - zum Beispiel "
        "\"Abbrechen\", wo \"Hochladen\" steht."
        % (len(fehlt), "\n".join("  %s -> %r" % f for f in fehlt)))


def test_der_riegel_wird_bei_einem_namenlosen_knopf_rot():
    """KOEDER.

    Der Riegel SUCHT namenlose Knoepfe und meldet gruen, wenn er keinen
    findet - die gefaehrlichste Bauform. Also wird einer eingesetzt, und er
    MUSS gefunden werden. Ohne diese Probe hiesse \"keiner gefunden\" auch
    dann gruen, wenn das Muster nicht mehr passt.
    """
    roh = _lies()
    anker = "createElement('button', { title: \"Foto entfernen\""
    assert anker in roh, (
        "Der Anker fuer den Koeder ist weg. Dann muss der Koeder an einen "
        "anderen Symbol-Knopf - nicht weggelassen werden.")
    # Ein zusaetzlicher Knopf mit Symbol und OHNE Namen.
    kaputt = roh.replace(
        anker,
        "createElement('button', {onClick:()=>0}, \"✕\"), "
        "React.createElement('button', { title: \"Foto entfernen\"", 1)
    ohne = [(a, z, s) for a, z, s, hat in _symbolknoepfe(kaputt)
            if not hat and (a, s) not in AUSNAHMEN]
    assert ohne, (
        "KOEDER NICHT GEFUNDEN: ein eingesetzter Knopf mit Symbol und ohne "
        "Namen wird nicht erkannt. Der Zaehler ist blind, nicht die Datei ist "
        "sauber.")


def test_die_ausnahme_ist_noch_eine_ausnahme():
    """Eine Ausnahme ohne Pruefung wird zur stillen Erlaubnis.

    Steht die Statusanzeige nicht mehr da, gehoert die Ausnahme WEG - sonst
    deckt sie beim naechsten Mal einen echten namenlosen Knopf.
    """
    roh = _lies()
    assert '(x.pass||x.ok)?"✓":"✗"' in roh, (
        "Die Statusanzeige in SmokeTestPanel, fuer die die Ausnahme gilt, "
        "steht nicht mehr im Code. Dann muss die Ausnahme aus AUSNAHMEN "
        "heraus - eine Ausnahme, deren Anlass verschwunden ist, erlaubt beim "
        "naechsten Mal einen echten Fehler.")
