-- ═══════════════════════════════════════════════════════════════════
-- MONTAGEZULAGE_v1.sql — Fundament manuelle Montagezulage (App v3.9.671)
-- IDEMPOTENT. NICHT automatisch ausgefuehrt — Human-Run-Gate (Sebastian).
-- Ausfuehren im Supabase SQL-Editor (Projekt jiggujpruejkaomgxarp).
--
-- Entscheid Sebastian (05.07.2026, KV Metallgewerbe Abschn. VIII Pkt. 5):
-- Die Montagezulage wird MANUELL pro Mitarbeiter-Tag vergeben (Buero/PL
-- setzt ein Tages-Flag), KEINE Auto-Erkennung Baustelle/Werkstatt/Fahrt,
-- keine Wegzeiten, keine Lehrlinge. Die App rechnet:
--   zulagefaehige Tages-Std (ohne Pause) x Satz(Jahr des Tages).
-- Diese Tabelle speichert ausschliesslich das Tages-Flag (aktiv ja/nein);
-- die Berechnung passiert im Client (Pure-Fn _kvMontagezulageTag).
-- ═══════════════════════════════════════════════════════════════════

-- ── 1) Tages-Flag je Mitarbeiter-Tag ────────────────────────────────
-- PK (worker_id, datum): ein Flag PRO TAG (nicht pro time_entry — ein Tag
-- hat oft mehrere Buchungen). Kollidiert damit nicht mit time_entries.
CREATE TABLE IF NOT EXISTS public.montagezulage_tage (
  worker_id  text NOT NULL,
  datum      date NOT NULL,
  aktiv      boolean NOT NULL DEFAULT true,
  created_by text,
  created_at timestamptz DEFAULT now(),
  PRIMARY KEY (worker_id, datum)
);

-- ── 2) RLS: NUR Staff (is_staff()) ──────────────────────────────────
-- Buero/PL/Admin duerfen lesen + setzen; Monteur hat keinen Zugriff
-- (die App zeigt die Vergabe read-only, schreibt aber nichts als Monteur).
ALTER TABLE public.montagezulage_tage ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS montagezulage_tage_select_staff ON public.montagezulage_tage;
CREATE POLICY montagezulage_tage_select_staff ON public.montagezulage_tage
  FOR SELECT USING (is_staff());

DROP POLICY IF EXISTS montagezulage_tage_insert_staff ON public.montagezulage_tage;
CREATE POLICY montagezulage_tage_insert_staff ON public.montagezulage_tage
  FOR INSERT WITH CHECK (is_staff());

DROP POLICY IF EXISTS montagezulage_tage_update_staff ON public.montagezulage_tage;
CREATE POLICY montagezulage_tage_update_staff ON public.montagezulage_tage
  FOR UPDATE USING (is_staff()) WITH CHECK (is_staff());

DROP POLICY IF EXISTS montagezulage_tage_delete_staff ON public.montagezulage_tage;
CREATE POLICY montagezulage_tage_delete_staff ON public.montagezulage_tage
  FOR DELETE USING (is_staff());

-- ═══════════════════════════════════════════════════════════════════
-- ROLLBACK (manuell, NICHT Teil des Vorwaerts-Laufs):
--   DROP POLICY IF EXISTS montagezulage_tage_select_staff ON public.montagezulage_tage;
--   DROP POLICY IF EXISTS montagezulage_tage_insert_staff ON public.montagezulage_tage;
--   DROP POLICY IF EXISTS montagezulage_tage_update_staff ON public.montagezulage_tage;
--   DROP POLICY IF EXISTS montagezulage_tage_delete_staff ON public.montagezulage_tage;
--   DROP TABLE  IF EXISTS public.montagezulage_tage;
-- ═══════════════════════════════════════════════════════════════════
