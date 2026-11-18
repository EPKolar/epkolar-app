# -*- coding: utf-8 -*-
"""v3.9.1041 'DB-Schema veraltet' kam bei jedem Netz-/Zeitfehler (Server-Protokolle: nur 200).
Jetzt nur bei HTTP 404 (Tabelle unbekannt)."""


def _block(html):
    i = html.index("const _sc=await _authRetry(()=>fetch(SB_REST+\"/bautagebuch?select=id&limit=1\"")
    return html[i:html.index("console.warn('[schema-check]", i) + 200]


def test_meldung_nur_bei_404(index_html):
    b = _block(index_html)
    c = b[b.index("}catch(e){"):]
    assert "if(String(e&&e.message)==='404')" in c
    assert c.index("==='404')") < c.index("DB-Schema veraltet") < c.index("else console.warn('[schema-check]")


def test_umkehrprobe_alter_catch_meldet_immer(index_html):
    b = _block(index_html)
    kaputt = b.replace("if(String(e&&e.message)==='404')", "", 1)
    assert "if(String(e&&e.message)==='404')" not in kaputt
