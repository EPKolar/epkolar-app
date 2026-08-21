-- IDEMPOTENT
-- ═══════════════════════════════════════════════════════════════════════════════════════
-- CHECKLIST_SIGNATURES_v1 — Checklisten-Unterschriften persistent machen
-- HUMAN-RUN-GATE: NICHT automatisch ausführen. Sebastian entscheidet + klickt Run.
-- Projekt: jiggujpruejkaomgxarp (Baumanagement & Zeiterfassung). Kein CC-DDL.
--
-- BEFUND (Code-Read 2026-08-21, Nachtlauf-Hunt, verifiziert):
--   Die Checklisten-Unterschriften (SignaturePad :15658, d.sigMA / d.sigKunde) landen auf dem
--   lokalen Checklisten-Objekt (cl.sigMA/cl.sigKunde :15710/:15720), werden aber in KEINEM
--   Netz-Body geschrieben:
--     - POST /api/checklists  (:15712/:15722): body = {id,project_id,name,items,status,created_by}
--     - PUT  /api/checklists/<id> (update :15726): body = {items,status}
--   => Unterschriften leben nur im Render-State und gehen beim Reload / auf anderen Geräten
--      verloren. Das Checklisten-Protokoll-PDF (v3.9.840 _genChecklistPdf) druckt sie darum nur
--      innerhalb derselben Sitzung; nach einem Reload sind die Unterschriftsflächen leer.
--
-- WARUM DDL nötig (nicht rein clientseitig lösbar):
--   PostgREST lehnt einen PUT mit unbekannter Spalte mit 400 ab. Der Client-Schreibweg verwirft
--   bei 400 den GESAMTEN PUT — d.h. würde man sig_ma/sig_kunde blind in den PUT-Body aufnehmen
--   OHNE dass die Spalten existieren, gingen auch items+status verloren. Darum werden die Spalten
--   ZUERST angelegt, DANN wird die Client-Verdrahtung aktiviert (siehe unten).
--
-- SPALTEN: TEXT (die Signatur ist ein data:image/png;base64-String, wie in forms/PZE bereits genutzt).
--   Additiv, nullable, kein Default -> bestehende Zeilen unberührt, keine Migration von Bestandsdaten.
-- ═══════════════════════════════════════════════════════════════════════════════════════

ALTER TABLE public.checklists ADD COLUMN IF NOT EXISTS sig_ma    text;
ALTER TABLE public.checklists ADD COLUMN IF NOT EXISTS sig_kunde text;

COMMENT ON COLUMN public.checklists.sig_ma    IS 'Unterschrift Mitarbeiter (data:image/png;base64) — Abnahmeprotokoll. v3.9.847-staged.';
COMMENT ON COLUMN public.checklists.sig_kunde IS 'Unterschrift Auftraggeber (data:image/png;base64) — Abnahmeprotokoll. v3.9.847-staged.';

-- ── VALIDIERUNG (optional, in zurückgerollter Transaktion, ändert nichts) ──────────────────
-- BEGIN;
--   ALTER TABLE public.checklists ADD COLUMN IF NOT EXISTS sig_ma text;
--   ALTER TABLE public.checklists ADD COLUMN IF NOT EXISTS sig_kunde text;
--   SELECT column_name, data_type, is_nullable
--     FROM information_schema.columns
--    WHERE table_schema='public' AND table_name='checklists' AND column_name IN ('sig_ma','sig_kunde');
--   -- erwartet: 2 Zeilen, text, YES
-- ROLLBACK;
--
-- ── NACH DEM RUN: Client-Verdrahtung aktivieren (separater Commit, dann greift es) ─────────
--   1) POST-Body (:15712 + :15722) ergänzen:  sig_ma:cl.sigMA||"", sig_kunde:cl.sigKunde||""
--   2) update() PUT-Body (:15726) ergänzen:    sig_ma:(_next.sigMA||""), sig_kunde:(_next.sigKunde||"")
--      (und die Signatur-Änderung über update(id, c=>({...c,sigMA,sigKunde})) laufen lassen)
--   3) Load-Mapping (Checklisten, ~:6212) ergänzen:  sigMA:c.sig_ma||"", sigKunde:c.sig_kunde||""
--   4) checklists.items steht bereits in TEXT_JSON_FIELDS (:1802); sig_ma/sig_kunde sind reine
--      TEXT-Strings -> NICHT dort eintragen (kein JSON-Stringify).
--   Danach persistieren die Unterschriften und das v840-PDF zeigt sie auch nach Reload.
-- ═══════════════════════════════════════════════════════════════════════════════════════
