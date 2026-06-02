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
