# -*- coding: utf-8 -*-
"""v3.9.895 - Ein abgelehnter Mangel verschwand, und eine berechnete Zahl wurde nie gezeigt.

────────────────────────────────────────────────────────────────────────────
1 - Abgelehnte Kundenmeldungen waren unauffindbar
────────────────────────────────────────────────────────────────────────────
Die Kundenmeldungs-Triage schreibt bei einer Ablehnung:

    SQ.push({... body:{status:"abgelehnt", kunde_status:"abgelehnt",
                       review_note:reviewNote}});

Gerendert und gefiltert wurde die Maengelliste aber ueber `MANGEL_ST` - und da
steht nur `["offen","in Behebung","behoben"]`. Ein abgelehnter Mangel fiel damit
durch alle drei Gruppen und war **in der Liste nicht mehr vorhanden**.

Der Ablauf, den das kaputt macht: der Kunde meldet etwas ueber das Portal, das
Buero lehnt ab und vermerkt einen Grund - und danach ist der Vorgang weg. Weder
die Entscheidung nachlesbar noch zuruecknehmbar.

FIX mit einer bewussten Trennung:
  `MANGEL_ST`        die Zustaende, die man ueber die Statuszeile direkt SETZEN
                     kann - "abgelehnt" gehoert nicht dazu, dafuer gibt es den
                     Triage-Weg mit Begruendung
  `MANGEL_ST_SICHT`  was ANGEZEIGT und gefiltert wird - inklusive "abgelehnt"

Umgekehrt geht es weiterhin: bei einem abgelehnten Mangel ist kein Chip aktiv,
ein Klick auf "offen" holt ihn zurueck. Genau die Richtung, die man braucht.

Und die Farbe ist NEUTRAL, nicht gruen: mit der Erledigt-Farbe saehe eine
abgelehnte Kundenmeldung aus wie ein behobener Mangel.

────────────────────────────────────────────────────────────────────────────
2 - `allTickets` wurde in HomeView berechnet und nie benutzt
────────────────────────────────────────────────────────────────────────────
Eine Zeile, die eine Liste aufbaut, und danach kein einziger Zugriff. Die
Projektkachel zeigte die Zahl der Plaene, aber nicht, ob auf ihnen etwas offen
ist - ein Monteur auf drei Baustellen sah nirgends, wo noch Arbeit liegt.

Dieselbe Fehlerklasse wie `_konfCount` (v888) und das `geschaetzt`-Flag (v892):
berechnet, nie gelesen. Sie ist in dieser Datei inzwischen dreimal aufgetreten.
"""


# ══ 1 - Abgelehnte Maengel ══════════════════════════════════════════════════

def test_es_gibt_eine_eigene_anzeige_liste(index_html):
    assert 'const MANGEL_ST_SICHT=MANGEL_ST.concat(["abgelehnt"]);' in index_html, (
        "MANGEL_ST_SICHT fehlt - dann faellt ein abgelehnter Mangel wieder durch "
        "alle Gruppen und ist in der Liste nicht mehr auffindbar."
    )


def test_die_setzbare_liste_bleibt_eng(index_html):
    """Bewusste Grenze: 'abgelehnt' darf man nicht ueber die Statuszeile setzen -
    dafuer gibt es den Triage-Weg, der eine Begruendung verlangt."""
    assert 'const MANGEL_ST=["offen","in Behebung","behoben"];' in index_html, (
        "MANGEL_ST wurde erweitert - dann kann man einen Mangel ohne Begruendung "
        "auf 'abgelehnt' setzen und umgeht die Triage."
    )


def test_gruppen_und_filter_zeigen_abgelehnte(index_html):
    assert '["alle"].concat(MANGEL_ST_SICHT)' in index_html, (
        "Die Filter-Chips zeigen 'abgelehnt' nicht - man kann dann nicht gezielt "
        "nachsehen, was abgelehnt wurde."
    )
    assert ", MANGEL_ST_SICHT.map(st=>{" in index_html, (
        "Die Gruppen-Darstellung zeigt abgelehnte Maengel nicht."
    )


