-- ROLLBACK für storage_anon_listing_drop_v3.9.156.sql
-- Stellt die 2 gedroppten storage.objects-SELECT-Policies EXAKT wie vor dem Drop wieder her
-- (Definitionen vor dem Drop per pg_policies erfasst 2026-06-07: beide FOR SELECT, qual bucket_id='epkolar-files').
-- NUR nötig, falls ein authenticated-Feature doch Listing/auth-Download über storage.objects braucht
-- (aktuell nutzt das Frontend ausschließlich /object/public/ + listet nie → Rollback normalerweise nicht nötig).
-- ⚠️ Wiederherstellung öffnet die anon-Enumeration der Projekt-Dateien wieder.
CREATE POLICY "Allow anon reads" ON storage.objects
  FOR SELECT TO anon
  USING (bucket_id = 'epkolar-files'::text);

CREATE POLICY "Public read epkolar-files" ON storage.objects
  FOR SELECT TO public
  USING (bucket_id = 'epkolar-files'::text);
