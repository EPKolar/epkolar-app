"""Hunt-2 Batch A (Security + Fahrzeug-Feld/Rechte) — Static-Source-Regression-Guards.

Jeder Test belegt einen Hunt-2-Fund + seinen Minimal-Fix. Initial rot vor dem Fix.
"""
import re
from pathlib import Path

INDEX = Path(__file__).parent.parent / 'index.html'


def _txt():
    return INDEX.read_text(encoding='utf-8')


# ── Fund #2: Stored-XSS in genAsPdf — Foto-URL unescaped in img-src ──────────────
def test_genaspdf_foto_src_escaped():
    """genAsPdf Foto-Loop muss die URL quote-escapen (Attribut-Breakout neutralisiert).
    Vorher: <img src="${u}"> roh. Nachher: src="${esc(u).replace(/"/g,'&quot;')}"."""
    t = _txt()
    # der rohe, ungeschuetzte Foto-src darf NICHT mehr existieren
    assert 'return u?`<img src="${u}" style=' not in t, \
        '#2 XSS: genAsPdf Foto-src ist roh interpoliert (kein Quote-Escape)'
    # die geschuetzte Variante MUSS existieren
    assert "src=\"${esc(u).split(String.fromCharCode(34)).join('&quot;')}\"" in t, \
        '#2 XSS: genAsPdf Foto-src muss quote-escaped sein (charcode-Form, regex-/quote-literal-frei wegen bracket-checker)'


# ── Fund #5: Chef-KPI 'Service/Pickerl 14T' liest nicht-existente Fahrzeug-Felder ──
def test_chef_kpi_service_pickerl_real_fields():
    """fzFaellig-Memo muss f.naechstService/f.pickerl lesen (vorher next_service/pickerl_faellig_am = inexistent -> konstant 0)."""
    t = _txt()
    assert 'f.next_service||f.nextService' not in t, '#5: fzFaellig liest nicht-existentes next_service'
    assert 'f.pickerl_faellig_am' not in t, '#5: fzFaellig liest nicht-existentes pickerl_faellig_am'
    m = re.search(r'const fzFaellig=.*?\.length,\[fahrzeuge', t, re.S)
    assert m, 'fzFaellig-Memo nicht gefunden'
    seg = m.group(0)
    assert 'f.naechstService' in seg and 'f.pickerl' in seg, \
        '#5: fzFaellig muss die echten Felder naechstService/pickerl lesen'


# ── Fund #12: Dashboard _isFleetAdmin liest nicht-existentes curUser.isVAdmin ──────
def test_isfleetadmin_role_based():
    """_isFleetAdmin muss rollenbasiert (buero/lagerleitung als Flotten-Manager) sein,
    nicht das nie gesetzte curUser.isVAdmin lesen."""
    t = _txt()
    m = re.search(r'const _isFleetAdmin=.*?;', t)
    assert m, '_isFleetAdmin nicht gefunden'
    seg = m.group(0)
    assert 'isVAdmin' not in seg, '#12: _isFleetAdmin liest inexistentes curUser.isVAdmin'
    assert 'buero' in seg and 'lagerleitung' in seg, \
        '#12: _isFleetAdmin muss buero/lagerleitung (Flotten-Manager) einschliessen'


# ── Fund #15: canDo('fz_delete') zu eng ggue. Policy (admin/PL/buero/lagerleitung) ──
def test_fz_delete_cando_matches_policy():
    """Sebastian-Entscheid: admin/PL/buero/lagerleitung duerfen Fahrzeuge loeschen.
    canDo fz_delete muss das abbilden (isLager||isB = lagerleitung/admin/PL + buero),
    deckungsgleich mit UI (isVAdmin) und DB-RLS fahrzeuge_delete. KEIN DDL, kein Loesch-Pfad-Umbau."""
    t = _txt()
    assert 'fz_delete:isA||isPL,' not in t, '#15: canDo fz_delete war zu eng (nur admin/PL)'
    assert 'fz_delete:isLager||isB,' in t, \
        '#15: canDo fz_delete muss admin/PL/buero/lagerleitung sein (isLager||isB)'
