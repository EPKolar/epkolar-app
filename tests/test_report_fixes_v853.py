"""
Nachtlauf-Hunt v3.9.853 — 2 verifizierte Report-Korrektheitsfixes (PDF/Report-Agent).

(P1) VBer-Wochenbericht: die prominente Gesamt-Summe (tfoot :15393) rechnete
     `totalH` über ALLE Projekteinträge (`pe`, kein KW-Filter :15382), während die
     per-Gewerk-Zeilen und die per-Tag-Fußzeile wochen-scoped sind → das mit
     "Wochenbericht KW/yr" betitelte Blatt zeigte die Projekt-Lebenszeit-Stunden.
     Jetzt summiert `totalH` nur die 7 Tage der KW.
(P2) `_pzePdf` (PZE-Monatsblatt, Querformat 297×210): Fuß + Seitenzahl standen bei
     y=290 (:11585) → 80mm unter dem Seitenende der 210mm hohen Querformatseite →
     auf KEINER Seite sichtbar. Jetzt y=203.
"""


def test_vber_gesamtsumme_wochen_scoped(index_html):
    # der alte Alltime-totalH ist weg
    assert "const totalH=pe.reduce((s,e)=>s+(parseFloat(e.hours||e.stunden)||0),0);" not in index_html
    # jetzt nur die 7 KW-Tage
    assert "const _wkDays=new Set(days.map(dayStr));const totalH=pe.reduce((s,e)=>s+(_wkDays.has(e.datum||e.date)?(parseFloat(e.hours||e.stunden)||0):0),0);" in index_html


def test_pze_pdf_fuss_auf_querformatseite(index_html):
    # y=290 (Hochformat-Rest) ist weg, Fuss+Seitenzahl jetzt bei y=203
    assert "doc.text(pi+'/'+pc,PW-M,290,{align:'right'});" not in index_html
    # v3.9.879 NACHGEZOGEN - nicht abgeschwaecht: der Fuss traegt jetzt zusaetzlich
    # Mitarbeiter und Zeitraum, damit Blatt 2+ ueberhaupt zuordenbar ist (es trug
    # weder Namen noch Monat und war als Lohnbeleg wertlos). Die EIGENSCHAFT, die
    # dieser Riegel seit v853 sichert, ist die y-Position 203 auf der 210mm hohen
    # Querformatseite - die wird hier weiter geprueft, nur nicht mehr am Wortlaut.
    import re as _re
    m = _re.search(r"doc\.text\(_pdfStr\('Generiert am '\+fdt\(td2\(\)\)[^;]*?\),M,(\d+)\);"
                   r"doc\.text\(pi\+'/'\+pc,PW-M,(\d+),\{align:'right'\}\);", index_html)
    assert m, "Fuss-Zeile des PZE-PDFs nicht gefunden - Aufbau geaendert?"
    assert m.group(1) == '203' and m.group(2) == '203', (
        "Fuss oder Seitenzahl stehen nicht mehr auf y=203 (gefunden: %s / %s). "
        "Auf einer 210mm hohen Querformatseite waeren sie darunter unsichtbar - "
        "genau der Fehler, den v3.9.853 behoben hat." % (m.group(1), m.group(2))
    )
    assert 'worker.name' in m.group(0), (
        "Der Fuss nennt den Mitarbeiter nicht mehr - dann ist Blatt 2+ wieder "
        "ein anonymes Blatt ohne Zuordnung (v3.9.879)."
    )
