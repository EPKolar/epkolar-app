# -*- coding: utf-8 -*-
"""Welches MESSWERKZEUG kann seinen eigenen Ausfall nicht bemerken?

🔴 DIE FEHLERKLASSE, DIE DAS ADRESSIERT, HAT MICH AM 29.09.2026 VIERMAL
ERWISCHT - jedes Mal sah der Ausfall aus wie ein Ergebnis:

  * Eine nach HOEHE sortierte, auf zwoelf gekappte Beispielliste, und daraus
    eine Aussage ueber die BREITE. Die Aussage stimmte zufaellig.
  * `code_scan._klammer_zu` gibt die Stelle HINTER der Klammer zurueck; ich
    hielt sie fuer die Klammer. Der Sucher fand NULL Treffer - und null sieht
    aus wie „es gibt keine".
  * Eine zu grobe Zuordnung meldete SECHS Faelle, es waren drei. Eine Zahl,
    die zu GROSS ist, wird eher geglaubt, weil sie schlimmer aussieht.
  * Der neue Schalen-Haken stuerzte auf einer cp1252-Konsole ab - seine
    eigene Eichung sah es nicht, weil sie die Entscheidung prueft und nicht
    das Ausschreiben.

Drei davon hat eine Eichprobe gefangen, bevor die Zahl in einen Bericht kam.
Der vierte hatte an dieser Stelle keine.

WAS EINE WIRKSAME SELBSTPROBE IST (und was nicht):
  * Sie hat einen KOEDER - einen Fall, den das Werkzeug finden MUSS.
  * Sie bricht den Lauf AB, wenn der Koeder nicht gefunden wird. Eine Probe,
    die nur eine Warnung druckt und weitermacht, ist keine.
  * 🔴 Ein KOMMENTAR ueber die Selbstprobe ist keine Selbstprobe. Genau
    dieser Fehler hat am 27.09. einen Riegel gruen gehalten, dessen Funktion
    gar nicht mehr gerufen wurde. Deshalb wird hier im CODE gesucht -
    Kommentare und Dokumentationstexte werden vorher entfernt.

🔴 UND DER SUCHER KENNT FUENF SCHREIBWEISEN, weil mein erster Entwurf nur
EINE kannte und dadurch „4 von 45 haben eine Eichung" gemeldet hat. Gemessen
waren es dann ganz andere Zahlen. Ein Zaehler, der eine Schreibweise nicht
kennt, meldet „kommt nicht vor" - und das ist von einem Befund nicht zu
unterscheiden.

Aufruf:  python scripts/werkzeug_eichung.py
"""
import io
import os
import re
import sys
import tokenize

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
SKRIPTE = os.path.join(WURZEL, "scripts")

# Welche Dateien sind MESSWERKZEUGE? Die Namensformen dieses Hauses.
# Ausdruecklich NICHT jedes Skript: ein Bauwerkzeug (safe_edit,
# version_stempeln) misst nichts und braucht keine Eichung, es braucht einen
# Anker, der genau einmal trifft.
IST_MESSWERKZEUG = re.compile(
    r"(_messen|_audit|_wirkung|_pruefen|_erkunden|_vergleich|bilanz|_scan)"
    r"\.py$|^(bestand|code_scan|md5_geschuetzt)\.py$")

# Die fuenf Schreibweisen, in denen dieses Haus eine Selbstprobe schreibt.
# 🔴 Ein Koeder JE FORM steht in `eichen()`.
PROBE_FORMEN = {
    "eichen-Funktion": re.compile(r"\bdef\s+eich\w*\s*\(", re.M),
    "Koeder-Tafel": re.compile(r"\b(KOEDER|PROBEN|EICHPROBE|GEGENPROBEN)\b"),
    "Schalter": re.compile(r"--(koeder|eichen)"),
    "Aufruf": re.compile(r"\beich\w*\s*\(\s*\)"),
    "Selbstprobe-Zweig": re.compile(
        r"(selbstprobe|koeder|gegenprobe)", re.I),
}
# Der Abbruch. Ohne ihn ist die Probe eine Meinung.
ABBRUCH = re.compile(r"\breturn\s+2\b|sys\.exit\(\s*2\s*\)|raise\s+SystemExit")

