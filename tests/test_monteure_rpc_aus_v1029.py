# -*- coding: utf-8 -*-
"""v3.9.1029: die App rief rpc/juprowa_fetch_monteure auf - die Funktion existiert in der DB nicht
(Server-Log 16.11.: nur 404). Der Aufruf ist abgeschaltet; die Funktion bleibt fuer spaeter stehen."""
import re


def test_kein_aufruf_mehr(index_html):
    aufrufe = [m.start() for m in re.finditer(r"_juprowaFetchMonteure\(\)", index_html)]
    assert len(aufrufe) == 1, aufrufe          # nur noch die Definition
    assert "async function _juprowaFetchMonteure(){" in index_html


def test_umkehrprobe(index_html):
    kaputt = index_html.replace("Monteur-Zuordnung lernt", "_juprowaFetchMonteure(); lernt", 1)
    assert len(re.findall(r"_juprowaFetchMonteure\(\)", kaputt)) == 2
