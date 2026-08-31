# -*- coding: utf-8 -*-
"""v3.9.918 - Die Arbeitsschein-Zeile bekommt eine Rangordnung.

GEMESSEN, BEVOR ETWAS GEAENDERT WURDE
─────────────────────────────────────
Die Listenzeile traegt im Rechner-Zweig (`!isMob`) SECHS Editoren, jeder in
einem eigenen Kasten mit 1px-Rahmen:

  terminVorschlag  input type=date   :11290   -> updAs, NICHT in JUPROWA_PUSH_FIELDS
  terminBestaetigt input type=date   :11291   -> updAs, Push-Feld AK_TERMIN
  scheinstatus     select            :11292   -> updAs, Push-Feld AK_AUFSTATUS
  prioritaet       select            :11293   -> updAs, Push-Feld AK_PRIOR
  sachbearbeiter   select (isAdmin)  :11295   -> updAs, local-only (Push-Wert null)
  monteur          select            :11296   -> updAs, Push-Feld AK_MONTEUR

Bei dreissig Zeilen sind das 180 Kaesten. Die Mobil-Karte (`isMob`, :11244)
hat KEINEN einzigen dieser Editoren - dort stehen dieselben Werte als farbige
Chips. Die Ueberladung ist also ausschliesslich ein Rechner-Problem.

WARUM NICHTS AUS DER ZEILE GENOMMEN WURDE
─────────────────────────────────────────
Ein Editor darf nur dann aus der Zeile, wenn er woanders ohne Mehraufwand
erreichbar bleibt. Gemessen am Detail-Formular (`sub==="form"`, :11442-11585):

  * `sachbearbeiter` ist dort GAR NICHT bearbeitbar - nur Text-Anzeige mit dem
    Hinweis, dass er in der Liste gepflegt wird (v3.9.803 Kein-Dropdown-
    Grundsatz, :11528). Die Liste ist der EINZIGE Ort. Ihn herauszunehmen waere
    kein Aufraeumen, sondern ein Funktionsverlust.
  * Die uebrigen fuenf gibt es im Formular - aber das Formular speichert erst
    auf Knopfdruck (`saveAs`, :10847, Knopf :11556), waehrend die Liste sofort
    schreibt. Ein Feld ins Formular zu verschieben kostet also Oeffnen,
    Aendern, Speichern, Zurueck - vier Schritte statt einem.

Deshalb bleiben alle sechs Editoren, wo sie sind. Geaendert wird nur, wie laut
sie im Ruhezustand sind.

WAS GEAENDERT WURDE
───────────────────
Vier der sechs verlieren im Ruhezustand ihren Rahmen und lesen sich als Text
(genau wie die Chips der Mobil-Karte). Beim Zeigen kommt der Rahmen zurueck,
in der Farbe des Elements selbst. Zwei behalten ihren Rahmen dauerhaft:
bestaetigter Termin und Monteur.

WARUM AUSGERECHNET DIESE ZWEI
─────────────────────────────
Weil der Code sie als EINEN Vorgang kennt. Das Dispo-Brett uebergibt beim
Zuweisen (`onUebernehmen`, :11440) genau dieses Paar in einem Aufruf:

    updAs(scheinId,{terminBestaetigt:iso,monteur:monteurId,dauer:...,terminZeit:...})

Wer disponiert, beantwortet WER und WANN. Alles andere in der Zeile ist
entweder Nachtrag (Status, Prioritaet) oder Buero-Stammdatum (Sachbearbeiter)
oder eine Vorstufe ohne OFFA-Bedeutung (Terminvorschlag steht als einziges der
sechs NICHT in JUPROWA_PUSH_FIELDS, :3811-3827).

WAS DIESER RIEGEL NICHT KANN
────────────────────────────
Er misst NICHT, wie oft ein Disponent ein Feld tatsaechlich anfasst - das steht
in keiner Datei. Die Rangordnung stuetzt sich auf den Code, nicht auf gezaehlte
Klicks. Faellt Sebastian ein anderes Urteil, ist es eine Zeile: die Klasse
wandert von einem Editor zum anderen, und `_LAUT`/`_LEISE` hier mit.
"""
import re

