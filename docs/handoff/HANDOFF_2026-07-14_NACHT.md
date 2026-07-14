# Handoff 14.07.2026 (Nacht) — Stempeluhr-Rollout-Paket A–G

**Arbeitsklon:** `C:\repos\epkolar-app`. srvdc02-Share ist **nur Spiegel** (zieht sich täglich 05:00
selbst nach), **nie** Push-Quelle. Session-Start: `git fetch && git reset --hard origin/main`.

**Stand:** v3.9.691 → v3.9.693. Ausgangspunkt war v3.9.690 (`3fb2145`).

---

## Was gebaut wurde

### v3.9.691 — Stempeluhr Teil A (Rollout-Härte) + zwei Beifänge

Drei Fehler, die jeder für sich im Feld **still Schichten gefressen** hätte:

| # | Fehler | Warum er tödlich war |
|---|---|---|
| 1 | **HID-Puffer lebte ewig** | Eine vergessene Taste auf der Kiosk-Tastatur blieb im Scan-Puffer stehen und verschmolz Stunden später mit der nächsten echten UID zu Müll → „Chip nicht zugeordnet" trotz gültigem Chip. Jetzt: Inter-Key-Timeout `STEMPEL_HID_GAP_MS=200`. Reset **nur auf Zeichentasten, nicht auf Enter** — manche Wedges hängen den Terminator träge an, und ein verworfener *echter* Scan wäre schlimmer als ein ignorierter Müll-Scan. |
| 2 | **UUID-Schatten** | `StempelTafel` hatte ein **lokales** `_uuid`, das das korrekte globale (Z. 4111) überschattete. Sein Fallback `'st_'+Date.now()+…` ist **keine uuid**. `stempel_log.id` ist `uuid` → Postgres lehnt mit **22P02** ab → `doSync` wertet das als *permanent* → nach 5 Versuchen landet der Stempel in `syncQueueFailed`. Der Kiosk quittiert grün, die Schicht ist weg. **Der Fallback greift auf jedem Kiosk ohne Secure Context** (`http://192.168.x.x` im LAN) — denn `crypto.randomUUID` gibt es nur unter https/localhost. Das ist exakt der Betriebsfall des Wandpanels. Fix: Schatten gelöscht, globales `_uuid` benutzt (echtes v4, vom Selbsttest TC-U gedeckt). |
| 3 | **Jeder Lesefehler = „Tabelle fehlt"** | Ein simpler Netzaussetzer führte zu „stempel_log fehlt" **und zum Verwerfen des Scans** — obwohl die SyncQueue genau für diesen Fall existiert. Der Monteur sah einen Fehler, ging arbeiten, die Schicht fehlte. Jetzt `_stErrKind`: `missing` (42P01/HTTP404) ≠ `net` ≠ `other`. |

**Offline-Verhalten (Vorgabe Sebastian: „wenn offline, dann synch später"):** Der Stempel wird
**immer** gebucht, nie verworfen. Die Richtung kommt aus `_evCache` (gespeist aus jedem
erfolgreichen Read **und** jedem eigenen Schreibvorgang). Fehlt der Cache (Kiosk während der
Störung neu gestartet), wird `kommen` angenommen — aber **nie still**: die Zeile bekommt
`device='kiosk:offline?'` und landet damit in der Büro-Korrektur-Queue (Teil C). Geraten wird
also, aber sichtbar.

**Beifang:** `MonteurTafel` `autoRot` default **AN** (die Tafel hängt unbedient an der Wand —
ein Default-AUS hieß: sie rotiert nie). Flotte-Live-Poll **60 s → 10 s** (`FLOTTE_POLL_MS`),
nur die Karte, nur bei gemountetem Tab. Der 60-s-Poll in `WochenplanTafel` (Lager-Kiosk,
`kiosk_week_absences`) ist **bewusst unangetastet** — ein Test hält das fest.

### v3.9.692 — Teil C: PZE-Ansicht „⏱ Stempelzeiten" (Fink-Vorlage)

Neuer Sentinel `//@PZE` (reiner Rechenkern) + `PZEView` im Büro-Portal.

- Tagestabelle: Stempel-Paare **roh sichtbar, gerundet im Tooltip**; Fehlgrund-Badge; Gesamt /
  Soll / Pause / **+/-**; Wochen-Teilsummen + Monatssumme; Sa/So/Feiertag abgesetzt.
- **Gutschrift:** genehmigte Abwesenheit → Gesamt = Soll, Saldo 0 (wie Fink den Krank-Tag
  gutschreibt). Nur *beantragt* → blasser Badge, **keine** Gutschrift. **Stempel schlägt
  Gutschrift** — wer trotz Urlaub stempelt, war da.
- **Fehltag:** Werktag ohne Stempel und ohne Gutschrift → Datum rot, Saldo −Tagesnorm.
  Markierung, **kein Alarm**.
- **Auto-Pause** grau+kursiv im `11:30|12:30`-Stil, nominal in die Tagesmitte gelegt. Sie ist
  eine **Regel, keine gemessene Zeit** — darum optisch klar abgesetzt.
- Tab **„Fehlerhafte Buchungen"** über alle MA: ungerade Stempelzahl (0 Stempel ist **kein**
  Fehler, das ist Abwesenheit) plus die offline geratenen Richtungen.
