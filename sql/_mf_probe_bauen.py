# -*- coding: utf-8 -*-
"""Baut sql/MONATSFREIGABE_v1_PROBE.sql aus dem ENTWURF (woertlich) + Gegenmessung je Rolle.

Die Probe laeuft in EINER Transaktion und endet IMMER mit RAISE EXCEPTION (nichts bleibt).
Jede Zeile der Liste: (wer, name, art, sql, erwartet)
  wer      owner | mA | mB | buero | admin | tech | pl
  art      run  -> ergebnis 'ok<rowcount>' oder 'err'
           cnt  -> ergebnis 'n<count>'  (sql ist ein SELECT count(*) ...)
           own  -> als Eigentuemer ohne Pruefung (Vorbereitung)
  erwartet Muster fuer LIKE (z. B. 'err', 'ok1', 'n2')
Aufruf: python sql/_mf_probe_bauen.py
Hinweis: nach der Freigabe blockt beim Monteur schon die RLS (0 Zeilen, ok0); direktes DELETE auf storage.objects
verbietet Supabase selbst (err) - der Storage-API-Weg laeuft ueber die Policy epkolar_docs_delete (monatsfreigabe/ ausgenommen).
"""
import io, os

HIER = os.path.dirname(os.path.abspath(__file__))
ENTWURF = os.path.join(HIER, "MONATSFREIGABE_v1_ENTWURF.sql")
ZIEL = os.path.join(HIER, "MONATSFREIGABE_v1_PROBE.sql")
# GF 24.11.: Nachmessung nach dem Einspielen = dieselben Pruefschritte gegen das eingespielte Modell, OHNE Entwurf.
# Die Probezeilen (p_*, Periode 1999) werden am Ende trotzdem verworfen, damit keine Testdaten auf Prod bleiben.
ZIEL_NACH = os.path.join(HIER, "MONATSFREIGABE_v1_NACHMESSUNG.sql")
SCHEMA = [
    ("owner", "schema_spalten", "chk", "SELECT count(*) FROM information_schema.columns WHERE table_schema='public' AND table_name='finkzeit' AND column_name IN ('freigabe_bis','admin_freigabe_am','admin_freigabe_von','freigegeben_am','freigegeben_von','ohne_monteur','beanstandung','rueckgabe_grund','snapshot','signatur_pfad','pdf_pfad','admin_vermerk','frist_bei_admin_freigabe','freigabe_hash')", "n14"),
    ("owner", "schema_policies_finkzeit", "chk", "SELECT count(*) FROM pg_policies WHERE schemaname='public' AND tablename='finkzeit' AND policyname IN ('finkzeit_buero_admin','finkzeit_monteur_select','finkzeit_monteur_update')", "n3"),
    ("owner", "schema_policies_finkzeit_gesamt", "chk", "SELECT count(*) FROM pg_policies WHERE schemaname='public' AND tablename='finkzeit'", "n3"),
    ("owner", "schema_storage_regeln", "chk", "SELECT count(*) FROM pg_policies WHERE schemaname='storage' AND tablename='objects' AND policyname IN ('epkolar_docs_select','epkolar_docs_insert','epkolar_docs_update','epkolar_docs_delete','monatsfreigabe_monteur_insert')", "n5"),
    ("owner", "schema_trigger", "chk", "SELECT count(*) FROM pg_trigger WHERE tgname='zz_finkzeit_monatsfreigabe'", "n1"),
    ("owner", "schema_tabellen", "chk", "SELECT count(*) FROM information_schema.tables WHERE table_schema='public' AND table_name IN ('finkzeit_verlauf','monatsfreigabe_einstellungen')", "n2"),
    ("owner", "schema_rpc", "chk", "SELECT count(*) FROM pg_proc WHERE proname='monatsfreigabe_beanstanden'", "n1"),
]

NL = chr(10)

def q(s):
    return s.replace("'", "''")

FZ = "public.finkzeit"
SN = """'{"tage":[],"summe":{"min":0}}'::jsonb"""

