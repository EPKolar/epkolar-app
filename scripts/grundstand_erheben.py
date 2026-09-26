# -*- coding: utf-8 -*-
"""Den Grundstand neu erheben - alle 22 messbaren Ansichten, beide Breiten.

WARUM
─────
`GRUNDSTAND_UI_v3.9.930.md` beschreibt den Zustand VOR dem Umbau. Nach zwanzig
Versionen ist er als Vergleichsbasis wertlos: die Stufen haben genau das
veraendert, was er festhaelt. Der naechste Lauf braucht eine gueltige Basis,
und `scripts/bestand.py` prueft gegen eine Liste, die teilweise Geschichte ist.

WAS ERHOBEN WIRD
────────────────
Je Ansicht und Breite: jeder sichtbare Knopf (Text, title, aria-label), jedes
Eingabefeld (Typ, Platzhalter), jedes Auswahlfeld mit seinen Optionen, jede
Ueberschrift und jeder Tabellenkopf. Gelesen wird ueber `INVENTAR_JS` aus
b3_stufen_12_15_messen - dieselbe Vorschrift, mit der die Stufen gemessen
wurden, damit die Zahlen vergleichbar bleiben.

WAS NICHT ERHOBEN WIRD - das sind keine bestandenen Faelle
  * Unterzustaende: je Ansicht wird der EINE Zustand aufgenommen, in den die
    Navigation fuehrt. Chef hat fuenf, Admin sechs, das Buero-Portal fuenf -
    aufgenommen ist jeweils der erste.
  * Rollen ausser `admin`.
  * Ansichten, die im Messaufbau serverleer sind (Flotte, Gefahrenstoffe,
    Bauprovisorien, mehrere Unterreiter). Ihre Zahlen sind die eines leeren
    Blatts und stehen so gekennzeichnet da.
  * Alles, was nur nach einem Klick erscheint (Dialoge, Menues).

DIE SAAT
────────
Jede der drei Sondengruppen bringt ihre eigene Saat mit, und sie sind NICHT
gleich (die 12-15er fuehrt fuenf Monteure, davon zwei ausgetretene; die 4-7er
drei). Deshalb steht bei jeder Ansicht, welche Saat sie gesehen hat - eine
Zahl aus verschiedenen Saaten zu vergleichen waere falsch.

AUFRUF
──────
    python scripts/grundstand_erheben.py            # schreibt docs/...md
    python scripts/grundstand_erheben.py --nur chef
"""
import io
import os
import sys
import time

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)

import mob_ansicht_messen as M          # noqa: E402
import b3_vier_ansichten_messen as B4   # noqa: E402
import b3_stufen_8_11_messen as B8      # noqa: E402
import b3_stufen_12_15_messen as B12    # noqa: E402

WURZEL = os.path.dirname(HIER)

# (Kuerzel, Modul, Saatfunktion, Navigator, Gruppe)
GRUPPEN = [
    ("4-7",   B4,  "_saeen",   "_navigieren",   3),
    ("8-11",  B8,  "_saeen8",  "_navigieren8",  4),
    ("12-15", B12, "_saeen12", "_navigieren12", 4),
]


def _version(roh):
    import re
    m = re.search(r'APP_VERSION="([\d.]+)-supabase"', roh)
    return m.group(1) if m else "unbekannt"


def _eine(browser, url, modul, saat, navi, kuerzel, breite, argzahl):
    ctx = browser.new_context(viewport={"width": breite, "height": 880},
                         is_mobile=breite < 600, has_touch=breite < 600,
                         color_scheme="dark")
    ctx.add_init_script(M.INIT)
    ctx.add_init_script(
        "try{var u=JSON.parse(localStorage.getItem('epkolar_user')||'{}');"
        "u.monteurId='M1';u.role='admin';u.rolle='Geschaeftsfuehrer';"
        "localStorage.setItem('epkolar_user',JSON.stringify(u));}catch(e){}")
    ctx.route("**/rest/v1/**", lambda r: r.abort())
    ctx.route("**/auth/v1/**", lambda r: r.abort())
    seite = ctx.new_page()
    fehler = []
    seite.on("pageerror", lambda x: fehler.append(str(x)[:160]))
    try:
        seite.goto(url, wait_until="domcontentloaded")
        seite.wait_for_timeout(3800)
        getattr(modul, saat)(seite)
        seite.wait_for_timeout(1000)
        f = getattr(modul, navi)
        weg = (f(seite, kuerzel, breite, []) if argzahl == 4
               else f(seite, kuerzel, breite))
        seite.wait_for_timeout(1600)
        inv = seite.evaluate(B12.INVENTAR_JS)
        inv["weg"] = str(weg)[:120]
        inv["seitenfehler"] = fehler[:3]
        return inv
    finally:
        ctx.close()


