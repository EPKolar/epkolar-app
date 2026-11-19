-- IDEMPOTENT
-- =====================================================================================
-- AUTH_HAERTUNG_5_passwort_hilfe_v1056_ROLLBACK.sql  —  RPC und Protokoll wieder entfernen
-- STATUS: ENTWURF — nur durch Sebastian ueber das Tor. Das Protokoll (nur Benutzernamen + Zeitpunkte) geht verloren;
-- bereits angelegte Benachrichtigungen (id 'pwh_...') bleiben. Die App faellt danach auf den ehrlichen Text zurueck (404).
-- =====================================================================================

BEGIN;
DROP FUNCTION IF EXISTS public.passwort_hilfe_anfragen(text);
DROP TABLE IF EXISTS public.passwort_hilfe_log;
COMMIT;
