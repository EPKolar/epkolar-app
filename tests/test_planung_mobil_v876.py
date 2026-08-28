# -*- coding: utf-8 -*-
"""
v3.9.876 - !isMob && isMob: drei Bloecke, die am Handy nie gerendert wurden.

ACHTUNG: Diese Datei ist ROT, solange der Patch nicht angewendet ist. Sie
beschreibt den ZIELZUSTAND. Erst nach dem Eingriff in index.html werden die
Riegel gruen. Die Umkehrprobe am Ende ist immer gruen - sie prueft nur, dass
das Messgeraet den alten Zustand auch wirklich als falsch erkennt.

BEFUND (maschinell gemessen, nicht nach Augenmass):
Ein Klammerzaehler, der Strings, Template-Literale mit ${}, Regex und
Kommentare korrekt ueberspringt, ergab fuer index.html (v3.9.875, 29.201
Zeilen, Selbsttest der Endtiefe = 0/0/0):

    Z21251 Sp35   , !isMob&&React.createElement(React.Fragment, null
                  -> diese runde Klammer schliesst erst auf Z21422

Innerhalb dieser Spanne, also innerhalb von "nur wenn NICHT mobil", lagen:

    Z21256-21277  , spezFz.length>0&&isMob&&(()=>{ ... })()
                  Spezialfahrzeug-Streifen fuer den gewaehlten Tag.
                  Eigener Kommentar Z21254: "v3.9.505 Mobile (<600px)".
    Z21413-21421  , React.createElement('div', {gap:isMob?8:6, ...,
                                flexDirection:isMob?"column":"row"})
                  Eigener Kommentar: "v3.9.506 Mobile: Footer column-Layout".
                  darin Z21414-21417  isMob?<Excel/PDF full-width>:null
                  darin Z21420        "N BVH · ⚠️ Konflikte" / "✅"

!isMob && isMob ist nie wahr. Am Handy fehlten damit: der Fahrzeug-Streifen,
Excel- und PDF-Export der Wochenplanung und die EINZIGE Konfliktanzeige der
Planung. Auf dem Desktop war nichts davon zu sehen, weil dort jeweils der
!isMob-Zweig danebensteht (Z21418/21419) - der Fehler war unsichtbar.

Die Herkunft laesst sich nicht aus der Historie belegen: alle drei Stellen
kamen in 1eb4bfc (754 Dateien, 102.714 Zeilen = Erst-Import) in einem Rutsch
ins Repo, die Commit-Nachricht sagt nichts dazu.
VERMUTUNG (nicht belegt): v3.9.503 legte das Desktop-Fragment mit dem
!isMob-Waechter an, v3.9.505 und v3.9.506 setzten ihre Mobil-Bloecke danach
INNERHALB dieses Fragments ein, ohne den Waechter darueber zu bemerken. Der
Kommentar bei v3.9.505 ("Desktop unveraendert (durchfallen auf Tabelle)")
liest sich wie von jemandem, der keinen Waechter darueber vermutete.

DER EINGRIFF (kleinstmoeglich, Desktop-Ausgabe bit-identisch):
Beide Bloecke sind das ERSTE bzw. das LETZTE Kind des Fragments. Also muss
kein Block verschoben werden - nur der Waechter:
  1. Waechter-Zeile oben loeschen  (-1 offene Klammer)
  2. Waechter-Zeile vor dem Desktop-Fahrzeugstreifen neu setzen (+1 offene)
  3. Fragment vor der Fusszeile schliessen  (+1 schliessende)
  4. Am Ende ")) " -> ")"                   (-1 schliessende)
Klammerbilanz: 0. Mit `node --check` auf dem herausgeloesten <script>-Block
verifiziert: vorher gruen, nachher gruen.

Auf dem Desktop rendern beide verschobenen Bloecke weiterhin nichts bzw.
dasselbe an derselben Stelle - React.Fragment erzeugt keinen DOM-Knoten,
die DOM-Ausgabe ist unveraendert.
"""
import re

import pytest

from conftest import _extract_fn


