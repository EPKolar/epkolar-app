-- RPC juprowa_fetch_kunden: Pull Juprowa ServicePad KundeList -> Upsert in public.kunden.
-- Angewandt via Supabase MCP apply_migration (create_juprowa_fetch_kunden_rpc) 2026-06-30.
-- HARTE GRENZE: ausschliesslich GET gegen Juprowa (kein Write/Push). Upsert nur in UNSERE kunden-Tabelle.
-- KRITISCH: CURLOPT_TIMEOUT_MS=28000 (Default 5s reicht fuer 7,6 MB KundeList NICHT — verifiziert).
-- Idempotent: dedup auf kunde_nr (latest LAST_MODIFIED), ON CONFLICT (kunde_nr) DO UPDATE.
-- Erster Lauf 2026-06-30: source_count 6458 -> imported 6457 (1 doppelte KU_NUMMER dedupliziert).
CREATE OR REPLACE FUNCTION public.juprowa_fetch_kunden()
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, extensions
AS $function$
DECLARE
  cfg        juprowa_config%ROWTYPE;
  api_url    text;
  resp       extensions.http_response;
  data       jsonb;
  n_before   int;
  n_after    int;
  n_src      int;
BEGIN
  -- Eingeloggte Nutzer muessen Staff sein; direkter Service-Zugriff (auth.uid() null) erlaubt.
  IF auth.uid() IS NOT NULL AND NOT is_staff() THEN
    RETURN jsonb_build_object('error','forbidden');
  END IF;

  SELECT * INTO cfg FROM juprowa_config WHERE id = 'default';
  IF NOT FOUND THEN RETURN jsonb_build_object('error','Juprowa-Konfiguration nicht gefunden'); END IF;
  IF NOT cfg.sync_enabled THEN RETURN jsonb_build_object('error','Juprowa-Sync ist deaktiviert'); END IF;

  PERFORM extensions.http_set_curlopt('CURLOPT_TIMEOUT_MS','28000');

  api_url := 'https://services.juprowa.net/Cloud/WebService/v6.0/jsondata.php'
    || '?UID=' || cfg.uid
    || '&PASSPORT=' || cfg.passport
    || '&type=KundeList'
    || '&ts=' || extract(epoch from now())::bigint::text;

  BEGIN
    SELECT * INTO resp FROM extensions.http_get(api_url);
  EXCEPTION WHEN OTHERS THEN
    RETURN jsonb_build_object('error','HTTP-Fehler: ' || SQLERRM);
  END;

  IF resp.status <> 200 THEN
    RETURN jsonb_build_object('error','Juprowa API Status ' || resp.status,
                              'passport_expired', resp.status IN (401,403));
  END IF;

  BEGIN
    data := resp.content::jsonb;
  EXCEPTION WHEN OTHERS THEN
    RETURN jsonb_build_object('error','JSON-Parse-Fehler: ' || SQLERRM);
  END;

  SELECT count(*) INTO n_before FROM kunden;
  SELECT count(*) INTO n_src    FROM jsonb_each(data);

  WITH src AS (
    SELECT key AS juprowa_id, value AS rec FROM jsonb_each(data)
  ),
  mapped AS (
    SELECT
      rec->'STAMM'->>'KU_NUMMER'                          AS kunde_nr,
      juprowa_id,
      rec->'STAMM'->>'KU_NAME'                            AS name,
      rec->'STAMM'->>'KU_STREET'                          AS strasse,
      rec->'STAMM'->>'KU_ZIP'                             AS plz,
      rec->'STAMM'->>'KU_CITY'                            AS ort,
      rec->'STAMM'->>'KU_COUNTRY'                         AS land,
      rec->'STAMM'->>'KU_MATCH'                           AS matchcode,
      rec->'STAMM'->>'KU_TITEL'                           AS titel,
      (rec->'STAMM'->>'KU_GESPERRT') = '1'                AS gesperrt,
      nullif(rec->'CONTACTS'->0->>'KK_EMAIL','')          AS email,
      nullif(rec->>'PHONENUMBERS','')                     AS tel,
      rec                                                 AS juprowa_raw,
      nullif(rec->>'LAST_MODIFIED','')::timestamptz       AS last_modified
    FROM src
    WHERE coalesce(rec->'STAMM'->>'KU_NUMMER','') <> ''
  ),
  dedup AS (
    SELECT DISTINCT ON (kunde_nr) *
    FROM mapped
    ORDER BY kunde_nr, last_modified DESC NULLS LAST
  )
  INSERT INTO kunden AS k
    (kunde_nr,juprowa_id,name,strasse,plz,ort,land,matchcode,titel,gesperrt,email,tel,juprowa_raw,last_modified,synced_at,updated_at)
  SELECT kunde_nr,juprowa_id,name,strasse,plz,ort,land,matchcode,titel,gesperrt,email,tel,juprowa_raw,last_modified,now(),now()
  FROM dedup
  ON CONFLICT (kunde_nr) DO UPDATE SET
    juprowa_id=excluded.juprowa_id, name=excluded.name, strasse=excluded.strasse, plz=excluded.plz, ort=excluded.ort,
    land=excluded.land, matchcode=excluded.matchcode, titel=excluded.titel, gesperrt=excluded.gesperrt,
    email=excluded.email, tel=excluded.tel, juprowa_raw=excluded.juprowa_raw, last_modified=excluded.last_modified,
    synced_at=now(), updated_at=now();

  SELECT count(*) INTO n_after FROM kunden;
  RETURN jsonb_build_object('ok', true, 'source_count', n_src, 'imported', n_after, 'added', n_after - n_before);
END
$function$;

REVOKE EXECUTE ON FUNCTION public.juprowa_fetch_kunden() FROM anon, public;
GRANT  EXECUTE ON FUNCTION public.juprowa_fetch_kunden() TO authenticated, service_role;
