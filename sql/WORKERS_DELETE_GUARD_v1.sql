-- ═══════════════════════════════════════════════════════════════════
-- WORKERS_DELETE_GUARD_v1.sql — Loeschschutz workers auf DB-Ebene
-- (Handoff 23.07.2026, Punkt 3 — "FK-/ON DELETE RESTRICT-Konzept").
-- IDEMPOTENT. NICHT automatisch ausgefuehrt — Human-Run-Gate (Sebastian).
-- Ausfuehren im Supabase SQL-Editor (Projekt jiggujpruejkaomgxarp).
--
-- ── WARUM TRIGGER STATT FOREIGN KEYS ────────────────────────────────
-- Der Auftrag lautet "ON DELETE RESTRICT-Konzept, NICHT CASCADE": ein
-- Mitarbeiter mit anhaengenden Daten darf nicht loeschbar sein, ohne die
-- Daten mitzureissen. Echte FOREIGN-KEY-Constraints leisten das — wuerden
-- aber ZUSAETZLICH jeden INSERT/UPDATE des Kindes gegen workers.id pruefen.
-- Die App schreibt bei "kein Fahrer/Monteur" NICHT NULL, sondern den
-- LEERSTRING '' (z.B. VehicleView.addFz: fahrer:"", AS-Formular: montId="").
-- '' ist nicht NULL -> ein FK wuerde diese Writes ablehnen (kein workers.id=''):
-- Fahrzeug-Anlage und Schein-ohne-Monteur wuerden brechen. Das zu umgehen
-- hiesse alle Write-Pfade auf NULL umzubauen (breiter, riskanter App-Eingriff).
-- Ein BEFORE-DELETE-Trigger auf workers erreicht die GLEICHE Semantik
-- (Loeschen blockieren wenn referenziert), fasst die Kind-Spalten aber NICHT
-- an -> '' bleibt erlaubt, keine App-Aenderung noetig.
--
-- ── VERHAELTNIS ZUM APP-BLOCK (v3.9.824) ────────────────────────────
-- Der App-Block in delMonteur prueft 5 Tabellen und ist die schnelle,
-- benutzerfreundliche Vorderseite (Dialog mit Zahlen). Dieser Trigger ist
-- die HINTERSEITE: er greift auch bei einem DELETE per SQL-Editor/Dashboard,
-- gegen den die App nichts ausrichten kann. Als letzte Verteidigungslinie
-- deckt er BEWUSST MEHR ab — die volle worker-referenzierende Historie.
-- Feuert der Trigger bei einem App-DELETE (nur moeglich wenn ausschliesslich
-- eine der "kleinen" Tabellen referenziert und keine der App-5), faengt
-- delMonteur die Exception und zeigt "Loeschen fehlgeschlagen" — kein
-- stiller Datenverlust. (Optionale spaetere Angleichung: App-Block auf die
-- gleiche Tabellenliste ziehen. Nicht Teil dieses Files.)
--
-- ── DATENSTAND-PREFLIGHT (read-only, 23.07.2026 gemessen) ────────────
-- KEINE Waisen in irgendeiner Referenzspalte (0/0/0/0/0 bei den App-5).
-- Nur Leerstrings, die ein Trigger NICHT stoert (er prueft nur DELETE auf
-- workers, nicht die Kind-Writes): arbeitsscheine.monteur=2, fahrzeuge.fahrer=12,
-- users.monteur_id 1x schon NULL. -> Es ist KEINE Datenbereinigung noetig,
-- der Trigger ist rein vorwaerts wirkend. Zur Re-Verifikation vor dem Lauf:
--
--   with w as (select id from workers)
--   select 'time_entries' t, count(*) filter (where worker_id not in (select id from w) and coalesce(worker_id,'')<>'') orphan from time_entries
--   union all select 'absences', count(*) filter (where worker_id not in (select id from w) and coalesce(worker_id,'')<>'') from absences
--   union all select 'arbeitsscheine', count(*) filter (where monteur not in (select id from w) and coalesce(monteur,'')<>'') from arbeitsscheine
--   union all select 'fahrzeuge', count(*) filter (where fahrer not in (select id from w) and coalesce(fahrer,'')<>'') from fahrzeuge;
--   -- alle 0 erwartet.
-- ═══════════════════════════════════════════════════════════════════


-- ── 1) Guard-Funktion ───────────────────────────────────────────────
-- Prueft eine feste Liste (Tabelle, Spalte) auf Zeilen, die auf OLD.id
-- zeigen (nicht NULL, nicht ''). Sammelt "tabelle (n)" fuer alle Treffer
-- und wirft dann EINE Exception mit vollstaendiger Auflistung.
-- SQLSTATE 23001 = restrict_violation -> semantisch exakt ON DELETE RESTRICT.
--
-- Die Liste ist bewusst als VALUES-Array editierbar: um eine Tabelle vom
-- Schutz auszunehmen bzw. hinzuzufuegen, genau eine Zeile streichen/ergaenzen.
CREATE OR REPLACE FUNCTION public.workers_block_delete_if_referenced()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
  r        record;
  n        bigint;
  hits     text := '';
