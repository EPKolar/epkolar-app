# -*- coding: utf-8 -*-
"""B3: das Mengengeruest der vier Ansichten aus dem QUELLTEXT, gegen den
Grundstand.

WOZU
────
`scripts/b3_vier_ansichten_messen.py` zaehlt, was am Schirm STEHT. Diese Zahl
haengt am Datenbestand: sechs gesaete Arbeitsscheine ergeben sechs
Aktionsknopfsaetze, 296 echte ergeben 296. Der Bestandsschutz braucht daneben
eine Zahl, die NICHT am Datenbestand haengt - die Menge der HANDLUNGEN,
Felder, Auswahloptionen und Beschriftungen im Quelltext der Komponente.

Diese Sonde ist die Klammer um `scripts/ansicht_inventar.py`: sie liest die
Datei aus EPK_INDEX (statt fest index.html), fasst die vier Ansichten
zusammen, schreibt einen Vergleichsstand und meldet die Schriftgroessen, die
im Quelltext unter 12 liegen - und zwar nur die, die im CODE stehen, nicht die
in Kommentaren oder Zeichenketten.

WAS GEMESSEN WIRD
─────────────────
  handler     onClick/onChange/onSubmit/onInput - die HANDLUNGEN
  felder      input / select / textarea
  optionen    <option value=...>
  platzhalter placeholder-Texte
  emoji       Emoji im Rumpf
  groessen    fontSize-Zahlen im Rumpf
  fontSize<12 jede Stelle mit einem Wert unter 12, die im CODE steht - in
              BEIDEN Schreibweisen: fest (`fontSize:9`) und bedingt
              (`fontSize:isMob?7:9`). Die bedingte Form ist der Grund, warum
              diese Sonde einen zweiten Lauf brauchte: mit ihr kommt der
              kleinste Wert der App ueberhaupt erst ins Bild (7 px).

WAS NICHT GEMESSEN WIRD
───────────────────────
  * Was am Schirm ANKOMMT. Eine fontSize:10 im Quelltext kann von einer
    CSS-Regel geschlagen werden und umgekehrt - deshalb gibt es die
    Schirm-Sonde daneben. Diese hier ist die Landkarte, nicht das Gelaende.
  * Rollen-Gatter: ein Rumpf enthaelt alle Zweige, auch die, die ein Monteur
    nie sieht.
  * Groessen, die nicht als `fontSize:<zahl>` geschrieben sind (Variablen wie
    `UI.fMeta`, Vorlagenliterale, CSS-Klassen).

DIE KOEDER
──────────
  K1  Ein selbst gebauter Rumpf mit EINEM Handler, EINEM input, EINER option,
      EINEM placeholder, EINER fontSize:9 und EINER fontSize:isMob?7:9 muss
      in allen fuenf Mengen
      genau diesen Fall zeigen. Findet das Inventar dort nichts, zaehlt es
      auch in den echten Rumpfen nichts.
  K2  Aus dem ECHTEN Rumpf wird ein bekannter Handler entfernt; die
      Handlerzahl MUSS um mindestens eins sinken. Ein Zaehler, der beim
      eigenen Ausfall dieselbe Zahl nennt, ist wertlos.
  K3  code_scan.eichen() muss bestehen, sonst wird keine Zahl genannt (das
      Modul verweigert von selbst).

AUFRUF
──────
    set EPK_INDEX=_mess_stand_939.html
    python scripts/b3_bestand_quelltext.py
    python scripts/b3_bestand_quelltext.py --json quelltext.json
"""
import io
import json
import os
import re
import sys

for _strom in (sys.stdout, sys.stderr):
    try:
        _strom.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
sys.path.insert(0, HIER)
sys.path.insert(0, os.path.join(WURZEL, "tests"))

import ansicht_inventar as AI        # noqa: E402
import code_scan as CS               # noqa: E402
from conftest import _extract_fn     # noqa: E402

# Die vier Ansichten des Auftrags und die Komponente, die sie tragen.
ANSICHTEN = [
    ("Werkzeuge", "WerkzeugView"),
    ("Planung / Wochenplanung", "WeekPlan"),
    ("Home / Startseite", "HomeView"),
    ("Arbeitsschein bearbeiten", "ArbeitsscheinView"),
]

# K1: der gebaute Fall. Jede der fuenf Mengen hat hier genau einen Eintrag.
KOEDER_RUMPF = (
    "React.createElement('button', { onClick: koederHandlerXY, "
    "style: {fontSize:9}}, \"Koedertext sichtbar\")\n"
    "React.createElement('input', { placeholder: \"Koeder Platzhalter\"})\n"
    "React.createElement('select', {}, React.createElement('option', "
    "{ value: koederOptionXY}, \"Koeder Option\"))\n"
    "React.createElement('textarea', {})\n"
    # Die BEDINGTE Groessenangabe - der Fall, den die erste Fassung des
    # Groessenzaehlers durchliess.
    "React.createElement('div', { style: {fontSize:isMob?7:9}}, "
    "\"Koeder bedingte Groesse\")\n"
)


