# EPKolar — Backlog-Abschluss 18.06.2026 (read-only verifiziert)

Aufgabe: „Alle offenen technischen Punkte (BLOCK 1–5) der Reihe nach erledigen."
Ergebnis: **BLOCK 1, 2, 3 bereits erledigt; BLOCK 5 sauber; BLOCK 4 blockiert (keine Quelle).**
Alle Befunde read-only gegen Supabase `jiggujpruejkaomgxarp` verifiziert. **Kein Code-Change nötig → keine Schein-Commits** (außer diesem Handoff).

## BLOCK 1 — gefahrstoff_files → privater Bucket ✅ BEREITS ERLEDIGT (v3.9.403)
- Spalte `storage_path` existiert; **59/59 Zeilen befüllt** (alle migriert).
- Bucket `epkolar-gefahrstoff` = **privat** (`public=false`).
- **0** Zeilen mit Legacy-`file_url` → kein öffentlicher Rest-Leak.
- RLS: `SELECT = authenticated`, `ALL (Write) = is_staff()`.
- Code: `SB_GEF_BUCKET="epkolar-gefahrstoff"`, `_sbUploadGef` (→ storage_path), Anzeige `_sbSignedGefUrl` (signiert), `delFile` löscht DB + Storage-Objekt.
- **→ Privacy-Ziel voll erreicht.** Die in der Aufgabe genannte „Migration nach epkolar-docs" ist nicht nötig — gefahrstoff hat einen eigenen, dedizierten privaten Bucket (sauberer als Sammel-Bucket). Keine SQL/Code-Änderung.

## BLOCK 2 — Zombie-Absences ✅ NICHTS ZU TUN
- `SELECT count(*) FROM absences WHERE worker_id IS NULL OR worker_id NOT IN (SELECT id FROM workers)` → **0**.
- Keine verwaisten Einträge. DELETE würde 0 Zeilen treffen. Nicht ausgeführt.

## BLOCK 3 — tickets.page ✅ BEREITS VORHANDEN
- Spalte `tickets.page` **existiert** bereits (information_schema verifiziert). Kein ALTER nötig.

## BLOCK 5 — RLS-Backlog „~15 Tabellen ALL(true)" ✅ LÄNGST GETIGHTENED
- `SELECT … FROM pg_policies WHERE qual='true'` → nur **EINE** Policy:
  `system_config.system_config_select` (SELECT, roles=`{authenticated}`, qual=`true`).
- `system_config` zusätzlich: `system_config_admin_write` (ALL, `current_user_role()='admin'`).
- **Bewertung:** Kein Sicherheitsloch — Lesen nur für **authentifizierte** Nutzer (nicht anon), Schreiben nur admin; system_config enthält App-Konfiguration (nicht-sensibel) und wird von vielen Views gelesen. **Bewusst so gelassen** (deckt sich mit Stand 15.06.: „system_config/juprowa/notif-insert bewusst offen"). Empfehlung: belassen. Falls dennoch gewünscht, einzeiliger Tighten auf eine konkrete Rolle möglich — aber funktional riskant (App liest Config früh).
- Die übrigen ~14 vermuteten ALL(true)-Tabellen (werkzeuge/fahrzeuge/projects/workers/…) sind bereits rollen-/staff-gegated (frühere Härtungswellen).

## BLOCK 4 — Edge Function `sync_supplier` v3 ⛔ BLOCKIERT (keine Quelle)
- `C:\temp\epkfn\supabase\functions` enthält: **`supplier-sync`** + `admin-create-user` — **kein `sync_supplier`**.
- Repo `supabase/functions`: `admin-create-user`, `ocr_tankbeleg`, **`supplier-sync`** — ebenfalls kein `sync_supplier`.
- Die **Live**-Funktion heißt `sync_supplier` (deployed, `verify_jwt=false`), aber **ihr v3-Quellcode liegt nirgends vor** (weder Repo noch C:\temp). → Deploy einer „v3" ist ohne Quelle nicht möglich.
- Zusätzlich: Supabase-CLI ist nicht eingeloggt (`LegacyPlatformAuthRequiredError`, kein `SUPABASE_ACCESS_TOKEN`) → CLI-Deploy generell blockiert; Alternative wäre `deploy_edge_function` via Plugin.
- **Offene Entscheidung für Sebastian:**
  1. Wo liegt der `sync_supplier`-v3-Quellcode? (dann nach `C:\temp\epkfn` legen + deployen — via Plugin, da CLI uneingeloggt)
  2. ODER: meinst du die Repo-Funktion **`supplier-sync`** (gehärteter JWT-Wrapper, Stub-Sync)? Die ist eine andere Funktion.
  3. ODER: die aktuelle Live-`sync_supplier` (funktioniert, anon-aufrufbar) bleibt — kein Deploy nötig?
  Hinweis: Frontend ruft **keine** der beiden auf (DATANORM-Import ist clientseitig `_parseDatanormFiles`).

## Fazit
Stand HEAD `35b2da5` (v3.9.460) bleibt unverändert — alle technischen Backlog-Punkte sind entweder bereits umgesetzt (1/2/3), bewusst belassen (5) oder mangels Quelle blockiert (4). Es wurden keine überflüssigen Migrationen/Commits erzeugt.
