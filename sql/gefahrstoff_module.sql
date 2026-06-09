-- ═══════════════════════════════════════════════════════════════════════
-- GEFAHRSTOFF-MODUL (Sicherheitsdatenblätter / SDS) — v3.9.196
-- Eigenständiges Modul wie Werkzeuge/Fahrzeuge. Explorer mit freien Ordnern.
-- Lesen: alle authentifizierten Mitarbeiter. Bearbeiten: Admin + Pinger + Schmid (client-gated via canDo('gefahrstoff_edit')).
-- PDFs liegen im bestehenden Storage-Bucket unter Prefix 'gefahrstoff/<fileId>.pdf' (kein neuer Bucket nötig).
-- ⚠️ APPLY erst wenn Pinger NICHT live arbeitet (Tabellen-Create stört ihn zwar nicht, aber sauberes Fenster wählen).
-- ═══════════════════════════════════════════════════════════════════════

-- Ordner (frei verschachtelbar, echter Explorer)
create table if not exists public.gefahrstoff_folders (
  id          text primary key,
  name        text not null,
  parent_id   text references public.gefahrstoff_folders(id) on delete cascade,
  created_by  text,
  created_at  timestamptz default now(),
  updated_at  timestamptz default now()
);
create index if not exists gefahrstoff_folders_parent_idx on public.gefahrstoff_folders(parent_id);

-- Dateien (überwiegend PDF). file_path = Storage-Objektpfad im bestehenden Bucket; file_url = öffentliche/abgeleitete URL.
create table if not exists public.gefahrstoff_files (
  id          text primary key,
  folder_id   text references public.gefahrstoff_folders(id) on delete set null,
  name        text not null,            -- Anzeigename (z.B. "Aceton technisch SDB.pdf")
  file_path   text,                     -- Storage-Pfad, z.B. 'gefahrstoff/<id>.pdf'
  file_url    text,                     -- abgeleitete URL (public)
  mime        text,
  size        bigint,
  lieferant   text,                     -- optional: Hersteller/Lieferant für Suche
  notiz       text,                     -- optional
  created_by  text,
  created_at  timestamptz default now(),
  updated_at  timestamptz default now()
);
create index if not exists gefahrstoff_files_folder_idx on public.gefahrstoff_files(folder_id);

-- RLS: Lesen für alle authentifizierten; Schreiben client-gated (canDo), DB additiv offen wie übrige App-Tabellen.
-- (Härtung der Write-Policy auf Rollen/User = Sebastian-Option, analog SECURITY-ADVISOR-BACKLOG.)
alter table public.gefahrstoff_folders enable row level security;
alter table public.gefahrstoff_files   enable row level security;

drop policy if exists gefahrstoff_folders_rw on public.gefahrstoff_folders;
create policy gefahrstoff_folders_rw on public.gefahrstoff_folders
  for all to authenticated using (true) with check (true);

drop policy if exists gefahrstoff_files_rw on public.gefahrstoff_files;
create policy gefahrstoff_files_rw on public.gefahrstoff_files
  for all to authenticated using (true) with check (true);

-- HINWEIS Storage: kein neuer Bucket — die App nutzt einen bestehenden Bucket (SB_BUCKET, public).
-- PDFs werden unter Prefix 'gefahrstoff/' abgelegt. Falls strikt-privat gewünscht: eigener Bucket
-- 'gefahrenstoffe' + signed URLs + Storage-RLS (Sebastian-Entscheidung).
