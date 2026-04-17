# B-007 Monteur-RLS Fix — Plan

**Datum:** 18.04.2026
**Basiert auf:** Live-Audit gegen Supabase (riedmann eingeloggt, sieht 54/36/649 Rows)
**Status Vorher:** Monteur sieht alle Daten aller Kollegen (B-007 = HIGH SEVERITY Privacy-Leak)

---

## Betroffene Tabellen + Zielverhalten

| Tabelle | Schlüssel-Spalte | Monteur sieht | Admin/PL/Büro sieht |
|---------|-----------------|---------------|---------------------|
| `arbeitsscheine` | `monteur` = `w<N>` | nur eigene (`monteur = own_worker_id`) | alles |
| `time_entries` | `worker_id` = `w<N>` | nur eigene | alles |
| `notifications` | `user_id` = `u<N>` (PK von public.users) | nur eigene | nur eigene (auch Admins nur eigene Benachrichtigungen) |
| `as_checklist` | `as_id` (→ AS) | nur von eigenen AS | alles |
| `as_kommentare` | `as_id` (→ AS) | nur von eigenen AS | alles |
| `urlaubsantraege` | `worker_id` | nur eigene | alles |
| `fahrtenbuch` | `worker_id` | nur eigene | alles |
| `worker_kompetenzen` | `worker_id` | nur eigene lesbar (alle sehen Kompetenzen der anderen Monteure für AS-Zuweisung) | alles, Admin-Write |

---

## Helper-Funktionen (einmal anlegen)

```sql
-- Sichere Helper für RLS-Policies. SECURITY DEFINER → umgehen eigene RLS der users-Tabelle.
CREATE OR REPLACE FUNCTION public.current_monteur_id() RETURNS text AS $$
  SELECT monteur_id FROM public.users WHERE auth_user_id = auth.uid() LIMIT 1;
$$ LANGUAGE sql SECURITY DEFINER STABLE;

CREATE OR REPLACE FUNCTION public.current_user_role() RETURNS text AS $$
  SELECT role FROM public.users WHERE auth_user_id = auth.uid() LIMIT 1;
$$ LANGUAGE sql SECURITY DEFINER STABLE;

CREATE OR REPLACE FUNCTION public.current_user_pk() RETURNS text AS $$
  SELECT id FROM public.users WHERE auth_user_id = auth.uid() LIMIT 1;
$$ LANGUAGE sql SECURITY DEFINER STABLE;

-- Shortcut: darf alles? (admin/projektleiter/buero)
CREATE OR REPLACE FUNCTION public.is_staff() RETURNS boolean AS $$
  SELECT (SELECT role FROM public.users WHERE auth_user_id = auth.uid() LIMIT 1) IN ('admin','projektleiter','buero');
$$ LANGUAGE sql SECURITY DEFINER STABLE;

GRANT EXECUTE ON FUNCTION public.current_monteur_id() TO authenticated;
GRANT EXECUTE ON FUNCTION public.current_user_role()  TO authenticated;
GRANT EXECUTE ON FUNCTION public.current_user_pk()    TO authenticated;
GRANT EXECUTE ON FUNCTION public.is_staff()           TO authenticated;
```

---

## Policy-Set (per Tabelle)

### arbeitsscheine
```sql
ALTER TABLE public.arbeitsscheine ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "authenticated_read"               ON public.arbeitsscheine;
DROP POLICY IF EXISTS "authenticated_read_arbeitsscheine" ON public.arbeitsscheine;
DROP POLICY IF EXISTS "role_filtered_as"                  ON public.arbeitsscheine;
DROP POLICY IF EXISTS "role_filtered_as_read"             ON public.arbeitsscheine;
DROP POLICY IF EXISTS "role_filtered_as_write"            ON public.arbeitsscheine;

CREATE POLICY "role_filtered_as_read" ON public.arbeitsscheine
  FOR SELECT TO authenticated
  USING (is_staff() OR monteur = current_monteur_id());

CREATE POLICY "role_filtered_as_write" ON public.arbeitsscheine
  FOR ALL TO authenticated
  USING (is_staff() OR monteur = current_monteur_id())
  WITH CHECK (is_staff() OR monteur = current_monteur_id());
```

### time_entries
```sql
ALTER TABLE public.time_entries ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "authenticated_read" ON public.time_entries;
DROP POLICY IF EXISTS "role_filtered_te_read" ON public.time_entries;
DROP POLICY IF EXISTS "role_filtered_te_write" ON public.time_entries;

CREATE POLICY "role_filtered_te_read" ON public.time_entries
  FOR SELECT TO authenticated
  USING (is_staff() OR worker_id = current_monteur_id());

CREATE POLICY "role_filtered_te_write" ON public.time_entries
  FOR ALL TO authenticated
  USING (is_staff() OR worker_id = current_monteur_id())
  WITH CHECK (is_staff() OR worker_id = current_monteur_id());
```

