"""Sprint 69 — apply 69.1/69.2/69.3/69.4 edits to index.html and sw.js."""
import sys
from pathlib import Path

ROOT = Path('.').resolve()
IDX = ROOT / 'index.html'
SW  = ROOT / 'sw.js'

src = IDX.read_text(encoding='utf-8')
orig = src

def bracket_diffs(s):
    return (s.count('(')-s.count(')'),
            s.count('{')-s.count('}'),
            s.count('[')-s.count(']'))

print('PRE  brackets:', bracket_diffs(src))

# ───────── 69.1 .epk-form-field on form inputs ─────────
form_field_edits = [
    ('React.createElement(\'input\', { id:"lbl_monteurNew_name",',
     'React.createElement(\'input\', { id:"lbl_monteurNew_name", className: "epk-form-field",'),
    ('React.createElement(\'input\', { id:"lbl_monteurNew_vorname",',
     'React.createElement(\'input\', { id:"lbl_monteurNew_vorname", className: "epk-form-field",'),
    ('React.createElement(\'select\', { id:"lbl_monteurNew_rolle",',
     'React.createElement(\'select\', { id:"lbl_monteurNew_rolle", className: "epk-form-field",'),
    ('React.createElement(\'input\', { id:"lbl_monteurNew_telefon",',
     'React.createElement(\'input\', { id:"lbl_monteurNew_telefon", className: "epk-form-field",'),
    ('React.createElement(\'input\', { id:"lbl_monteurNew_email",',
     'React.createElement(\'input\', { id:"lbl_monteurNew_email", className: "epk-form-field",'),
    ('React.createElement(\'input\', { id:"lbl_monteurNew_gebDat",',
     'React.createElement(\'input\', { id:"lbl_monteurNew_gebDat", className: "epk-form-field",'),
    ('React.createElement(\'input\', { id:"lbl_monteurNew_fsNr",',
     'React.createElement(\'input\', { id:"lbl_monteurNew_fsNr", className: "epk-form-field",'),
    ('React.createElement(\'input\', { id:"lbl_monteurNew_svnr",',
     'React.createElement(\'input\', { id:"lbl_monteurNew_svnr", className: "epk-form-field",'),
    ('React.createElement(\'input\', { id:"lbl_monteurNew_reisepass",',
     'React.createElement(\'input\', { id:"lbl_monteurNew_reisepass", className: "epk-form-field",'),
    ('React.createElement(\'input\', { id:"lbl_monteurNew_eintritt",',
     'React.createElement(\'input\', { id:"lbl_monteurNew_eintritt", className: "epk-form-field",'),
    ('React.createElement(\'input\', { id:"lbl_monteurNew_austritt",',
     'React.createElement(\'input\', { id:"lbl_monteurNew_austritt", className: "epk-form-field",'),
    ('React.createElement(\'input\', { id:"lbl_asForm_kundNr",',
     'React.createElement(\'input\', { id:"lbl_asForm_kundNr", className: "epk-form-field",'),
    ('React.createElement(\'input\', { id:"lbl_asForm_kundName",',
     'React.createElement(\'input\', { id:"lbl_asForm_kundName", className: "epk-form-field",'),
    ('React.createElement(\'input\', { id:"lbl_asForm_kundStr",',
     'React.createElement(\'input\', { id:"lbl_asForm_kundStr", className: "epk-form-field",'),
    ('React.createElement(\'input\', { id:"lbl_asForm_kundPlz",',
     'React.createElement(\'input\', { id:"lbl_asForm_kundPlz", className: "epk-form-field",'),
    ('React.createElement(\'input\', { id:"lbl_asForm_kundOrt",',
     'React.createElement(\'input\', { id:"lbl_asForm_kundOrt", className: "epk-form-field",'),
    ('React.createElement(\'input\', { id:"lbl_asForm_dauer",',
     'React.createElement(\'input\', { id:"lbl_asForm_dauer", className: "epk-form-field",'),
]

applied = 0
for needle, repl in form_field_edits:
    if needle in src and repl not in src:
        cnt = src.count(needle)
        if cnt == 1:
            src = src.replace(needle, repl, 1)
            applied += 1
        else:
            print(f'  [69.1] SKIP (count={cnt}): {needle[:80]}')
    else:
        if repl in src:
            pass  # already done
        else:
            print(f'  [69.1] skip (not found): {needle[:80]}')

print(f'69.1 total applied: {applied}')

# ───────── 69.3 Section-Header polish ─────────
sh_edits = [
    ('style: {fontSize:11,fontWeight:700,color:V.dm,marginBottom:6,textTransform:"uppercase",letterSpacing:.5}}, "📋 Heute (" ',
     'style: {fontSize:13,fontWeight:700,color:V.dm,marginBottom:8,textTransform:"uppercase",letterSpacing:1}}, "📋 Heute (" '),
]

sh_applied = 0
for needle, repl in sh_edits:
    if needle in src and repl not in src:
        cnt = src.count(needle)
        if cnt == 1:
            src = src.replace(needle, repl, 1)
            sh_applied += 1
        else:
            print(f'  [69.3] SKIP (count={cnt}): {needle[:80]}')
print(f'69.3 total applied: {sh_applied}')

# ───────── 69.5 Version bump v3.9.89 → v3.9.90 ─────────
hits_idx = src.count('v3.9.89')
print(f'  [69.5 idx] occurrences of v3.9.89 before: {hits_idx}')
if hits_idx > 0:
    src = src.replace('v3.9.89', 'v3.9.90')
    print(f'  [69.5 idx] replaced {hits_idx} occurrences')

print('POST brackets:', bracket_diffs(src))

if src != orig:
    IDX.write_text(src, encoding='utf-8')
    print(f'WRITE index.html bytes={len(src)}')
else:
    print('NO CHANGE to index.html')

# ───────── sw.js bump ─────────
sw = SW.read_text(encoding='utf-8')
sw_orig = sw
cnt_sw = sw.count('v3.9.89')
print(f'  [69.5 sw] occurrences of v3.9.89 before: {cnt_sw}')
if cnt_sw > 0:
    sw = sw.replace('v3.9.89', 'v3.9.90')
    print(f'  [69.5 sw] replaced {cnt_sw} occurrences')
if sw != sw_orig:
    SW.write_text(sw, encoding='utf-8')
    print(f'WRITE sw.js bytes={len(sw)}')
else:
    print('NO CHANGE to sw.js')
