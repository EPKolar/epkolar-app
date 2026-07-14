# Setup Traccar / GPS-Flotte

Inbetriebnahme-Doku für die GPS-Kette (Tracker → Traccar → App). Referenz-Stand:
`sql/GPS_v1.sql` (`fz_positions`), `sql/GPS_LATEST_v1.sql` (View `fz_latest`),
`sql/FZ_TRACKER_v1.sql` (Geräte-Stammdaten am Fahrzeug),
`docs/handoff/FLOTTE_F1_2026-07-13.md`, `docs/handoff/HANDOFF_2026-07-14_ABEND.md`.

---

## 1 · Ausgangszustand (ehrlich)

**`fz_positions` ist leer. Die Tracker sind nicht bestellt.**

Die gesamte Flotte-Kette — Segmentierung (`_fzSegmente`), Fahrtenbuch,
Reverse-Geocoding (Nominatim), Auswertung, das Fink-Layout der Karte — ist zum
Stand dieses Dokuments **ausschließlich durch Tests abgesichert**. Kein
einziger echter GPS-Punkt und kein einziger echter Nominatim-Lookup ist je
durch diese Kette gelaufen. Was im Browser zu sehen ist, ist durchgängig der
Leer-Zustand (Leer-Banner, `wartet`-Status, keine Crashes — das ist geprüft
und funktioniert).

**Der erste Realitätstest ist der Traccar-Pilot.** Bis dahin ist jede Aussage
über „funktioniert mit echten Daten" eine Vermutung, keine Beobachtung.

Hardware-Bestand (Einkaufsliste, Stand 03.07.2026): **12× Teltonika FMC003**
(OBD-gebunden) + **1× Teltonika FMC130** (festverdrahtet, für den LKW Scania
TU-83JM — pflicht, nicht optional, da nicht auf einen OBD-Port angewiesen),
jeweils mit **1NCE-SIM**. Traccar-Server ist für **srvdc02** vorgesehen.
Vor dem Rollout offen: Teltonika-Kompatibilität je Fahrzeug-Baujahr
(OBD-Protokoll/PIDs), Portfreigabe + DynDNS für Traccar auf srvdc02, sowie die
**§96-Zustimmungen** (Kontrollmaßnahme — Betriebsvereinbarung/Zustimmung nötig,
bevor getrackt wird). Monteure sehen den Flotte-Tab ohnehin nicht (Gate
`isStaff`).

---

## 2 · Tracker-Konfiguration (Teltonika, On-Moving-Profil)

Vorgabe von Sebastian, 14.07.2026:

| Parameter | Wert |
|---|---|
| Min Period | **10 s** |
| Min Distance | **100 m** |
| Min Angle | **10°** |
| On Stop → Heartbeat | **300 s** |

**Begründung, damit die Werte bei einer Neukonfiguration nicht „optimiert"
werden, ohne den Grund zu kennen:**

- **Min Angle 10°** ist der Wert, der den Trail in der Kurve auf der Straße
  hält. Ohne ihn sendet der Tracker nur bei Zeit-/Distanz-Trigger und die
  Polyline schneidet Kurven ab — auf der Karte fährt das Fahrzeug dann
  sichtbar querfeldein, obwohl es der Straße gefolgt ist.
- **Min Period 10 s + Min Distance 100 m** sind der Kompromiss zwischen
  Kurventreue (mehr Punkte = genauerer Trail) und SIM-Datenvolumen/
  Geräte-Lebensdauer (jeder Punkt kostet Funk und Batterie/Bordnetz-Last).
  Kleinere Werte würden den Trail glätten, aber das Datenvolumen bei 13
  Fahrzeugen im Dauerbetrieb spürbar erhöhen.
- **On-Stop-Heartbeat 300 s** verhindert, dass ein **stehendes** Fahrzeug die
  SIM leerfunkt — ohne einen reduzierten Sende-Takt im Stand würde der
  Tracker weiter im Bewegungs-Takt senden, obwohl sich nichts ändert.

Diese vier Werte sind eine Einheit — wer einen davon ändert, sollte die
anderen drei mitdenken (z. B. reduziert ein größerer Min-Angle-Wert die
Kurventreue, kann aber mit kleinerem Min-Period kompensiert werden).

---

## 3 · App-Seite

