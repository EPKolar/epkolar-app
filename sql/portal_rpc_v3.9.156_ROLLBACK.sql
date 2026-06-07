-- ROLLBACK für portal_rpc_v3.9.156.sql
-- Entfernt die RPC. NUR ausführen, wenn das Portal NICHT mehr direkt auf die Tabellen zugreift
-- UND die anon-Policies (Phase 4) noch NICHT gedroppt sind — sonst bricht das Portal komplett.
-- (Reihenfolge-Sicherheit: RPC droppen ist nur sicher, solange das Frontend noch den Direktread-Fallback hat.)
DROP FUNCTION IF EXISTS public.portal_fetch(text);