SCHRITTE = [
    # Vorbereitung als Eigentuemer (Trigger laesst ohne JWT alles durch)
    ("owner", "prep", "own", "INSERT INTO %s(id,worker_id,period,jahr,monat,status,freigabe_bis,snapshot) VALUES ('p_a_zf',$A,'1999-01',1999,0,'zur_freigabe',$H+10,%s),('p_a_zf2',$A,'1999-02',1999,1,'zur_freigabe',$H+10,%s),('p_b_zf',$B,'1999-01',1999,0,'zur_freigabe',$H+10,%s),('p_a_ia',$A,'1999-03',1999,2,'in_arbeit',NULL,NULL),('p_a_zaf',$A,'1999-04',1999,3,'zur_admin_freigabe',$H+1,%s),('p_a_zaf2',$A,'1999-05',1999,4,'zur_admin_freigabe',$H+10,%s),('p_a_fg',$A,'1999-06',1999,5,'freigegeben',$H+10,%s),('p_b_ia',$B,'1999-07',1999,6,'in_arbeit',NULL,NULL)" % (FZ, SN, SN, SN, SN, SN, SN), ""),
    ("owner", "prep_sig", "own", "INSERT INTO storage.objects(bucket_id,name,owner) VALUES ('epkolar-docs','monatsfreigabe/'||$A||'/p_sig.png',$UA)", ""),
    ("owner", "prep_einst", "own", "UPDATE public.monatsfreigabe_einstellungen SET erinnerung_tage=3 WHERE id=1", ""),

    # Monteur A
    ("mA", "mA_sieht_eigene_ab_zur_freigabe", "cnt", "SELECT count(*) FROM %s WHERE id LIKE 'p\\_%%'" % FZ, "n3"),
    ("mA", "mA_sieht_nichts_vor_admin_freigabe", "cnt", "SELECT count(*) FROM %s WHERE id IN ('p_a_ia','p_a_zaf','p_a_zaf2')" % FZ, "n0"),
    ("mA", "mA_fremde_zeile_lesen", "cnt", "SELECT count(*) FROM %s WHERE id='p_b_zf'" % FZ, "n0"),
    ("mA", "mA_fremde_zeile_freigeben", "run", "UPDATE %s SET status='freigegeben',signatur_pfad='monatsfreigabe/'||$A||'/p_sig.png' WHERE id='p_b_zf'" % FZ, "ok0"),
    ("mA", "mA_freigabe_ohne_unterschrift", "run", "UPDATE %s SET status='freigegeben' WHERE id='p_a_zf'" % FZ, "err"),
    ("mA", "mA_freigabe_unterschrift_nicht_in_storage", "run", "UPDATE %s SET status='freigegeben',signatur_pfad='monatsfreigabe/'||$A||'/gibtsnicht.png' WHERE id='p_a_zf'" % FZ, "err"),
    ("mA", "mA_freigabe_fremder_unterschriftspfad", "run", "UPDATE %s SET status='freigegeben',signatur_pfad='monatsfreigabe/'||$B||'/p_sig.png' WHERE id='p_a_zf'" % FZ, "err"),
    ("mA", "mA_zahlen_aendern", "run", "UPDATE %s SET snapshot='{\"x\":1}'::jsonb WHERE id='p_a_zf'" % FZ, "err"),
    ("mA", "mA_frist_aendern", "run", "UPDATE %s SET freigabe_bis=$H+30 WHERE id='p_a_zf'" % FZ, "err"),
    ("mA", "mA_freigabe_vor_zur_freigabe", "run", "UPDATE %s SET status='freigegeben',signatur_pfad='monatsfreigabe/'||$A||'/p_sig.png' WHERE id='p_a_ia'" % FZ, "ok0"),
    ("mA", "mA_admin_uebergang", "run", "UPDATE %s SET status='zur_freigabe' WHERE id='p_a_zaf2'" % FZ, "ok0"),
    ("mA", "mA_beanstanden_direkt_update", "run", "UPDATE %s SET status='in_arbeit',beanstandung='Am 3. fehlt' WHERE id='p_a_zf2'" % FZ, "err"),
    ("mA", "mA_beanstanden_ohne_grund", "run", "SELECT public.monatsfreigabe_beanstanden('p_a_zf2',' ')", "err"),
    ("mA", "mA_beanstanden_fremde", "run", "SELECT public.monatsfreigabe_beanstanden('p_b_zf','Am 3. fehlt eine Stunde')", "err"),
    ("mA", "mA_beanstanden_mit_grund", "run", "SELECT public.monatsfreigabe_beanstanden('p_a_zf2','Am 3. fehlt eine Stunde')", "ok1"),
    ("owner", "pruef_beanstandet", "chk", "SELECT count(*) FROM %s WHERE id='p_a_zf2' AND status='in_arbeit' AND beanstandung='Am 3. fehlt eine Stunde'" % FZ, "n1"),
    ("mA", "mA_freigabe_faelscht_serverfeld", "run", "UPDATE %s SET status='freigegeben',signatur_pfad='monatsfreigabe/'||$A||'/p_sig.png',freigegeben_von='gefaelscht' WHERE id='p_a_zf'" % FZ, "err"),
    ("mA", "mA_freigabe_mit_unterschrift", "run", "UPDATE %s SET status='freigegeben',signatur_pfad='monatsfreigabe/'||$A||'/p_sig.png' WHERE id='p_a_zf'" % FZ, "ok1"),
    ("mA", "mA_aenderung_nach_freigabe", "run", "UPDATE %s SET beanstandung='doch nicht' WHERE id='p_a_zf'" % FZ, "ok0"),
    ("mA", "mA_pdf_pfad_nach_freigabe", "run", "UPDATE %s SET pdf_pfad='monatsfreigabe/'||$A||'/p_sig.png' WHERE id='p_a_zf'" % FZ, "ok0"),
    ("mA", "mA_status_zurueck_nach_freigabe", "run", "UPDATE %s SET status='zur_freigabe' WHERE id='p_a_fg'" % FZ, "ok0"),
    ("owner", "pruef_monteur_aenderung_nicht_gespeichert", "chk", "SELECT count(*) FROM %s WHERE id='p_a_zf' AND beanstandung IS NULL AND coalesce(pdf_pfad,'')=''" % FZ, "n1"),
    ("owner", "pruef_freigegebene_bleibt_freigegeben", "chk", "SELECT count(*) FROM %s WHERE id='p_a_fg' AND status='freigegeben'" % FZ, "n1"),
    ("mA", "mA_anlegen", "run", "INSERT INTO %s(id,worker_id,period,status) VALUES ('p_x',$A,'1999-09','in_arbeit')" % FZ, "err"),
    ("mA", "mA_loeschen", "run", "DELETE FROM %s WHERE id='p_a_zf'" % FZ, "ok0"),
    ("mA", "mA_verlauf_lesen", "cnt", "SELECT count(*) FROM public.finkzeit_verlauf", "n0"),
    ("mA", "mA_einstellung_aendern", "run", "UPDATE public.monatsfreigabe_einstellungen SET erinnerung_tage=9 WHERE id=1", "ok0"),
    ("mA", "mA_storage_eigener_praefix", "run", "INSERT INTO storage.objects(bucket_id,name,owner) VALUES ('epkolar-docs','monatsfreigabe/'||$A||'/p_unterschrift_1.png',$UA)", "ok1"),
    ("mA", "mA_storage_kein_pdf", "run", "INSERT INTO storage.objects(bucket_id,name,owner) VALUES ('epkolar-docs','monatsfreigabe/'||$A||'/p_freigabe.pdf',$UA)", "err"),
    ("mA", "mA_storage_fremder_praefix", "run", "INSERT INTO storage.objects(bucket_id,name,owner) VALUES ('epkolar-docs','monatsfreigabe/'||$B||'/p_fremd.png',$UA)", "err"),
    ("mA", "mA_storage_docs_praefix", "run", "INSERT INTO storage.objects(bucket_id,name,owner) VALUES ('epkolar-docs','docs/'||$A||'/p_doc.pdf',$UA)", "err"),
    ("owner", "pruef_freigabe_server", "chk", "SELECT count(*) FROM %s WHERE id='p_a_zf' AND status='freigegeben' AND freigegeben_von=$PA AND freigegeben_am IS NOT NULL AND ohne_monteur=false AND freigabe_hash IS NOT NULL AND coalesce(pdf_pfad,'')=''" % FZ, "n1"),

    # Techniker / Projektleitung
    ("tech", "tech_sieht", "cnt", "SELECT count(*) FROM %s WHERE id LIKE 'p\\_%%'" % FZ, "n0"),
    ("tech", "tech_aendert", "run", "UPDATE %s SET notiz='x' WHERE id LIKE 'p\\_%%'" % FZ, "ok0"),
    ("tech", "tech_anlegen", "run", "INSERT INTO %s(id,worker_id,period,status) VALUES ('p_t',$A,'1999-10','in_arbeit')" % FZ, "err"),
    ("pl", "pl_sieht", "cnt", "SELECT count(*) FROM %s WHERE id LIKE 'p\\_%%'" % FZ, "n0"),
    ("pl", "pl_aendert", "run", "UPDATE %s SET notiz='x' WHERE id LIKE 'p\\_%%'" % FZ, "ok0"),
    ("pl", "pl_anlegen", "run", "INSERT INTO %s(id,worker_id,period,status) VALUES ('p_p',$A,'1999-10','in_arbeit')" % FZ, "err"),
    ("pl", "pl_storage_lesen", "cnt", "SELECT count(*) FROM storage.objects WHERE bucket_id='epkolar-docs' AND name LIKE 'monatsfreigabe/%'", "n0"),
    ("pl", "pl_storage_schreiben", "run", "INSERT INTO storage.objects(bucket_id,name,owner) VALUES ('epkolar-docs','monatsfreigabe/'||$A||'/p_pl.png',$UPL)", "err"),

    # Buero
    ("buero", "buero_sieht_alle", "cnt", "SELECT count(*) FROM %s WHERE id LIKE 'p\\_%%'" % FZ, "n8"),
    ("buero", "buero_admin_uebergang_direkt", "run", "UPDATE %s SET status='zur_freigabe',freigabe_bis=$H+10 WHERE id='p_a_zaf2'" % FZ, "err"),
    ("buero", "buero_admin_felder_faelschen", "run", "UPDATE %s SET admin_freigabe_am=now(),admin_freigabe_von='gefaelscht',notiz='n' WHERE id='p_a_ia'" % FZ, "ok1"),
    ("owner", "pruef_admin_felder_unveraendert", "chk", "SELECT count(*) FROM %s WHERE id='p_a_ia' AND admin_freigabe_am IS NULL AND admin_freigabe_von IS NULL" % FZ, "n1"),
    ("buero", "buero_fertig_frist_vergangen", "run", "UPDATE %s SET status='zur_admin_freigabe',freigabe_bis=$H-1,snapshot=%s WHERE id='p_a_ia'" % (FZ, SN), "err"),
    ("buero", "buero_fertig_ohne_frist", "run", "UPDATE %s SET status='zur_admin_freigabe',snapshot=%s WHERE id='p_a_ia'" % (FZ, SN), "err"),
    ("buero", "buero_fertig_ohne_zahlen", "run", "UPDATE %s SET status='zur_admin_freigabe',freigabe_bis=$H+10 WHERE id='p_a_ia'" % FZ, "err"),
    ("buero", "buero_fertig", "run", "UPDATE %s SET status='zur_admin_freigabe',freigabe_bis=$H+10,snapshot=%s WHERE id='p_a_ia'" % (FZ, SN), "ok1"),
    ("buero", "buero_frist_in_vergangenheit", "run", "UPDATE %s SET freigabe_bis=$H-1 WHERE id='p_b_zf'" % FZ, "err"),
    ("buero", "buero_frist_aendern", "run", "UPDATE %s SET freigabe_bis=$H+20 WHERE id='p_b_zf'" % FZ, "ok1"),
    ("buero", "buero_frist_vorziehen_nach_admin", "run", "UPDATE %s SET freigabe_bis=$H+15 WHERE id='p_b_zf'" % FZ, "err"),
    ("buero", "buero_storage_monatsfreigabe_aendern", "run", "UPDATE storage.objects SET name=name WHERE bucket_id='epkolar-docs' AND name LIKE 'monatsfreigabe/%'", "ok0"),
    ("owner", "prep_storage_api_weg_an", "own", "SELECT set_config('storage.allow_delete_query','true',true)", ""),
    ("owner", "prep_storage_kontrollobjekt", "own", "INSERT INTO storage.objects(bucket_id,name) VALUES ('epkolar-docs','docs/'||$A||'/p_kontrolle.pdf')", ""),
    ("buero", "buero_storage_monatsfreigabe_loeschen", "run", "DELETE FROM storage.objects WHERE bucket_id='epkolar-docs' AND name LIKE 'monatsfreigabe/%'", "ok0"),
    ("buero", "buero_storage_kontrolle_docs_loeschen", "run", "DELETE FROM storage.objects WHERE bucket_id='epkolar-docs' AND name='docs/'||$A||'/p_kontrolle.pdf'", "ok1"),
    ("owner", "prep_storage_api_weg_aus", "own", "SELECT set_config('storage.allow_delete_query','false',true)", ""),
    ("buero", "buero_storage_monatsfreigabe_lesen", "cnt", "SELECT count(*) FROM storage.objects WHERE bucket_id='epkolar-docs' AND name LIKE 'monatsfreigabe/%'", "n2"),
    ("buero", "buero_zahlen_in_zur_freigabe", "run", "UPDATE %s SET snapshot='{\"x\":2}'::jsonb WHERE id='p_b_zf'" % FZ, "err"),
    ("buero", "buero_ohne_monteur_vor_frist", "run", "UPDATE %s SET status='freigegeben' WHERE id='p_b_zf'" % FZ, "err"),
    ("buero", "buero_aendert_freigegebene", "run", "UPDATE %s SET notiz='x' WHERE id='p_a_fg'" % FZ, "err"),
    ("buero", "buero_vermerk_freigegebene", "run", "UPDATE %s SET admin_vermerk='Buero will' WHERE id='p_a_fg'" % FZ, "err"),
    ("buero", "buero_zurueck_ohne_grund", "run", "UPDATE %s SET status='in_arbeit' WHERE id='p_a_zaf2'" % FZ, "err"),
    ("buero", "buero_loescht_zur_freigabe", "run", "DELETE FROM %s WHERE id='p_b_zf'" % FZ, "err"),
    ("buero", "buero_rpc_beanstanden", "run", "SELECT public.monatsfreigabe_beanstanden('p_b_zf','Buero spielt Monteur')", "err"),
    ("buero", "buero_verlauf_lesen", "cnt", "SELECT count(*) FROM public.finkzeit_verlauf WHERE finkzeit_id IN ('p_b_zf','p_a_ia')", "n3"),
    ("buero", "buero_einstellung_aendern", "run", "UPDATE public.monatsfreigabe_einstellungen SET erinnerung_tage=3 WHERE id=1", "ok1"),
    ("owner", "prep_frist_umgangen", "own", "UPDATE %s SET freigabe_bis=$H-1,frist_bei_admin_freigabe=$H+10 WHERE id='p_b_zf'" % FZ, ""),
    ("buero", "buero_ohne_monteur_frist_bei_admin_laeuft", "run", "UPDATE %s SET status='freigegeben' WHERE id='p_b_zf'" % FZ, "err"),
    ("owner", "prep_frist_abgelaufen", "own", "UPDATE %s SET freigabe_bis=$H-1,frist_bei_admin_freigabe=$H-1 WHERE id='p_b_zf'" % FZ, ""),
    ("buero", "buero_ohne_monteur_nach_frist", "run", "UPDATE %s SET status='freigegeben' WHERE id='p_b_zf'" % FZ, "ok1"),
    ("owner", "pruef_ohne_monteur", "chk", "SELECT count(*) FROM %s WHERE id='p_b_zf' AND ohne_monteur AND freigegeben_von=$PBU" % FZ, "n1"),
    ("buero", "buero_pdf_pfad_nachtragen", "run", "UPDATE %s SET pdf_pfad='monatsfreigabe/'||$A||'/p_sig.png' WHERE id='p_a_zf'" % FZ, "ok1"),
    ("buero", "buero_pdf_pfad_ersetzen", "run", "UPDATE %s SET pdf_pfad='monatsfreigabe/'||$A||'/p_unterschrift_1.png' WHERE id='p_a_zf'" % FZ, "err"),

    # Admin
    ("admin", "admin_frist_zu_knapp", "run", "UPDATE %s SET status='zur_freigabe' WHERE id='p_a_zaf'" % FZ, "err"),
    ("admin", "admin_frist_anpassen_und_freigeben", "run", "UPDATE %s SET status='zur_freigabe',freigabe_bis=$H+10 WHERE id='p_a_zaf'" % FZ, "ok1"),
    ("owner", "pruef_admin_freigabe_protokoll", "chk", "SELECT count(*) FROM %s WHERE id='p_a_zaf' AND admin_freigabe_von=$PAD AND admin_freigabe_am IS NOT NULL" % FZ, "n1"),
    ("admin", "admin_zurueck_mit_grund", "run", "UPDATE %s SET status='in_arbeit',rueckgabe_grund='Tag 12 pruefen' WHERE id='p_a_zaf2'" % FZ, "ok1"),
    ("admin", "admin_aendert_freigegebene_ohne_vermerk", "run", "UPDATE %s SET notiz='x' WHERE id='p_a_fg'" % FZ, "err"),
    ("owner", "prep_storage_api_weg_an2", "own", "SELECT set_config('storage.allow_delete_query','true',true)", ""),
    ("admin", "admin_storage_monatsfreigabe_loeschen", "run", "DELETE FROM storage.objects WHERE bucket_id='epkolar-docs' AND name LIKE 'monatsfreigabe/%'", "ok0"),
    ("owner", "pruef_storage_monatsfreigabe_vollstaendig", "chk", "SELECT count(*) FROM storage.objects WHERE bucket_id='epkolar-docs' AND name LIKE 'monatsfreigabe/%'", "n2"),
    ("owner", "prep_storage_api_weg_aus2", "own", "SELECT set_config('storage.allow_delete_query','false',true)", ""),
    ("admin", "admin_vermerk_freigegebene", "run", "UPDATE %s SET admin_vermerk='Korrektur Lohnbuero',notiz='x' WHERE id='p_a_fg'" % FZ, "ok1"),

    # Gesperrtes Konto
    ("owner", "prep_sperren", "own", "UPDATE public.users SET locked=1 WHERE auth_user_id=$UA", ""),
    ("mA", "gesperrt_sieht", "cnt", "SELECT count(*) FROM %s WHERE id LIKE 'p\\_%%'" % FZ, "n0"),
    ("mA", "gesperrt_storage", "run", "INSERT INTO storage.objects(bucket_id,name,owner) VALUES ('epkolar-docs','monatsfreigabe/'||$A||'/p_gesperrt.png',$UA)", "err"),
]

