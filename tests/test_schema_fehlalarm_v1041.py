# -*- coding: utf-8 -*-
"""v3.9.1041 'DB-Schema veraltet' kam bei jedem Netz-/Zeitfehler (Server-Protokolle: nur 200).
Jetzt nur bei 404 mit Tabelle-fehlt-Kennung."""


def _block(html):
    i = html.index("const _sc=await _authRetry(()=>fetch(SB_REST+\"/bautagebuch?select=id&limit=1\"")
    return html[i:html.index("console.warn('[schema-check]", i) + 200]


def test_meldung_nur_bei_404(index_html):
    b = _block(index_html)
    assert "if(_sc.status===404){" in b
    assert "PGRST205|42P01" in b
    assert "if(!_sc.ok)throw" not in b
    # catch (Netz/Zeit) meldet nichts mehr
    c = b[b.index("}catch(e){"):]
    assert "DB-Schema veraltet" not in c


def test_umkehrprobe_alter_catch_meldet(index_html):
    b = _block(index_html)
    kaputt = b.replace("}catch(e){console.warn('[schema-check]", "}catch(e){__toast(\"DB-Schema veraltet\");console.warn('[schema-check]", 1)
    c = kaputt[kaputt.index("}catch(e){"):]
    assert "DB-Schema veraltet" in c
