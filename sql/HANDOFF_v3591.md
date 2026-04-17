# EPKolar HANDOFF — Stand 17.04.2026 ~21:50
## v3.5.88 → v3.5.94 + B-006 ✅ CLOSED + B-007 ✅ CLOSED

App-URL: https://epkolar.github.io/epkolar-app/ · Live-HEAD: v3.5.94 (bbbefa9 + nachfolgende Docs-Commit)

---

## 1. B-007 Monteur-RLS — ✅ CLOSED

**Ausgeführt via Browser-Chrome-MCP am 17.04.2026 ~21:50** (Supabase SQL-Editor, Tab 1454480885).

**DB-Verifikation (live-bestätigt):**

| Check | Soll | Ist | ✅ |
|-------|------|-----|----|
| Helper-Funktionen | 4 | 4 | ✅ |
| B-007 Policies gesamt | ≥16 | **22** | ✅ |
| RLS-enabled ohne Policy | 0 | 0 | ✅ (B-006b hat nachgezogen) |
| arbeitsscheine (read+write) | 2 | 2 | ✅ |
| time_entries (read+write) | 2 | 2 | ✅ |
| notifications (insert+r+u+d) | 4 | 4 | ✅ |
| urlaubsantraege (r+i+u+d) | 4 | 4 | ✅ |
| fahrtenbuch (r+w) | 2 | 2 | ✅ |
| as_checklist (r+w) | 2 | 2 | ✅ |
| as_kommentare (r+i+u+d) | 4 | 4 | ✅ |
| worker_kompetenzen (r_all+w_admin) | 2 | 2 | ✅ |

**Helper-Funktionen live:**
- `current_monteur_id()` → `u.monteur_id` (text, SECURITY DEFINER STABLE)
- `current_user_role()` → `u.role`
- `current_user_pk()` → `u.id` (text)
- `is_staff()` → role IN ('admin','projektleiter','buero')

**Cleanup:** Alt-Policies (auth_all, authenticated_read, role_filtered_as, etc.) via Cleanup-DO-Block gedroppt, danach 22 finale Policies erzeugt.

---

## 2. B-006 Anon-Block — ✅ CLOSED

Alle zuvor offenen Tabellen haben jetzt `authenticated_read_*` + `authenticated_write_*` Policies. `rls_zero_left=0` heißt: es gibt keine Tabelle mehr mit `rowsecurity=true` aber null Policies.

**DB-State:**
- 25121 supplier_articles — anon=0, authenticated liest alles
- users, projects, project_documents — RLS an + Policies ✅
- supplier_configs, material_items, material_orders, bautagebuch — ✅

---

## 3. Smoke-Test-JS (pending, für dich in Browser-Console)

**Als schober (schober/test1234):**
```js
(async()=>{
  const U=window.SUPABASE_URL||"https://jiggujpruejkaomgxarp.supabase.co";
  const H=window._sbH();const tests=[];
  for(const [n,p] of [
    ["AS eigene",          "/rest/v1/arbeitsscheine?select=id,monteur"],
    ["ZE eigene",          "/rest/v1/time_entries?select=id,worker_id"],
    ["Notif eigene",       "/rest/v1/notifications?select=id,user_id"],
    ["Fahrtenbuch eigene", "/rest/v1/fahrtenbuch?select=id,worker_id"],
    ["Urlaub eigene",      "/rest/v1/urlaubsantraege?select=id,worker_id"],
    ["Kompetenzen alle",   "/rest/v1/worker_kompetenzen?select=id"],
  ]){const r=await fetch(U+p,{headers:H});const d=await r.json();
     tests.push({n,count:Array.isArray(d)?d.length:"ERR",sample:Array.isArray(d)&&d[0]?JSON.stringify(d[0]).slice(0,80):"—"});}
  console.table(tests);
})();
```

**Erwartung Schober:** Nur eigene IDs in monteur/worker_id/user_id-Feldern; Kompetenzen alle lesbar.

**Erwartung Admin:** AS=54, ZE alle, Notif nur eigene, Kompetenzen alle.

**Erwartung Riedmann** (hat keine AS zugewiesen): `AS count=0`.

---

