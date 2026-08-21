"""
Nachtlauf-Hunt v3.9.844 — Büro-Export Regie repariert.

VBueroExport.loadAll (~:12018) lud regie über `forms?type=eq.regie`. Die Spalte
heißt kanonisch `form_type` (kanonischer Load :7809, POST :15636). `type`
existiert nicht → `_sbGet` wirft 400 → das gemeinsame Promise.all (time /
bautagebuch / regie / defects) rejected → der GANZE Büro-Export lud gar nichts.

Zusätzlich las die Regie-Map alle Felder top-level, obwohl der Regie-Inhalt im
`data`-JSON liegt (datum/arbeit) und der Owner in `created_by` (=monteur_id).
→ datum/arbeit leer, Monteur-Regie-Zähler (:12341 `r.monteur===m.id`) immer 0.
"""


def test_forms_query_nutzt_form_type(index_html):
    assert '_sbGet("forms","type=eq.regie")' not in index_html
    assert '_sbGet("forms","form_type=eq.regie")' in index_html


def test_regie_map_parst_data_und_created_by(index_html):
    # alte top-level-only-Map ist weg
    assert 'setAllRegie((rg||[]).map(r=>({...r,datum:r.datum||r.date,projekt:r.projekt||r.project_id||r.pid,arbeit:r.arbeit||r.beschreibung||r.taetigkeit||"",monteur:r.monteur||r.worker_id||""})));' not in index_html
    # neue Map parst data (...fd) und nimmt created_by als monteur
    assert "const fd=(typeof r.data==='string'?_safeJsonParse(r.data,{}):(r.data||{}));return {...r,...fd," in index_html
    assert 'arbeit:fd.arbeit||fd.beschreibung||fd.taetigkeit||""' in index_html
    assert 'monteur:r.created_by||fd.monteur||r.worker_id||""' in index_html