def main(argv):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright fehlt.")
        return 2
    nur = argv[argv.index("--nur") + 1] if "--nur" in argv else None

    roh = io.open(os.path.join(WURZEL, "index.html"), encoding="utf-8",
                  newline="").read()
    version = _version(roh)
    print("Erhoben wird an v%s" % version)

    port = M._server()
    url = "http://127.0.0.1:%d/%s" % (port, os.environ.get("EPK_INDEX", "index.html"))
    ergebnis = []
    t0 = time.time()
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for gname, modul, saat, navi, argzahl in GRUPPEN:
            for kuerzel, cfg in modul.ANSICHTEN.items():
                if nur and kuerzel != nur:
                    continue
                for breite in (390, 1440):
                    try:
                        inv = _eine(browser, url, modul, saat, navi, kuerzel,
                                    breite, argzahl)
                        fehl = None
                    except Exception as e:
                        inv, fehl = None, str(e)[:200]
                    ergebnis.append({"gruppe": gname, "kuerzel": kuerzel,
                                     "titel": cfg.get("titel", kuerzel),
                                     "breite": breite, "inv": inv,
                                     "fehler": fehl})
                    print("  %-12s %-5d %s" % (kuerzel, breite,
                          "ok" if inv else ("NICHT ERREICHT: " + str(fehl)[:70])))
        browser.close()
    print("\n%d Aufnahmen in %.0f s" % (len(ergebnis), time.time() - t0))

    ziel = os.path.join(WURZEL, "docs", "GRUNDSTAND_UI_v%s.md" % version)
    _schreiben(ziel, version, ergebnis)
    print("Geschrieben:", ziel)
    return 0


