-- Kundenstamm-Tabelle (Quelle: Juprowa ServicePad type=KundeList, 6457 Kunden).
-- Angewandt via Supabase MCP apply_migration (recreate_kunden_master_table_full) 2026-06-30.
-- RLS PFLICHT: staff-only + lager_display RESTRICTIVE geblockt (PII-Leck-Lehre).
DROP TABLE IF EXISTS public.kunden;

CREATE TABLE public.kunden (
  kunde_nr      text PRIMARY KEY,        -- KU_NUMMER (dedupliziert auf kunde_nr, latest LAST_MODIFIED gewinnt)
  juprowa_id    text,                    -- top-level KU object ID (KU_ID)
  name          text,                    -- KU_NAME
  strasse       text,                    -- KU_STREET
  plz           text,                    -- KU_ZIP
  ort           text,                    -- KU_CITY
  land          text,                    -- KU_COUNTRY
  matchcode     text,                    -- KU_MATCH
  titel         text,                    -- KU_TITEL
  gesperrt      boolean NOT NULL DEFAULT false,  -- KU_GESPERRT '1'/'0'
  email         text,                    -- CONTACTS[0].KK_EMAIL
  tel           text,                    -- PHONENUMBERS
  juprowa_raw   jsonb,                   -- ganze Zeile (CONTACTS/DEVICES/INFOS fuer spaeter)
  last_modified timestamptz,             -- LAST_MODIFIED (inkrementeller Sync spaeter)
  synced_at     timestamptz,
  created_at    timestamptz NOT NULL DEFAULT now(),
  updated_at    timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX kunden_juprowa_id_idx ON public.kunden(juprowa_id);
CREATE INDEX kunden_matchcode_idx  ON public.kunden(matchcode);

ALTER TABLE public.kunden ENABLE ROW LEVEL SECURITY;

CREATE POLICY kunden_select_staff ON public.kunden FOR SELECT USING (is_staff());
CREATE POLICY kunden_insert_staff ON public.kunden FOR INSERT WITH CHECK (is_staff());
CREATE POLICY kunden_update_staff ON public.kunden FOR UPDATE USING (is_staff()) WITH CHECK (is_staff());
CREATE POLICY kunden_delete_staff ON public.kunden FOR DELETE USING (is_staff());

-- lager_display von Anfang an hart geblockt (sensible Kundendaten).
CREATE POLICY lager_display_no_select ON public.kunden AS RESTRICTIVE FOR SELECT
  USING ( ((auth.jwt() -> 'app_metadata') ->> 'role') IS DISTINCT FROM 'lager_display' );
