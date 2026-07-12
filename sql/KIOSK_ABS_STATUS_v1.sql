-- KIOSK_ABS_STATUS_v1 — Kiosk-Abwesenheiten: nur GENEHMIGTE anzeigen
-- =============================================================================
-- STATUS: BEREITS AUSGEFUEHRT — Sebastian-Run 12.07.2026 ~16:15.
--   Verifiziert: KW29 liefert 5 korrekte Zeilen, Riedmann-KW24 (4 abgelehnte
--   Tage) liefert 0. Diese Datei bleibt als Doku + Wiederherstellungspunkt im
--   Repo; sie ist idempotent (CREATE OR REPLACE), ein erneuter Run schadet nicht.
--   Von Claude Code NICHT autonom ausgefuehrt (SQL = Human-Run-Gate).
--
-- BEFUND (12.07.2026, verifiziert via pg_get_functiondef):
--   kiosk_week_absences filtert auf a.type, aber NICHT auf a.status.
--   Der Kiosk-Screen (?screen=planung) zeigt damit auch abgelehnte und
--   beantragte Abwesenheiten als echte Abwesenheit an.
--   Stand 12.07.2026: 9 abgelehnte Saetze in absences (Schmid/Pinger April,
--   Riedmann Juni). Keiner davon in KW28/29 — das erklaert NICHT das
--   gemeldete KW29-Symptom, ist aber ein eigener, belegter Defekt.
--
-- Die App-Seite (Streifen/Excel/PDF der Wochenplanung) ist in v3.9.674 bereits
-- gefixt (gemeinsamer Helper _absShow, nur status==='genehmigt').
-- Der Kiosk kann clientseitig NICHT gefiltert werden, weil diese RPC gar kein
-- status-Feld zurueckgibt — deshalb dieser Fix hier.
--
-- UEBERGANGSPHASE: unkritisch. Der Kiosk-Client ruft _absShow nicht auf; er
-- rendert bis zum Run dieser Datei weiter alles, was die RPC liefert, und wird
-- danach automatisch korrekt. Kein Client-Deploy noetig, kein undefined-Risiko.
--
-- IDEMPOTENT: CREATE OR REPLACE, beliebig oft ausfuehrbar.
-- Signatur, RETURNS TABLE, STABLE, SECURITY DEFINER und search_path sind
-- unveraendert aus der bestehenden Definition uebernommen — einzige Aenderung
-- ist die zusaetzliche status-Bedingung in der WHERE-Klausel.
-- =============================================================================

CREATE OR REPLACE FUNCTION public.kiosk_week_absences(p_from text, p_to text)
 RETURNS TABLE(worker_name text, day text, atype text)
 LANGUAGE plpgsql
 STABLE SECURITY DEFINER
 SET search_path TO 'public', 'pg_temp'
AS $function$
begin
  if not (public.auth_role()='lager_display' or public.is_staff()) then
    raise exception 'not authorized' using errcode='42501';
  end if;
  return query
    select coalesce(w.name, a.worker_id)::text, a.from_date::text, a.type::text
    from public.absences a
    left join public.workers w on w.id = a.worker_id
    where a.from_date >= p_from and a.from_date <= p_to
      and a.type in ('krankenstand','krank','urlaub','zeitausgleich','za')
      and a.status = 'genehmigt';   -- v3.9.674: nur freigegebene Abwesenheiten
end $function$;

-- Verifikation nach dem Run (muss 0 Zeilen liefern — kein abgelehnter Tag mehr sichtbar):
--   select * from public.kiosk_week_absences('2026-04-20','2026-04-24');
--   -- vorher: Pinger 22.04. + 24.04. (beide abgelehnt) tauchten hier auf