def _datei():
    name = os.environ.get("EPK_INDEX", "index.html")
    pfad = os.path.join(WURZEL, name)
    return name, io.open(pfad, encoding="utf-8", newline="").read()


# ZWEI FORMEN, und die erste Fassung kannte nur eine.
# `fontSize:\s*(\d+)` findet `fontSize:9`. Es findet NICHT
# `fontSize:isMob?7:9` - und genau in dieser Form steht der kleinste Wert der
# ganzen App: die Wetterzeile auf Home traegt am Telefon SIEBEN Pixel. Der
# Schirm hat sie gemeldet, dieser Quelltext-Zaehler nicht; die ersten Zahlen
# (47/53/61/54 Stellen) waren damit UNTERGEZAEHLT. Jetzt beide Formen, und die
# bedingte wird als solche gekennzeichnet - bei ihr haengt der Wert von der
# Breite ab, was fuer eine Zwei-Breiten-Messung genau der interessante Fall ist.
FS_EINFACH = re.compile(r"fontSize:\s*(\d+(?:\.\d+)?)\s*[,}]")
FS_BEDINGT = re.compile(
    r"fontSize:\s*([A-Za-z_][\w.]*)\s*\?\s*(\d+(?:\.\d+)?)\s*:\s*(\d+(?:\.\d+)?)")


def _fontsize_klein(rumpf, feld_versatz, feld):
    """fontSize-Werte unter 12 - nur wo sie im CODE stehen.

    feld/feld_versatz beziehen sich auf die GANZE Datei: der Rumpf ist ein
    Ausschnitt, die Eichung von code_scan laeuft ueber das Ganze.
    """
    out = []

    def nimm(m, px, form, bedingung=None):
        pos = feld_versatz + m.start()
        out.append({"px": px, "form": form, "bedingung": bedingung,
                    "im_code": bool(feld[pos]),
                    "umgebung": rumpf[max(0, m.start() - 70):
                                      m.start() + 46].replace("\r\n", " ")})

    for m in FS_EINFACH.finditer(rumpf):
        n = float(m.group(1))
        if n < 12:
            nimm(m, n, "fest")
    for m in FS_BEDINGT.finditer(rumpf):
        a, b = float(m.group(2)), float(m.group(3))
        if min(a, b) < 12:
            nimm(m, min(a, b), "bedingt (%s ? %s : %s)"
                 % (m.group(1), m.group(2), m.group(3)), m.group(1))
    out.sort(key=lambda x: x["px"])
    return out


