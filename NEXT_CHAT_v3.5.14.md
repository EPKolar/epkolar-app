# NEXT CHAT — ab v3.5.14

## Aktueller Stand (v3.5.14, 22.03.2026)

### Juprowa Phase 1 — KOMPLETT + GETESTET ✅
- Alle 6 E2E-Tests bestanden (KPI-Filter, Sync, Code 11, SB-Persistenz, Dropdown-Darstellung, Büro-Export)
- Code 11→bar_bezahlt Fix eingebaut
- Sync-Idempotenz Fix eingebaut (needsInit statt always-patch)
- Projektnummer Font verbessert (SF Mono Stack)

### JUPROWA Status-Mapping (10 Codes → 8 EPKolar-Status)
| API Code | EPKolar Key | Label |
|----------|-------------|-------|
| 0 | aufgenommen | 📋 aufgenommen |
| 1 | freigegeben | ✅ freigegeben |
| 2 | aufgeschoben | ⏸️ aufgeschoben |
| 3 | in_bearbeitung | 🔧 in Bearbeitung |
| 4 | freigegeben | ✅ freigegeben |
| 5 | erledigt | 🔵 erledigt |
| 10 | abgerechnet | 💰 abgerechnet |
| 11 | bar_bezahlt | 💵 bar bezahlt |
| 15 | bar_bezahlt | 💵 bar bezahlt |
| 20 | storniert | ❌ storniert |

### Aktuelle Juprowa API Status-Verteilung (41 Scheine)
- Code 0 (aufgenommen): 2
- Code 3 (in_bearbeitung): 22
- Code 10 (abgerechnet): 14
- Code 11 (bar_bezahlt): 1
- Code 20 (storniert): 2

---

## Nächste Schritte (priorisiert)

### 1. GitHub Push v3.5.14
- Sebastian pusht index.html + sw.js manuell
- Kein SQL-Migration nötig

### 2. Juprowa Phase 2 — Bidirektional (MIT SEBASTIAN BESPRECHEN!)
**Offene Fragen vor Implementierung:**
- Welche Felder sollen zurückgeschrieben werden? (Status, durchgeführte, Termin, Monteur?)
- Wann? (Sofort / Batch-Push / Auto-Sync)
- Welcher Code für bar_bezahlt: 11 oder 15?
- Gibt es eine Juprowa Write-API? Welche Endpoints?
- Conflict Resolution: Wer gewinnt bei gleichzeitiger Änderung?

### 3. Büro-Export Vorschau-Tabelle
- Sebastian-Feedback: KW×MA×Stunden HTML-Vorschau
- Tätigkeitstext bearbeiten
- KW-Filter, MA ein/ausblenden
- Vorschau-Druck

### 4. Material Umbau (mit Sebastian besprechen!)

### 5. Dashboard-KPIs live

### 6. Weitere Features (Backlog)
- Benachrichtigungen 2.0 (Eskalation)
- Urlaubsplanung visuell
- QR-Code Arbeitsscheine
- Offline-Indikator/Sync-Status
- Multi-Projekt Wochenübersicht PL

---

## Operativ / Bekannte Issues
- **Schober PW = "test1234"** → muss geändert werden
- **Lindhuber PW** noch nicht gesetzt
- **Worker-Mapping:** Nur 3 von 10+ Juprowa-Monteuren gemappt (P011→w1, P008→w4, P005→w5)
- **PASSPORT:** Session-basiert, kann ablaufen → kein Admin-UI zum Erneuern
- **demoUsers-Fallback:** Noch nicht entfernt (Sicherheits-Issue aus v3.5.5)
