# -*- coding: utf-8 -*-
"""Welche Abfrage holt eine GANZE Tabelle, ohne zu filtern und ohne Grenze?

🔴 AUFGEFALLEN BEIM BEFUND B1. Die Atteste werden mit

    _sbGet("absence_files", "select=...&order=created_at.desc")

geholt - kein `worker_id=eq.`, kein `limit=`. Der Browser bekommt alles, was
die Datenbank herausgibt, und sortiert erst danach im Speicher. Das hat drei
Seiten:

  * **Menge.** Waechst die Tabelle, waechst die Ladezeit mit - auf einem
    Telefon im Funkloch ist das der Unterschied zwischen benutzbar und nicht.
  * **Sichtbarkeit.** Was der Server liefert, steht im Speicher des Browsers,
    auch wenn die Oberflaeche es nicht zeigt. Ob er es liefern darf,
    entscheidet der Zeilenschutz - von hier aus nicht pruefbar.
  * **Stille Kappung.** Steht doch ein `limit`, liefert die Datenbank
    stillschweigend weniger Zeilen, als es gibt. Eine Liste, die bei 5000
    aufhoert, sieht vollstaendig aus.

🔴 WAS DIESES WERKZEUG NICHT BEHAUPTET: dass jede solche Abfrage falsch ist.
Eine kleine Stammdatentabelle ganz zu holen ist voellig richtig. Gezaehlt
wird die FORM, und daneben steht, wie gross die Tabelle werden kann - das
entscheidet, ob es ein Fehler ist. Diese Einschaetzung ist NICHT gemessen und
als Vermutung gekennzeichnet.

🔴 DER ERSTE ENTWURF HAT DIE FALSCHE SCHICHT GEMESSEN, und das ist der
wichtigste Satz in diesem Kopftext. Er las nur die Abfrage, die der AUFRUFER
uebergibt, und meldete daraufhin "36 Abfragen ohne Grenze". Das ist falsch:

    async function _sbGet(table, filter){
      const parts=[hasSelect?"":"select=*", filter||"", "limit=5000"]...

`_sbGet` UND `_sbGetOrder` haengen **bedingungslos** `limit=5000` an
(index.html:2152 und 2160). Es gibt also keine Abfrage ohne Grenze - jede ist
bei 5000 Zeilen gekappt. Der Befund dreht sich damit: nicht "holt alles",
sondern **"hoert bei 5000 auf, und niemand merkt es"**.

Gefunden wurde das nicht durch Nachdenken, sondern durch einen Kommentar
neben einer der gemeldeten Zeilen: "v3.9.500 - _sbGet setzt default
limit=5000". Eine Messung, die eine Schicht zu hoch ansetzt, liefert eine
saubere Zahl zur falschen Frage.

🔴 SELBSTPROBE: vier gebaute Faelle - ohne alles, nur mit `order`, mit
`eq.`-Filter, mit eigenem `limit` - und dazu die Probe, dass die
Helfer-Grenze im Quelltext ueberhaupt gefunden wird. Faellt die weg, meldet
dieses Werkzeug wieder die falsche Frage.

Aufruf:  python scripts/vollabzug_jagen.py
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

# 🔴 ZWEI SCHREIBWEISEN: einfache UND doppelte Anfuehrungszeichen.
AUFRUF = re.compile(
    r"""_sbGet\w*\(\s*(['"])([A-Za-z_][A-Za-z0-9_]*)\1\s*,\s*(['"])(.*?)\3""",
    re.S)
# Ein echter Filter in PostgREST: spalte=eq.wert, =in.(...), =gte. usw.
FILTER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*=(eq|neq|gt|gte|lt|lte|in|is|"
                    r"like|ilike|cs|cd|ov|sl|sr|fts|plfts|phfts|wfts)\.")
GRENZE = re.compile(r"\blimit=(\d+)")


def stellen(text, ist=None):
    """(Zeile, Tabelle, Abfrage, hat_filter, grenze) je `_sbGet`-Aufruf."""
    if ist is None:
        ist = code_scan.ist_code(text)
    aus = []
    for m in AUFRUF.finditer(text):
        if m.start() < len(ist) and not ist[m.start()]:
            continue
        q = m.group(4)
        g = GRENZE.search(q)
        aus.append((text.count("\n", 0, m.start()) + 1, m.group(2), q,
                    bool(FILTER.search(q)), int(g.group(1)) if g else None))
    return aus


HELFER_GRENZE = re.compile(
    r"async function _sbGet(?:Order)?\([^)]*\)\{[^}]{0,400}?"
    r'"limit=(\d+)"', re.S)


def helfer_grenze(text):
    """Die Grenze, die der HELFER selbst anhaengt - oder None.

    🔴 Ohne diese Zahl misst das Werkzeug die falsche Frage. Genau daran ist
    der erste Entwurf gescheitert: er las nur die Abfrage des Aufrufers.
    """
    werte = set(int(m) for m in HELFER_GRENZE.findall(text))
    return sorted(werte)


def eichen():
    """🔴 Vier Koeder, plus die Probe auf die Helfer-Grenze."""
    schief = []
    # 🔴 Die Helfer-Grenze MUSS im Quelltext gefunden werden.
    kunst = ('async function _sbGet(table,filter){\n'
             '  const parts=[hasSelect?"":"select=*",filter||"",'
             '"limit=5000"].filter(Boolean);\n}')
    if helfer_grenze(kunst) != [5000]:
        schief.append("Die Helfer-Grenze wird im Kunsttext nicht gefunden "
                      "(%r statt [5000]).\n     Dann misst dieses Werkzeug "
                      "wieder die falsche Schicht."
                      % helfer_grenze(kunst))
    proben = [
        ("ohne alles", '_sbGet("tabelle","select=id")', True),
        ("nur order", "_sbGet('t2','select=id&order=x.desc')", True),
        ("mit Filter", '_sbGet("t3","select=id&worker_id=eq.7")', False),
        ("mit Grenze", "_sbGet('t4','select=id&limit=50')", False),
    ]
    for name, quelle, soll_voll in proben:
        s = stellen(quelle, [True] * len(quelle))
        if len(s) != 1:
            schief.append("%s: %d Treffer statt 1" % (name, len(s)))
            continue
        _z, _t, _q, hat_filter, grenze = s[0]
        ist_voll = not hat_filter and grenze is None
        if ist_voll != soll_voll:
            schief.append("%s: als %s eingestuft, erwartet %s"
                          % (name, "Vollabzug" if ist_voll else "gefiltert",
                             "Vollabzug" if soll_voll else "gefiltert"))
    return schief


# 🔴 VERMUTUNG, NICHT MESSUNG: wie gross kann die Tabelle werden? Ohne
#    Datenbankzugang ist das eine Einschaetzung aus dem Zweck der Tabelle.
#    Sie steht hier, damit der Bericht die Form von der Bedeutung trennt.
WAECHST_MIT = {
    "absence_files": "je Krankmeldung eine Zeile - waechst mit den Jahren",
    "absences": "je Abwesenheitstag eine Zeile - waechst stark",
    "entries": "je Zeiterfassung eine Zeile - waechst am staerksten",
    "arbeitsscheine": "je Auftrag eine Zeile - waechst stark",
    "weekplan_rows": "je Planzeile und Woche - waechst stark",
    "notifications": "je Meldung eine Zeile - waechst stark",
    "push_log": "je Zustellversuch eine Zeile - waechst stark",
    "workers": "Stammdaten - klein",
    "users": "Stammdaten - klein",
    "fahrzeuge": "Stammdaten - klein",
    "werkzeuge": "Stammdaten - mittel",
    "projects": "je Bauvorhaben - mittel",
}


def main(argv):
    schief = eichen()
    print("Eichung: 2 Koeder, 2 Gegenproben")
    if schief:
        for s in schief:
            print("   \U0001F534 " + s)
        print("\nNICHT GEMESSEN.")
        return 2
    print("   \U0001F7E2 alle vier richtig\n")

    text = io.open(ZIEL, encoding="utf-8", newline="").read()
    alle = stellen(text)
    if not alle:
        print("\U0001F534 KEIN `_sbGet`-Aufruf gefunden. Das ist kein "
              "Ergebnis - der Sucher greift daneben.")
        return 2

    hg = helfer_grenze(text)
    if not hg:
        print("\U0001F534 Im Quelltext ist keine Grenze im Helfer zu finden. "
              "Dann ist unklar,\n   wie viele Zeilen eine Abfrage wirklich "
              "liefert. NICHT GEMESSEN.")
        return 2
    print("Der HELFER haengt an jede Abfrage an: limit=%s"
          % ", ".join(str(g) for g in hg))
    print("Damit gibt es KEINE Abfrage ohne Grenze - jede ist gekappt.\n")

    voll = [s for s in alle if not s[3] and s[4] is None]
    eigen = [s for s in alle if s[4] is not None]
    gefiltert = [s for s in alle if s[3]]
    doppelt = [s for s in eigen if s[4] > max(hg)]
    print("%d Leseaufrufe im Code:" % len(alle))
    print("   mit Filter                     : %3d" % len(gefiltert))
    print("   ohne Filter (Helfergrenze %d)  : %3d  \U0001F534 hoert still "
          "bei %d auf" % (max(hg), len(voll), max(hg)))
    print("   mit EIGENER Grenze             : %3d" % len(eigen))
    print("   davon eigene Grenze > %d      : %3d  \U0001F534 zwei "
          "widersprechende limit-Angaben" % (max(hg), len(doppelt)))
    if doppelt:
        print("\n\U0001F534 Der Aufrufer fordert MEHR, als der Helfer "
              "zulaesst - beide limit-Angaben\n   stehen in derselben "
              "Adresse, die des Helfers ZULETZT:")
        for z, tab, _q, _f, g in doppelt:
            print("   Zeile %-7d %-24s fordert %d, Helfer haengt %d an"
                  % (z, tab, g, max(hg)))

    def zeig(liste, titel):
        if not liste:
            return
        print("\n%s" % titel)
        gesehen = {}
        for z, tab, q, _f, g in sorted(liste, key=lambda x: x[1]):
            gesehen.setdefault(tab, []).append((z, g))
        for tab in sorted(gesehen):
            wo = ", ".join("%d%s" % (z, "" if g is None else " (limit %d)" % g)
                           for z, g in gesehen[tab])
            hinweis = WAECHST_MIT.get(tab, "unbekannt, nicht eingeschaetzt")
            print("   %-22s Zeile %-28s %s" % (tab, wo, hinweis))

    zeig(voll, "\U0001F534 GANZE Tabelle, ohne Filter und ohne Grenze:")
    zeig(gekappt, "\U0001F7E1 ohne Filter, aber mit Grenze:")
    print("\n\U0001F534 GRENZE DIESER MESSUNG: gezaehlt ist die FORM der "
          "Abfrage. Ob eine Tabelle\n   wirklich gross wird und ob der "
          "Zeilenschutz sie einschraenkt, ist von hier\n   aus nicht "
          "pruefbar - die Spalte rechts ist eine Einschaetzung aus dem "
          "Zweck,\n   keine Messung.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
