"""v3.9.704 — Spezialfahrzeuge-Übersicht auf der Wochenplan-Kiosk-Tafel.

Der Wochenplan-Kiosk (?screen=planung) zeigt unten Krankenstand/Urlaub/Zeitausgleich; die
🚛-Spezialfahrzeug-Streifen der Haupt-Planung fehlten. Ableitung EXAKT wie im Haupt-WeekPlan
(kein Neu-Erfinden), nur aus fahrzeuge + rows, kein neuer Fetch. NUR die WochenplanTafel.
"""
import re


def _tafel(index_html):
    m = re.search(r"function WochenplanTafel\(props\)\{.*?\n\}\n", index_html, re.S)
    assert m, "WochenplanTafel nicht gefunden"
    return m.group(0)


def test_spezfz_ableitung_exakt_wie_hauptplan(index_html):
    t = _tafel(index_html)
    # Gleiches Prädikat wie Z.18049: nicht stillgelegt UND (LKW/Anhänger/Stapler/Hebewerk/Steiger/Kompressor)
    assert 'f.status!=="stillgelegt"' in t
    for typ in ('"LKW"', '"Anhänger"', '"Stapler"', '"Hebewerk"'):
        assert typ in t
    assert '(f.modell||"").includes("Steiger")' in t
    assert '(f.modell||"").includes("Kompressor")' in t


def test_tagesbelegung_aus_rows_z_fz(index_html):
    t = _tafel(index_html)
    # Tages-BVH-Ableitung: rows.filter(r => r.z[tag].fz.includes(fzId))
    assert "const _spezFzTag=function(tagKey,fzId){return rows.filter(" in t
    assert "z.fz.indexOf(fzId)>=0" in t


def test_doppelbelegung_rot_und_warn(index_html):
    t = _tafel(index_html)
    assert "var conflict=assigned.length>1;" in t
    assert "conflict?'⚠️ '" in t
    assert "conflict?'rgba(239,68,68,.12)'" in t


def test_fz_ohne_belegung_ausgeblendet(index_html):
    """filter(hasAny) — Fahrzeuge ohne Belegung in der Woche erscheinen nicht (Muster v3.9.505)."""
    t = _tafel(index_html)
    assert "const _spezVisible=_spezFzListe.filter(function(f){return DAYS.some(function(dn){return _spezFzTag(dn,f.id).length>0;});});" in t


def test_zeilen_unter_zeitausgleich(index_html):
    t = _tafel(index_html)
    # Die 🚛-Zeilen hängen NACH den drei _absRow-Aufrufen im tbody.
    assert re.search(r"_absRow\('⏰ Zeitausgleich',_zaMatch\)\s*,_spezVisible\.map\(_fzRow\)", t)


def test_kein_neuer_fetch(index_html):
    """Read-only: die neue Ableitung nutzt nur fahrzeuge + rows, kein zusätzlicher fetch/RPC."""
    t = _tafel(index_html)
    i = t.find("const _spezFzListe=")
    j = t.find("return h('div'", i)
    assert 0 < i < j, "Spez-FZ-Block nicht gefunden"
    block = t[i:j]
    assert "fetch(" not in block and "SQ.push" not in block


def test_hauptweekplan_spezfz_unveraendert(index_html):
    """Die Haupt-Planung (Z.~18049) bleibt unangetastet — dort steht weiter die eigene spezFz-Zeile."""
    assert 'const spezFz=(fahrzeuge||[]).filter(f=>f.status!=="stillgelegt"' in index_html


def test_label_stil_wie_absrow(index_html):
    """Gleiche Zeilen-Optik wie Krankenstand/Urlaub: Label-<td> links, DAYS-Zellen."""
    t = _tafel(index_html)
    assert "'🚛 '+((f.kennzeichen||'').split(' ')[0]||f.kennzeichen||'')" in t
