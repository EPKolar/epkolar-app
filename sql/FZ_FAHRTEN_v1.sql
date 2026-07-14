-- ═══════════════════════════════════════════════════════════════════
-- FZ_FAHRTEN_v1.sql — Fahrtenbuch-Persistenz (App v3.9.681, Phase F2)
-- IDEMPOTENT. NICHT automatisch ausgefuehrt — HUMAN-RUN-GATE.
-- Ausfuehren im Supabase SQL-Editor (Projekt jiggujpruejkaomgxarp).
--
-- Entscheid Sebastian 14.07.2026: Fahrten werden PERSISTIERT.
-- Alles ist geschaeftlich — es gibt KEIN zweck-Feld und keinen
-- Privat/Geschaeftlich-Umschalter. Der "Zweck" einer Fahrt ist die
-- Kundenzuordnung: optional ein Projekt und/oder ein Arbeitsschein,
-- nachtraeglich gesetzt durch Buero/Projektleitung.
--
-- ── Wie die Daten entstehen ────────────────────────────────────────
-- Die Fahrt selbst wird NICHT vom Tracker geliefert, sondern aus
-- fz_positions segmentiert (_fzSegmente, App v3.9.679: Zuendung
-- primaer, speed als Fallback, Stillstand > 5 min beendet die Fahrt,
-- km via Haversine). Der Client schreibt die berechneten Fahrten hier
-- hoch — idempotent ueber (fahrzeug_id, beginn).
--
-- WICHTIG, damit spaeter niemand raetselt: (fahrzeug_id, beginn) ist
-- nur so stabil wie die Segmentierungs-Parameter. Aendert jemand
-- stillMin oder minFahrtM, verschieben sich Fahrt-Grenzen und es
-- entstehen Karteileichen mit alten beginn-Zeitpunkten. Wer an den
-- Parametern dreht, muss die Tabelle neu aufbauen.
-- ═══════════════════════════════════════════════════════════════════

-- ── 1) Fahrten ──────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.fz_fahrten (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  fahrzeug_id      text NOT NULL,
  beginn           timestamptz NOT NULL,
  ende             timestamptz NOT NULL,
  dauer_min        integer,
  km               numeric,
  start_lat        double precision,
  start_lon        double precision,
  end_lat          double precision,
  end_lon          double precision,
  start_ort        text,          -- Reverse-Geocoding (Nominatim, Phase F3). Bis zum 1. Lookup NULL.
  ziel_ort         text,          -- dito. Siehe sql/GEO_CACHE_v1.sql.
  tacho_von        numeric,       -- OEM-Kilometerstand, fahrzeugabhaengig verfuegbar
  tacho_bis        numeric,       -- ZUSATZINFO — km wird IMMER aus Haversine gerechnet
  fahrer_id        text,          -- workers.id; wer das Fahrzeug an dem Tag hatte
  projekt_id       text,          -- optionale Kundenzuordnung (Buero/PL, nachtraeglich)
  arbeitsschein_id text,          -- optionale AS-Verknuepfung
  notiz            text,
  created_at       timestamptz DEFAULT now(),
  updated_at       timestamptz DEFAULT now()
);

-- Idempotenz-Anker: eine Fahrt ist eindeutig ueber Fahrzeug + Beginn.
-- Darueber laeuft der Upsert des Clients (on_conflict=fahrzeug_id,beginn).
CREATE UNIQUE INDEX IF NOT EXISTS fz_fahrten_fz_beginn_uidx
  ON public.fz_fahrten (fahrzeug_id, beginn);

CREATE INDEX IF NOT EXISTS fz_fahrten_fahrzeug_beginn_idx
  ON public.fz_fahrten (fahrzeug_id, beginn DESC);

-- ── 2) RLS: exakt wie fz_positions ─────────────────────────────────
-- GPS ist eine Kontrollmassnahme (§96 ArbVG). Monteure sehen den
-- Flotte-Tab nicht und duerfen diese Tabelle nicht lesen.
ALTER TABLE public.fz_fahrten ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS fz_fahrten_select_staff ON public.fz_fahrten;
CREATE POLICY fz_fahrten_select_staff ON public.fz_fahrten
  FOR SELECT USING (is_staff());

-- Schreiben: ebenfalls nur Staff. Der Client schreibt die segmentierten
-- Fahrten hoch und setzt spaeter die Kundenzuordnung.
DROP POLICY IF EXISTS fz_fahrten_insert_staff ON public.fz_fahrten;
CREATE POLICY fz_fahrten_insert_staff ON public.fz_fahrten
  FOR INSERT WITH CHECK (is_staff());

DROP POLICY IF EXISTS fz_fahrten_update_staff ON public.fz_fahrten;
CREATE POLICY fz_fahrten_update_staff ON public.fz_fahrten
  FOR UPDATE USING (is_staff()) WITH CHECK (is_staff());

-- lager_display hart geblockt (Kiosk darf GPS-Daten NIE sehen) —
-- RESTRICTIVE, gilt zusaetzlich zu allen PERMISSIVE-Policies oben.
DROP POLICY IF EXISTS fz_fahrten_no_lager_display ON public.fz_fahrten;
CREATE POLICY fz_fahrten_no_lager_display ON public.fz_fahrten AS RESTRICTIVE
  FOR ALL USING ( ((auth.jwt() -> 'app_metadata') ->> 'role') IS DISTINCT FROM 'lager_display' );

-- ── 3) updated_at automatisch ──────────────────────────────────────
CREATE OR REPLACE FUNCTION public.fz_fahrten_touch()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END $$;

DROP TRIGGER IF EXISTS fz_fahrten_touch_trg ON public.fz_fahrten;
CREATE TRIGGER fz_fahrten_touch_trg
  BEFORE UPDATE ON public.fz_fahrten
  FOR EACH ROW EXECUTE FUNCTION public.fz_fahrten_touch();

-- ── Verifikation nach dem Run ──────────────────────────────────────
--   select count(*) from public.fz_fahrten;               -- 0, Tabelle existiert
--   select * from pg_policies where tablename='fz_fahrten';
-- Die App erkennt die fehlende Tabelle selbst (42P01/404) und zeigt
-- bis zum Run einen Banner statt zu crashen.
