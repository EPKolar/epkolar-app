# DB-BEDARF — RLS Silent-Delete/Divergenz-Audit · 2026-06-11

**✅ ERLEDIGT 2026-06-11 (Sebastian-autorisierte Migration, Chat-Claude-SQL, von CC ausgeführt + verifiziert):**
- **Fund 1** material_orders/items DELETE → `current_user_role() IN (admin,projektleiter,buero)` (war JWT-basiert). ✅
- **Fund 2** supplier_orders DELETE+UPDATE → `current_user_role() IN (admin,projektleiter,buero)` (war `true`/offen). ✅
- **Fund 3 = Variante 3B gewählt:** project_documents INSERT → `auth.role()='authenticated'` (Monteure dürfen jetzt Projekt-Doku hochladen). ✅
- **Client-Abgleich:** `material_delete`-Gate (admin/PL/buero) + `doc_upload` (inkl. Monteur) decken sich mit den neuen Policies → **kein Client-Write nötig.**
- **Fund 4** (whatsapp_messages) bewusst unangetastet (gewollt/System).
Migration self-verifying (Worker-Guard + 3 RAISE-EXCEPTION-Checks), COMMIT erfolgreich, read-only-Matrix bestätigt.

---
**(Original-Audit:)**

**Für Chat-Claude (SQL-Editor) — CC macht KEINE Policy-Writes (Direktive). CC liefert Vorschlag + macht danach Client-Abgleich + read-only Verify.**

Read-only-Audit aller DELETE/UPDATE-Policies gg. die Client-`canDo`-Gates. Gleiches Muster wie der
fahrzeuge_delete-Bug: Client erlaubt → Server blockt → PostgREST liefert 204/0-Zeilen (kein Fehler) →
Client wertet als Erfolg → Datensatz „resurrected" nach Reload. (fahrzeuge_delete ist bereits gefixt.)

## Fund 1 — material_orders + material_items DELETE: falsche Auth-Quelle (kritisch)
Aktuell:
```
USING ((auth.role()='authenticated') AND (((auth.jwt() -> 'app_metadata') ->> 'role') = ANY (ARRAY['admin','projektleiter'])))
```
Problem: nutzt **JWT `app_metadata.role`** statt `auth_role()` (users.role) wie ALLE anderen Tabellen.
Verifiziert: nur **7 von 11** auth.users tragen `app_metadata.role` (Werte admin/monteur/projektleiter) →
die 4 ohne Claim können NICHT löschen, auch buero ist ausgeschlossen. Client `canDo('material_delete')`
= admin/PL/buero → Büro + die 4 claim-losen User laufen still ins Leere.

Fix (an auth_role() + Client angleichen):
```sql
ALTER POLICY material_orders_delete ON public.material_orders
  USING ((auth.role()='authenticated') AND (auth_role() = ANY (ARRAY['admin','projektleiter','buero'])));
ALTER POLICY material_items_delete ON public.material_items
  USING ((auth.role()='authenticated') AND (auth_role() = ANY (ARRAY['admin','projektleiter','buero'])));
-- Policy-Namen ggf. anpassen (pg_policies prüfen). Auch material_*_update prüfen falls jwt-basiert.
```

## Fund 2 — supplier_orders DELETE + UPDATE = `true` (Security/offen)
Aktuell USING = `true` → **jeder authentifizierte User** kann fremde Lieferbestellungen ändern/löschen.
Fix (auf material-berechtigte Rollen einschränken; Client material_order = admin/PL/buero):
```sql
ALTER POLICY <supplier_orders_delete> ON public.supplier_orders
  USING ((auth.role()='authenticated') AND (auth_role() = ANY (ARRAY['admin','projektleiter','buero'])));
ALTER POLICY <supplier_orders_update> ON public.supplier_orders
  USING ((auth.role()='authenticated') AND (auth_role() = ANY (ARRAY['admin','projektleiter','buero'])));
```

## Verifikation nach Run (read-only) — macht CC
```sql
select tablename, cmd, qual from pg_policies
where schemaname='public' and tablename in ('material_orders','material_items','supplier_orders')
order by tablename, cmd;
```

## Danach: Client-Abgleich (CC)
- `canDo('material_delete')` ist bereits admin/PL/buero → nach Fund-1-Fix deckungsgleich, **kein Client-Write nötig**.
  Falls Chat-Claude material-DELETE bewusst enger (z.B. admin/PL) setzt → CC zieht den Client-Gate nach.

## Fund 3 — project_documents INSERT vs Client doc_upload (Monteur-Silent-Fail)
Server INSERT: `auth_role() = ANY(['admin','projektleiter','buero'])`.
Client-Gate `canDo('doc_upload')` = `isA||isPL||isB||isField` → **inkl. Monteur** (Z.3859). Der „📤 Hochladen"-
Button (Dokumentexplorer, Z.12732) ist für Monteure sichtbar → `POST /api/project-documents` (Z.12583) →
Server blockt still → Upload verschwindet. **Entscheidung nötig (Intent):**
- (A) Monteure SOLLEN keine Projekt-Doku hochladen → **Client-Fix (CC, kein DB):** `doc_upload` von
  `isField` befreien (= admin/PL/buero, deckt sich mit Server). Empfohlen, da Server das ohnehin blockt.
- (B) Monteure SOLLEN hochladen → **Server-Fix (Chat-Claude):** project_documents INSERT um isField/
  authenticated erweitern.
→ Sag welche Variante; (A) baue ich client-seitig, (B) ist DB.

## Fund 4 — whatsapp_messages: RLS an, KEIN UPDATE/DELETE-Policy (niedrig)
Deny-all für UPDATE/DELETE. Vermutlich gewollt (System/WhatsApp-Integration, kein User-Flow). Nur falls
ein Code-Pfad whatsapp_messages updaten/löschen will → silent-fail. Zur Kenntnis.

## Kein Befund (geprüft, OK)
- fahrzeuge_delete: bereits gefixt (admin/PL/buero/lagerleitung).
- time_entries: ALL-Policy `is_staff() OR worker_id=current_monteur_id()` → Monteur löscht eigene, Staff alle. OK.
- defects/bautagebuch/checklists/forms/photos/weekplans DELETE = admin/PL/buero → matcht Client. OK.
- plans/tickets/werkzeue DELETE = admin/PL; Client enger/gleich → kein Silent-Fail (Server ≥ Client). OK.
- projects/workers/users/activity_log DELETE = admin-only → matcht Client (isA). OK.
