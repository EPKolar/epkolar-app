# -*- coding: utf-8 -*-
"""Z1 / Z6 / B1: die AUFRUFER der drei Kuren.

Z1  ProjectShell.yr und VZeit.yr stehen jetzt auf isoWY() statt auf dem
    Kalenderjahr. Betroffen ist nicht die Zuweisung, sondern JEDE Stelle,
    die `yr` in diesen beiden Rumpfbereichen liest - und jedes Kind, das
    `yr` als Eigenschaft bekommt.

Z6  `if(_d>0)` ist weg; die Rechnung gilt jetzt immer, `_d<=0` bricht mit
    einer eigenen Meldung ab. Betroffen ist der Weg dahinter: was passiert
    bei einer NICHT-ZAHL als Pause (NaN<=0 ist FALSCH, der Abbruch greift
    dort also nicht)?

B1  Krankmeldungen ueber die Kennung. Betroffen ist jeder Aufrufer von
    MAAttesteSection: wer nur einen NAMEN uebergibt, sieht jetzt KEINE
    Zeile mehr, die eine Kennung traegt.

Alles ueber die Codemaske - die Kur-Kommentare zitieren die alten Formen.
"""
import re
import sys

from nebenwirkung_helfer import lies, codemaske, zeile_von


def bereich_ab(text, maske, marke, zeilen=420):
    """Von `marke` an die naechsten n Zeilen - bewusst ein AUSSCHNITT und
    nicht der Funktionsrumpf: die Klammerzaehlung traegt hier nicht
    (code_scan kennt keine Regex-Literale). Der Ausschnitt eines Riegels
    ist selbst die Luecke, darum wird die Laenge GENANNT."""
    a = text.index(marke)
    b = a
    for _ in range(zeilen):
        nb = text.find("\n", b + 1)
        if nb < 0:
            return a, len(text)
        b = nb
    return a, b


def main():
    text = lies()
    maske = codemaske(text)

    print("#### Z1 - wer liest `yr` in den beiden geaenderten Rumpfbereichen?")
    for marke, titel in [("function ProjectShell({p,onBack", "ProjectShell"),
                         ("function VZeit({p,entries,setEntries", "VZeit")]:
        a, b = bereich_ab(text, maske, marke, 400)
        print("  %s  Zeile %d..%d (AUSSCHNITT von 400 Zeilen, nicht der ganze Rumpf)"
              % (titel, zeile_von(text, a), zeile_von(text, b)))
        n = 0
        for x in re.finditer(r"\byr\b", text[a:b]):
            p = a + x.start()
            if not maske[p]:
                continue
            n += 1
            print("     Z%-7d ...%s..."
                  % (zeile_von(text, p),
                     " ".join(text[max(a, p - 55):p + 55].split())))
        print("     -> %d Lesestellen" % n)
    print("")

    print("#### Z6 - der Weg hinter der Kur, beide Stellen")
    for x in re.finditer(r"_wrapHrs\(_rVon,_rBis\)-addPause", text):
        p = x.start()
        if not maske[p]:
            continue
        z = zeile_von(text, p)
        # die naechsten 3 Zeilen zeigen, was die Kur nach sich zieht
        e = p
        for _ in range(3):
            e = text.find("\n", e + 1)
        print("  Z%d:" % z)
        print("     %s" % " ".join(text[p - 120:p + 620].split())[:600])
        print("")
    print("  addPause - woher kommt der Wert?")
    for x in re.finditer(r"addPause\s*[,)\]=]", text):
        p = x.start()
        if not maske[p]:
            continue
        s = " ".join(text[max(0, p - 90):p + 40].split())
        if "setAddPause" in s or "useState" in s:
            print("     Z%-7d %s" % (zeile_von(text, p), s[:150]))
    for x in re.finditer(r"setAddPause\(", text):
        p = x.start()
        if not maske[p]:
            continue
        print("     Z%-7d %s" % (zeile_von(text, p),
                                 " ".join(text[p:p + 130].split())))
    print("")

    print("#### B1 - die Aufrufer von MAAttesteSection")
    for x in re.finditer(r"MAAttesteSection", text):
        p = x.start()
        if not maske[p]:
            continue
        print("  Z%-7d %s" % (zeile_von(text, p),
                             " ".join(text[max(0, p - 60):p + 200].split())[:240]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