# 🔴 EIN VERSPRECHEN IST NICHT JEDE ERWAEHNUNG. Mein erster Entwurf nahm
#    jedes Vorkommen der Woerter und hat damit `md5_geschuetzt.py`
#    beschuldigt - dort steht bloss eine Rueckschau: "Gefunden von einem
#    Koeder, der genau das nachstellte". Das ist kein Versprechen, das ist
#    Projektgeschichte. Lieber zu wenig melden als falsch beschuldigen: ein
#    Werkzeug, dessen Befunde man nachpruefen und verwerfen muss, wird nicht
#    mehr gelesen.
#    Gezaehlt wird nur die ausdrueckliche Zusage in der Form dieses Hauses:
#    SELBSTPROBE in Grossbuchstaben oder "Selbstprobe:" mit Doppelpunkt.
VERSPRECHEN = re.compile(r"\bSELBSTPROBE\b|\bSelbstprobe\s*:")

# 🔴 UND EINE ZWEITE KORREKTUR, SOFORT NACH DEM ERSTEN LAUF. Der Sucher
#    entfernt Kommentare - richtig, sonst erfuellt die Begruendung die
#    Pruefung. Aber eine Selbstprobe, die als schlichtes `if ...: return 2`
#    gebaut ist und nur im KOMMENTAR darueber so heisst, wird dadurch
#    unsichtbar. `thema_cssvariablen_messen.py` hat genau das:
#        # 🔴 SELBSTPROBE ZUERST.
#        if hell.get("modus") != "light" or ...:
#            print(...); return 2
#    Das IST die Probe. Sie als "Versprechen ohne Deckung" zu melden heisst,
#    ein Werkzeug zu beschuldigen, das es richtig macht - und ein Zaehler,
#    dessen Befunde man verwerfen muss, wird nicht mehr gelesen.
#    Gezaehlt wird deshalb als GEBAUT: eine Marke als INLINE-Kommentar, der
#    innerhalb der naechsten Zeilen ein Abbruch folgt. Ein Kommentar ALLEIN
#    genuegt weiterhin nicht - das bleibt die Regel.
MARKE_INLINE = re.compile(r"^[ \t]*#[^\n]*"
                          r"(SELBSTPROBE|Selbstprobe|Koeder|KOEDER)[^\n]*$",
                          re.M)
FENSTER_ZEILEN = 12


def probe_als_kommentar_mit_abbruch(quelle):
    """Marke als Inline-Kommentar, und kurz darauf ein Abbruch."""
    zeilen = quelle.split("\n")
    for m in MARKE_INLINE.finditer(quelle):
        nr = quelle.count("\n", 0, m.start())
        fenster = "\n".join(zeilen[nr + 1:nr + 1 + FENSTER_ZEILEN])
        if ABBRUCH.search(fenster):
            return True
    return False


def ohne_worte(quelle):
    """Quelltext ohne Kommentare und ohne Dokumentationstexte.

    🔴 DAS IST DER KERN DIESES WERKZEUGS. Jede der fuenf Schreibweisen kommt
    in den Kopftexten dieses Hauses staendig vor - wer den ROHEN Text
    durchsucht, misst seine eigene Begruendung mit und meldet jedes Werkzeug
    als geeicht.
    """
    aus = []
    letzte_art = tokenize.NEWLINE
    try:
        marken = list(tokenize.generate_tokens(
            io.StringIO(quelle).readline))
    except (tokenize.TokenError, IndentationError, SyntaxError):
        # Nicht zerlegbar: dann lieber den rohen Text, aber das wird gemeldet.
        return None
    for m in marken:
        if m.type == tokenize.COMMENT:
            continue
        if m.type == tokenize.STRING and letzte_art in (
                tokenize.NEWLINE, tokenize.NL, tokenize.INDENT,
                tokenize.DEDENT, tokenize.ENCODING):
            # Alleinstehende Zeichenkette am Anweisungsanfang = Kopftext.
            letzte_art = m.type
            continue
        if m.type not in (tokenize.NL, tokenize.NEWLINE, tokenize.INDENT,
                          tokenize.DEDENT):
            letzte_art = m.type
        else:
            letzte_art = m.type
        aus.append(m.string)
    return "\n".join(aus)


