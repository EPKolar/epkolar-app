# -*- coding: utf-8 -*-
"""v3.9.942 - die B3-Befunde 4 bis 7, und der Nutzerbefund zur Planflaeche.

WAS DIESE DATEI KANN UND WAS NICHT
──────────────────────────────────
Sie liest Quelltext. Die eigentlichen Befunde sind am gerenderten Schirm
gemessen worden (scripts/b3_vier_ansichten_messen.py bei 375, 390 und 1440 px,
scripts/hellmodus_ansichten.py ueber alle 31 Ansichten) - das kann pytest hier
nicht nachstellen. Diese Riegel halten deshalb die URSACHEN fest, die dort
gemessen wurden, damit ein spaeteres "Aufraeumen" auffaellt.

Wo ein Riegel nur Anwesenheit pruefen kann, steht es dabei. Jede zaehlende
Pruefung hat einen KOEDER: findet sie ihre Grundgesamtheit nicht, meldet sie
nicht gruen, sondern rot. Ohne das wird aus "nichts gefunden" ein "keine
Fehler" - der haeufigste Ausfall in diesem ganzen Umbau.

DIE GEGENMESSUNGEN, auf die sich diese Datei stuetzt (12 Laeufe, alle Koeder an)
    Tippziele (Knoepfe) < 44 px  bei 375 und 390 px:  vorher 4 bzw. 1 -> 0
    nur-Emoji ohne title/aria:   vorher 5/6/2/2       -> 0 in allen Ansichten
    Home, waagrechter Roller:    vorher .main-pad 460/390 -> keiner
    Planflaeche im Hellmodus:    vorher 57,5 % (390) / 72,7 % (1440) des Schirms
"""
import io
import re

from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]


def _roh():
    return io.open(str(WURZEL / "index.html"), encoding="utf-8",
                   newline="").read()


# ── Der Nutzerbefund: die Planflaeche war in beiden Themen schwarz ────────

def test_die_planflaeche_folgt_dem_thema():
    """DER Befund aus "mobil hell ist auch sehr dunkel".

    Die Flaeche trug `background: "#1a1a1a"` FEST - der Hellmodus konnte sie
    gar nicht erreichen. Gemessen nach dem, was man sieht (Rasterabtastung):
    57,5 Prozent des Schirms bei 390 px, 72,7 Prozent bei 1440 px.
    """
    roh = _roh()
    i = roh.find("{ref: viewportRef, style:")
    assert i > 0, "Die Planflaeche (viewportRef) wurde nicht gefunden."
    block = roh[i:i + 1400]
    assert 'background: "#1a1a1a"' not in block, (
        "Die Planflaeche traegt die Farbe wieder fest. Dann ist sie im "
        "Hellmodus genauso schwarz wie im Dunkelmodus, und der Nutzerbefund "
        "ist zurueck.")
    assert '_dark?"#1a1a1a":V.bd' in block, (
        "Die Planflaeche haengt nicht mehr an _dark. Erwartet "
        "`_dark?\"#1a1a1a\":V.bd` - der Dunkelmodus bleibt bytegleich, der "
        "Hellmodus bekommt ein vorhandenes Token.")


def test_der_dunkelmodus_der_planflaeche_ist_unveraendert():
    """KOEDER-Gegenstueck. Der Dunkelmodus war nie zu beanstanden; haette der
    Umbau ihn mitgenommen, waere das eine Verschlechterung durch eine
    Verbesserung."""
    roh = _roh()
    i = roh.find("{ref: viewportRef, style:")
    block = roh[i:i + 1400]
    assert '"#1a1a1a"' in block, (
        "Im Dunkelmodus steht #1a1a1a nicht mehr - dann wurde mehr geaendert "
        "als der Befund verlangte.")


# ── B2: drei CSS-Regeln schlugen die 44-px-Hausregel ──────────────────────

