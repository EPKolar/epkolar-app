"""v3.9.128 — Finder L (Portal-Defense-in-Depth) + Finder M (Druck-Escaping/Null-Guards)."""


def test_generatebwb_escapes(index_html):
    # M-P2: generateBWB escapte Kunden-/MA-/Tätigkeitsnamen nicht (Excel-Bruch beim Kunden)
    assert 'const esc=s=>String(s==null?"":s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");/* v3.9.128 M-P2: generateBWB' in index_html
    assert "html+='<th>'+esc(w.name)+'</th>';" in index_html
    assert index_html.count("'</td><td>'+esc(taetigkeit)+'</td></tr>';") == 2
    assert index_html.count("text-align:right\">'+esc(proj.") == 2


def test_no_txt_exports_remain(index_html):
    # v3.9.308: Alle TXT-Exporte aus der App entfernt (Buero nutzt nur Excel).
    # genPdf (Projektdoku-TXT), exportTxt (Bautagebuch/Wochenplanung/Zeiterfassung), exportAbsTxt
    # — keine dieser Funktionsdefinitionen darf mehr existieren.
    for marker in ("const genPdf=", "const exportAbsTxt=", "const exportTxt="):
        assert marker not in index_html, f"v3.9.308: {marker} muss entfernt sein"
    # Auch keine text/plain-Blob-Downloads mehr (nur Uploads via accept=.txt sind ok).
    assert 'type:"text/plain;charset=utf-8"' not in index_html


def test_portal_loads_only_kunde_defects(index_html):
    # L-Defense-in-Depth: anon-Portal lädt nur kunden-gemeldete Mängel (interne Felder bleiben draußen)
    assert 'project_id=eq."+encodeURIComponent(p.id)+"&melder=eq.Kunde"' in index_html
