# -*- coding: utf-8 -*-
"""
v3.9.874 - Teil C: Ausgetretene sind in Zuweisungs-Auswahlen nicht mehr waehlbar.

Der Auftrag vom 25.08. hatte Teil C ausdruecklich als REPORT angelegt
("Sebastian entscheidet danach, was drankommt"). Die Entscheidung ist gefallen,
das hier ist die Umsetzung.

18 Stellen: Arbeitsscheine (Tabellen-Zuordnung, Zeile, Neu-Formular), AdminPanel
Monteur-Zuordnung, Projekt-Kopf, Maengel (Zuweisen an / Verantw. / Bulk),
TicketDetail, QuickEditPin, VPlan-Neu-Ticket, Bautagebuch-Chips, Fahrzeug-Fahrer
(neu und bestehend), Werkzeuge (Scan-Ausgabe, Zuweisung, Checkout, Zugewiesen an).

ZWEI BEWUSSTE GRENZEN - beide sind hier festgeschrieben, weil ein spaeterer
"Aufraeumer" sie sonst wegoptimiert:

1. Ein BEREITS ZUGEWIESENER Ausgetretener bleibt in SEINER Liste sichtbar.
   Sonst verschwaende die bestehende Zuweisung stillschweigend aus dem Feld -
   und der naechste Speichern-Klick wuerde sie loeschen. Das waere Datenverlust
   durch eine reine Anzeige-Aenderung.

2. FILTER- und REPORT-Listen bleiben VOLLSTAENDIG: Monteur-Filter und
   Kalender-Auswahl in den Arbeitsscheinen, der Maengel-Filter und der
   KV-Zulagen-Report. Wer die alten Scheine eines Ausgetretenen sucht, muss ihn
   dort weiter auswaehlen koennen - sonst wird Historie unauffindbar.

Kein Loeschen, keine workers-Daten angefasst, kein DB-Write.
"""
import re


def _helfer(index_html):
    m = re.search(r"function _maWaehlbar\(liste,aktuell\)\{.*?\n\}", index_html, re.S)
    assert m, "_maWaehlbar fehlt - dann ist Teil C zurueckgebaut."
    return m.group(0)


def test_helfer_nutzt_das_bestehende_praedikat(index_html):
    """KEINE neue Datumslogik - das war eine ausdrueckliche Auflage des Auftrags."""
    body = _helfer(index_html)
    assert "_maIstEhemalig(m,h)" in body, (
        "Der Helfer rechnet nicht mehr ueber _maIstEhemalig - zwei Quellen fuer "
        "dieselbe Frage:\n" + body
    )
    assert "_ezHeuteISO()" in body, "Wiener Datum via _ezHeuteISO fehlt:\n" + body


def test_bereits_zugewiesener_bleibt_sichtbar(index_html):
    """Grenze 1. Faellt sie weg, loescht der naechste Speichern-Klick eine
    bestehende Zuweisung."""
    body = _helfer(index_html)
    assert "String(m.id)===String(aktuell)" in body, (
        "Der aktuell zugewiesene Worker wird nicht mehr durchgelassen - eine "
        "bestehende Zuweisung an einen Ausgetretenen verschwaende aus dem Feld:\n" + body
    )
    assert "!_maIstEhemalig(m,h) ||" in body, (
        "Die Ausnahme haengt nicht mehr am ODER - dann waere entweder alles oder "
        "nichts sichtbar:\n" + body
    )


def test_alle_zuweisungs_stellen_umgestellt(index_html):
    """18 Callsites + 1 Definition. Kommt eine Zuweisung dazu, muss sie hier
    auftauchen - sonst schleicht sich eine ungefilterte Stelle ein."""
    # Der Versions-Kommentar erwaehnt den Helfer im Fliesstext - der zaehlt nicht mit.
    zeilen = [l for l in index_html.splitlines() if not l.startswith("const APP_VERSION=")]
    n = len(re.findall(r"_maWaehlbar\(", "\n".join(zeilen)))
    assert n == 19, (
        "Erwartet 1 Definition + 18 Zuweisungs-Auswahlen = 19 '_maWaehlbar('; "
        "gefunden %d. Neue Zuweisung dazugekommen oder eine entfernt?" % n
    )


def test_filter_und_report_listen_bleiben_vollstaendig(index_html):
    """Grenze 2. Diese vier duerfen NICHT gefiltert werden."""
    unveraendert = [
        ("filterMonteur", "Monteur-Filter der Arbeitsscheine"),
        ("calMonteur", "Kalender-Auswahl der Arbeitsscheine"),
        ("fWorker", "Maengel-Filter"),
    ]
    for var, was in unveraendert:
        m = re.search(r"value: " + var + r",.{0,400}", index_html, re.S)
        assert m, "Anker fuer %s (%s) nicht gefunden" % (var, was)
        assert "_maWaehlbar" not in m.group(0), (
            "%s (%s) wird gefiltert - dann sind die alten Eintraege eines "
            "Ausgetretenen dort nicht mehr auffindbar." % (var, was)
        )


def test_kein_schreibzugriff_im_neuen_code(index_html):
    """Der Auftrag verbietet Loeschen und jede Aenderung an workers-Daten."""
    body = _helfer(index_html)
    for verboten in ("setMonteure", "_sbDelete", "DELETE", "_sbUpsert"):
        assert verboten not in body, (
            "Im Auswahl-Helfer steht '%s' - hier wird nur gefiltert." % verboten
        )


def test_praedikat_und_helfer_liegen_beieinander(index_html):
    """Beide auf Modulebene, damit jede Ansicht dieselbe Antwort bekommt."""
    i_pred = index_html.find("function _maIstEhemalig(m,heute){")
    i_help = index_html.find("function _maWaehlbar(liste,aktuell){")
    assert i_pred != -1 and i_help != -1, "Einer der beiden Helfer fehlt"
    assert abs(i_pred - i_help) < 4000, (
        "Praedikat und Auswahl-Helfer sind auseinandergewandert - sie gehoeren "
        "zusammen gelesen."
    )


def test_selbsttest_riegel_schlaegt_beim_rueckbau_an(index_html):
    ohne_ausnahme = index_html.replace(
        "return !_maIstEhemalig(m,h) || (aktuell && m && String(m.id)===String(aktuell));",
        "return !_maIstEhemalig(m,h);", 1)
    assert ohne_ausnahme != index_html, "Rueckbau griff nicht - Anker veraltet"
    assert "String(m.id)===String(aktuell)" not in _helfer(ohne_ausnahme), (
        "Umkehrprobe: der Riegel fuer bestehende Zuweisungen wuerde nicht anschlagen"
    )
