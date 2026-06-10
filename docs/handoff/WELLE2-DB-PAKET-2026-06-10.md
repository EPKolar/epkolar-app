# PlanRadar Welle 2 — DB-Paket für Chat-Claude / Sebastian

**Erstellt:** 2026-06-10 (CC, read-only-verifiziert gegen `jiggujpruejkaomgxarp`)
**Status:** VORSCHLAG — von CC **NICHT ausgeführt** (DB-Write-Stopp-Direktive). Mensch-im-Loop: Sebastian klickt Run, Chat-Claude verifiziert.

## Read-only-Befund (Ist-Zustand, verifiziert)
- `tickets` hat bereits Pin-Spalten: `x real`, `y real`, `plan_id text`, `page integer NOT NULL` → **nicht migrieren**.
- `defects` hat **KEINE** davon → das ist der einzige fehlende DB-Teil für die Mängel-Pins.
- `defects`-RLS: 4 Policies, alle `{public}` permissiv (SELECT/INSERT/UPDATE/DELETE) → spalten-scoped Pin-Writes sind **bereits erlaubt**, kein neuer RLS-Bedarf fürs Feature.
- `notifications` worker→user-Mapping: **kein DB-Bedarf**, client-seitig über `users.monteur_id` gelöst (W2.1 bereits live, v3.9.275).
- `tickets.page` / `plans.page_count`: vorhanden → nutzen, nicht migrieren.

---

## SQL — idempotent, Mängel-Pins (spiegelt tickets-Pin-Spalten auf defects)

```sql
-- PlanRadar Welle 2 — defects-Pin-Spalten. Typen exakt wie tickets (verifiziert).
ALTER TABLE public.defects ADD COLUMN IF NOT EXISTS x real;            -- Pin-X in % (0-100)
ALTER TABLE public.defects ADD COLUMN IF NOT EXISTS y real;            -- Pin-Y in % (0-100)
ALTER TABLE public.defects ADD COLUMN IF NOT EXISTS plan_id text;      -- = plans.id (wie tickets.plan_id)
ALTER TABLE public.defects ADD COLUMN IF NOT EXISTS page integer NOT NULL DEFAULT 1;  -- Plan-Seite (Multi-Page)

-- Index für Pin-Render je Plan/Seite (Performance beim Plan-Aufbau)
CREATE INDEX IF NOT EXISTS idx_defects_plan_page ON public.defects(plan_id, page) WHERE plan_id IS NOT NULL;
```

**Verifikation nach Run (read-only):**
```sql
select column_name, data_type, is_nullable
from information_schema.columns
where table_schema='public' and table_name='defects'
  and column_name in ('x','y','plan_id','page')
order by column_name;
-- Erwartung: page/integer/NO, plan_id/text/YES, x/real/YES, y/real/YES
```

---

## SEPARAT — Sicherheits-Empfehlung (KEIN Welle-2-Blocker, Chat-Claude entscheidet)

`defects_insert`/`defects_update` sind rollenlos `{public}` → ein authentifizierter Monteur kann via
SyncQueue/DevTools Status/Review-Felder frei schreiben (Client-Gate umgehbar). Details:
`docs/handoff/HUNT-2026-06-10-SERVER-RLS-NOTES.md` Punkt A1/A2.
Empfehlung: UPDATE von `kunde_status`/`review_*`/`status` auf
`current_user_role() in ('admin','projektleiter','buero')` bzw. Owner einschränken.
**Wichtig:** Die Pin-Writes (`x/y/plan_id/page`) müssen für zuweisende Rollen erlaubt bleiben — beim
Verschärfen der UPDATE-Policy die Pin-Spalten nicht mit-sperren.

---

## Nach dem Apply
CC baut dann das Client-Feature **Mängel-Pins** (VMang/defects, spiegelt das vorhandene VPlan-`PlanPin`-System:
x/y in %, Zwei-Ebenen-Pin, Counter-Scale-Zoom). Bis dahin: WARTET AUF DB.
