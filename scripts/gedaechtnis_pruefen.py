# -*- coding: utf-8 -*-
"""Der Gedaechtnis-Index: passt er noch durch, und zeigt er auf alles?

🔴 DREI FEHLER, DIE AM 29.09.2026 ALLE AM SELBEN TAG AUFTRATEN:

1. **Der Index war ueber der Lesegrenze.** MEMORY.md ist die Datei, die zu
   Beginn JEDER Sitzung geladen wird. Wird sie zu gross, wird sie
   abgeschnitten oder gar nicht gelesen - und dann sind alle Regeln darin
   wirkungslos, ohne dass irgendwo etwas rot wird. Gemessen: 24.883 Bytes
   bei einer Grenze von 17.510.

2. **Zwei WAISEN an einem Tag.** `mlg_regel_marketing_immer_zweisprachig.md`
   und `mlg_regel_unschluessig_verbirgt.md` wurden von ANDEREN Sitzungen
   geschrieben, und ihr Zeiger landete nie im Index. Eine Erinnerung, auf die
   nichts zeigt, wird nie wieder gelesen - sie ist geschrieben und verloren.
   Das ist Frage 25 („MEMORY.md hat mehrere Schreiber und keine Sperre") in
   ihrer praktischen Form.

3. **Zeiger ins Leere** waeren die Gegenrichtung: ein Eintrag, dessen Datei
   nicht mehr da ist.

🔴 GEFUNDEN WURDEN BEIDE WAISEN NICHT DURCH NACHDENKEN, sondern durch eine
Zaehlung, die nicht auf null ging. Genau deshalb gehoert sie in ein Werkzeug
und nicht in einen Vorsatz.

WAS DIESES WERKZEUG NICHT TUT: kuerzen. Welcher Nachsatz entbehrlich ist, ist
eine Entscheidung ueber den Inhalt, und die faellt nicht ein Skript. Es sagt,
WIEVIEL zu viel ist und WELCHE Zeilen die laengsten sind.

Aufruf:  python scripts/gedaechtnis_pruefen.py
         python scripts/gedaechtnis_pruefen.py --haken   (Ausgabe als JSON)
"""
import io
import json
import os
import re
import sys


def _ins_sperrprotokoll(grund):
    """Schreibt eine Sperre ins gemeinsame Protokoll unter ~/.claude/hooks/.

    🔴 30.09.2026 — Punkt 3 des Regelwerk-Auftrags: „Das Sperrprotokoll zaehlt
       den ersten echten Stop-Stopp mit." Bis heute protokollierte KEIN Haken
       etwas; auf die Frage „wie oft hat er gegriffen" war die einzige ehrliche
       Antwort: unbekannt.

    🔴 FAELLT NIE AUS. Liegt das Protokoll nicht da (anderer Rechner, anderes
       Projekt), passiert nichts. Ein Haken, der wegen eines fehlenden
       Protokolls abstuerzt, sperrt beim naechsten Mal aus dem falschen Grund —
       und das waere schlimmer als ein ungezaehltes Ereignis.
    """
    try:
        ort = os.path.join(os.path.expanduser("~"), ".claude", "hooks")
        if ort not in sys.path:
            sys.path.insert(0, ort)
        from sperrprotokoll import notiere  # noqa: PLC0415
        notiere("gedaechtnis-index", "sperre", grund, "Stop")
    except Exception:
        pass


# Die Grenze, ab der der Index nicht mehr verlaesslich gelesen wird.
# 17,1 KB in der strengeren Lesart (1 KB = 1024 Bytes).
GRENZE = 17510
ZEIGER = re.compile(r"\]\(([^)]+\.md)\)")


def _ordner():
    """Der Gedaechtnisordner - oder None, wenn es ihn hier nicht gibt.

    🔴 Auf einer anderen Maschine gibt es ihn nicht. Dann meldet dieses
    Werkzeug „nicht anwendbar" und NICHT rot: ein Tor, das auf einer fremden
    Maschine grundlos rot wird, wird uebersprungen, und dann misst es nie
    wieder etwas.
    """
    p = os.path.expanduser(
        r"~\.claude\projects\C--Users-technik\memory")
    return p if os.path.isdir(p) else None


