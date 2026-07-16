# -*- coding: utf-8 -*-
"""v3.9.721 — Dispo P2#4: E4b-Uebernahme-Diff == manueller Buero-Edit (Beleg, test-only).

Belegt schwarz auf weiss, dass "✓ Uebernehmen" byte-gleich zu einem manuellen Buero-Edit derselben
drei Felder ist — Voraussetzung fuer die kontrollierte Live-Abnahme durch Chat-Claude.

Der Uebernahme-Diff:
  updAs(scheinId, {terminBestaetigt:<Tag-ISO>, monteur:<Monteur-id>, dauer:<HH:MM>})
  -> updAs setzt push_pending=true (s.juprowa_id && push-Feld in updates)
  -> SQ.push PUT /api/arbeitsscheine/<id> body {…, push_pending:true, local_updated_at}
  -> Auto-Push (online).
Kein SQ.push/Bulk-Sonderpfad im Callback, kein fz_bedarf. updAs ist DER einzige Schreibpfad fuer
diese Felder -> ein manueller Listen-Inline-Edit derselben Felder erzeugt denselben Body/Push.
"""


def test_uebernahme_callback_ist_updAs(index_html):
    assert ("onUebernehmen: (scheinId,monteurId,iso,dauerMin)=>{"
            "updAs(scheinId,{terminBestaetigt:iso,monteur:monteurId,dauer:_dispoMinToHHMM(dauerMin)})"
            in index_html)


def test_uebernahme_felder_sind_push_felder(index_html):
    """terminBestaetigt/monteur/dauer sind JUPROWA_PUSH_FIELDS -> push_pending feuert exakt wie manuell."""
    start = index_html.index("const JUPROWA_PUSH_FIELDS={")
    end = index_html.index("}", start)
    block = index_html[start:end]
    for feld in ("terminBestaetigt:", "monteur:", "dauer:"):
        assert feld in block, "Push-Feld %s fehlt in JUPROWA_PUSH_FIELDS" % feld


def test_updAs_setzt_push_pending_und_put(index_html):
    """updAs (der Schreibpfad beider Wege) setzt push_pending bei Push-Feldern + SQ.push PUT."""
    start = index_html.index("const updAs=(id,updates)=>{")
    end = index_html.index("const exportOffa=", start)
    block = index_html[start:end]
    assert "s.juprowa_id&&Object.keys(JUPROWA_PUSH_FIELDS).some(k=>k in updates)" in block
    assert 'SQ.push({url:"/api/arbeitsscheine/"+id,method:"PUT"' in block


def test_callback_ohne_sqpush_und_ohne_fzbedarf(index_html):
    seg = index_html.split("onUebernehmen: (scheinId,monteurId,iso,dauerMin)=>{", 1)[1][:220]
    assert "SQ.push" not in seg
    assert "fz_bedarf" not in seg and "fzBedarf" not in seg
