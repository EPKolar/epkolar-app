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

### 🐛 Material/Bestellwesen — deleteSuppOrd + deleteCatalog canDo-Gaps (v3.9.328)
**Zeilen:** 14124 (deleteSuppOrd Render) + 14203 (deleteCatalog Handler-Eintritt) + 14220 (deleteCatalog Render)
**Befund:**
- `deleteSuppOrd`: Handler hat `canDo("material_delete")`-Guard, aber Render-Button war IMMER sichtbar → Nicht-Berechtigte sehen Button, klicken, bekommen Permission-Toast (UX-Verwirrung + nutzlos).
- `deleteCatalog`: Handler hatte WEDER `canDo`-Guard NOCH Render-Filter. `_confirmModal` allein ist nicht Defense-in-Depth — programmatischer Aufruf umgeht ihn.

**Risiko:** Bei deleteCatalog: Monteur ruft `deleteCatalog(catId)` aus DevTools-Console → DATANORM-Katalog gelöscht. Server-API hat zwar i.d.R. eigene Auth-Layer, aber Client-Defense-in-Depth fehlte ganz.

**Fix:**
- `deleteSuppOrd`: Render-Button mit `canDo("material_delete",curUser)&&...` gegated.
- `deleteCatalog`: Handler-Eintritt `if(!canDo("material_delete",curUser)){toast(„Keine Berechtigung");return;}` + Render-Button mit `canDo`-Filter.
- Bestehender `_confirmModal` bleibt.

### 📝 Material — addItem manueller Mengen-Parse + delWzPhoto-canDo-Inkonsistenz
- **`addItem`** (Z.13421): `parseFloat(String(r.menge).replace(",","."))||1` — Fallback `||1` maskiert leere Eingabe als 1 Stk. **Risiko:** quantitativ falsche Anforderung ohne Validierungs-Toast. **Vorschlag:** mit Validierungs-Toast bei NaN — nicht jetzt fixen (UX-Entscheidung).
- **`delWzPhoto`** (Z.19225/19813): Render+Handler-Guard ist `isVAdmin` statt `canDo("wz_edit")` wie checkout/checkin. Funktional korrekt, nur inkonsistent. **Vorschlag:** auf `canDo` umstellen bei nächster Wz-Refactor-Welle.

### 📝 Native `confirm()` Legacy-Stellen (Modal-Migration nicht komplett)

Beim Schreiben der Regression-Tests aufgefallen — alte native `confirm()`-Aufrufe sind noch vorhanden. Keine destruktive Wirkung (User-Warnings mit klarem Trotzdem-fortsetzen-Pfad), aber inkonsistent mit dem `_confirmModal`-Standard seit v3.9.11.

- **`logout`-Handler** (Z.5555): 2× native `confirm()` für „N ungespeicherte Änderungen werden VERWORFEN" + „Timer läuft noch — wird VERWORFEN". Konvertierung erfordert async-Umbau der Logout-Sequenz (Auth-Logout muss nach Confirm warten).
- **`saveAs`-Handler ArbeitsscheinView** (Z.6462): 1× native `confirm()` für AS-Duplikat-Warnung („Möglicher Duplikat-AS, trotzdem speichern?"). Liegt im saveAs-Flow vor Submit, einfacher zu konvertieren als Logout.

**Status:** Nicht jetzt fixen (UX-Funktion ist intakt — native confirm() funktioniert). Bei nächster Modal-Round-5-Pass mitnehmen.

### 9 Regression-Tests `tests/test_bughunt_alt_2026_06_12.py`

Verhindert dass die Bug-Hunt-Fixes v3.9.325-328 regressieren:
1. `test_wochenplanung_clearRow_uses_confirmModal` (v3.9.325)
2. `test_wochenplanung_delRow_uses_confirmModal_danger`
3. `test_urlaub_approve_has_admin_guard_and_modal` (v3.9.326)
4. `test_urlaub_reject_has_admin_guard_and_modal_danger`
5. `test_deleteNotif_uses_confirmModal` (v3.9.327)
6. `test_notifs_clear_all_button_uses_confirmModal`
7. `test_deleteSuppOrd_render_has_canDo_guard` (v3.9.328)
8. `test_deleteCatalog_handler_has_canDo_guard`
9. `test_deleteCatalog_render_has_canDo_guard`

Alle 9 grün.

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