def pruefe(ordner):
    """Liste von (Kennung, Meldung). Leer heisst: in Ordnung."""
    index = os.path.join(ordner, "MEMORY.md")
    if not os.path.exists(index):
        return [("fehlt", "MEMORY.md gibt es nicht.")]
    s = io.open(index, encoding="utf-8", newline="").read()
    n = len(s.encode("utf-8"))
    befunde = []

    if n > GRENZE:
        zeilen = sorted(((len(z), z) for z in s.split("\n")), reverse=True)[:3]
        befunde.append((
            "groesse",
            "MEMORY.md ist %d Bytes gross, die Grenze liegt bei %d "
            "(%+d).\nDer Index wird zu Beginn JEDER Sitzung geladen - wird "
            "er abgeschnitten, sind\nalle Regeln darin wirkungslos, ohne "
            "dass irgendwo etwas rot wird.\nDie drei laengsten Zeilen:\n%s"
            % (n, GRENZE, n - GRENZE,
               "\n".join("   %4d  %s..." % (ln, z[:70]) for ln, z in zeilen))))

    verlinkt = set(ZEIGER.findall(s))
    archiv = os.path.join(ordner, "archiv_aeltere_etappen.md")
    if os.path.exists(archiv):
        verlinkt |= set(ZEIGER.findall(
            io.open(archiv, encoding="utf-8", newline="").read()))
    alle = {f for f in os.listdir(ordner)
            if f.endswith(".md") and f != "MEMORY.md"}

    waisen = sorted(alle - verlinkt)
    if waisen:
        befunde.append((
            "waisen",
            "%d Erinnerungen, auf die NICHTS zeigt:\n%s\n"
            "Eine Erinnerung ohne Zeiger wird nie wieder gelesen - sie ist "
            "geschrieben und\nverloren. Am 29.09. waren es zwei an einem "
            "Tag, beide von anderen Sitzungen."
            % (len(waisen), "\n".join("   " + w for w in waisen))))

    tot = sorted(z for z in verlinkt
                 if not os.path.exists(os.path.join(ordner, z)))
    if tot:
        befunde.append((
            "tote_zeiger",
            "%d Zeiger gehen ins Leere:\n%s"
            % (len(tot), "\n".join("   " + t for t in tot))))
    return befunde


# ── Selbstprobe ──────────────────────────────────────────────────────────
# 🔴 Ohne sie waere „keine Waisen" von „der Sucher greift daneben" nicht zu
#    unterscheiden. Gebaut wird ein kleiner Ordner mit bekannten Antworten.
def eichen():
    import shutil
    import tempfile
    schief = []
    tmp = tempfile.mkdtemp(prefix="gedprobe_")
    try:
        def schreib(name, text):
            io.open(os.path.join(tmp, name), "w", encoding="utf-8",
                    newline="").write(text)

        # Fall 1: alles in Ordnung.
        schreib("MEMORY.md", "- [A](a.md)\n- [B](b.md)\n")
        schreib("a.md", "a")
        schreib("b.md", "b")
        if pruefe(tmp):
            schief.append("Ein sauberer Ordner wird beanstandet: %r"
                          % pruefe(tmp))

        # Fall 2: eine Waise.
        schreib("c.md", "c")
        arten = [a for a, _m in pruefe(tmp)]
        if "waisen" not in arten:
            schief.append("Eine Waise wird nicht gefunden (gefunden: %s)."
                          % arten)

        # Fall 3: ein toter Zeiger.
        schreib("MEMORY.md", "- [A](a.md)\n- [B](b.md)\n- [C](c.md)\n"
                             "- [Weg](gibtsnicht.md)\n")
        arten = [a for a, _m in pruefe(tmp)]
        if "tote_zeiger" not in arten:
            schief.append("Ein toter Zeiger wird nicht gefunden "
                          "(gefunden: %s)." % arten)
        if "waisen" in arten:
            schief.append("Nach dem Eintragen gilt c.md weiter als Waise - "
                          "der Sucher liest den\n     Index nicht richtig.")

        # Fall 4: zu gross.
        schreib("MEMORY.md", "- [A](a.md)\n- [B](b.md)\n- [C](c.md)\n"
                             + "x" * (GRENZE + 10))
        if "groesse" not in [a for a, _m in pruefe(tmp)]:
            schief.append("Eine zu grosse Datei wird nicht beanstandet.")

        # Gegenprobe: das Archiv zaehlt als Zeiger.
        schreib("MEMORY.md", "- [A](a.md)\n- [Archiv](archiv_aeltere_"
                             "etappen.md)\n")
        schreib("archiv_aeltere_etappen.md", "- [B](b.md)\n- [C](c.md)\n")
        arten = [a for a, _m in pruefe(tmp)]
        if "waisen" in arten:
            schief.append("Eine nur im ARCHIV verlinkte Datei gilt als "
                          "Waise. Dann meldet das\n     Werkzeug 60 "
                          "Fehlalarme und wird nicht mehr gelesen.")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return schief


