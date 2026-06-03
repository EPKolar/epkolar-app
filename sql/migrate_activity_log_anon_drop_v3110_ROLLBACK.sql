-- v3.10.5 ROLLBACK activity_log anon-INSERT
CREATE POLICY activity_log_anon_insert
  ON public.activity_log FOR INSERT TO public
  WITH CHECK (auth.role() = 'anon');