def test_abgelehnt_ist_nicht_gruen(index_html):
    """Mit der Erledigt-Farbe saehe eine abgelehnte Kundenmeldung aus wie ein
    behobener Mangel - das ist eine Aussage, keine Kosmetik."""
    assert 'st==="abgelehnt"?V.dm:COLORS.SUCCESS' in index_html, (
        "Die Gruppenfarbe fuer 'abgelehnt' ist nicht neutral."
    )
    assert 's==="abgelehnt"?V.dm:COLORS.SUCCESS' in index_html, (
        "Die Chip-Farbe fuer 'abgelehnt' ist nicht neutral."
    )


def test_der_triage_weg_ist_unveraendert(index_html):
    """Gegenprobe: der Schreibpfad wurde NICHT angefasst - nur die Anzeige."""
    assert 'body:{status:"abgelehnt",kunde_status:"abgelehnt",review_note:reviewNote}' in index_html, (
        "Der Ablehnungs-Schreibpfad hat sich veraendert. Ziel war, das Ergebnis "
        "sichtbar zu machen - nicht, das Schreiben zu aendern."
    )


# ══ 2 - Offene Pins auf der Projektkachel ═══════════════════════════════════

def test_die_berechnete_ticketliste_wird_benutzt(index_html):
    assert "const prOffeneTickets=allTickets.filter(function(t){return t&&t.pid===pr.id" in index_html, (
        "allTickets wird wieder berechnet und nicht benutzt - die Projektkachel "
        "zeigt dann nicht, ob auf den Plaenen etwas offen ist."
    )


def test_die_zustaende_kommen_nicht_aus_einer_zweiten_liste(index_html):
    """Wichtig: 'zu' wird an EINER Stelle definiert. Eine zweite Liste waere die
    naechste Groesse mit zwei Wahrheiten - genau das Muster, das v886/v888/v891
    in dieser Datei aufgeraeumt haben."""
    i = index_html.find("const prOffeneTickets=")
    assert i != -1, "prOffeneTickets nicht gefunden"
    block = index_html[i:i + 320]
    assert '["erledigt","abgenommen","abgeschlossen","storniert"].indexOf(t.status)<0' in block, (
        "Die Abgrenzung 'offen vs. zu' hat sich veraendert - sie muss dieselben "
        "Zustaende meinen wie TICKET_STATUS:\n" + block[:220]
    )


def test_die_zahl_erscheint_nur_wenn_es_etwas_gibt(index_html):
    """Eine dauerhafte 0 neben jeder Planzahl waere Rauschen."""
    assert "prOffeneTickets>0?React.createElement('span'" in index_html, (
        "Die Pin-Zahl haengt nicht an >0."
    )
    assert 'prOffeneTickets>0?(", "+prOffeneTickets+" offene Pins")' in index_html, (
        "Der Hinweistext nennt die offenen Pins nicht."
    )


# ══ Umkehrprobe ═════════════════════════════════════════════════════════════

def test_selbsttest_riegel_schlagen_beim_rueckbau_an(index_html):
    z1 = index_html.replace(", MANGEL_ST_SICHT.map(st=>{", ", MANGEL_ST.map(st=>{", 1)
    assert z1 != index_html, "Rueckbau 1 griff nicht"
    assert ", MANGEL_ST_SICHT.map(st=>{" not in z1, (
        "Umkehrprobe: der Gruppen-Riegel wuerde nicht anschlagen"
    )

    z2 = index_html.replace("prOffeneTickets>0?React.createElement('span'",
                            "false?React.createElement('span'", 1)
    assert z2 != index_html, "Rueckbau 2 griff nicht"
    assert "prOffeneTickets>0?React.createElement('span'" not in z2, (
        "Umkehrprobe: der Pin-Riegel wuerde nicht anschlagen"
    )
