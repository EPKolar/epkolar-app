# Permission Matrix v3.7

Generiert aus ROLES-Config (Line 1508-1517) und canDo()-Action-Map (Line 2330-2335) in index.html.

## Rollen (aus `const ROLES`)

| Code | Label | Farbe | Icon |
|---|---|---|---|
| `admin` | Administrator | #ef4444 | 👑 |
| `projektleiter` | Projektleiter | #f97316 | 🏗️ |
| `buero` | Büro | #6366f1 | 📋 |
| `obermonteur` | Obermonteur | #a855f7 | ⭐ |
| `techniker` | Techniker | #0ea5e9 | 🔬 |
| `monteur` | Monteur | #3b82f6 | 🔧 |
| `helfer` | Helfer | #22c55e | 👷 |
| `viewer` | Nur Lesen | #71717a | 👁️ |

## Tab-Visibility (aus `ROLES[x].modules`)

| Tab/Modul | admin | projektleiter | buero | obermonteur | techniker | monteur | helfer | viewer |
|---|---|---|---|---|---|---|---|---|
| 🏠 Home (`_home`) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| 👑 Chef (`_chef`) | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| 🏗️ Projekte | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| 📋 Arbeitsscheine | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ |
| 📅 Wochenplanung | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ |
| ⏱️ Zeiterfassung | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ |
| 🏖️ Urlaub | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| 📄 Monatsabrechnung (`stunden`) | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ |
| 🚐 Fahrzeuge | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ |
| 🔧 Werkzeuge | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ | ✗ |
| 👷 Mitarbeiter | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ |
| 📊 Auswertungen | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ |
| 🔌 Einstellungen (`_settings`) | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | ✓ |
| 📋 Büro-Export | ✓ | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ |
| ⚙️ Admin | ✓ | ✗ (außer `admin_panel` für Lagerleitung) | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |

**Hinweise**:
- `_settings` Gate: `!(role==="monteur"||role==="helfer")` → monteur+helfer SEHEN nicht. (siehe Line 3730)
- `_chef` Gate: `role==="admin"` exklusiv (Line 3729).
- Admin-Tab: zusätzlich via `canDo("admin_panel")` für Lagerleitung (siehe Rolle-Feld `rolle`, nicht `role`!)

## Action-Matrix (aus `canDo(action, user)`)

Gruppierung für Übersichtlichkeit. Detail in Line 2332 `const m={...}`.

### Projekte
| Action | A | PL | B | OM | T | M | H |
|---|---|---|---|---|---|---|---|
| proj_create | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ |
| proj_delete | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| proj_archive | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |

### Arbeitsscheine
| Action | A | PL | B | OM | T | M | H |
|---|---|---|---|---|---|---|---|
| as_create | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ |
| as_delete | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ |

### Fahrzeuge/Werkzeuge
| Action | A | PL | B | OM | T | M | H |
|---|---|---|---|---|---|---|---|
| fz_create/edit | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ |
| fz_delete | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ |
| wz_create/delete/edit | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |

### Material
| Action | A | PL | B | OM | T | M | H |
|---|---|---|---|---|---|---|---|
| material_view | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ |
| material_add | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ |
| material_edit/delete/order | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ |
| view_ek_price | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ (+ Lagerleitung via isLager) |
| supplier_manage | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ (+ Lagerleitung) |

### Zeiterfassung/Formulare
| Action | A | PL | B | OM | T | M | H |
|---|---|---|---|---|---|---|---|
| zeit_other (fremde Einträge) | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ |
| zeit_delete_own | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ |
| zeit_delete_any | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ |
| form_create | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | ✗ |
| form_delete_own | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | ✗ |
| form_delete_any | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ |

### Mängel/Bautagebuch
| Action | A | PL | B | OM | T | M | H |
|---|---|---|---|---|---|---|---|
| mangel_create | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | ✗ |
| mangel_delete | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ |
| bt_create | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | ✗ |
| bt_delete | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ |

### User-Management
| Action | A | PL | B | OM | T | M | H |
|---|---|---|---|---|---|---|---|
| user_manage | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| worker_create | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| worker_edit | ✓ | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ |
| worker_delete | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| abs_approve | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ |
| abs_kontingent | ✓ | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ |

### Export/Audit
| Action | A | PL | B | OM | T | M | H |
|---|---|---|---|---|---|---|---|
| auswertungen | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ |
| offa_export | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ |
| admin_panel | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ (+ Lagerleitung) |
| doc_upload | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ |
| doc_delete | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ |

## RLS-Scope (aus B-007 Policies — sql/B006b_B007_FINAL.sql)

**Row-Level-Security filtert zusätzlich zur Client-Permission**:
- `arbeitsscheine`: Monteur sieht nur wo `monteur=current_monteur_id()`, Staff sieht alle
- `time_entries`: Monteur sieht nur wo `worker_id=current_monteur_id()`, Staff alle
- `notifications`: User sieht nur eigene
- `absences`: Monteur sieht nur eigene, Staff alle
- `as_checklist`, `as_kommentare`: Monteur nur eigener AS (via JOIN), Staff alle
- `fahrtenbuch`: Monteur nur eigene, Staff alle
- `worker_kompetenzen`: Monteur nur eigene, Staff alle
- `users`: Non-Staff sieht nur self (durch `is_staff()` OR `id = current_user_pk()`)

## Gefundene Abweichungen (IST vs SOLL)

**Keine bekannten Abweichungen** zum aktuellen SOLL-Stand.

Sebastian kann via `window._rlsAudit()` (Block 16) live prüfen, ob RLS-Scope je nach Rolle dem erwarteten Muster folgt.

## Monteur-spezifisches: "nur eigene" Durchsetzung

| Wo | Mechanismus |
|---|---|
| AS-Liste | Client: `isMonteurRole&&a.monteur!==curUser.monteurId` filter (Line ~4302) + RLS Policy |
| Zeiterfassung | Client filter + RLS |
| Urlaub | Client filter + RLS |
| Mangel-Foto-Upload | captureAndQueue übergibt worker_id, RLS erzwingt |

## Audit-Queries für Sebastian

```js
// in Browser Console nach Login
window._b017check()   // window-Exposure-Audit
window._s8Suite()     // Auth-Konsistenz (inkl. T-B020 Soft-Render-Check)
window._rlsAudit()    // Live RLS-Probe-Queries (nach Block 16)
```

SQL im Supabase-Editor:
```sql
-- Welche User in welcher Rolle?
SELECT id, username, role, monteur_id FROM public.users ORDER BY role, id;

-- Welcher User sieht welche AS? (RLS-ausgeführt)
SET ROLE authenticated;
SET LOCAL request.jwt.claims = '{"role":"authenticated","sub":"<uuid>"}';
SELECT count(*) FROM arbeitsscheine;
RESET ROLE;
```