# ── Marker (jeder genau 1x in WeekPlan, geprueft in test_marker_sind_eindeutig)
GUARD = ", !isMob&&React.createElement(React.Fragment, null"
MOBFRAG = ", isMob&&React.createElement(React.Fragment, null"
MOB_FZ = ", spezFz.length>0&&isMob&&(()=>{"
DESK_FZ = ", spezFz.length>0&&!isMob&&(React.createElement("
FOOTER = (', React.createElement(\'div\', { style: {display:"flex",'
          'gap:isMob?8:6,marginTop:isMob?10:6,')
MOB_EXPORT = "isMob?React.createElement('div',{style:{display:'flex',gap:8,width:'100%'}}"
DESK_XLS = ", !isMob&&React.createElement('button', { onClick: exportXls,"
DESK_PDF = ", !isMob&&React.createElement('button', { onClick: _wpPrintPlan,"
COUNTER = '" BVH · "'
WEATHER = "/* Weather strip - aligned with table columns */"
TABLE = "/* Main table */"
FZBOOK = "/* Vehicle booking - only show if vehicles are booked or conflicts exist */"
ENDE = '/* end wpView==="planung" Fragment */'

ALLE_MARKER = [GUARD, MOBFRAG, MOB_FZ, DESK_FZ, FOOTER, MOB_EXPORT,
               DESK_XLS, DESK_PDF, COUNTER, WEATHER, TABLE, FZBOOK, ENDE]


# ── Messgeraet ──────────────────────────────────────────────────────────────
def _zu(src, i):
    """Index der ')', die zur '(' an Position i gehoert.

    Ueberspringt '..', "..", `..` inkl. ${}-Verschachtelung, // .., /* .. */
    und /regex/. Ohne das misst man in einer Datei mit 2000 Zeichen langen
    Zeilen Unsinn - genau daran ist der erste Anlauf dieser Messung
    gescheitert (ein `.replace(/"/g,"")` in einem Template-Literal hat den
    Zaehler 2900 Zeilen lang eingefroren, ohne dass er es gemeldet haette).
    """
    assert src[i] == "(", "Startposition ist keine oeffnende Klammer"
    n = len(src)
    tiefe = 0
    tpl = []          # Brace-Tiefen, bei denen ein ${ offen ist
    braces = 0
    vor = "("         # letztes bedeutsames Zeichen (fuer Regex-Erkennung)
    wort = ""
    j = i
    while j < n:
        c = src[j]
        if c in " \t\r\n":
            j += 1
            continue
        if c == "/" and j + 1 < n:
            nx = src[j + 1]
            if nx == "/":
                k = src.find("\n", j)
                j = n if k < 0 else k
                continue
            if nx == "*":
                k = src.find("*/", j + 2)
                j = n if k < 0 else k + 2
                vor, wort = "c", ""
                continue
            if vor in "(,=:[!&|?{};+-*%<>~^" or wort in (
                    "return", "typeof", "case", "in", "of", "new", "delete",
                    "void", "instanceof", "do", "else", "yield", "await"):
                k, klasse, ok = j + 1, False, False
                while k < n:
                    ck = src[k]
                    if ck == "\\":
                        k += 2
                        continue
                    if ck == "\n":
                        break
                    if ck == "[":
                        klasse = True
                    elif ck == "]":
                        klasse = False
                    elif ck == "/" and not klasse:
                        ok = True
                        break
                    k += 1
                if ok:
                    k += 1
                    while k < n and src[k].isalpha():
                        k += 1
                    j, vor, wort = k, "r", ""
                    continue
            j += 1
            vor, wort = "/", ""
            continue
        if c in "\"'":
            q, k = c, j + 1
            while k < n:
                if src[k] == "\\":
                    k += 2
                    continue
                if src[k] == q:
                    break
                k += 1
            j, vor, wort = k + 1, "s", ""
            continue
        if c == "`":
            k = j + 1
            while k < n:
                ck = src[k]
                if ck == "\\":
                    k += 2
                    continue
                if ck == "$" and k + 1 < n and src[k + 1] == "{":
                    tpl.append(braces)
                    braces += 1
                    j, vor, wort = k + 2, "{", ""
                    break
                if ck == "`":
                    j, vor, wort = k + 1, "s", ""
                    break
                k += 1
            else:
                j = n
            continue
        if c == "(":
            tiefe += 1
        elif c == ")":
            tiefe -= 1
            if tiefe == 0:
                return j
        elif c == "{":
            braces += 1
        elif c == "}":
            braces -= 1
            if tpl and braces == tpl[-1]:
                tpl.pop()
                k = j + 1
                while k < n:
                    ck = src[k]
                    if ck == "\\":
                        k += 2
                        continue
                    if ck == "$" and k + 1 < n and src[k + 1] == "{":
                        tpl.append(braces)
                        braces += 1
                        k += 2
                        break
                    if ck == "`":
                        k += 1
                        break
                    k += 1
                j, vor, wort = k, "s", ""
                continue
        if c.isalnum() or c in "_$":
            k = j
            while k < n and (src[k].isalnum() or src[k] in "_$"):
                k += 1
            wort, vor, j = src[j:k], "w", k
            continue
        vor, wort = c, ""
        j += 1
    raise AssertionError("keine passende schliessende Klammer gefunden")


