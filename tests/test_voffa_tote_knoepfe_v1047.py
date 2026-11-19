"""v3.9.1047 GF 19.11.: Projektakte > OFFA (VOffa) - funktionslose Knoepfe entfernt.

Beleg vorher (v3.9.1045): die drei Karten ZUZEIT.ASC / Excel Export / Drucken und die
Knoepfe Mail / Clipboard hatten KEINEN onClick (VOffa enthielt kein einziges onClick,
gepinnt von test_tablet_rest_v1040). Sie wurden entfernt; die ASC-Vorschau (Anzeige) bleibt.
Der echte OFFA-Excel-Export (exportOffa, Arbeitsscheine) ist nicht Teil von VOffa und unberuehrt.
"""
import io
import os
import re

PFAD = os.path.join(os.path.dirname(__file__), "..", "index.html")
KOPF = "function VOffa({p,entries,kw,yr,monteure,ww}){"


def _voffa(src):
    i = src.index(KOPF)
    return src[i:src.index("\nfunction ", i + len(KOPF))]


def _knoepfe_weg(blk):
    """True, wenn keiner der 5 toten Knoepfe mehr gerendert wird."""
    tot = ['"ZUZEIT.ASC"', '"Excel Export"', '"Drucken"', '"Mail"', '"Clipboard"', 'className: "export-grid"']
    return not any(t in blk for t in tot)


def _src():
    return io.open(PFAD, encoding="utf-8", newline="").read()


def test_tote_knoepfe_nicht_mehr_im_render():
    blk = _voffa(_src())
    assert _knoepfe_weg(blk)
    assert len(re.findall(r"React\.createElement\('button'", blk)) == 0, "VOffa hat keine Knoepfe mehr"


def test_asc_vorschau_und_offa_daten_bleiben():
    blk = _voffa(_src())
    assert 'const ascP=pe.slice(0,5).map(' in blk
    assert '"ASC Vorschau"' in blk
    assert '_ikVw("verbindung","OFFA Daten")' in blk
    for feld in ('"PA-Nr:"', '"Kd-Nr:"', '"MC:"', '"Betrag:"'):
        assert feld in blk


def test_umkehrprobe_alter_stand_wird_erkannt():
    """Der Pruefer muss den alten Stand (Knoepfe ohne Handler) als NICHT entfernt erkennen."""
    alt = ('function VOffa({p,entries,kw,yr,monteure,ww}){ x\n'
           '  , React.createElement(\'div\', { className: "export-grid", style: {marginBottom:14}}\n'
           '    , [{i:"dokument",t:"ZUZEIT.ASC",d:"OFFA Zeitübergabe",primary:true}]\n'
           '  , React.createElement(\'button\', { style: beS}, _ikVw("brief","Mail") )\n}\n')
    assert not _knoepfe_weg(alt)


def test_echter_offa_excel_export_unberuehrt():
    src = _src()
    assert '"📊 OFFA Excel"' in src or "OFFA Excel" in src
    assert "exportOffa" in src
