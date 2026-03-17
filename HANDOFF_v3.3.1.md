# HANDOFF v3.3.1 — EPKolar Auto-Save + Browser-Zurück + Tätigkeit-Fix

## Aktueller Stand (17.03.2026)

**App:** EPKolar v3.3.1 — Baustellenmanagement PWA  
**Live:** https://epkolar.github.io/epkolar-app/  
**Repo:** https://github.com/EPKolar/epkolar-app  
**Supabase:** jiggujpruejkaomgxarp.supabase.co (eu-west-2, MICRO) — **PRO-Version**  
**Entwickler:** Sebastian Günther (Admin-User: admin, Worker-ID: w6)

---

## v3.3.1 Änderungen

### 1. Auto-Save (Wochenplanung + Stundenzettel)

Beide Views speichern jetzt automatisch bei jeder Änderung — der manuelle Speichern-Button wurde entfernt.

| View | Vorher | Nachher |
|------|--------|--------|
| **Wochenplanung** | Manueller Button | Auto-Save per useEffect auf rows, 800ms Debounce |
| **Stundenzettel** | saveAll() Batch-Button | updateEntryHours speichert pro Entry mit 800ms Debounce |

- wpInitRef / wpSaveTimer — verhindert Speichern bei Init/KW-Switch
- stzSaveTimers — pro Entry ein Debounce-Timer
- saveAll() komplett entfernt
- Dezenter Status-Text: Speichert... / Gespeichert

### 2. Browser-Zurück-Button (History API)

**Problem:** SPA-Navigation über React State — Browser-Zurück schließt die ganze PWA.

**Lösung:** history.pushState / popstate bei jeder Navigation.

- _skipPush Counter handles React-batched State Changes
- ProjectShell registriert setView-Wrapper via _regProjView
- Forward-Button re-öffnet Projekte per ID

### 3. Tätigkeit durchgängig (Stundenzettel + Exporte)

**Problem:** Tätigkeit-Feld existierte nur bei Freitext-Typ. Bei Projekt/Störung fehlte es.

**Fixes:** buildDayMap speichert taetigkeit separat, alle 4 Exporte (Wochen-Stz, Tages-Stz, BWB, Detail-XLS) zeigen taetigkeit korrekt, Karten mit gelber Tätigkeit-Zeile, updateEntryHours sendet taetigkeit als task.

**Supabase time_entries:** Hat task Spalte (text). Kein Schema-Change nötig.

---

## Technische Details

- **Bracket-Baseline:** () delta=-2 — unverändert
- **Zeilenzahl:** ~9569
- **SW Cache:** epkolar-v3.3.1
- **APP_VERSION:** 3.3.1-supabase-2026-03-17

## Offene Punkte (aus v3.3.0)

- (A) Pläne + Tickets E2E testen
- (B) Foto-Upload Storage testen
- (C) Kundendaten befüllen
- (D) Duplikat-Projekt löschen
- (E) FinkZeit Standby