def main(argv):
    name, text = _datei()
    import hashlib
    h = hashlib.md5(io.open(os.path.join(WURZEL, name), "rb").read()).hexdigest()
    print("Gemessen: %s   md5 %s" % (name, h))

    # K3: die Eichung von code_scan. Sie verweigert von selbst, wenn sie
    # scheitert - hier wird sie nur benannt, damit im Bericht steht, dass sie
    # gelaufen ist.
    ok, gef, erw = CS.eichen(text)
    print("K3 code_scan-Eichung: %s (%d von %d isMob-Deklarationen als Code)"
          % ("BESTANDEN" if ok else "GESCHEITERT", gef, erw))
    if not ok:
        print("Keine Zahl - ein Abtaster, der zu wenig findet, meldet gruen.")
        return 1
    feld = CS.ist_code(text)

    # K1
    k = AI.inventar(KOEDER_RUMPF)
    # Der Groessenzaehler wird am gebauten Fall MIT gepruefet: er muss die
    # feste 9 UND die bedingte 7 finden.
    k_gr = _fontsize_klein(KOEDER_RUMPF, 0, bytearray(b"\x01" * len(KOEDER_RUMPF)))
    k_px = sorted(x["px"] for x in k_gr)
    k_ok = (len(k["handler"]) >= 1 and "input" in k["felder"]
            and len(k["optionen"]) >= 1 and len(k["platzhalter"]) >= 1
            and 9 in k["groessen"] and 7.0 in k_px and 9.0 in k_px)
    print("K1 Inventar am gebauten Fall: %s "
          "(handler %d, felder %s, optionen %d, platzhalter %d, groessen %s, "
          "Groessenzaehler fand %s)"
          % ("ANGESCHLAGEN" if k_ok else "STUMM", len(k["handler"]),
             k["felder"], len(k["optionen"]), len(k["platzhalter"]),
             k["groessen"], k_px))
    if not k_ok:
        print("Das Inventar findet im gebauten Fall nicht, was drinsteht - "
              "jede Zahl darunter waere wertlos.")
        return 1

    bericht = {"datei": name, "md5": h, "ansichten": {}}
    schlimm = 0
    for titel, komp in ANSICHTEN:
        rumpf = _extract_fn(text, komp)
        if not rumpf:
            print("\n%s (%s): KOMPONENTE NICHT GEFUNDEN - das ist rot."
                  % (titel, komp))
            schlimm += 1
            continue
        versatz = text.find(rumpf)
        d = AI.inventar(rumpf)

        # K2: einen bekannten Handler herausnehmen, die Zahl MUSS sinken.
        #
        # ERSTE FASSUNG WAR ZU GROB und wurde bei WeekPlan zu Recht stumm:
        # sie schnitt den ERSTEN Handler-Treffer heraus. `inventar()` zaehlt
        # aber ueber eine MENGE - derselbe Ausdruck kommt in einer Tabelle
        # dutzendfach vor, und nach dem Entfernen EINES Vorkommens stand die
        # Zahl unveraendert bei 38. Der Koeder muss deshalb ALLE Vorkommen
        # EINES Handlers treffen, und die Zahl muss um genau eins sinken.
        vorher = len(d["handler"])
        nachher, ziel = vorher, None
        for kandidat in d["handler"]:
            geputzt = re.sub(
                r"on(?:Click|Change|Submit|Input)\s*:\s*" + re.escape(kandidat),
                "onNixDa: _koeder", rumpf)
            if geputzt == rumpf:
                continue
            n = len(AI.inventar(geputzt)["handler"])
            if n < vorher:
                nachher, ziel = n, kandidat
                break
        k2 = ziel is not None and nachher < vorher
        klein = _fontsize_klein(rumpf, versatz, feld)
        im_code = [x for x in klein if x["im_code"]]

        print("\n%s  (%s, %d Zeichen Rumpf)" % (titel, komp, len(rumpf)))
        print("   K2 Handler-Zaehler: %s (%d -> %d nach Entnahme ALLER "
              "Vorkommen von %r)" % ("ANGESCHLAGEN" if k2 else "STUMM",
                                     vorher, nachher, (ziel or "")[:40]))
        if not k2:
            schlimm += 1
        print("   handler %3d | felder %-28s | optionen %3d | platzhalter %3d"
              % (len(d["handler"]), ",".join(d["felder"]) or "-",
                 len(d["optionen"]), len(d["platzhalter"])))
        print("   groessen (fontSize-Zahlen im Rumpf): %s"
              % ", ".join(str(x) for x in d["groessen"]))
        print("   fontSize < 12: %d Stellen, davon im CODE %d "
              "(die anderen stehen in Kommentar/Zeichenkette)"
              % (len(klein), len(im_code)))
        for x in im_code[:16]:
            print("      %4s px  %-26s ... %s"
                  % (x["px"], x["form"], x["umgebung"][-78:]))
        print("   aria-label im Rumpf: %d" % len(d["ariaLabel"]))
        print("   Emoji im Rumpf: %d verschiedene" % len(d["emoji"]))

        bericht["ansichten"][komp] = {
            "titel": titel, "rumpf_zeichen": len(rumpf),
            "koeder_handler_sinkt": k2,
            "handler": d["handler"], "felder": d["felder"],
            "optionen": d["optionen"], "platzhalter": d["platzhalter"],
            "groessen": d["groessen"], "ariaLabel": d["ariaLabel"],
            "emoji": d["emoji"],
            "fontsize_klein_im_code": im_code,
            "fontsize_klein_gesamt": len(klein),
            "texte_anzahl": len(d["texte"]),
        }

    if "--json" in argv:
        ziel = argv[argv.index("--json") + 1]
        io.open(ziel, "w", encoding="utf-8", newline="\n").write(
            json.dumps(bericht, indent=1, ensure_ascii=False, sort_keys=True))
        print("\nJSON: %s" % ziel)

    print("\n" + "=" * 70)
    for komp, d in bericht["ansichten"].items():
        print("  %-18s handler %3d  felder %-22s optionen %3d  "
              "fontSize<12 im Code %2d"
              % (komp, len(d["handler"]), ",".join(d["felder"]) or "-",
                 len(d["optionen"]), len(d["fontsize_klein_im_code"])))
    if schlimm:
        print("\n%d Selbstproben gescheitert - die Zahlen darueber sind "
              "NICHT belastbar." % schlimm)
        return 1
    print("\nAlle Selbstproben bestanden (K1 gebauter Fall, K2 je Ansicht, "
          "K3 code_scan-Eichung).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
