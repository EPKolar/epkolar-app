# -*- coding: utf-8 -*-
"""Baut sql/DISPO_PLANUNG_v1_PROBE.sql aus dem ENTWURF (DDL woertlich eingebettet, nie abgeschrieben).

Aufruf:  python sql/_dispo_planung_probe_bauen.py
Der Kopf der erzeugten Datei traegt die Ergebniszeile des letzten Laufs (ERGEBNIS unten von Hand nachtragen).
"""
import io
import os

HIER = os.path.dirname(os.path.abspath(__file__))
ENTWURF = os.path.join(HIER, "DISPO_PLANUNG_v1_ENTWURF.sql")
PROBE = os.path.join(HIER, "DISPO_PLANUNG_v1_PROBE.sql")

ERGEBNIS = """--   GELAUFEN 24.11.2026 auf Prod (execute_sql, zurueckgerollt):
--   import [S075430] termin=2099-02-02 planung=2099-03-03/07:15/03:00/w1 aktualisiert=1
--   monteur [mpv7wxngtat6] planen=42501 leeren=42501 normal=OK(1) unveraendert=OK(1)
--   helfer KEIN-TESTFALL (kein Benutzer mit Rolle helfer und Login)
--   techniker [mu3zg26dyesc] planen=42501 leeren=42501 normal=OK(1) unveraendert=OK(1)
--   projektleiter/buero/admin: planen=OK(1) leeren=OK(1) normal=OK(1) unveraendert=OK(1)
--   nojwt planen=OK(1); service_role planen=OK(1)
--   Nachmessung: 0 dispo-Spalten, nur trg_updated_at_arbeitsscheine, Funktion NULL, 0 Constraints,
--   S075430 termin_bestaetigt unveraendert (leer), 0 Probe-Reste in notizen."""

KOPF = """-- DISPO PLANUNG v1 - PROBE (rollt IMMER zurueck)
-- EIN DO-Block = EINE Transaktion: wendet den ENTWURF an (DDL-Text verbatim aus DISPO_PLANUNG_v1_ENTWURF.sql,
-- per sql/_dispo_planung_probe_bauen.py eingebettet), prueft
--   (1) den OFFA-Abgleich juprowa_apply_worksheets: ein Schein mit Planung bekommt aus OFFA einen neuen Termin -
--       der Termin aendert sich, die Planungsfelder bleiben,
--   (2) je Rolle (monteur, helfer, techniker, projektleiter, buero, admin) + no-JWT + service_role:
--       planen / leeren / normal / unveraendert,
-- und endet mit RAISE EXCEPTION -> alles (Spalten, Trigger, Funktion, Testschreibvorgaenge) wird verworfen.
-- Jeder Einzelfall laeuft in einem eigenen Unterblock (Savepoint).
-- Erwartet:
--   import: termin=2099-02-02 planung=2099-03-03/07:15/03:00/<monteur> (unveraendert)
--   monteur/helfer/techniker: planen=42501 leeren=42501 normal=OK(1) unveraendert=OK(1)
--   projektleiter/buero/admin: alle OK(1); nojwt planen=OK(1); service_role planen=OK(1)
-- Danach messen: keine dispo-Spalte, nur trg_updated_at_arbeitsscheine, to_regprocedure('public.as_dispo_planung_guard()') NULL.
-- ERGEBNIS:
"""

