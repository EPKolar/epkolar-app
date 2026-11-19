-- IDEMPOTENT
-- =====================================================================================
-- TANKLOG_ATOMAR_v1051_ENTWURF.sql  —  Tankbuch-Schreibwege atomar am Server (kein Lost-Update mehr)
--
-- STATUS: ENTWURF — NICHT APPLIZIERT. Pruefung durch Chat-Claude, Einspielen nur durch Sebastian ueber das Tor.
-- Zweig feature/tanklog-atomar (Basis release/v1050). Die App (v3.9.1051) erkennt selbst, ob die Funktionen da sind:
-- Antwortet /rpc/fz_tanklog_* mit 404, nimmt sie bis zum Neuladen den bisherigen Weg (ganzes Array bzw. Lesen-Aendern-Schreiben).
-- Reihenfolge daher beliebig; empfohlen: erst App ausliefern, dann dieses SQL.
--
-- PROBLEM (gemessen im Code, index.html release/v1050):
--   fahrzeuge.tank_log ist TEXT mit einem JSON-Array. Die Schreibwege schicken das GANZE Array aus dem lokalen Stand
--   (Tank-Dialog addTank, Sammel-Tanken "entfernen") oder lesen-aendern-schreiben im Client (QR-/Sammel-Tanken ueber
--   tankLog_add, Buero-Kontrolle _tankMark, Buero-Korrektur _tankEditSave). Hat ein anderes Geraet inzwischen eine
--   Tankung eingetragen, wird sie ueberschrieben (Last-Write-Wins) bzw. im Lese-Schreib-Fenster verloren.
--
-- LOESUNG: drei SECURITY-DEFINER-Funktionen, jede sperrt die Fahrzeugzeile (SELECT ... FOR UPDATE) und aendert nur
--   EINEN Eintrag (per id):
--     fz_tanklog_add(p_fahrzeug_id, p_eintrag, p_km, p_km_log_id)  haengt an, wenn die id noch nicht da ist (Wiederholung
--                                                                   = kein Duplikat); km_stand nur ERHOEHEN (max);
--                                                                   km_log-Zeile id 'km_'||eintrag.id idempotent anhaengen.
--     fz_tanklog_del(p_fahrzeug_id, p_eintrag_id)                   entfernt per id (Wiederholung = nichts mehr da = ok).
--     fz_tanklog_set(p_fahrzeug_id, p_eintrag_id, p_patch)          Buero: kontrolliert/_von/_am bzw. datum/liter/preis/km
--                                                                   eines Eintrags; bei datum/km wird km_stand wie v3.9.555
--                                                                   neu bestimmt (neuester Beleg: datum desc, km desc).
--
-- BERECHTIGUNG (spiegelt die LIVE-Policy, Stand 19.11.2026 laut sql/FZ_FINANZEN_staff_only_v1049.sql):
--   fahrzeuge_update_office_or_driver  FOR UPDATE  USING/CHECK (is_hr() OR fahrer = current_monteur_id())
--   -> in jeder Funktion: erlaubt genau dann, wenn public.is_hr() OR (fahrer IS NOT NULL AND fahrer = public.current_monteur_id()).
--   Abgewiesen wird NICHT mit Fehler, sondern mit {"ok":false,"grund":"nicht_berechtigt"} — die App behandelt das wie den
--   heutigen "0 Zeilen"-Fall (Toast "Fahrzeug-Aenderung NICHT gespeichert", Auftrag gilt als erledigt), also exakt wie bisher.
--   OFFENE FRAGE an Sebastian: Heute kann ein Monteur per QR-Schnelltanken nur SEIN Fahrzeug betanken (fremdes Fahrzeug =
--   RLS weist still ab, Toast). Ist das gewollt (z. B. Kollege tankt den Bus des Kollegen)? Diese Datei aendert daran NICHTS.
--   OFFENE FRAGE 2: Der Fahrer darf heute (RLS) auch "kontrolliert" an seinen eigenen Belegen setzen (Policy kennt keine
--   Spalten). fz_tanklog_set spiegelt das unveraendert; eine Einschraenkung auf is_hr() waere eine bewusste Verschaerfung.
--
-- KEINE DATEIEN (Dauerregel 18.11.): p_eintrag / p_patch mit 'data:' oder ';base64,' -> RAISE 'files_not_allowed' (HTTP 400).
--   Alte Base64-Belege, die noch IN tank_log stehen (Migration offen), bleiben unangetastet in der Zeile; sie gehen nie
--   ueber die Leitung (die Funktionen geben tank_log NICHT zurueck).
--
-- TEXT <-> JSONB: tank_log/km_log NULL oder '' -> '[]'. Ungueltiges JSON oder kein Array -> RAISE 'tank_log_korrupt' /
--   'km_log_korrupt' (der alte Client-Weg startete dann mit [] neu = Datenverlust; der Server verweigert lieber).
--   Hinweis: das Zurueckschreiben ueber jsonb::text normalisiert die Formatierung (Leerzeichen, Schluesselreihenfolge).
--   JSON.parse in der App ist davon unberuehrt; der Inhalt bleibt gleich.
--
-- GRANTS: EXECUTE nur fuer authenticated; REVOKE von PUBLIC und anon (Supabase vergibt sonst Default-EXECUTE an anon).
-- updated_at wird wie in den App-PATCHes auf now() gesetzt.
-- =====================================================================================