def test_keine_header_regel_geht_unter_44_px():
    """Gemessen bei 390 px: vier Kopfknoepfe 40 px hoch, einer bei
    Arbeitsschein bearbeiten. Die Hausregel traegt `!important` und verliert
    trotzdem: `.header-row .mob-stack button` hat die Spezifitaet 0,2,1 gegen
    `button` 0,0,1, und zwei `!important` entscheiden nach Spezifitaet.

    Der KOEDER ist die Grundgesamtheit selbst: findet der Riegel diese Regeln
    nicht mehr, ist seine Null keine Aussage.
    """
    roh = _roh()
    stellen = [m.start() for m in
               re.finditer(r"\.header-row \.mob-stack button \{", roh)]
    assert len(stellen) >= 3, (
        "KOEDER STUMM: nur %d Regeln `.header-row .mob-stack button` gefunden, "
        "erwartet mindestens 3 (gemessen: @media 600px, 414px, 380px). Ohne "
        "die Grundgesamtheit sagt dieser Riegel nichts." % len(stellen))

    zu_klein = []
    for p in stellen:
        block = roh[p:roh.index("}", p)]
        for m in re.finditer(r"min-height:\s*(\d+)px", block):
            if int(m.group(1)) < 44:
                zu_klein.append((p, int(m.group(1))))
    assert not zu_klein, (
        "Diese Regeln setzen die Knopfhoehe wieder unter 44 px: %s. Sie "
        "schlagen die Hausregel @media (pointer:coarse),(max-width:768px) "
        "durch hoehere Spezifitaet - hier nachziehen, nicht dort."
        % zu_klein)


def test_keine_header_regel_geht_unter_12_px_schrift():
    """12 px ist der Boden der App (UI.fMeta). Gemessen standen hier 11, 10
    und 9 px."""
    roh = _roh()
    stellen = [m.start() for m in
               re.finditer(r"\.header-row \.mob-stack button \{", roh)]
    assert len(stellen) >= 3, "KOEDER STUMM: %d Regeln." % len(stellen)
    zu_klein = []
    for p in stellen:
        block = roh[p:roh.index("}", p)]
        for m in re.finditer(r"font-size:\s*(\d+)px", block):
            gr = int(m.group(1))
            # font-size: 0 ist Absicht (<=340 px: Text weg, Emoji bleibt) und
            # traegt keine Schrift, die man lesen muesste. Genau darunter steht
            # die Regel, die das Emoji wieder auf 16 px setzt.
            if 0 < gr < 12:
                zu_klein.append((p, gr))
    assert not zu_klein, (
        "Diese Regeln setzen die Schrift wieder unter 12 px: %s." % zu_klein)


# ── B3: die fuenf Icon-Reiter in Werkzeuge ────────────────────────────────

def test_die_werkzeug_reiter_tragen_ihre_beschriftung():
    """Gemessen: bei 390 px trugen 0 von 5 Reitern Text, bei 1440 px 5 von 5 -
    `title` und `aria-label` fehlten in BEIDEN Breiten. Die Beschriftung stand
    schon im Objekt (`l`); es wurde kein Wort erfunden.

    Der eindeutige Anker ist die Werkzeug-Farbe #d97706 - der naheliegende
    Anker `, t.i, " " , isMob?"":t.l)` steht ZWEIMAL im Dokument (einmal
    Zeiterfassung, einmal Werkzeuge) und waere hier falsch.
    """
    roh = _roh()
    i = roh.find('color:sub===t.id?"#d97706":V.dm')
    assert i > 0, (
        "KOEDER STUMM: die Reiterzeile in Werkzeuge wurde nicht gefunden "
        "(Anker: die Werkzeug-Farbe #d97706).")
    block = roh[max(0, i - 700):i]
    assert "title: t.l" in block and "'aria-label': t.l" in block, (
        "Den fuenf Icon-Reitern in Werkzeuge fehlt title/aria-label wieder. "
        "Bei 390 px tragen sie keinen Text - dann liegt die Bedeutung allein "
        "im Emoji.")


# ── B5: Symbol-Knoepfe ohne Beschriftung ──────────────────────────────────

def test_die_symbolknoepfe_tragen_bedeutung():
    """Sieben Stellen in drei Ansichten, je bei 390 UND 1440 px gemessen. Das
    Tippziel war ueberall in Ordnung - es fehlte die Bedeutung."""
    roh = _roh()
    faelle = [
        ("Woche zurück", "()=>switchKw(Math.max(1,kw-1))"),
        ("Woche vor", "()=>switchKw(Math.min(_getMaxKW(yr),kw+1))"),
        ("Bearbeiten", 'padding:"3px 8px",fontSize:12}}, "✏️"'),
        ("Arbeitsschein löschen", "()=>deleteAs(editId)"),
        ("Punkt hinzufügen", "style:{...bpS,padding:'7px 13px'}},'+')"),
    ]
    fehlt = []
    for txt, anker in faelle:
        i = roh.find(anker)
        if i < 0:
            fehlt.append("%s: ANKER WEG (%r)" % (txt, anker[:40]))
            continue
        block = roh[max(0, i - 420):i + 200]
        if txt not in block:
            fehlt.append("%s: keine Beschriftung am Knopf" % txt)
    assert not fehlt, (
        "Diese Symbol-Knoepfe tragen keine Bedeutung mehr: %s" % fehlt)


