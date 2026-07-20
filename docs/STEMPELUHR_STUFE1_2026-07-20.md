# Stempeluhr Stufe 1 — Ist-Stand + Bauplan (20.07.2026)

**Ziel:** Ein Chip-Scan landet real in `stempel_log`, und der `//@PZE`-Rechenkern (v3.9.692) zeigt
Soll/Ist im Büro — **testbar, ohne dass Lohn davon abhängt** (niemand stempelt echt, bis Sebastian freigibt).
Fernziel: FinkZeit ablösen (eigene PZE-Monatsübersicht).

**Read-only geprüft** gegen die Live-DB (`pg_proc`, `pg_policies`, `pg_class`, `pg_trigger`,
`information_schema`) und gegen `index.html` @ **v3.9.768**. **Nichts gebaut, keine SQL ausgeführt, kein
Auth-Eingriff.** Bauplan (Teil B) ist ein Vorschlag und wartet auf Sebastians Go.

---

# TEIL A — Ist-Stand (Fakten)

## A1) RPCs — `stempel_terminal_workers` fehlt (Vorbefund verifiziert, nicht geglaubt)

`pg_proc`-Suche über `%stempel%`/`%kiosk%`/`%pze%`/`is_kiosk_role`:

| RPC | Args | Security | für die Stempeluhr |
|---|---|---|---|
| `is_kiosk_role()` | — | DEFINER | Baustein — **da** |
| `kiosk_fahrzeuge()` | — | DEFINER | Flotte-Kiosk |
| `kiosk_field_workers()` | — | DEFINER | Monteur-Tafel |
| `kiosk_week_absences(text,text)` | | DEFINER | Dispo-Kiosk |
| `kiosk_week_arbeitsscheine(text,text)` | | DEFINER | Dispo-Kiosk |
| **`stempel_terminal_workers()`** | — | — | **FEHLT** |

→ **Bestätigt: kein `stempel*`-RPC in der DB.** Die App ruft ihn aber schon auf (`index.html:6677`,
`StempelTafel`, v3.9.695) und zeigt bei Fehlen „RPC stempel_terminal_workers() fehlt — sql/
STEMPEL_TERMINAL_v2.sql ausführen" (`index.html:6684`).

## A2) `stempel_log` — Tabelle da, RLS sperrt genau die Terminal-Rolle aus

| Prüfung | Ergebnis |
|---|---|
| Tabelle `public.stempel_log` | ✅ existiert |
| RLS aktiv | ✅ `true` |
| Zeilen **gesamt** | **0** — komplett leer, es wurde noch nie gestempelt (nicht nur Juni/Riedmann) |
| Schema | `id uuid NN` · `worker_id text NN` · `ts timestamptz NN` · `direction text NN` · `device text` · `created_at timestamptz` |

**Policies — alle vier `is_staff()`:**

| Policy | cmd | USING / WITH CHECK |
|---|---|---|
| `stempel_log_select_staff` | SELECT | `is_staff()` |
| `stempel_log_insert_staff` | INSERT | WITH CHECK `is_staff()` |
| `stempel_log_update_staff` | UPDATE | `is_staff()` |
| `stempel_log_delete_staff` | DELETE | `is_staff()` |

**⚠️ Kern-Blocker.** `is_staff()` = `role IN ('admin','buero','projektleiter')`. Ein `stempel_terminal`-User
ist kein Staff → die INSERT-Policy lässt ihn **nicht** in `stempel_log` schreiben. Genau die Rolle, für die
das Terminal gedacht ist, ist ausgesperrt.

## A3) `guard_urlaub_edit`-Trigger — blockt den Stempel-INSERT NICHT (Vorbefund überholt)

