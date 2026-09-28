# -*- coding: utf-8 -*-
"""Die zu kleinen Bedienelemente aus der Messung vom 28.09.2026 bleiben gehoben.

🔴 DIESER RIEGEL SICHERT ZWEI MESSUNGEN, DIE ES VORHER NICHT GAB.

**Die erste Dialogmessung.** Jeder Grundstand seit Wochen endete mit dem Satz
„keine geoeffneten Dialoge". `scripts/dialog_messen.py` hat die vier
Ueberlagerungen der Huelle zum ersten Mal von innen gemessen - Suchpalette,
Benachrichtigungen, Sync-Fenster, Foto-Warteschlange. Keine Schrift unter
12 px, kein namenloser Knopf, und genau zwei Elemente unter 24 px:

    Suchpalette   ESC  42x22   (padding 4px 10px bei 12 px Schrift)
    Sync-Fenster  ✕    23x24   (padding 0 4px, minHeight ausdruecklich 0)

Beim Heben kam ein DRITTER dazu, den die Messung nicht gesehen hatte: der
Schliesser der Foto-Warteschlange ist zeichengleich mit dem des Sync-Fensters.
Der Anker traf zweimal, `safe_edit` verweigerte den Schnitt und nannte beide
Zeilen. Ohne diese Weigerung waere die Haelfte des Mangels stehen geblieben.

**Die Tippziele unter 24 px.** `scripts/echtmengen_messen.py` (44 Aufnahmen,
390 und 1440 px) fand 50 Bedienelemente unter 24 px, alle bei 1440 px, in
sechs Gruppen. Fuenf davon sind in v3.9.976 gehoben; die sechste ist der
Leaflet-Hinweis der Kartenansicht und gehoert uns nicht (siehe unten).

🔴 UND HIER STAND EINE SPERRE, DIE ICH WIEDER ENTFERNT HABE - der Grund ist
wichtiger als die Sperre. Meine erste Fassung verlangte, die Hausform
`minHeight:isMob?40:0` duerfe nirgends mehr vorkommen. Zwei Fehler auf einmal:

  1. Ich hatte ZWEI Knoepfe gemessen und ueber alle geurteilt. Die Form stand
     nicht zweimal da, sondern 23 mal.
  2. Dann hielt ich 23 fuer die Grundgesamtheit - bis beim Suchen nach einem
     anderen Knopf `isMob?44:0` auftauchte. Ueber alle Formen gezaehlt: 110
     Vorkommen in 17 Schreibweisen. Mein Riegel hatte 87 davon nicht gesehen
     und dabei ausgesehen, als haette er die Datei vermessen.

Und die Messung sagt: die Form ist gar nicht der Mangel. Die allermeisten
dieser 110 Stellen sind gross genug, weil Inhalt und Polsterung sie tragen.
Der Mangel ist die GERENDERTE Groesse - die sieht nur der Browser. Das
Verzeichnis der Hausform fuehrt jetzt `scripts/hausform_mindestmass.py`, mit
Koeder je Schreibweise, und es faellt ausdruecklich KEIN Urteil.

🔴 WAS DIESER RIEGEL MISST UND WAS NICHT. Er prueft NUR DEN QUELLTEXT: dass
die gehobenen Masse dastehen. Er sieht NICHT, wie gross ein Knopf am Schirm
wirklich ist - eine CSS-Regel mit !important koennte ihn jederzeit wieder
zusammendruecken, wie bei den Schriftgroessen in v3.9.965/966. Die WIRKUNG
messen:

    python scripts/dialog_messen.py          -> 4 Ueberlagerungen, je 0/0/0
    python scripts/echtmengen_messen.py      -> 44 Aufnahmen

Berichte: `docs/befunde/DIALOG_MESSUNG.json`, `docs/befunde/DIALOGE.md`,
`docs/befunde/UNTER24.md`.

🔴 GESUCHT WIRD AN CODE-STELLEN, NICHT IM ROHEN DATEITEXT. Die gehobenen
Formen stehen in diesem Riegel und in der Aenderungsgeschichte ausgeschrieben
da. Wer rohen Dateitext durchsucht, misst seine eigene Begruendung mit - der
Fehler, der mir bis zum 27.09. viermal passiert ist.
"""
import io
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HIER, "..", "scripts"))

import code_scan  # noqa: E402

PFAD = os.path.join(HIER, "..", "index.html")

