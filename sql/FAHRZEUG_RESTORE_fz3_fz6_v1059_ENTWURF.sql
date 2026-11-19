-- IDEMPOTENT
-- =====================================================================================
-- FAHRZEUG_RESTORE_fz3_fz6_v1059_ENTWURF.sql  —  die zwei am 19.11.2026 hart geloeschten Fahrzeuge zurueckholen
--
-- STATUS: ENTWURF — NICHT APPLIZIERT. Nur Sebastian, SQL-Editor, Projekt jiggujpruejkaomgxarp.
-- IDEMPOTENT: die Vorpruefung bricht ab, sobald fz3 oder fz6 (oder ihre Kennzeichen) schon in fahrzeuge stehen —
--   ein zweiter Lauf aendert nichts. Die Werte kommen AUSSCHLIESSLICH aus der Quelle (Tagesbackup oder Geraete-
--   Kopie); dieses Skript erfindet keinen einzigen Wert. Solange ein Platzhalter <AUS_BACKUP...> drinsteht, bricht
--   es ab.
--
-- PROBE ZUERST: letzte Zeile "COMMIT;" durch "ROLLBACK;" ersetzen, laufen lassen, NOTICE-Zeilen lesen
--   (VORHER/geparste Werte/NACHHER). Erst wenn alles stimmt, mit COMMIT erneut ausfuehren.
--
-- ── VORFALL ──────────────────────────────────────────────────────────────────────────
--   19.11.2026 13:18:41 UTC  DELETE /rest/v1/fahrzeuge?id=eq.fz6  (TU-516CP)  HTTP 200, Firefox 160 / Windows
--   19.11.2026 13:19:05 UTC  DELETE /rest/v1/fahrzeuge?id=eq.fz3  (TU-545BC)  HTTP 200, gleiches Geraet
--   (vorher 13:15:57-13:16:09 drei PATCH auf fz4 vom selben Geraet — fz4 steht noch.)
--
-- ── BEFUND (read-only, 19.11.2026 gemessen) ─────────────────────────────────────────
--   Fremdschluessel auf public.fahrzeuge: KEINE (pg_constraint confrelid='public.fahrzeuge' = 0 Zeilen)
--     -> es gab kein ON DELETE CASCADE, KEINE Kind-Zeile wurde mitgeloescht. Einziger Trigger auf fahrzeuge:
--        trg_updated_at_fahrzeuge (BEFORE UPDATE). activity_log hat zu fz3/fz6 nichts.
--   Was VERLOREN ist = nur die zwei fahrzeuge-Zeilen, aber die tragen viel: tank_log, km_log, schaeden, termine,
--     serviceheft, verbrauchsmaterial (Text-Spalten mit JSON), Stammdaten, Pickerl/Service, Tracker-IMEI/SIM.
--   Was NOCH DA ist (verwaist, haengt sich nach dem Restore ueber die id automatisch wieder an):
--     fz3: fz_positions 30, fz_latest 1, fz_fahrten 2  (alle vom 14.07.2026 15:00-16:16 UTC, raw = {"test":1}
--          -> Testdaten der GPS-Einrichtung, keine echte Fahrt)
--     fz6: nichts.
--     beide: fahrtenbuch 0, fahrzeug_buchungen 0, fz_finanzen 0, fz_termine 0, arbeitsscheine.fz_bedarf 0,
--          weekplan_rows 0, dispo_blocks 0, bescheinigungen 0, Storage-Objekte (alle Buckets, Pfad .../fz3|fz6/...) 0.
--     notifications: 4 alte Pickerl-Hinweise ("Pickerl TU-516CP" 02./03.11.2026, "Pickerl TU-545BC" 03.08.2026)
--          -> nur Hinweis zur Plausibilitaet der Pickerl-Daten in der Quelle, KEINE Datenquelle.
--   Kein anderes Fahrzeug traegt heute einen Tracker (tracker_imei ueberall leer) -> die GPS-Einspeisung kennt
--     fz3 erst nach dem Restore wieder.
--
-- ── QUELLE A (empfohlen): logisches Tagesbackup ────────────────────────────────────
--   1. Dashboard -> Project jiggujpruejkaomgxarp -> Database -> Backups. Das Tagesbackup VOR 19.11.2026 13:18 UTC
--      waehlen (normalerweise das vom 19.11. frueh; sonst 18.11.) -> "Download". KEIN "Restore" (PITR/Restore
--      setzt das GANZE Projekt zurueck — alle Zeiteintraege/Scheine seither waeren weg).
--      Hinweis: ist das PITR-Add-on aktiv, gibt es keine Download-Datei — dann Quelle B.
--   2. Datei entpacken (.gz) und in einem Editor oeffnen, der TABULATOREN NICHT in Leerzeichen umwandelt
--      (z. B. Notepad++ / VS Code; NICHT Word).
--   3. Suchen nach:  COPY public.fahrzeuge (     -> diese ganze Zeile ist der KOPF (Spaltenliste).
--   4. Darunter die zwei Datenzeilen, die mit  fz3<TAB>  bzw.  fz6<TAB>  beginnen (Block endet mit "\.").
--   5. Kopf und Zeilen unten in Abschnitt 1 woertlich zwischen die $-Klammern kopieren (Platzhalter ersetzen).
--      Jede Zeile genau so, wie sie im Backup steht — Tabulatoren, \N (= NULL), \n usw. NICHT anfassen.
--
-- ── QUELLE B (Ersatz): Geraete-Kopie in der App (IndexedDB) ─────────────────────────
--   Die App legt die Fahrzeugliste nach jedem Laden in IndexedDB ab: Datenbank "epkolar_offline",
--   Speicher "fahrzeuge", Schluessel "data" (Array). Bei jedem Laden mit Netz wird sie UEBERSCHRIEBEN.
--   Kandidaten laut Edge-Log (letztes Laden der Fahrzeugliste VOR dem Loeschen, danach nicht mehr):
--     iPhone (Google-App) zuletzt 18.11. 21:49 UTC; Android Samsung Internet zuletzt 19.11. 10:22 UTC;
--     Android Chrome Mobile zuletzt 19.11. 10:38 UTC. (User-Agent ist nicht eindeutig je Geraet.)
--   WICHTIG: auf so einem Geraet die App NICHT online oeffnen (sonst ueberschreibt der Abgleich die Kopie).
--     Flugmodus an, App/Browser oeffnen, Entwicklerwerkzeuge -> Konsole (am Handy: Remote-Debugging via USB)
--     und ausfuehren:
--       (async()=>{const r=indexedDB.open("epkolar_offline");r.onsuccess=()=>{const t=r.result.transaction("fahrzeuge","readonly").objectStore("fahrzeuge").get("data");t.onsuccess=()=>{const l=(t.result||[]).filter(f=>f&&(f.id==="fz3"||f.id==="fz6"));console.log(JSON.stringify(l));};};})();
--     Das ist reines LESEN (readonly-Transaktion), es wird nichts veraendert. Ausgabe kopieren.
--   Jedes Objekt dann in Abschnitt 1 als json eintragen (kopf/zeile leer lassen). Die Geraete-Kopie ist die
--   App-Sicht (zusaetzliche camelCase-Felder werden ignoriert; nur echte Spalten zaehlen). updated_at mit dem
--   Backup vergleichen und die NEUERE Quelle nehmen.
--
-- ── WAS DAS SKRIPT TUT ──────────────────────────────────────────────────────────────
--   0 Vorpruefung (Abbruch, wenn fz3/fz6 oder ihre Kennzeichen schon existieren).
--   1 Quelle eintragen (Platzhalter).  2 Parsen + pruefen (id, Kennzeichen, Spaltenzahl, keine fehlende/fremde
--   Spalte — ausser archiviert_am/archiviert_von aus v1059, die bleiben NULL = aktiv).  3 INSERT.
--   4 Kind-Zeilen: NICHTS zu tun (nichts kaskadiert, siehe Befund).  5 Nachher-Zahlen.
--   Kein CASCADE, kein UPDATE/DELETE an anderen Zeilen.
--
-- ROLLBACK: sql/FAHRZEUG_RESTORE_fz3_fz6_v1059_ROLLBACK.sql (loescht genau fz3 und fz6, sonst nichts)
-- =====================================================================================

BEGIN;

-- 0. VORPRUEFUNG + VORHER
DO $$
DECLARE v_as int; v_n int; v_da text;
BEGIN
  SELECT count(*) INTO v_as FROM public.arbeitsscheine;
  SELECT count(*) INTO v_n FROM public.fahrzeuge;
  SELECT string_agg(id || ' ' || coalesce(kennzeichen, ''), ', ') INTO v_da FROM public.fahrzeuge
   WHERE id IN ('fz3', 'fz6')
      OR upper(replace(replace(coalesce(kennzeichen, ''), ' ', ''), '-', '')) IN ('TU545BC', 'TU516CP');
  IF v_da IS NOT NULL THEN
    RAISE EXCEPTION 'Vorpruefung: schon vorhanden (%) - Restore wurde bereits gemacht oder Fahrzeug neu angelegt. Nichts geaendert.', v_da;
  END IF;
  RAISE NOTICE 'VORHER: arbeitsscheine=%, fahrzeuge=% (am 19.11. nach dem Vorfall: 19)', v_as, v_n;
END $$;

-- 1. QUELLE EINTRAGEN  (pro Fahrzeug ENTWEDER kopf+zeile aus dem Backup ODER json von einem Geraet)
CREATE TEMP TABLE _fz_restore_quelle (
  id_erwartet text PRIMARY KEY,
  kz_erwartet text NOT NULL,
  kopf  text,   -- Quelle A: die ganze Zeile "COPY public.fahrzeuge (...) FROM stdin;"
  zeile text,   -- Quelle A: die Datenzeile, beginnt mit fz3<TAB> bzw. fz6<TAB>
  obj   jsonb   -- Quelle B: ein Objekt aus der IndexedDB-Ausgabe
) ON COMMIT DROP;

INSERT INTO _fz_restore_quelle (id_erwartet, kz_erwartet, kopf, zeile, obj) VALUES
  ('fz3', 'TU-545BC',
   $kopf$<AUS_BACKUP: Zeile "COPY public.fahrzeuge (...) FROM stdin;">$kopf$,
   $zeile$<AUS_BACKUP: Datenzeile fz3 (TU-545BC)>$zeile$,
   NULL),   -- Quelle B statt A: kopf/zeile = NULL und hier '<AUS_GERAET: JSON-Objekt fz3>'::jsonb
  ('fz6', 'TU-516CP',
   $kopf$<AUS_BACKUP: Zeile "COPY public.fahrzeuge (...) FROM stdin;">$kopf$,
   $zeile$<AUS_BACKUP: Datenzeile fz6 (TU-516CP)>$zeile$,
   NULL);

-- 2. PARSEN + PRUEFEN
-- COPY-Textformat: Felder durch TAB getrennt, \N = NULL, \\ = Backslash, \n \r \t = Steuerzeichen.
-- Zuerst an "\\" teilen, dann in jedem Stueck \n/\r/\t aufloesen, mit "\" wieder zusammensetzen.
CREATE FUNCTION pg_temp.fz_copy_feld(t text) RETURNS text LANGUAGE sql IMMUTABLE AS $f$
  SELECT CASE WHEN t = '\N' THEN NULL ELSE
    array_to_string(ARRAY(
      SELECT replace(replace(replace(u.teil, '\n', E'\n'), '\r', E'\r'), '\t', E'\t')
        FROM unnest(string_to_array(t, '\\')) WITH ORDINALITY AS u(teil, nr) ORDER BY u.nr), '\')
  END
$f$;

CREATE TEMP TABLE _fz_restore_zeilen (id_erwartet text PRIMARY KEY, obj jsonb NOT NULL) ON COMMIT DROP;

DO $$
DECLARE
  q record; v_spalten text[]; v_felder text[]; v_obj jsonb; v_tab text[]; v_fehlt text[]; v_fremd text[];
  v_neu constant text[] := ARRAY['archiviert_am', 'archiviert_von'];  -- erst seit v1059, im Backup nicht vorhanden
BEGIN
  SELECT array_agg(column_name::text ORDER BY ordinal_position) INTO v_tab
    FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'fahrzeuge';
  FOR q IN SELECT * FROM _fz_restore_quelle ORDER BY id_erwartet LOOP
    IF coalesce(q.kopf, '') LIKE '%<AUS_BACKUP%' OR coalesce(q.zeile, '') LIKE '%<AUS_BACKUP%' THEN
      RAISE EXCEPTION '%: Platzhalter <AUS_BACKUP...> noch nicht ersetzt - Abschnitt 1 ausfuellen', q.id_erwartet;
    END IF;
    IF q.obj IS NOT NULL AND q.zeile IS NOT NULL THEN
      RAISE EXCEPTION '%: bitte NUR eine Quelle (Backup-Zeile ODER Geraete-JSON)', q.id_erwartet;
    END IF;
    IF q.obj IS NOT NULL THEN
      IF jsonb_typeof(q.obj) <> 'object' THEN RAISE EXCEPTION '%: json ist kein Objekt', q.id_erwartet; END IF;
      -- nur echte Spalten uebernehmen (App-Felder wie kmStand/tankLog werden ignoriert)
      SELECT coalesce(jsonb_object_agg(k, q.obj -> k), '{}'::jsonb) INTO v_obj
        FROM unnest(v_tab) AS k WHERE q.obj ? k;
    ELSE
      IF q.kopf IS NULL OR q.zeile IS NULL THEN RAISE EXCEPTION '%: Quelle fehlt (kopf/zeile oder obj)', q.id_erwartet; END IF;
      IF q.kopf !~* '^\s*COPY\s+public\.fahrzeuge\s*\(' THEN
        RAISE EXCEPTION '%: kopf ist nicht die Zeile "COPY public.fahrzeuge (...)"', q.id_erwartet; END IF;
      SELECT array_agg(trim(BOTH '"' FROM trim(s)) ORDER BY nr) INTO v_spalten
        FROM unnest(string_to_array(substring(q.kopf FROM '\(([^)]*)\)'), ',')) WITH ORDINALITY AS x(s, nr);
      v_felder := string_to_array(btrim(q.zeile, E'\r\n'), E'\t');
      IF array_length(v_felder, 1) IS DISTINCT FROM array_length(v_spalten, 1) THEN
        RAISE EXCEPTION '%: % Felder, aber % Spalten im Kopf - Tabulatoren beim Kopieren verloren?',
          q.id_erwartet, array_length(v_felder, 1), array_length(v_spalten, 1);
      END IF;
      SELECT jsonb_object_agg(v_spalten[i], to_jsonb(pg_temp.fz_copy_feld(v_felder[i]))) INTO v_obj
        FROM generate_subscripts(v_spalten, 1) AS i;
      SELECT array_agg(s) INTO v_fremd FROM unnest(v_spalten) AS s WHERE NOT (s = ANY (v_tab));
      IF v_fremd IS NOT NULL THEN
        RAISE EXCEPTION '%: Spalten im Backup, die es nicht mehr gibt: % - Schema hat sich geaendert, bitte melden', q.id_erwartet, v_fremd;
      END IF;
    END IF;
    -- Pruefungen gemeinsam fuer A und B
    IF v_obj ->> 'id' IS DISTINCT FROM q.id_erwartet THEN
      RAISE EXCEPTION 'Quelle fuer % liefert id=% - falsche Zeile kopiert', q.id_erwartet, v_obj ->> 'id';
    END IF;
    IF upper(replace(replace(coalesce(v_obj ->> 'kennzeichen', ''), ' ', ''), '-', ''))
       IS DISTINCT FROM upper(replace(replace(q.kz_erwartet, ' ', ''), '-', '')) THEN
      RAISE EXCEPTION 'Quelle fuer % hat Kennzeichen "%" statt % - bitte pruefen', q.id_erwartet, v_obj ->> 'kennzeichen', q.kz_erwartet;
    END IF;
    SELECT array_agg(c) INTO v_fehlt FROM unnest(v_tab) AS c WHERE NOT (v_obj ? c) AND NOT (c = ANY (v_neu));
    IF v_fehlt IS NOT NULL THEN
      -- kein Auffuellen mit Defaults: ein fehlender Wert wuerde erfunden
      RAISE EXCEPTION '%: in der Quelle fehlen Spalten % - nichts eingefuegt', q.id_erwartet, v_fehlt;
    END IF;
    INSERT INTO _fz_restore_zeilen VALUES (q.id_erwartet, v_obj);
    RAISE NOTICE 'GEPARST %: kennzeichen=% marke=% modell=% km_stand=% pickerl=% tracker_imei=% updated_at=% | tank_log % Zeichen, serviceheft % Zeichen',
      q.id_erwartet, v_obj ->> 'kennzeichen', v_obj ->> 'marke', v_obj ->> 'modell', v_obj ->> 'km_stand',
      v_obj ->> 'pickerl', v_obj ->> 'tracker_imei', v_obj ->> 'updated_at',
      length(coalesce(v_obj ->> 'tank_log', '')), length(coalesce(v_obj ->> 'serviceheft', ''));
  END LOOP;
  IF (SELECT count(*) FROM _fz_restore_zeilen) <> 2 THEN RAISE EXCEPTION 'erwartet 2 Zeilen (fz3, fz6)'; END IF;
END $$;

-- 3. INSERT (nur die zwei geprueften Zeilen; Werte 1:1 aus der Quelle, Typumwandlung durch Postgres)
INSERT INTO public.fahrzeuge
SELECT (jsonb_populate_record(NULL::public.fahrzeuge, z.obj)).*
  FROM _fz_restore_zeilen z
 ORDER BY z.id_erwartet;

-- 4. KIND-ZEILEN: nichts wiederherzustellen. Es gibt keinen Fremdschluessel und damit kein CASCADE auf fahrzeuge;
--    fz_positions/fz_latest/fz_fahrten von fz3 sind nie geloescht worden und zeigen ab jetzt wieder auf eine Zeile.

-- 5. NACHHER
DO $$
DECLARE v_n int; r record;
BEGIN
  SELECT count(*) INTO v_n FROM public.fahrzeuge;
  FOR r IN SELECT id, kennzeichen, status, km_stand, updated_at FROM public.fahrzeuge WHERE id IN ('fz3', 'fz6') ORDER BY id LOOP
    RAISE NOTICE 'NACHHER Zeile: % % status=% km=% updated_at=%', r.id, r.kennzeichen, r.status, r.km_stand, r.updated_at;
  END LOOP;
  IF (SELECT count(*) FROM public.fahrzeuge WHERE id IN ('fz3', 'fz6')) <> 2 THEN RAISE EXCEPTION 'NACHHER: fz3/fz6 nicht beide da'; END IF;
  RAISE NOTICE 'NACHHER: fahrzeuge=% (erwartet 21, wenn seit dem Vorfall nichts angelegt/geloescht wurde); fz3 haengt an: fz_positions=%, fz_latest=%, fz_fahrten=%',
    v_n, (SELECT count(*) FROM public.fz_positions WHERE fahrzeug_id = 'fz3'),
         (SELECT count(*) FROM public.fz_latest WHERE fahrzeug_id = 'fz3'),
         (SELECT count(*) FROM public.fz_fahrten WHERE fahrzeug_id = 'fz3');
END $$;

DROP FUNCTION pg_temp.fz_copy_feld(text);

COMMIT;

-- ── PROBE (Variante zum Abschreiben, falls lieber getrennt) ──────────────────────────
-- BEGIN;
--   ... Abschnitte 0 bis 5 wie oben ...
-- ROLLBACK;
-- danach:  select count(*) from public.fahrzeuge where id in ('fz3','fz6');   -- muss 0 sein
--
-- NACH DEM COMMIT: App auf einem Geraet neu laden -> beide Fahrzeuge erscheinen wieder (Liste, Flotte-Karte fz3).
