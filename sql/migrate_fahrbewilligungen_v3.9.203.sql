-- ═══════════════════════════════════════════════════════════════════════
-- FAHRBEWILLIGUNGEN (interne Fahrberechtigungen je Mitarbeiter) — v3.9.203
-- PDF als Base64 in file_data (wie Gefahrenstoffe, KEINE Storage-Abhängigkeit).
-- worker_id = workers.id (w1..wN) — dieselbe ID wie MitarbeiterView selM.id / curUser.monteurId.
-- ✅ ANGEWENDET 09.06.2026 via MCP (auf Chef-Wunsch "alles anlegen, muss sauber laufen"). Idempotent (re-run safe).
-- ═══════════════════════════════════════════════════════════════════════

create table if not exists public.fahrbewilligungen (
  id          text primary key,
  worker_id   text not null,            -- = workers.id (kein harter FK: offline-Sync-sicher, wie gefahrstoff)
  name        text,                     -- Anzeigename (z.B. "Staplerschein.pdf")
  file_data   text,                     -- Base64-dataUrl des PDFs (in der DB, nicht im Storage)
  mime        text,
  size        int,
  created_by  text,
  created_at  timestamptz default now()
);
create index if not exists fahrbewilligungen_worker_idx on public.fahrbewilligungen(worker_id);

alter table public.fahrbewilligungen enable row level security;

-- Lesen absichtlich offen für alle authenticated — interne Fahrbewilligungen sollen alle sehen.
-- (Die "nur eigene"-Sicht für Monteure ist client-seitig in MitarbeiterView gescoped.)
drop policy if exists fahrbewilligungen_select on public.fahrbewilligungen;
create policy fahrbewilligungen_select on public.fahrbewilligungen
  for select to authenticated using (true);

-- Schreiben (Upload/Update/Löschen) nur admin/projektleiter/buero — über die KANONISCHE Rolle
-- public.current_user_role() (SECURITY DEFINER, users.role via auth_user_id=auth.uid()).
-- Bewusst NICHT app_metadata.role: das ist in dieser DB veraltet/inkonsistent (buero=null, ein PL=monteur)
-- und würde echte Manager fälschlich blockieren. current_user_role() ist zuverlässig (alle User verlinkt).
drop policy if exists fahrbewilligungen_insert on public.fahrbewilligungen;
create policy fahrbewilligungen_insert on public.fahrbewilligungen
  for insert to authenticated
  with check (public.current_user_role() = any (array['admin','projektleiter','buero']));

drop policy if exists fahrbewilligungen_update on public.fahrbewilligungen;
create policy fahrbewilligungen_update on public.fahrbewilligungen
  for update to authenticated
  using (public.current_user_role() = any (array['admin','projektleiter','buero']));

drop policy if exists fahrbewilligungen_delete on public.fahrbewilligungen;
create policy fahrbewilligungen_delete on public.fahrbewilligungen
  for delete to authenticated
  using (public.current_user_role() = any (array['admin','projektleiter','buero']));