from _hilfen import nur_code

# Die Koepfe der sechs Editoren in der Listenzeile. Jeder kommt in index.html
# GENAU EINMAL vor (mitgeprueft von test_die_sechs_koepfe_sind_eindeutig) -
# sonst wuerde jede Aussage hier die falsche Stelle vermessen.
_LEISE = {
    "terminVorschlag":
        'React.createElement(\'input\', { className: "epk-ruhig", type: "date", '
        'value: (_hasTermin(a.terminVorschlag)',
    "scheinstatus":
        'React.createElement(\'select\', { className: "epk-ruhig", '
        'value: a.scheinstatus',
    "prioritaet":
        'React.createElement(\'select\', { className: "epk-ruhig", '
        'value: a.prioritaet||"keine", onChange:',
    "sachbearbeiter":
        'isAdmin?React.createElement(\'select\', { className: "epk-ruhig", '
        'value: a.sachbearbeiter||"", onChange:',
}
_LAUT = {
    "terminBestaetigt":
        'React.createElement(\'input\', { type: "date", '
        'value: (_hasTermin(a.terminBestaetigt)',
    "monteur":
        'React.createElement(\'select\', { value: a.monteur||"",',
}

# Die sechs Schreibwege. Sie sind der eigentliche Gegenstand des Riegels:
# diese Version darf die BEDIENDICHTE aendern und sonst nichts.
_SCHREIBWEGE = (
    "updAs(a.id,{terminVorschlag:e.target.value})",
    "updAs(a.id,{terminBestaetigt:e.target.value})",
    "updAs(a.id,{scheinstatus:_newS})",
    "updAs(a.id,{prioritaet:e.target.value})",
    "updAs(a.id,{sachbearbeiter:e.target.value})",
    "updAs(a.id,{monteur:e.target.value})",
)


def _regeln(index_html):
    """Alle CSS-Regeln, deren Selektor die Ruhe-Klasse nennt.

    Rueckgabe: Liste von (selektor, rumpf).

    Kommentare MUESSEN vorher raus. Der Erklaertext neben den Regeln nennt die
    Fokus-Regel beim Namen; bliebe er stehen, zoege der Selektor-Teil des
    Musters ihn mit ein und die Regel `.epk-ruhig` selbst gaelte als
    Fokus-Regel. Das ist genau die Krankheit aus `_hilfen`: ein Riegel, der den
    Kommentar mitmisst.
    """
    aus = []
    for m in re.finditer(r"([^{}]*\.epk-ruhig[^{}]*)\{([^{}]*)\}",
                         nur_code(index_html)):
        aus.append((m.group(1).strip(), m.group(2).strip()))
    return aus


def _deklarationen(rumpf):
    """Rumpf -> Liste von Eigenschaftsnamen, kleingeschrieben."""
    namen = []
    for teil in rumpf.split(";"):
        if ":" in teil:
            namen.append(teil.split(":", 1)[0].strip().lower())
    return namen


# ══ Die Messung selbst ══════════════════════════════════════════════════════

def test_die_sechs_koepfe_sind_eindeutig(index_html):
    """Ohne das misst jede andere Aussage hier moeglicherweise die falsche
    Stelle - im Zweifel eine, die es zweimal gibt."""
    for name, kopf in list(_LEISE.items()) + list(_LAUT.items()):
        assert index_html.count(kopf) == 1, (
            "Der Kopf des Editors %s kommt %dx vor, erwartet genau 1x. "
            "Entweder ist er weg oder es gibt ihn doppelt - beides macht die "
            "uebrigen Riegel dieser Datei wertlos."
            % (name, index_html.count(kopf))
        )


