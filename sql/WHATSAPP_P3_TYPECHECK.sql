-- P3-Diagnose: arbeitsscheine.id und projects.id Typen prüfen
-- vor FK-Ergänzung in whatsapp_log. Lektion 23.04: erst prüfen, dann SQL.
-- Ausführen: Supabase SQL Editor, Ergebnis an Chat-Claude zurückgeben.

SELECT table_name, column_name, data_type, udt_name
FROM information_schema.columns
WHERE table_name IN ('arbeitsscheine','projects') AND column_name = 'id'
ORDER BY table_name;

-- Erwartet: entweder beide int/bigint, oder beide uuid.
-- Ergebnis diktiert ob WHATSAPP_SCHEMA_v3.8.sql die Spalten
--   arbeitsschein_id text  →  arbeitsschein_id <int|uuid> REFERENCES ...
-- umstellen muss (ON DELETE SET NULL).

-- Plus Rollen-Werte prüfen (Plan nutzt 'projektleiter' — verifizieren):
SELECT role, COUNT(*) FROM public.users GROUP BY role ORDER BY role;
