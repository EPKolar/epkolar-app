# Setup Stempeluhr

Inbetriebnahme-Doku für das Kiosk-Terminal `?screen=stempel`. Teil D des
Stempeluhr-Rollout-Pakets (Teil A Robustheit, Teil B Terminal-Rolle, Teil C
Büro-Auswertung, Teil D = dieses Dokument). Referenz-Stand: `index.html`
Sentinel `//@STEMPEL-HELPERS-START` (ab Z. 2037), `StempelTafel` (ab Z. 5718),
`StempelPauseConfig` (ab Z. 7814), SQL `sql/STEMPEL_v1.sql`.

---

## 1 · Was die Stempeluhr ist

Eine Kiosk-Tafel — Vollbild, kein Login-Formular im Alltagsbetrieb, aufgerufen
über `?screen=stempel`. Ein HID-Barcode-/NFC-Wedge (Tastatur-Emulation) liest
die Chip-UID des Mitarbeiters, die App gleicht sie gegen `workers.nfc_uid` ab
und schreibt einen **append-only**-Eintrag nach `stempel_log`
(kein Update, kein Delete im Normalbetrieb).

Die Richtung (Kommen/Gehen) wird **automatisch** bestimmt — der Mitarbeiter
wählt sie nicht selbst:

- Gibt es heute schon einen Eintrag, kippt die Richtung einfach (`_stNextDir`:
  kommen → gehen → kommen → …).
