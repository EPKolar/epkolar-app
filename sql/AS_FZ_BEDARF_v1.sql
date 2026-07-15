-- ═══════════════════════════════════════════════════════════════════════════
-- AS_FZ_BEDARF_v1.sql  ·  Dispo-Assistent Etappe 2  ·  Human-Run-Gate
-- ═══════════════════════════════════════════════════════════════════════════
-- Fahrzeug-Bedarf am Arbeitsschein (App-only — OFFA/JUPROWA hat kein Feld dafuer).
-- Inhalt: jsonb-Array von Anforderungen, Stufe 1:
--   [{"typ":"Steiger"}]           -- Typ-Bedarf (aus dem Spez-Praedikat)
--   [{"fz_id":"<uuid>"}]          -- konkretes Fahrzeug, wenn das Buero eines will
-- Idempotent, keine RLS-Aenderung (erbt die bestehenden arbeitsscheine-Policies).
-- KEIN Ausführen durch CC.
--
-- Client ist 42703-tolerant gebaut (v706-Muster): solange die Spalte fehlt, laesst
-- der Schreibpfad fz_bedarf beim PATCH weg, der Lesepfad behandelt undefined wie
-- leer. Der App-Push auf main ist damit VOR diesem Run gefahrlos.
-- HART: fz_bedarf geht NIE in einen Juprowa/OFFA-Push-Body (App-only).
-- ═══════════════════════════════════════════════════════════════════════════

ALTER TABLE public.arbeitsscheine
  ADD COLUMN IF NOT EXISTS fz_bedarf jsonb DEFAULT NULL;

-- Selbst-Nachweis nach dem Run (read-only):
--   SELECT column_name, data_type FROM information_schema.columns
--     WHERE table_schema='public' AND table_name='arbeitsscheine' AND column_name='fz_bedarf';
--   -- Erwartung: 1 Zeile, data_type=jsonb.