RUMPF = r"""DO $probe$
DECLARE
  r_role text;
  v_uid uuid;
  v_as text;
  v_mon text;
  v_other text;
  v_n int;
  v_res text := '';
  v_case text;
  v_sql text;
  v_imp text; v_imp_nr text; v_raw jsonb; v_r jsonb;
  v_t text; v_d text; v_z text; v_dau text; v_m text;
BEGIN
  IF EXISTS (SELECT 1 FROM pg_trigger WHERE tgrelid='public.arbeitsscheine'::regclass AND tgname='trg_as_dispo_planung_guard') THEN
    RAISE EXCEPTION 'PROBE-ABBRUCH: trg_as_dispo_planung_guard existiert bereits';
  END IF;
  IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='arbeitsscheine' AND column_name='dispo_datum') THEN
    RAISE EXCEPTION 'PROBE-ABBRUCH: dispo_datum existiert bereits';
  END IF;

  -- ENTWURF anwenden (verbatim)
  EXECUTE $ddl$__DDL__$ddl$;

  -- (1) OFFA-Abgleich laesst die Planung stehen
  PERFORM set_config('request.jwt.claims', '{}', true);
  SELECT a.id, a.nummer, a.juprowa_raw INTO v_imp, v_imp_nr, v_raw
    FROM public.arbeitsscheine a
   WHERE a.juprowa_raw IS NOT NULL AND upper(coalesce(a.juprowa_raw->>'AK_SCHEINNR','')) = upper(coalesce(a.nummer,''))
     AND NOT coalesce(a.push_pending, false) AND coalesce(a.monteur,'') <> ''
   ORDER BY a.updated_at DESC LIMIT 1;
  IF v_imp IS NULL THEN
    v_res := 'import KEIN-TESTFALL | ';
  ELSE
    SELECT a.monteur INTO v_m FROM public.arbeitsscheine a WHERE a.id = v_imp;
    UPDATE public.arbeitsscheine SET dispo_datum = '2099-03-03', dispo_zeit = '07:15', dispo_dauer = '03:00', dispo_monteur = v_m WHERE id = v_imp;
    v_raw := jsonb_set(v_raw, '{AK_TERMIN}', to_jsonb('2099-02-02 00:00:00'::text), true);
    v_r := public.juprowa_apply_worksheets(jsonb_build_array(v_raw), false, false);
    SELECT termin_bestaetigt, dispo_datum, dispo_zeit, dispo_dauer, dispo_monteur INTO v_t, v_d, v_z, v_dau, v_m
      FROM public.arbeitsscheine WHERE id = v_imp;
    v_res := v_res || 'import [' || v_imp_nr || '] termin=' || coalesce(v_t,'-') || ' planung=' || coalesce(v_d,'-') || '/' || coalesce(v_z,'-')
      || '/' || coalesce(v_dau,'-') || '/' || coalesce(v_m,'-') || ' aktualisiert=' || coalesce(v_r->>'aktualisiert', v_r->>'error', '?') || ' | ';
  END IF;

  -- (2) Rollen
  FOREACH r_role IN ARRAY ARRAY['monteur','helfer','techniker','projektleiter','buero','admin','nojwt','service_role'] LOOP
    v_uid := NULL; v_as := NULL; v_mon := NULL; v_other := NULL;
    RESET ROLE;
    PERFORM set_config('request.jwt.claims', '{}', true);
    IF r_role IN ('monteur','helfer','techniker') THEN
      SELECT u.auth_user_id, a.id, a.monteur INTO v_uid, v_as, v_mon
        FROM public.users u JOIN public.arbeitsscheine a ON a.monteur = u.monteur_id
       WHERE u.role = r_role AND u.auth_user_id IS NOT NULL AND coalesce(a.scheinstatus,'') <> 'storniert'
       ORDER BY (a.scheinstatus IN ('aufgenommen','freigegeben','in_bearbeitung','aufgeschoben')) DESC, a.updated_at DESC
       LIMIT 1;
    ELSE
      IF r_role IN ('projektleiter','buero','admin') THEN
        SELECT u.auth_user_id INTO v_uid FROM public.users u
         WHERE u.role = r_role AND u.auth_user_id IS NOT NULL ORDER BY u.auth_user_id LIMIT 1;
      END IF;
      SELECT a.id, a.monteur INTO v_as, v_mon FROM public.arbeitsscheine a
       WHERE coalesce(a.scheinstatus,'') <> 'storniert' AND coalesce(a.monteur,'') <> ''
       ORDER BY a.updated_at DESC LIMIT 1;
    END IF;
    IF v_as IS NULL OR (r_role NOT IN ('nojwt','service_role') AND v_uid IS NULL) THEN
      v_res := v_res || r_role || ' KEIN-TESTFALL | ';
      CONTINUE;
    END IF;
    SELECT x.m INTO v_other FROM (SELECT DISTINCT a.monteur AS m FROM public.arbeitsscheine a
      WHERE coalesce(a.monteur,'') <> '' AND a.monteur IS DISTINCT FROM v_mon) x ORDER BY x.m LIMIT 1;
    v_res := v_res || r_role || ' [' || v_as || ']';

    FOREACH v_case IN ARRAY ARRAY['planen','leeren','normal','unveraendert'] LOOP
      IF r_role IN ('nojwt','service_role') AND v_case <> 'planen' THEN CONTINUE; END IF;
      v_sql := CASE v_case
        WHEN 'planen'       THEN 'UPDATE public.arbeitsscheine SET dispo_datum = ''2099-01-01'', dispo_zeit = ''08:00'', dispo_dauer = ''02:00'', dispo_monteur = $2 WHERE id = $1'
        WHEN 'leeren'       THEN 'UPDATE public.arbeitsscheine SET dispo_datum = NULL, dispo_zeit = NULL, dispo_dauer = NULL, dispo_monteur = NULL WHERE id = $1'
        WHEN 'normal'       THEN 'UPDATE public.arbeitsscheine SET notizen = coalesce(notizen,'''') || '' [probe]'' WHERE id = $1'
        WHEN 'unveraendert' THEN 'UPDATE public.arbeitsscheine SET dispo_datum = dispo_datum, dispo_zeit = dispo_zeit, dispo_dauer = dispo_dauer, dispo_monteur = dispo_monteur WHERE id = $1'
      END;
      BEGIN
        IF v_case = 'leeren' THEN
          -- Vorbedingung als Eigentuemer: eine Planung liegt vor
          UPDATE public.arbeitsscheine SET dispo_datum = '2099-05-05', dispo_zeit = '09:00' WHERE id = v_as;
        END IF;
        IF r_role = 'nojwt' THEN
          PERFORM set_config('request.jwt.claims', '{}', true);
        ELSIF r_role = 'service_role' THEN
          PERFORM set_config('request.jwt.claims', '{"role":"service_role"}', true);
          SET LOCAL ROLE service_role;
        ELSE
          PERFORM set_config('request.jwt.claims', json_build_object('sub', v_uid, 'role', 'authenticated')::text, true);
          SET LOCAL ROLE authenticated;
        END IF;
        EXECUTE v_sql USING v_as, coalesce(v_other, v_mon);
        GET DIAGNOSTICS v_n = ROW_COUNT;
        RAISE EXCEPTION USING ERRCODE = 'P0001', MESSAGE = '__OK__' || v_n;
      EXCEPTION WHEN others THEN
        IF SQLERRM LIKE '\_\_OK\_\_%' THEN
          v_res := v_res || ' ' || v_case || '=OK(' || substr(SQLERRM, 7) || ')';
        ELSE
          v_res := v_res || ' ' || v_case || '=' || SQLSTATE || '(' || left(SQLERRM, 70) || ')';
        END IF;
      END;
      RESET ROLE;
      PERFORM set_config('request.jwt.claims', '{}', true);
    END LOOP;
    v_res := v_res || ' | ';
  END LOOP;

  RAISE EXCEPTION 'PROBE-ERGEBNIS %', v_res;
END
$probe$;
"""


