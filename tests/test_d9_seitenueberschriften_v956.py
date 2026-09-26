# -*- coding: utf-8 -*-
"""v3.9.956 - D9: Seitenueberschriften, und wo bewusst keine steht.

WARUM ES DIESE DATEI GIBT
─────────────────────────
Der Schluss-Grundstand an v3.9.954 hat 22 Ansichten bei je zwei Breiten
aufgenommen. FUENF lieferten `ueberschriften: []` - keine einzige h1/h2/h3.
Fuer eine Vorlesehilfe ist das eine Seite ohne Gliederung.

Der urspruengliche Befund D9 nannte nur DREI (Zeiterfassung, Flotte,
Bauprovisorien), weil er die dreizehn Ansichten der Stufen 12-15 gemessen
hatte. Ueber alle 22 gemessen kommen Wochenplanung und Startseite dazu. Das
steht hier, weil es die Art Fehler ist, die dieser Lauf immer wieder
produziert hat: ein Schluss aus einer Menge, die den Fall nicht enthaelt.

DIE DREITEILUNG, UND WAS SIE GEMESSEN ERGIBT
────────────────────────────────────────────
(a) Ueberschrift fertig, nur im falschen Element  -> umbauen, kostet kein Pixel
(b) oberster Panel-Titel MIT TEXT vorhanden       -> zur Seitenueberschrift heben
(c) kein geeigneter Text vorhanden                -> NICHTS erfinden

  Bauprovisorien   (a)  "🚧 Bauprovisorien" stand in einem div, fontSize 20,
                        fontWeight 800, als erstes Kind des Baums. Jetzt h2
                        mit margin:0. Gebaut.
  Wochenplanung    (c)  Der Baum beginnt mit einer header-row, und die
                        beginnt mit dem Wochenschalter: ◀ | KW 39 / 2026 | ▶
                        | 23.09.-28.09. | Abzeichen. "KW 39 / 2026" ist ein
                        ZEITRAUM zwischen zwei Pfeilknoepfen, kein Titel.
  Zeiterfassung    (c)  Formgleich mit Wochenplanung, dieselbe header-row,
                        derselbe Wochenschalter.
  Flotte           (c)  FlotteView fuehrt NULL Textliterale in einem Element
                        mit Titelgewicht. Das "📖 Fahrtenbuch" aus dem
                        D9-Befund gehoert zu FahrtenbuchView, und die
                        rendert laut eigenem Kommentar "als Overlay INNERHALB
                        von FlotteView" - ein Fenstertitel, keine
                        Seitenueberschrift.
  Startseite       (c)  Hier IST oberster Text mit Titelgewicht
                        (fontSize isMob?22:28, fontWeight 800) - aber es ist
                        eine BEGRUESSUNG: greet + ", " + firstName +
                        Jahreszeiten-Emoji, also "Guten Abend, Sebastian ☀️".
                        Als h2 gehoben wuerde eine Vorlesehilfe
                        "Ueberschrift Ebene 2: Guten Abend, Sebastian"
                        ansagen - das benennt den Leser, nicht die Seite.

(b) HAT KEINEN EINZIGEN VERTRETER. Keine der fuenf Ansichten fuehrt oben
einen Panel-Titel mit Text. Das ist ein Messergebnis, kein Versaeumnis.

🔴 WAS DIESER RIEGEL SCHUETZT - und warum er bei einer NEUEN Ueberschrift
   in den vier Ansichten ROT wird, obwohl das nach einer Verbesserung aussieht
─────────────────────────────────────────────────────────────────────────────
Vier Ansichten warten auf eine Entscheidung, die nur Sebastian treffen kann:
welchen Titel sie tragen. Eine erfundene Ueberschrift ist schlimmer als keine
- sie sieht richtig aus und behauptet etwas, das niemand entschieden hat. Ein
Titel aus dem Bauteilnamen ("FlotteView" -> "Flotte"), aus dem Reiter oder
frei formuliert ist genau das.

Deshalb macht dieser Riegel jede h2/h1/h3 in diesen vier Ansichten rot. Wer
eine setzt, muss hier vorbei und den Text nennen, den Sebastian vorgegeben
hat. Das ist kein Verbot von Ueberschriften, sondern ein Verbot von
Ueberschriften OHNE Herkunft.

WAS DIESE DATEI NICHT MISST
───────────────────────────
Ob die h2 im Bild genauso gross ist wie das div vorher. Das kann nur der
Browser; die Pixelneutralitaet ist hier am Quelltext BEGRUENDET (fontSize und
fontWeight bleiben inline, margin:0 nimmt den Vorgabeabstand, und die einzige
h2-Regel der Huelle steht unter @media(max-width:340px) und verlangt
.header-row) und nicht gemessen. Und sie misst nicht, ob die 17 uebrigen
Ansichten ihre Ueberschrift behalten - das tut der Grundstand.
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import code_scan  # noqa: E402

PFAD = os.path.join(os.path.dirname(__file__), "..", "index.html")

# Die vier Ansichten, deren Titel Sebastian vorgibt. Bauteilname -> Warum.
OHNE_UEBERSCHRIFT = {
    "WeekPlan": "header-row beginnt mit dem Wochenschalter; KW ist ein Zeitraum",
    "ZeiterfassungView": "formgleich mit WeekPlan, derselbe Wochenschalter",
    "FlotteView": "null Textliterale mit Titelgewicht; Fahrtenbuch ist ein Overlay",
    "HomeView": "oberster Text ist eine Begruessung mit Vornamen, kein Titel",
}


def _lies():
    roh = io.open(PFAD, encoding="utf-8", newline="").read()
    if len(roh) < 3_000_000:
        raise AssertionError(
            "index.html hat nur %d Bytes - Datenverlust, keine "
            "Ueberschriftenfrage." % len(roh))
    return roh


def _dekl(text):
    return [(m.start(), m.group(1))
            for m in re.finditer(r"function\s+([A-Za-z_]\w*)\s*\(", text)]


def _rumpf(text, name):
    """Von der Deklaration bis zur NAECHSTEN, mit Ober- UND Untergrenze.

    Nicht Klammern zaehlen - das lief in diesem Lauf einmal auf 1,77 MB
    davon und aenderte 1744 Stellen. Keine feste Laenge - ein 95_000er
    Fenster hat einen fremden Riegel gebrochen, als ein Kommentar dazukam.
    """
    d = _dekl(text)
    idx = [i for i, (_, n) in enumerate(d) if n == name]
    assert len(idx) == 1, "%s ist %dx deklariert - Abgrenzung unmoeglich." % (
        name, len(idx))
    i = idx[0]
    a = d[i][0]
    b = d[i + 1][0] if i + 1 < len(d) else len(text)
    gr = b - a
    assert 5_000 < gr < 200_000, (
        "%s: Rumpf %d Zeichen. Ausserhalb von 5k..200k heisst das, die "
        "Abgrenzung ist davongelaufen oder zu kurz - die Aussage darueber "
        "waere wertlos." % (name, gr))
    return a, text[a:b]


# 🔴 ZWEI SCHREIBWEISEN, EINE EIGENSCHAFT.
# Die erste Fassung dieser Datei suchte nur `createElement('h2'` und meldete
# die neue Ueberschrift als fehlend - Bauprovisorien benutzt durchgehend den
# lokalen Kuerzel `const h=React.createElement`. Der Riegel hat also eine
# SCHREIBWEISE gemessen, nicht die Eigenschaft "es gibt hier eine
# Ueberschrift", und wurde dadurch rot an einer Stelle, wo alles stimmte.
# Dieselbe Fehlerform in der Gegenrichtung waere schlimmer: ein Muster, das
# eine Form nicht kennt, meldet "keine erfundene Ueberschrift gefunden".
# Das `(?<![A-Za-z0-9_$.])` verhindert, dass `search(`, `_ch(` oder `.h(`
# als Aufruf des Kuerzels gelesen werden.
UEBERSCHRIFT = re.compile(
    r"""(?:createElement|(?<![A-Za-z0-9_$.])h)\(\s*['"](h[123])['"]""")


def _ueberschriften_in(text, name):
    """h1/h2/h3-Aufrufe im CODE dieses Bauteils, beide Schreibweisen."""
    a, r = _rumpf(text, name)
    feld = code_scan.ist_code(text)
    aus = []
    for m in UEBERSCHRIFT.finditer(r):
        p = a + m.start()
        if feld[p]:
            aus.append((m.group(1), text.count("\n", 0, p) + 1))
    return aus


def test_bauprovisorien_traegt_eine_echte_ueberschrift():
    """Fall (a): das div ist ein h2 - und zwar mit margin:0.

    Gemessen werden die EIGENSCHAFTEN, nicht die Schreibweise: Element h2,
    der Text steht drin, margin:0 ist gesetzt, und fontSize/fontWeight sind
    unveraendert inline. Ohne margin:0 kostet der Umbau Pixel (der
    Vorgabeabstand eines h2 ist 0.83em oben und unten), und dann waere aus
    einer Gliederungsfrage eine Geometrieaenderung geworden.
    """
    roh = _lies()
    treffer = _ueberschriften_in(roh, "BauprovisorienView")
    assert treffer, (
        "BauprovisorienView fuehrt keine h1/h2/h3 mehr. Dann ist der D9-Umbau "
        "verlorengegangen und die Ansicht ist wieder eine Seite ohne "
        "Gliederung.")
    assert len(treffer) == 2, (
        "BauprovisorienView fuehrt %d Ueberschrift(en), erwartet 2 - eine je "
        "Seitenzustand (Liste und Formular). Gefunden: %s"
        % (len(treffer), treffer))
    a, r = _rumpf(roh, "BauprovisorienView")
    # Je Zustand die Groesse, die vorher im div stand. Eine andere Zahl kostet
    # Pixel, und dann waere aus einer Gliederungsfrage eine
    # Geometrieaenderung geworden.
    # Der Text ist der VOLLE Wortlaut des Literals, Emoji eingeschlossen. Ein
    # Teilstring ab "Bauprovisorien" schlug fehl, weil das Literal mit dem
    # Baustellenzeichen beginnt - und ein Riegel, der auf einen Teilstring
    # prueft, wuerde auch eine geaenderte Beschriftung durchlassen.
    ERWARTET = [("Formular", "fontSize:18", "Bauprovisorium bearbeiten"),
                ("Liste", "fontSize:20", "\U0001f6a7 Bauprovisorien")]
    h2s = list(re.finditer(
        r"""(?:createElement|(?<![A-Za-z0-9_$.])h)\(\s*'h2'\s*,"""
        r"""\s*\{\s*style:\s*\{([^}]*)\}""", r))
    assert len(h2s) == 2, (
        "Die h2 in BauprovisorienView haben nicht die erwartete Form "
        "(h('h2',{style:{...}})): %d von 2 gefunden. Treffer laut "
        "Elementzaehlung: %s" % (len(h2s), treffer))
    for m, (wie, groesse, text) in zip(h2s, ERWARTET):
        stil = m.group(1)
        for eig, warum in ((groesse, "die Groesse stand vorher so im div - "
                            "jede andere Zahl kostet Pixel"),
                           ("fontWeight:800", "das Gewicht war vorher 800"),
                           ("margin:0", "ohne margin:0 setzt der Browser dem "
                            "h2 0.83em Abstand oben und unten dazu")):
            assert eig in stil, (
                "Zustand '%s': `%s` fehlt im Stil der Ueberschrift (%s).\n"
                "Stil gemessen: %s" % (wie, eig, warum, stil))
        # Und der Text steht wirklich DRIN. Ein h2 mit richtigem Stil und
        # leerem Inhalt waere Anwesenheit statt Wirkung: vorhanden, gemessen,
        # und fuer eine Vorlesehilfe stumm.
        #
        # Das Fenster ist 1400 Zeichen breit, nicht 300: der erklaerende
        # Kommentar hinter dem Stil ist selbst ueber 600 Zeichen lang und hat
        # den Text aus einem engeren Fenster geschoben. Ein Kommentar, der den
        # eigenen Riegel bricht, ist in diesem Lauf sechsmal vorgekommen.
        #
        # 🔴 UND GEPRUEFT WIRD DIE ARGUMENTSTELLUNG, nicht das Vorkommen des
        # Wortes. Die Mutationsprobe hat gefunden, dass ein rohes Fenster hier
        # gruen bleibt, wenn man den Text aus der h2 ENTFERNT: derselbe
        # Kommentar enthaelt das Wort "Bauprovisorien" selbst, ein leeres h2
        # haette bestanden. Das ist die gefaehrliche Richtung der
        # Kommentar-Fehlerform - der Kommentar macht die Pruefung nicht rot,
        # sondern GRUEN.
        #
        # `ist_code` kommentarblind zu lesen half nicht: es schliesst
        # ZEICHENKETTEN mit aus, und der Titel IST eine. Verlangt wird
        # deshalb, dass der Text als Zeichenkette in Argumentstellung steht -
        # hinter einem Komma (Liste) oder einem Fragezeichen (Formular, der
        # Titel haengt an editId). Im Kommentar steht das Wort unquotiert;
        # eine Verwechslung ist damit ausgeschlossen.
        inhalt = r[m.end():m.end() + 1400]
        assert re.search(r'[,?:]\s*"' + re.escape(text), inhalt), (
            "Zustand '%s': %r steht nicht als Zeichenkette in "
            "Argumentstellung in der h2. Ein leeres h2 gliedert nichts, und "
            "das Wort irgendwo im Kommentar zaehlt nicht.\n"
            "Gefunden hinter dem Stil: %r" % (wie, text, inhalt[:160]))


def test_die_ueberschrift_steht_ganz_oben_im_baum():
    """Eine Seitenueberschrift, die nicht oben steht, gliedert nichts.

    Gemessen: zwischen dem `return h('div'` und der h2 liegt genau ein
    weiteres createElement (die Kopfzeile, die Titel und Knoepfe traegt).
    Rutscht die h2 nach unten, waere sie zwar vorhanden - und genau das ist
    die Fehlerform "Anwesenheit statt Wirkung".
    """
    roh = _lies()
    _, r = _rumpf(roh, "BauprovisorienView")
    # 🔴 ZWEI SEITENZUSTAENDE, und beide brauchen ihre Ueberschrift.
    # BauprovisorienView gibt zweimal zurueck: bei `sub==="form"` das
    # Formular, sonst die Liste. Der Grundstand hat nur die LISTE aufgenommen -
    # die Sonde hat das Formular nie geoeffnet. Beide Zustaende waren also
    # Seiten ohne Gliederung, einer davon unbemerkt.
    #
    # Die erste Fassung dieses Riegels nahm die LETZTE `return h('div'` und
    # landete im QR-Overlay, das weiter unten ebenfalls ein div zurueckgibt -
    # sie meldete "keine Ueberschrift dahinter", obwohl sie sieben Zeilen nach
    # der Listen-Rueckgabe steht. Ein Anker, der zu weit schneidet, ist in
    # diesem Lauf die haeufigste Fehlerform. Deshalb wird jeder Zustand an
    # seinem eigenen Zweigwaechter verankert.
    ZWEIGE = [
        ('if(sub==="form"){', "Formular"),
        ("// ── LISTE ──", "Liste"),
    ]
    for anker, wie in ZWEIGE:
        assert r.count(anker) == 1, (
            "Der Zweig '%s' ist %dx zu finden statt 1x (Anker %r). Dann "
            "trifft die Abgrenzung nicht mehr, und alles darunter ist eine "
            "Aussage ueber die falsche Stelle."
            % (wie, r.count(anker), anker))
        ret = r.index(anker)
        m = UEBERSCHRIFT.search(r, ret)
        assert m, (
            "Im Zustand '%s' steht hinter dem Zweigwaechter keine "
            "Ueberschrift. Beide Zustaende dieser Ansicht rendern eine eigene "
            "Seite; fehlt einem die Ueberschrift, ist er eine Seite ohne "
            "Gliederung - und der Grundstand wuerde es nicht zeigen, weil er "
            "nur die Liste aufgenommen hat." % wie)
        dazwischen = len(
            re.findall(r"(?<![A-Za-z0-9_$.])h\(\s*'", r[ret:m.start()]))
        assert dazwischen <= 4, (
            "Zustand '%s': zwischen Zweigbeginn und Ueberschrift liegen %d "
            "Elemente. So tief im Baum ist sie vorhanden, gliedert die Seite "
            "aber nicht mehr - Anwesenheit statt Wirkung." % (wie, dazwischen))


def test_die_vier_offenen_ansichten_haben_keine_erfundene_ueberschrift():
    """Fall (c): hier entscheidet Sebastian den Text, nicht ich.

    Rot bei einer NEUEN Ueberschrift - auch wenn das nach einer Verbesserung
    aussieht. Eine erfundene Ueberschrift sieht richtig aus und behauptet
    etwas, das niemand entschieden hat; ein Titel aus dem Bauteilnamen oder
    aus dem Reiter ist genau das. Wer hier eine setzt, nennt in dieser Datei
    den Text und woher er kommt.
    """
    roh = _lies()
    fund = {}
    for name in OHNE_UEBERSCHRIFT:
        t = _ueberschriften_in(roh, name)
        if t:
            fund[name] = t
    assert not fund, (
        "In %d Ansicht(en), die auf eine Entscheidung warten, steht jetzt "
        "eine Ueberschrift:\n%s\n\n"
        "Kommt der Text von Sebastian? Dann gehoert er in diese Datei, und "
        "diese Pruefung wird um die Ansicht erleichtert - mit dem Wortlaut "
        "im Klartext. Kommt er aus dem Bauteilnamen, aus dem Reiter oder aus "
        "einer freien Formulierung: herausnehmen. Der Grund je Ansicht:\n%s"
        % (len(fund),
           "\n".join("  %-20s %s" % (k, v) for k, v in fund.items()),
           "\n".join("  %-20s %s" % (k, v)
                     for k, v in OHNE_UEBERSCHRIFT.items())))


def test_der_riegel_wird_bei_einer_erfundenen_ueberschrift_rot():
    """KOEDER auf den Zaehler von oben.

    Der Riegel SUCHT etwas und meldet gruen, wenn er nichts findet - die
    gefaehrlichste Bauform. Findet er eine absichtlich eingesetzte
    Ueberschrift nicht, wuerde er auch eine echte nicht finden, und "keine
    erfundene Ueberschrift" waere die Aussage eines Blinden.
    """
    roh = _lies()
    for name in OHNE_UEBERSCHRIFT:
        a, r = _rumpf(roh, name)
        # Eine Ueberschrift unmittelbar hinter die Deklaration setzen.
        stelle = a + r.index("{") + 1
        kaputt = (roh[:stelle]
                  + """React.createElement('h2',{},"Erfundener Titel");"""
                  + roh[stelle:])
        t = _ueberschriften_in(kaputt, name)
        assert t, (
            "KOEDER NICHT GEFUNDEN in %s: eine eingesetzte h2 wird nicht "
            "erkannt. Der Zaehler ist blind - entweder greift das Muster "
            "nicht, oder die Abgrenzung des Rumpfes trifft die Stelle nicht, "
            "oder code_scan haelt sie fuer Text." % name)


def test_die_gesamtzahl_der_seitenueberschriften():
    """30 statt 28 - die Zahl STEIGT, weil ZWEI dazukamen.

    Zwei, nicht eine: BauprovisorienView rendert zwei Seitenzustaende (Liste
    und Formular), und beide hatten ihren Titel in einem div. Der zweite war
    nie gemessen - die Sonde hat das Formular nie geoeffnet.

    Waere die Zahl gesunken, waere eine Ueberschrift verlorengegangen. Die
    Richtung ist hier die ganze Aussage.
    """
    roh = _lies()
    # Nur h2 - h1/h3 zaehlen hier nicht mit, sonst misst die Zahl etwas
    # anderes als sie behauptet.
    st = code_scan.nur_code_stellen(
        roh, r"""(?:createElement|(?<![A-Za-z0-9_$.])h)\(\s*'h2'""",
        regex=True)
    assert len(st) == 30, (
        "%d h2-Aufrufe im Code, erwartet 30. Sinkt die Zahl, ist eine "
        "Seitenueberschrift verschwunden - das ist ein Fehler und kein "
        "Aufraeumen. Steigt sie, pruefen: in welcher Ansicht, und woher "
        "kommt der Text?" % len(st))
