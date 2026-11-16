# -*- coding: utf-8 -*-
"""v3.9.1026: Kennungs-Spalten (Kundennr., Inventar-Nr., Seriennr., Projektnr., PA-Nr., Entity-ID) als Text,
sonst macht Excel aus "00123" die Zahl 123. Gezaehlt 16.11.: 6 Kopfzeilen fielen an _XKENN vorbei."""
import re


def _rx(html):
    m = re.search(r"_XKENN=/([^/]+)/i", html)
    assert m
    return re.compile(m.group(1), re.I)


def test_kennungen_sind_text(index_html):
    rx = _rx(index_html)
    for h in ("KdNr", "Inventar-Nr", "Seriennr", "ProjNr", "PA-Nr", "Entity-ID", "Scheinnr.", "PLZ"):
        assert rx.search(h), h


def test_zahlen_bleiben_zahlen(index_html):
    rx = _rx(index_html)
    for h in ("Stunden", "Betrag", "Summe", "Nr", "Datum", "Menge", "EUR"):
        assert not rx.search(h), h


def test_umkehrprobe(index_html):
    kaputt = index_html.replace("|kdnr|kundennr", "", 1)
    assert not _rx(kaputt).search("KdNr")