def beurteile(quelle):
    """(hat_probe, hat_abbruch, gefundene Formen) - gemessen am CODE."""
    code = ohne_worte(quelle)
    if code is None:
        return None, None, ["NICHT ZERLEGBAR"]
    formen = [n for n, r in PROBE_FORMEN.items() if r.search(code)]
    if probe_als_kommentar_mit_abbruch(quelle):
        formen.append("Marke+Abbruch")
    return bool(formen), bool(ABBRUCH.search(code)), formen


def werkzeuge():
    return [f for f in sorted(os.listdir(SKRIPTE))
            if f.endswith(".py") and IST_MESSWERKZEUG.search(f)]


# ── Selbstprobe dieses Werkzeugs ─────────────────────────────────────────
# 🔴 Ein Werkzeug, das Eichungen zaehlt und selbst keine hat, waere die
#    Pointe des ganzen Befunds.
_MIT_PROBE = (
    '"""Kopftext."""\n'
    "def eichen():\n"
    "    return []\n"
    "def main():\n"
    "    if eichen():\n"
    "        return 2\n"
    "    return 0\n")
_OHNE_PROBE = (
    '"""Kopftext, in dem das Wort Selbstprobe und KOEDER vorkommt."""\n'
    "def main():\n"
    "    print('42 Treffer')\n"
    "    return 0\n")
_NUR_KOMMENTAR = (
    "def main():\n"
    "    # KOEDER: hier waere eine Selbstprobe sinnvoll, siehe eichen()\n"
    "    print('42 Treffer')\n"
    "    return 0\n")
_PROBE_OHNE_ABBRUCH = (
    "def eichen():\n"
    "    return ['kaputt']\n"
    "def main():\n"
    "    for s in eichen():\n"
    "        print('Warnung:', s)\n"
    "    return 0\n")


def eichen():
    schief = []
    p, a, _f = beurteile(_MIT_PROBE)
    if not (p and a):
        schief.append("Ein Werkzeug MIT Probe und Abbruch wird nicht erkannt "
                      "(Probe=%s, Abbruch=%s)." % (p, a))
    p, _a, _f = beurteile(_OHNE_PROBE)
    if p:
        schief.append("Ein Werkzeug, das die Woerter nur im KOPFTEXT hat, "
                      "gilt als geeicht.\n     Dann meldet dieses Werkzeug "
                      "jedes Haus-Skript als in Ordnung.")
    p, _a, _f = beurteile(_NUR_KOMMENTAR)
    if p:
        schief.append("Ein KOMMENTAR ueber die Selbstprobe erfuellt die "
                      "Pruefung.\n     Genau so ist am 27.09. ein Riegel "
                      "gruen geblieben, dessen Funktion nicht\n     mehr "
                      "gerufen wurde.")
    p, a, _f = beurteile(_PROBE_OHNE_ABBRUCH)
    if not p or a:
        schief.append("Eine Probe, die nur WARNT und weitermacht, wird als "
                      "vollwertig gezaehlt\n     (Probe=%s, Abbruch=%s)."
                      % (p, a))
    # 🔴 Das Versprechen: eine ausdrueckliche Zusage zaehlt, eine Rueckschau
    #    nicht. Der zweite Fall hat am 29.09. `md5_geschuetzt.py` zu Unrecht
    #    beschuldigt.
    if not VERSPRECHEN.search("🔴 SELBSTPROBE: derselbe Lauf muss melden..."):
        schief.append("Eine ausdrueckliche SELBSTPROBE-Zusage wird nicht "
                      "als Versprechen erkannt.")
    if VERSPRECHEN.search("Gefunden von einem Koeder, der genau das "
                          "nachstellte (v3.9.9)."):
        schief.append("Eine RUECKSCHAU auf einen frueheren Koeder gilt als "
                      "Versprechen.\n     Dann beschuldigt dieses Werkzeug "
                      "Skripte, die nichts zugesagt haben.")
    return schief