Die Fahrzeug-Marker/Fleet-Liste laufen über die View **`fz_latest`**
(`sql/GPS_LATEST_v1.sql`, `security_invoker=true`, `DISTINCT ON (fahrzeug_id)`
— genau eine, die neueste Zeile je Fahrzeug, indexiert). Das ersetzt den
früheren globalen `fz_positions?order=ts.desc&limit=200`, bei dem der Marker
eines länger stillstehenden Fahrzeugs aus den Top-200 herausfallen konnte,
sobald mehrere Tracker gleichzeitig pingen.

**Ziel-Takt laut Sebastian-Vorgabe (14.07.2026): 5–10 s Aktualisierung, 1
Request pro 10 s über `fz_latest`, ausschließlich bei gemountetem
Flotte-Tab.** Fahrtenbuch- und Analyse-Fetches laufen bewusst **nicht** in
diesem Takt (die Fahrtenbuch-Historie wird nur on-demand pro ausgewähltem
Fahrzeug geladen, nicht im Poll-Intervall).

**Erledigt seit v3.9.691:** Der Poll läuft auf `FLOTTE_POLL_MS = 10 * TIME_SECOND`
(vorher 60 s). Der Fetch ist gegen Overlap abgesichert (`_polling`-Ref — bei
10-s-Takt und langsamem Netz ist dieser Guard nicht mehr Kosmetik, sondern
tragend: sonst überholt eine ältere Antwort eine neuere und die Karte springt
zurück) und bricht bei fehlender View/Tabelle sauber auf den Leer-Zustand herunter
(404/`42P01` → `missing`-Flag statt Crash).

> **Nicht mitbeschleunigt — und das mit Absicht:** Der 60-Sekunden-Poll in
> `WochenplanTafel` (Lager-Kiosk, `kiosk_week_absences`-RPC) bleibt bei 60 s. Er
> hat mit der Flotte nichts zu tun. Ein Test hält das fest, damit ihn niemand
> „mit aufräumt".

---

## 4 · `gps_ingest` — die Brücke (gebaut, NICHT deployt)

Quelle: `supabase/functions/gps_ingest/index.ts`. SQL-Fundament:
`sql/GPS_INGEST_v1.sql`. **Beides liegt fertig im Repo und wartet auf Sebastians
Go.** Claude Code deployt nichts.

### Inbetriebnahme

1. **Secret setzen** (langes Zufallstoken, z. B. `openssl rand -hex 32`):
   `supabase secrets set GPS_INGEST_TOKEN=<token>`
2. **SQL laufen lassen:** `sql/GPS_INGEST_v1.sql` (Unique-Index auf
   `(fahrzeug_id, ts)` + Index auf `fahrzeuge.tracker_imei`).
3. **Deployen — ohne JWT-Pflicht**, denn Traccar hat kein Supabase-JWT und wird
   nie eines haben:
   ```
   cd C:\temp\epkfn
   supabase functions deploy gps_ingest --no-verify-jwt
   ```
   (Die Supabase-CLI verträgt weder UNC-Pfade noch Netzlaufwerke — daher
   `C:\temp\epkfn`, siehe CLAUDE.md.)
4. **Traccar-Forward** (`conf/traccar.xml`):
   ```xml
   <entry key='forward.enable'>true</entry>
   <entry key='forward.type'>json</entry>
   <entry key='forward.url'>https://jiggujpruejkaomgxarp.functions.supabase.co/gps_ingest?token=&lt;token&gt;</entry>
   ```
   Kann die Traccar-Version Custom-Header, ist `x-gps-token: <token>` der
   sauberere Weg — dann steht das Token nicht im Log.
5. **IMEI am Fahrzeug eintragen** (Fahrzeug-Formular, seit v3.9.689).

### Die vier Fallstricke, die die Function bewusst behandelt

