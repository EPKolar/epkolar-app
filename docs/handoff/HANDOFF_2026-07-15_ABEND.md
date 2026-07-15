# Handoff 15.07.2026 (Abend) — Stand v3.9.704

**Arbeitsklon:** `C:\repos\epkolar-app`. srvdc02-Share nur Spiegel (zieht sich tägl. 05:00 selbst nach),
nie Push-Quelle. Session-Start: `git fetch && git reset --hard origin/main`.

**HEAD:** `9db4c45` (v3.9.704). Live verifiziert (raw main auf 3.9.704). **pytest 1525 grün.**

> **Pflicht-Gates vor jedem Push** (CLAUDE.md): `node_check` (0) · `_bracket_check` (`()` -1 Baseline) ·
> `_check_version` (synchron) · voller pytest · **Browser-Check** (Seite laden, 0 Console-Errors,
> `APP_VERSION` definiert, `#root` gefüllt). Der Browser-Check ist Pflicht — er hat den Boot-Crash am
> 14.07. gefangen, den kein statisches Gate sah.

---

## ✅ Diese Session gebaut & live (v3.9.691 → 704)

**Stempeluhr-Rollout A–G + Terminal (DB + Client fertig, wartet auf Hardware):** Härte, PZE-Büro-Auswertung,
NFC im Büro, Terminal-UI + Urlaubsantrag. Rollenkonsolidierung auf `auth_role()`. `TERMINAL_FINAL_v3.sql`
**gelaufen** (nach 1-Zeichen-Semikolon-Hotfix), nachgemessen: Trigger `47e14985…`/2434, 7 Kiosk-Sperren.
**Korrektur (16.07.):** `terminal_user = 0` — bewusst. Die Hardware ist erst bestellt; die Terminal-User-Anlage
erfolgt bei Inbetriebnahme. Die frühere Zeile „Terminal-User da" war falsch. Terminal-Status = **DB + Client
fertig, wartet auf Hardware.**

**Bug-Hunt (7 von 9 Befunden gefixt, v699–701):** Terminal-Datenleck, `_sbGet`-403-Swallow, PZE-DST,
Doppel-Kommen, Antrags-Scan, FinkZeit-Rahmen, Chip-Button. Zeitbomben 4 (Teilzeit) + 9 (Nachtschicht)
bewusst offen (gibt es beides nicht) — Trigger-Bedingung in `docs/BUGHUNT_2026-07-14.md`.

**Weiteres:** FinkZeit-Differenz entschärft (v697) · „Projektstunden" statt „Arbeitszeit" (v694) ·
Dead-Code Batch 1 (v698) · Flotte-Fahrtenbuch vergrößerbar, Drag-Splitter + Maximieren (v702) ·
`gps_ingest`-Quelle + 16 Tests (nicht deployt) · **Mitarbeiter-Anlage erzeugt optional Login (v703)** ·
**Spezialfahrzeuge auf der Wochenplan-Kiosk-Tafel (v704)**.

---

## ⏳ Offen — wartet auf Sebastian (alles gesperrt)

1. **Punkt 2 — Anwesenheits-Basis auf `stempel_log`** (lohnrelevant). Entschieden: KVZulagenReport
   (Taggeld) **und** KVZuschlagReport mitumstellen (Frage 1 = ja), Chef-Ampel auf `stempel_log`
   (Frage 3 = ja). **Fehlt: dein Go + Abnahme am durchgerechneten €-Beispiel.** Übergangsregel je MA+Monat
   (Stempel vorhanden → Stempel, sonst `time_entries`-Näherung, gekennzeichnet).
2. **KV-/Zulagen-Vorlage** (`docs/ZULAGEN_VORLAGE_2026-07.md`): **Z1 entschieden** → Zuschlag-Report wird
   **Gleitkonto-Report** (Stunden, ±300 h, Periode 01.07.–30.06., ZA 1:1). **1 Rückbestätigung offen:**
   So/Feiertag ausnahmslos 1:1? **Offen:** Z2 (Fr 4,5 vs „max 5h"), Z3 (Label „Entfernungszulage" +
   Stufensätze, `taggeldNacht` tot), Z4 (Pause 60 vs 30), Z6 (Metallgewerbe vs Metallnebengewerbe →
   Lohnverrechner). Nichts davon gebaut.
3. **`gps_ingest`-Deploy** (Traccar → `fz_positions`): GPS-Hardware bestellen → Traccar-Pilot → dein Go.
   Quelle + `sql/GPS_INGEST_v1.sql` liegen fertig.
4. **Dead-Code Phase 2** weitere Batches: nur nach Freigabe je Kandidat (UNSICHER-Liste `_photoSrc`,
   `asNextWeek`).
5. **Nebenbefund (nur gemeldet):** Worker-Anlage erzeugt keinen `urlaubskontingent`-Datensatz (Lazy-Default
   beim ersten Öffnen von „Urlaub", `{urlaub:25,stunden:192.5,vorjahr:0,woche:38.5}`). Lohnnah → Entscheid.
6. **Offener Feature-Punkt v703:** kein Haus-Initialpasswort im Code → Login-Passwort tippt der Admin
   (min. 4). Falls ein Muster gewünscht ist, nennen.

**Teststatus v703 Auto-Login (ehrlich, Stand 16.07.):** Username-Ableitung browser-belegt
(`Mueller` → `mueller`), Logik pytest-abgedeckt (**1525 grün**). End-to-End bewusst **NICHT** synthetisch
getestet — ein Playwright-Durchlauf würde echte `auth.users`-Zeilen gegen die Live-DB anlegen, und
Auth-Pfade sind Dauer-Tabu (auch für Tests mit Teardown, Sebastian-Entscheid 16.07.). Die Erstverwendung
erfolgt am nächsten echten Neuzugang **unter Beobachtung**; bis dahin gilt der **v558-Button** („Login
erstellen" in der Benutzerverwaltung) als erprobter Fallback.

---

## Der eine Satz, der über allem steht

**`fz_positions` ist leer** (kein Tracker bestellt). Die Flotte ist ausschließlich test-/browser-abgesichert
— kein echter GPS-Punkt lief je durch die Kette. Erster Realitätstest = Traccar-Pilot.
Die **Stempeluhr** ist DB-seitig in Betrieb, aber noch ohne angelernte Chips im Feld.

## Dauer-Tabus
`sync_supplier` nicht deployen · Juprowa-Kern · Auth-Pfade (`auth.users`) · OFFA-Writes ·
`.github/workflows/*` · kein `.env` mit DB-Passwort · die 5 Security-Trigger nie per `CREATE OR REPLACE`
aus Repo-Rekonstruktion (echte Bodies: `docs/wip/*_LIVE_2026-07-14.sql`) · kein optional chaining
(Sucrase pre-baked; Samsung-TV bei Kiosk-Screens).

## Lektionen dieser Session (Kurzindex in CLAUDE.md)
Browser-Check-Pflicht · Kommentar-braucht-Test · kein Replace aus Repo-Rekonstruktion · Mess-Query
braucht Kontrollwert (Cross-Engine `\s`) · generierte Live-Artefakte tragen Selbst-Nachweis · SQL-Pakete
parse-testen · `sql/` im Checkout ist eine Waffe · Fund außerhalb Auftrag: erst melden · DB-Body via Datei.
