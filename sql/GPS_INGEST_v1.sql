-- ═══════════════════════════════════════════════════════════════════
-- GPS_INGEST_v1.sql — Fundament fuer die Edge-Function gps_ingest
-- IDEMPOTENT. NICHT automatisch ausgefuehrt — Human-Run-Gate.
-- Ausfuehren im Supabase SQL-Editor (Projekt jiggujpruejkaomgxarp).
--
-- Setzt sql/GPS_v1.sql voraus (Tabelle fz_positions, Spalte
-- fahrzeuge.tracker_imei).
--
-- WOZU: Traccar wiederholt einen fehlgeschlagenen Forward. Ohne
-- Eindeutigkeit haette jede Wiederholung denselben Ortungspunkt ein
-- zweites Mal angelegt — und damit Fahrtenbuch, Tageskilometer und
-- Durchschnittsgeschwindigkeit still verfaelscht. Der Unique-Index
-- macht den Insert der Function idempotent (ON CONFLICT DO NOTHING).
-- ═══════════════════════════════════════════════════════════════════

-- ── 1) Idempotenz-Schluessel: ein Ortungspunkt je Fahrzeug und Zeit ──
-- HINWEIS: fz_positions ist Stand 14.07.2026 LEER — der Index kann ohne
-- Bereinigung angelegt werden. Sollte die Tabelle wider Erwarten schon
-- Duplikate enthalten, scheitert das CREATE; dann vorher deduplizieren
-- (Query steht auskommentiert am Dateiende).
CREATE UNIQUE INDEX IF NOT EXISTS fz_positions_fahrzeug_ts_uidx
  ON public.fz_positions (fahrzeug_id, ts);

-- ── 2) Der IMEI-Lookup der Function laeuft je Position einmal ─────────
-- Ohne Index waere das bei 10s-Takt ein Seq-Scan pro Ortungspunkt.
CREATE INDEX IF NOT EXISTS fahrzeuge_tracker_imei_idx
  ON public.fahrzeuge (tracker_imei) WHERE tracker_imei IS NOT NULL;

-- ── 3) KEINE Insert-Policy fuer fz_positions ─────────────────────────
-- Bewusst so gelassen (sql/GPS_v1.sql): Rohpunkte darf ausschliesslich
-- die Edge-Function gps_ingest schreiben, und die benutzt den
-- SERVICE_ROLE_KEY (umgeht RLS). Kein App-Benutzer, kein Kiosk und kein
-- anon-Key darf jemals eine Position anlegen — sonst waere das
-- Fahrtenbuch faelschbar.

-- ═══════════════════════════════════════════════════════════════════
-- DEPLOY DER FUNCTION (Sebastian / manuell — NICHT Teil dieses SQL):
--
--   1. Secret setzen (langes Zufallstoken, z.B. openssl rand -hex 32):
--        supabase secrets set GPS_INGEST_TOKEN=<token>
--   2. Deploy OHNE JWT-Pflicht — Traccar hat kein Supabase-JWT:
--        cd C:\temp\epkfn
--        supabase functions deploy gps_ingest --no-verify-jwt
--      (Die Supabase-CLI vertraegt weder UNC-Pfade noch Netzlaufwerke —
--       darum C:\temp\epkfn, siehe CLAUDE.md.)
--   3. In Traccar (conf/traccar.xml) den Forward einrichten:
--        <entry key='forward.enable'>true</entry>
--        <entry key='forward.type'>json</entry>
--        <entry key='forward.url'>https://jiggujpruejkaomgxarp.functions.supabase.co/gps_ingest?token=<token></entry>
--      Kann die Traccar-Version Custom-Header, ist der Header
--      x-gps-token: <token> der sauberere Weg (Token nicht im Log).
--   4. Am Fahrzeug die IMEI eintragen (Fahrzeug-Formular, seit v3.9.689).
--      OHNE diesen Schritt kann die Function den Tracker keinem Fahrzeug
--      zuordnen und antwortet mit unmapped — das ist kein Fehler der
--      Function, sondern fehlende Stammdatenpflege.
-- ═══════════════════════════════════════════════════════════════════

-- ═══════════════════════════════════════════════════════════════════
-- VERIFIKATION (nach dem ersten echten Tracker-Punkt):
--   select fahrzeug_id, count(*), min(ts), max(ts)
--     from public.fz_positions group by 1 order by 2 desc;
--   -- Plausibilitaet der Geschwindigkeit (Traccar liefert KNOTEN, die
--   -- Function rechnet in km/h um — Werte >200 deuten auf eine
--   -- vergessene Umrechnung hin):
--   select max(speed) from public.fz_positions;
--
-- DEDUPLIZIERUNG (nur falls der Unique-Index oben scheitert):
--   delete from public.fz_positions a using public.fz_positions b
--    where a.ctid < b.ctid
--      and a.fahrzeug_id = b.fahrzeug_id and a.ts = b.ts;
--
-- ROLLBACK (manuell, NICHT Teil des Vorwaerts-Laufs):
--   DROP INDEX IF EXISTS public.fz_positions_fahrzeug_ts_uidx;
--   DROP INDEX IF EXISTS public.fahrzeuge_tracker_imei_idx;
-- ═══════════════════════════════════════════════════════════════════
