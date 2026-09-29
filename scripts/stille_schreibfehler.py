# -*- coding: utf-8 -*-
"""Welcher Schreibvorgang scheitert, ohne dass es jemand erfaehrt?

🔴 DIE FORM DIESES MANGELS IST „BEIDE ENDEN GEMESSEN, DIE MITTE BLIND".

Das EINE Ende ist in Ordnung, und zwar nachweislich: `_sbPost`, `_sbPatch`,
`_sbUpsert`, `_sbDelete`, `_sbDeleteWhere`, `_sbInsertIfAbsent` pruefen JEDER
auf 401 und 403, rufen `_onAuthFail` und **werfen** mit Status im Text. Am
Helfer ist nichts zu reparieren.

Das ANDERE Ende ist der Nutzer, und dort steht im Zweifel nichts. Dazwischen
liegt der Aufrufer - und ein

    try{ await _sbPatch(...); }catch(_){}

wirft den sauber geworfenen Fehler weg. Der Monteur sieht keine Meldung, die
Oberflaeche zeigt den neuen Wert, und gespeichert ist nichts. **Ein stiller
Schreibfehler ist schlimmer als ein lauter**: bei einem lauten weiss der
Nutzer, dass er es nochmal machen muss.

🔴 WARUM EIN ZEILEN-GREP DAS NICHT KANN. Gesucht ist nicht „ein leeres
`catch`" (davon gibt es 83, die meisten voellig harmlos - `localStorage`,
`JSON.parse`, `navigator.vibrate`). Gesucht ist die **Paarung**: ein leeres
`catch`, dessen zugehoeriges `try` einen SCHREIBVORGANG enthaelt. Die
Zuordnung braucht einen Klammerabgleich, weil beides zeilenweise beliebig weit
auseinanderliegt und `index.html` kaum Zeilenumbrueche hat.

LESEN GEGEN SCHREIBEN wird getrennt gefuehrt. Ein verschluckter LESEfehler
heisst meist „zeig die alten Daten weiter" und ist am Bau oft gewollt
(Offline-Faehigkeit). Ein verschluckter SCHREIBfehler heisst Datenverlust.
Deshalb stehen beide im Bericht, aber nur die Schreibfaelle sind der Befund.

Aufruf:  python scripts/stille_schreibfehler.py
Ergebnis: docs/befunde/STILLE_SCHREIBFEHLER.md
"""
import io
import os
import re
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
WURZEL = os.path.dirname(HIER)

import code_scan  # noqa: E402

ZIEL = os.path.join(WURZEL, "index.html")

# Die Helfer, die WIRKLICH schreiben. Jeder von ihnen wirft bei 401/403.
SCHREIBER = ["_sbPost", "_sbPatch", "_sbUpsert", "_sbDelete", "_sbDeleteWhere",
             "_sbInsertIfAbsent", "_sbUploadFile", "_sbRpc", "_sbStorageDelete"]
# Lesen wird getrennt gefuehrt, nicht mitgezaehlt.
LESER = ["_sbGet", "_sbGetOrder", "_sbGetUsersSafe", "_sbSignedDocUrl"]

# 🔴 EINE ZAHL IST KEIN BEFUND. Drei verworfene Schreibfehler koennen drei
#    Defekte sein oder dreimal dieselbe berechtigte Entscheidung. Wer das
#    nicht dazuschreibt, laesst den naechsten Leser dreimal dieselbe
#    Untersuchung machen - oder schlimmer, etwas "reparieren", das richtig
#    ist. Beurteilt wird nach der Tabelle, in die geschrieben wird.
BEURTEILT = {
    "plz_geo": ("berechtigt",
                "Zwischenspeicher fuer eine Geokodierung. Die ARBEIT steht "
                "seit v3.9.987 vor dem Versuch - vorher riss der "
                "fehlgeschlagene Cache-Schreibvorgang den ganzen Lauf mit. "
                "Beleg: scripts/geo_nachzieh_wirkung.py"),
    "plz_distanz": ("berechtigt",
                    "Zwischenspeicher fuer die Entfernungsmatrix. "
                    "`distMatrix` und `matrixRows` stehen seit v3.9.987 vor "
                    "dem Versuch. Beleg: scripts/geo_nachzieh_wirkung.py"),
}

