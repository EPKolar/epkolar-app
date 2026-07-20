-- ═══════════════════════════════════════════════════════════════════════════
-- STEMPEL_TERMINAL_RPC_v3.sql  ·  Stufe 1 Stempeluhr — Weg B (SECURITY-DEFINER-RPC)
-- IDEMPOTENT · Human-Run-Gate · Supabase SQL-Editor (Projekt jiggujpruejkaomgxarp)
-- ═══════════════════════════════════════════════════════════════════════════
-- MODELL (Sebastian, 20.07.2026): Das Wandpanel am Werkstor ist NICHT eingeloggt.
-- Monteur zieht den Chip drueber -> Panel liest die nfc_uid -> ruft DIESEN RPC.
-- Der RPC ist der EINZIGE Schreibweg in stempel_log fuer das Terminal; die
-- bestehenden is_staff()-Policies bleiben unveraendert (Buero/Admin korrigiert
-- weiter ueber die App). Es wird KEINE offene anon-INSERT-Policy angelegt.
--
-- HAERTE (anon-aufrufbarer SECURITY DEFINER — maximale Vorsicht):
--   * SET search_path = public  -> kein DEFINER-Hijack ueber den search_path.
--   * Liest NUR workers (id,name,nfc_uid,active) + stempel_log (worker/ts/dir).
--     KEIN Zugriff auf users, projects, Loehne, SVNR, Adressen.
--   * Unbekannte nfc_uid -> definierter Fehler, KEIN INSERT, KEIN Leak welche
--     UIDs existieren (immer dieselbe Meldung 'unknown_chip').
--   * Doppel-Scan-Schutz im RPC: letzter Eintrag des Workers juenger als 12 s
--     -> als Dublette gemeldet, KEIN zweiter INSERT (HID-Wedge feuert doppelt).
--   * Richtung server-seitig: letzter Eintrag 'kommen' und < 18 h alt -> 'gehen',
--     sonst 'kommen' (deckt Uebernacht + vergessenen Gehen-Stempel; v662-Muster).
--   * GRANT EXECUTE nur an anon + authenticated (das Panel ist anon; ein
--     eingeloggter Admin-Preview laeuft als authenticated denselben Weg).
--   * ts wird ROH/ungerundet gespeichert (Rundung ist Sache der PZE-Auswertung).
--
-- €/LOHN: null Wirkung. stempel_log ist lohn-unabhaengig (die Zulagen-Reports
-- lesen time_entries, nicht stempel_log). time_entries wird NICHT angefasst.
-- ═══════════════════════════════════════════════════════════════════════════

CREATE OR REPLACE FUNCTION public.stempel_terminal_stempel(p_nfc_uid text)
RETURNS json
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  v_uid      text := btrim(COALESCE(p_nfc_uid, ''));
  v_wid      text;
  v_name     text;
  v_last_dir text;
  v_last_ts  timestamptz;
  v_dir      text;
  v_now      timestamptz := now();
BEGIN
  -- leere/fehlende UID -> kein INSERT
  IF v_uid = '' THEN
    RETURN json_build_object('ok', false, 'error', 'no_uid');
  END IF;

  -- Worker per nfc_uid — NUR id + name, nur aktive. Kein weiteres Feld verlassen den RPC.
  SELECT w.id, w.name
    INTO v_wid, v_name
    FROM public.workers w
    WHERE w.nfc_uid = v_uid
      AND w.active = 1
    LIMIT 1;

  -- unbekannter/inaktiver Chip -> immer dieselbe Meldung, kein INSERT, kein Leak
  IF v_wid IS NULL THEN
    RETURN json_build_object('ok', false, 'error', 'unknown_chip');
  END IF;

  -- letzter Stempel dieses Workers (fuer Doppel-Scan-Schutz + Richtung)
  SELECT s.direction, s.ts
    INTO v_last_dir, v_last_ts
    FROM public.stempel_log s
    WHERE s.worker_id = v_wid
    ORDER BY s.ts DESC
    LIMIT 1;

  -- Doppel-Scan HART: < 12 s seit dem letzten Eintrag -> Dublette, KEIN INSERT
  IF v_last_ts IS NOT NULL AND (v_now - v_last_ts) < interval '12 seconds' THEN
    RETURN json_build_object(
      'ok', true, 'dup', true,
      'worker_name', v_name,
      'richtung', v_last_dir,
      'ts', v_last_ts
    );
  END IF;

  -- Richtung: offenes 'kommen' juenger als 18 h -> 'gehen', sonst Frischstart 'kommen'
  IF v_last_dir = 'kommen' AND (v_now - v_last_ts) < interval '18 hours' THEN
    v_dir := 'gehen';
  ELSE
    v_dir := 'kommen';
  END IF;

  INSERT INTO public.stempel_log (id, worker_id, ts, direction, device)
  VALUES (gen_random_uuid(), v_wid, v_now, v_dir, 'terminal:rpc');

  RETURN json_build_object(
    'ok', true, 'dup', false,
    'worker_name', v_name,
    'richtung', v_dir,
    'ts', v_now
  );
END;
$$;

-- Ausfuehrungsrechte eng halten: das Panel ist anon; ein eingeloggter Admin-Preview
-- (authenticated) laeuft denselben Weg. NICHT breiter (kein PUBLIC).
REVOKE ALL ON FUNCTION public.stempel_terminal_stempel(text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.stempel_terminal_stempel(text) TO anon, authenticated;

-- ─────────────────────────────────────────────────────────────────────────────
-- OPTIONALE HAERTUNG (empfohlen, aber Datenpflege-Voraussetzung pruefen):
-- Ein UNIQUE-Index auf nfc_uid verhindert, dass zwei Worker denselben Chip tragen
-- (sonst trifft LIMIT 1 einen beliebigen). Erst aktivieren, wenn sicher ist, dass
-- keine Doppelbelegung existiert (Stand 20.07.: 0 von 11 Workern haben eine nfc_uid).
--   CREATE UNIQUE INDEX IF NOT EXISTS workers_nfc_uid_uidx
--     ON public.workers (nfc_uid) WHERE nfc_uid IS NOT NULL AND nfc_uid <> '';
-- ─────────────────────────────────────────────────────────────────────────────

-- VERIFY (read-only, nach dem Run):
--   SELECT proname, prosecdef, proconfig FROM pg_proc
--     WHERE proname='stempel_terminal_stempel';           -- prosecdef=t, proconfig={search_path=public}
--   SELECT stempel_terminal_stempel('__kein_echter_chip__');  -- -> {"ok":false,"error":"unknown_chip"}
