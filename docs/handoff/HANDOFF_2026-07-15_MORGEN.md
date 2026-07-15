# Handoff 15.07.2026 (früh) — Stand v3.9.702

**Arbeitsklon:** `C:\repos\epkolar-app`. srvdc02-Share ist nur Spiegel (zieht sich täglich 05:00
selbst nach), nie Push-Quelle. Session-Start: `git fetch && git reset --hard origin/main`.

**HEAD:** `41923cd` (v3.9.702). Live verifiziert (raw main + github.io-Edge auf 3.9.702).
**pytest:** 1501 grün. **Browser-Check ist Pflicht-Gate** (siehe CLAUDE.md) — heute zweimal
teuer gelernt.

---

## Was diese Session gebaut hat (v3.9.691 → 702)

### Stempeluhr-Rollout-Paket A–G (v3.9.691–696)
- **Teil A** Rollout-Härte: HID-Inter-Key-Timeout, UUID-Schatten weg, Fehlerklassifizierung, Offline
  wird gebucht statt verworfen.
- **Teil C** PZE-Ansicht „⏱ Stempelzeiten" im Büro-Portal (Fink-Vorlage): Gutschrift, roter Fehltag,
  Auto-Pause, Fehler-Queue, additive Korrektur, Excel/PDF, neutrale Projektzeit-Spalte.
- **Teil F** NFC-Chip im Mitarbeiter-Formular (Büro-Reader, Kollisionscheck, 23505-Abfang).
- **Teil G** eigene Terminal-UI + Urlaubs-/ZA-Antrag am Panel (`status='beantragt'`, 4-Schritt-Flow,
  30 s-Timeout, keine Salden am Panel).

### Terminal-User lauffähig (v3.9.695), Rollenquelle konsolidiert
Entscheid: **EINE Rollenwahrheit = `auth_role()` = `public.users.role`.** v1 der Terminal-SQL prüfte
`app_metadata` (falsch, nie gelaufen, gelöscht). `STEMPEL_TERMINAL_v2.sql` + `KIOSK_RESTRICTIVE_FIX_v1.sql`
sind die Run-Gate-Dateien.

### Zwei Beinahe-Unfälle, beide abgewendet
1. **Boot-Crash (v691–694 waren live tot):** `window._stUuid=_stUuid` ohne Deklaration → ReferenceError
   auf Top-Level. Kein Gate fand es, weil keins das Bundle *lud*. → **Browser-Check jetzt Pflicht.**
   `tests/test_window_exports_defined.py` fängt die Klasse statisch (mit Selbsttest).
2. **`guard_urlaub_edit`-Replace stillgelegt:** `security_triggers_LIVE_v3911.sql` ist eine
   **unvollständige Rekonstruktion** (Live 1746 Zeichen, Repo 953). Ein `CREATE OR REPLACE` hätte
   ~800 Zeichen Live-Logik kommentarlos gelöscht. → Regel in CLAUDE.md: nie Live-Objekt aus
   Repo-Rekonstruktion ersetzen, erst `pg_get_functiondef` ziehen.

### Bug-Hunt (v3.9.699–701) — 9 Befunde, 7 gefixt
Voller Report: `docs/BUGHUNT_2026-07-14.md`.
- **699** Befund 1 (Terminal lädt keine Belegschaftsdaten) + Befund 2 (`_stReadLog` wirft bei 403)
  + Auflage 1b (grün nur nach bestätigter Persistenz).
- **700** Befund 3 (PZE-DST: 31.03. fiel aus) + Befund 5 (Doppel-Kommen).
- **701** Befund 6 (Antrags-Scan stempelt nicht) + 8 (FinkZeit-Rahmen) + 7 (Chip-Button).
- **Bewusst offen:** Befund 4 (Teilzeit) + 9 (Nachtschicht) — Sebastian: gibt es beides nicht.

