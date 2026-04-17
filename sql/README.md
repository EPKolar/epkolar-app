# EPKolar RLS SQL

Security fixes for B-006 (anon-read) and B-007 (Monteur-Isolation).

## Ausführung

**Schnell (1 Paste):** `ALL_SQL_ONEPASTE.sql` im Supabase Dashboard SQL Editor paste → Run.

**Script:** `.env` mit `SUPABASE_DB_URL=postgres://...` erstellen, dann `node sql-runner.mjs`.

## Dateien

- `B006b_HEILUNGS_SQL.sql` — 20 Tabellen authenticated_read + authenticated_write (muss ZUERST laufen)
- `B007_EXECUTE.sql` — 4 Helper-Funktionen + 22 Policies auf 8 Monteur-sensible Tabellen
- `ALL_SQL_ONEPASTE.sql` — konkateniert B006b + B007 für einzelnen Paste
- `sql-runner.mjs` — Node-Runner via `pg`-Client mit Verification am Ende
- `RLS_B007_PLAN.md` — Design-Doc (Policy-Entscheidungen, Seiteneffekte)

Idempotent. Kann mehrfach ausgeführt werden.