def _klammerneutral(quelle):
    """True, wenn die runden Klammern in `quelle` netto aufgehen.

    Trick statt zweitem Zaehler: eine Huellklammer drumherum muss dann genau
    am letzten Zeichen schliessen. Zu viele '(' -> _zu findet nichts,
    zu viele ')' -> _zu schliesst zu frueh.
    """
    hilfs = "(" + quelle + ")"
    try:
        return _zu(hilfs, 0) == len(hilfs) - 1
    except AssertionError:
        return False


def _spanne(quelle, marker):
    """(anfang, ende) der React.createElement(...)-Klammer hinter `marker`."""
    p = quelle.index(marker)
    auf = quelle.index("React.createElement(", p) + len("React.createElement(") - 1
    return auf, _zu(quelle, auf)


def _drin(spanne, pos):
    return spanne[0] < pos < spanne[1]


@pytest.fixture(scope="module")
def wp(index_html):
    q = _extract_fn(index_html, "WeekPlan")
    assert q, "function WeekPlan nicht gefunden"
    return q


# ── Riegel ──────────────────────────────────────────────────────────────────
def test_marker_sind_eindeutig(wp):
    """Ohne das misst jeder folgende Riegel eine beliebige Fundstelle."""
    for m in ALLE_MARKER:
        assert wp.count(m) == 1, (
            "Marker kommt %dx statt 1x in WeekPlan vor - Messung wertlos:\n%s"
            % (wp.count(m), m)
        )


def test_messgeraet_selbsttest(wp):
    """Positivkontrolle: das MOBIL-Fragment umschliesst nachweislich den
    Tageswaehler und endet nachweislich VOR dem Desktop-Waechter. Faende der
    Zaehler das nicht, waeren alle weiteren Aussagen wertlos."""
    mob = _spanne(wp, MOBFRAG)
    assert mob[1] > mob[0], "Messgeraet liefert keine Spanne"
    for name, marker in (("Karten-Picker", MOB_PICKER), ("Tages-Karten", MOB_CARDS)):
        assert wp.count(marker) == 1, "Marker %s nicht eindeutig" % name
        assert _drin(mob, wp.index(marker)), (
            "%s liegt angeblich NICHT im isMob-Fragment - dann zaehlt das "
            "Messgeraet falsch, nicht der Code ist kaputt." % name
        )
    assert not _drin(mob, wp.index(GUARD)), (
        "Das isMob-Fragment umschliesst angeblich den !isMob-Waechter - "
        "das Messgeraet ist desynchronisiert."
    )


def test_fahrzeugstreifen_liegt_nicht_im_desktop_waechter(wp):
    """Der Kern des Befunds: !isMob && ... && isMob ist nie wahr."""
    g = _spanne(wp, GUARD)
    assert not _drin(g, wp.index(MOB_FZ)), (
        "Der mobile Spezialfahrzeug-Streifen (spezFz.length>0&&isMob) liegt "
        "weiterhin INNERHALB von !isMob&&React.createElement(React.Fragment). "
        "!isMob && isMob ist nie wahr - am Handy erscheint kein Fahrzeug, "
        "auch kein Doppelbelegungs-Konflikt."
    )


