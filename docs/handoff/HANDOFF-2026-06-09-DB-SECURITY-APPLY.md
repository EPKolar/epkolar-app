# HANDOFF 2026-06-09 — DB-Security Apply-Runbook (#1–#5) + jwt_exp

**Repo:** `epkolar-app` · Supabase `jiggujpruejkaomgxarp` · Frontend live **v3.9.214** (HEAD `107ca03`)
**Erstellt von:** CC (kein DB-Schreibzugriff — Plugin-MCP falsche Org). **Alle SQL = Editor-Run durch Sebastian/Chat-Claude.**

---

## 0. Was bereits LIVE ist (Frontend, gepusht)
- **v3.9.213 (`fa9d37a`)** — `API.login`: bcrypt-Fallback gegen `login_lookup.password_hash` **entfernt**. Online-Auth nur noch GoTrue. Vollprofil (`permissions`/`monteur_id`/`perms_override`/`login_count`) wird nach Login per **authentifiziertem RLS-Self-Read** (`_sbGetUsersSafe`) geladen. Offline-Login (`_OFFPW`/`offlinePwHash`) unverändert.
- **v3.9.214 (`d4f0e4b`)** — Folgefixes aus Agenten-Review: `[B020-PROF]`-Log bei leerem Self-Read · `login_count` nur mit echtem Profil hochzählen · Precedence-Fix `details`.
- Triade je Push grün (bracket-Baseline `() -1 / {} 0 / [] 0`, `node --check` 0, **726 pytest**).

> ⚠️ Das Frontend ist **vorwärts-kompatibel**: es funktioniert mit dem ALTEN `login_lookup` (liefert noch alles) UND mit dem NEUEN (8 Felder). Du kannst die Migrationen also in Ruhe und einzeln anwenden.

---

## 1. 🔴🔴 P0-GATE — VOR `fix_login_lookup` zwingend
Der Profil-Self-Read hängt zu 100 % an `users.auth_user_id`. Prüfe **read-only**:
```sql
SELECT id, username, role, auth_user_id IS NOT NULL AS linked
FROM public.users ORDER BY role;
```
**Alle 10 müssen `linked = true`.** Fehlt ein Link → nach der `login_lookup`-Migration (die `permissions`/`monteur_id`/`login_count` aus der RPC entfernt) lädt der Self-Read **0 Zeilen** → leere Berechtigungen + leere `monteurId` (still, v. a. monteur/techniker). Erst `auth_user_id` nachziehen, **dann** Migration. *(Das Frontend loggt einen leeren Read jetzt als `[B020-PROF]` in der Konsole.)*

---

## 2. Apply-Reihenfolge (empfohlen: risikoarm → risikoreich)

| Reihenfolge | Datei | Risiko | Gate |
|---|---|---|---|
| 1 | `sql/fix_activity_log_anon_insert_v3.9.213.sql` | niedrig | — (idempotent; ggf. schon via v3110 abgedeckt) |
| 2 | `sql/fix_material_catalogs_anon_v3.9.213.sql` | niedrig | Block-0-Snapshot sichten |
| 3 | `sql/fix_supplier_views_v3.9.213.sql` | mittel | Pre-Apply-Verify (a/b/c) im Header |
| 4 | `sql/fix_auth_role_v3.9.213.sql` | **hoch** (~20 Policies) | CAPTURE + 5-Rollen-Smoke |
| 5 | `sql/fix_login_lookup_v3.9.213.sql` | **hoch** (Login) | §1-Gate + CAPTURE + 10-User-Smoke |

Jede Datei: idempotent (`CREATE OR REPLACE` / `DROP … IF EXISTS`), `_ROLLBACK`-Datei daneben, `VERIFY`-Block als Kommentar. Bei jedem Bruch → Instant-ROLLBACK.

---

