# -*- coding: utf-8 -*-
"""v3.9.906 - Die Arbeitsschein-Liste zeigte jeden Filter zweimal.

GEMESSEN, bevor etwas geaendert wurde
─────────────────────────────────────
Der Listen-Schirm traegt: **6 Bedienelemente in der Kopfzeile** (Suche, Status,
Art, Monteur, Sachbearbeiter, Sortierung) und **6 Editoren je ZEILE**
(Terminvorschlag, bestaetigter Termin, Scheinstatus, Prioritaet,
Sachbearbeiter, Monteur). Bei dreissig Zeilen sind das 180 aktive
Bedienelemente auf einem Schirm.

Und die Kopfzeile hat eine Doppelung: unter den Auswahlfeldern steht bereits je
ein CHIP pro aktivem Filter, der ihn auch entfernen kann. Derselbe Zustand also
zweimal - einmal als Wert im Feld, einmal als Chip. Auf dem Handy kosten die
vier Felder damit Platz, ohne etwas zu zeigen, was nicht schon darunter steht.

WAS GEAENDERT WURDE - UND WAS AUSDRUECKLICH NICHT
─────────────────────────────────────────────────
Auf dem Handy sind die vier Felder hinter einem Knopf eingeklappt, der die Zahl
der aktiven Filter nennt. Auf dem RECHNER bleibt alles, wie es war: dort ist
Platz, und wer viel filtert, will die Felder sehen.

Geaendert wurde ausschliesslich die SICHTBARKEIT. Kein Zustand, kein Filter,
keine Logik, keine Zeile am Zeilen-Editor. Die sechs Editoren je Zeile bleiben,
wo sie sind - vier davon schreiben beim Aendern direkt nach OFFA
(`monteur`, `terminBestaetigt`, `prioritaet`, `scheinstatus`), und ob das so
bleiben soll, ist eine Entscheidung ueber den Arbeitsablauf des Bueros, keine
Aufraeumarbeit.

WIDERLEGT UND DESHALB NICHT GEBAUT
──────────────────────────────────
Verdacht: ein Mausrad ueber einem Auswahlfeld koennte dessen Wert aendern - in
einer scrollenden Liste waere das gefaehrlich, weil vier der Editoren nach OFFA
schreiben. Gemessen in beide Richtungen (ohne Fokus, mit Fokus, plus Gegenprobe
per Tastatur, dass das Feld ueberhaupt aenderbar ist): **das Rad aendert
nichts.** Kein Riegel gegen ein Nicht-Problem.
"""
from _hilfen import nur_code


def test_der_filterknopf_gibt_es_nur_auf_dem_handy(index_html):
    assert "isMob&&(()=>{const _n=(filterStatus!==" in index_html, (
        "Der Filter-Knopf ist weg oder nicht mehr an isMob gebunden - dann "
        "aendert sich der Rechner-Schirm mit, und das war nicht die Absicht."
    )


def test_der_knopf_nennt_die_zahl_der_aktiven_filter(index_html):
    """Ein Knopf, der nur 'Filter' sagt, verbirgt, DASS gefiltert wird - dann
    sucht jemand einen Schein, der da ist, und findet ihn nicht."""
    i = index_html.find("isMob&&(()=>{const _n=(filterStatus!==")
    assert i != -1
    block = index_html[i:i + 900]
    for feld in ("filterStatus", "filterArt", "filterMonteur", "filterSB"):
        assert feld in block, (
            "Der Zaehler am Filter-Knopf beruecksichtigt %s nicht - dann kann "
            "ein aktiver Filter unsichtbar bleiben." % feld
        )
    assert '_n?(" ("+_n+")"):""' in block, (
        "Die Zahl wird nicht angezeigt."
    )


def test_alle_vier_felder_haengen_an_derselben_bedingung(index_html):
    """Eine Groesse, EINE Bedingung. Vier Felder mit vier verschiedenen
    Sichtbarkeitsregeln waeren die naechste Stelle, an der etwas auseinander
    laeuft."""
    code = nur_code(index_html)
    assert code.count("(!isMob||_fltOffen)&&") == 4, (
        "Es haengen %d Felder an der Klappbedingung, erwartet werden vier "
        "(Status, Art, Monteur, Sachbearbeiter)."
        % code.count("(!isMob||_fltOffen)&&")
    )


def test_die_rechte_bleiben_unangetastet(index_html):
    """GEGENPROBE: Monteur- und Sachbearbeiter-Filter waren schon vorher nur
    fuer Verwalter sichtbar. Die Klappbedingung darf das nicht ersetzen,
    sondern nur ergaenzen - sonst saehe sie ploetzlich jeder."""
    for feld in ("filterMonteur", "filterSB"):
        assert ("isAdmin&&(!isMob||_fltOffen)&&React.createElement('select', "
                "{ value: " + feld) in index_html, (
            "Die Rechtebedingung isAdmin steht nicht mehr vor der "
            "Klappbedingung bei %s." % feld
        )


def test_die_chips_bleiben_die_zweite_haelfte(index_html):
    """Das Einklappen ist nur vertretbar, WEIL die Chips den aktiven Filter
    weiterhin zeigen und entfernen koennen. Fallen sie weg, ist der Filter auf
    dem Handy unsichtbar - dann muss auch das Einklappen zurueck."""
    assert 'chips.push({l:"Suche: \\""+search+"\\""' in index_html, (
        "Die Filter-Chips sind weg. Ohne sie darf die Filterleiste auf dem "
        "Handy nicht eingeklappt sein - der Nutzer saehe sonst nicht, dass "
        "gefiltert wird."
    )


def test_kein_zeilen_editor_wurde_angefasst(index_html):
    """GEGENPROBE zur Abgrenzung: die sechs Editoren je Zeile bleiben. Vier
    davon schreiben nach OFFA; sie anzufassen waere eine Entscheidung ueber den
    Arbeitsablauf, keine Aufraeumarbeit."""
    for kette in ("value: a.scheinstatus",
                  'value: a.prioritaet||"keine",',
                  'value: a.monteur||"",'):
        assert kette in index_html, (
            "Ein Zeilen-Editor hat sich veraendert (%s) - diese Version sollte "
            "ausschliesslich die Kopfzeile entlasten." % kette[:30]
        )


# ══ Umkehrprobe ═════════════════════════════════════════════════════════════

def test_selbsttest_riegel_schlagen_beim_rueckbau_an(index_html):
    z1 = index_html.replace("(!isMob||_fltOffen)&&", "", 1)
    assert z1 != index_html, "Rueckbau 1 griff nicht"
    assert nur_code(z1).count("(!isMob||_fltOffen)&&") == 3, (
        "Umkehrprobe: der Zaehl-Riegel wuerde ein fehlendes Feld nicht bemerken"
    )

    z2 = index_html.replace("isMob&&(()=>{const _n=(filterStatus!==",
                            "false&&(()=>{const _n=(filterStatus!==", 1)
    assert z2 != index_html, "Rueckbau 2 griff nicht"
    assert "isMob&&(()=>{const _n=(filterStatus!==" not in z2, (
        "Umkehrprobe: der Knopf-Riegel wuerde nicht anschlagen"
    )
