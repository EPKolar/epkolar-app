"""
Nachtlauf-Hunt v3.9.854 — _genPlanReportPdf-Legende: Spaltenkopf auf Folgeseiten.

PDF-Agent-Fund P2 (kosmetisch): der Legenden-Spaltenkopf (Nr/Titel/Status/Frist/
Verantwortlich + graue Zeile) wurde nur einmal gezeichnet (:16473-16474);
`_legHeader` (:16476) legte bei Überlauf eine neue Seite an, zog den Spaltenkopf
aber nicht mit → Legenden-Zeilen auf Seite 2+ ohne Spaltentitel. Fix:
Kopf-Zeichnung in `_legCols()` extrahiert, in beiden Pfaden aufgerufen.
"""


def test_legcols_extrahiert_und_zweimal_genutzt(index_html):
    # der Spaltenkopf ist in _legCols() extrahiert
    assert 'const _legCols=()=>{doc.setFontSize(8);doc.setFont("helvetica","bold");doc.setFillColor(238,238,238);doc.rect(M,y-4,PW-2*M,6,"F");doc.text("Nr",CX.nr+1,y);doc.text("Titel",CX.title+1,y);doc.text("Status",CX.status+1,y);doc.text("Frist",CX.frist+1,y);doc.text("Verantwortlich",CX.who+1,y);y+=6;doc.setFont("helvetica","normal");};' in index_html
    # _legCols() wird an ZWEI Stellen aufgerufen: Erststart + Folgeseiten-Funktion
    assert index_html.count("_legCols();") == 2
    # und die Folgeseiten-Funktion ruft _legCols() (statt frueher gar keinen Kopf)
    assert 'const _legHeader=()=>{doc.addPage();_header("Plan-Report — Legende");y=32;_legCols();};' in index_html


def test_kein_einmaliger_inline_kopf_mehr(index_html):
    # die alte, nur-einmal-inline gezeichnete Kopfzeile (ohne _legCols) ist weg
    assert 'doc.setFont("helvetica","normal");\n    const _legHeader=()=>{doc.addPage();_header("Plan-Report — Legende");y=32;doc.setFont("helvetica","normal");doc.setFontSize(8);};' not in index_html