-- 0. VORPRUEFUNG der Spaltentypen (bricht ab, wenn die Annahmen nicht stimmen — dann NICHT weiter, sondern melden)
do $$
declare v_t text;
begin
  select data_type into v_t from information_schema.columns
   where table_schema='public' and table_name='fahrzeuge' and column_name='tank_log';
  if v_t is distinct from 'text' then raise exception 'Vorpruefung: fahrzeuge.tank_log ist %, erwartet text', v_t; end if;
  select data_type into v_t from information_schema.columns
   where table_schema='public' and table_name='fahrzeuge' and column_name='km_log';
  if v_t is distinct from 'text' then raise exception 'Vorpruefung: fahrzeuge.km_log ist %, erwartet text', v_t; end if;
  select data_type into v_t from information_schema.columns
   where table_schema='public' and table_name='fahrzeuge' and column_name='km_stand';
  if v_t not in ('integer','bigint','numeric','smallint','double precision','real') or v_t is null then
    raise exception 'Vorpruefung: fahrzeuge.km_stand ist %, erwartet eine Zahl', v_t; end if;
  select data_type into v_t from information_schema.columns
   where table_schema='public' and table_name='fahrzeuge' and column_name='id';
  if v_t is distinct from 'text' then raise exception 'Vorpruefung: fahrzeuge.id ist %, erwartet text', v_t; end if;
  if to_regprocedure('public.is_hr()') is null or to_regprocedure('public.current_monteur_id()') is null then
    raise exception 'Vorpruefung: is_hr() oder current_monteur_id() fehlt'; end if;
end $$;


-- 1. Hilfsfunktion: TEXT-Spalte -> jsonb-Array (NULL/'' -> []), sonst Fehler statt stiller Neuanfang
create or replace function public._fz_json_array(p_text text, p_feld text)
returns jsonb
language plpgsql immutable
set search_path to 'public', 'pg_temp'
as $$
declare v jsonb;
begin
  if nullif(btrim(coalesce(p_text,'')),'') is null then return '[]'::jsonb; end if;
  begin
    v := p_text::jsonb;
  exception when others then
    raise exception '%_korrupt', p_feld using errcode = '22023';
  end;
  if jsonb_typeof(v) <> 'array' then raise exception '%_korrupt', p_feld using errcode = '22023'; end if;
  return v;
end $$;
revoke all on function public._fz_json_array(text, text) from public, anon, authenticated;


-- 2. Anhaengen (Tank-Dialog, QR-Schnelltanken, Sammel-Tanken)
create or replace function public.fz_tanklog_add(
  p_fahrzeug_id text, p_eintrag jsonb, p_km integer default null, p_km_log_id text default null
) returns jsonb
language plpgsql volatile security definer
set search_path to 'public', 'pg_temp'
as $$
declare
  v_fahrer text;
  v_tl     jsonb;
  v_kl     jsonb;
  v_id     text;
  v_kmid   text;
  v_neu    boolean := false;
  v_kmneu  boolean := false;