def test_genau_vier_editoren_sind_gedaempft(index_html):
    """Eine Groesse, EINE Zahl. Vier gedaempfte Editoren - nicht drei (dann
    ist die Zeile noch laut) und nicht sechs (dann ist auch die Disposition
    verschwunden)."""
    code = nur_code(index_html)
    n = code.count('className: "epk-ruhig"')
    assert n == 4, (
        "Es tragen %d Zeilen-Editoren die Ruhe-Klasse, erwartet werden vier "
        "(Terminvorschlag, Status, Prioritaet, Sachbearbeiter)." % n
    )
    for name, kopf in _LEISE.items():
        assert kopf in index_html, (
            "Der Editor %s traegt die Ruhe-Klasse nicht (mehr)." % name
        )


def test_die_beiden_dispositionsfelder_bleiben_laut(index_html):
    """GEGENPROBE zur Zahl vier: sie allein wuerde nicht bemerken, dass die
    Klasse am FALSCHEN Editor sitzt. Wer disponiert, muss WER und WANN ohne
    Zielsuche treffen - diese zwei behalten ihren Rahmen."""
    for name, kopf in _LAUT.items():
        i = index_html.find(kopf)
        assert i != -1, "Der Editor %s ist nicht mehr auffindbar." % name
        assert "epk-ruhig" not in index_html[i:i + len(kopf) + 200], (
            "Der Editor %s ist gedaempft worden. Bestaetigter Termin und "
            "Monteur sind das Paar, das das Dispo-Brett in EINEM updAs-Aufruf "
            "schreibt - sie bleiben sichtbar bedienbar." % name
        )


def test_der_rahmen_kommt_beim_zeigen_zurueck(index_html):
    """DIE eigentliche Gefahr dieser Version: ein Bedienelement ohne Rahmen,
    das nie wieder einen bekommt, ist unauffindbar. Gemessen wird nicht, dass
    eine Regel existiert, sondern dass es BEIDE Zustaende gibt - Ruhe und
    Rueckkehr - und dass die Rueckkehr die Farbe des Elements nimmt."""
    regeln = _regeln(index_html)
    assert regeln, "Es gibt keine einzige CSS-Regel zur Ruhe-Klasse."

    ruhe = [(s, r) for s, r in regeln
            if ":hover" not in s and ":focus" not in s and "::" not in s]
    zeigen = [(s, r) for s, r in regeln if ":hover" in s and "::" not in s]

    assert ruhe, "Die Ruhe-Regel fehlt - dann ist gar nichts gedaempft."
    assert zeigen, (
        "Es gibt KEINE :hover-Regel zur Ruhe-Klasse. Vier Bedienelemente je "
        "Zeile waeren damit dauerhaft rahmenlos - unsichtbar bedienbar."
    )

    assert any("transparent" in r for _, r in ruhe), (
        "Die Ruhe-Regel macht den Rahmen nicht durchsichtig - dann daempft "
        "sie nichts."
    )
    assert any("currentcolor" in r.lower() for _, r in zeigen), (
        "Der zurueckkehrende Rahmen nimmt nicht currentColor. Status und "
        "Prioritaet faerben ihren Rahmen aus dem Wert (st.c / pri.c); eine "
        "feste Farbe hier waere dieselbe Groesse an zwei Stellen."
    )


def test_die_letzte_bedienbarkeitsanzeige_bleibt(index_html):
    """Der Pfeil am Auswahlfeld und das Kalendersymbol am Datumsfeld sind das
    Einzige, was nach dem Wegnehmen des Rahmens noch zeigt, DASS die Zelle
    bedienbar ist. Wer beides nimmt, hat die Zeile nicht beruhigt, sondern vier
    Bedienelemente je Zeile versteckt - derselbe Fehler wie oben, nur eine
    Stufe frueher. (Der erste Entwurf dieser Version blendete das
    Kalendersymbol im Ruhezustand aus; genau deshalb steht dieser Riegel hier.)
    """
    verboten = ("appearance", "-webkit-appearance", "-moz-appearance")
    for selektor, rumpf in _regeln(index_html):
        for eigenschaft in _deklarationen(rumpf):
            assert eigenschaft not in verboten, (
                "Die Regel '%s' setzt '%s' - das nimmt dem Auswahlfeld seinen "
                "Pfeil." % (selektor, eigenschaft)
            )
        assert "calendar-picker-indicator" not in selektor, (
            "Die Regel '%s' greift das Kalendersymbol des Datumsfelds an - das "
            "ist dessen letzter Hinweis auf Bedienbarkeit." % selektor
        )


