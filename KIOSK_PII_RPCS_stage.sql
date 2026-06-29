-- =============================================================================
-- KIOSK_PII_RPCS_stage.sql   (2026-06-29)   project-ref: jiggujpruejkaomgxarp
-- =============================================================================
-- SCHRITT 1 von 2 (HIGH-Fund A-1, Kiosk-PII-Lockdown).
-- Legt die beiden Ersatz-RPCs an, die der lager_display-Kiosk STATT der direkten
-- workers-/arbeitsscheine-REST-Reads nutzen soll. REIN ADDITIV — bricht nichts,
-- JETZT SOFORT gefahrlos ausfuehrbar. Erst NACH Client-Umstellung darf die
-- Sperr-Datei KIOSK_PII_LOCKDOWN_stage.sql laufen.
-- Idempotent (create or replace), self-guarding (Gate auth_role()='lager_display'
-- OR is_staff()), Muster 1:1 aus public.kiosk_week_absences.
-- =============================================================================


-- A1) Minimale Mitarbeiter-Liste fuer beide Tafeln (Name/Rolle/Austritt) — KEIN PII.
--     WochenplanTafel: maName/maRole (m.n/m.r); MonteurTafel: fieldM (m.r/m.austritt).
create or replace function public.kiosk_field_workers()
returns table(id text, name text, role text, austritt text)
language plpgsql
stable
security definer
set search_path to 'public','pg_temp'
as $function$
begin
  if not (public.auth_role()='lager_display' or public.is_staff()) then
    raise exception 'not authorized' using errcode='42501';
  end if;
  return query
    select w.id, w.name, w.role, w.austritt
    from public.workers w;
end
$function$;

revoke all on function public.kiosk_field_workers() from public, anon;
grant execute on function public.kiosk_field_workers() to authenticated;


-- A2) Minimale Wochen-Arbeitsscheine fuer die MonteurTafel — NUR Plandaten.
--     IMMER RAUS (nie auf den oeffentlichen Monitor): telefon, kund_tel, kontakt,
--       kund_email, kund_str, kund_plz, kund_nr, sachbearbeiter, notizen,
--       arbeitsanweisungen, durchgefuehrte, material, juprowa_*.
--
--     >>> SEBASTIAN-ENTSCHEIDUNG: arbeitsort (Ort/Strasse der Baustelle) auf der
--         Lager-Tafel sichtbar — JA oder NEIN? Unten ZWEI Varianten.
--         Genau EINE ausfuehren (beide haben dieselbe Signatur, die zweite
--         create-or-replace wuerde die erste ueberschreiben).
--
-- ── VARIANTE 1 (DEFAULT, aktiv): OHNE arbeitsort — strikt kein Ort auf dem Monitor ──
create or replace function public.kiosk_week_arbeitsscheine(p_from text, p_to text)
returns table(
  id text, nummer text, kund_name text, monteur text,
  termin_bestaetigt text, termin_zeit text, termin_vorschlag_zeit text,
  scheinstatus text, scheinart text, prioritaet text
)
language plpgsql
stable
security definer
set search_path to 'public','pg_temp'
as $function$
begin
  if not (public.auth_role()='lager_display' or public.is_staff()) then
    raise exception 'not authorized' using errcode='42501';
  end if;
  return query
    select a.id, a.nummer, a.kund_name, a.monteur,
           a.termin_bestaetigt, a.termin_zeit, a.termin_vorschlag_zeit,
           a.scheinstatus, a.scheinart, a.prioritaet
    from public.arbeitsscheine a
    where left(coalesce(a.termin_bestaetigt,''),10) between p_from and p_to
      and coalesce(a.scheinstatus,'') <> 'storniert';
end
$function$;


-- ── VARIANTE 2 (Alternative): MIT arbeitsort — Baustellen-Ort sichtbar ──
--    Wenn der Ort auf die Tafel SOLL: die folgende Funktion statt Variante 1
--    ausfuehren (Kommentarzeichen unten entfernen). Kund-Tel/Kontakt/Anweisungen
--    bleiben auch hier draussen.
--
-- create or replace function public.kiosk_week_arbeitsscheine(p_from text, p_to text)
-- returns table(
--   id text, nummer text, kund_name text, monteur text,
--   termin_bestaetigt text, termin_zeit text, termin_vorschlag_zeit text,
--   scheinstatus text, scheinart text, prioritaet text, arbeitsort text
-- )
-- language plpgsql
-- stable
-- security definer
-- set search_path to 'public','pg_temp'
-- as $function$
-- begin
--   if not (public.auth_role()='lager_display' or public.is_staff()) then
--     raise exception 'not authorized' using errcode='42501';
--   end if;
--   return query
--     select a.id, a.nummer, a.kund_name, a.monteur,
--            a.termin_bestaetigt, a.termin_zeit, a.termin_vorschlag_zeit,
--            a.scheinstatus, a.scheinart, a.prioritaet, a.arbeitsort
--     from public.arbeitsscheine a
--     where left(coalesce(a.termin_bestaetigt,''),10) between p_from and p_to
--       and coalesce(a.scheinstatus,'') <> 'storniert';
-- end
-- $function$;

revoke all on function public.kiosk_week_arbeitsscheine(text,text) from public, anon;
grant execute on function public.kiosk_week_arbeitsscheine(text,text) to authenticated;

-- ── Verify (read-only) ───────────────────────────────────────────────────────
-- select proname, pg_get_function_result(oid) from pg_proc
--  where pronamespace='public'::regnamespace and proname like 'kiosk_%';
