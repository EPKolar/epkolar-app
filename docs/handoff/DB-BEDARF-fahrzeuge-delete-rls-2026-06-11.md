# DB-BEDARF — Fahrzeug-DELETE Resurrection (RLS-Fix) · 2026-06-11

**Für Chat-Claude / Sebastian — von CC NICHT ausgeführt (DB-Write-Stopp). Sebastian klickt Run, Chat-Claude verifiziert.**

## Bug
Gelöschte Fahrzeuge tauchen nach Hard-Reset wieder auf.

## Root Cause (read-only verifiziert, Projekt jiggujpruejkaomgxarp)
Client-Gate `isVAdmin` (index.html Z.17999) erlaubt **admin OR projektleiter OR buero** zu löschen.
Server-Policy `fahrzeuge_delete` erlaubt **nur** `auth_role()='admin'`:

```
USING ((auth.role() = 'authenticated') AND (auth_role() = 'admin'))
```

→ Löscht ein projektleiter/buero-User (oder admin mit fehlendem users.auth_user_id-Link), trifft der
`DELETE /fahrzeuge?id=eq.<id>` **0 Zeilen**, PostgREST liefert aber **204 (Erfolg)** — kein Fehler.
Der Client wertet das als Erfolg, entfernt das SyncQueue-Item, retried nie → Server behält das Fahrzeug
→ App-Load nach Reset holt es wieder. **Stille Resurrection.**

SELECT/UPDATE-Policies erlauben bereits admin/projektleiter/buero — nur DELETE ist auf admin verengt
(Inkonsistenz, vermutlich versehentlich).

## Fix — DELETE- (und UPDATE-)Policy an Client-isVAdmin angleichen

Erlaubte Rollen: **admin, projektleiter, buero, lagerleitung** (= Client `isVAdmin` ab v3.9.285).
Hinweis: **Pinger Leo hat role='projektleiter'** → ist schon mit dem alten Vorschlag abgedeckt; `lagerleitung`
ist für künftige Lagerleitungs-User ergänzt (Sebastians Wunsch). Client-Gate wurde bereits erweitert (v3.9.285).

```sql
-- DELETE: war fälschlich nur admin -> Resurrection
DROP POLICY IF EXISTS fahrzeuge_delete ON public.fahrzeuge;
CREATE POLICY fahrzeuge_delete ON public.fahrzeuge
  FOR DELETE TO public
  USING (
    (auth.role() = 'authenticated')
    AND (auth_role() = ANY (ARRAY['admin','projektleiter','buero','lagerleitung']))
  );

-- UPDATE: zur Konsistenz lagerleitung mit aufnehmen (sonst editiert Lagerleitung in der UI,
-- Server blockt still = derselbe Effekt bei Fahrzeug-Edits)
DROP POLICY IF EXISTS fahrzeuge_update ON public.fahrzeuge;
CREATE POLICY fahrzeuge_update ON public.fahrzeuge
  FOR UPDATE TO public
  USING (
    (auth.role() = 'authenticated')
    AND (auth_role() = ANY (ARRAY['admin','projektleiter','buero','lagerleitung']))
  );
```

**Wichtig:** Es gibt aktuell KEINEN User mit `role='lagerleitung'` in der DB. Falls Sebastian einem User
Lagerleitung geben will → dessen `users.role` auf `'lagerleitung'` setzen (dann greifen Client-Gate + RLS).
Alternativ (granularer, größerer Umbau, NICHT in diesem Fix): per-User-Permission `fz_delete` über
`users.permissions`/`permsOverride` + RLS, die diese Permission liest — nur wenn echtes per-User-Vergeben
gewünscht ist.

## Verifikation nach Run (read-only)
```sql
select policyname, cmd, qual from pg_policies
where schemaname='public' and tablename='fahrzeuge' and cmd='DELETE';
-- Erwartung: qual enthält auth_role() = ANY (ARRAY['admin','projektleiter','buero'])
```
Danach: als projektleiter/buero ein Test-Fahrzeug löschen → Hard-Reset → bleibt weg.

## Zusatz-Hinweise
- **Falls auch der admin nicht löschen kann:** prüfen ob `users.auth_user_id` des admins gesetzt ist
  (sonst `auth_role()`→'anon'). `select id, role, auth_user_id from users where role='admin';`
- **Systemisches Risiko (VORSCHLAG, separat prüfen):** Andere Tabellen könnten dieselbe Divergenz haben
  (DELETE-Policy enger als Client-Gate) → derselbe stille Resurrection-Effekt. Audit empfohlen:
  `select tablename, cmd, qual from pg_policies where cmd='DELETE' and qual ilike '%admin%';`
- **Client-Härtung (VORSCHLAG, nicht gebaut):** `_sbDelete` könnte mit `Prefer: return=representation`
  prüfen, ob ≥1 Zeile gelöscht wurde, und 0-Zeilen-„Erfolge" sichtbar machen statt still zu schlucken —
  Trade-off: legitime Schon-gelöscht-Zeilen würden dann auch als Fehl-Sync auftauchen (app-weites
  Rauschen). Daher bewusst NICHT umgesetzt; der saubere Fix ist die RLS-Policy oben.
