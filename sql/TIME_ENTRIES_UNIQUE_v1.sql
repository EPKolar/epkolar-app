-- IDEMPOTENT
-- ═══════════════════════════════════════════════════════════════════════════════════════
-- TIME_ENTRIES_UNIQUE_v1 — Absicherung gegen Doppel-Übernahme (Zwei-Geräte-Race)
-- HUMAN-RUN-GATE: NICHT automatisch ausführen. Sebastian entscheidet + klickt Run.
-- Projekt: jiggujpruejkaomgxarp (Baumanagement & Zeiterfassung). Kein CC-DDL.
--
-- BEFUND (DB-Read 2026-07-21, read-only, autorisiert):
--   SELECT arbeitsschein_id, count(*) FROM time_entries
--   WHERE arbeitsschein_id IS NOT NULL AND arbeitsschein_id <> ''
--   GROUP BY arbeitsschein_id HAVING count(*) > 1;              -> []  (0 Mehrfach-Gruppen)
--   Gesamt 86 time_entries; davon mit arbeitsschein_id = 0, ohne = 86, distinct arbeitsschein_id = 0.
--   -> Das AS-Übernahme-Feature (v3.9.809) hat noch KEINEN AS-verknüpften Eintrag erzeugt.
--   -> Der Index kann KONFLIKTFREI angelegt werden (0 bestehende betroffene Zeilen).
--
-- GEWÄHLTE VARIANTE: partielles UNIQUE auf arbeitsschein_id (Branch "keine Mehrfach-Gruppen").
--   - Manuelle Zeiterfassung (addEntry) setzt KEINE arbeitsschein_id -> vom WHERE ausgeschlossen,
--     bleibt vollständig unberührt (beliebig viele Einträge ohne arbeitsschein_id erlaubt).
--   - Nur AS-Übernahme-Einträge (Schreibweg mit asId/s.id) sind betroffen. Die Übernahme legt genau
--     EINEN Eintrag je Schein an (Idempotenz-Marker ze_uebernommen). Uniqueness ist die korrekte
--     Invariante und macht die Client-Idempotenz DB-hart: bei einem Zwei-Geräte-Race scheitert der
--     zweite INSERT mit derselben arbeitsschein_id am UNIQUE (statt eine Doppelbuchung anzulegen).
--
-- TRADE-OFF (bewusst, für die Entscheidung dokumentiert):
--   Der Index VERBIETET mehr als einen time_entry je Schein. Das deckt sich exakt mit der heutigen
--   Übernahme-Regel (1 verschmolzener Eintrag = Arbeit + Fahrt). SOLLTE später ein Feature die Zeit
--   eines Scheins auf mehrere Tage/Einträge aufteilen wollen, ist DIESER Index NICHT geeignet ->
--   dann stattdessen UNIQUE(arbeitsschein_id, date) (ein Eintrag je Schein UND Tag) ODER den Race
--   rein client-seitig absichern (deterministische id + insert-if-absent). Heute gilt 1:1.
--
-- ROLLBACK (falls nötig):  DROP INDEX IF EXISTS public.uq_time_entries_as;
-- ═══════════════════════════════════════════════════════════════════════════════════════

CREATE UNIQUE INDEX IF NOT EXISTS uq_time_entries_as
  ON public.time_entries (arbeitsschein_id)
  WHERE arbeitsschein_id IS NOT NULL AND arbeitsschein_id <> '';
