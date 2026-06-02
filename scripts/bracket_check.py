"""Bracket-baseline checker for index.html (sprint verify)."""
import re
import sys
import pathlib

def main():
    p = pathlib.Path(__file__).resolve().parent.parent / 'index.html'
    content = p.read_text(encoding='utf-8')
    scripts = re.findall(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)
    combined = '\n'.join(scripts)
    # Strip block /* */
    combined = re.sub(r'/\*.*?\*/', '', combined, flags=re.DOTALL)
    # Strip line // (naive)
    combined = re.sub(r'//[^\n]*', '', combined)
    # Strip strings (naive but consistent)
    combined = re.sub(r"'(?:\\.|[^'\\])*'", "''", combined)
    combined = re.sub(r'"(?:\\.|[^"\\])*"', '""', combined)
    combined = re.sub(r'`(?:\\.|[^`\\])*`', '``', combined, flags=re.DOTALL)
    o = combined.count('(')
    c = combined.count(')')
    ob = combined.count('{')
    cb = combined.count('}')
    osq = combined.count('[')
    cs = combined.count(']')
    print(f'() {o - c}')
    print(f'{{}} {ob - cb}')
    print(f'[] {osq - cs}')

if __name__ == '__main__':
    main()
