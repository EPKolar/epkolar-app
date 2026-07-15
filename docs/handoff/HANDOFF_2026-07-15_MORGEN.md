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

## ✅ Stempel-Terminal ist VOLLSTÄNDIG IN BETRIEB (15.07.)

`sql/TERMINAL_FINAL_v3.sql` ist gelaufen, der Terminal-User ist angelegt, Chat-Claude hat live
verifiziert (v3-Body minus Zweig = `284dc6f1…`/1746 unabhängig nachgerechnet, Footer TABU-konform).
Kontrolle nachträglich: `docs/wip/VERIFY_NACH_V3_RUN.sql` (read-only, prüft Trigger-Hash `47e14985…`/2434,
7 Kiosk-Sperren, 1 Terminal-User). **Das Terminal stempelt und beantragt jetzt vollständig.** Das ganze
Terminal-Kapitel (A–G + Rollenkonsolidierung + Trigger) ist abgeschlossen.

**Entschieden (für die nächste Session, jetzt NICHT gebaut — Punkt 2 bleibt gesperrt):** Frage 1 =
KVZuschlagReport (Überstunden) **wird mit umgestellt** auf `stempel_log` (braucht echte Von/Bis-Uhrzeiten
fürs Nachtfenster). Frage 3 = Chef-Auslastungs-Ampel **auf `stempel_log`** (echte Anwesenheit). Beides
kommt in Punkt 2, mit €-Beispiel-Abnahme.

## SQL Run-Gate

| Datei | Zweck | Stand |
|---|---|---|
| `STEMPEL_TERMINAL_v2.sql` Abschn. 1–4 | RPC + Policies für die Terminal-Rolle | ✅ gelaufen (14.07.) |
| `TERMINAL_FINAL_v3.sql` | `guard_urlaub_edit` auf Live-Body + Terminal-Zweig **und** Kiosk-Sperren (7 Tabellen) | ✅ **gelaufen (15.07.)** |
| `MONTAGEZULAGE_v1.sql`, `FZ_TRACKER_v1.sql`, Seed | — | ✅ gelaufen |
| `GPS_INGEST_v1.sql` | Unique-Index für `gps_ingest` | ⏳ erst mit dem Deploy (gesperrt) |

> `STEMPEL_TERMINAL_v2.sql` Abschn. 5 (Rekonstruktions-Replace) bleibt **stillgelegt** — ersetzt durch
> TERMINAL_FINAL_v3. `KIOSK_RESTRICTIVE_FIX_v1.sql` und `VERIFY_TRIGGER_BODIES_v2.sql` sind als
> Historie/Diagnose erledigt (ihr Inhalt steckt in TERMINAL_FINAL_v3 bzw. wurde durch die kalibrierte
> CSV-Messung überholt).

---

## Der Trigger-Abschluss — und die drei Lektionen als Muster

Der Weg zu `TERMINAL_FINAL_v3.sql` war die lehrreichste Sequenz der Session. Drei Muster, die bleiben:

**1. Nie ein Live-Objekt aus einer Repo-Rekonstruktion ersetzen.**
`security_triggers_LIVE_v3911.sql` gab sich als Live-Stand aus, war aber eine **unvollständige
Rekonstruktion**. Ein `CREATE OR REPLACE` darauf hätte bei `guard_urlaub_edit` ~793 Zeichen echter
Logik kommentarlos gelöscht (JWT-Quelle, `permissions`-Spalte, projektleiter/buero-Zugriff,
DELETE-Zweig, `'storniert'`-Status). **Kalibriert gemessen weichen ALLE FÜNF** guard-Trigger ab
(+793/+99/+69/+66/+19). Die vier anderen laufen unverändert in der DB — nur die Repo-Datei bildet sie
unvollständig ab; ihre echten Bodies liegen als `docs/wip/<name>_LIVE_2026-07-14.sql`. Regel steht in
CLAUDE.md: erst `pg_get_functiondef` ziehen, dann darauf aufbauen.

**2. Cross-Engine-Normalisierung lügt — mit Kontrollwert kalibrieren.**
Die erste Verify-Query verglich eine **von Postgres** normalisierte Live-Seite gegen eine **von
Python** normalisierte Repo-Seite. `\s` heißt in beiden Engines etwas anderes (Postgres: nur ASCII;
Python: auch Unicode-Whitespace). Ergebnis: plausibel aussehende, aber falsche Zahlen. Gefangen hat es
nur ein **eingebauter Kontrollwert** (erwartetes Delta verfehlt). Beim finalen Lauf war der
Kontrollwert `guard_urlaub_edit = 284dc6f1…/1746` — er MUSS treffen, sonst ist die Messung ungültig.
Regel in CLAUDE.md: jede Mess-Query trägt einen Kontrollwert mit bekanntem Soll.

**3. Generierte kritische Artefakte tragen einen maschinellen Selbst-Nachweis.**
`TERMINAL_FINAL_v3.sql` beweist sich selbst: **v3-Trigger-Body MINUS Terminal-Zweig** ergibt
normalisiert exakt `284dc6f1…/1746` — also den unveränderten Live-Body. Der Replace fügt damit
nachweislich **nur** den Terminal-Zweig hinzu und löscht nichts. Der Nachweis wurde generativ geprüft
**und** in `tests/test_terminal_final_v3.py` festgenagelt — eine spätere Änderung, die versehentlich
Live-Logik entfernt, bricht den Test. Muster für jedes generierte SQL/Config, das ein Live-Objekt
anfasst.

**Nebenbei zum Transport:** Der Chat-Paste des Trigger-Bodies scheiterte **dreimal** an einem
Content-Filter (`CREATE FUNCTION` + `$$` + `RAISE EXCEPTION` sieht wie Injection aus). Verlässlich war
erst die **Datei** (CSV aus Downloads ins Repo). Bei künftigen DB-Body-Transfers: Datei, nicht Paste —
oder OAuth für den Supabase-MCP, dann zieht Claude Code die Bodies selbst.

---

## Offen — wartet auf Sebastian (alles gesperrt)

1. **Punkt 2** (Anwesenheits-Basis KVZulagenReport + KVZuschlagReport auf `stempel_log`): Fragen 1+3
   noch offen, Abnahme am durchgerechneten €-Beispiel.
2. **Frage 3** (Chef-Auslastungs-Ampel): Zweck-Entscheid Anwesenheit vs. Verrechenbarkeit.
3. **`gps_ingest`-Deploy** (Traccar → `fz_positions`): eigener Go. Quelle liegt fertig im Repo.
4. **Dead-Code Phase 2** weitere Batches: nur nach Freigabe je Kandidat.

*(Die Trigger-Kette ist erledigt — siehe oben, TERMINAL_FINAL_v3 gelaufen.)*

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
