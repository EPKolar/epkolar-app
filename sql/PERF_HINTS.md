# Perf-Profiling-Hints v3.7 · Block 17

## Workflow für Sebastian

### Quick-Check: DB-Query-Latenz
```js
// In Browser-Console als eingeloggter User:
await window._perfBench()
```
Liefert Tabelle mit ms-Dauer für 9 typische Queries. Referenz:
- **< 500 ms pro Query**: gut
- **500-1000 ms**: Index-Kandidat prüfen
- **> 1000 ms**: wahrscheinlich full-table-scan, Index dringend

Wenn Werte schlecht: `sql/INDEX_AUDIT_v3.7.sql` im Supabase SQL-Editor ausführen, dann `_perfBench()` nochmal.

### Deep-Profiling: Chrome DevTools Performance
1. Chrome → F12 → Performance-Tab
2. Record
3. 30 s typische User-Interaktion (AS öffnen, filtern, scrollen, neuer Eintrag)
4. Stop
5. "Long Tasks" (>50 ms) Liste: welche sind systemisch?
6. Flame-Graph: welche Komponenten rendern am häufigsten?

### React-Profiler (wenn React-DevTools installiert)
1. DevTools → Profiler-Tab
2. Record
3. Typische Aktion
4. Stop
5. Top-5 "renders" ansehen — besonders Listen wo React.memo fehlen

## Bekannte Verdächtige

### VERDICHTUNG der Liste aus sql/PERF_v3.6.md

1. **AS-Liste** (`ArbeitsscheinView`): 500+ Einträge, jede Zeile ist inline-`React.createElement` ohne memo. Jeder unrelated setState triggert full re-render.
   - v3.6.13 Teil-Fix: `filtered`+`sorted` in `useMemo` gewrappt (Block 11)
   - Offen: Row-Components in React.memo + Parent-useCallback für Props-Stabilisierung

2. **supplier_articles** (25k+ Rows): Material-Dialog-Search ohne Debounce. Jeder Keystroke triggert `.filter(ilike)` auf 25k Rows.
   - Workaround: mit v3.6.14 `ix_sa_fts_german` GIN-Index → ilike ist schneller
   - Besser: 200ms-Debounce auf Search-Input

3. **Chef-Dashboard**: lädt 15+ Queries sequentiell (useEffect chain). Total ~3-5s First-Paint auf Monteure-iPhone.
   - Workaround: `Promise.all([_sbGet(...), _sbGet(...), ...])` Parallelisierung
   - Bereits teilweise via `fetchStats` (Line 5644) parallelisiert, aber ChefDashboard hat weitere

4. **AS-Modal Open**: rendert komplettes Formular + Signaturen + Photo-Grid. iPad-Pro 200-400ms.
   - Lazy-Load Photo-Grid (nur bei View-Scroll)
   - Signatur-Pads erst bei Klick mounten

5. **Werkzeug-Liste** (~300 Einträge): inline Row-Renderer, kein memo.

## Sebastian-Action-Liste (nach Perf-Test)

1. `_perfBench()` laufen (Baseline vor Index-Deploy)
2. SQL-Files ausführen (`INDEX_AUDIT_v3.6.sql` + `INDEX_AUDIT_v3.7.sql`)
3. `_perfBench()` erneut (sollte Verbesserung zeigen, besonders `AS-Suche-kundName` + `Artikel-FTS`)
4. pg_stat_user_indexes Query (Monitoring-SQL am Ende von INDEX_AUDIT_v3.7.sql) nach 1-2 Tagen Betrieb — unused indices droppen
5. Bei sichtbarer Lag: DevTools Performance-Record, top-Long-Tasks fixen

## Nicht applied in v3.7 (Backlog)

- React.memo auf Listen-Rows (braucht Props-Stabilisierung via useCallback)
- Virtualisierung für 500+ AS-Liste und 25k supplier_articles (react-window oder custom)
- Code-Splitting (Tab-Lazy-Load per dynamic import)
- IndexedDB statt localStorage für cart/filter-state (larger payloads)

Alle davon sind größere Refactors. Sebastian entscheidet wenn User echte Perf-Complaints melden.