begin
  if p_eintrag is null or jsonb_typeof(p_eintrag) <> 'object' then raise exception 'eintrag_ungueltig' using errcode = '22023'; end if;
  v_id := nullif(btrim(coalesce(p_eintrag->>'id','')),'');
  if v_id is null or length(v_id) > 100 then raise exception 'eintrag_id_fehlt' using errcode = '22023'; end if;
  if position('data:' in p_eintrag::text) > 0 or position(';base64,' in p_eintrag::text) > 0 then
    raise exception 'files_not_allowed' using errcode = '22023';
  end if;
  if length(p_eintrag::text) > 4000 then raise exception 'eintrag_zu_gross' using errcode = '22023'; end if;

  select f.fahrer into v_fahrer from public.fahrzeuge f where f.id = p_fahrzeug_id for update;
  if not found then return jsonb_build_object('ok', false, 'grund', 'fahrzeug_fehlt'); end if;
  if not (public.is_hr() or (v_fahrer is not null and v_fahrer = public.current_monteur_id())) then
    return jsonb_build_object('ok', false, 'grund', 'nicht_berechtigt');
  end if;

  select public._fz_json_array(f.tank_log, 'tank_log'), public._fz_json_array(f.km_log, 'km_log')
    into v_tl, v_kl from public.fahrzeuge f where f.id = p_fahrzeug_id;

  -- idempotent: gleiche id schon da -> nicht nochmal anhaengen
  if not exists (select 1 from jsonb_array_elements(v_tl) e where e->>'id' = v_id) then
    v_tl := jsonb_build_array(p_eintrag) || v_tl;   -- vorne wie im lokalen Stand der App (neueste zuerst)
    v_neu := true;
  end if;

  if p_km is not null and p_km > 0 then
    v_kmid := coalesce(nullif(btrim(coalesce(p_km_log_id,'')),''), 'km_' || v_id);
    if not exists (select 1 from jsonb_array_elements(v_kl) e where e->>'id' = v_kmid) then
      v_kl := v_kl || jsonb_build_array(jsonb_build_object(
                'id', v_kmid, 'km', p_km,
                'date', to_char((now() at time zone 'Europe/Vienna')::date, 'YYYY-MM-DD')));
      v_kmneu := true;
    end if;
  end if;

  update public.fahrzeuge f set
    tank_log   = case when v_neu then v_tl::text else f.tank_log end,
    km_log     = case when v_kmneu then v_kl::text else f.km_log end,
    km_stand   = case when p_km is not null and p_km > 0 then greatest(coalesce(f.km_stand, 0), p_km) else f.km_stand end,  -- nur ERHOEHEN (v3.9.578)
    updated_at = now()
  where f.id = p_fahrzeug_id;

  return jsonb_build_object('ok', true, 'neu', v_neu, 'km_neu', v_kmneu);
end $$;


-- 3. Entfernen per id (Sammel-Tanken "entfernen")
create or replace function public.fz_tanklog_del(p_fahrzeug_id text, p_eintrag_id text)
returns jsonb
language plpgsql volatile security definer
set search_path to 'public', 'pg_temp'
as $$
declare
  v_fahrer text;
  v_tl     jsonb;
  v_neu    jsonb;
  v_n      integer;
begin
  if nullif(btrim(coalesce(p_eintrag_id,'')),'') is null then raise exception 'eintrag_id_fehlt' using errcode = '22023'; end if;

  select f.fahrer into v_fahrer from public.fahrzeuge f where f.id = p_fahrzeug_id for update;
  if not found then return jsonb_build_object('ok', false, 'grund', 'fahrzeug_fehlt'); end if;
  if not (public.is_hr() or (v_fahrer is not null and v_fahrer = public.current_monteur_id())) then
    return jsonb_build_object('ok', false, 'grund', 'nicht_berechtigt');
  end if;

  select public._fz_json_array(f.tank_log, 'tank_log') into v_tl from public.fahrzeuge f where f.id = p_fahrzeug_id;
  select coalesce(jsonb_agg(e order by o), '[]'::jsonb) into v_neu
    from jsonb_array_elements(v_tl) with ordinality as t(e, o)
   where e->>'id' is distinct from p_eintrag_id;
  v_n := jsonb_array_length(v_tl) - jsonb_array_length(v_neu);

  if v_n > 0 then
    update public.fahrzeuge f set tank_log = v_neu::text, updated_at = now() where f.id = p_fahrzeug_id;
  end if;
  return jsonb_build_object('ok', true, 'entfernt', v_n);   -- Wiederholung: entfernt = 0, trotzdem ok
end $$;


-- 4. Einen Eintrag aendern (Buero: Kontrolle markieren/zuruecksetzen, Werte korrigieren)
create or replace function public.fz_tanklog_set(p_fahrzeug_id text, p_eintrag_id text, p_patch jsonb)
returns jsonb
language plpgsql volatile security definer
set search_path to 'public', 'pg_temp'
as $$
declare
  v_fahrer text;
  v_tl     jsonb;
  v_neu    jsonb;
  v_patch  jsonb;
  v_found  boolean;
  v_km     numeric;
  v_ks     numeric := null;
