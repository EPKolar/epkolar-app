"""v3.9.152 — WhatsApp-Abschluss zentral (Helper aus updAs + saveAs) + Double-Fire-Guard + kundTel."""


def test_central_helper_exists(index_html):
    assert "function _maybeNotifyAsDone(asRec,prevStatus,newStatus,idFallback){" in index_html
    # kundTel-Fallback
    assert 'const phone=(asRec.telefon||asRec.kundTel||"").trim();' in index_html
    # Double-Fire-Guard + persistierte Menge
    assert "if(_key&&_waNotifiedAs.has(_key))return;" in index_html
    assert 'ODB.save("waNotifiedAs",[..._waNotifiedAs].slice(-2000));' in index_html


def test_called_from_updas_and_saveas(index_html):
    # updAs ruft Helper (statt Inline-Block)
    assert "_maybeNotifyAsDone({...s,...updates}, s&&s.scheinstatus, updates&&updates.scheinstatus, id);" in index_html
    # saveAs ruft Helper (Edit-Branch + Auto-Close)
    assert "_maybeNotifyAsDone({..._prevAs,..._finalForm}, _prevAs.scheinstatus, _finalForm.scheinstatus, editId);" in index_html
    # alter Inline-Trigger ist weg
    assert "/* v3.9.19 Feature 12: WhatsApp Auto-Trigger" not in index_html


def test_manual_button_kundtel(index_html):
    assert 'const phone=(form.telefon||form.kundTel||"").trim();' in index_html
