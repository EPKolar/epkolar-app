# Bug-Hunt Alt-Flächen 2026-06-12 (autonom)

Scope: Bereiche, die seit Wochen niemand reviewt hat — **NICHT** v3.9.306-324 (frisch geprüft). Bereich-Checklist je Befund (a-g):

| Code | Check |
|---|---|
| (a) | tote/duplizierte Event-Handler |
| (b) | fehlende `_confirmModal` bei destruktiven Aktionen |
| (c) | fehlende canDo-Guards (Render UND Funktions-Ebene) |
| (d) | NaN-Risiken (alles durch `_n()`?) |
| (e) | 38.5h-Regel: irgendwo hardcoded 40h? |
| (f) | Feld-Prioritäten (`taetigkeit\|\|task`, `bemerkung\|\|description`, `datum\|\|date`) konsistent |
| (g) | `kunde_freigabe` als INTEGER 0/1 behandelt |

Status-Legende: 🐛 = echter Bug (gefixt) · 📝 = Zweifelsfall (nur dokumentiert) · ✅ = clean

## Befunde

### 🐛 Wochenplanung — clearRow + delRow ohne _confirmModal (v3.9.325)
**Zeilen:** 14549-14550
**Befund:** `clearRow(id)` (Zeile leeren — alle Mitarbeiter+Fahrzeug-Zuordnungen für die KW weg) und `delRow(id)` (Zeile löschen) waren ein-Klick-destruktiv. Modal-Migration-Lücke seit v3.9.11.
**Risiko:** Versehentliche Bulk-Löschung der Wochenplanung-Zeile, kein Recovery.
**Fix:** Beide als `async` + `_confirmModal` (delRow danger-Variant). Internals unverändert.

---

## Bereich-Status

| Bereich | Reviewer | Status |
|---|---|---|
| Urlaubsplanung | – | ⏳ |
| Wochenplanung | – | ⏳ |
| Material/Bestellwesen | – | ⏳ |
| Werkzeuge | – | ⏳ |
| Benachrichtigungen | – | ⏳ |
| Bautagebuch | – | ⏳ |
| Monatsabrechnung-UI | – | ⏳ |

## Strikte Schutz-Liste (NICHT ANFASSEN)
- Tank-Flow / `parseTankBeleg` / `addTank` / Kontroll-Dialog / km-Sperre / 0-rows-Safeguard
- `_juprowaPush` / Juprowa-Phase-1-Pull
- RLS-Client-Labels `_RLS_SILENT_DENIAL_LABELS`
- alles aus v3.9.306-324 ohne expliziten Auftrag