BEGIN
  FOR r IN
    -- (Tabelle, Spalte, Klartext-Label). Reihenfolge = Anzeige-Reihenfolge.
    -- GESCHUETZT: Historie / Lohn / Compliance / Zuordnung. Ein Loeschen
    -- wuerde diese Zeilen verwaisen lassen (kein FK -> stiller Verlust).
    SELECT * FROM (VALUES
      ('time_entries',           'worker_id',  'Zeiteintraege'),
      ('absences',               'worker_id',  'Abwesenheiten'),
      ('arbeitsscheine',         'monteur',    'Arbeitsscheine'),
      ('fahrzeuge',              'fahrer',     'Fahrzeuge (Fahrer)'),
      ('users',                  'monteur_id', 'Logins'),
      ('fahrtenbuch',            'worker_id',  'Fahrtenbuch'),
      ('stempel_log',            'worker_id',  'Stempeluhr-Log'),
      ('finkzeit',               'worker_id',  'FinkZeit-Lohnexport'),
      ('urlaubsantraege',        'worker_id',  'Urlaubsantraege'),
      ('urlaubskontingent',      'worker_id',  'Urlaubskontingent'),
      ('entfernungszulage_tage', 'worker_id',  'Entfernungszulage-Tage'),
      ('montagezulage_tage',     'worker_id',  'Montagezulage-Tage'),
      ('fahrbewilligungen',      'worker_id',  'Fahrbewilligungen'),
      ('fahrzeug_buchungen',     'worker_id',  'Fahrzeug-Buchungen'),
      ('material_items',         'worker_id',  'Material-Zuordnungen'),
      ('defects',                'worker',     'Maengel'),
      ('anmeldungen',            'worker_id',  'Anmeldungen'),
      ('absence_files',          'worker_id',  'Abwesenheits-Anhaenge'),
      ('worker_kompetenzen',     'worker_id',  'Kompetenzen'),
      ('worker_projects',        'worker_id',  'Projekt-Zuordnungen')
      -- BEWUSST NICHT GESCHUETZT (transiente Planungsdaten, ueberschreibbar):
      --   dispo_blocks (worker_id)  — Dispo-Sperren
      --   weekplan_rows (jsonb z)   — Wochenplan-Belegung (kein Skalar-FK moeglich)
      -- Begruendung wie im App-Block: an ihnen haengt keine Historie; sie zu
      -- schuetzen wuerde jeden je verplanten Mitarbeiter dauerhaft unloeschbar
      -- machen. Zum Hinzufuegen: Zeile oben in die VALUES-Liste aufnehmen.
    ) AS t(tab, col, label)
  LOOP
    EXECUTE format(
      'SELECT count(*) FROM public.%I WHERE %I = $1 AND %I IS NOT NULL AND %I <> ''''',
      r.tab, r.col, r.col, r.col
    ) INTO n USING OLD.id;
    IF n > 0 THEN
      hits := hits || CASE WHEN hits = '' THEN '' ELSE ', ' END || r.label || ' (' || n || ')';
    END IF;
  END LOOP;

  IF hits <> '' THEN
    RAISE EXCEPTION
      'Mitarbeiter % (%) kann nicht geloescht werden — es haengen noch Daten daran: %. Bitte stattdessen ein Austrittsdatum setzen (workers.austritt).',
      COALESCE(NULLIF(TRIM(COALESCE(OLD.vorname,'') || ' ' || COALESCE(OLD.name,'')), ''), OLD.id), OLD.id, hits
      USING ERRCODE = '23001';  -- restrict_violation
  END IF;

  RETURN OLD;  -- keine Referenzen -> Loeschen zugelassen
END;
$$;


-- ── 2) Trigger (idempotent neu binden) ──────────────────────────────
DROP TRIGGER IF EXISTS trg_workers_block_delete ON public.workers;
CREATE TRIGGER trg_workers_block_delete
  BEFORE DELETE ON public.workers
  FOR EACH ROW
  EXECUTE FUNCTION public.workers_block_delete_if_referenced();


-- ── 3) Nach dem Lauf verifizieren (read-only) ───────────────────────
-- (a) Trigger ist da:
--     select tgname, tgenabled from pg_trigger
--     where tgrelid='public.workers'::regclass and tgname='trg_workers_block_delete';
-- (b) Schutz greift (MUSS mit SQLSTATE 23001 fehlschlagen; w1=Paschinger hat 97 AS):
--     -- in einer Transaktion, die zurueckgerollt wird:
--     begin;
--       delete from workers where id = 'w1';   -- erwartet: ERROR 23001 ... haengen noch Daten daran ...
--     rollback;
-- (c) Ein wirklich freier Datensatz bleibt loeschbar (kein Regress):
--     -- nur zur Kontrolle der Logik, NICHT ausfuehren wenn kein Wegwerf-Worker da ist.
--
-- ── ECHTES HART-LOESCHEN (falls je gewollt) ─────────────────────────
-- Der Trigger ersetzt kein Rechte-System: er blockt IMMER, solange Kinder
-- existieren. Ein legitimes Purgen (z.B. Test-Worker) heisst: erst die
-- Kind-Zeilen loeschen, dann den Worker — das ist die korrekte
-- RESTRICT-Semantik, kein CASCADE. Es gibt bewusst KEINE Bypass-Flag.