def test_die_beiden_zu_kleinen_symbole_sind_groesser():
    """Zwei der sieben waren 10 bzw. 11 px. Ein Symbol, das die einzige
    Information traegt, darf nicht die kleinste Schrift der Seite sein."""
    roh = _roh()
    assert 'padding:"3px 8px",fontSize:10}}, "✏️"' not in roh, (
        "Der Stift in der Werkzeug-Tabelle ist wieder 10 px.")
    assert "{...bdS,fontSize:11}}, \"\U0001f5d1️\"" not in roh, (
        "Der Muelleimer im Arbeitsschein-Formular ist wieder 11 px.")
    assert "{...bdS,fontSize:UI.fKlein}}" in roh, (
        "Der Muelleimer haengt nicht an UI.fKlein.")


# ── B4: der Querroller auf Home ───────────────────────────────────────────

def test_das_home_gitter_nimmt_dem_track_das_auto_minimum():
    """Gemessen bei 390 px: `.main-pad` hatte scrollWidth 460 gegen
    clientWidth 390 - 70 px zu viel -, waehrend
    `document.scrollingElement.scrollWidth` genau 390 meldete. Eine Regel, die
    das Dokument fragt, kann diesen Fall NIE sehen, und sie war gruen.

    Ursache: ein `1fr`-Track ist `minmax(auto,1fr)`, und das auto-Minimum ist
    die min-content-Breite des Kindes. Die Team-Karte war 452 px breit und zog
    den Track ueber die verfuegbaren 374 px.
    """
    roh = _roh()
    i = roh.find("ACTIVE PROJECTS")
    assert i > 0, "KOEDER STUMM: der Abschnitt ACTIVE PROJECTS wurde nicht gefunden."
    block = roh[max(0, i - 2200):i]
    assert 'isMob?"minmax(0,1fr)":"minmax(0,1fr) minmax(0,1fr)"' in block, (
        "Der Abschnittsrahmen auf Home steht wieder auf `1fr`. Damit hat der "
        "Track das auto-Minimum zurueck, und die Seite rollt bei 390 px "
        "wieder quer (gemessen 70 px) - sichtbar als angeschnittene dritte "
        "Team-Kachel.")


# ── B7 bleibt ausdruecklich UNENTSCHIEDEN ─────────────────────────────────

def test_b7_ist_nicht_entschieden_und_wird_nicht_repariert():
    """Der gemeldete Beschnitt am Sync-Knopf (scrollWidth 48 gegen
    clientWidth 44) ist NICHT bestaetigt und NICHT widerlegt.

    scripts/b7_syncknopf_messen.py misst, ob wirklich Text verloren geht -
    nicht nur, ob der Kasten ueberlaeuft. Ergebnis: in diesem Aufbau tritt der
    Fall gar nicht auf, weil der Knopf dafuer den Zustand "offline UND vier
    ausstehende Auftraege" braeuchte. Der Koeder der Sonde schlaegt an (198 px
    belegt verlorener Text), sie hatte also nur nichts zu messen.

    Dieser Riegel haelt genau das fest: es wurde NICHTS auf Verdacht geaendert,
    und die Sonde verweigert bei leerer Grundgesamtheit ein Urteil. Ohne diese
    Verweigerung waere "kein Textverlust" eine Aussage ueber eine leere Menge -
    derselbe Fehler, der in diesem Lauf schon zweimal ein falsches Gruen
    erzeugt hat.
    """
    sonde = WURZEL / "scripts" / "b7_syncknopf_messen.py"
    assert sonde.exists(), "Die Sonde zu B7 fehlt."
    txt = io.open(str(sonde), encoding="utf-8").read()
    assert "kandidaten == 0" in txt and "NICHT GEMESSEN" in txt, (
        "Die B7-Sonde verweigert bei leerer Grundgesamtheit kein Urteil mehr. "
        "Dann kann sie wieder 'kein Textverlust' melden, ohne etwas gemessen "
        "zu haben.")
    assert "KOEDER" in txt, "Die B7-Sonde hat keinen Koeder mehr."
