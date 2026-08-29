# -*- coding: utf-8 -*-
"""v3.9.908 - Eine harte Null, wo "nicht gemessen" gemeint war.

    const absThisWeek = (function(){ try{ ... return names.size; }
                                     catch(_){ return 0; } })();

Der Auffangzweig lieferte eine **0** - ununterscheidbar von "niemand ist diese
Woche abwesend". Direkt daneben, in derselben Zeile der Kachelreihe, kennt die
Nachbarkachel `nextWeekAbs` bereits **null** fuer *nicht gemessen*, und die
Anzeigefunktion `_metric` stellt das laengst als drei Punkte dar:

    (val===null||val===undefined) ? '…' : val

Die Null ist hier die gefaehrlichere Angabe. "Niemand abwesend" ist eine
Auskunft, nach der jemand HANDELT: der Chef plant die Woche mit voller
Mannschaft. "Die Rechnung ist fehlgeschlagen" ist keine Auskunft - und genau
das sollte auf dem Schirm stehen.

Dieselbe Krankheit wie bei den Urlaubsantraegen in v3.9.898. Dort hiess sie
"Alle bearbeitet", waehrend in Wahrheit nur nichts gemessen worden war; die
Lehre daraus stand schon im Handoff, diese Stelle war noch offen (7k #25).

Der Fix ist eine Zeile - null statt 0 - und braucht KEINE Aenderung an der
Anzeige, weil _metric den Fall seit jeher kennt. Das ist der eigentliche Punkt:
die Faehigkeit, Nichtwissen zu zeigen, war da; sie wurde nur nicht benutzt.
"""
from _hilfen import nur_code


def test_der_auffangzweig_meldet_nicht_gemessen(index_html):
    assert "});return names.size;}catch(_){return null;}})();" in index_html, (
        "Der Auffangzweig von absThisWeek liefert wieder eine harte Zahl. Eine "
        "0 heisst dort 'niemand ist abwesend' - danach plant jemand die Woche."
    )


def test_die_anzeige_kann_nichtwissen_darstellen(index_html):
    """Der Fix ist nur vertretbar, WEIL _metric null bereits als drei Punkte
    zeigt. Faellt das weg, stuende dort nichts oder 'null'."""
    assert "(val===null||val===undefined)?'…':val" in index_html, (
        "_metric stellt null nicht mehr als '…' dar - dann zeigt die Kachel "
        "bei einem Fehler gar nichts oder das Wort null."
    )


def test_die_nachbarkachel_bleibt_wie_sie_war(index_html):
    """GEGENPROBE: nextWeekAbs hat null von Anfang an richtig gemacht. Diese
    Version sollte die ANDERE Kachel nachziehen, nicht beide umbauen."""
    assert "_metric('Abwesend nächste Woche',nextWeekAbs?nextWeekAbs.length:null," in index_html, (
        "Die Nachbarkachel hat sich veraendert - sie war das Vorbild."
    )


def test_die_farbe_behauptet_nichts_bei_nichtwissen(index_html):
    """Bei null darf die Kachel nicht warnorange leuchten - das waere die
    umgekehrte Luege: ein Alarm ohne Messung."""
    assert "_metric('Abwesend diese Woche',absThisWeek,absThisWeek>0?'#f97316':V.dm)" in index_html, (
        "Die Farbgebung haengt nicht mehr an >0 - bei null (nicht gemessen) "
        "muss sie gedaempft bleiben, nicht warnen."
    )


def test_es_bleibt_bei_einer_quelle(index_html):
    """Eine Groesse, EINE Rechnung: absThisWeek wird an genau EINER Stelle
    berechnet.

    Erwartet werden DREI Vorkommen, nicht zwei: die Berechnung, der Wert in der
    Kachel, und die Farbbedingung daneben - die liest denselben Wert ein
    zweites Mal. Mein erster Entwurf pruefte auf zwei und wurde zu Recht rot.
    Das ist heute die dritte Fehlzaehlung dieser Art: die zweite Verwendung IM
    SELBEN Ausdruck zu uebersehen ist offenbar mein blinder Fleck, und ein
    Riegel, den man an die Zahl anpassen muss, ist besser als einer, der die
    Zahl gar nicht nennt."""
    code = nur_code(index_html)
    n = code.count("absThisWeek")
    assert n == 3, (
        "absThisWeek kommt %d mal im Code vor, erwartet werden drei "
        "(Berechnung, Wert in der Kachel, Farbbedingung)." % n
    )


# ══ Umkehrprobe ═════════════════════════════════════════════════════════════

def test_selbsttest_riegel_schlaegt_beim_rueckbau_an(index_html):
    z = index_html.replace("});return names.size;}catch(_){return null;}})();",
                           "});return names.size;}catch(_){return 0;}})();", 1)
    assert z != index_html, "Rueckbau griff nicht"
    assert "});return names.size;}catch(_){return null;}})();" not in z, (
        "Umkehrprobe: der Riegel wuerde die harte Null nicht bemerken"
    )