def test_fusszeile_liegt_nicht_im_desktop_waechter(wp):
    """Excel/PDF und der Zaehler haengen an derselben Fusszeile."""
    g = _spanne(wp, GUARD)
    assert not _drin(g, wp.index(FOOTER)), (
        "Die Fusszeile der Planung (gap:isMob?8:6 / flexDirection:isMob?...) "
        "liegt weiterhin im !isMob-Fragment. Damit sind am Handy Excel, PDF "
        "und die Zeile 'N BVH · Konflikte' unerreichbar."
    )


def test_mobiler_exportzweig_ist_erreichbar(wp):
    g = _spanne(wp, GUARD)
    assert not _drin(g, wp.index(MOB_EXPORT)), (
        "Der mobile Export-Zweig (isMob?<Excel/PDF full-width>:null) steht "
        "immer noch unter !isMob - Excel und PDF fehlen am Handy vollstaendig."
    )


def test_konfliktanzeige_ist_erreichbar(wp):
    """Es gibt in der Wochenplanung keine zweite Stelle, die Konflikte meldet."""
    g = _spanne(wp, GUARD)
    assert not _drin(g, wp.index(COUNTER)), (
        "Der Zaehler 'N BVH · ⚠️ Konflikte' steht immer noch unter !isMob. "
        "Er ist die EINZIGE Konfliktanzeige der Planung - am Handy plant man "
        "sonst blind."
    )


def test_desktop_zweig_bleibt_im_waechter(wp):
    """Gegenprobe: der Eingriff darf den Desktop nicht mit herausziehen."""
    g = _spanne(wp, GUARD)
    for name, marker in (("Desktop-Fahrzeugstreifen", DESK_FZ),
                         ("Wetterstreifen", WEATHER),
                         ("Haupttabelle", TABLE),
                         ("Fahrzeug-Buchungszeile", FZBOOK)):
        assert _drin(g, wp.index(marker)), (
            "%s liegt nicht mehr im !isMob-Fragment - dann erscheint die "
            "7-Spalten-Desktop-Ansicht am Handy." % name
        )


def test_desktop_knoepfe_behalten_ihren_eigenen_waechter(wp):
    """Sonst stuenden nach dem Eingriff auf dem Desktop vier Knoepfe."""
    assert DESK_XLS in wp, (
        "Der Desktop-Excel-Knopf hat seinen eigenen !isMob-Waechter verloren."
    )
    assert DESK_PDF in wp, (
        "Der Desktop-PDF-Knopf hat seinen eigenen !isMob-Waechter verloren."
    )


def test_reihenfolge_der_bloecke_ist_erhalten(wp):
    """Die DOM-Reihenfolge des Desktops darf sich nicht verschieben."""
    folge = [("mobiles Fragment", MOBFRAG), ("mobiler Fahrzeugstreifen", MOB_FZ),
             ("Desktop-Waechter", GUARD), ("Desktop-Fahrzeugstreifen", DESK_FZ),
             ("Wetterstreifen", WEATHER), ("Haupttabelle", TABLE),
             ("Fahrzeug-Buchungszeile", FZBOOK), ("Fusszeile", FOOTER)]
    positionen = [(n, wp.index(m)) for n, m in folge]
    for (n1, p1), (n2, p2) in zip(positionen, positionen[1:]):
        assert p1 < p2, "Reihenfolge verletzt: %s steht hinter %s" % (n1, n2)


def test_klammerbilanz_von_weekplan_ist_ausgeglichen(wp):
    """Ein verschobener Waechter darf die Bilanz nicht anfassen. WeekPlan ist
    eine einzelne Funktion - runde Klammern muessen darin auf 0 aufgehen."""
    assert _klammerneutral(wp), (
        "Die runden Klammern in WeekPlan gehen nicht mehr auf. Der Eingriff "
        "hat die Bilanz zerrissen - die Datei laedt so nicht."
    )
    g = _spanne(wp, GUARD)
    assert g[1] < len(wp), "Das !isMob-Fragment wird in WeekPlan nicht geschlossen"


