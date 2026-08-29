"""v3.9.697 — Die FinkZeit-Differenz ist kein Fehlerzustand mehr (Freigabe Sebastian, Frage 2).

WAS DIE WARNUNG TAT:
Sie verglich `time_entries` (= PROJEKTZEIT, was auf Projekte gebucht wurde) mit den händisch aus
dem FinkZeit-PDF übertragenen Stunden (= ANWESENHEIT) und meldete ab 1 h Abweichung orange
"Abgleich prüfen". Die KPI-Kachel färbte sich zusätzlich ROT.

WARUM DAS FALSCH WAR:
Nach dem Zwei-Domänen-Entscheid (Sebastian, 14.07.) ist genau diese Abweichung NORMAL — die
beiden Zahlen messen Verschiedenes. Unverbuchte Fahrt-, Werkstatt- und Verwaltungszeit fehlt in
`time_entries`. Das ist kein Buchungsfehler, das ist die Definition. Eine App, die darüber rot
schreit, behauptet einen Fehler, den es nicht gibt — und trainiert dem Büro an, Warnungen zu
ignorieren.

WAS BLEIBT:
Die ZAHL bleibt sichtbar (das Büro will die Differenz sehen), nur der Alarm ist weg. Exakt so,
wie die Projektzeit-Spalte neutral neben dem Stempel-Netto in der PZE-Ansicht steht.
Offene Abrechnungen bleiben gelb — DAS ist echte Arbeit, die liegenbleibt.
"""
import re


def _alert_zeile(index_html):
    m = re.search(r"if\(FINKZEIT_ENABLED&&finkStats\.diffWarn>0&&isAdmin\)alerts\.push\(\{.*?\}\);", index_html, re.S)
    assert m, "FinkZeit-Alert nicht gefunden"
    return m.group(0)


def test_alert_ist_info_kein_warning(index_html):
    zeile = _alert_zeile(index_html)
    assert 'type:"info"' in zeile
    assert 'type:"warning"' not in zeile


def test_alert_hat_kein_alarm_styling(index_html):
    zeile = _alert_zeile(index_html)
    assert "⚠️" not in zeile, "Das Warndreieck behauptet einen Fehler, den es nicht gibt."
    assert "#f97316" not in zeile, "Orange ist Alarmfarbe — die Differenz ist normal."


def test_alert_erklaert_statt_zu_mahnen(index_html):
    zeile = _alert_zeile(index_html)
    assert "Abgleich prüfen" not in zeile, "Es gibt nichts zu prüfen — die Abweichung ist erwartet."
    assert "messen Verschiedenes" in zeile


def test_kpi_kachel_faerbt_sich_nicht_mehr_rot(index_html):
    """Die Kachel darf bei einer Differenz NICHT mehr rot werden. Gelb bei OFFENEN
    Abrechnungen bleibt — das ist liegengebliebene Arbeit und damit ein echter Hinweis."""
    # v3.9.909 NACHGEZOGEN: der Anker war die exakte SCHREIBWEISE der Argumente
    #     finkStats.abgeglichen, "/", finkStats.total
    # Seit die Kachel bei ungemessenen Daten drei Punkte zeigt, setzt sie den
    # Wert als EINE Zeichenkette zusammen - der Riegel wurde rot, obwohl seine
    # Aussage (keine rote Faerbung bei Differenz) unveraendert erfuellt ist.
    # Verankert jetzt an der Kachel selbst, nicht an ihrer Argumentform.
    i = index_html.find("finkStats.abgeglichen")
    assert i != -1, "Monatsabrechnungs-Kachel nicht gefunden"
    umfeld = index_html[max(0, i - 400):i + 500]
    assert "diffWarn>0?COLORS.ERROR" not in umfeld, \
        "Die Kachel faerbt sich bei einer Differenz weiterhin rot — das behauptet einen Fehler."
    assert "finkStats.offen>0?COLORS.WARNING" in umfeld, \
        "Offene Abrechnungen sollen weiterhin gelb bleiben (echte liegengebliebene Arbeit)."
