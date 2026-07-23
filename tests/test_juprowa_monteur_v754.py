# -*- coding: utf-8 -*-
"""v3.9.754 — Register #31f + #31c: Monteur-Code-Map (Kiener/Aliti) + Badge fuer nicht-uebertragbare Monteure.

Sebastian (Cloud-verifiziert): P026 = Kiener (worker mpxpwdhrht1b) in der Map (Push worker->P0xx + Pull
P0xx->worker). 31c: ein Schein mit Monteur OHNE Juprowa-Code zeigt ein Badge "⚠ Monteur nicht nach OFFA
uebertragbar". Push sendet NIE einen Fantasie-Code (Feld ausgelassen).

v3.9.820: P028 (Aliti, worker mqyxfca35x6i) ist STILLGELEGT — der Worker wurde in der App geloescht.
Die alte Erwartung "'P028':'mqyxfca35x6i' steht in der Map" ist damit bewusst obsolet.
"""


def test_map_hat_kiener_p028_stillgelegt(index_html):
    """P026 bleibt in der Map; P028 gehoert NICHT mehr rein (Map-Zeile auf einen geloeschten Worker
    wuerde beim Pull eine Zombie-Referenz schreiben), sondern in JUPROWA_RETIRED."""
    assert "'P026':'mpxpwdhrht1b'" in index_html, "P026->Kiener (mpxpwdhrht1b) fehlt in JUPROWA_WORKER_MAP"
    _a = index_html.index("const JUPROWA_WORKER_MAP={")
    _wmap = index_html[_a:index_html.index("};", _a)]
    assert "'P028'" not in _wmap, "P028 (Aliti) steht noch in JUPROWA_WORKER_MAP — Zombie-Worker-ID beim Pull"
    _r = index_html.index("const JUPROWA_RETIRED=")
    assert "'P028'" in index_html[_r:index_html.index("\n", _r)], "P028 fehlt in JUPROWA_RETIRED"


def test_push_laesst_monteur_ohne_code_aus(index_html):
    # Der Payload-Bau setzt AK_MONTEUR nur, wenn ein Code aufgeloest wurde (nie Fantasie-Code).
    i = index_html.index("if(schein.monteur){const code=_juprowaWorkerToCode(schein.monteur)")
    seg = index_html[i:i + 120]
    assert "if(code)json.AK_MONTEUR=code" in seg, "Push sendet einen Monteur-Code auch ohne Aufloesung (Fantasie-Code-Risiko)"


def test_uebertragbar_check_existiert(index_html):
    # 31c: eine Check-Funktion, ob der Monteur nach OFFA uebertragbar ist (Code vorhanden).
    assert "_dispoMonteurUebertragbar" in index_html, "kein Uebertragbarkeits-Check fuer das 31c-Badge"
    assert "nicht nach OFFA übertragbar" in index_html or "nicht nach OFFA uebertragbar" in index_html, "kein 31c-Badge-Text"
