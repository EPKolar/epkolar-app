# Pre-Flight (vor Abreise zwingend abarbeiten)

## Power & Energie

- [ ] Power-Plan auf Höchstleistung: `powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c`
- [ ] Backup aktiver Plan in `scripts\powerplan-backup-baumgmt.txt` (Bat tut das automatisch beim Start)
- [ ] Monitor-Timeout AC: 0; Standby-AC: 0; Disk-AC: 0
- [ ] Netzwerk-Adapter Energieoptionen: "Computer kann das Gerät ausschalten" → AUS
- [ ] Windows-Updates pausiert für 35 Tage (Settings → Update → Pausieren)
- [ ] Auto-Login aktiv (sonst Reboot bricht Hunt ab)
- [ ] AV-Exclusion auf Repo-Pfad UND auf `T:\STOP-BUG-HUNT-BAUMGMT.flag`

## Repo & Branch

- [ ] `git status` clean auf `cc-bug-hunt-eternal/2026-04-26`
- [ ] `git push` erfolgreich (Branch existiert auf origin)
- [ ] Letzter main-Commit notiert: `8c11b41` (v3.8.64)

## Stop-Mechanik (ZWINGEND testen vor Abflug!)

- [ ] **Lokal**: `type nul > T:\STOP-BUG-HUNT-BAUMGMT.flag` → Bat starten → muss innerhalb 60s beenden
- [ ] Flag löschen, Bat neu starten, läuft normal → ok
- [ ] **Remote-Stop-Test**: GitHub-Web auf `main` eine Datei `STOP-BUG-HUNT-BAUMGMT.flag` mit Inhalt "test" committen → Bat muss bei nächstem Iteration-Check beenden
- [ ] Datei wieder löschen auf GitHub

## Token & Verbindung

- [ ] Claude-API-Key aktiv, kein abgelaufenes Limit
- [ ] Internet-Restart-Resilience: WLAN-Adapter manuell aus/ein → Bat muss weiterlaufen
- [ ] **MotorLog-Hunt-Status checken** (parallel laufender Hunt) — Token-Pool geteilt!

## Letzte Aktion vor Abflug

- [ ] Bat starten: `start /B "" scripts\bughunt-eternal-baumgmt.bat`
- [ ] 1× kompletten Sprint-Zyklus abwarten und log prüfen
- [ ] PC NICHT runterfahren

## Konflikt-Vermeidung mit MotorLog (parallel laufender Hunt)

| Item | Baumanagement (DIESER) | MotorLog (anderer Hunt) |
|---|---|---|
| Stop-Flag-File (lokal) | `T:\STOP-BUG-HUNT-BAUMGMT.flag` | `T:\STOP-BUG-HUNT.flag` |
| Stop-Flag-File (remote) | `STOP-BUG-HUNT-BAUMGMT.flag` | `STOP-BUG-HUNT.flag` |
| Bat-Filename | `bughunt-eternal-baumgmt.bat` | `bughunt-eternal.bat` |
| Queue/State-Files | `*-baumgmt.txt` | `*.txt` |
| Sprints/Tag | 4 (reduziert) | 8 (default) |
| Sleep zwischen Sprints | 90 min (5400 s) | 60 min |
| Token-Cooldown | 4h | 1h |