def ersetzen(sql):
    for k, v in (("$UPL", "quote_literal(v_upl)"), ("$UA", "quote_literal(v_ua)"), ("$PBU", "quote_literal(v_pbu)"), ("$PAD", "quote_literal(v_pad)"),
                 ("$PA", "quote_literal(v_pa)"), ("$A", "quote_literal(v_a)"), ("$B", "quote_literal(v_b)"), ("$H", "quote_literal(v_h)||'::date'")):
        sql = sql.replace(k, "'||" + v + "||'")
    return "'" + sql + "'"

def block(wer, name, art, sql, erw):
    s = ersetzen(q(sql))
    out = []
    uid = {"mA": "v_ua", "mB": "v_ub", "buero": "v_ubu", "admin": "v_uad", "tech": "v_ut", "pl": "v_upl"}.get(wer)
    if uid:
        out.append("  PERFORM set_config('request.jwt.claims', json_build_object('sub',%s,'role','authenticated')::text, true);" % uid)
        out.append("  EXECUTE 'SET LOCAL ROLE authenticated';")
    if art == "own":
        out.append("  EXECUTE %s;" % s)
    elif art in ("cnt", "chk"):
        out.append("  BEGIN EXECUTE %s INTO v_n; v_got := 'n'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err:'||SQLSTATE; END;" % s)
    else:
        out.append("  BEGIN EXECUTE %s; GET DIAGNOSTICS v_n = ROW_COUNT; v_got := 'ok'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err'; v_msg := SQLERRM; END;" % s)
    if art != "own":
        out.append("  IF v_got LIKE '%s' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL %s=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;" % (erw, name))
    if uid:
        out.append("  EXECUTE 'RESET ROLE';")
        out.append("  PERFORM set_config('request.jwt.claims', '{}', true);")
    return "\n".join(out)