begin
  if nullif(btrim(coalesce(p_eintrag_id,'')),'') is null then raise exception 'eintrag_id_fehlt' using errcode = '22023'; end if;
  if p_patch is null or jsonb_typeof(p_patch) <> 'object' then raise exception 'patch_ungueltig' using errcode = '22023'; end if;
  if position('data:' in p_patch::text) > 0 or position(';base64,' in p_patch::text) > 0 then
    raise exception 'files_not_allowed' using errcode = '22023';
  end if;
  -- nur diese Felder duerfen geaendert werden (genau die, die _tankMark / _tankEditSave heute schreiben)
  select coalesce(jsonb_object_agg(k, v), '{}'::jsonb) into v_patch
    from jsonb_each(p_patch) as x(k, v)
   where k in ('kontrolliert','kontrolliert_von','kontrolliert_am','datum','liter','preis','km');
  if v_patch = '{}'::jsonb then raise exception 'patch_leer' using errcode = '22023'; end if;

  select f.fahrer into v_fahrer from public.fahrzeuge f where f.id = p_fahrzeug_id for update;
  if not found then return jsonb_build_object('ok', false, 'grund', 'fahrzeug_fehlt'); end if;
  if not (public.is_hr() or (v_fahrer is not null and v_fahrer = public.current_monteur_id())) then
    return jsonb_build_object('ok', false, 'grund', 'nicht_berechtigt');
  end if;

  select public._fz_json_array(f.tank_log, 'tank_log') into v_tl from public.fahrzeuge f where f.id = p_fahrzeug_id;
  select exists (select 1 from jsonb_array_elements(v_tl) e where e->>'id' = p_eintrag_id) into v_found;
  if not v_found then return jsonb_build_object('ok', false, 'grund', 'eintrag_fehlt'); end if;

  select coalesce(jsonb_agg(case when e->>'id' = p_eintrag_id then e || v_patch else e end order by o), '[]'::jsonb)
    into v_neu
    from jsonb_array_elements(v_tl) with ordinality as t(e, o);

  -- v3.9.555: km-/Datumskorrektur zieht den Tacho mit — km des NEUESTEN Belegs (datum desc, km desc); km_log bleibt
  if v_patch ? 'km' or v_patch ? 'datum' then
    select (e->>'km')::numeric into v_ks
      from jsonb_array_elements(v_neu) e
     where jsonb_typeof(e) = 'object'
       and coalesce(e->>'km','') ~ '^\s*-?[0-9]+(\.[0-9]+)?\s*$'
     order by coalesce(e->>'datum','') collate "C" desc, (e->>'km')::numeric desc
     limit 1;
  end if;

  update public.fahrzeuge f set
    tank_log   = v_neu::text,
    km_stand   = case when v_ks is not null then v_ks else f.km_stand end,
    updated_at = now()
  where f.id = p_fahrzeug_id;

  return jsonb_build_object('ok', true, 'km_stand', v_ks);
end $$;


-- 5. Rechte: nur angemeldete Nutzer; anon und PUBLIC nichts
revoke all on function public.fz_tanklog_add(text, jsonb, integer, text) from public, anon;
revoke all on function public.fz_tanklog_del(text, text)                 from public, anon;
revoke all on function public.fz_tanklog_set(text, text, jsonb)          from public, anon;
grant execute on function public.fz_tanklog_add(text, jsonb, integer, text) to authenticated;
grant execute on function public.fz_tanklog_del(text, text)                 to authenticated;
grant execute on function public.fz_tanklog_set(text, text, jsonb)          to authenticated;

-- PostgREST-Schema neu laden, damit /rpc/fz_tanklog_* sofort erreichbar ist (sonst 404 bis zum naechsten Reload)
notify pgrst, 'reload schema';