### Weiteres
- **697** FinkZeit-Differenz entschärft (neutral statt rot) — Frage 2.
- **694** Self-Service-Karte „Projektstunden" statt „Arbeitszeit" — Frage 4.
- **698** Dead-Code Batch 1 (4 Symbole).
- **gps_ingest** Quelle + 16 Tests + Traccar-Doku (`d8a1551`) — **nicht deployt**.
- **702** Flotte-Fahrtenbuch vergrößerbar (Drag-Splitter + Maximieren).

---

## SQL Run-Gate — was Sebastian ausführen muss

| Datei | Zweck | Stand |
|---|---|---|
| `STEMPEL_TERMINAL_v2.sql` **Abschn. 1–4** | RPC + Policies für die Terminal-Rolle | ⏳ **danach stempelt das Terminal** |
| `STEMPEL_TERMINAL_v2.sql` **Abschn. 5** | `guard_urlaub_edit`-Zweig | ⛔ **stillgelegt** — wartet auf v3 (echter Live-Body) |
| `KIOSK_RESTRICTIVE_FIX_v1.sql` | Kiosk-Sperren auf `is_kiosk_role()` + time_entries/forms/bautagebuch | ⏳ offen |
| `VERIFY_TRIGGER_BODIES_v2.sql` | read-only, misst alle 5 Trigger gegen die DB | ⏳ **zuerst laufen lassen** |
| `GPS_INGEST_v1.sql` | Unique-Index für `gps_ingest` | ⏳ erst mit dem Deploy |
| `MONTAGEZULAGE_v1.sql`, `FZ_TRACKER_v1.sql`, Seed | — | ✅ gelaufen |

**Terminal-User anlegen geht NUR per SQL** (die App-Benutzerverwaltung kann `stempel_terminal` nicht
vergeben — Template in v2). `auth.users` bleibt tabu für Claude Code.

---

## Offen — wartet auf Sebastian (alles gesperrt)

1. **Trigger-Kette v3:** Sebastian legt `docs/wip/trigger_bodies_LIVE_2026-07-14.csv` ab (Voll-Export
   aller 5 Bodies mit norm_md5). Daraus: 5 Einzeldateien + Hash-Selbstcheck + Diff-Erklärung je
   Trigger + `STEMPEL_TERMINAL_v3.sql` (Trigger-Abschnitt auf echtem Live-Body). Bis dahin keinerlei
   Trigger-Replace. Der Chat-Paste des Bodies ist **dreimal** an einem Content-Filter gescheitert —
   Datei-ins-Repo ist der verlässliche Weg.
2. **Punkt 2** (Anwesenheits-Basis KVZulagenReport + KVZuschlagReport auf `stempel_log`): Fragen 1+3
   noch offen, Abnahme am durchgerechneten €-Beispiel.
3. **Frage 3** (Chef-Auslastungs-Ampel): Zweck-Entscheid Anwesenheit vs. Verrechenbarkeit.
4. **`gps_ingest`-Deploy** (Traccar → `fz_positions`): eigener Go. Quelle liegt fertig im Repo.
5. **Dead-Code Phase 2** weitere Batches: nur nach Freigabe je Kandidat.

---

## Der eine Satz, der über allem steht

**`fz_positions` und `stempel_log` sind leer.** Kein Tracker bestellt, kein NFC-Chip beschafft, kein
Terminal-User angelegt. Flotte und Stempeluhr sind ausschließlich durch Tests + Browser-Interaktion
abgesichert — kein echter GPS-Punkt und kein echter Scan ist je durch die Ketten gelaufen. Der erste
Realitätstest ist der Traccar-Pilot bzw. der erste angelernte Chip.

## Dauer-Tabus
`sync_supplier` nicht deployen · Juprowa-Kern · Auth-Pfade (`auth.users`) · OFFA-Writes ·
`.github/workflows/*` · kein `.env` mit DB-Passwort · die fünf Security-Trigger nicht per
`CREATE OR REPLACE` aus Repo-Rekonstruktion.
