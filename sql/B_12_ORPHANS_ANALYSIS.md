# B_12_ORPHANS_ANALYSIS · arbeitsscheine mit orphan `monteur`-Wert

**Datum**: 2026-04-19 (v3.8.19 Block B)
**Status**: DECISION PENDING (Sebastian muss Query ausführen + Kategorisierung entscheiden)
**Datenbasis**: Nacht-2-Baseline-Messung 19.04.2026 — 12 Rows identifiziert

CC kann die Query nicht selbst gegen Supabase ausführen (keine DB-Rechte).
Dieses Dokument enthält:
1. Die Details-Query
2. Kategorisierungs-Logik (CC analysiert dann die Output-Tabelle)
3. 3 Staging-SQLs (NICHT ausführen ohne Sebastian-Entscheidung)

---

## Step 1 · Details-Query (Sebastian führt aus)

```sql
-- Full-Detail der 12 Orphan-AS
SELECT
  a.id,
  a.nummer,
  a.monteur,
  CASE
    WHEN a.monteur IS NULL THEN '[NULL]'
    WHEN a.monteur = '' THEN '[EMPTY_STRING]'
    WHEN a.monteur ~ '^w[0-9]+$' THEN '[WORKER_ID_PATTERN:' || a.monteur || ']'
    WHEN a.monteur ~ '^P[0-9]+$' THEN '[JUPROWA_CODE:' || a.monteur || ']'
    ELSE '[UNKNOWN:' || a.monteur || ']'
  END AS kategorie,
  a.scheinstatus,
  a.kunde_name,
  a.created_at,
  a.juprowa_id
FROM public.arbeitsscheine a
WHERE a.monteur IS NOT NULL
  AND a.monteur <> ''
  AND NOT EXISTS (SELECT 1 FROM public.workers w WHERE w.id = a.monteur)
ORDER BY a.created_at DESC;

-- Zusatz: Extended-Check inkl. Leerstrings (Baseline-Messung filtert sie ggf. raus)
SELECT
  COUNT(*) FILTER (WHERE monteur IS NULL) as null_count,
  COUNT(*) FILTER (WHERE monteur = '') as empty_string_count,
  COUNT(*) FILTER (WHERE monteur IS NOT NULL AND monteur <> '' AND NOT EXISTS(
    SELECT 1 FROM public.workers w WHERE w.id = public.arbeitsscheine.monteur
  )) as orphan_with_value_count
FROM public.arbeitsscheine;
```

Sebastian pastet Output hier:

```
[Sebastian füllt aus nach Query-Ausführung]
```

---

## Step 2 · Kategorisierungs-Logik

Nach Output-Review fällt jede der 12 Rows in eine dieser 4 Kategorien:

| Kategorie | Merkmal | Aktion |
|---|---|---|
| **A · EMPTY_STRING** | `monteur = ''` (leer aber nicht NULL) | UPDATE SET monteur = NULL |
| **B · WORKER_ID_PATTERN** | `monteur` matcht `w1..w99`, aber Worker-Row fehlt | Ex-Monteur, Worker mit `aktiv=false` wiederanlegen |
| **C · JUPROWA_CODE** | `monteur` matcht Juprowa-Pattern `P001..P099` | Auto-Match in `_juprowaDynMap` fehlte — manuell mappen oder leaveen |
| **D · UNKNOWN** | beliebiger Free-Text | Sebastian einbinden |

---

## Step 3 · Staging-SQLs (NICHT ausführen ohne Sebastian-Entscheidung)

### Action (a) · Empty-String → NULL (safe)

```sql
-- Nur wenn Step 1 zeigt: alle 12 sind EMPTY_STRING
BEGIN;
UPDATE public.arbeitsscheine
SET monteur = NULL
WHERE monteur = '';
-- Commit erst nach COUNT-Check:
-- SELECT count(*) FROM public.arbeitsscheine WHERE monteur = '';  -- muss 0 sein
COMMIT;
```

### Action (b) · Ex-Worker wiederanlegen als aktiv=false

**Voraussetzung**: Step 1 zeigt z.B. `[WORKER_ID_PATTERN:w4]` → Sebastian bestätigt dass w4 der historische Monteur war.

```sql
-- Beispiel für w4 (Sebastian passt UUID/Name an)
BEGIN;
INSERT INTO public.workers (id, name, aktiv, created_at)
VALUES ('w4', '[ORIG-NAME]', false, NOW())
ON CONFLICT (id) DO NOTHING;
-- FK der 12 Rows bleibt jetzt intakt, Ex-Monteur historisch sichtbar.
-- Chef-Seite v2 Sorgenkind-Widget zeigt ihn nicht mehr als Orphan.
COMMIT;
```

Pro Ex-Worker 1× Insert. Name aus historischem Kontext (ggf. aus `activity_log` extrahierbar: `SELECT DISTINCT user_id, details FROM activity_log WHERE details LIKE '%w4%' LIMIT 5;`).

### Action (c) · Juprowa-Code ohne worker-Match

```sql
-- Beispiel: monteur='P011' aber _juprowaDynMap hat kein Mapping für P011
-- Option 1: Auto-Mapping jetzt manuell in Frontend setzen (localStorage.epkolar_juprowa_wmap)
--           dann nächster Juprowa-Pull resolved es
-- Option 2: monteur = NULL setzen (verliert historische Info)
-- Option 3: Synthetischen Worker "JUPROWA-P011" anlegen als Platzhalter
--
-- Empfehlung: Option 1 (least invasive). Siehe index.html line 2175+ JUPROWA_WORKER_MAP.

-- Kein Staging-SQL — Frontend-Action.
```

### Action (d) · Gemischt oder UNKNOWN-Text

Sebastian entscheidet per Row. Kein automatisiertes SQL.

---

## Step 4 · Final-Verify (nach Aktion)

```sql
-- Nach Aktion(en): erneuter Count
SELECT count(*) as remaining_orphans
FROM public.arbeitsscheine a
WHERE a.monteur IS NOT NULL
  AND a.monteur <> ''
  AND NOT EXISTS (SELECT 1 FROM public.workers w WHERE w.id = a.monteur);
-- Erwartet: 0
```

---

## CC-Ehrlichkeit

Ohne Supabase-DB-Zugriff kann CC die 12 Rows nicht sehen. Die obige Staging-SQL
ist eine **Matrix** über alle 4 Kategorien — Sebastian selektiert basierend auf
echtem Query-Output.

Historische Context-Hinweise (aus Code + Memory):
- `workers.id` Format: `w1..w9` (siehe `JUPROWA_WORKER_MAP` in index.html:2175)
- `u4` ist historischer Monteur, worker-Mapping `P024 → w2`
- Juprowa-Codes haben `P0xx`-Format
- `JUPROWA_RETIRED=['P002','P006']` — diese sind bekannt ausgeschieden

Wenn Step 1 zeigt `monteur IN ('P002','P006')`: Action (b) mit `aktiv=false`.
Wenn Step 1 zeigt `monteur IN ('w4', ...)`: dito.
Wenn Step 1 zeigt Free-Text-Namen: Action (d).

---

## Follow-Up

Nach Sebastian's Query-Run + Entscheidung: separater Commit
`v3.8.19-wip 12-orphan-arbeitsscheine resolved (N rows)` mit echtem
Resolution-SQL im File.
