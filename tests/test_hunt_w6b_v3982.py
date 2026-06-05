"""v3.9.128 — Finder L (Portal-Defense-in-Depth) + Finder M (Druck-Escaping/Null-Guards)."""


def test_generatebwb_escapes(index_html):
    # M-P2: generateBWB escapte Kunden-/MA-/Tätigkeitsnamen nicht (Excel-Bruch beim Kunden)
    assert 'const esc=s=>String(s==null?"":s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");/* v3.9.128 M-P2: generateBWB' in index_html
    assert "html+='<th>'+esc(w.name)+'</th>';" in index_html
    assert index_html.count("'</td><td>'+esc(taetigkeit)+'</td></tr>';") == 2
    assert index_html.count("text-align:right\">'+esc(proj.") == 2


def test_genpdf_null_guards(index_html):
    # M-P2: TXT-Projektdoku druckte "Kunde: undefined" bei Altprojekten
    assert '"Kunde:          "+(p.kunde||"—")' in index_html
    assert '"Matchcode:       "+(p.matchcode||"—")' in index_html
    assert '"Fortschritt:    "+(p.fortschritt||0)+"%"' in index_html


def test_bautagebuch_txt_guard(index_html):
    # Robust ohne Umlaut-Literal: Null-Guard-Marker im Bautagebuch-TXT-Export
    assert "v3.9.128 M-P3: Null-Guard Bautagebuch-TXT" in index_html
    assert '+(e.taetigkeiten||"—")+' in index_html


def test_portal_loads_only_kunde_defects(index_html):
    # L-Defense-in-Depth: anon-Portal lädt nur kunden-gemeldete Mängel (interne Felder bleiben draußen)
    assert 'project_id=eq."+encodeURIComponent(p.id)+"&melder=eq.Kunde"' in index_html
