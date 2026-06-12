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

### 🐛 Urlaubsplanung — approve + reject ohne Handler-Guard + _confirmModal (v3.9.326)
**Zeilen:** 14995-14996
**Befund:** `approve(m,d)` und `reject(m,d)` (AbsView) mutieren DB-Status (`absences.status` PUT) ohne `_confirmModal` und ohne Handler-Eingangsguard. Render-Buttons sind isAdmin-gated (Z.15043-15044), aber Handler-Defense-in-Depth fehlte → schneller Klick = irreversible Status-Änderung; programmatischer Aufruf (z.B. via DevTools) hätte canDo umgangen.
**Risiko:** Versehentlicher Klick auf ✅/❌ → Genehmigung/Ablehnung sofort committed. Push-Notification an Mitarbeiter ist raus.
**Fix:** Beide als `async` + Handler-Guard `if(!isAdmin)return;` + `_confirmModal` mit Antrag-Detail im Text. reject mit danger-Variant.

### 🐛 Benachrichtigungen — deleteNotif + „Alle löschen" ohne _confirmModal (v3.9.327)
**Zeilen:** 5432 (`deleteNotif`) + 5861 (Inline-onClick „🗑️ Alle Benachrichtigungen löschen")
**Befund:** Beide Lösch-Pfade in der Notif-Center-Komponente waren ohne Modal. Ein-Klick zum Wegputzen einzelner ODER aller Notifications eines Users.
**Risiko:** Versehentliches Löschen unwiederbringlich (Notif-History weg, SQ.push DELETE / POST clear an Server raus).
**Fix:**
- `deleteNotif` als `async` + `_confirmModal("Benachrichtigung wirklich löschen?", {variant:"danger"})` voran.
- Inline-onClick für „Alle löschen" als `async`-Arrow + `_confirmModal("Alle N Benachrichtigungen wirklich löschen?", {variant:"danger"})` mit Count im Text.

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