# 🔴 Ein `catch` ohne Klammern um den Fehler gibt es auch: `catch{}`. Wer nur
#    `catch(` sucht, meldet die stillsten Faelle nicht - und das sieht aus wie
#    ein Befund. Beide Schreibweisen, plus beliebiger Zwischenraum.
CATCH = re.compile(r"\bcatch\s*(\([^)]{0,40}\))?\s*\{")
TRY = re.compile(r"\btry\s*\{")


def _leer(rumpf):
    """Ist der Rumpf leer - oder enthaelt er nur einen Kommentar?

    🔴 Beides wird gefunden, aber GETRENNT gemeldet. Ein Kommentar erklaert
    hoechstens, warum geschluckt wird; er sagt dem Nutzer nichts. Ihn als
    Behandlung zu zaehlen waere genau die Regel
    [[mlg-regel-kommentar-erfuellt-den-riegel]].
    """
    ohne = re.sub(r"/\*.*?\*/", "", rumpf, flags=re.S)
    ohne = re.sub(r"//[^\n]*", "", ohne)
    if ohne.strip():
        return None
    return "nur_kommentar" if rumpf.strip() else "leer"


def _rumpf(text, auf):
    """Der Inhalt zwischen `auf` (Position der oeffnenden Klammer) und der
    passenden schliessenden.

    🔴 `code_scan._klammer_zu` gibt die Stelle HINTER der schliessenden
    Klammer zurueck, nicht die Klammer selbst - so steht es in seinem
    Kopftext. Mein erster Entwurf hat sie fuer die Klammer gehalten und war
    damit um eins verschoben: das `catch` fing danach mit `atch` an und wurde
    NIE gefunden. Die Eichung hat das abgefangen, bevor eine Null als Befund
    gemeldet wurde.

    Zurueck kommt (Rumpf, Stelle hinter der schliessenden Klammer).
    """
    ende = code_scan._klammer_zu(text, auf, "{", "}")
    if ende < 0:
        return None, -1
    return text[auf + 1:ende - 1], ende


def paare(text, ist=None):
    """Alle try/catch-Paare als (try_anfang, rumpf_von, rumpf_bis, form).

    `form` ist 'leer', 'nur_kommentar' oder None (das catch behandelt etwas).
    """
    if ist is None:
        ist = code_scan.ist_code(text)
    aus = []
    for m in TRY.finditer(text):
        auf = m.end() - 1
        if auf < len(ist) and not ist[auf]:
            continue
        rumpf, ende = _rumpf(text, auf)
        if ende < 0:
            continue
        # Direkt hinter dem try-Block muss das catch stehen. Dazwischen darf
        # nur Zwischenraum liegen - `finally` ohne catch ist kein Fall.
        rest = text[ende:ende + 60]
        c = CATCH.match(rest.lstrip())
        if not c:
            continue
        cauf = ende + (len(rest) - len(rest.lstrip())) + c.end() - 1
        crumpf, _cende = _rumpf(text, cauf)
        if crumpf is None:
            continue
        aus.append((m.start(), auf + 1, ende - 1, _leer(crumpf)))
    return aus


def faelle(text, ist=None):
    """Jeder Aufruf eines Helfers, dessen INNERSTES try ihn wegwirft.

    🔴 WARUM DAS INNERSTE UND NICHT JEDES. Mein erster Entwurf urteilte ueber
    jeden try-Block, in dessen Rumpf irgendwo ein Schreibaufruf vorkam. Das
    ist wahr und trotzdem irrefuehrend: bei zwei der sechs Treffer war der
    Schreibaufruf in ein EIGENES try/catch gefasst, das ihn behandelt, und
    das aeussere catch galt der Geocoding-Abfrage daneben. Gemeldet wurden
    damit sechs Faelle, wo es weniger sind - eine Zahl, die zu GROSS ist,
    ist genauso falsch wie eine zu kleine.

    Beurteilt wird deshalb pro AUFRUF das innerste ihn umschliessende
    try/catch. Behandelt dieses den Fehler, ist der Fall erledigt - auch
    wenn zehn aeussere ihn verwerfen wuerden.

    Zurueck: (position, art, leerform, name).
    """
    if ist is None:
        ist = code_scan.ist_code(text)
    p = paare(text, ist)
    aus = []
    for name, art in ([(s, "schreiben") for s in SCHREIBER]
                      + [(s, "lesen") for s in LESER]):
        i = text.find(name + "(")
        while i >= 0:
            if i < len(ist) and ist[i]:
                innen = [x for x in p if x[1] <= i < x[2]]
                if innen:
                    _t, von, _bis, form = max(innen, key=lambda x: x[1])
                    if form:
                        aus.append((i, art, form, [name]))
            i = text.find(name + "(", i + 1)
    return sorted(aus)


