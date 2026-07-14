"""v3.9.682 Zeiterfassung — Sonntag nur bei vorhandenen Eintraegen sichtbar.

Produktentscheid Sebastian: Sonntag ist kein Arbeitstag. Das Wochen-Grid ist Mo–Sa
(repeat(6,1fr)), der 7. Tag brach als einsame zweite Zeile um und stoerte optisch.

HARTE GRENZE — der v3.9.546-Schutz:
Sonntags-Eintraege duerfen NIE wieder unsichtbar werden. Das hier ist eine reine ANZEIGE-Regel:
  * DAYS bleibt intern 7-taegig (kein Rueckbau der Datenlogik)
  * ein Sonntag MIT Eintraegen oder Stunden wird IMMER gerendert — mit Warnakzent, damit er als
    Ausnahme lesbar ist und nicht als Normalfall
  * die Wochensumme zaehlt den Sonntag IMMER mit; es faellt nur die leere Spalte weg, nie ein Wert
  * Timer und Schreibpfade sind unberuehrt

Muster uebernommen von exportWochenStz (v3.9.661), das genau dieselbe Regel schon hat.
"""


def _ze_body(index_html):
    start = index_html.index("function ZeiterfassungView({")
    return index_html[start : start + 90000]


def test_days_bleibt_siebentaegig(index_html):
    # Kein Rueckbau der v3.9.546-Datenlogik. DAYS MUSS den Sonntag weiter enthalten.
    assert 'const DAYS=["Mo","Di","Mi","Do","Fr","Sa","So"];' in index_html, (
        "DAYS in ZeiterfassungView muss 7-taegig bleiben — sonst ist v3.9.546 rueckgaengig gemacht"
    )


def test_sonntagskarte_nur_bei_eintraegen(index_html):
    # Leerer Sonntag -> Karte faellt weg. Sonntag MIT Eintraegen ODER Stunden -> bleibt.
    assert "if(isSo&&arr.length===0&&!(dt>0))return null;" in _ze_body(index_html)


def test_sonntag_mit_eintraegen_bleibt_sichtbar(index_html):
    """Der Kern des v3.9.546-Schutzes: die Bedingung darf NUR bei leerem Sonntag greifen.

    Beide Fluchtwege sind gefordert — Eintraege (arr) UND Stunden (dt). Ein Sonntag mit
    Stunden, aber ohne geladene Eintragsliste, muss trotzdem erscheinen.
    """
    body = _ze_body(index_html)
    bed = "if(isSo&&arr.length===0&&!(dt>0))return null;"
    assert bed in body
    # Kein unbedingtes Ausblenden irgendwo — das waere exakt der v546-Bug.
    for verboten in (
        "if(isSo)return null;",
        "if(i===6)return null;",
        "DAYS.slice(0,6)",
        'const DAYS=["Mo","Di","Mi","Do","Fr","Sa"];/* ZE',
    ):
        assert verboten not in body, f"unbedingtes Ausblenden des Sonntags gefunden: {verboten}"


def test_sonntag_warnakzent(index_html):
    # Sichtbar als Ausnahme, nicht als Normalfall: oranger Rand + Tooltip.
    body = _ze_body(index_html)
    assert 'title:isSo?"Sonntags-Einträge vorhanden":undefined' in body
    assert '(isSo?"#f97316":V.bd)' in body


def test_summenleiste_sonntag_bedingt_aber_wochensumme_vollstaendig(index_html):
    body = _ze_body(index_html)
    # Spalte faellt bei 0h weg ...
    assert "if(isSo&&!(dt>0))return null;" in body
    # ... die Wochensumme bleibt aber unangetastet (kein Filter auf weekTotal).
    assert '"Σ Woche"' in body
    assert "_n(weekTotal,1)" in body
    assert "weekTotal" in body


def test_v3661_muster_unveraendert(index_html):
    # Die Vorlage (exportWochenStz) darf dabei nicht kaputtgehen.
    assert "if(i>=6&&dt===0&&arr.length===0)return;" in index_html
