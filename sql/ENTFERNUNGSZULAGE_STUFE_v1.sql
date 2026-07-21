-- IDEMPOTENT
-- sql/ENTFERNUNGSZULAGE_STUFE_v1.sql — v3.9.785 Entfernungszulage 3-Stufen (Sebastian 21.07.2026)
-- =============================================================================
-- HUMAN-RUN-GATE: manuell im Supabase SQL-Editor ausfuehren. KEIN autonomes DDL.
-- =============================================================================
-- Fachlich: KV-Blatt gueltig ab 01.01.2026 -> GENAU EINE Entfernungszulage-Stufe pro Tag:
--   klein 11,94 | mittel 30,00 | gross 62,04 EUR/Tag (Saetze liegen in system_config.kv_rules,
--   NICHT in dieser Tabelle). Naechtigungsgeld wird NICHT verwendet.
--
-- Modell-Umbau der Vergabe-Tabelle entfernungszulage_tage:
--   bisher: aktiv boolean  (true = Entfernungszulage-Tag)
--   neu:    stufe text CHECK in ('klein','mittel','gross'); NULL = keine (abgelehnt)
--
-- ADDITIV — die Spalte aktiv wird in DIESEM Schritt NICHT gedroppt (separater Drop-Auftrag
-- spaeter, sobald v3.9.785 stabil live ist). Der App-Lesepfad (_ezStufeFromRow) ist migration-
-- tolerant: eine Zeile mit stufe IS NULL + aktiv=true wird weiterhin als 'klein' gelesen.
--
-- Migration der Bestandsdaten:
--   aktiv = true   ->  stufe = 'klein'   (bisherige Entfernungszulage-Tage = kleine Stufe)
--   aktiv = false  ->  stufe = NULL      (Zeile bleibt bestehen, bedeutet "keine")
-- =============================================================================

-- 1) Neue Spalte additiv + CHECK. NULL ist erlaubt (= keine); der CHECK laesst NULL durch.
alter table public.entfernungszulage_tage
  add column if not exists stufe text
  check (stufe in ('klein','mittel','gross'));

-- 2) Backfill nur dort, wo stufe noch nicht gesetzt ist (idempotent bei Wiederholung).
update public.entfernungszulage_tage
   set stufe = 'klein'
 where stufe is null
   and aktiv = true;

-- aktiv = false -> stufe bleibt NULL (= "keine"/abgelehnt). Explizit nichts zu tun.

-- 3) Kontrolle (read-only) — Verteilung nach Migration:
--   select stufe, aktiv, count(*) from public.entfernungszulage_tage group by 1,2 order by 1,2;

-- SPAETERER, SEPARATER SCHRITT (NICHT hier ausfuehren):
--   alter table public.entfernungszulage_tage drop column aktiv;
--   -> erst nachdem v3.9.785 live+stabil ist und kein Lesepfad mehr auf aktiv faellt.