def main(nachmessung=False):
    entwurf = io.open(ENTWURF, encoding="utf-8").read()
    kopf = ("-- MONATSFREIGABE_v1_PROBE.sql - GENERIERT von sql/_mf_probe_bauen.py. ENTWURF woertlich + Gegenmessung je Rolle\n"
            "-- in EINER Transaktion; endet IMMER mit RAISE EXCEPTION 'PROBE_ERGEBNIS ...' -> nichts bleibt bestehen.\n"
            "-- Zurueck zum Eigentuemer immer mit set_config('request.jwt.claims','{}',true) (nie '', guard_users_privilege parst JSON).\n"
            "BEGIN;\n")
    vor = ("DO $probe$\n"
           "DECLARE r text := ''; v_n int; v_got text; v_msg text; v_ok int := 0; v_fail int := 0; v_h date := (now() AT TIME ZONE 'Europe/Vienna')::date;\n"
           "  v_ua uuid; v_ub uuid; v_ubu uuid; v_uad uuid; v_ut uuid; v_upl uuid; v_a text; v_b text; v_pa text; v_pbu text; v_pad text;\n"
           "BEGIN\n"
           "  SELECT auth_user_id, monteur_id, id INTO v_ua, v_a, v_pa FROM public.users WHERE role='monteur' AND auth_user_id IS NOT NULL AND coalesce(monteur_id,'')<>'' AND coalesce(active,0)=1 AND coalesce(locked,0)=0 ORDER BY id LIMIT 1;\n"
           "  SELECT auth_user_id, monteur_id INTO v_ub, v_b FROM public.users WHERE role='monteur' AND auth_user_id IS NOT NULL AND coalesce(monteur_id,'')<>'' AND monteur_id<>v_a ORDER BY id LIMIT 1;\n"
           "  SELECT auth_user_id, id INTO v_ubu, v_pbu FROM public.users WHERE role='buero' AND auth_user_id IS NOT NULL AND coalesce(active,0)=1 AND coalesce(locked,0)=0 ORDER BY id LIMIT 1;\n"
           "  SELECT auth_user_id, id INTO v_uad, v_pad FROM public.users WHERE role='admin' AND auth_user_id IS NOT NULL AND coalesce(active,0)=1 AND coalesce(locked,0)=0 ORDER BY id LIMIT 1;\n"
           "  SELECT auth_user_id INTO v_ut FROM public.users WHERE role='techniker' AND auth_user_id IS NOT NULL ORDER BY id LIMIT 1;\n"
           "  SELECT auth_user_id INTO v_upl FROM public.users WHERE role='projektleiter' AND auth_user_id IS NOT NULL ORDER BY id LIMIT 1;\n"
           "  IF v_ua IS NULL OR v_ub IS NULL OR v_ubu IS NULL OR v_uad IS NULL OR v_ut IS NULL OR v_upl IS NULL THEN RAISE EXCEPTION 'PROBE_ERGEBNIS Konten fehlen'; END IF;\n"
           "  PERFORM set_config('request.jwt.claims', '{}', true);\n")
    teile = []
    vorher = None
    for st in ((SCHEMA + SCHRITTE) if nachmessung else SCHRITTE):
        b = block(*st)
        zeilen = b.split(NL)
        wer = st[0]
        if wer != "owner":
            if vorher == wer:
                zeilen = zeilen[2:]
            zeilen = zeilen[:-2]
        if vorher not in (None, "owner") and vorher != wer:
            zeilen = ["  EXECUTE 'RESET ROLE';", "  PERFORM set_config('request.jwt.claims', '{}', true);"] + zeilen
        vorher = wer
        teile.append(NL.join(zeilen))
    if vorher not in (None, "owner"):
        teile.append("  EXECUTE 'RESET ROLE';" + NL + "  PERFORM set_config('request.jwt.claims', '{}', true);")
    nach = ("  RAISE EXCEPTION 'PROBE_ERGEBNIS ok=% fail=% %', v_ok, v_fail, r;\n"
            "END $probe$;\nROLLBACK;\n")
    if nachmessung:
        kopf2 = ("-- MONATSFREIGABE_v1_NACHMESSUNG.sql - GENERIERT von sql/_mf_probe_bauen.py. NACH dem Einspielen: Schema + dieselben\n"
                 "-- Pruefschritte je Rolle gegen das eingespielte Modell (ohne Entwurf). Endet mit RAISE + ROLLBACK, damit die\n"
                 "-- Probezeilen (p_*, Periode 1999) nicht auf Prod bleiben. Erwartung: fail=0.\n"
                 "BEGIN;\n")
        io.open(ZIEL_NACH, "w", encoding="utf-8", newline="\n").write(kopf2 + vor + "\n".join(teile) + "\n" + nach)
        print("geschrieben:", ZIEL_NACH, len(SCHEMA) + len(SCHRITTE), "Schritte")
        return
    io.open(ZIEL, "w", encoding="utf-8", newline="\n").write(kopf + entwurf + "\n" + vor + "\n".join(teile) + "\n" + nach)
    print("geschrieben:", ZIEL, len(SCHRITTE), "Schritte")

if __name__ == "__main__":
    main()
    main(nachmessung=True)
