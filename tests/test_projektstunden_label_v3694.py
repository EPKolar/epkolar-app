"""v3.9.694 — Self-Service-Karte: Label "Arbeitszeit" -> "Projektstunden" (Frage 4, Freigabe Sebastian).

Warum das kein Kosmetik-Ticket ist:
Die Karte zeigt `time_entries` — also PROJEKTZEIT (was auf Projekte gebucht wurde). Unter dem alten
Label "Arbeitszeit" las der Monteur sie als seine ANWESENHEIT und verglich sie mit seinem Lohnzettel.
Genau diese Verwechslung soll der Zwei-Domaenen-Entscheid (Sebastian, 14.07.) verhindern:
  time_entries = PROJEKTZEIT   ·   stempel_log = ANWESENHEIT (PZE-Ansicht im Buero)
Eine Abweichung zwischen beiden ist NORMAL. Sie ist nur dann kein Aerger, wenn die Beschriftung
nicht das Falsche verspricht.

Der Test haelt die Umbenennung fest — und stellt sicher, dass niemand sie versehentlich
zurueckdreht, wenn er die Karte anfasst.
"""
import re


def _card(index_html):
    m = re.search(r"const _cardZeit=React\.createElement\(.*?\n    \);", index_html, re.S)
    if not m:
        # Fallback: ab der Deklaration die naechsten ~40 Zeilen
        i = index_html.find("const _cardZeit=")
        assert i > 0, "Self-Service-Zeitkarte (_cardZeit) nicht gefunden"
        return index_html[i:i + 4000]
    return m.group(0)


def test_karte_heisst_projektstunden(index_html):
    card = _card(index_html)
    assert '"Projektstunden "' in card, "Die Self-Service-Karte traegt nicht mehr das Label 'Projektstunden'"


def test_karte_heisst_nicht_mehr_arbeitszeit(index_html):
    """Regression: 'Arbeitszeit' darf als Titel dieser Karte nicht zurueckkommen.

    Achtung, bewusst nur auf DIESE Karte begrenzt: das Wort 'Arbeitszeit' ist an anderen Stellen
    voellig korrekt (KV-Regeln-Gruppe, Arbeitsschein-Feld, Stundenbestaetigungs-Formular) und wird
    hier NICHT angefasst.
    """
    card = _card(index_html)
    assert '"Arbeitszeit "' not in card


def test_nur_das_label_wurde_geaendert(index_html):
    """Keine Zahl, keine Berechnung, kein Datenpfad — die Karte rechnet unveraendert aus time_entries."""
    card = _card(index_html)
    for unveraendert in ("Stunden gesamt", "Jahres-Total", "Diese Woche", "Letzte Woche"):
        assert unveraendert in card, f"'{unveraendert}' fehlt — es wurde mehr als das Label geaendert"