def test_die_daempfung_faerbt_nichts_um(index_html):
    """Bei Status und Prioritaet IST die Farbe die Information (st.c, pri.c -
    dieselbe, die die Mobil-Karte als Chip zeigt). Diese Version darf den
    Rahmen wegnehmen und sonst nichts. Gemessen an den Eigenschaftsnamen, nicht
    am Wortlaut der Regel."""
    erlaubt = {"border-color"}
    for selektor, rumpf in _regeln(index_html):
        for eigenschaft in _deklarationen(rumpf):
            assert eigenschaft in erlaubt, (
                "Die Regel '%s' setzt '%s'. Erlaubt sind nur %s - alles andere "
                "aendert Aussehen oder Groesse des Werts selbst, und die Farbe "
                "des Status ist die Information."
                % (selektor, eigenschaft, sorted(erlaubt))
            )


def test_der_tastaturfokus_bleibt_der_akzentrahmen(index_html):
    """Wer mit der Tastatur arbeitet, hat kein Zeigen. Die bestehende Regel
    fuer den Fokus-Rahmen muss stehen bleiben, UND die Ruhe-Klasse darf sie
    nicht ueberstimmen - sonst haette der Tastaturweg gar keinen Rahmen."""
    code = nur_code(index_html)
    treffer = [(s, r) for s, r in
               re.findall(r"([^{}]*)\{([^{}]*)\}", code)
               if "select:focus" in s and "border-color" in _deklarationen(r)]
    assert treffer, (
        "Es gibt keine CSS-Regel mehr, die 'select:focus' einen border-color "
        "gibt. Ohne sie haetten die vier gedaempften Editoren am Tastaturweg "
        "keinen sichtbaren Rahmen."
    )
    for selektor, rumpf in _regeln(index_html):
        if ":focus" in selektor and "::" not in selektor:
            assert "border-color" not in _deklarationen(rumpf), (
                "Die Regel '%s' setzt border-color im Fokus. Sie ist "
                "spezifischer als 'select:focus' und wuerde den Akzentrahmen "
                "verdraengen." % selektor
            )


def test_kein_schreibweg_wurde_angefasst(index_html):
    """Der Kern der Abgrenzung: diese Version aendert die BEDIENDICHTE. Vier
    der sechs Wege schreiben nach OFFA - haette sich einer verschoben, waere
    das keine Aufraeumarbeit mehr."""
    for weg in _SCHREIBWEGE:
        assert weg in index_html, (
            "Der Schreibweg %s ist nicht mehr da. Diese Version durfte "
            "ausschliesslich Rahmen wegnehmen." % weg
        )


def test_die_mobil_karte_bleibt_unberuehrt(index_html):
    """GEGENPROBE zum Geltungsbereich: die Ueberladung ist ein Rechner-Problem
    (die Mobil-Karte hat keinen einzigen Zeilen-Editor). Landet die Klasse
    dort, wurde am falschen Zweig gearbeitet."""
    i = index_html.find('isMob&&React.createElement(\'div\', { style: '
                        '{display:"flex",flexDirection:"column",gap:8}}')
    assert i != -1, "Der Mobil-Kartenzweig ist nicht mehr auffindbar."
    j = index_html.find("!isMob&&React.createElement('div', { style: "
                        "{...CC(),padding:0,overflow:\"hidden\"}}", i)
    assert j != -1, "Der Rechner-Tabellenzweig ist nicht mehr auffindbar."
    assert "epk-ruhig" not in index_html[i:j], (
        "Die Ruhe-Klasse steht im Mobil-Kartenzweig. Dort gibt es keine "
        "Zeilen-Editoren zu daempfen - die Werte sind schon Chips."
    )


