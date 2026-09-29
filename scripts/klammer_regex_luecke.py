# -*- coding: utf-8 -*-
"""Wie oft kann `code_scan._klammer_zu` an einem Regex-Literal entgleisen?

🔴 GEMELDET VON EINEM MESSAGENTEN in der Nacht auf den 30.09.2026, und es
ist ein Befund an UNSEREM Werkzeug, nicht am Programm: `_klammer_zu`
ueberspringt Zeichenketten (`"`, `'`, Backtick), aber **keine
Regex-Literale**. Der Rumpf von `_translateAndExec` kam dadurch mit
**2 195 Zeilen statt 341** zurueck - viermal die Funktion.

Das trifft fuenf Riegel und Werkzeuge, die den Rumpf per Klammerabgleich
holen: `stille_schreibfehler.py`, `keydown_container_audit.py`,
`test_geo_cache_nicht_tragend_v987.py`, `test_tafel_austritt_v988.py` und
`test_tote_regeln_v989.py`.

WAS HIER GEZAEHLT WIRD: Regex-Literale im CODE, die ein Zeichen enthalten,
an dem `_klammer_zu` aus dem Tritt kommt -

    {  }   verschieben die Klammerzaehlung
    "  '   eroeffnen fuer `_klammer_zu` eine Zeichenkette, die nie endet
    `      dasselbe mit einem Vorlagenliteral

🔴 Gefunden werden die Regex-Literale mit `code_scan.ist_code`, denn das
KENNT sie (es hat einen eigenen Zweig dafuer). Der Vergleich ist also:
was das eine Werkzeug richtig erkennt, stolpert das andere um.

🔴 SELBSTPROBE: ein gebautes Regex-Literal mit einer Klammer darin muss
gefunden werden, und `_klammer_zu` muss daran nachweislich entgleisen.
Ohne diese zweite Haelfte waere die Zahl nur eine Vermutung.

Aufruf:  python scripts/klammer_regex_luecke.py
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
STOLPERSTEINE = "{}\"'`"


def regex_literale(text, ist=None):
    """Alle Regex-Literale im Code, als (Anfang, Ende, Text).

    Gefunden werden sie ueber die Code-Maske: `ist_code` markiert ein
    Regex-Literal vollstaendig als Code, und es beginnt mit `/`, dem kein
    `*` oder `/` folgt. Die Maske ist die einzige Quelle, die sie kennt -
    ein eigenes Muster waere ein zweites, das anders irrt.
    """
    if ist is None:
        ist = code_scan.ist_code(text)
    aus = []
    i = 0
    n = len(text)
    while i < n - 1:
        if text[i] == "/" and ist[i] and text[i + 1] not in "*/":
            # Ende suchen: das naechste unmaskierte `/` in derselben Zeile.
            j = i + 1
            in_klasse = False
            while j < n:
                c = text[j]
                if c == "\\":
                    j += 2
                    continue
                if c == "\n":
                    j = -1
                    break
                if c == "[":
                    in_klasse = True
                elif c == "]":
                    in_klasse = False
                elif c == "/" and not in_klasse:
                    break
                j += 1
            # 🔴 IST DAS WIRKLICH EIN REGEX - oder eine DIVISION? Mein erster
            #    Entwurf fragte nicht und meldete 572 Literale, darunter
            #    `/TIME_HOUR);return{...` und `/1000;if(isNaN(diff))...`.
            #    Das sind Divisionen, und die Zahl war damit zu GROSS - was
            #    genauso falsch ist wie zu klein, nur glaubwuerdiger.
            #    Entschieden wird es von der EINEN Quelle, die es weiss:
            #    `ist_code` markiert ein Regex-Literal VOLLSTAENDIG als Code,
            #    auch die Anfuehrungszeichen darin. Bei einer Division waere
            #    ein Anfuehrungszeichen dahinter der Anfang einer
            #    Zeichenkette und damit NICHT als Code markiert.
            if j > i and all(ist[k] for k in range(i, j + 1)):
                aus.append((i, j, text[i:j + 1]))
                i = j + 1
                continue
        i += 1
    return aus


def eichen():
    """🔴 Zwei Haelften: der Sucher findet es, UND `_klammer_zu` entgleist."""
    schief = []
    # 🔴 DER ERSTE KOEDER WAR FALSCH GEWAEHLT, und das gehoert hierher:
    #    `/[{}]/g` enthaelt eine OEFFNENDE und eine SCHLIESSENDE Klammer -
    #    die Zaehlung geht auf, `_klammer_zu` entgleist nicht. Der Koeder
    #    teilte die Luecke nicht, er war gar keine. Die echten Faelle sind
    #    eine UNPAARIGE Klammer und ein ANFUEHRUNGSZEICHEN im Regex.
    faelle = [
        ("unpaarige schliessende Klammer",
         'function f(){ var r = /\\}/g; return 1; }'),
        ("Anfuehrungszeichen im Regex",
         'function f(){ var r = /["\']/g; return 1; }'),
    ]
    for name, quelle in faelle:
        ist = code_scan.ist_code(quelle)
        gef = [t for _a, _b, t in regex_literale(quelle, ist)]
        if not gef:
            schief.append("%s: das Regex-Literal wird nicht gefunden." % name)
            continue
        auf = quelle.index("{")                  # die Funktionsklammer
        ende = code_scan._klammer_zu(quelle, auf, "{", "}")
        if ende == len(quelle):
            schief.append(
                "%s: `_klammer_zu` kommt NICHT aus dem Tritt (Ende %d, "
                "richtig %d).\n     Dann ist die gemeldete Luecke fuer "
                "diese Form keine." % (name, ende, len(quelle)))
    # Gegenprobe: ohne Regex-Literal muss es stimmen.
    sauber = 'function f(){ var r = 1; return 1; }'
    if code_scan._klammer_zu(sauber, sauber.index("{"), "{", "}") != \
            len(sauber):
        schief.append("`_klammer_zu` irrt sich schon OHNE Regex-Literal - "
                      "dann liegt der Fehler\n     woanders und dieser "
                      "Vergleich taugt nicht.")
    return schief


def main(argv):
    schief = eichen()
    print("Eichung: 3 Proben - zwei Entgleisungsformen und eine Gegenprobe")
    if schief:
        for s in schief:
            print("   \U0001F534 " + s)
        print("\nNICHT GEMESSEN.")
        return 2
    print("   \U0001F7E2 alle drei richtig\n")

    text = io.open(ZIEL, encoding="utf-8", newline="").read()
    ist = code_scan.ist_code(text)
    alle = regex_literale(text, ist)
    if not alle:
        print("\U0001F534 KEIN Regex-Literal gefunden. Das ist kein "
              "Ergebnis - die Datei ist voll davon.")
        return 2

    # 🔴 NICHT JEDER STOLPERSTEIN LENKT UM. `{4}` und `{1,2}` sind PAARIG -
    #    die Zaehlung geht auf, `_klammer_zu` entgleist nicht. Wer sie
    #    mitzaehlt, meldet eine zu grosse Zahl. Gefaehrlich ist nur:
    #      * eine UNPAARIGE Klammer  -> die Zaehlung verschiebt sich um eins
    #      * ein ANFUEHRUNGSZEICHEN  -> `_zeichenkette_ueberspringen` sucht
    #        das Gegenstueck und schluckt alles dazwischen, oft ueber
    #        tausende Zeichen
    unpaarig, mit_quote = [], []
    for a, _b, t in alle:
        if t.count("{") != t.count("}"):
            unpaarig.append((a, t))
        if any(c in t for c in "\"'`"):
            mit_quote.append((a, t))
    risiko = {a: t for a, t in unpaarig}
    risiko.update({a: t for a, t in mit_quote})
    print("%d Regex-Literale im Code." % len(alle))
    print("   mit unpaariger Klammer : %3d  \U0001F534 verschiebt die "
          "Zaehlung" % len(unpaarig))
    print("   mit Anfuehrungszeichen : %3d  \U0001F534 schluckt alles bis "
          "zum Gegenstueck" % len(mit_quote))
    print("   zusammen               : %3d Stellen mit echtem Risiko"
          % len(risiko))
    print("   (nur paarige Klammern wie `{4}` oder `{1,2}`: harmlos, "
          "nicht gezaehlt)")
    print("\nDie riskanten, die ersten zwoelf:")
    for a in sorted(risiko)[:12]:
        print("   Zeile %-7d %s" % (text.count("\n", 0, a) + 1,
                                    risiko[a][:70]))
    print("\n\U0001F7E1 DIE ZAHL IST EINE OBERGRENZE, und das steht hier, "
          "statt weggelassen zu werden.\n"
          "   Zwei Formen zaehlt dieser Sucher faelschlich mit:\n"
          "     * eine DIVISION, deren Spanne zufaellig ganz aus Code "
          "besteht (Zeile 696, 7920)\n"
          "     * HTML in einem Vorlagenliteral, wo `</span>` wie ein "
          "Regex-Anfang aussieht\n       (Zeile 11321 und die Reihe "
          "darunter)\n"
          "   Beide gehoeren nicht dazu. Die ECHTE Zahl liegt darunter - "
          "wieviel darunter,\n   ist nicht gemessen. Sie genuegt fuer die "
          "Aussage „die Luecke ist real und\n   nicht einzeln "
          "abzaehlbar“, nicht fuer eine Statistik.")
    print("\n\U0001F534 Jedes davon kann einen Klammerabgleich umlenken, der "
          "darueber hinweglaeuft.\n   Betroffen: stille_schreibfehler.py, "
          "keydown_container_audit.py,\n   "
          "test_geo_cache_nicht_tragend_v987.py, test_tafel_austritt_v988.py")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
