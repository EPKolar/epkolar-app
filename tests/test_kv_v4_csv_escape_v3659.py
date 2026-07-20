"""v3.9.776 — Der KV-V4 Zulagen-CSV-Export ist entfernt (Regression-Pin der Ablösung).

Historie: v3.9.659 fuehrte ein CSV-Feld-Escaping (_csvEsc) fuer den Zulagen-CSV-Export ein. In
v3.9.776 wurde der CSV-Export durch den PZE-PDF-Uebergabezettel an den Lohnverrechner ersetzt
(FinkZeit-Monatsblatt inkl. Entfernungszulage-Fuss). Damit sind _csvEsc und der CSV-Export ohne
Referenz — dieser Test haelt die Ablösung fest, damit der tote Pfad nicht stillschweigend zurueckkehrt.
"""


def test_csv_escape_entfernt(index_html):
    assert "var _csvEsc=function" not in index_html, "toter CSV-Escaper darf nicht zurueckkehren"
    assert "head.map(_csvEsc)" not in index_html, "CSV-Kopf-Wiring muss entfernt sein"


def test_csv_export_entfernt(index_html):
    assert "'KV-Zulagen_'+ym+'.csv'" not in index_html, "CSV-Download darf nicht mehr existieren"
    assert "const _csv=()=>{" not in index_html, "KVZulagenReport._csv muss entfernt sein"


def test_pze_pdf_uebergabe_ersetzt_csv(index_html):
    assert "📄 PZE-PDF (Lohnverrechner)" in index_html, "PZE-PDF-Uebergabe-Button muss den CSV-Button ersetzen"
