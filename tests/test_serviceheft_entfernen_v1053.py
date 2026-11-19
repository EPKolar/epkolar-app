# -*- coding: utf-8 -*-
"""19.11. GF: "Serviceheft - das X fuer Loeschen der PDF-Files passt ueberhaupt nicht".
Vorher: 16px-Kreis mit 12px-Kreuz, schief an der Kachel (top:-6,right:-2), 16px Tippflaeche, Loeschen OHNE Rueckfrage
(_delSvcDoc loescht das Storage-Objekt endgueltig), PDF-Kachel rot umrandet (Rot = Gefahr, CI).
Jetzt: echter <button> mit 44px Tippflaeche, 24px-Kreis mit Rand, Rueckfrage vor dem unveraenderten _delSvcDoc,
PDF-Kachel neutral, Kachelabstand 16px (die Tippflaeche ragt nicht in die Nachbarkachel)."""
import io
import os
import re

PFAD = os.path.join(os.path.dirname(__file__), "..", "index.html")


def _src():
    return io.open(PFAD, encoding="utf-8", newline="").read()


def _knopf(src):
    i = src.index("'data-svc-del': \"1\"")
    a = src.rfind("isVAdmin&&React.createElement('button'", 0, i)
    e = src.index("_ik(\"kreuz\",12)))", i)
    return src[a:e]


def test_tippflaeche_44_und_kreis_24():
    k = _knopf(_src())
    assert "width:44,height:44" in k
    assert "width:24,height:24" in k and "border:\"2px solid \"+V.cd" in k
    assert "COLORS.ERROR_FILL" in k


def test_rueckfrage_vor_loeschen():
    k = _knopf(_src())
    i = k.index("window._confirmModal(")
    j = k.index("_delSvcDoc(i,d)")
    assert i < j and ")))return;" in k[i:j], "erst Rueckfrage, bei Abbruch return"


def test_loeschfunktion_unveraendert():
    src = _src()
    assert "const _delSvcDoc=(i,d)=>{if(d&&d.storage_path)_sbDeleteObj(SB_FZ_BUCKET,d.storage_path);" in src


def test_pdf_kachel_nicht_rot_und_abstand():
    src = _src()
    assert 'border:"1.5px solid #ef4444",background:"#ef444412"' not in src
    assert 'gap:16,flexWrap:"wrap",alignItems:"flex-start",marginTop:3,paddingTop:12,paddingRight:12' in src


def test_umkehrprobe_alter_stand_faellt_durch():
    """Der Stand vor dem Fix (origin/main v3.9.1052) muss an diesen Riegeln scheitern."""
    import subprocess
    alt = subprocess.run(["git", "show", "525c606:index.html"], cwd=os.path.dirname(PFAD), capture_output=True,
                         text=True, encoding="utf-8").stdout
    assert alt, "alter Stand nicht lesbar"
    assert "'data-svc-del'" not in alt, "alter Stand hatte noch keinen Entfernen-Knopf mit Rueckfrage"
    assert 'top:-6,right:-2,cursor:"pointer"' in alt and "width:16,height:16" in alt
    assert 'border:"1.5px solid #ef4444",background:"#ef444412"' in alt
