"""Z9-Sperre (GF-Entscheidung 24.11.2026 abends) - Quelltext-Riegel als Ergaenzung zum Ausgabe-Test.

Die fuenf Z9-Exporte der Zeiterfassung (ZeiterfassungView) bleiben VOLLSTAENDIG unveraendert, bis Sebastian im Buero
geklaert hat, ob diese Dateien irgendwo eingelesen werden: exportWochenStz, exportTagesStz, exportBauwochenbericht,
exportXls, exportAllXls. Paket 13 (b24317e) hatte exportTagesStz, exportXls und exportAllXls geaendert.

Die eigentliche Pruefung ist der Ausgabe-Vergleich test_exporte_golden_v1114.py (Datei-Inhalt gegen 3.9.1114).
Dieser Riegel haelt zusaetzlich den Quelltext der fuenf Bloecke byte-gleich zu dfc369b (md5, LF, Block von
"  const <name>=" bis zum naechsten "\\n  const " innerhalb von ZeiterfassungView). Umkehrprobe: gegen b24317e/3ba544b rot.
"""
import hashlib

import pytest

# md5 (LF) gemessen an dfc369b (3.9.1114)
Z9_MD5 = {
    "exportWochenStz": "008517082b7471c82a55c6fd82db0c10",
    "exportTagesStz": "39060e139382e9a069db61dd9b3b8c87",
    "exportBauwochenbericht": "cf6161a7a3a46aa9fd9b28a6f953edbc",
    "exportXls": "0b58042ea3da4decf6e2071e60ce7125",
    "exportAllXls": "d02405794c3e20894c0bf8817267adbf",
}


def _block(src, name):
    s = src.replace("\r\n", "\n")
    z = s.index("\nfunction ZeiterfassungView(")
    i = s.index("\n  const " + name + "=", z) + 1
    j = s.index("\n  const ", i + 5)
    return s[i:j]


@pytest.mark.parametrize("name", sorted(Z9_MD5))
def test_z9_export_quelltext_wie_1114(index_html, name):
    ist = hashlib.md5(_block(index_html, name).encode("utf-8")).hexdigest()
    assert ist == Z9_MD5[name], name + " wurde veraendert - Z9-Sperre (GF 24.11.2026)"
