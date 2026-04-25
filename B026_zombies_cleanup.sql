-- B-026 Zombie-Cleanup
-- Datum: 25.04.2026
-- Quelle: Bug 4dd8a67 (pre-fix), 3 absences-Rows mit worker_id='Günther'
-- Sebastian: nach Rückkehr im Supabase SQL-Editor ausführen.

-- Vorab-Check: wieviele Zeilen werden gelöscht?
SELECT COUNT(*) AS zombie_count FROM absences WHERE worker_id='Günther';
-- Erwartet: 3

-- Detail-Check
SELECT id, worker_id, von, bis, art FROM absences WHERE worker_id='Günther';

-- DELETE (nach Verifikation der COUNT-Query)
DELETE FROM absences WHERE worker_id='Günther';

-- Verify nach DELETE
SELECT COUNT(*) AS post_delete_count FROM absences WHERE worker_id='Günther';
-- Erwartet: 0
