# RLS / RPC / Referenz-Snapshot — 2026-07-15

**Zweck:** Soweit aus den Repo-Dateien belegbarer Stand von RLS-Policies, Guard-Triggern,
SECURITY-DEFINER-Funktionen und den vom Client referenzierten RPCs/Tabellen. Grundlage fuer
den spaeteren **0-Referenz-Abgleich** (welche DB-Objekte werden vom Code gar nicht mehr
angefasst?) und fuer das Scharfstellen von `sql/CLEANUP_2026-07.sql`.

> **Kennzeichnung durchgehend:**
> - **(Repo-Behauptung)** = aus einer Datei im Working-Tree abgeleitet, **NICHT** Live-verifiziert.
> - **(wartet auf Read #3/#4)** = muss durch `docs/db/HYGIENE_READ_QUERIES_2026-07.sql` bestaetigt werden.
>
> CC hat **keinen** Live-DB-Zugriff. Nichts in diesem Dokument ist gegen die laufende DB geprueft.

---

## 1. Kiosk-Aussperrung — der app_metadata-Fehlgriff (Kern von CLEANUP S1)

Quelle: `sql/KIOSK_RESTRICTIVE_FIX_v1.sql` (v3.9.695) **(Repo-Behauptung)**.

- Mehrere Tabellen trugen je eine **RESTRICTIVE**-Policy `*_no_lager_display`, die die Rolle
  ueber `((auth.jwt()->'app_metadata')->>'role')` prueft.
- Das ist die **falsche Rollenquelle**: der `lager_display`-User traegt seine Rolle in
  `public.users.role` (gelesen von `auth_role()`), `app_metadata` kommt in `index.html`
  **kein einziges Mal** vor. Der Claim ist an den Kiosk-Accounts nicht gesetzt → Vergleich
  gegen NULL → **die Sperre hat nie gegriffen**.
- **Kein aktives Leck** (laut Datei, verifiziert Sebastian/Chat-Claude): `fz_fahrten`,
  `fz_positions`, `geo_cache` haben als PERMISSIVE-Policy nur `is_staff()`; `lager_display`
  ist nicht staff, RLS ist Default-Deny → Kiosk kommt ohnehin nicht an die Zeilen.
- **Ersatz** (dieselbe Datei): Helper `public.is_kiosk_role()` (= `auth_role() IN
  ('lager_display','stempel_terminal')`) + RESTRICTIVE-Policies `*_no_kiosk`.

**Betroffene Tabellen laut Datei** — alte `*_no_lager_display` raus, neue `*_no_kiosk` rein:

| Tabelle        | Alt-Policy (tot)                | Ersatz (aktiv?)        |
|----------------|---------------------------------|------------------------|
| fz_fahrten     | fz_fahrten_no_lager_display     | fz_fahrten_no_kiosk    |
| fz_positions   | fz_positions_no_lager_display   | fz_positions_no_kiosk  |
| geo_cache      | geo_cache_no_lager_display      | geo_cache_no_kiosk     |
| kunden         | kunden_no_lager_display         | kunden_no_kiosk        |
| time_entries   | (neu aufgenommen)               | time_entries_no_kiosk  |
| forms          | (neu aufgenommen)               | forms_no_kiosk         |
| bautagebuch    | (neu aufgenommen)               | bautagebuch_no_kiosk   |

Status: **(wartet auf Read #3a/#3b)** — ob die `*_no_lager_display`-Policies live noch da sind
und ob die 7 `*_no_kiosk`-Policies bereits aktiv sind, entscheidet, ob CLEANUP **S1** ueberhaupt
etwas zu droppen hat. Zusatz: `sql/KUNDEN_TABLE_v3.9.586.sql` Z.37 nutzt denselben
app_metadata-Vergleich → ebenfalls als Alt-Muster im Blick behalten.

---

## 2. Guard-Trigger (Correctness-/Berechtigungs-Wall)

Quelle: `sql/security_triggers_LIVE_v3911.sql` (Rekonstruktion — **laut CLAUDE.md NICHT als
Wahrheit verwenden**) + `docs/wip/guard_*_LIVE_2026-07-14.sql` (1:1-Live-Bodies, **die einzige
Wahrheit**) + `docs/wip/trigger_bodies_LIVE_2026-07-14.csv`.

**5 Trigger / 5 Guard-Funktionen (Repo-Behauptung, Live-Bodies in docs/wip gesichert):**

| Trigger                     | Funktion                | Tabelle (laut Name)        |
|-----------------------------|-------------------------|----------------------------|
| trg_guard_kontingent        | guard_kontingent        | urlaubskontingent          |
| trg_guard_projects          | guard_projects          | projects                   |
| trg_guard_system_config     | guard_admin_only        | system_config              |
| trg_guard_urlaub_absences   | guard_urlaub_edit       | absences                   |
| trg_guard_users_privilege   | guard_users_privilege   | users                      |

**guard_urlaub_edit-Stand:** `docs/wip/guard_urlaub_edit_LIVE_2026-07-14.sql` nennt als
Normalform (prosrc, ASCII-\s kollabiert, getrimmt) **md5 `284dc6f19d45f4a8804ddb69e74e8ef6`,
1746 Zeichen**. Read #4b vergleicht den Live-Hash dagegen. **(wartet auf Read #4b)**

> Diese Funktionen/Trigger sind **NICHT** Cleanup-Kandidaten (sie sind die Sicherung selbst).
> In CLEANUP werden sie nur als „NICHT anfassen" gefuehrt.

---

## 3. Kiosk-/Terminal-RPCs (SECURITY DEFINER, harte Rollenpruefung im Body)

Quelle: `sql/KIOSK_FAHRZEUGE_v1.sql` (v3.9.708), `sql/STEMPEL_TERMINAL_v2.sql`,
`sql/KIOSK_ABS_STATUS_v1.sql` **(Repo-Behauptung)**.

- `public.is_kiosk_role()` — SECURITY DEFINER, `auth_role() IN ('lager_display','stempel_terminal')`.
  **(wartet auf Read #3c)**
- `public.kiosk_fahrzeuge()` — `RETURNS TABLE(id text, kennzeichen text, typ text, modell text,
  status text)`, SECURITY DEFINER, EXECUTE nur `authenticated`. Liefert der Wandtafel einen
  kontrollierten Lesepfad auf `fahrzeuge` OHNE tank_log/km_stand/fahrer/pickerl.
  **(wartet auf Read #3d)**
- `public.stempel_terminal_workers()` (v3.9.695) — Hausmuster fuer kiosk_fahrzeuge.

---

## 4. Vom CLIENT referenzierte RPCs (aus `index.html`, `/rpc/…`) — 0-Referenz-Basis

Jede DB-RPC, die **hier fehlt**, wird vom Client nicht (mehr) aufgerufen → Kandidat fuer den
0-Referenz-Check gegen Read #4 (pg_proc). Umgekehrt: fehlt eine hier gelistete RPC in Read #4,
ist der Client-Pfad tot/kaputt.

```
admin_create_user
admin_reset_password
juprowa_fetch_kunden
juprowa_fetch_monteure
juprowa_fetch_worksheets
juprowa_get_config
juprowa_push_worksheet
juprowa_update_passport
kiosk_fahrzeuge
kiosk_field_workers
kiosk_week_absences
kiosk_week_arbeitsscheine
login_lookup
portal_fetch
stempel_terminal_workers
```

(Extrahiert via `grep -oiE "rpc/[a-z0-9_]+" index.html`. Portal-Pfad zusaetzlich ueber
`_portalRpc` / `_portalRpcCall`-Helper → `portal_fetch`.)

---

## 5. Vom CLIENT direkt gelesene Tabellen (`_sbGet('<tabelle>')`) — 0-Referenz-Basis

Basis-Tabellen, die der Client per REST direkt liest. Zusammen mit Abschnitt 4 der Gegenstand
fuer den 0-Referenz-Abgleich: Tabellen aus Read #2, die **weder hier noch** als RPC-Quelle
auftauchen, sind Legacy-/Waisen-Kandidaten.

```
absences
arbeitsscheine
fahrzeuge
finkzeit
gefahrstoff_files
material_orders
projects
stempel_log
system_config
users
werkzeuge
workers
```

> **Nicht vollstaendig:** `_sbGet` ist nur der eine Lese-Helper. Schreibpfade (POST/PATCH auf
> `urlaubskontingent`, `weekplan_rows`, `notifications`, `tank_log` …) laufen ueber andere
> Helfer und sind hier nicht erfasst. Fuer den echten 0-Referenz-Beweis muss der jeweilige
> Tabellenname zusaetzlich als String im gesamten `index.html` gesucht werden, bevor in
> CLEANUP irgendetwas gedroppt wird.

---

## 6. Legacy-/Deprecated-Kandidaten (Repo-Wissen) — Ziel von CLEANUP S4

- **`weekplans` (Tabelle)** — **(Repo-Behauptung)** Legacy seit v500. Die App schreibt seit
  v500 in `weekplan_rows` (einzelne SQ-Items), das alte `weekplans`-Blob wird nicht mehr
  gefuellt. In `index.html` steht `weekplans` noch ~13×, aber laut Fund nur als
  Kommentar/Label (`weekplans:"Wochenplanung"`) und in `_loadWeekplansFromRows`-Helfernamen —
  **kein aktiver `_sbGet('weekplans')`-Read**. Die Datei-Kommentare selbst sagen: „Alte
  weekplans-Tabelle bleibt als … (NICHT droppen). Legacy /api/weekplans-Endpoint bleibt …".
  → DROP nur nach ausdruecklichem Sebastian-„ja" + Read-Bestaetigung, dass 0 Zeilen frisch
  geschrieben werden. **(wartet auf Read #1/#2)**
- **`urlaubskontingent.urlaub` (Spalte)** — **(Repo-Behauptung)** deprecated seit v648;
  Urlaub wird aus `absences` + `kontingent.stunden` gerechnet. → DROP COLUMN nur nach
  Sebastian-„ja" + Read #2-Zusatz (Spalte existiert noch? Non-NULL-Werte?).

---

## 7. Offene Plattform-Themen (NICHT Teil dieses Cleanups, nur Kontext)

- **Storage-Upload-Blocker (ES256-JWT):** storage-api verifiziert das asymmetrische User-JWT
  nicht → RLS=anon → Uploads 400/403. Plattform-seitig, KEINE anon-Policy anlegen. Storage
  bleibt in dieser Runde tabu (Read #6 zaehlt nur).
- **Auth ''-statt-NULL-Token:** bekanntes Muster; Read #7 zaehlt nur, Reparatur laeuft
  separat ueber `fix_*_v3.9.213`-Skripte. Auth-Schema ist tabu.
- **tank_log Base64-Reste:** Tankfoto-Migration (`migrate_tankfotos.mjs`) teils offen; Read
  #5d diagnostiziert, CLEANUP fasst es nicht an.