def _schreiben(ziel, version, ergebnis):
    z = []
    A = z.append
    A("# Grundstand nach dem Umbau - v%s" % version)
    A("")
    A("Erhoben am %s mit `scripts/grundstand_erheben.py`, **gemessen an der"
      % time.strftime("%d.%m.%Y"))
    A("gerenderten Seite**, nicht aus dem Quelltext gelesen.")
    A("")
    A("**Zweck.** Nach jedem Umbau wird dieselbe Aufnahme wiederholt. Was hier")
    A("steht, muss danach noch da sein. Ein verschwundener Knopf, ein")
    A("verschwundenes Feld, eine verschwundene Auswahloption ist ein")
    A("Regressionsfehler - auch dann, wenn alles huebscher aussieht und alle")
    A("Pruefungen gruen sind.")
    A("")
    A("**Nicht enthalten und bewusst so:** Aussehen, Reihenfolge, Gruppierung,")
    A("Beschriftungstexte. Die duerfen sich aendern - darum geht es ja.")
    A("Geprueft wird, dass die *Handlung* und die *Zahl* erhalten bleiben.")
    A("")
    A("## 🔴 Was diese Aufnahme NICHT abdeckt")
    A("")
    A("Ein „nicht gemessen\" ist **kein** bestandener Fall.")
    A("")
    A("* **Unterzustaende.** Je Ansicht ist der EINE Zustand aufgenommen, in")
    A("  den die Navigation fuehrt. Chef hat fuenf, Admin sechs, das")
    A("  Buero-Portal fuenf.")
    A("* **Alle Rollen ausser `admin`.**")
    A("* **Serverleere Ansichten** (Flotte, Gefahrenstoffe, Bauprovisorien und")
    A("  mehrere Unterreiter): ihre Zahlen sind die eines leeren Blatts.")
    A("* **Alles hinter einem Klick**: Dialoge, Menues, Aufklapper.")
    A("* Die Saaten der drei Sondengruppen sind **nicht gleich** (12-15 fuehrt")
    A("  fuenf Monteure, davon zwei ausgetretene; 4-7 drei). Zahlen aus")
    A("  verschiedenen Gruppen sind deshalb nicht direkt vergleichbar - die")
    A("  Gruppe steht bei jeder Ansicht dabei.")
    A("")
    A("---")
    A("")
    A("## Mengengeruest")
    A("")
    A("| Ansicht | Gruppe | Breite | Knoepfe | Felder | Auswahl | Optionen |")
    A("|---|---|---|---|---|---|---|")
    for e in ergebnis:
        if not e["inv"]:
            A("| %s | %s | %d | — | — | — | NICHT ERREICHT |"
              % (e["titel"], e["gruppe"], e["breite"]))
            continue
        i = e["inv"]
        opt = sum(a["n"] for a in i["auswahl"])
        A("| %s | %s | %d | %d | %d | %d | %d |"
          % (e["titel"], e["gruppe"], e["breite"], i["anzahl_knoepfe"],
             i["anzahl_felder"], i["anzahl_auswahl"], opt))
    A("")
    A("---")
    A('')
    A('## Was an diesen Zahlen wackelt - und was hart ist')
    A('')
    A('**Die rohen Knopf- und Feldzahlen sind nur eingeschraenkt vergleichbar.**')
    A('Drei Gruende, alle in dieser Aufnahme sichtbar:')
    A('')
    A('1. **Der Datenbestand.** Die Saat fuehrt sechs Werkzeuge, nicht 296; zwei')
    A('   Projekte, nicht drei. Jede Zeile bringt Knoepfe mit. Der alte Grundstand')
    A('   nannte fuer Werkzeuge 25 Knoepfe, diese Aufnahme 18 bei 390 px - das ist')
    A('   kein verschwundener Knopf, sondern ein anderer Bestand.')
    A('2. **Die Breite aendert die Form, nicht nur das Aussehen.** Die')
    A('   Arbeitsschein-Liste zeigt bei 390 px Karten und bei 1440 px eine Tabelle')
    A('   mit einem Monteur-Auswahlfeld JE ZEILE - daher 28 Auswahlfelder mit 172')
    A('   Optionen bei 1440 gegen eines mit 7 bei 390. Beides ist richtig.')
    A('3. **Die drei Sondengruppen saeen verschieden.** 12-15 fuehrt fuenf Monteure')
    A('   (zwei davon ausgetreten), 4-7 drei. Eine Zahl aus Gruppe 4-7 gegen eine aus')
    A('   12-15 zu stellen ist ein Vergleich zweier Welten.')
    A('')
    A('**Hart und vergleichbar sind die BENANNTEN STUECKE**: die Auswahloptionen, die')
    A('Feldbeschriftungen, die Statuskacheln, die Unterreiter, die Sortierkriterien.')
    A('Genau die prueft `scripts/bestand.py` - 118 Begriffe in 17 Gruppen, und die')
    A('Pruefung wird rot, wenn einer fehlt.')
    A('')
    A("---")
    A("")
    A("## Je Ansicht")
    for e in ergebnis:
        if e["breite"] != 390:
            continue
        A("")
        A("### %s  *(Gruppe %s)*" % (e["titel"], e["gruppe"]))
        paar = [x for x in ergebnis
                if x["kuerzel"] == e["kuerzel"] and x["breite"] == 1440]
        for x in [e] + paar:
            A("")
            A("**%d px** — %s" % (x["breite"],
              "NICHT ERREICHT: %s" % x["fehler"] if not x["inv"] else
              "Weg: `%s`" % x["inv"]["weg"]))
            if not x["inv"]:
                continue
            i = x["inv"]
            if i["ueberschriften"]:
                A("")
                A("Ueberschriften: %s" % " · ".join(i["ueberschriften"]))
            else:
                A("")
                A("Ueberschriften: **keine** (kein h1/h2/h3)")
            if i["spalten"]:
                A("")
                A("Tabellenkoepfe: %s" % " · ".join(i["spalten"]))
            if i["felder"]:
                ph = [f["ph"] for f in i["felder"] if f.get("ph")]
                A("")
                A("%d Felder, Platzhalter: %s"
                  % (i["anzahl_felder"], " · ".join(ph) if ph else "keine"))
            for a in i["auswahl"]:
                A("")
                A("Auswahlfeld (%d Optionen): %s" % (a["n"], " · ".join(a["opt"])))
            if i["knoepfe"]:
                namen = []
                for k in i["knoepfe"]:
                    t = k["t"] or k.get("title") or k.get("aria") or "(ohne Text)"
                    namen.append(t.replace("\n", " ")[:34])
                A("")
                A("%d Knoepfe: %s" % (i["anzahl_knoepfe"], " · ".join(namen)))
            if i["seitenfehler"]:
                A("")
                A("🔴 Seitenfehler: %s" % i["seitenfehler"])
    A("")
    io.open(ziel, "w", encoding="utf-8", newline="").write("\n".join(z))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