### notifications
```sql
ALTER TABLE public.notifications ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "own_notifications" ON public.notifications;
DROP POLICY IF EXISTS "own_notifs" ON public.notifications;
DROP POLICY IF EXISTS "own_notifs_read" ON public.notifications;
DROP POLICY IF EXISTS "own_notifs_write" ON public.notifications;
DROP POLICY IF EXISTS "any_auth_insert" ON public.notifications;

-- Jeder darf INSERT (z.B. Admin-PushNotif, Mention-Notif an andere)
CREATE POLICY "any_auth_insert" ON public.notifications
  FOR INSERT TO authenticated WITH CHECK (true);

-- Jeder sieht/ändert nur eigene
CREATE POLICY "own_notifs_read" ON public.notifications
  FOR SELECT TO authenticated USING (user_id = current_user_pk());

CREATE POLICY "own_notifs_write" ON public.notifications
  FOR UPDATE TO authenticated
  USING (user_id = current_user_pk())
  WITH CHECK (user_id = current_user_pk());

CREATE POLICY "own_notifs_delete" ON public.notifications
  FOR DELETE TO authenticated USING (user_id = current_user_pk());
```

### urlaubsantraege
```sql
ALTER TABLE public.urlaubsantraege ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "auth all" ON public.urlaubsantraege;
DROP POLICY IF EXISTS "role_filtered_urlaub" ON public.urlaubsantraege;

CREATE POLICY "urlaub_read" ON public.urlaubsantraege
  FOR SELECT TO authenticated
  USING (is_staff() OR worker_id = current_monteur_id());

CREATE POLICY "urlaub_insert" ON public.urlaubsantraege
  FOR INSERT TO authenticated
  WITH CHECK (worker_id = current_monteur_id() OR is_staff());

CREATE POLICY "urlaub_update" ON public.urlaubsantraege
  FOR UPDATE TO authenticated
  USING (is_staff() OR (worker_id = current_monteur_id() AND status = 'beantragt'))
  WITH CHECK (is_staff() OR (worker_id = current_monteur_id() AND status = 'beantragt'));

CREATE POLICY "urlaub_delete" ON public.urlaubsantraege
  FOR DELETE TO authenticated
  USING (is_staff() OR (worker_id = current_monteur_id() AND status = 'beantragt'));
```

### fahrtenbuch
```sql
ALTER TABLE public.fahrtenbuch ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "auth all" ON public.fahrtenbuch;

CREATE POLICY "fahrtenbuch_read" ON public.fahrtenbuch
  FOR SELECT TO authenticated
  USING (is_staff() OR worker_id = current_monteur_id());

CREATE POLICY "fahrtenbuch_write" ON public.fahrtenbuch
  FOR ALL TO authenticated
  USING (is_staff() OR worker_id = current_monteur_id())
  WITH CHECK (is_staff() OR worker_id = current_monteur_id());
```

### as_checklist (via as_id → arbeitsscheine RLS)
```sql
ALTER TABLE public.as_checklist ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "auth all" ON public.as_checklist;

CREATE POLICY "checklist_read" ON public.as_checklist
  FOR SELECT TO authenticated
  USING (is_staff() OR EXISTS(SELECT 1 FROM arbeitsscheine a WHERE a.id = as_id AND a.monteur = current_monteur_id()));

CREATE POLICY "checklist_write" ON public.as_checklist
  FOR ALL TO authenticated
  USING (is_staff() OR EXISTS(SELECT 1 FROM arbeitsscheine a WHERE a.id = as_id AND a.monteur = current_monteur_id()))
  WITH CHECK (is_staff() OR EXISTS(SELECT 1 FROM arbeitsscheine a WHERE a.id = as_id AND a.monteur = current_monteur_id()));
```

### as_kommentare (analog)
```sql
ALTER TABLE public.as_kommentare ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "auth all" ON public.as_kommentare;

CREATE POLICY "komm_read" ON public.as_kommentare
  FOR SELECT TO authenticated
  USING (is_staff() OR EXISTS(SELECT 1 FROM arbeitsscheine a WHERE a.id = as_id AND a.monteur = current_monteur_id()));

CREATE POLICY "komm_insert" ON public.as_kommentare
  FOR INSERT TO authenticated
  WITH CHECK (autor_id = current_user_pk());

CREATE POLICY "komm_update_delete" ON public.as_kommentare
  FOR ALL TO authenticated
  USING (is_staff() OR autor_id = current_user_pk());
```

