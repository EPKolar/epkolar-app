"""Extract <script> blocks from index.html and run node --check on combined JS."""
import re
import pathlib
import subprocess
import sys
import tempfile
import os

def main():
    root = pathlib.Path(__file__).resolve().parent.parent
    html = (root / 'index.html').read_text(encoding='utf-8')

    # v3.9.894 LEBENSZEICHEN-RIEGEL. Am 29.08. hat ein abgebrochener Schreib-
    # vorgang index.html auf 0 Bytes gekuerzt - und BEIDE Gates meldeten gruen:
    # eine leere Datei parst fehlerfrei und hat ausgeglichene Klammern. Ein Gate,
    # das auf NICHTS besteht, ist genau der Fehler, den dieses Repo den ganzen
    # Vortag ueber bei anderen Riegeln gefunden hat. Die Schwelle ist bewusst
    # grob (die Datei ist ~3,4 MB): sie soll Totalverlust und Abbruch mitten im
    # Schreiben fangen, nicht ueber Groessenaenderungen urteilen.
    MIN_BYTES = 1_000_000
    if len(html) < MIN_BYTES:
        print('exit: 1')
        print('index.html ist nur %d Bytes gross (erwartet >%d).'
              % (len(html), MIN_BYTES))
        print('Das ist kein Syntaxfehler, sondern ein Datenverlust - vermutlich'
              ' ein abgebrochener Schreibvorgang. NICHT committen:'
              ' git checkout -- index.html')
        sys.exit(1)  # NICHT 'return 1': main() wird ohne sys.exit(main()) aufgerufen,
                     # ein Rueckgabewert verpufft also und die Kette liefe weiter.
    if 'APP_VERSION' not in html:
        print('exit: 1')
        print('APP_VERSION fehlt in index.html - die Datei ist unvollstaendig.')
        sys.exit(1)  # NICHT 'return 1': main() wird ohne sys.exit(main()) aufgerufen,
                     # ein Rueckgabewert verpufft also und die Kette liefe weiter.
    scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
    combined = '\n;\n'.join(scripts)
    tmp = tempfile.NamedTemporaryFile(
        suffix='.js', delete=False, mode='w', encoding='utf-8'
    )
    try:
        tmp.write(combined)
        tmp.close()
        r = subprocess.run(
            ['node', '--check', tmp.name],
            capture_output=True, text=True, timeout=60
        )
        print('exit:', r.returncode)
        if r.stdout:
            print('STDOUT:', r.stdout[-2000:])
        if r.stderr:
            print('STDERR:', r.stderr[-2000:])
        sys.exit(r.returncode)
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass

if __name__ == '__main__':
    main()