- **Korrektur strikt additiv:** `INSERT device='korrektur:<user>'`, nie UPDATE/DELETE. Das
  Roh-Log ist die lohnrelevante Urkunde.
- Excel + PDF (A4-Monatsblatt), Mobile als Card-Liste.
- **Projektzeit-Spalte neutral** — kein Fehler-Styling. Anwesenheit und Projektzeit messen
  Verschiedenes; eine Abweichung ist normal.

### v3.9.693 — Teil F (NFC im Büro) + Teil G (Terminal-UI + Antrag)

**Teil F — `WorkerNfcPanel`** im Mitarbeiter-Formular (Gate wie `worker_edit`): Chips können
jetzt im Büro zugeordnet werden statt nur am Kiosk. Reader-tauglich; **Enter im Chip-Feld
submittet das Worker-Formular nicht** (sonst hätte jeder Chip-Scan nebenbei den ganzen
Datensatz gespeichert). Kollisionsprüfung als **frischer REST-Read** vor dem Patch (nicht aus
lokalem State — ein anderer Büro-Rechner könnte den Chip gerade vergeben haben), plus **23505**
vom Unique-Index abgefangen. „Chip entfernen" für Verlust/Austritt. Kein neues DDL.

**Teil G — eigene Terminal-UI.** Idle: große Uhr, „Chip hinhalten zum Stempeln", **genau ein**
Antrags-Button. Der Scan bleibt der Hauptweg. 4-Schritt-Flow: Chip-Identifikation (kein
Passwort) → Urlaub|ZA → Von/Bis → Bestätigen.

**Der kritischste Punkt des ganzen Pakets:** der Antrag schreibt `status='beantragt'` —
**nicht** `'ausstehend'`. Der Auftragstext sagte `'ausstehend'`; der Code sagt etwas anderes.
`'ausstehend'` ist nur der Wert der Client-Map `absApprovals`; der DB-Trigger
`guard_urlaub_edit()` prüft hart auf `COALESCE(NEW.status,'beantragt')='beantragt'`. Ein Antrag
mit `'ausstehend'` wäre erst **beim Sync** gescheitert — lange nachdem der Monteur am Panel ein
grünes Häkchen gesehen hat. Ein Test nagelt das fest.

Datenweg sonst 1:1 wie `submitRequest`: ein Datensatz **pro Werktag**, `id=Name_YYYY-MM-DD`,
`from_date=to_date`, Sa/So/Feiertage übersprungen, Schreibweg `SQ.push`. Doppel-Antrag wird
übersprungen und gemeldet, nie still überschrieben.

**Datenschutz am Wandpanel:** nur Vor-/Nachname, **keine Salden, kein Resturlaub, keine
Historie**. 30-s-Inaktivitäts-Timeout vergisst die Identifikation (Erfolgs-Screen 5 s). Ein
Test verbietet `Resturlaub`/`Saldo`/`urlaubskontingent` in den Panel-Screens.

---

## SQL Run-Gate — WAS SEBASTIAN AUSFÜHREN MUSS

| Datei | Stand |
|---|---|
| `sql/FZ_TRACKER_v1.sql` | ✅ gelaufen (14.07., Human-Run-Gate) |
| `system_config` Seed `stempel_pause_rules` = `{"Backoffice":0,"default":60}` | ✅ gelaufen — Schlüssel **„Backoffice"**, nicht „buero" |
| `sql/MONTAGEZULAGE_v1.sql` | ✅ gelaufen (Tabelle `montagezulage_tage` existiert) |
| **`sql/STEMPEL_TERMINAL_v1.sql`** | ⏳ **OFFEN — Teil G funktioniert ohne diese Datei NICHT** |
| `sql/GPS_RETENTION_v1.sql` | ⏳ offen, bewusst inert (nur Vorbereitung) |

> **Achtung, der Stolperstein:** `STEMPEL_TERMINAL_v1.sql` enthält nicht nur die Policies, sondern
> auch ein `CREATE OR REPLACE FUNCTION guard_urlaub_edit()`. **Grund:** Der Terminal-User hat
> keine Zeile in `public.users` und damit **keine `monteur_id`**. Der bestehende Trigger erlaubt
> Nicht-Admins nur `NEW.worker_id = me.monteur_id` — für den Terminal-User ist das nie wahr, also
> würde **jeder** Terminal-Antrag am `RAISE EXCEPTION` scheitern. Der neue Zweig erlaubt der Rolle
> `stempel_terminal` ausschließlich `INSERT` mit `status='beantragt'`, für beliebige `worker_id`.
> Kein UPDATE, kein DELETE, kein Zugriff auf `urlaubskontingent`.