# ══ Umkehrprobe ═════════════════════════════════════════════════════════════

def test_selbsttest_riegel_schlagen_beim_rueckbau_an(index_html):
    # 1. Ein Editor verliert die Klasse -> die Zahl vier muss auffallen.
    z1 = index_html.replace('className: "epk-ruhig", ', "", 1)
    assert z1 != index_html, "Rueckbau 1 griff nicht"
    assert nur_code(z1).count('className: "epk-ruhig"') == 3, (
        "Umkehrprobe: der Zaehl-Riegel wuerde einen fehlenden Editor nicht "
        "bemerken."
    )

    # 2. Die Klasse wandert an den Monteur -> der Laut-Riegel muss anschlagen.
    #    v3.9.919 NACHGEZOGEN: der Rueckbau suchte den Kopf samt ", onChange:" und
    #    griff nicht mehr, als das Feld ein title bekam - das steht zwischen
    #    value und onChange. Der Selbsttest meldete dann "Rueckbau griff nicht",
    #    also immerhin laut. Waere er still durchgelaufen, haette der
    #    Laut-Riegel ab sofort GAR NICHTS mehr belegt - ein Selbsttest, der
    #    nicht mehr greift, ist schlimmer als keiner.
    _kopf = ('React.createElement(' + chr(39) + 'select' + chr(39) + ', { value: a.monteur||' + chr(34)*2 + ',')
    assert index_html.count(_kopf) == 1, (
        'Der Monteur-Editor ist nicht mehr eindeutig zu finden (%dx) - '
        'dieser Selbsttest misst dann nichts.' % index_html.count(_kopf))
    _gedaempft = ('React.createElement(' + chr(39) + 'select' + chr(39) + ', { className: ' + chr(34) + 'epk-ruhig' + chr(34) + ', '
                  'value: a.monteur||' + chr(34)*2 + ',')
    z2 = index_html.replace(_kopf, _gedaempft, 1)
    assert z2 != index_html, 'Rueckbau 2 griff nicht'
    i = z2.find(_gedaempft)
    assert i != -1 and 'epk-ruhig' in z2[i:i + 260], (
        'Umkehrprobe: der Laut-Riegel wuerde eine Daempfung am Monteur nicht '
        'bemerken.'
    )

    # 3. Die :hover-Regel faellt weg -> der gefaehrlichste Fall (rahmenlos fuer
    #    immer) muss auffallen.
    zeigen = [s for s, _ in _regeln(index_html)
              if ":hover" in s and "::" not in s]
    assert zeigen, "Vorbedingung: es gibt eine :hover-Regel"
    z3 = re.sub(r"[^{}]*\.epk-ruhig:hover(?![:a-zA-Z-])[^{}]*\{[^{}]*\}",
                "", index_html, count=1)
    assert z3 != index_html, "Rueckbau 3 griff nicht"
    assert not [s for s, _ in _regeln(z3)
                if ":hover" in s and "::" not in s], (
        "Umkehrprobe: der Rueckkehr-Riegel wuerde eine fehlende :hover-Regel "
        "nicht bemerken - und genau das waere der unbedienbare Zustand."
    )

    # 4. Ein Schreibweg verschiebt sich -> der Abgrenzungs-Riegel muss rot.
    z4 = index_html.replace("updAs(a.id,{prioritaet:e.target.value})",
                            "updAs(a.id,{prioritaet:_x})", 1)
    assert z4 != index_html, "Rueckbau 4 griff nicht"
    assert "updAs(a.id,{prioritaet:e.target.value})" not in z4, (
        "Umkehrprobe: der Schreibweg-Riegel wuerde eine Verschiebung nicht "
        "bemerken."
    )
