# OVERNIGHT #2 · STATUS · Block 5 · Statische Analyse v2

**Baseline:** `5e190ef`
**End-State:** `af5b7e5`

## Sub-Tasks

| ID | Theme | File | Kern-Befund |
|---|---|---|---|
| 5-1 | Dead-Code v2 | `sql/DEAD_CODE_CANDIDATES_v2.md` | 4 Kandidaten (von 7 in v1), nach v3.8.37-Cleanup |
| 5-2 | Duplicate-String-Audit | `sql/DUPLICATE_STRINGS.md` | 546 Strings ≥5×; Top: CSS-Farben, Table-Names |
| 5-3 | CODE_DEBT v2 Update | `sql/CODE_DEBT_v2.md` | 9 Items CLOSED, 2 neu (QW6 Colors + L6 Tables) |
| 5-4 | a11y-Audit | `sql/A11Y_AUDIT.md` | **0/154 Label-htmlFor-Bindings!** P2-Refactor |

## Commits (1)

| SHA | Subject |
|---|---|
| af5b7e5 | docs: block 5 static analysis v2 (dead-code, dup-strings, code-debt, a11y) |

## Kein Code-Touch

Block 5 ist pure Doku (wie vorgesehen). H1-konform.

## Nächster Block

Block 6 (18h→19.5h): Hardening Docs.
- 6-1 SECURITY_NOTES.md
- 6-2 UPGRADE_NOTES_v3.8.md
- 6-3 Status-File
