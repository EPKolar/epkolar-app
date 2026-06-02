# SQL-Runbook v3953/3954/3919/3959 (Sebastian-Action 2026-06-02)

**Backend:** Supabase `jiggujpruejkaomgxarp`
**Reihenfolge (kritisch):** 3953 → 3954 → 3919 → 3959 (3959 nach Auth-Dashboard-Step)
**Modus:** Idempotent — alle Skripte können mehrfach ausgeführt werden.

---

## STEP 1: `migrate_notifications_rls_v3953.sql` (Riedmann-Bug Fix)

**Zweck:** UPDATE-Policy fehlt → Monteure können Notifications nicht als gelesen markieren. Polling überschreibt optimistic state.

**Ausführen via Supabase SQL Editor:**
1. Dashboard → SQL Editor → New Query
2. Inhalt von `sql/migrate_notifications_rls_v3953.sql` einfügen
3. Run
4. Verify:
```sql
SELECT polname, polcmd, polqual, polwithcheck
FROM pg_policy
WHERE polrelid = 'public.notifications'::regclass;
```
Erwartet: 5 Policies (SELECT/UPDATE-own/UPDATE-admin/DELETE/INSERT)

**Quick-Smoke nach Run:**
```sql
-- Als Monteur-Test-User: lese eigene Notifs
SELECT id, user_id, read, title FROM notifications LIMIT 5;
-- Update sollte funktionieren (vorher: silent fail)
UPDATE notifications SET read=1 WHERE user_id IN
  (SELECT id FROM users WHERE auth_user_id = auth.uid()) AND read=0;
```

---

## STEP 2: `migrate_supplier_articles_safe_v3954.sql` (B-006 EK-Preise Security)

**Zweck:** Monteure dürfen `ek_preis` NICHT sehen. View mit CASE-WHEN-Maskierung.

**Ausführen:**
1. SQL Editor → New Query
2. Inhalt von `sql/migrate_supplier_articles_safe_v3954.sql` einfügen
3. Run

**Verify:**
```sql
-- Als Monteur (z.B. nach login als kiener):
SELECT id, bezeichnung, vk_preis, ek_preis FROM supplier_articles_safe LIMIT 3;
-- ek_preis sollte NULL sein

-- Als Admin (guenther):
-- ek_preis sollte echten Wert zeigen
```

---

## STEP 3: `migrate_whatsapp_v3919.sql` (WhatsApp Scaffolding)

**Zweck:** 3 Tables für WhatsApp-Integration (config, templates, messages).

**Ausführen:**
1. SQL Editor → Run der Datei
2. Verify:
```sql
SELECT count(*) FROM whatsapp_templates;
-- Erwartet: 2 Seed-Templates (epkolar_as_done, epkolar_appt_confirm)
SELECT count(*) FROM whatsapp_config;
-- Erwartet: 0 (Sebastian füllt via UI)
```

**Sebastian-Action (nach SQL):**
1. Meta Business Console: Templates `epkolar_as_done` + `epkolar_appt_confirm` anlegen + approven lassen
2. App → Einstellungen → 📱 WhatsApp → Credentials + Toggle aktivieren

---

## STEP 4: Kiener Auth-Dashboard + `migrate_user_kiener_v3959.sql`

### 4.1 Auth-Dashboard FIRST (vor SQL):
1. Supabase Dashboard → **Authentication → Users**
2. **+ Add user**
3. Felder:
   - **Email:** `kiener@ep-kolar.at`
   - **Password:** Sebastian-Choice (z.B. `Test1234!` als Initial-PW, User muss bei Login ändern)
   - **Auto Confirm User:** ✅ ON
4. Save
5. UUID kopieren aus der neuen Row (z.B. `aaaa-bbbb-cccc-dddd-eeeeeeeeeeee`)

### 4.2 UUID in SQL ersetzen:
Im File `sql/migrate_user_kiener_v3959.sql`:
- Suche `:AUTH_UUID`
- Ersetze mit der UUID aus Step 4.1
- (ALTERNATIV: einfach Skript ausführen — der UPDATE-Block holt UUID per Email-Lookup nach, BLOCK 2 INSERT würde dann mit Placeholder fehlschlagen, ist aber als ON CONFLICT DO UPDATE definiert, kein Schaden)

