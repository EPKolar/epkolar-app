-- Bauprovisorien QR-Aufkleber: physischer (fremder) Code pro Kasten, einlernbar + wiederfindbar.
-- Angewandt via Supabase MCP apply_migration (bauprovisorien_add_qr_code) 2026-06-30.
-- Spaltenname: qr_code (Werkzeug nutzt 'barcode'; hier bewusst 'qr_code' = klarer + per Auftrag vorgegeben).
-- UNIQUE: ein Code = ein Kasten (kein Doppel-Einlernen). Partieller Index → mehrere NULLs (noch nicht
-- eingelernt) erlaubt. RLS bauprovisorien = staff-only + lager_display_no_select RESTRICTIVE deckt die
-- neue Spalte ab (row-level, spaltenagnostisch) — verifiziert.
ALTER TABLE public.bauprovisorien ADD COLUMN IF NOT EXISTS qr_code text;
CREATE UNIQUE INDEX IF NOT EXISTS bauprovisorien_qr_code_uniq
  ON public.bauprovisorien (qr_code) WHERE qr_code IS NOT NULL;
