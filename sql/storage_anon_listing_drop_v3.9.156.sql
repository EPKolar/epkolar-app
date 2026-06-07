-- ✅ APPLIZIERT 2026-06-07 (CC, Sebastian-freigegeben). Storage-Enumeration-Lücke geschlossen.
--
-- BEFUND: Bucket epkolar-files (public) hatte 2 storage.objects-SELECT-Policies, die anon volles LISTEN
--   erlaubten ("Allow anon reads" TO anon, "Public read epkolar-files" TO public) → anon konnte alle
--   Projekt-Dokumente/Fotos/Pläne enumerieren (/object/list → Pfade) und per public-URL laden.
-- App-Abhängigkeit geprüft: Frontend nutzt NUR den public-Endpoint (/storage/v1/object/public/, umgeht RLS,
--   Z.1583 _publicUrl) und listet NIE (kein .list()) → diese SELECT-Policies werden nicht gebraucht.
-- FIX: beide SELECT-Policies droppen → anon kann nicht mehr listen; public-URL-Download bleibt.
-- Verifiziert (anon, Vorher→Nachher): public-Download HEAD 200 → 200 (unverändert); /object/list 200/4 → 200/0 (leer).

DROP POLICY IF EXISTS "Allow anon reads" ON storage.objects;
DROP POLICY IF EXISTS "Public read epkolar-files" ON storage.objects;

-- OFFEN (größere Sebastian-Entscheidung): Bucket bleibt PUBLIC → wer einen exakten Pfad kennt/errät
--   (plans/<projectid>/<ts>_<name>.pdf) kann weiter direkt laden. Echter Schutz = Bucket privat +
--   createSignedUrl (zeitbegrenzt) überall im Frontend (Refactor). Dieser Drop schließt nur die Enumeration.
-- REIHENFOLGE: standalone, keine Abhängigkeit (App nutzt nur /object/public). Bereits LIVE ausgeführt.
-- ROLLBACK: sql/storage_anon_listing_drop_v3.9.156_ROLLBACK.sql (Recreate beider Policies, exakte alte Defs).