### 4.3 SQL ausführen:
1. SQL Editor → Run
2. Verify (uncomment BLOCK 6 SELECT):
```sql
SELECT
  u.id, u.username, u.name, u.email, u.role, u.active,
  u.monteur_id, u.auth_user_id,
  CASE WHEN u.password_hash IS NULL THEN '⚠ kein PW-Hash' ELSE '✓ PW-Hash gesynct' END AS pw_status,
  w.name AS worker_name, w.role AS worker_role,
  k.urlaub AS urlaub_tage, k.stunden AS urlaub_stunden, k.woche AS arbeitswoche_h
FROM public.users u
LEFT JOIN public.workers w ON w.id = u.monteur_id
LEFT JOIN public.urlaubskontingent k ON k.worker_id = u.monteur_id AND k.jahr = 2026
WHERE u.id = 'u10';
```

Erwartet:
- pw_status = `✓ PW-Hash gesynct`
- worker_name = `Kiener Bernd`
- urlaub_tage = `25`, urlaub_stunden = `192.5`, arbeitswoche_h = `38.5`

### 4.4 Login-Test:
1. App → Login: `kiener` / `Test1234!`
2. Sollte funktionieren als Monteur-User
3. Erwartet: nur eigene AS sichtbar (v3.9.23 Permission-Filter), Material-Katalog ohne EK (v3.9.54)

---

## STEP 5: End-to-End Live-Smoke

Nach allen 4 Migrations ausgeführt:

### 5.1 Riedmann/Kiener Mark-as-read Test:
1. Login als kiener (oder anderer Monteur)
2. Notifications-Panel öffnen
3. "Alle gelesen" → unread-Counter → 0
4. **30s warten** (60s-Polling-Cycle)
5. Counter bleibt 0 ✓

### 5.2 EK-Preise Test:
1. Login als kiener
2. Material-Tab öffnen
3. **DevTools → Network** → supplier_articles-Request
4. Response: `ek_preis: null` für alle Items ✓
5. Login als guenther (admin)
6. Same View → `ek_preis: <number>` für alle Items ✓

### 5.3 Offline-Queue Test:
1. DevTools → Network → Offline
2. Create new AS (sollte SQ.push triggern)
3. Banner: "📤 1 Änderung wartet auf Sync"
4. **Browser-Tab schließen**, neu öffnen
5. Banner: noch da, "1 Änderung wartet"
6. DevTools → Network → Online
7. ~2s später: Sync → Banner verschwindet
8. AS jetzt in Supabase ✓

### 5.4 Visual-Smoke v3.9.50-58:
- HomeView Mein-Tag: nur 2 KPIs (AS heute + Stunden KW) ✓
- Urlaub: kleiner 🏖️ Button top-right (statt KPI-Kachel) ✓
- Timer/Material: Primary equal-width ✓
- Foto: schmaler Icon-Button (sekundär) ✓
- LoginScreen: gradient-Background ✓

---

## ROLLBACK (manuell, NUR im Notfall)

```sql
-- 3959 Kiener
DELETE FROM public.urlaubskontingent WHERE id='u10';
DELETE FROM public.users WHERE id='u10';
DELETE FROM public.workers WHERE id='w10';
-- auth.users via Dashboard löschen

-- 3954 EK-Safe
DROP VIEW IF EXISTS supplier_articles_safe;
DROP FUNCTION IF EXISTS can_see_ek();
ALTER TABLE supplier_articles DISABLE ROW LEVEL SECURITY;

-- 3953 Notifications-RLS
DROP POLICY IF EXISTS notifications_select_own_or_admin ON notifications;
DROP POLICY IF EXISTS notifications_update_own_read ON notifications;
DROP POLICY IF EXISTS notifications_update_admin ON notifications;
DROP POLICY IF EXISTS notifications_delete_own_or_admin ON notifications;
DROP POLICY IF EXISTS notifications_insert_admin ON notifications;
DROP FUNCTION IF EXISTS is_admin();

-- 3919 WhatsApp
DROP TABLE IF EXISTS whatsapp_messages;
DROP TABLE IF EXISTS whatsapp_templates;
DROP TABLE IF EXISTS whatsapp_config;
```

---

## QUICK-COMMAND-LIST (Copy-Paste in SQL-Editor)

Aufeinanderfolgend in 4 separaten Queries:

```sql
-- 1
\i sql/migrate_notifications_rls_v3953.sql
-- 2
\i sql/migrate_supplier_articles_safe_v3954.sql
-- 3
\i sql/migrate_whatsapp_v3919.sql
-- 4 (vorher Auth-Dashboard!)
\i sql/migrate_user_kiener_v3959.sql
```

(`\i` funktioniert nur in `psql` CLI. Im Supabase Dashboard SQL Editor: Inhalt jeweils manuell einfügen + Run.)