-- =====================================================================================
-- NACHPRUEFUNG (nach dem Einspielen, nur lesen):
--   select p.proname, p.prosecdef, p.proconfig, pg_get_function_identity_arguments(p.oid) as args
--     from pg_proc p where p.pronamespace = 'public'::regnamespace and p.proname like 'fz_tanklog_%';
--     -- erwartet 3 Zeilen, prosecdef = true, proconfig = {search_path=public, pg_temp}
--   select routine_name, grantee, privilege_type from information_schema.routine_privileges
--    where routine_schema = 'public' and routine_name like 'fz_tanklog_%' order by 1, 2;
--     -- erwartet: authenticated (+ postgres/service_role als Eigentuemer/Superuser), KEIN anon, KEIN PUBLIC
--
-- PROBE (BEGIN ... ROLLBACK — aendert nichts dauerhaft). Platzhalter ersetzen:
--   <FZ>          eine echte fahrzeuge.id
--   <AUTH_BUERO>  auth.users.id eines Buero-/Admin-Nutzers
--   <AUTH_FAHRER> auth.users.id des Monteurs, dessen monteur_id = fahrzeuge.fahrer von <FZ>
--   <AUTH_FREMD>  auth.users.id eines Monteurs, der NICHT Fahrer von <FZ> ist
--
-- begin;
--   -- VORHER
--   select id, km_stand, jsonb_array_length(public._fz_json_array(tank_log,'tank_log')) as n_tank,
--          jsonb_array_length(public._fz_json_array(km_log,'km_log')) as n_km from public.fahrzeuge where id = '<FZ>';
--
--   -- (a) Buero haengt an; Wiederholung derselben id = kein Duplikat
--   set local role authenticated;
--   select set_config('request.jwt.claims', json_build_object('sub','<AUTH_BUERO>','role','authenticated')::text, true);
--   select public.fz_tanklog_add('<FZ>', '{"id":"__probe_t1","datum":"2026-11-19","liter":40,"preis":60,"km":999999,"foto":""}'::jsonb, 999999, null);
--     -- erwartet {"ok":true,"neu":true,"km_neu":true}
--   select public.fz_tanklog_add('<FZ>', '{"id":"__probe_t1","datum":"2026-11-19","liter":40,"preis":60,"km":999999,"foto":""}'::jsonb, 999999, null);
--     -- erwartet {"ok":true,"neu":false,"km_neu":false}
--   -- (b) Base64-Abweisung: siehe Schritt (g) ganz am Ende (ein Fehler bricht die Transaktion ab)
--   -- (c) Kontrolle setzen, Korrektur mit km-Neuberechnung
--   select public.fz_tanklog_set('<FZ>', '__probe_t1', '{"kontrolliert":true,"kontrolliert_von":"Probe","kontrolliert_am":"2026-11-19T10:00:00Z"}'::jsonb);
--     -- erwartet {"ok":true,"km_stand":null}
--   select public.fz_tanklog_set('<FZ>', '__probe_x', '{"kontrolliert":true}'::jsonb);   -- erwartet {"ok":false,"grund":"eintrag_fehlt"}
--   -- (d) Entfernen, Wiederholung
--   select public.fz_tanklog_del('<FZ>', '__probe_t1');   -- erwartet {"ok":true,"entfernt":1}
--   select public.fz_tanklog_del('<FZ>', '__probe_t1');   -- erwartet {"ok":true,"entfernt":0}
--   -- (e) Rollen-Probe: fremder Monteur wird abgewiesen, Fahrer darf
--   select set_config('request.jwt.claims', json_build_object('sub','<AUTH_FREMD>','role','authenticated')::text, true);
--   select public.fz_tanklog_add('<FZ>', '{"id":"__probe_t3","liter":1,"preis":1,"km":0}'::jsonb, null, null);
--     -- erwartet {"ok":false,"grund":"nicht_berechtigt"}
--   select set_config('request.jwt.claims', json_build_object('sub','<AUTH_FAHRER>','role','authenticated')::text, true);
--   select public.fz_tanklog_add('<FZ>', '{"id":"__probe_t3","liter":1,"preis":1,"km":0}'::jsonb, null, null);
--     -- erwartet {"ok":true,"neu":true,"km_neu":false}
--   -- (f) anon darf gar nicht
--   reset role; set local role anon;
--   select public.fz_tanklog_del('<FZ>', '__probe_t3');   -- erwartet ERROR permission denied for function fz_tanklog_del
--   reset role;
--   -- NACHHER (innerhalb der Transaktion): n_tank = vorher + 1 (__probe_t3), km_stand = max(vorher, 999999)
--   select id, km_stand, jsonb_array_length(public._fz_json_array(tank_log,'tank_log')) as n_tank from public.fahrzeuge where id = '<FZ>';
--   -- (g) Base64 wird abgewiesen (als LETZTER Schritt — der Fehler bricht die Transaktion ab)
--   set local role authenticated;
--   select set_config('request.jwt.claims', json_build_object('sub','<AUTH_BUERO>','role','authenticated')::text, true);
--   select public.fz_tanklog_add('<FZ>', '{"id":"__probe_t2","foto":"data:image/jpeg;base64,AAAA"}'::jsonb, null, null);
--     -- erwartet ERROR files_not_allowed
-- rollback;
--   -- nach ROLLBACK: dieselben Werte wie VORHER
-- =====================================================================================
