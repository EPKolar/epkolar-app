# -*- coding: utf-8 -*-
"""v3.9.907 - Das Fenster "naechste Woche" liess den Sonntag aus.

    const _nextMonStart = ... d.getDate()+(8-day)   // Montag
    const _nextMonEnd   = ... d.getDate()+(14-day)  // SAMSTAG, exklusiv Sonntag

Zusammen mit dem halboffenen Vergleich (`dt<_nextMonEnd`) deckte das Fenster
Montag bis SAMSTAG - sechs Tage statt sieben. Der Kommentar daneben spricht
ausdruecklich von "nextMon..nextMon+7 (halbopen)".

Nachgerechnet, ausgehend vom Samstag 29.08.2026:

    Start           Mo 31.08.
    Ende (exkl)     So 06.09.      -> gedeckt: Mo 31.08. bis Sa 05.09.
    Sonntag 06.09.  faellt heraus

ZWEI Anzeigen lesen aus diesem Fenster:
  * die Kachel "Abwesend naechste Woche"
  * "Geplant naechste Woche" - seit v3.9.900 ueberhaupt erst sichtbar, vorher
    wurde sie berechnet und nie gezeigt

Warum das kein leerer Tag ist: die Dispo kennt eine eigene Tagesart fuer
Stoerungen, und ein Elektrobetrieb faehrt Stoerungsdienst auch sonntags. Ein
bestaetigter Sonntagstermin der kommenden Woche war in beiden Zahlen
unsichtbar - der Chef plant den Sonntag also gegen eine Null.

Der Fix ist +(15-day). Die Grenze bleibt HALBOFFEN: der Montag der
uebernaechsten Woche gehoert weiterhin nicht dazu, sonst waere er in zwei
Wochenfenstern.
"""
from _hilfen import nur_code


def test_das_fenster_reicht_bis_sonntag(index_html):
    assert ("const _nextMonEnd=(function(){const d=new Date();const day=d.getDay()||7;"
            "d.setDate(d.getDate()+(15-day));return _ymd(d);})();") in index_html, (
        "Das Fenster endet nicht mehr am Sonntag - dann sind "
        "Sonntagstermine und -abwesenheiten der kommenden Woche wieder "
        "unsichtbar."
    )


def test_der_start_bleibt_der_montag(index_html):
    """GEGENPROBE: nur das ENDE war falsch. Waere der Start mitverschoben,
    haette sich das Fenster um einen Tag verdreht, statt sich zu schliessen."""
    assert ("const _nextMonStart=(function(){const d=new Date();const day=d.getDay()||7;"
            "d.setDate(d.getDate()+(8-day));return _ymd(d);})();") in index_html, (
        "Der Start des Fensters hat sich veraendert - er muss der Montag der "
        "kommenden Woche bleiben."
    )


def test_die_grenze_bleibt_halboffen(index_html):
    """Mit `<=` waere der Montag der uebernaechsten Woche in ZWEI Fenstern -
    einmal hier, einmal in der Woche darauf. Genau die Doppelzaehlung, die im
    Fahrtenbuch (v3.9.897) Kilometergeld zweimal ausgewiesen hat."""
    for stelle in ("dt>=_nextMonStart&&dt<_nextMonEnd",
                   "t>=_nextMonStart&&t<_nextMonEnd"):
        assert stelle in index_html, (
            "Der Vergleich %r ist nicht mehr halboffen - dann zaehlt ein Tag "
            "in zwei Wochen." % stelle
        )


def test_beide_leser_teilen_dasselbe_fenster(index_html):
    """Eine Groesse, EINE Rechnung. Zwei Kacheln auf einem Schirm, die
    verschieden weit rechnen, waeren die naechste Stelle, an der sich zwei
    Zahlen widersprechen.

    KOMMENTARBLIND gezaehlt, und die erwartete Zahl ist VIER, nicht drei: die
    Definition, die zwei Lesestellen - und die Abhaengigkeitsliste des useMemo,
    die ebenfalls dazugehoert. Mein erster Entwurf hat auf drei geprueft und
    ist zu Recht rot geworden; dass ich die Deps-Liste vergessen hatte, hat die
    Umkehrprobe des Riegels selbst ans Licht gebracht."""
    code = nur_code(index_html)
    n = code.count("_nextMonEnd")
    assert n == 4, (
        "Erwartet: Definition + zwei Leser (Abwesend naechste Woche, Geplant "
        "naechste Woche) + die useMemo-Abhaengigkeit. Gefunden: %d." % n
    )
    assert "[arbeitsscheine,_nextMonStart,_nextMonEnd]" in code, (
        "Die useMemo-Abhaengigkeit fehlt - dann friert die Kachel 'Geplant "
        "naechste Woche' auf dem Fenster vom Seitenaufruf ein."
    )


# ══ Umkehrprobe ═════════════════════════════════════════════════════════════

def test_selbsttest_riegel_schlaegt_beim_rueckbau_an(index_html):
    z = index_html.replace("d.setDate(d.getDate()+(15-day));return _ymd(d);})();",
                           "d.setDate(d.getDate()+(14-day));return _ymd(d);})();", 1)
    assert z != index_html, "Rueckbau griff nicht"
    assert ("const _nextMonEnd=(function(){const d=new Date();const day=d.getDay()||7;"
            "d.setDate(d.getDate()+(15-day));return _ymd(d);})();") not in z, (
        "Umkehrprobe: der Riegel wuerde den alten Samstag-Schluss nicht bemerken"
    )