def eichen():
    """🔴 Ein Koeder JE FORM. Ohne sie ist jede Null hier wertlos.

    Gibt die Liste der misslungenen Proben zurueck; leer heisst geeicht.
    """
    proben = [
        ("leeres catch mit Klammern",
         "try{await _sbPatch('t',1,{a:1});}catch(_){}", "schreiben", "leer"),
        ("catch OHNE Klammern",
         "try{await _sbPost('t',{});}catch{}", "schreiben", "leer"),
        ("catch mit NUR einem Kommentar",
         "try{await _sbUpsert('t',{});}catch(e){/* egal */}",
         "schreiben", "nur_kommentar"),
        ("Lesen wird als Lesen gefuehrt",
         "try{await _sbGet('t');}catch(_){}", "lesen", "leer"),
    ]
    schief = []
    for name, quelle, art_soll, form_soll in proben:
        f = faelle(quelle, [True] * len(quelle))
        if len(f) != 1:
            schief.append("%s: %d Treffer statt 1" % (name, len(f)))
            continue
        _, art, form, _n = f[0]
        if art != art_soll or form != form_soll:
            schief.append("%s: gefunden als (%s,%s), erwartet (%s,%s)"
                          % (name, art, form, art_soll, form_soll))
    # Gegenproben: was NICHT gefunden werden darf.
    gegen = [("behandeltes catch",
              "try{await _sbPatch('t',1,{});}catch(e){meldeFehler(e);}"),
             ("catch mit nur einer Zuweisung",
              "try{await _sbPost('t',{});}catch(e){ok=false;}"),
             ("try ohne catch",
              "try{await _sbPost('t',{});}finally{schliesse();}"),
             # 🔴 DIE PROBE, DIE DEN ERSTEN ENTWURF WIDERLEGT HAT: das
             #    aeussere catch verwirft, das innere behandelt. Gemeldet
             #    werden darf hier NICHTS - sonst zaehlt der Sucher zu viel.
             ("inneres catch behandelt, aeusseres verwirft",
              "try{hole();try{await _sbPost('t',{});}catch(e){melde(e);}}"
              "catch(_){}")]
    for name, quelle in gegen:
        if faelle(quelle, [True] * len(quelle)):
            schief.append("GEGENPROBE %s: wird faelschlich gemeldet" % name)
    # 🔴 Und die Umkehrung, damit die Gegenprobe darueber nicht einfach
    #    dadurch besteht, dass gar nichts gefunden wird.
    verschachtelt = ("try{hole();try{await _sbPost('t',{});}catch(e){}}"
                     "catch(x){melde(x);}")
    if len(faelle(verschachtelt, [True] * len(verschachtelt))) != 1:
        schief.append("Verschachtelt MIT leerem INNEREN catch wird nicht "
                      "gemeldet - dann sieht der Sucher gar keine "
                      "verschachtelten Faelle.")
    return schief