def main(argv):
    schief = eichen()
    print("Eichung: 6 Proben - Koeder, zwei Kommentar-Gegenproben, "
          "Probe-ohne-Abbruch,\n         und zwei zum Unterschied "
          "Versprechen gegen Rueckschau")
    if schief:
        for s in schief:
            print("   \U0001F534 " + s)
        print("\nNICHT GEMESSEN. Ein Werkzeug, das Eichungen zaehlt und "
              "selbst keine hat,\nwaere die Pointe des ganzen Befunds.")
        return 2
    print("   \U0001F7E2 alle sechs richtig\n")

    liste = werkzeuge()
    if not liste:
        print("\U0001F534 KEIN Messwerkzeug gefunden. Das ist kein Ergebnis.")
        return 2

    voll, halb, ohne, versprochen = [], [], [], []
    for f in liste:
        q = io.open(os.path.join(SKRIPTE, f), encoding="utf-8",
                    newline="").read()
        p, a, formen = beurteile(q)
        if p and a:
            voll.append((f, formen))
        elif p:
            halb.append((f, formen))
        else:
            ohne.append((f, formen))
            # 🔴 DIE SCHAERFSTE KATEGORIE: der Kopftext VERSPRICHT eine
            #    Selbstprobe, im Code steht keine. Das ist schlimmer als gar
            #    keine - wer den Kopf liest, haelt das Werkzeug fuer
            #    abgesichert und glaubt seiner Null.
            if VERSPRECHEN.search(q):
                versprochen.append(f)

    print("%d Messwerkzeuge in scripts/" % len(liste))
    print("   mit Probe UND Abbruch : %3d" % len(voll))
    print("   Probe ohne Abbruch    : %3d  (warnt und macht weiter)"
          % len(halb))
    print("   ohne Selbstprobe      : %3d" % len(ohne))
    print("   davon NUR VERSPROCHEN : %3d  \U0001F534 Kopftext sagt ja, "
          "Code sagt nein" % len(versprochen))
    if halb:
        print("\n   Probe ohne Abbruch:")
        for f, _fo in halb:
            print("      " + f)
    if versprochen:
        print("\n   \U0001F534 verspricht eine Selbstprobe und hat keine:")
        for f in versprochen:
            print("      " + f)
    stumm = [f for f, _fo in ohne if f not in versprochen]
    if stumm:
        print("\n   ohne Selbstprobe, ohne Versprechen:")
        for f in stumm:
            print("      " + f)
    return 0


if __name__ == "__main__":
    # v3.9.995: DIE KONSOLE VERTRAEGT NICHT JEDES ZEICHEN. Auf Windows
    # laeuft sie auf cp1252; ein Symbol in der Ausgabe beendet das Tor
    # dann mit einem UnicodeEncodeError - und zwar oft auf dem
    # ERFOLGSZWEIG, beim Hinschreiben des gruenen Punktes. Die Torkette
    # liest den Rueckgabewert und meldet ROT, obwohl die Messung selbst
    # in Ordnung war. Am 30.09.2026 ist genau das zwei Toren passiert.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    sys.exit(main(sys.argv[1:]))