### worker_kompetenzen
```sql
ALTER TABLE public.worker_kompetenzen ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "auth all" ON public.worker_kompetenzen;

-- Alle Auth-User dürfen Kompetenzen aller Monteure lesen (für AS-Zuweisung)
CREATE POLICY "komp_read_all" ON public.worker_kompetenzen
  FOR SELECT TO authenticated USING (true);

-- Schreiben nur Admin
CREATE POLICY "komp_write_admin" ON public.worker_kompetenzen
  FOR ALL TO authenticated
  USING (is_staff()) WITH CHECK (is_staff());
```

---

## Verifikation nach SQL-Run

```javascript
// In Browser-Console als riedmann eingeloggt:
(async()=>{
  const tests=[];
  const r1=await fetch('https://jiggujpruejkaomgxarp.supabase.co/rest/v1/arbeitsscheine?select=id',{headers:window._sbH()});
  const d1=await r1.json();
  tests.push({t:'AS nur eigene',pass:d1.length===0,got:d1.length}); // riedmann hat 0 eigene AS

  const r2=await fetch('https://jiggujpruejkaomgxarp.supabase.co/rest/v1/time_entries?select=id',{headers:window._sbH()});
  const d2=await r2.json();
  tests.push({t:'ZE nur eigene',pass:d2.length===0,got:d2.length});

  const r3=await fetch('https://jiggujpruejkaomgxarp.supabase.co/rest/v1/notifications?select=id',{headers:window._sbH()});
  const d3=await r3.json();
  tests.push({t:'Notif nur eigene',pass:d3.length<=10,got:d3.length}); // <=10 eigene notif

  console.table(tests);
})();
```

**Erwartet:**
- AS nur eigene: 0 (riedmann hat keine zugewiesenen AS)
- ZE nur eigene: 0 (keine eigenen time_entries)
- Notif nur eigene: sollte <<649 sein (ggf. nur die für u9)

---

## Potenzielle Seiteneffekte (Code-Impact)

**Bestehender Frontend-Code filtert schon client-seitig:**
- `arbeitsscheine`: Zeile 4113 `if(isMonteurRole&&!isAdmin&&a.monteur!==curUser.monteurId) return false;`
- HomeView `myProjects`: filtert client-seitig
- ZE: `entries.filter(e=>e.worker===selWorker)` etc.

Das bedeutet **RLS wird die Liste dünner machen**, aber der Client filtert sowieso noch drüber. Kein App-Break zu erwarten.

**Ein möglicher Break:**
- Juprowa-Sync läuft aktuell mit service_role-Key im Edge-Function — umgeht RLS, also kein Problem
- Client-seitiger Pull (`_juprowaSync`) nutzt aber auch `_sbGet("arbeitsscheine")` — nach RLS-Fix: als Monteur nur noch eigene AS geliefert. Das ist sogar **gewollt**: Juprowa-Sync soll nur Admin-initiiert sein.

**Kritisch:** Admin-Panel und AdminViews benötigen `is_staff()=true`. Wenn Admin-User andere `role`-Werte als 'admin'/'projektleiter'/'buero' haben, siehe ROLES-Enum in index.html — sollte passen.

---

## Ausführungsreihenfolge

1. **Erst B-006-Rest schließen** (4 SQL-Zeilen aus vorheriger Nachricht — DROP VIEW + ALTER TABLE RLS-Enable für users/projects/project_documents)
2. **Dann Helper-Funktionen** anlegen (4 × CREATE FUNCTION)
3. **Dann pro Tabelle** die Policy-Sets (Reihenfolge: arbeitsscheine → as_checklist/as_kommentare, dann Rest)
4. **Verifikations-Script** (Konsole als riedmann) → alle Tests grün?
5. **App-Smoke-Test** als admin: alle Listen laden weiterhin?

---

## Offene Fragen für Sebastian

- **Büro-Role** (`buero`) — darf Büro time_entries fremder Monteure sehen? PLAN: ja (is_staff=true). Bestätigen/ablehnen.
- **Projektleiter** — gleicher Scope wie Admin? PLAN: ja.
- **Urlaubsantrag ändern** nach Genehmigung — User darf NICHT mehr editieren, nur Admin. Im Plan so.
- **notifications.user_id** auf text statt uuid? Unser `user_id` speichert `u9` (public.users.id, text). Muss `current_user_pk()` helfer genau dieses Format liefern — SQL tut das.
