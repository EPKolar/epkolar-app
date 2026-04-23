# canDo() Permission Matrix · 2026-04-24

**Quelle:** `index.html` L3008-3014 (`function canDo(action,user,ownerId)`).
**Baseline:** Stand Commit `9e8bdae`.
**Methode:** Statische Analyse des Matrix-Objekts `m={...}` + zwei Sonder-Zweige (`zeit_delete`, `form_delete`).

## Rollen-Herkunft

- `user.role` — Haupt-Feld: `admin`, `projektleiter`, `buero`, `obermonteur`, `techniker`, `monteur`
- `user.rolle` (!) — Alt-Feld: `lagerleitung` (wenn `toLowerCase()==="lagerleitung"`)
- `isField = obermonteur || techniker || monteur` (Feld-Personal, alle gleichberechtigt)
- `isLager = rolle==="lagerleitung" || admin || projektleiter` (merged mit A/PL!)
- `isOwn = ownerId && (ownerId===user.monteurId || ownerId===user.name || ownerId===user.id)`

## Matrix (44 Actions · 2 Owner-Zweige)

| Action | admin | pl | büro | om | tech | mont | lager* |
|--------|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| `proj_create` | ✅ | ✅ | ✗ | ✗ | ✗ | ✗ | ✗ |
| `proj_delete` | ✅ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| `proj_archive` | ✅ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| `worker_create` | ✅ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| `worker_delete` | ✅ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| `worker_edit` | ✅ | ✗ | ✅ | ✗ | ✗ | ✗ | ✗ |
| `user_manage` | ✅ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| `as_create` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✗ |
| `as_delete` | ✅ | ✅ | ✅ | ✗ | ✗ | ✗ | ✗ |
| `fz_create` | ✅ | ✅ | ✅ | ✗ | ✗ | ✗ | ✗ |
| `fz_delete` | ✅ | ✅ | ✗ | ✗ | ✗ | ✗ | ✗ |
| `fz_edit` | ✅ | ✅ | ✅ | ✗ | ✗ | ✗ | ✗ |
| `wz_create` | ✅ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| `wz_delete` | ✅ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| `wz_edit` | ✅ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| `plan_create` | ✅ | ✅ | ✗ | ✗ | ✗ | ✗ | ✗ |
| `plan_delete` | ✅ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| `ticket_create` | ✅ | ✅ | ✗ | ✗ | ✗ | ✗ | ✗ |
| `doc_upload` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✗ |
| `doc_delete` | ✅ | ✅ | ✅ | ✗ | ✗ | ✗ | ✗ |
| `folder_delete` | ✅ | ✅ | ✅ | ✗ | ✗ | ✗ | ✗ |
| `zeit_other` | ✅ | ✅ | ✅ | ✗ | ✗ | ✗ | ✗ |
| `zeit_delete_own` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✗ |
| `zeit_delete_any` | ✅ | ✅ | ✅ | ✗ | ✗ | ✗ | ✗ |
| `form_create` | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | ✗ |
| `form_delete_own` | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | ✗ |
| `form_delete_any` | ✅ | ✅ | ✗ | ✗ | ✗ | ✗ | ✗ |
| `mangel_create` | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | ✗ |
| `mangel_delete` | ✅ | ✅ | ✗ | ✗ | ✗ | ✗ | ✗ |
| `bt_create` | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | ✗ |
| `bt_delete` | ✅ | ✅ | ✗ | ✗ | ✗ | ✗ | ✗ |
| `abs_approve` | ✅ | ✅ | ✅ | ✗ | ✗ | ✗ | ✗ |
| `abs_kontingent` | ✅ | ✗ | ✅ | ✗ | ✗ | ✗ | ✗ |
| `admin_panel` | ✅ | ✗ | ✗ | ✗ | ✗ | ✗ | ✅ |
| `auswertungen` | ✅ | ✅ | ✅ | ✗ | ✗ | ✗ | ✗ |
| `offa_export` | ✅ | ✅ | ✅ | ✗ | ✗ | ✗ | ✗ |
| `material_view` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✗ |
| `material_add` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✗ |
| `material_edit` | ✅ | ✅ | ✅ | ✗ | ✗ | ✗ | ✗ |
| `material_delete` | ✅ | ✅ | ✅ | ✗ | ✗ | ✗ | ✗ |
| `material_order` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✗ |
| `view_ek_price` | ✅ | ✅ | ✗ | ✗ | ✗ | ✗ | ✅ |
| `supplier_manage` | ✅ | ✅ | ✗ | ✗ | ✗ | ✗ | ✅ |