---

## OFFEN — bewusst NICHT gebaut

### Punkt 2: Anwesenheits-Basis auf `stempel_log` (lohnrelevant) — **HÄLT AUF SEBASTIAN**

Die Inventur ist fertig. **Anzufassen:** `KVZulagenReport` (Taggeld-Tage >6 h/>11 h) und
`KVZuschlagReport` (Überstunden, Ü50/Ü100). **Unverändert:** BWB, Projektstunden,
Stundenbestätigung, Projekt-Budget, Montagezulage-Teil (der ist bereits sauber auf
Baustellen-Flags geschnitten).

**Vier Fragen, die Sebastian einzeln entscheiden muss — vorher wird keine Zeile umgestellt:**

1. **KVZuschlagReport mit umstellen?** Überstunde = „Stunden über der Tagesnorm" ist inhaltlich
   Anwesenheit. Zuschläge brauchen echte Von/Bis-Uhrzeiten (Nachtfenster 20–6), die
   `time_entries` gar nicht sauber führt — Stempel wäre die bessere Basis.
2. **FinkZeit-Abgleich entschärfen?** HomeView + Monatsabrechnung warnen **rot** bei ≥0,5 h
   Abweichung — strukturell genau die Abweichung, die zur Normalität erklärt wurde, nur gegen
   ein externes System.
3. **Chef-Auslastungs-Ampel** auf `stempel_log`? Nicht lohnrelevant; unverbuchte Zeit drückt die
   Ampel heute künstlich.
4. **Self-Service-Karte „⏱️ Arbeitszeit"** — auf `stempel_log` umstellen oder Label auf
   „Projektstunden" präzisieren? Der Monteur liest sie heute als seine Anwesenheit.

Bei Freigabe gilt die **Übergangsregel je MA+Monat**: Stempel vorhanden → Stempel-Basis; keine
Stempel → bisherige `time_entries`-Näherung, im Report gekennzeichnet („Basis: Zeiterfassung
(keine Stempel)"). Kein Stichtag, der Rollout läuft MA-weise. **Abnahme am durchgerechneten
€-Beispiel** (1 MA, 1 Monat, Delta beim Taggeld) **vor** weiteren lohnwirksamen Änderungen.

### Flotte-Ausbau — nach dem Stempel-Paket

Richtung steht (Fahrer-Zuordnung, Kosten & Fristen, Karten-UX), mit Leitplanken:
Stammfahrer-Anzeige ja, **automatische Ableitung „wer ist wann gefahren" aus Stempel-/NFC-Daten
ist TABU** ohne eigenen Entscheid (§96 ArbVG — GPS mit Personen zu verknüpfen ist eine andere
Kategorie als Fahrzeug-Ortung). Kosten/Fristen: **Bestand prüfen** (Tank-Log, Ø-Verbrauch v600,
Pickerl-/Service-Alerts v622 existieren) — nur verlinken, keine Zweitimplementierung.

### Gleitzeit-Konto — Produktentscheid, nichts vorweggenommen

Fink führt ein **kumulatives** Gleitzeit-Stundenkonto über Monatsgrenzen (+78:06). Wir haben
Resturlaub (`_resturlaubK`), aber **kein kumulatives Gleitzeit-Saldo**. Die PZE zeigt den
Monatssaldo **nur an** und schreibt ihn **nicht fort**.

---

## Der eine Satz, der über allem steht

**`fz_positions` ist leer. Die Tracker sind nicht bestellt** (laufen, aber nicht da). Die gesamte
Flotte ist ausschließlich durch Tests abgesichert — kein echter GPS-Punkt ist je durch die Kette
gelaufen. Der erste Realitätstest ist der Traccar-Pilot.

Für die Stempeluhr gilt sinngemäß dasselbe: **`stempel_log` ist leer, bis der erste Chip
angelernt und der erste Scan gemacht ist.** Teil C rechnet korrekt — aber niemand hat je einen
echten Stempel durch diese Kette geschickt.

---

## Dauerhafte Tabus

- **`sync_supplier` NICHT deployen.** Läuft produktiv als **v9**, Source nicht im Repo.
- Juprowa-Kern, Auth-Pfade, OFFA-Writes, `.github/workflows/*` (PAT ohne `workflow`-Scope).
- **Kein `.env` mit DB-Passwort** (Entscheid Sebastian 14.07.). Braucht Claude Code einen eigenen
  SQL-Pfad, läuft das über OAuth mit Sebastians Klick — nie über Credentials auf der Platte.
- **NFC-Chips:** nur die neu beschafften 13,56-MHz-Chips. Die **Fink-Ausweise werden nicht
  wiederverwendet** — sie werden am neuen Reader nicht gelesen. Beide Reader (Büro + Panel)
  vorher auf **10-stellig dezimal** fixieren, sonst liefert derselbe Chip zwei verschiedene UIDs.
