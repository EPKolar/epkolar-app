# Re-Entry nach Rückkehr

## Schritt 1 · State-Inventur

```bash
cd "T:\05_Claude\02_Baumanagment & Zeiterfassungs - APP\03_Repos\epkolar-app"
git fetch --all
git checkout cc-bug-hunt-eternal/2026-04-26
git log --oneline | head -30
```

## Schritt 2 · Report durchgehen

- `docs/bug-hunt/REPORT.md` im Editor öffnen
- **Nur die NEUESTE "Master-Index"-Sektion** zählt zur Übersicht (alte sind Audit-Trail)
- Filter-Strategie:
  - **HIGH + P1** → SOFORT triagieren, eigener Hotfix-Branch
  - **HIGH + P2** → in nächsten Sprint einplanen
  - **HIGH + P3** → Backlog
  - **MEDIUM** → 1× re-verifizieren bevor Aufwand
  - **LOW + DISPUTED** → mit jemandem diskutieren oder ignorieren
  - **NOISE** → ignorieren

## Schritt 3 · Disposition setzen

Pro Finding eintragen:

- `Reviewed-by-Sebastian: YES`
- `Status: Open / Fixed / Won't-Fix / Backlog / False-Positive`
- Optional Notiz

**Tipp**: Im REPORT.md mit Suchen+Ersetzen `Reviewed-by-Sebastian: NO` → `Reviewed-by-Sebastian: YES` für ganze Sprints, falls man durchgegangen ist.

## Schritt 4 · Hunt fortsetzen oder stoppen

- **FORTSETZEN**: STOP-Flag entfernen (lokal + remote), Bat neu starten
- **STOPPEN**: Branch behalten als Audit-Archiv. Findings in normales Backlog überführen. Branch erst löschen wenn alle reviewt.

## Schritt 5 · Findings-zu-Fix-Pipeline

- Pro HIGH-Finding einen **normalen Fix-Run** via CC auf eigenem Hotfix-Branch
- **NICHT im Hunt-Branch fixen** (Hunt = nur Doku)
- Nach Fix: Hunt-Branch-Eintrag auf `Status: Fixed in <commit-sha>` setzen

## Schritt 6 · Hunt-Logfiles

Logs liegen in `scripts/`:

- `bughunt-log-baumgmt.txt` — Sprint-Start/Ende, Failures, Cooldowns
- `bughunt-state-baumgmt.txt` — SPRINT_COUNTER, FAIL_COUNT, LAST_SUCCESS
- `bughunt-last-output-baumgmt.txt` — letzte CC-CLI-Ausgabe (für Failure-Diagnose)
- `powerplan-backup-baumgmt.txt` — Power-Plan-GUID vor Hunt-Start (für Restore)

## Schritt 7 · Branch-Cleanup nach voll-reviewt

```bash
git checkout main
git branch -d cc-bug-hunt-eternal/2026-04-26  # local
git push origin --delete cc-bug-hunt-eternal/2026-04-26  # remote
```

(Nur wenn alle Findings disposition-gesetzt sind UND in Backlog/Fixed/Won't-Fix überführt!)