# ─────────────────────────────────────────────────────────────────────────────
# Die gehobenen Stellen, je Gruppe eine Zeile:
#   (Muster, Name, erwartete Anzahl, was vorher gemessen wurde)
# Die Anzahl ist festgeschrieben, damit ein Umbau, der den Knopf ERSETZT statt
# ihn zu verkleinern, nicht still durchgeht.
# ─────────────────────────────────────────────────────────────────────────────
GEHOBEN = [
    ('minHeight:isMob?40:24,minWidth:isMob?0:24', 2,
     "Schliesser von Sync-Fenster und Foto-Warteschlange", "je 23x24"),
    ('fontWeight:600,minHeight:24}}, "ESC")', 1,
     "ESC-Knopf der Suchpalette", "42x22"),
    ("flexShrink:0,minHeight:28,minWidth:24,lineHeight:1", 1,
     "Favoritenstern in der Fahrzeugliste", "23x32"),
    ("padding:4,minWidth:24,zIndex:2", 1,
     "Favoritenstern auf der Fahrzeugkarte", "23x32"),
    ('display:"inline-flex",alignItems:"center",justifyContent:"center",'
     'minWidth:24,minHeight:24', 2,
     "Zeiterfassung: Eintrag bearbeiten und loeschen", "24.5x22 und 17.8x22"),
    ('padding:"3px 8px",minHeight:24,borderRadius:4', 1,
     "Tagesknoepfe des Stundenzettel-Exports", "rund 68x22"),
    ("width:36,height:24,borderRadius:12", 1,
     "Diagramm-Schalter der Auswertungen", "36x20"),
    ('width:20,height:20,borderRadius:"50%",background:"#fff",'
     'position:"absolute",top:2,left:visible?14:2', 1,
     "Knauf des Diagramm-Schalters (waechst mit der Huelle)",
     "16x16 bei 20 px Huelle"),
]

# ─────────────────────────────────────────────────────────────────────────────
# 🔴 ZWEI STELLEN LIEGEN AUSSERHALB DESSEN, WAS `ist_code` ALS CODE FUEHRT -
#    und das ist kein Mangel des Werkzeugs, sondern die Bauweise der Datei.
#    Die zweite Kaestchenregel steht in einem TEMPLATE-LITERAL (sie enthaelt
#    `${V.ac}`), die Kartenbibliothek in einer URL. Beides ist fuer eine
#    Zustandsmaschine eine Zeichenkette, kein Code.
#    Fuer sie wird im ROHEN Text gesucht, mit dem Risiko, das dieser Riegel
#    sonst gerade vermeidet: ein Kommentar, der die Zeichenfolge zitiert,
#    wuerde mitzaehlen. Deshalb sind die Anker so gewaehlt, dass sie in
#    Prosa nicht vorkommen koennen - `${V.ac}` und ein vollstaendiger
#    CDN-Pfad -, und der Gegenwert (die alte 22er-Regel) wird ausdruecklich
#    als ABWESEND geprueft.
ROH = [
    ('input[type="checkbox"]{width:24px;height:24px;accent-color:${V.ac}', 1,
     "zweite Kaestchenregel, im Template-Literal statt im <style>-Block",
     "22x22"),
]
ROH_VERBOTEN = [
    ('input[type="checkbox"]{width:22px;height:22px',
     "Die alte 22er-Kaestchenregel ist zurueck. Sie steht SPAETER im Dokument "
     "als die\n  24er-Regel aus v3.9.974 und gewinnt gegen sie - genau "
     "deshalb blieb das Kaestchen\n  in der Werkzeugansicht bei 22 px, "
     "obwohl der Quelltextriegel gruen war."),
]


def _text():
    return io.open(PFAD, encoding="utf-8", newline="").read()


def _treffer_im_code(text, muster):
    """Vorkommen von `muster`, gezaehlt NUR an Code-Stellen."""
    ist = code_scan.ist_code(text)
    aus, i = [], text.find(muster)
    while i >= 0:
        if ist[i]:
            aus.append(i)
        i = text.find(muster, i + 1)
    return aus


def test_koeder_der_sucher_findet_ueberhaupt_etwas():
    """🔴 SELBSTPROBE: ohne sie ist jede Zahl dieses Riegels wertlos.

    Ein Sucher, der die Form gar nicht kennt, meldet „kommt nicht vor" - und
    das ist von einem echten Befund nicht zu unterscheiden. Geprueft wird mit
    JEDEM der neun Muster, nicht mit einem stellvertretenden.
    """
    for muster, _, name, _vorher in GEHOBEN:
        kuenstlich = "var a = {" + muster + "};"
        assert _treffer_im_code(kuenstlich, muster), (
            "Der Sucher findet das Muster fuer %r nicht einmal in einem Text, "
            "der nur aus ihm besteht." % name)


