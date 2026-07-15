# docs/wip — Status (Stand 15.07.2026)

## 📌 REFERENZ — bleibt (nicht löschen)
- `trigger_bodies_LIVE_2026-07-14.csv` — Voll-Export der 5 guard-Trigger-Bodies aus der DB, kalibriert.
- `guard_*_LIVE_2026-07-14.sql` (5×) — die echten Live-Bodies 1:1. **Einzige Wahrheit**, wenn je einer
  dieser Trigger geändert werden muss (NIE die Rekonstruktion `sql/security_triggers_LIVE_v3911.sql`).
- `VERIFY_NACH_V3_RUN.sql` — read-only Kontrolle nach dem TERMINAL_FINAL_v3-Run (Trigger-Hash, 7 Kiosk-
  Sperren, 1 Terminal-User). Kann bleiben als Wiederhol-Check.

## ✅ ERLEDIGT — historisch, kann bei Bedarf archiviert werden
- `ZEITERFASSUNG_AUFTRAG_2026-07-13.md` — ursprünglicher Terminal-/Stempeluhr-Auftrag. **Komplett
  umgesetzt** (Teile A–G + Rollenkonsolidierung + Trigger, live in Betrieb seit 15.07.).

## 🟡 WIP — offen, gehört noch nicht ins Repo-Hauptwerk
- `FLOTTE_GPS_WIP_2026-07.md` / `.patch` — GPS/Flotte-WIP-Stash. Bezug: `gps_ingest`-Deploy (gesperrt).
- `HUNT_ASCII_WIP_2026-04.md` / `.patch` — Alt-WIP aus April.
