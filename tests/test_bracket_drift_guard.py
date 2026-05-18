"""v3.9.14+: Bracket-Drift-Guard — verhindert silent worsening von index.html bracket-balance."""
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).parent.parent
SCRIPT = REPO / 'scripts' / '_bracket_check.py'
INDEX = REPO / 'index.html'


def test_bracket_drift_within_baseline():
    """Drift muss bei baseline (-1/0/0) bleiben — kein silent worsening."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(INDEX)],
        capture_output=True, text=True, timeout=30
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