## 3. PFLICHT-CAPTURE vor Apply (Live-Body unbekannt → nicht raten)
Für **`fix_auth_role`** und **`fix_login_lookup`** ist der reale Funktions-Body nicht im Repo. Vor Apply ziehen und gegen die Datei diffen:
```sql
SELECT pg_get_functiondef('public.login_lookup(text)'::regprocedure);  -- WHERE-Klausel exakt übernehmen!
SELECT pg_get_functiondef('public.auth_role()'::regprocedure);          -- Rückgabetyp/Default exakt übernehmen!
-- Attribute (müssen erhalten bleiben): prosecdef=t, provolatile=s, proconfig enthält search_path=public,pg_temp
SELECT proname, prosecdef, provolatile, proconfig FROM pg_proc
WHERE proname IN ('login_lookup','auth_role')
  AND pronamespace=(SELECT oid FROM pg_namespace WHERE nspname='public');
```
- `fix_login_lookup`: die **WHERE-Klausel** (username-Match/Case/active-Filter) ist load-bearing → aus Live-Def in den `<<< CAPTURE >>>`-Block übernehmen.
- `fix_auth_role`: der **ROLLBACK** ist ohne Pre-Apply-Capture ein No-Op → vor Apply den alten Body capturen, falls echter Rückrollstand gebraucht wird.

---

## 4. Was jede Migration tut (Kurz)
- **#1 `auth_role`** → `COALESCE((SELECT role FROM public.users WHERE auth_user_id=auth.uid() LIMIT 1),'anon')`, `STABLE SECURITY DEFINER SET search_path=public,pg_temp`. Wirkt auf ~20 Policies → 5-Rollen-Smoke. *(Analog zum bereits gefixten `is_staff`/`current_user_role`.)*
- **#2 `login_lookup`** → `jsonb_build_object` mit GENAU `id, auth_user_id, username, name, email, role, active, locked`. **Kein** `password_hash`, **kein** `permissions`, **kein** `to_jsonb(u.*)`. anon-EXECUTE erhalten.
- **#3 `material_catalogs`** → `REVOKE INSERT,UPDATE,DELETE,TRUNCATE … FROM anon` + authenticated-DML-Policies. SELECT unverändert. **Frontend-Impact: keiner** (Katalog-READ + alle 5 Writes laufen authenticated; kein anon-Schreibpfad).
- **#4 `activity_log`** → `DROP POLICY activity_log_anon_insert` + authenticated-INSERT sicherstellen. Login-Audit läuft authenticated. *(Konsolidiert die bestehende `migrate_activity_log_anon_drop_v3110.sql`.)*
- **#5 `supplier_views`** → `supplier_articles_safe.ek_preis` nur sichtbar wenn `current_user_role() IN ('admin','projektleiter','buero')`, sonst `NULL` (jetzt auch **techniker maskiert**). Views bleiben **SECURITY DEFINER** (Base-RLS gäbe monteur/techniker via `security_invoker` 0 Zeilen → Material-Suche leer). `supplier_articles_public`: vom Frontend nicht genutzt → Capture+Drop-Empfehlung auskommentiert im File. **Frontend-Impact: keiner** (`ek_preis=NULL` überall toleriert: `effEk`-Guard, Fallback auf `listenpreis`, Anzeige „—").

---

## 5. jwt_exp 8h (gegen „Session läuft ständig ab")
`jwt_exp=3600` + aggressive Refresh-Rotation → Rotation-Races → Logout. Mit PAT (nicht committen):
```bash
curl -s -X GET  "https://api.supabase.com/v1/projects/jiggujpruejkaomgxarp/config/auth" \
  -H "Authorization: Bearer $PAT" | grep -o '"jwt_exp":[0-9]*'            # vorher: 3600
curl -s -X PATCH "https://api.supabase.com/v1/projects/jiggujpruejkaomgxarp/config/auth" \
  -H "Authorization: Bearer $PAT" -H "Content-Type: application/json" \
  -d '{"jwt_exp":28800}' | grep -o '"jwt_exp":[0-9]*'                     # erwartet: 28800
```
Optional gegen die „jede-Minute"-Logouts zusätzlich: `"security_refresh_token_reuse_interval":10` in denselben PATCH (oder Rotation aus). PAT danach nicht speichern/loggen.

---

## 6. Offene Felder / Annahmen (Operator prüfen)
- `material_catalogs` Block 4 nimmt globale Stammdaten an (`WITH CHECK (true)`). Falls feinere authenticated-Policies existieren (Snapshot zeigt's) → Block 4 weglassen.
- `supplier_views`: Rolle `lager` bewusst NICHT in EK-Liste (Vorgabe nur admin/PL/Büro). Falls Lager EK sehen soll → ergänzen.
- `auth_role` Rückgabetyp `text` + Default `'anon'` = Annahme → gegen Live-Signatur diffen.
