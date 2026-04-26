# Stop-Procedure (von unterwegs)

## Schnelle Stop-Methoden (jede für sich ausreichend)

### Methode 1 — Lokal-Flag (wenn du Remote-Zugriff hast)

1. RDP/AnyDesk auf den Hunt-PC
2. PowerShell: `New-Item -Path "T:\STOP-BUG-HUNT-BAUMGMT.flag" -ItemType File`
3. Bat beendet binnen 60s

### Methode 2 — GitHub-Web-Commit (Empfohlen wenn nur Smartphone)

1. https://github.com/EPKolar/epkolar-app öffnen
2. Branch wechseln auf **`main`** (NICHT den Hunt-Branch!)
3. Add-File → Create-New-File
4. Filename: `STOP-BUG-HUNT-BAUMGMT.flag`
5. Inhalt: `stop` (egal was, Hauptsache vorhanden)
6. Commit direkt auf main
7. Bat checkt bei jedem Iteration-Start mit `git fetch origin main` und beendet wenn Datei vorhanden

### Methode 3 — Process-Kill (nur Notfall)

- Task-Manager → `bughunt-eternal-baumgmt.bat` killen
- ⚠ **WARNUNG**: Power-Plan-Restore unterbleibt → manuell zurücksetzen via PRE_FLIGHT-Anweisung
- Auch Anti-Sleep-PowerShell-Prozess `BUGHUNT-AntiSleep-Baumgmt` killen

## Was passiert nach Stop?

- Bat schreibt `STOPPED at <timestamp>` ans Ende von `docs/bug-hunt/REPORT.md`
- Bat restored Power-Plan aus `scripts\powerplan-backup-baumgmt.txt`
- Anti-Sleep-Mechanismen werden zurückgenommen
- Letzter laufender Sprint wird **ABGEBROCHEN** (kein "fertig schreiben") → Sprint-State bleibt unfinished, beim Re-Entry kann das Sprint mit Resume-Flag fortgesetzt werden

## Unterschied zu MotorLog-Hunt-Stop

⚠ **WICHTIG**: Ein Stop-Flag mit Filename `STOP-BUG-HUNT.flag` (ohne `-BAUMGMT`-Suffix) stoppt **NUR** den MotorLog-Hunt, **NICHT** diesen Baumanagement-Hunt.

Beide Hunts müssen separat gestoppt werden:

| Aktion | MotorLog | Baumanagement |
|---|---|---|
| Lokal | `T:\STOP-BUG-HUNT.flag` | `T:\STOP-BUG-HUNT-BAUMGMT.flag` |
| Remote (Web-Commit) | `STOP-BUG-HUNT.flag` | `STOP-BUG-HUNT-BAUMGMT.flag` |
