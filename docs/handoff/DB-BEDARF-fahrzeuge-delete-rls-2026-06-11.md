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

## Fix — DELETE-Policy an UPDATE-Policy + Client-isVAdmin angleichen

```sql
DROP POLICY IF EXISTS fahrzeuge_delete ON public.fahrzeuge;
CREATE POLICY fahrzeuge_delete ON public.fahrzeuge
  FOR DELETE TO public
  USING (
    (auth.role() = 'authenticated')
    AND (auth_role() = ANY (ARRAY['admin','projektleiter','buero']))
  );
```

(Spiegelt exakt die bestehende `fahrzeuge_update`-USING-Klausel.)

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
