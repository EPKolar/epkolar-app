"""v3.9.648 KV-V2 — kontingent.urlaub (Tage) sanft stillgelegt.

Resturlaub laeuft ausschliesslich in Stunden (_resturlaubK). Save serialisiert das
Feld nicht mehr, Load uebernimmt es nicht mehr; DB-Spalte bleibt (kein DDL).
Das lebendige Verbrauchs-Aggregat (_absStats.urlaub / yearSt-urlaubStd*) bleibt.
"""


def test_save_payload_ohne_urlaub(index_html):
    # Der urlaubskontingent-POST-Body serialisiert kontingent.urlaub NICHT mehr
    assert "urlaub:ks.urlaub" not in index_html


def test_load_uebernimmt_kein_urlaub(index_html):
    # Load-Map liest k.urlaub nicht mehr -> Row ohne Spalte crasht nicht
    assert "urlaub:parseInt(k.urlaub)" not in index_html


def test_deprecation_kommentar(index_html):
    assert "urlaub-Spalte DEPRECATED seit v3.9.647" in index_html


def test_resturlaub_nutzt_stunden(index_html):
    """Einzige Wahrheit: _resturlaubK rechnet mit stunden + vorjahr - Verbrauch.

    🔴 DER ZEUGE IST AM 30.09.2026 GETAUSCHT WORDEN, DER ZWECK NICHT.
    Hier stand woertlich `(ks.stunden||192.5)+(ks.vorjahr||0)-ys.urlaubStdGen`.
    Diese Form ist in v3.9.992 gekurt worden: `x||192.5` liest die **0 als
    FEHLEND** - sie ist in JavaScript falsy -, und damit wurde ein
    ausdruecklich eingetragener Anspruch von 0 Stunden als 192,5 angezeigt;
    der Resturlaub stand auf 192,5 statt 0. Jetzt steht dort
    `_ktgStd(ks.stunden)`, das nur bei `null`, `undefined`, Leertext oder
    einem unlesbaren Wert auf 192,5 zurueckfaellt.

    Der ZWECK bleibt unveraendert: die Rechnung geht ueber **stunden** (nicht
    ueber die seit v3.9.647 veraltete Tages-Spalte `urlaub`), plus Vorjahr,
    minus Verbrauch. Genau das wird unten geprueft - nur nicht mehr an einer
    Zeichenkette, die eine bekannte Fehlerform festnagelt.
    """
    assert "function _resturlaubK(abs,approvals,kontingent,m,yr){" in index_html
    assert "_ktgStd(ks.stunden)+(ks.vorjahr||0)-ys.urlaubStdGen" in index_html, (
        "Die Resturlaubs-Rechnung hat ihre Form geaendert.\n"
        "  Verlangt ist: aus `stunden` (ueber `_ktgStd`, damit eine 0 eine 0 "
        "bleibt), plus\n  `vorjahr`, minus `urlaubStdGen`. Die veraltete "
        "Tages-Spalte `urlaub` darf hier\n  NICHT wieder auftauchen.")
    # 🔴 Und die Gegenrichtung, damit der Riegel nicht dadurch gruen bleibt,
    #    dass jemand zur falsy-Form zurueckkehrt.
    assert "ks.stunden||192.5" not in index_html, (
        "Die alte Form `ks.stunden||192.5` ist zurueck. Damit gilt ein "
        "Anspruch von 0\n  Stunden wieder als fehlend und wird als 192,5 "
        "angezeigt.")


def test_lebendiges_aggregat_unangetastet(index_html):
    # _absStats.urlaub (Verbrauchs-Tage aus absences) bleibt erhalten
    assert "s.urlaub+=dayUnit" in index_html
    assert "urlaubStdGen" in index_html
