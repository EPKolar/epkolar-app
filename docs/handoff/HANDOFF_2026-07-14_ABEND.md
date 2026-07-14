# Handoff 14.07.2026 (Abend) — Stand v3.9.690, pytest 1362 grün

**Arbeitsklon:** `C:\repos\epkolar-app`. srvdc02-Share ist **nur Spiegel** (zieht sich täglich 05:00
selbst nach), **nie** Push-Quelle. Session-Start: `git fetch && git reset --hard origin/main`.

**HEAD:** `3fb2145` (v3.9.690). Working Tree sauber.

---

## Heute gebaut (14.07.)

| Version | SHA | Inhalt |
|---|---|---|
| v3.9.686 | `0449b7f` | Planungs-Wetterzeile zeigte **hartcodierte Demo-Daten** (4/2/7/5/6/3 °) und rief nie eine API auf. Jetzt echte Open-Meteo-Werte für die **angezeigte** KW, Zuordnung über das ISO-Datum. Leaflet-Mausrad zoomt erst nach Klick. |
| v3.9.687 | `7e7c90a` | Flotte F4: Tageskilometer, Geschwindigkeit je Fahrt, Filtersuche, Favoriten. |
| v3.9.688 | `fec37ae` | **LOHNRELEVANT:** 5-Minuten-Raster manuelle Zeiterfassung (von AUF, bis AB). |
| v3.9.689 | `dd5810f` | Flotte-Rollout: alle Fahrzeuge sichtbar (4-stufig), **IMEI-Zuordnung**, GPS-Gerät am Fahrzeug. |
| v3.9.690 | `3fb2145` | Flotte im **Fink-Layout** (3 Panels, ein Frame), Fahrtenbuch fahrzeugübergreifend + Zeitraum + Summen + Excel/PDF. |

### v3.9.688 — 5-Minuten-Rundung (die wichtigste Regel des Tages)

**Betriebsregel, fixiert und vereinbart:** von (Kommen) **AUF**, bis (Gehen) **AB**. Geht bewusst
**zulasten der Monteure**. Ein Test nagelt die Richtung fest — wer sie dreht, dreht die Lohnrichtung.

- Gilt in **beiden** Erfassungskomponenten: `VZeit` **und** `ZeiterfassungView`. (Achtung: die im
  Auftrag genannten Zeilen 12421/12422 liegen in `VZeit`, nicht in `ZeiterfassungView`.)
- Sichtbare Normalisierung beim Verlassen des Feldes (WYSIWYG) + defensiv im Save.
- Timer: Start AUF, Stopp AB; Lauf < 5 min wird **verworfen** statt als 0h gebucht.
- **Nicht rückwirkend.** Stempeluhr unangetastet (hat die Regel längst, rundet erst bei der Auswertung).
- Grenzfall 23:56–23:59: Aufrunden ergäbe 24:00 → wird auf **23:55 gekappt** (ein `00:00` wäre 24 h
  zu früh). Definiert, nicht geraten.

---

## Flotte: F1–F4 komplett + Rollout-fähig

**Sentinels in `index.html`** (Tests hängen daran, Zeilennummern verschieben sich):
`//@FLOTTE-HELPERS` · `//@FLOTTE-STATUS` · `//@FLOTTE-SEGMENTE` · `//@FLOTTE-ANALYSE` ·
`//@FLOTTE-ROLLOUT` · `//@FAHRTENBUCH` · `//@GEOCODE` · `//@WETTER` · `//@ZEIT-RUNDUNG`

**Layout (v690, Fink 1:1):** ein Frame, drei Panels — Fahrzeugliste (~38 %) | Karte oben,
Fahrtenbuch über volle Breite unten. Kein Overlay, kein Toggle, App-Theme.
Mobile: gestapelt, Fahrtenliste als Cards.

**Zwei bewusste Abweichungen vom Auftrag:**
1. **Live-Follow bleibt in der Zeile.** „Sonst nichts pro Zeile" hätte ihn entfernt — dann wäre
   Follow nur noch *beendbar*, nicht mehr *startbar*, und das Feature wäre still verschwunden.
2. **Tacho-Spalte** existiert im Datenmodell (`fz_fahrten.tacho_von/tacho_bis`), wird aber nur
   gerendert, wenn Werte da sind. Bis `gps_ingest` einen Odometer liefert: nie. **Nicht aus
   `km_stand` schätzen** — das ist ein Fahrzeug-Stammdatum, keine Fahrt-Information.

---

## SQL Run-Gate

| Datei | Stand |
|---|---|
| `sql/FZ_FAHRTEN_v1.sql` | ✅ gelaufen |
| `sql/GEO_CACHE_v1.sql` | ✅ gelaufen |
| `sql/MONTAGEZULAGE_v1.sql` | ⏳ **offen** — schaltet die Montagezulage-Tagesvergabe frei (v3.9.685) |
| `sql/FZ_TRACKER_v1.sql` | ⏳ **offen** — `tracker_typ`/`tracker_sim`/`tracker_eingebaut`. Bis dahin sind diese drei Felder im Fahrzeug-Formular gesperrt (Spalten-Sniff), **die IMEI geht aber schon** |
| `sql/STEMPEL_TERMINAL_v1.sql` | noch nicht erstellt (Teil des Stempel-Pakets) |

---

## Offene Aufträge (Reihenfolge)

1. **DB-Lücken direkt schließen** (Sebastian autorisiert CC explizit, 14.07.): `FZ_TRACKER`-Spalten
   ausführen, `system_config`-Seed `stempel_pause_rules` = `{"Backoffice":0,"default":60}`
   (**Schlüssel „Backoffice", nicht „buero"** — v3.9.652-Lektion), plus Policy-/Index-Inventar via
   `pg_policies`/`pg_indexes` für stempel_log, montagezulage_tage, tickets, fahrzeuge.
2. **Stempeluhr-Rollout-Paket** (Teil A Robustheit: HID-Inter-Key-Timeout 200 ms, Fehler-
   klassifizierung 42P01 vs. Netz, `id`-Feld/uuid; Teil B Terminal-Rolle + `STEMPEL_TERMINAL_v1.sql`;
   Teil C Büro-Auswertung + **additive** Korrektur; Teil D Setup-Doku).
3. **`gps_ingest`** (Traccar → `fz_positions`) — eigener Auftrag, der eigentliche Blocker.

---

## Der eine Satz, der über allem steht

**`fz_positions` ist leer. Die Tracker sind nicht bestellt.** Die gesamte Flotte — Segmentierung,
Fahrtenbuch, Geocoding, Auswertung, Fink-Layout — ist **ausschließlich durch Tests abgesichert**.
Kein einziger echter GPS-Punkt und kein einziger echter Nominatim-Lookup ist je durch diese Kette
gelaufen. Was du im Browser siehst, ist der Leer-Zustand.

Der erste Realitätstest ist der Traccar-Pilot.

---

## Dauerhafte Tabus

- **`sync_supplier` NICHT deployen.** Läuft produktiv als **v9**, Source liegt nicht im Repo
  (`ARCHITECTURE.md:144`). Ein „v3-Deploy" hätte eine laufende v9 überschrieben. Daneben existiert
  ein fachlich anderes `supplier-sync` (v2, `verify_jwt: true`) — nicht verwechseln.
- Juprowa-Kern, Auth-Pfade, OFFA-Writes, `.github/workflows/*` (PAT ohne `workflow`-Scope).
- Beide Stashes auf dem srvdc02-Spiegel bleiben liegen (als Patch in `docs/wip/` gesichert).