def test_gegenprobe_im_kommentar_zaehlt_nicht():
    """Dieselbe Form im Kommentar darf NICHT zaehlen - sonst misst der Riegel
    seine eigene Begruendung mit."""
    muster = GEHOBEN[0][0]
    kuenstlich = "/* frueher stand hier " + muster + " */\nvar y = 1;"
    assert not _treffer_im_code(kuenstlich, muster), (
        "Der Sucher zaehlt ein Vorkommen im KOMMENTAR mit. Dann wird er "
        "gruen, sobald jemand die Hebung nur BESCHREIBT.")


def test_alle_gehobenen_masse_stehen_noch_da():
    """Neun Stellen, neun feste Anzahlen.

    🔴 ANWESENHEIT, und der Riegel sagt das auch: er belegt nicht, dass die
    Knoepfe am Schirm 24 px gross sind, sondern nur, dass die Angabe dasteht.
    Die Wirkung messen `dialog_messen.py` und `echtmengen_messen.py`.
    """
    t = _text()
    fehler = []
    for muster, erwartet, name, vorher in GEHOBEN:
        n = len(_treffer_im_code(t, muster))
        if n != erwartet:
            fehler.append("   %-58s %d statt %d  (gemessen war: %s)"
                          % (name, n, erwartet, vorher))
    assert not fehler, (
        "Gehobene Masse fehlen oder sind vervielfacht:\n%s\n"
        "Entweder ist der Knopf umgebaut worden - dann gehoert die Zahl hier "
        "angepasst UND die Wirkung neu gemessen - oder die Hebung ist "
        "verloren gegangen." % "\n".join(fehler))


def test_die_zweite_kaestchenregel_steht_auf_24():
    """Die Regel, die im Template-Literal steht und den <style>-Block schlaegt.

    🔴 SIE WAR DIE QUELLE, DIE ICH ZWEIMAL VERGEBLICH GESUCHT HABE. v3.9.974
    hob `input[type="checkbox"]` im <style>-Block von 20 auf 24 px, und das
    Kaestchen der Werkzeugansicht blieb trotzdem bei 22x22. Der Grund: eine
    ZWEITE Regel derselben Spezifitaet, spaeter im Dokument, in einem
    JavaScript-Template-Literal. Wer nur den <style>-Block liest, findet sie
    nie - und meldet „die Regel steht auf 24", waehrend das Kaestchen 22 ist.
    """
    t = _text()
    for muster, erwartet, name, vorher in ROH:
        n = t.count(muster)
        assert n == erwartet, (
            "%s: %d statt %d Vorkommen (gemessen war: %s)."
            % (name, n, erwartet, vorher))
    for muster, warum in ROH_VERBOTEN:
        assert muster not in t, warum


def test_der_leaflet_hinweis_ist_ausgenommen_UND_BEGRUENDET():
    """🔴 Die eine Gruppe, die NICHT gehoben wurde - mit Namen und Grund.

    Bei 390 UND 1440 px steht in der Flottenansicht ein Verweis von 51.4x14 px:
    der Urheberhinweis der Kartenbibliothek Leaflet
    (`div.leaflet-control-attribution > a`). Er gehoert nicht zu dieser App,
    seine Darstellung ist Teil der Lizenzbedingung der Kartendaten, und ihn zu
    vergroessern hiesse, in eine fremde Komponente hineinzugreifen.

    Eine Ausnahme ohne Messdatum und ohne Namen ist eine Attrappe - deshalb
    steht sie hier als PRUEFUNG und nicht als Satz in einem Kommentar: die
    Bibliothek muss ueberhaupt eingebunden sein, sonst ist die Ausnahme
    gegenstandslos und gehoert geloescht.
    """
    t = _text()
    assert "cdnjs.cloudflare.com/ajax/libs/leaflet/" in t, (
        "Leaflet ist nicht mehr eingebunden. Dann ist die Ausnahme fuer den "
        "Urheberhinweis gegenstandslos - sie gehoert aus diesem Riegel und "
        "aus `docs/befunde/UNTER24.md` entfernt, statt stehen zu bleiben und "
        "eine Luecke zu begruenden, die es nicht mehr gibt.")