def main(argv):
    schief = eichen()
    print("Eichung: 5 Koeder, 4 Gegenproben")
    if schief:
        for s in schief:
            print("   \U0001F534 " + s)
        print("\nNICHT GEMESSEN. Ein ungeeichter Sucher meldet eine Null, die "
              "von\n„es gibt keine“ nicht zu unterscheiden ist.")
        return 2
    print("   \U0001F7E2 alle neun richtig\n")

    text = io.open(ZIEL, encoding="utf-8", newline="").read()
    ist = code_scan.ist_code(text)

    # 🔴 GEGENPROBE ZUR NULL an der echten Datei: findet der Klammerabgleich
    #    ueberhaupt try/catch-Paare, und kommen die Helfer ueberhaupt vor?
    #    Ohne das koennte eine Null auch heissen, dass nichts gemessen wurde.
    p = paare(text, ist)
    rufe = sum(len(code_scan.nur_code_stellen(text, s + "("))
               for s in SCHREIBER + LESER)
    print("Grundgesamtheit: %d try/catch-Paare, %d Helfer-Aufrufe im Code"
          % (len(p), rufe))
    if not p or not rufe:
        print("\U0001F534 Eine der beiden ist LEER. Das ist kein Ergebnis.")
        return 2

    alle = faelle(text, ist)
    nach = {"schreiben": [], "lesen": []}
    ziel_re = re.compile(r"""_sb\w+\(\s*["']([^"']+)["']""")
    for pos, art, form, namen in alle:
        z = ziel_re.match(text[pos:pos + 80])
        tab = z.group(1) if z else "?"
        nach[art].append((text.count("\n", 0, pos) + 1, form, namen, tab))
    unbeurteilt = [x for x in nach["schreiben"] if x[3] not in BEURTEILT]

    print("Aufrufe, deren INNERSTES catch den Fehler verwirft:")
    print("   schreiben : %3d von %d" % (len(nach["schreiben"]),
                                         sum(len(code_scan.nur_code_stellen(
                                             text, s + "(")) for s in SCHREIBER)))
    print("   lesen     : %3d  (oft gewollt: Offline-Faehigkeit)"
          % len(nach["lesen"]))

    z = ["# Stille Schreibfehler - wer wirft den Fehler weg?", "",
         "Erzeugt von `scripts/stille_schreibfehler.py`.", "",
         "Die Schreib-Helfer sind in Ordnung: `_sbPost`, `_sbPatch`, "
         "`_sbUpsert`,",
         "`_sbDelete`, `_sbDeleteWhere`, `_sbInsertIfAbsent` pruefen "
         "**jeder** auf 401",
         "und 403, rufen `_onAuthFail` und **werfen** mit Status im Text.",
         "Gesucht wird deshalb nicht am Helfer, sondern beim **Aufrufer**: "
         "ein leeres",
         "`catch`, dessen `try` einen Schreibvorgang enthaelt.", "",
         "| Art | Anzahl | Bedeutung |", "|---|---:|---|",
         "| **schreiben** | **%d** | der Nutzer glaubt, es sei gespeichert |"
         % len(nach["schreiben"]),
         "| lesen | %d | zeigt die alten Daten weiter - oft gewollt |"
         % len(nach["lesen"]), "",
         "Beurteilt wird je Aufruf das **innerste** ihn umschliessende "
         "`try/catch`.",
         "Behandelt dieses den Fehler, ist der Fall erledigt - auch wenn ein",
         "aeusseres ihn verwerfen wuerde. Der erste Entwurf urteilte ueber "
         "jedes",
         "umschliessende `try` und meldete dadurch zu VIELE Faelle.", ""]

    for art, ueber in (("schreiben",
                        "🔴 Schreibvorgaenge, deren Fehler verworfen wird"),
                       ("lesen",
                        "Lesevorgaenge (zur Einordnung, kein Befund)")):
        z += ["## %s" % ueber, ""]
        if not nach[art]:
            z += ["Keiner.", ""]
            continue
        z += ["| Zeile | Ziel | catch | Urteil |", "|---:|---|---|---|"]
        for zeile, form, namen, tab in sorted(nach[art]):
            u, warum = BEURTEILT.get(tab, ("UNBEURTEILT",
                                           "noch niemand angesehen"))
            z.append("| %d | `%s` | %s | **%s** — %s |"
                     % (zeile, tab,
                        "leer" if form == "leer" else "nur Kommentar",
                        u, warum))
        z.append("")

    ordner = os.path.join(WURZEL, "docs", "befunde")
    if not os.path.isdir(ordner):
        os.makedirs(ordner)
    pfad = os.path.join(ordner, "STILLE_SCHREIBFEHLER.md")
    io.open(pfad, "w", encoding="utf-8", newline="").write("\n".join(z) + "\n")
    print("\ngeschrieben:", pfad)
    if nach["schreiben"]:
        print("\n%d Stellen verwerfen einen Schreibfehler:"
              % len(nach["schreiben"]))
        for zeile, form, namen, tab in sorted(nach["schreiben"]):
            u = BEURTEILT.get(tab, ("\U0001F534 UNBEURTEILT",))[0]
            print("   Zeile %-6d %-13s %-13s %s" % (zeile, tab, u,
                                                    ", ".join(namen)))
    if unbeurteilt:
        print("\n\U0001F534 %d davon hat noch niemand beurteilt. Eine ZAHL "
              "ist kein Befund -\n   jede Stelle gehoert angesehen und in "
              "BEURTEILT eingetragen, mit Grund."
              % len(unbeurteilt))
        return 1
    print("\n\U0001F7E2 Jede verworfene Schreibstelle ist angesehen und "
          "begruendet.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
