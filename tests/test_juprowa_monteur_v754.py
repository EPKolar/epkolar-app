# -*- coding: utf-8 -*-
"""v3.9.754 — Register #31f + #31c: Monteur-Code-Map (Kiener/Aliti) + Badge fuer nicht-uebertragbare Monteure.

Sebastian (Cloud-verifiziert): P026 = Kiener (worker mpxpwdhrht1b), P028 = Aliti (worker mqyxfca35x6i) — beide
Codes in die Map (Push worker->P0xx + Pull P0xx->worker). 31c: ein Schein mit Monteur OHNE Juprowa-Code zeigt
ein Badge "⚠ Monteur nicht nach OFFA uebertragbar". Push sendet NIE einen Fantasie-Code (Feld ausgelassen).
"""


def test_map_hat_kiener_aliti(index_html):
    assert "'P026':'mpxpwdhrht1b'" in index_html, "P026->Kiener (mpxpwdhrht1b) fehlt in JUPROWA_WORKER_MAP"
    assert "'P028':'mqyxfca35x6i'" in index_html, "P028->Aliti (mqyxfca35x6i) fehlt in JUPROWA_WORKER_MAP"


def test_push_laesst_monteur_ohne_code_aus(index_html):
    # Der Payload-Bau setzt AK_MONTEUR nur, wenn ein Code aufgeloest wurde (nie Fantasie-Code).
    i = index_html.index("if(schein.monteur){const code=_juprowaWorkerToCode(schein.monteur)")
    seg = index_html[i:i + 120]
    assert "if(code)json.AK_MONTEUR=code" in seg, "Push sendet einen Monteur-Code auch ohne Aufloesung (Fantasie-Code-Risiko)"


def test_uebertragbar_check_existiert(index_html):
    # 31c: eine Check-Funktion, ob der Monteur nach OFFA uebertragbar ist (Code vorhanden).
    assert "_dispoMonteurUebertragbar" in index_html, "kein Uebertragbarkeits-Check fuer das 31c-Badge"
    assert "nicht nach OFFA übertragbar" in index_html or "nicht nach OFFA uebertragbar" in index_html, "kein 31c-Badge-Text"
