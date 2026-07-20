# SQL-Status — verifiziert am 20.07.2026 (read-only gegen die Live-DB)

Für Chat-Claude: **alle SQL-Dateien liegen bereits in git** unter `sql/` (131 Dateien).
Direktzugriff über Raw-URL:

```
https://raw.githubusercontent.com/EPKolar/epkolar-app/main/sql/<DATEINAME>
```

Diese Liste ist **nicht** aus der Doku abgeschrieben, sondern gegen die Datenbank geprüft
(`to_regclass`, `pg_proc`, `pg_policies`, `pg_indexes`, `information_schema.columns`).
Die alte Liste in `sql/README.md` (Stand 14.07.) ist an mehreren Stellen **überholt** — siehe unten.

---

## 🔴 OFFEN — muss noch laufen (Human-Run-Gate, Supabase SQL-Editor, Projekt `jiggujpruejkaomgxarp`)

### 1. `sql/TERMINAL_FINAL_v3.sql` — **teilweise offen**
Raw: https://raw.githubusercontent.com/EPKolar/epkolar-app/main/sql/TERMINAL_FINAL_v3.sql

| Prüfobjekt | in DB | Bedeutung |
|---|---|---|
| `is_kiosk_role()` | ✅ vorhanden | Abschnitt B **ist gelaufen** |
| Policy `fz_positions_no_kiosk` | ✅ vorhanden | Abschnitt B **ist gelaufen** |
| RPC `stempel_terminal_workers()` | ❌ **fehlt** | Kern der Terminal-Rolle **fehlt** |

**⚠️ WIDERSPRUCH ZUR DOKU:** Der Kopf von `sql/STEMPEL_TERMINAL_v2.sql` behauptet, die
Abschnitte 1–4 (inkl. RPC `stempel_terminal_workers`) seien **am 14.07. gelaufen**. In der DB
existiert aber **kein einziger** `stempel*`-RPC — geprüft über `pg_proc` mit
`ILIKE '%stempel%' OR '%terminal%' OR '%kiosk%'`, gefunden wurden nur:
`is_kiosk_role`, `kiosk_fahrzeuge`, `kiosk_field_workers`, `kiosk_week_absences`,
`kiosk_week_arbeitsscheine`.
→ Entweder wurde der RPC-Teil nie ausgeführt, oder er wurde nachträglich entfernt.
**Vor dem Stempeluhr-Rollout klären** — die Terminal-Rolle kann ohne diesen RPC nicht funktionieren.

### 2. `sql/GPS_INGEST_v1.sql` — **offen**
Raw: https://raw.githubusercontent.com/EPKolar/epkolar-app/main/sql/GPS_INGEST_v1.sql

| Prüfobjekt | in DB |
|---|---|
| Spalte `fahrzeuge.tracker_imei` | ✅ vorhanden (aus `GPS_v1.sql`) |
| Index `fahrzeuge_tracker_imei_idx` | ❌ **fehlt** → Datei ist noch nicht gelaufen |

Fundament für die Edge-Function `gps_ingest`. Kein akuter Druck: die Tracker sind laut
Handoff nicht bestellt, `fz_positions` ist leer.

### 3. `sql/GPS_RETENTION_v1.sql` — **bewusst nicht scharf**
Raw: https://raw.githubusercontent.com/EPKolar/epkolar-app/main/sql/GPS_RETENTION_v1.sql

Enthält nur auskommentierten DELETE + pg_cron-Vorschlag. Reine Vorsorge, `fz_positions` ist leer.
**Nicht ausführen**, solange keine GPS-Daten fließen.

---

## ✅ BEREITS GELAUFEN — README/Memory waren hier veraltet

| Datei | Prüfobjekt in DB | Status |
|---|---|---|
| `MONTAGEZULAGE_v1.sql` | Tabelle `montagezulage_tage` | ✅ existiert — **entgegen** „nur gestaged, Human-Run-Gate" im alten Stand |
| `AS_FZ_BEDARF_v1.sql` | Spalte `arbeitsscheine.fz_bedarf` (jsonb) | ✅ existiert — **entgegen** „offener Sebastian-Gate" im Memory |
| `DISPO_BLOCKS_v1.sql` | Tabelle `dispo_blocks` | ✅ existiert |
| `PLZ_GEO_v1.sql` | Tabelle `plz_geo` | ✅ existiert (20 Zeilen, Stand 20.07.) |
| `PLZ_DISTANZ_v1.sql` | Tabelle `plz_distanz` | ✅ existiert (171 Zeilen, Stand 20.07.) |
| `GPS_v1.sql` | Tabelle `fz_positions`, Spalte `tracker_imei` | ✅ existiert |
| `GPS_LATEST_v1.sql` | View `fz_latest` | ✅ existiert |
| `TERMINAL_FINAL_v3.sql` **Abschnitt B** | `is_kiosk_role()` + `*_no_kiosk`-Policies | ✅ gelaufen (Abschnitt A/RPC siehe oben) |

**Kein SQL nötig für #19b:** `plz_geo`/`plz_distanz` haben bereits je eine SELECT-Policy für
`authenticated` und eine `*_write_staff`-Policy (cmd `ALL`, `USING`+`WITH CHECK` = `is_staff()`,
also admin|buero|projektleiter). Ein `B_19b_geo_rls.sql` wurde deshalb **bewusst nicht angelegt**.

---

## Hinweis zur Pflege
`sql/README.md` Abschnitt „Human-Run-Gate — offen/manuell (14.07.2026)" ist überholt
(nennt `STEMPEL_TERMINAL_v1.sql`, das durch `TERMINAL_FINAL_v3.sql` ersetzt wurde, und
führt gelaufene Dateien als offen). Diese Datei hier ist der geprüfte Stand vom 20.07.2026.