- Gibt es heute noch keinen Eintrag, prüft die App den **letzten Eintrag
  überhaupt**: liegt ein offenes „kommen" weniger als 18 Stunden zurück, ist
  die nächste Buchung „gehen" (Übernacht-/Bereitschaftsschicht). Sonst ist es
  ein frischer Start („kommen").

`stempel_log.ts` speichert **immer** den rohen, ungerundeten Zeitpunkt — dazu
mehr in Abschnitt 3.

Zugriff aktuell: **admin-only** (`curUser.role==='admin'`, Z. 7395). Eine
eigene Terminal-Rolle (`stempel_terminal`) ist Teil B des Rollout-Pakets.
`sql/STEMPEL_TERMINAL_v1.sql` liegt bereit (Human-Run-Gate, additiv, noch
**nicht** ausgeführt) — sie legt nur das DB-Fundament, der App-seitige
Anschluss ist ein eigener, noch offener Schritt. Details in Abschnitt 4,
Schritt 4.

---

## 2 · Hardware-Setup

- **HID-Wedge-Scanner** (Barcode oder NFC), der sich dem Betriebssystem als
  Tastatur meldet. **Muss die UID mit einem Enter/Return abschließen** — der
  Key-Listener in `StempelTafel` sammelt Zeichen bis `Enter` und wertet dann
  erst aus (`_buf`, Z. ~5777).
- Der Wedge muss die UID als **Burst** senden (deutlich unter 30 ms zwischen
  den Zeichen). Grund: ein Inter-Key-Timeout von `STEMPEL_HID_GAP_MS=200`
  verwirft den bisherigen Puffer, wenn eine Taste über 200 ms später kommt
  als die vorherige — das schützt vor liegengebliebenen Einzeltasten
  (Putzkraft über die Tastatur, Katze auf dem Keyboard), die sich sonst nach
  Stunden mit dem nächsten echten Scan zu Datenmüll verschmelzen würden.
  Ein langsamer/tröpfelnder Wedge würde sich damit selbst zerhacken — vor dem
  Rollout einmal mit `?screen=stempel` gegentesten.
- **Tablet oder Mini-PC im Kiosk-Modus** (Vollbild-Browser, keine Adressleiste,
  kein Weg zurück zur normalen App) — analog zu den bestehenden Kiosk-Screens
  `?screen=planung` / `?screen=monteure`.
- **WakeLock** hält den Bildschirm an (`navigator.wakeLock`, Screen-Wake-Lock-
  API), Reacquire bei jedem `visibilitychange` auf `visible`. Die Screen-Wake-
  Lock-API verlangt wie `crypto.randomUUID()` einen **Secure Context**
  (HTTPS oder `localhost`) — ein Kiosk auf reinem `http://192.168.x.x` im LAN
  bekommt keinen WakeLock und degradiert beim ID-Fallback (siehe Abschnitt 5).
  Für den Dauerbetrieb daher wenn möglich HTTPS am Terminal.

---

## 3 · Rundungs- und Pausenregeln — sauber abgrenzen

**Wichtig, wird häufig verwechselt** — zwei unterschiedliche Verträge im selben Repo:

| | Stempeluhr | Manuelle Zeiterfassung (v3.9.688) |
|---|---|---|
| Wann gerundet wird | **Bei der Auswertung**, nicht beim Speichern | **Bei der Eingabe**, sichtbar |
| Was gespeichert wird | `stempel_log.ts` roh/ungerundet | Bereits gerundeter `HH:MM`-String |
| Regel | Kommen **AUF**, Gehen **AB**, 5-Min-Raster | Kommen **AUF**, Gehen **AB**, 5-Min-Raster (dieselbe Betriebsregel) |
| Implementierung | `_stRoundKommen`/`_stRoundGehen` (ms-basiert, `//@STEMPEL-HELPERS`) | eigene String-Variante (`//@ZEIT-RUNDUNG-START`, `_zeitParse` + Raster) |

Beide Komponenten runden nach derselben Betriebsregel (zulasten der
Monteure — Kommen aufrunden, Gehen abrunden), aber an **unterschiedlichen
Stellen im Datenfluss**. Die Stempeluhr ist damit auditierbar: der Rohwert
bleibt in der DB erhalten, die Rundung ist reproduzierbar aus dem Rohwert
ableitbar. Die manuelle Erfassung hat diesen Rohwert nicht — dort ist die
Rundung Teil der Eingabe. Das ist **kein Bug**, sondern zwei bewusst getrennte
Verträge — nicht angleichen, ohne beide Seiten explizit zu prüfen.

### Pausenabzug

Einmal pro Tag, aus `system_config.stempel_pause_rules` (JSON, Key =
Rolle → Minuten, plus `default`). In-Memory-Fallback im Client, falls der Key
fehlt: `{"Backoffice":0,"default":60}`.

> **Stolperfalle (v3.9.652-Lektion):** Der Rollen-Schlüssel ist die
> **Anzeige-Rolle aus `workers.role`**, also z. B. `"Backoffice"` —
> **NICHT** `"buero"`. `workers.role` führt die Anzeige-Rollen, nicht die
> internen Kürzel. Im auskommentierten Seed-Block in `sql/STEMPEL_v1.sql`
> (Z. 56–58) steht noch der **falsche** Key `"buero"` — dieser Block ist
> absichtlich auskommentiert und darf **nicht** unverändert einkommentiert
> werden. Wer die Pausenregeln setzt, entweder den JSON-Key auf `Backoffice`
> korrigieren oder — besser — die UI benutzen (siehe unten).

Der Abzug greift **einmal pro Tag, nie negativ** (`_stTagNetto`: Brutto minus
Pausenabzug, gekappt bei 0). Sichtbare Konfig-UI: `StempelPauseConfig`
(Mitarbeiter-Verwaltung, admin-only, „⏱ Stempel-Pausenregeln"). Sie liest die
tatsächlich in `workers.role` vorkommenden Rollen selbst aus und bietet pro
Rolle ein Minuten-Feld — **das ist der sichere Weg**, weil dabei kein
Rollen-Key von Hand getippt werden muss.

---

## 4 · Inbetriebnahme-Checkliste

In dieser Reihenfolge:

1. **SQL laufen lassen:** `sql/STEMPEL_v1.sql` im Supabase SQL-Editor
   (Projekt `jiggujpruejkaomgxarp`). Legt `workers.nfc_uid` (+ Unique-Index),
   die Tabelle `stempel_log` und die RLS-Policies an (`is_staff()`-Gate für
   SELECT/INSERT/UPDATE/DELETE). Idempotent, beliebig oft ausführbar.
2. **`system_config`-Seed setzen:** `stempel_pause_rules` =
   `{"Backoffice":0,"default":60}`. Empfohlen über die App-UI
   (`StempelPauseConfig`, admin-only) — dort ist der Rollen-Key automatisch
   korrekt. Alternativ direkt per SQL, dann **nicht** den auskommentierten
   Block aus `sql/STEMPEL_v1.sql` unverändert übernehmen (falscher Key
   `"buero"`, siehe Abschnitt 3).
3. **`nfc_uid` je Mitarbeiter pflegen:** zwei gleichwertige Wege — direkt in
   `workers` per SQL/Admin-UI ist weiterhin möglich, komfortabler sind die
   beiden folgenden:

   > **⚠️ Welche Chips? Nur die NEU beschafften NFC-Chips (13,56 MHz) aus der
   > Einkaufsliste.** Die **bestehenden FinkZeit-Ausweise werden NICHT
   > wiederverwendet** — sie werden am neuen Reader nicht gelesen. Wer es
   > trotzdem versucht, sucht den Fehler an der falschen Stelle.
   > Solange FinkZeit parallel läuft, tragen die Mitarbeiter übergangsweise
   > **beide Medien**: den Fink-Ausweis für Fink, den neuen NFC-Chip für die
   > Stempeluhr.

   - **Am Panel selbst**, über den **Anlern-Modus** in `StempelTafel`
     (Button „＋ Chip anlernen"): Mitarbeiter aus der Liste wählen, Chip an
     den Reader halten — die UID wird zugewiesen. Ein Kollisions-Check
     verhindert, dass eine UID doppelt vergeben wird.
   - **Ab sofort auch vorab im Büro**, über einen Reader am Büro-PC:
     Sektion „📡 NFC-Chip" im Mitarbeiter-Formular (Mitarbeiter-Verwaltung).
     Chip an den Büro-Reader halten, die UID wird direkt am
     Mitarbeiter-Datensatz gespeichert — der Mitarbeiter muss dafür nicht
     extra ans Panel.

   > **⚠️ WICHTIG, bevor überhaupt ein Chip zugeordnet wird:** Beide Reader
   > (Büro **und** Panel) vorher fest auf **10-stellig dezimal** einstellen.
   > Liefert ein Reader die UID in einem anderen Modus (z. B. hexadezimal
   > oder mit abweichender Stellenzahl), erzeugt **derselbe physische Chip
   > zwei unterschiedliche UID-Strings** — die Büro-Zuordnung passt dann
   > nicht zur Panel-Lesung, und der Mitarbeiter wird beim Scannen am
   > Terminal **nicht erkannt** (kein Fehlerdialog, der auf die Ursache
   > hinweist — der Chip „funktioniert einfach nicht"). Beide Reader müssen
   > exakt denselben UID-Modus liefern, bevor die erste Zuordnung passiert.
4. **Terminal-User anlegen:** `sql/STEMPEL_TERMINAL_v1.sql` legt das
   DB-Fundament für eine eigene Rolle `stempel_terminal` (analog
   `lager_display`): eine RPC `stempel_terminal_workers()` mit minimalen
   Feldern (`id,name,role,nfc_uid` — kein Telefon/Adresse/Lohn), SELECT+INSERT
   (bewusst **kein** UPDATE/DELETE, RLS-Default-Deny reicht) auf `stempel_log`,
   und SELECT auf `system_config` nur für den Key `stempel_pause_rules`.
   Human-Run-Gate, additiv — der bestehende Admin-Betrieb bleibt beim
   Ausführen unangetastet. Drei Teilschritte, in dieser Reihenfolge:
   1. SQL-Datei ausführen (Fundament steht).
   2. **Sebastian legt den Auth-User an** (Supabase Dashboard → Authentication
      → Users, analog zum bestehenden `lager_display`-User) und setzt
      `raw_app_meta_data` auf `{"role":"stempel_terminal"}`. Auth ist für
      Claude Code tabu — dieser Schritt ist nicht automatisierbar.
   3. **App-Code-Änderung (separater Schritt, nicht Teil der SQL-Datei):** das
      Gate `?screen=stempel` (aktuell `curUser.role==='admin'`, Z. ~7395) muss
      um `stempel_terminal` erweitert werden, und `StempelTafel` muss von
      `_sbGet('workers',...)` auf `stempel_terminal_workers()` umgestellt
      werden — sonst läuft der Terminal-User in eine fehlende `workers`-Policy.
   Bis Schritt 3 umgesetzt ist, läuft das Terminal **interimsmäßig weiter mit
   einem eingeloggten Admin-Account** (aktuelles Gate bleibt bis dahin
   unverändert; `lager_display` hat ohnehin **keinen** Zugriff auf den
   Stempel-Screen und fällt auf den Standard-Kiosk zurück).
5. **Kiosk starten:** Tablet/Mini-PC im Kiosk-Browser auf
   `<app-url>?screen=stempel` öffnen, mit dem Terminal-User (bzw. interimsmäßig
   Admin) einloggen, Vollbild. WakeLock greift automatisch beim Laden.
6. **Testscan:** einen bereits angelernten Chip scannen → Vollbild-Feedback
   „✓ KOMMEN" mit Uhrzeit sollte erscheinen. Zweiten Scan (andere UID oder
   nach Ablauf der 12-Sekunden-Sperre) prüfen → „✓ GEHEN" mit Netto-Zeit.
   In `stempel_log` sollte pro Testscan eine neue Zeile mit `device:'kiosk'`
   auftauchen.

---

## 5 · Troubleshooting

**„stempel_log fehlt" / „stempel_log / nfc_uid fehlt — sql/STEMPEL_v1.sql
ausführen"**
SQL aus Schritt 1 wurde nicht (oder nicht vollständig) ausgeführt. Die App
erkennt das selbst (`_stErrKind` klassifiziert die Fehlerantwort: `42P01`/
„does not exist"/„schema cache" → `'missing'`) und zeigt den Hinweis statt
zu crashen. Fix: `sql/STEMPEL_v1.sql` laufen lassen, danach ohne App-Update
sofort funktionsfähig.

**Scanner tippt ins Eingabefeld statt zu scannen**
Der Key-Listener hat einen Fokus-Guard: liegt der Fokus auf einem
`INPUT`/`TEXTAREA`/`SELECT` (z. B. im Anlern-Modus-Formular oder im
Test-Eingabefeld „UID (Test ohne Reader)"), wertet der Wedge-Handler
**nicht** aus — die Zeichen landen stattdessen als Text im fokussierten Feld.
Fix: vor dem Scannen irgendwo außerhalb eines Eingabefelds klicken (oder den
Anlern-Modus verlassen), dann greift der globale Key-Listener wieder.

**Doppelscan**
12-Sekunden-Sperre je Mitarbeiter (`_lastScan`-Ref, seit v3.9.662). Ein
HID-Wedge feuert `Enter` gelegentlich doppelt, oder der Mitarbeiter hält den
Chip zweimal hin — ohne Sperre würde der zweite Scan die Tagesparität kippen
(kommen→gehen in derselben Minute → Schicht zählt 0). Innerhalb von 12 s
zeigt die Tafel „⏱ Bereits erfasst" statt einen zweiten Eintrag zu schreiben.
Echte Kommen/Gehen-Scans liegen im Betrieb Stunden auseinander, die Sperre
stört den Normalbetrieb nicht.

**Schicht über Mitternacht**
Ein 18-Stunden-Fenster bestimmt die Richtung, wenn heute noch kein Eintrag
existiert: liegt der letzte Eintrag überhaupt „kommen" und ist er jünger als
18 Stunden, ist die nächste Buchung „gehen" (Übernachtschicht — Netto wird
im Büro nachgezogen, die Tafel zeigt dafür „Übernacht-Schicht — Netto im
Büro" statt einer irreführenden 0h-Anzeige). Ist das letzte „kommen" älter
als 18 Stunden, gilt es als vergessener Gehen-Stempel und eskaliert **nicht**
über Tage — die nächste Buchung ist ein frischer Start („kommen").

**ID-Fehler / Stempel verschwinden lautlos**
Nur relevant, wenn das Terminal über reines HTTP (kein Secure Context)
läuft: `crypto.randomUUID()` gibt es nur unter HTTPS/`localhost`. Ohne
Secure Context greift ein RFC4122-v4-Fallback (`_stUuid`) — wichtig, weil
`stempel_log.id` als `uuid` typisiert ist und ein Nicht-UUID-Fallback von
Postgres mit `22P02` abgelehnt würde (Stempel würde als dauerhaft
fehlgeschlagen in der Sync-Queue landen, ohne dass am Terminal etwas
auffällt). Symptom, falls doch einmal auftritt: Mitarbeiter stempelt
scheinbar normal, aber die Schicht taucht nie in der Auswertung auf — dann
`window.SQ.count()` bzw. die Sync-Queue am Terminal prüfen.

---

## 6 · Urlaubs-/ZA-Antrag am Terminal

Ergänzung zum reinen Kommen/Gehen-Stempeln: Mitarbeiter sollen am Wandpanel
künftig auch einen Urlaubs- oder Zeitausgleichs-Antrag stellen können, ohne
dafür einen eigenen Software-Login zu brauchen.

**Architektur-Klarstellung (Sebastian-Entscheid, verbindlich):** Es gibt
**genau EINEN** Terminal-Login (`stempel_terminal`, siehe Abschnitt 4,
Schritt 4) für das gesamte Panel. Mitarbeiter haben **keine eigenen User** —
sie identifizieren sich ausschließlich über ihren NFC-Chip
(`workers.nfc_uid`), exakt wie beim Kommen/Gehen-Stempeln. Das Terminal
schreibt den Antrag mit dem einen gemeinsamen Terminal-Login **für den
gescannten Mitarbeiter** (dessen `worker_id`), nicht für sich selbst.

**Ablauf (4 Schritte):**

1. **Identifikation per Chip:** Mitarbeiter hält seinen Chip an den Reader —
   dieselbe Erkennung wie beim Kommen/Gehen-Stempeln. Kein Passwort, keine
   PIN, kein eigener Login.
2. **Aktion wählen:** neben der automatischen Kommen/Gehen-Buchung bietet
   das Panel die Option „Urlaub/Zeitausgleich beantragen".
3. **Zeitraum wählen:** Mitarbeiter gibt Von-/Bis-Datum an.
4. **Bestätigen:** das Terminal legt **pro Werktag** eine eigene Zeile in
   `absences` an, mit `status='beantragt'` — **Samstag, Sonntag und
   Feiertage werden dabei übersprungen**, dafür entstehen keine Zeilen. Die
   DB-seitige Grundlage dafür (RLS-Policy + Trigger-Anpassung) liegt in
   `sql/STEMPEL_TERMINAL_v1.sql`, Abschnitte 4+5.

Die **Genehmigung läuft unverändert im Büro** (normale Urlaubsverwaltung,
admin bzw. `perms_override.urlaub_edit`) — das Terminal kann Anträge nur
**einreichen**, nie selbst genehmigen, ändern oder löschen: es gibt bewusst
keine UPDATE-/DELETE-Policy für `stempel_terminal` auf `absences`, und der
Trigger `guard_urlaub_edit()` lässt für diese Rolle ausschließlich INSERT
mit `status='beantragt'` durch.

**Datenschutz am Panel:** Es werden ausschließlich Vor- und Nachname
angezeigt — **keine Salden**. Resturlaub/Kontingent (`urlaubskontingent`)
ist am Wandpanel bewusst **nicht** sichtbar, weil es dort keine
`stempel_terminal`-Policy gibt (RLS = Default-Deny). Die Eingabemaske hat
einen **30-Sekunden-Timeout** und fällt danach automatisch auf die
Stempel-Ansicht zurück — Schutz gegen fremde Augen an einem öffentlich
zugänglichen Gerät.

> **Stand:** DB-Fundament (RLS-Policy + Trigger-Fix) liegt bereit in
> `sql/STEMPEL_TERMINAL_v1.sql`, Human-Run-Gate, noch nicht ausgeführt. Die
> Client-UI (Aktion „Urlaub/Zeitausgleich beantragen" in `StempelTafel`,
> POST auf `absences`) ist ein separater, noch offener App-Code-Schritt —
> analog zum bereits offenen Anschluss aus Abschnitt 4, Schritt 4.

---

## Referenzen

- `sql/STEMPEL_v1.sql` — Tabelle, RLS, `nfc_uid`-Spalte (Human-Run-Gate).
- `sql/STEMPEL_TERMINAL_v1.sql` — Terminal-Rolle `stempel_terminal`
  (Teil B des Rollout-Pakets). **Liegt bereit, Human-Run-Gate, noch nicht
  ausgeführt** — plus offener App-Code-Schritt danach (siehe Abschnitt 4).
  Enthält seit 2026-07-14 zusätzlich die INSERT-Policy auf `absences` und
  den Trigger-Fix `guard_urlaub_edit()` für den Urlaubs-/ZA-Antrag am
  Terminal (Abschnitt 6 in diesem Dokument).
- `sql/security_triggers_LIVE_v3911.sql` — Live-Dokumentation der 5
  Security-Trigger, u. a. `guard_urlaub_edit()` (Vorzustand vor dem
  Terminal-Fix).
- `index.html` Sentinel `//@STEMPEL-HELPERS-START` … `-END` (ab Z. 2037) —
  Rundung, Pausenabzug, Richtungslogik, Fehlerklassifizierung.
- `index.html` `function StempelTafel(props)` (ab Z. 5718) — Kiosk-UI.
- `index.html` `function StempelPauseConfig(props)` (ab Z. 7814) —
  Pausenregeln-UI in der Mitarbeiter-Verwaltung.
- `docs/handoff/HANDOFF_2026-07-14_ABEND.md` — Stand des Gesamt-Rollout-Pakets.