**(*)** `lager` = `user.rolle==="lagerleitung"` (pures Alt-Feld, ohne Admin/PL-Merge).

## Owner-Zweige (Runtime-Check)

| Action | admin | pl | büro | om | tech | mont |
|--------|:-:|:-:|:-:|:-:|:-:|:-:|
| `zeit_delete` (generic) | ✅ | ✅ | ✅ | isOwn | isOwn | isOwn |
| `form_delete` (generic) | ✅ | ✅ | ✗ | isOwn | isOwn | isOwn |

## Inkonsistenzen / Beobachtungen

### I1 · `admin_panel` Abweichung von `isLager`
L3010: `admin_panel: isA||(user.rolle||"").toLowerCase()==="lagerleitung"`
— benutzt **raw Rolle**, nicht `isLager`. Daraus folgt: **PL hat keinen admin_panel-Zugang**, obwohl PL anderswo (`view_ek_price`, `supplier_manage`) via `isLager` als Lager-äquivalent behandelt wird.
**Frage:** Absicht oder Copy-Paste? Wenn PL kein Admin-Panel sehen soll, sind `view_ek_price` und `supplier_manage` via `isLager` evtl. zu großzügig.

### I2 · `isLager` hat A+PL bereits inkl.
`isLager = (rolle==="lagerleitung") || isA || isPL` — damit ergibt jedes `isA||isLager` redundant.
`view_ek_price: isA||isPL||isLager` ⇒ äquivalent zu `isA||isPL||raw-lager`. Klar, aber die doppelte A/PL-Erwähnung maskiert die Intention.
`supplier_manage: isA||isLager` ⇒ äquivalent zu `isA||isPL||raw-lager`.
**Empfehlung:** `isLager` umbenennen → `isLagerOrGreater` oder Guard-Logik invertieren (`rawLager` + explizite A/PL-Clauses).

### I3 · Feld-Granularität fehlt
`isField = isOM || isTech || isM` — obermonteur, techniker, monteur sind **über alle 44 Actions identisch berechtigt**. Falls irgendwann nur OM eigene Tickets öffnen dürfen soll (oder ähnlich), muss `isField` aufgelöst werden.

### I4 · `buero` hat keine Field-Action
Buero kann weder `form_create`, `mangel_create`, noch `bt_create`. Falls Büro-Personal bei einem Einsatz mal Formulare nachreicht, geht das nur via Admin. Konsistent mit "Büro = Office-only", aber prüfenswert.

### I5 · `ownerId`-Matching
`isOwn = ownerId===user.monteurId || ownerId===user.name || ownerId===user.id` — drei alternative Felder. Risiko: falls `ownerId` in DB auf `user.id` (UUID) gesetzt ist, funktioniert das; falls auf `user.name` (String), auch. Ambiguität mit User-Namensänderung: nach Rename wird eigener Content möglicherweise als "fremd" klassifiziert.

## Nicht adressiert in canDo()

- `signature_capture` (Block 8 AS-Signatur) — separater Guard in AS-UI
- `photo_upload` — über `doc_upload` inkludiert
- `juprowa_push` — nur über `isAdmin`-Check im Header-Button (nicht canDo)
- `datanorm_upload` — AdminPanel-spezifisch, canDo prüft hier nicht

## Quellen-Inventar (10 Call-Sites)

L4476, L4788 (admin_panel), L5424, L5846 (as_*), L10262 (doc_upload), L10697 (view_ek_price), L10839, L11029, L11102 (material_delete).
Weitere canDo-Calls in Sub-Komponenten evtl. nicht durch diesen Grep erfasst (z. B. in Form-Templates).

## Next Steps (Sebastian)

1. I1 klären: Soll PL `admin_panel` sehen?
2. I5 → ownerId-Policy festlegen (UUID-only?).
3. I3 bei Bedarf später entflechten (kein akuter Bedarf).