## 4. Bug-Fix-Sprint v3.5.88 → v3.5.94

### Null-Safety-Pack (v3.5.89 → v3.5.93)
- v3.5.89 Header `curUser.name.split()` + Timer `Math.max(0,hours)`
- v3.5.90 6× null-safe `.toLowerCase()` (Search, Timer-Prompt, ProjektView, AS-Dup-Check)
- v3.5.91 3× null-safe `.substring()`/`.slice()` (OrderList, FzBuch-Kalender, ChefDashboard)
- v3.5.92 9× null-safe (`a.nummer.replace`, `p.name.replace`, `r.bvh.trim` 6×, Bautagebuch `erstelltVon`)
- v3.5.93 5× null-safe `.localeCompare` in Sort-Callbacks

### Mobile+Perf (v3.5.94)
- TimerBanner: Idle-Poll 1s→5s (80% weniger State-Updates wenn kein Timer läuft)
- AS-Swipe: `dt<700ms` + `dy/dx<0.5` Ratio + Single-Touch-Guard
- useSwipe: Single-Touch-Guard
- iOS URL-Bar-Cutoff (100vh-Bug): 6× `100vh`→`100dvh`

---

## 5. Deployed Push-Chain

```
bbbefa9 v3.5.94 Mobile+Perf (Swipe, Timer-Idle, 100dvh)
f0c84c2 v3.5.93 5x null-safe localeCompare
d72af4b v3.5.92 9x null-safe (nummer/name/bvh/erstelltVon)
478e65d v3.5.91 3x null-safe substring/slice
c9c92ad v3.5.90 6x null-safe toLowerCase
2847fae v3.5.89 Header null-safe + Timer Math.max
1dca6f6 sql: B-006b + B-007 RLS fixes archive
```

SQL-Artefakte im Repo: `/sql/B006b_HEILUNGS_SQL.sql`, `/sql/B007_EXECUTE.sql`, `/sql/ALL_SQL_ONEPASTE.sql`, `/sql/sql-runner.mjs`, `/sql/B006b_B007_FINAL.sql` (archivierte ausgeführte Fassung).

---

## 6. Deferred Blocks (aus CC_OVERNIGHT_v3575.md)

| Block | Titel | Aufwand |
|-------|-------|---------|
| 4 | Fahrzeug-Buchungs-Kalender (mit Konflikt-Logik) | 2-3h |
| 5 | Projekt-Gantt (SVG + Drag&Drop) | 2h |
| 6 | ZE-Kalender-Wochenansicht | 2h |
| 8 | AS-Signature-Close-Flow (SignaturePad-Integration) | 1-2h |
| 9 | AS-PDF-Export v2 (echtes jsPDF statt HTML) | 2h |
| 12 | SW-Cache-Bust-Automation | 1h (riskant) |
| 13 | Audit-Log-UI (activity_log wird schon gefüllt) | 1-2h |
| 14 | Web-Push (braucht VAPID + Server-Endpoint) | 30min Skeleton / 1 Woche Prod |
| 15 | Mobile iOS-Quirks Final Pass | Echtgerät-Tests |
| 16 | Perf-Benchmark + Indizes | 1h |
| 17 | v3.6.0 Final-QS + Deploy | abhängt vom Rest |

**Empfehlung:** Als Nächstes **Block 8 (AS-Signature-Close-Flow)** — SignaturePad-Komponente existiert bereits, nur in AS-Close-Dialog integrieren, 1-2h. Oder **Block 13 (Audit-Log-UI)** — reiner Read-Pfad, kein DB-Schema-Change.

---

## 7. Offene Fragen

- **Büro-Role** (`buero`): is_staff()=true — Büro sieht alle AS/ZE. Bestätigen OK.
- **Projektleiter**: is_staff()=true — selbe Rechte wie Admin. Bestätigen OK.
- **Urlaubsantrag nach Genehmigung**: User blockiert (`status='beantragt'` Constraint in urlaub_update Policy). Bestätigen OK.
- **Portal-User**: hat keine `auth_user_id` → `current_monteur_id()` liefert NULL → sieht 0 AS. Portal-Session läuft über eigenen Flow (`portalCode`). Bestätigen OK.
