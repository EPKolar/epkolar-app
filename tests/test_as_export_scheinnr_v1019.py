# -*- coding: utf-8 -*-
"""v3.9.1019 GF: Arbeitsschein-Excel ohne Scheinnummer - "muss unbedingt dazu".
Spalte 1 war die laufende Zeilennummer (i+1). Jetzt die Scheinnummer, als Text (Kennung, fuehrende Nullen)."""
import re


def _fn(src):
    i = src.index("const exportOffa=(statusFilter)=>{")
    return src[i:src.index("\n  };", i)]


def test_erste_spalte_ist_die_scheinnummer(index_html):
    fn = _fn(index_html)
    assert 'const hdrs=["Scheinnr.","KdNr","Kunde",' in fn
    assert 'const data=src.map((a,i)=>[String(a.nummer||""),a.kundNr,' in fn
    assert "[i+1,a.kundNr" not in fn


def test_scheinnummer_bleibt_text(index_html):
    m = re.search(r"_XKENN=/([^/]+)/i", index_html)
    assert m and re.search(m.group(1), "Scheinnr.", re.I)
    assert not re.search(m.group(1), "Stunden", re.I)


def test_umkehrprobe(index_html):
    kaputt = index_html.replace('[String(a.nummer||""),a.kundNr,', "[i+1,a.kundNr,", 1)
    assert "[i+1,a.kundNr" in _fn(kaputt)
