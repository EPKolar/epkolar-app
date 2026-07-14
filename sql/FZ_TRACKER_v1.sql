-- ═══════════════════════════════════════════════════════════════════
-- FZ_TRACKER_v1.sql — GPS-Geraet am Fahrzeug fuehren (App v3.9.689)
-- IDEMPOTENT. NICHT automatisch ausgefuehrt — HUMAN-RUN-GATE.
-- Ausfuehren im Supabase SQL-Editor (Projekt jiggujpruejkaomgxarp).
--
-- Hardware-Bestand: 12x Teltonika FMC003 (OBD) + 1x FMC130 (festverdrahtet,
-- LKW Scania TU-83JM) + 1NCE-SIMs.
--
-- tracker_imei existiert bereits (aus sql/GPS_v1.sql) — hier kommen nur die
-- drei fehlenden Geraete-Felder dazu.
--
-- RLS: KEINE Aenderung noetig. Die bestehende fahrzeuge_update-Policy
-- (admin/projektleiter/buero) deckt neue Spalten automatisch mit ab —
-- Policies gelten pro ZEILE, nicht pro Spalte.
-- ═══════════════════════════════════════════════════════════════════

ALTER TABLE public.fahrzeuge ADD COLUMN IF NOT EXISTS tracker_typ       text;  -- FMC003 | FMC130 | sonstiges
ALTER TABLE public.fahrzeuge ADD COLUMN IF NOT EXISTS tracker_sim       text;  -- 1NCE-SIM: ICCID oder Nummer
ALTER TABLE public.fahrzeuge ADD COLUMN IF NOT EXISTS tracker_eingebaut date;  -- Einbautag

-- ── Verifikation nach dem Run ──────────────────────────────────────
--   select column_name, data_type from information_schema.columns
--     where table_name='fahrzeuge'
--       and column_name in ('tracker_imei','tracker_typ','tracker_sim','tracker_eingebaut');
--   -- erwartet: 4 Zeilen
--
-- Die App erkennt fehlende Spalten SELBST (Sniff am geladenen Datensatz) und
-- sperrt die drei Felder bis zum Run — sie versucht dann keinen PATCH auf
-- nicht existierende Spalten (PostgREST wuerde 400 werfen). Nach dem Run ist
-- sie ohne App-Update voll funktionsfaehig.
--
-- IDEMPOTENT: ADD COLUMN IF NOT EXISTS. Beliebig oft ausfuehrbar.