| Fallstrick | Warum er wehtut |
|---|---|
| **`speed` kommt in KNOTEN** | Ungerechnet gespeichert fährt die Flotte dauerhaft **46 % zu langsam** (1 kn = 1,852 km/h) — und es fällt niemandem auf, weil 50 statt 93 km/h plausibel aussieht. Die Function rechnet um. |
| **`device.uniqueId` = IMEI** | Der einzige Schlüssel zum Fahrzeug. Fehlt sie am Fahrzeug, antwortet die Function mit **200** und `unmapped:[…]` — **nicht** mit 500. Bei ≠ 2xx wiederholt Traccar endlos einen Zustand, den nur das Büro auflösen kann (IMEI nachtragen). Ein DB-Ausfall gibt dagegen sehr wohl 500, denn **der** Retry ist richtig. |
| **`fixTime` ≠ `serverTime`** | `fixTime` ist der Zeitpunkt der Ortung, `serverTime` nur der des Empfangs. Nimmt man serverTime, verschiebt eine Funkloch-Nachlieferung die halbe Fahrt. |
| **Traccar wiederholt Forwards** | Ohne Eindeutigkeit legt jede Wiederholung denselben Punkt nochmal an und verfälscht Tageskilometer und Ø-Geschwindigkeit still. Darum der Unique-Index `(fahrzeug_id, ts)` + `ON CONFLICT DO NOTHING`. |

Zusätzlich verworfen werden: Punkte mit `valid:false`, Koordinaten außerhalb des
Wertebereichs und die **Nullinsel** (0/0) — ein Tracker ohne Fix meldet die gern,
und ein einziger solcher Punkt zieht die Karte nach Afrika und macht jede
Distanzrechnung der Fahrt kaputt.

Abgesichert durch `tests/test_gps_ingest.py` (16 Tests). **Aber:** kein einziger
echter GPS-Punkt ist je durch diese Kette gelaufen. Der erste Tracker ist der
Realitätstest, nicht die Testsuite.

Ebenfalls offen, aber nachgelagert: `sql/FZ_TRACKER_v1.sql`
(`tracker_typ`/`tracker_sim`/`tracker_eingebaut`) ist noch nicht ausgeführt —
bis dahin sind diese drei Felder im Fahrzeug-Formular gesperrt (die App
erkennt die fehlenden Spalten selbst per Sniff), die IMEI-Zuordnung
(`tracker_imei`, aus `sql/GPS_v1.sql`) funktioniert bereits unabhängig davon.

---

## 5 · Retention

Rohpunkte in `fz_positions` sollen **nicht unbegrenzt** wachsen. Regelung:
**`sql/GPS_RETENTION_v1.sql`** — 12 Monate Aufbewahrung für Rohpunkte, danach
Löschung; **`fz_fahrten`** (die segmentierten, persistierten Fahrten inkl.
Kundenzuordnung) bleibt davon **unberührt**, weil Fahrtenbuch/Auswertung
ausschließlich aus `fz_fahrten` lesen, nie direkt aus `fz_positions` — die
Retention setzt nur an der Rohpunkt-Tabelle an.

Die Datei ist reine **Vorsorge und aktuell komplett inert**: kein einziges
ausführendes Statement ist scharf geschaltet. Sie enthält nur
auskommentiert (a) einen einzeiligen `DELETE … WHERE ts < now() - interval
'12 months'` und (b) einen `pg_cron`-Vorschlag (monatlich, 1. des Monats
03:00 Server-Zeit — `pg_cron` muss vorher als Extension im Dashboard
aktiviert werden). Human-Run-Gate wie üblich: kein automatischer Lauf.
Aktivierung (manueller Lösch-Lauf oder Cron-Job) ist eine bewusste,
separate Sebastian-Entscheidung, **sobald `fz_positions` tatsächlich Daten
trägt und die ersten Punkte 12 Monate zurückliegen** — vorher gibt es
nichts zu löschen.

---

## Referenzen

- `sql/GPS_v1.sql` — Tabelle `fz_positions` (Rohpunkte).
- `sql/GPS_LATEST_v1.sql` — View `fz_latest` (neueste Position je Fahrzeug).
- `sql/FZ_TRACKER_v1.sql` — Geräte-Stammdaten am Fahrzeug (`tracker_typ`/
  `tracker_sim`/`tracker_eingebaut`), **Run-Gate offen**.
- `sql/GPS_RETENTION_v1.sql` — 12-Monats-Retention für `fz_positions`.
  **Liegt bereit, komplett inert (nur auskommentierte Statements), nicht
  aktiviert.**
- `docs/handoff/FLOTTE_F1_2026-07-13.md` — Hardware-Kontext, Architektur-
  Entscheide (Geocoding, Segmentierung), F1–F4-Stand.
- `docs/handoff/HANDOFF_2026-07-14_ABEND.md` — Gesamt-Reihenfolge (DB-Lücken
  → Stempeluhr-Paket → `gps_ingest`).
