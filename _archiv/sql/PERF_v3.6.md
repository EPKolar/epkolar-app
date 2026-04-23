# Performance-Empfehlungen v3.6.0 · Block 10 Audit

## Status-Quo (v3.5.195)
- `React.memo` aktuell 0x verwendet — KEINE Listen-Items memoisiert
- `_react.useMemo.call(void 0, ...)` 8x verwendet (Chef-Dashboard stats, kwMon, weekEntries, etc)
- `_react.useCallback.call(void 0, ...)` 15x verwendet (doSync, toggleTheme, etc)

## Messungen (via window._measurePerf)
Sebastian kann `await window._measurePerf()` in Console laufen und sieht:
- workers_ms, as50_ms, articles_ms, notif_ms
Referenz-Werte (Good Laptop + Austrian-DSL): < 500ms pro Query.

## Top-Empfehlungen (nicht automatisch angewendet — Sebastian prüft pro Komponente)

### A) React.memo auf Listen-Zeilen
Kandidaten:
- **ArbeitsscheinView** Liste — jede Row ist eine inline `React.createElement('div', {onClick, ...})`. Bei 100+ AS teurer Re-render bei jedem setState.
- **ProjList** Tile-Karten — ähnlich.
- **MitarbeiterView** Zeilen.
- **WerkzeugView** Zeilen.
- **FahrzeugView** Zeilen.
- **Supplier-Articles-Liste** (25k rows, virtualized).

Muster:
```js
const ASRow=React.memo(function ASRow({as,onClick}){
  return React.createElement('div',{onClick,style:{...}},...);
});
```

Nur sicher wenn die Props stabil sind. Props mit Inline-Objekten `style:{margin:8}` verhindern memo-Hit. → zuerst Props stabilisieren (via useMemo in Parent oder constants).

### B) useMemo für teure Filter/Sortierung
Kandidaten:
- `filtered=arbeitsscheine.filter(...).sort(...)` in ArbeitsscheinView (Line ~4300) — läuft bei jedem Re-Render, auch wenn nur Input-Text sich ändert und Liste invariant ist.
- `monatsGrouped=entries.reduce(...)` in Stundenzettel.
- `supplier_articles.filter(txt-match)` in Material-Dialog — 25k Rows!

Muster:
```js
const filtered=_react.useMemo.call(void 0, ()=>
  arbeitsscheine.filter(a=>a.scheinstatus===filter).sort(...),
  [arbeitsscheine,filter,sortBy]
);
```

### C) useCallback für Event-Handler die in memoized Rows landen
Sobald A) gemacht ist, müssen onClick-Handler für Row-Komponenten via useCallback stabilisiert werden, sonst memo wirkungslos.

### D) IndexedDB-Batch-Queries
ODB.load() einzeln 15x bei App-Start (Line 3225-ish — initial load useEffect). Parallelisierung via Promise.all bereits done. Nicht weiter optimierbar ohne Schema-Änderung.

### E) SQ.getAll() wiederholt aufgerufen in doSync
Optimierung: cache queue-snapshot zwischen Ops. Minimal value — doSync läuft max 1x/1.5s.

## Entscheidung für v3.6.0
**Keine der obigen Änderungen angewendet**, nur Dokumentation. Gründe:
1. React.memo ohne Props-Stabilisierung ist nutzlos oder kontraproduktiv
2. Risiko von Stale-Closure wenn useCallback-Deps vergessen werden
3. Block 3 hat bereits 146 setState-Stellen functionalized → Halbzeit-Check im Real-Betrieb erwünscht bevor weitere Refactor-Welle

**Sebastians Entscheidung**: wenn User echte Perf-Issues melden (Listen-Scroll-Lag, Tab-Switch > 500ms), dann gezielt A/B/C anwenden. Vorher nicht.
