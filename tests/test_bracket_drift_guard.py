"""v3.9.14+: Bracket-Drift-Guard — verhindert silent worsening von index.html bracket-balance."""
import subprocess
import sys
from pathlib import Path

from conftest import EPK_TEST_TIMEOUT

REPO = Path(__file__).parent.parent
SCRIPT = REPO / 'scripts' / '_bracket_check.py'
INDEX = REPO / 'index.html'

# Timeout kommt aus conftest (Master). Ein hartes Limit stirbt bei langsamer I/O und
# liefert dann leeren stdout = Fail, obwohl die Balance stimmt.
TIMEOUT = EPK_TEST_TIMEOUT


def test_bracket_drift_within_baseline():
    """Drift muss bei baseline (-1/0/0) bleiben — kein silent worsening."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(INDEX)],
        capture_output=True, text=True, timeout=TIMEOUT
    )
    output = result.stdout
    lines = output.strip().split('\n')
    assert len(lines) >= 3, f"Erwarte 3 Zeilen output, got: {output!r}"
    paren_line = lines[0]
    assert paren_line == '() -1', (
        f"Bracket-Drift hat sich verschlechtert! Baseline: '() -1', "
        f"aktuell: {paren_line!r}. Untersuche letzte Edits in index.html."
    )
    assert lines[1] == '{} 0', f"Brace-Drift abnormal: {lines[1]!r}"
    assert lines[2] == '[] 0', f"Bracket-Drift abnormal: {lines[2]!r}"


def test_bracket_check_script_exists():
    assert SCRIPT.exists(), "scripts/_bracket_check.py muss existieren"


# ══ Umkehrprobe (v3.9.921) ══════════════════════════════════════════════════
#
# WARUM ES DIESE ZWEI PROBEN GIBT: bis v3.9.920 stand an ZWEI weiteren Stellen
# eine ROHE Klammerbilanz der ganzen Datei -
#   tests/test_invariants.py             (paren, brace, bracket) == (-7, 0, 0)
#   tests/test_dispo_tagesplan_v894.py   count("(") - count(")")  == -7
# Beide sind gestrichen, weil sie Fliesstext gemessen haben, nicht Code:
# in den Kommentaren von index.html stehen 6.879 "(" und 6.998 ")", Saldo -119.
# Der Sollwert -7 wurde folgerichtig schon einmal nachgezogen (-5 -> -7).
#
# Gestrichen werden durfte er nur, wenn DIESER Riegel das Echte traegt. Genau
# das zeigen die zwei Proben: eine fehlende Klammer im CODE macht ihn rot, eine
# ueberzaehlige im KOMMENTAR laesst ihn zu Recht gruen.

_CODE_ANKER = "function _dataUrlToBlob(dataUrl){"
_KOMMENTAR_ANKER = "EP KOLAR SELF-HEAL v1: Nuke stale SW cache"


def _lauf(tmp_path, text, name):
    ziel = tmp_path / name
    ziel.write_text(text, encoding="utf-8")
    r = subprocess.run([sys.executable, str(SCRIPT), str(ziel)],
                       capture_output=True, text=True, timeout=TIMEOUT)
    return r.returncode, r.stdout.strip().split('\n')


def test_umkehrprobe_fehlende_klammer_im_code_wird_rot(tmp_path):
    """Nimmt man dem CODE eine Klammer, MUSS der Riegel anschlagen."""
    quelle = INDEX.read_text(encoding='utf-8')
    assert quelle.count(_CODE_ANKER) == 1, "Vorbedingung weg - Anker anpassen"
    kaputt = quelle.replace(_CODE_ANKER, _CODE_ANKER.replace(")", "", 1), 1)
    assert kaputt != quelle
    rc, zeilen = _lauf(tmp_path, kaputt, "ohne_klammer.html")
    assert zeilen[0] != '() -1', (
        "Umkehrprobe traegt nicht: eine fehlende Code-Klammer aendert die "
        "Bilanz nicht (%r). Dann misst _bracket_check.py nichts." % zeilen[0]
    )
    assert rc != 0, "Umkehrprobe traegt nicht: das Skript meldet trotzdem Erfolg"


def test_umkehrprobe_klammer_im_kommentar_bleibt_gruen(tmp_path):
    """Und die Gegenrichtung: Prosa darf den Riegel NICHT bewegen.

    Genau hier lagen die gestrichenen rohen Zaehler falsch - sie waeren von
    dieser Aenderung rot geworden, obwohl am Code nichts anders ist."""
    quelle = INDEX.read_text(encoding='utf-8')
    assert quelle.count(_KOMMENTAR_ANKER) == 1, "Vorbedingung weg - Anker anpassen"
    prosa = quelle.replace(_KOMMENTAR_ANKER, _KOMMENTAR_ANKER + " )", 1)
    assert prosa.count("(") - prosa.count(")") == (
        quelle.count("(") - quelle.count(")") - 1), (
        "Die rohe Bilanz muesste sich um 1 verschieben - sonst zeigt die Probe "
        "nicht, was sie zeigen soll."
    )
    rc, zeilen = _lauf(tmp_path, prosa, "kommentar_klammer.html")
    assert zeilen[0] == '() -1' and rc == 0, (
        "Eine Klammer im Kommentar hat _bracket_check.py bewegt (%r). Dann "
        "misst er doch Prosa mit - und die Streichung der rohen Zaehler in "
        "test_invariants.py / test_dispo_tagesplan_v894.py war voreilig."
        % zeilen[0]
    )