def main(argv):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    # 🔴 30.09.2026 — STDERR FEHLTE HIER, UND GENAU DORT STEHT JETZT DIE
    #    SPERRBEGRUENDUNG. Gemessen beim ersten Koederlauf: die Meldung kam als
    #    `\U0001f534 GEDAECHTNIS-INDEX ...` heraus statt mit dem roten Punkt —
    #    Pythons Vorgabe fuer stderr ist `backslashreplace`, und die Windows-
    #    Konsole (cp1252) kann das Zeichen nicht. Eine Sperrbegruendung, die
    #    als Zeichenfolge-Muell ankommt, wird nicht gelesen.
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    haken = "--haken" in argv

    schief = eichen()
    if schief:
        if not haken:
            print("Eichung: 5 Proben")
            for s in schief:
                print("   \U0001F534 " + s)
            print("\nNICHT GEMESSEN.")
        else:
            # 🔴 30.09.2026 — DIE SPERRE WAR STUMM.
            #    Bis heute war dieser Haken als `... 2>/dev/null || true`
            #    registriert: `|| true` machte den Ausgang 2 WIRKUNGSLOS, der
            #    Haken konnte also gar nicht sperren. Nach dem Entfernen sperrt
            #    er wirklich — und dann muss dabeistehen, WARUM, sonst endet ein
            #    Zug ohne Begruendung und der Naechste sucht im Dunkeln.
            #    Gemessen am 30.09.: Koeder mit verbogener Eichung -> Ausgang 2,
            #    und KEINE Zeile Ausgabe. Das ist hiermit behoben.
            sys.stderr.write(
                "\U0001F534 GEDAECHTNIS-INDEX: NICHT GEMESSEN - der Pruefer "
                "ist nicht geeicht.\n"
                + "".join("   - " + s + "\n" for s in schief)
                + "Angehalten wird, WEIL die Pruefung selbst nicht traegt. Das "
                "ist kein Befund am Gedaechtnis, sondern einer am Werkzeug:\n"
                "nicht gemessen ist nicht bestanden.\n"
                "Nachsehen mit:  python scripts/gedaechtnis_pruefen.py\n")
            _ins_sperrprotokoll("Eichung gescheitert: "
                                + "; ".join(schief)[:200])
        return 2

    ordner = _ordner()
    if ordner is None:
        if not haken:
            print("Kein Gedaechtnisordner auf dieser Maschine - nicht "
                  "anwendbar.")
        return 0

    befunde = pruefe(ordner)
    if haken:
        if befunde:
            kurz = "; ".join(m.split("\n")[0] for _a, m in befunde)
            sys.stdout.write(json.dumps(
                {"systemMessage": "Gedaechtnis-Index: " + kurz},
                ensure_ascii=True) + "\n")
        return 0

    print("Eichung: 5 Proben  \U0001F7E2")
    if not befunde:
        print("\U0001F7E2 Der Index passt durch, jede Erinnerung hat einen "
              "Zeiger, kein Zeiger\n   geht ins Leere.")
        return 0
    print("\n\U0001F534 %d Befunde:" % len(befunde))
    for _a, m in befunde:
        print("\n" + m)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