# ── Umkehrprobe ─────────────────────────────────────────────────────────────
def _alten_zustand_bauen(quelle):
    """Rekonstruiert den Zustand von v3.9.875 - klammerneutral.

    Der Waechter wird samt seiner ZUGEHOERIGEN Schliessklammer versetzt:
    oeffnend vor den mobilen Fahrzeugstreifen, schliessend ans Ende des
    wpView-Fragments. Damit bleibt die Bilanz erhalten und die Rekonstruktion
    funktioniert unabhaengig davon, ob der Patch schon angewendet ist.
    """
    _, zu = _spanne(quelle, GUARD)
    kaputt = quelle[:zu] + quelle[zu + 1:]              # Schliessklammer raus
    kaputt = kaputt.replace(GUARD, "", 1)               # Waechterzeile raus
    kaputt = kaputt.replace(MOB_FZ, GUARD + "\n      " + MOB_FZ, 1)
    assert kaputt.count(ENDE) == 1, "Endmarke des wpView-Fragments fehlt"
    return kaputt.replace(ENDE, ")" + ENDE, 1)          # Schliessklammer ans Ende


def test_umkehrprobe_riegel_werden_rot(wp):
    """Der alte Zustand muss von genau diesen Riegeln erkannt werden. Ohne das
    waere jeder gruene Lauf oben nur ein Riegel, der nichts misst."""
    alt = _alten_zustand_bauen(wp)
    assert alt != wp, "Rueckbau griff nicht - Marker veraltet"
    assert alt.count(GUARD) == 1, "Rueckbau hat den Waechter dupliziert"

    g = _spanne(alt, GUARD)
    assert _drin(g, alt.index(MOB_FZ)), (
        "Umkehrprobe: der Fahrzeugstreifen-Riegel wuerde beim alten Zustand "
        "NICHT anschlagen - er misst nichts."
    )
    assert _drin(g, alt.index(FOOTER)), (
        "Umkehrprobe: der Fusszeilen-Riegel wuerde beim alten Zustand NICHT "
        "anschlagen - er misst nichts."
    )
    assert _drin(g, alt.index(MOB_EXPORT)), (
        "Umkehrprobe: der Export-Riegel wuerde beim alten Zustand NICHT "
        "anschlagen."
    )
    assert _drin(g, alt.index(COUNTER)), (
        "Umkehrprobe: der Konflikt-Riegel wuerde beim alten Zustand NICHT "
        "anschlagen."
    )
    # und der Desktop-Riegel muss auch im alten Zustand gruen bleiben,
    # sonst misst er die falsche Sache.
    assert _drin(g, alt.index(DESK_FZ)), (
        "Umkehrprobe: der Desktop-Riegel unterscheidet alt und neu nicht."
    )


def test_umkehrprobe_am_kuenstlichen_muster():
    """Zweite, vom Repo unabhaengige Kontrolle des Messgeraets: ein winziges
    Muster mit derselben Verschachtelung - inklusive einer Klammer in einem
    String und einer Regex, an denen ein naiver Zaehler scheitern wuerde."""
    falle = ", 'zu )( frueh', /\\)/g, `${(1)} )`"   # String, Regex, Template
    innen = ", spezFz.length>0&&!isMob&&(React.createElement('div'))"
    gut = "x(a" + GUARD + falle + innen + ")" + MOB_FZ + ")"
    schlecht = "x(a" + GUARD + falle + MOB_FZ + innen + "))"
    g = _spanne(gut, GUARD)
    assert not _drin(g, gut.index(MOB_FZ)), "Messgeraet meldet falsch-positiv"
    assert _drin(g, gut.index(DESK_FZ)), "Messgeraet verliert den Desktop-Block"
    s = _spanne(schlecht, GUARD)
    assert _drin(s, schlecht.index(MOB_FZ)), (
        "Messgeraet erkennt die Verschachtelung !isMob&&...&&isMob nicht - "
        "dann waeren alle Riegel dieser Datei wertlos."
    )


def test_versionsmarke_im_code(index_html):
    """Damit der Eingriff im Code auffindbar bleibt."""
    assert re.search(r"v3\.9\.876", index_html), (
        "Der Eingriff traegt keine Versionsmarke v3.9.876 - dann ist in einem "
        "halben Jahr nicht mehr nachvollziehbar, warum der Waechter wanderte."
    )