Der frühere Verdacht („guard lehnt jeden Terminal-Antrag ab") ist so **nicht mehr richtig**:

- **Der Trigger liegt nur auf `absences`** (`trg_guard_urlaub_absences`, enabled), **nicht auf `stempel_log`**.
  `stempel_log` hat gar keinen `guard_urlaub`-Trigger. → Für den **Stempel-INSERT ist er irrelevant.**
- Selbst auf `absences` **erlaubt** er der Terminal-Rolle seit v3.9.703 einen INSERT:
  ```
  IF c_role = 'stempel_terminal' THEN
    IF TG_OP='INSERT' AND COALESCE(NEW.status,'beantragt')='beantragt' THEN RETURN NEW; END IF;
    RAISE EXCEPTION 'stempel_terminal darf nur INSERT mit status=beantragt';
  END IF;
  ```
  Also: Terminal darf per NFC einen Urlaubs-Antrag `status=beantragt` anlegen, aber nicht genehmigen/ändern.
  service_role wird per `c_sub IS NULL`-Bypass durchgelassen.

**Wichtig:** Der Trigger-Kommentar spricht von einer `public.users`-Zeile `role='stempel_terminal'` als
existierend — **die gibt es aber nicht** (siehe A4). Der Trigger ist auf die Rolle vorbereitet, die Rolle
selbst ist nie angelegt worden.

## A4) Rolle `stempel_terminal` existiert in der DB nicht

- `auth.users` mit Stempel-Bezug = **0**
- `public.users WHERE role='stempel_terminal'` = **0**

Die Rolle lebt bisher nur als **String im App-Code** und im Trigger-Zweig — es gibt keinen realen User.

## A5) App-Code — fast vollständig, eine klar benennbare Lücke

**Live im Code (v3.9.768):**
- **Kiosk `?screen=stempel`** — `_isKioskPath` (`index.html:7421`), rendert nur `StempelTafel`
  (`index.html:6590`); für `stempel_terminal` lädt der Bootstrap bewusst NICHTS (`index.html:7607`, sonst
  403-Sturm über die Portal-Fetches).
- **Toggle:** Scan → `nfc_uid`-Lookup → letzter heutiger `stempel_log`-Eintrag → Richtung → INSERT
  `POST /stempel_log` (`index.html:6811`), echte uuid als id.
- **PZE-Rechenkern** `//@PZE-START..@PZE-END` (`index.html:4517–4605`): `_pzeDayKey` (lokaler Tag, DST-sicher),
  `_pzeUngerade`, `_pzeAutoPause`, `_pzeTagRow`, `_stTagNetto`/`_stPauseAbzug`.
- **Büro-Auswertung `PZEView`** (`index.html:10944`): `stempel_log`=Anwesenheit, `time_entries`=Info-Spalte
  „Projektzeit"; Korrektur rein additiv (`device='korrektur:<user>'`); Excel- + PDF-Export.

**Lücke „Code da" → „Scan landet in `stempel_log`":**

| Ebene | Status |
|---|---|
| App-UI (Kiosk, Tafel, Toggle) | ✅ fertig |
| PZE-Rechenkern + Büro-Auswertung | ✅ fertig |
| RPC `stempel_terminal_workers()` | ❌ fehlt → Tafel lädt keine Worker |
| DB-Rolle `stempel_terminal` (auth + users) | ❌ nicht angelegt |
| `stempel_log`-INSERT für Terminal-Rolle | ❌ nur `is_staff()` → Rolle ausgesperrt |
| `nfc_uid` an Workern gepflegt | ⚠️ offen (Tafel matcht darüber) |
| Hardware (Gerät + NFC-Leser) | ⚠️ außerhalb Software |

**Fazit A:** Es fehlt **keine nennenswerte Software**, sondern **RPC + Rolle + eine RLS-INSERT-Regel**.

---

# TEIL B — Stufe-1-Bauplan (Vorschlag, wartet auf Freigabe)

**Testbarkeit ohne Lohn-Risiko:** `stempel_log` ist heute leer und wird von keiner Lohnrechnung gelesen
(die Zulagen-Reports lesen `time_entries`, nicht `stempel_log`). Testdaten in `stempel_log` haben also
**null Lohn-Wirkung** — Stufe 1 ist gefahrlos testbar, solange die echten Monteure noch nicht stempeln.

### B1 — SQL-Run (Human-Gate über Chat-Claude, KEINE Auto-Ausführung, Auth-nah)
1. **`sql/TERMINAL_FINAL_v3.sql` gegen die Live-DB gegenprüfen**, dann den **fehlenden Teil** ausführen:
   RPC `stempel_terminal_workers()` (SECURITY DEFINER, durchlässig für `auth_role()='stempel_terminal'`
   ODER `is_staff()`, liefert nur id/name/role/nfc_uid) **+** einen **`stempel_log`-INSERT-Zweig, der
   `stempel_terminal` durchlässt** (analog `lager_display`; SELECT/UPDATE/DELETE bleiben `is_staff()`).
   ⚠️ **Der Datei-Kopf ist nachweislich veraltet** (behauptet „am 14.07. gelaufen" — die DB widerlegt das).
   **Vor dem Run** Zeile für Zeile verifizieren, dass genau das angelegt wird und nichts Bestehendes ersetzt.
2. Idempotenz sicherstellen (`CREATE OR REPLACE` / `IF NOT EXISTS`) — der Run soll wiederholbar sein.

### B2 — Auth/Rolle (Dashboard, KEIN App-Auth-Write — TABU)
3. **Auth-User `stempel_terminal` im Supabase-Dashboard anlegen** (Sebastian, wie bei `lager_display`).
4. **`public.users`-Zeile** mit `role='stempel_terminal'`, **ohne `monteur_id`** (der guard-Trigger und
   der Bootstrap-Sonderpfad hängen genau daran).

### B3 — App-Code
5. **Voraussichtlich NICHTS.** Kiosk, Tafel, Toggle, RPC-Aufruf und PZE sind vorhanden. Erst nach dem
   Live-Smoke entscheiden, ob eine Kleinigkeit klemmt (z.B. Fehlertext, Fokus, Scanner-Feldbindung). Kein
   Code auf Verdacht.
6. **`nfc_uid` an mind. 1 Test-Worker pflegen** — sonst matcht die Tafel keinen Scan. (Daten-Handgriff,
   kein Code.)

### B4 — Testen (ohne echte Mitarbeiter)
7. **Simulierter Scan:** die Tafel liest den `nfc_uid` als Tastatur-/Text-Eingabe (HID-Wedge-Muster). Ein
   **Test-Chip** oder die manuelle Eingabe der Test-`nfc_uid` löst denselben Pfad aus — kein echter Leser nötig.
8. **Headless-Mount** von `StempelTafel` (wie bei DispoPanel/KVZulagenReport): mit gemocktem RPC-Ergebnis
   Kommen→Gehen togglen, prüfen dass der INSERT-Payload `{worker_id, ts, direction}` korrekt ist (0 Console-
   Errors, kein Throw). **Beweist die App-Seite ohne DB.**
9. **Ende-zu-Ende (nach B1/B2):** als `stempel_terminal` einloggen, Test-`nfc_uid` scannen → `stempel_log`
   füllt (read-only-Gegencheck: `count(*)` steigt von 0) → `PZEView` (Büro) zeigt die Zeile mit Soll/Ist.
10. Danach die Testzeilen wieder entfernen (Staff-DELETE-Policy existiert) — sauberer Nullstand vor echtem Start.

### B5 — BEWUSST NICHT in Stufe 1
- **Gleitzeit-/Sollzeit-Pool** (kumulatives ±-Konto) — spätere Stufe.
- **PZE-PDF/Excel als offizielle Monatsurkunde** (FinkZeit-Ablösung) — Export existiert, aber die
  Abnahme als lohnrelevantes Dokument ist eine eigene Stufe.
- **Pausenregeln je Rolle** final bestätigen (`system_config.stempel_pause_rules`) — für Stufe 1 reicht
  der Default.
- **Hardware-Rollout** (Gerät am Werkstor, physischer NFC-Leser).

### B6 — Risiken / Auth-Fallen (explizit)
- **TABU Auth:** `auth.users` wird **nur** im Dashboard angelegt (Sebastian), nie aus der App/MCP.
- **RLS-INSERT-Formulierung:** der neue Zweig muss `stempel_terminal` erlauben, ohne `is_staff()`
  aufzuweichen — sonst könnte ein Terminal plötzlich lesen/löschen. Eng auf INSERT begrenzen.
- **`stempel_log` ist die lohnrelevante Urkunde:** additiver Korrektur-Pfad (v692) beibehalten, nie
  UPDATE/DELETE des Roh-Logs im Normalbetrieb. Testzeilen sind die einzige erlaubte Ausnahme (vor Go-Live).
- **`c_sub IS NULL`-Bypass** im guard-Trigger = service_role. Der Terminal-User ist **kein** service_role —
  er läuft über den `stempel_terminal`-Zweig. Beim SQL-Run darauf achten, dass der Bypass nicht versehentlich
  breiter wird.
- **Veralteter Datei-Kopf** von `STEMPEL_TERMINAL_v2.sql`/`TERMINAL_FINAL_v3.sql`: nicht dem Kommentar
  vertrauen, nur der DB. Vor jedem Run erneut `pg_proc`/`pg_policies` gegenprüfen.
- **`nfc_uid`-Kollision/Leere:** ohne gepflegte `nfc_uid` matcht kein Scan; doppelte `nfc_uid` würde den
  falschen Worker treffen — vor Go-Live auf Eindeutigkeit prüfen.

---

**Nächster Schritt:** Sebastian gibt B1/B2 frei (oder Teile davon), dann führt Chat-Claude die SQL im
Human-Gate aus und legt den Auth-User an. Erst danach App-Live-Smoke. Kein index.html-Commit nötig, bis
der Live-Smoke eine konkrete Lücke zeigt.
