# -*- coding: utf-8 -*-
"""v3.9.1022: Prioritaet, Monteur (Listenzeile) und Wischen (Monteur-Karte) setzen OFFA-Felder
(JUPROWA_PUSH_FIELDS) erst nach Rueckfrage. Nutzlast unveraendert, nur dahinter."""


def test_prio_erst_nach_rueckfrage(index_html):
    assert ('_asZeileRueckfrage(a,"prioritaet",_np).then(_ok=>{if(_ok)updAs(a.id,{prioritaet:_np});});') in index_html


def test_monteur_erst_nach_rueckfrage(index_html):
    assert ('_asZeileRueckfrage(a,"monteur",_nm,monteure).then(_ok=>{if(_ok)updAs(a.id,{monteur:_nm});});') in index_html


def test_wischen_erst_nach_rueckfrage(index_html):
    i = index_html.index("const _swipeEnd=(as,e)=>{")
    teil = index_html[i:index_html.index("\n  };", i)]
    j = teil.index('_asZeileRueckfrage(as,"scheinstatus",newStatus).then(_ok=>{if(!_ok)return;')
    assert j < teil.index("updAs(as.id,{scheinstatus:newStatus});")


def test_text_nennt_alt_und_neu(index_html):
    assert 'if(feld==="prioritaet")' in index_html and 'if(feld==="monteur")' in index_html
    assert "function _asZeileRueckfrage(a,feld,neu,namen)" in index_html


def test_umkehrprobe(index_html):
    kaputt = index_html.replace('_asZeileRueckfrage(a,"prioritaet",_np).then(_ok=>{if(_ok)', "(", 1)
    assert '_asZeileRueckfrage(a,"prioritaet",_np)' not in kaputt