NACH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "DISPO_PLANUNG_v1_NACHMESSUNG.sql")


def main():
    ddl =io.open(ENTWURF, encoding="utf-8").read().replace("\r\n", "\n")
    # nur der ausfuehrbare Teil ab dem ersten ALTER TABLE
    i = ddl.index("ALTER TABLE public.arbeitsscheine\n")
    ddl = ddl[i:].rstrip() + "\n"
    assert "$ddl$" not in ddl
    io.open(PROBE, "w", encoding="utf-8", newline="\n").write(KOPF + ERGEBNIS + "\n" + RUMPF.replace("__DDL__", ddl))
    print("geschrieben:", PROBE)
    # GF 24.11.: Nachmessung NACH dem Einspielen = dieselben Faelle gegen das eingespielte Modell (ohne DDL); endet mit RAISE,
    # damit die Testschreibvorgaenge verworfen werden.
    r = RUMPF
    for a, b in (("  IF EXISTS (SELECT 1 FROM pg_trigger", "  IF NOT EXISTS (SELECT 1 FROM pg_trigger"),
                 ("  IF EXISTS (SELECT 1 FROM information_schema.columns", "  IF NOT EXISTS (SELECT 1 FROM information_schema.columns"),
                 ("existiert bereits", "fehlt (Entwurf nicht eingespielt)"),
                 ("  EXECUTE $ddl$__DDL__$ddl$;", "  -- Nachmessung: kein DDL, Modell ist eingespielt")):
        assert a in r, a
        r = r.replace(a, b)
    kopf = ("-- DISPO PLANUNG v1 - NACHMESSUNG nach dem Einspielen (GENERIERT von sql/_dispo_planung_probe_bauen.py).\n"
            "-- Gleiche Faelle wie die PROBE gegen das eingespielte Modell; endet mit RAISE -> Testschreibvorgaenge werden verworfen.\n")
    io.open(NACH, "w", encoding="utf-8", newline="\n").write(kopf + r)
    print("geschrieben:", NACH)


if __name__ == "__main__":
    main()
