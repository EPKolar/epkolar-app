-- ═══════════════════════════════════════════════════════════════════════════════════════
-- FAHRER_FAHRZEUG_HISTORIE_v1 — zeitliche Fahrer<->Fahrzeug-Zuordnung fuer ein rechtssicheres
--   Fahrtenbuch (Phase 2 zum v846/v855-Nachzieher).
--
-- ██ FUER CHAT-CLAUDE / SEBASTIAN — NICHT AUSFUEHREN. Human-Run-Gate. ██
--   Kein Auto-Apply. Erst nach Freigabe des Modells durch Sebastian ausfuehren; danach wird die
--   Client-Verdrahtung (Phase-2-Lookup in _fahrerVon + Write-on-Read) freigeschaltet.
--   Projekt: jiggujpruejkaomgxarp (Baumanagement & Zeiterfassung). Kein CC-DDL.
--
-- WARUM (Befund v855):
--   Bis heute gibt es KEINE zeitlich belegbare Quelle, wer wann welches Fahrzeug gefahren hat.
--   Der v846-Snapshot nahm den AKTUELLEN Fahrzeugfahrer zum Ansehzeitpunkt -> falsch nach jedem
--   Fahrerwechsel. v855 schreibt darum fahrer_id=null (lieber leer als falsch). Diese Tabelle
--   liefert die fehlende Wahrheit: pro Fahrzeug ein zeitlicher Verlauf der zugeordneten Fahrer.
--
-- MODELL:
--   Eine Zeile = "Fahrer F hatte Fahrzeug Z von `von` bis `bis` (bis NULL = bis heute/offen)".
--   Lookup fuer eine Fahrt (Fahrt-Beginn `t`, Fahrzeug `z`):
--     SELECT fahrer_id FROM fahrer_fahrzeug_historie
--      WHERE fahrzeug_id = z AND von <= t AND (bis IS NULL OR t < bis)
--      ORDER BY von DESC LIMIT 1;
--   -> genau der Fahrer, der ZUM FAHRT-ZEITPUNKT zugeordnet war (nicht der aktuelle).
--
-- ID-TYPEN: fahrzeug_id/fahrer_id hier als text (die App erzeugt String-uids; fahrzeuge.id und
--   fahrer=monteur_id sind Strings). Falls die realen Spalten uuid sind, Typen entsprechend
--   anpassen + echte FOREIGN KEYS ergaenzen (hier bewusst weggelassen, bis Sebastian die
--   Zieltypen bestaetigt — kein blindes FK auf vermutete Typen).
-- ═══════════════════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS public.fahrer_fahrzeug_historie (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  fahrzeug_id text NOT NULL,
  fahrer_id   text NOT NULL,
  von         timestamptz NOT NULL,
  bis         timestamptz,                 -- NULL = aktuell/offen
  notiz       text,
  created_at  timestamptz NOT NULL DEFAULT now(),
  created_by  text,
  CONSTRAINT fahrer_hist_von_vor_bis CHECK (bis IS NULL OR bis > von)
);

-- Lookup-Index (Kern der Zuordnung: pro Fahrzeug entlang der Zeit)
CREATE INDEX IF NOT EXISTS idx_fahrer_hist_fz_von
  ON public.fahrer_fahrzeug_historie (fahrzeug_id, von DESC);

-- Optionaler Ueberlappungsschutz je Fahrzeug (verhindert zwei offene/ueberlappende Fahrer):
--   braucht die btree_gist-Extension. NUR aktivieren, wenn Sebastian das will.
-- CREATE EXTENSION IF NOT EXISTS btree_gist;
-- ALTER TABLE public.fahrer_fahrzeug_historie
--   ADD CONSTRAINT fahrer_hist_no_overlap
--   EXCLUDE USING gist (fahrzeug_id WITH =, tstzrange(von, bis, '[)') WITH &&);

-- ── PROVENIENZ (Vorschlag, Teil des Modells — erst nach Freigabe) ──────────────────────────
--   Damit jede Fahrt-Zeile traegt, WOHER ihr Fahrer stammt, bekommt fz_fahrten eine Quelle.
--   fahrer_id bleibt NULLABLE (Luecke ist erlaubt und ehrlich).
--     'historie' = aus dieser Tabelle aufgeloest · 'manuell' = Buero hat nachgetragen · NULL = offen
-- ALTER TABLE public.fz_fahrten ADD COLUMN IF NOT EXISTS fahrer_quelle text;
-- COMMENT ON COLUMN public.fz_fahrten.fahrer_quelle IS
--   'Provenienz des Fahrers: historie|manuell|NULL. v855-Modell.';

-- ── NACH DEM RUN: Client-Verdrahtung (separater Commit, dann greift es) ────────────────────
--   1) Write-on-Read (:25731): fahrer_id = Lookup(historie, fahrzeug_id, beginn) statt null;
--      fahrer_quelle = fahrer_id ? 'historie' : NULL.
--   2) _fahrerVon (:25986): weiterhin NUR x.fahrer_id zeigen (kein Fallback) — die Historie
--      fuellt den Snapshot jetzt korrekt, die Anzeige-Regel bleibt unveraendert.
--   3) Buero-UI zum Pflegen der Historie (von/bis je Fahrzeug) — NICHT vor Freigabe bauen.
-- ═══════════════════════════════════════════════════════════════════════════════════════
