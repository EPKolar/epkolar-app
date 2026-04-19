# Testkonzept EPKolar v4.4 — DELTA gegenüber v4.3/v5.0

Nur das Neue. Basis `sql/Testkonzept_EPKolar_v5_0.md` bleibt gültig (die v4.x/v5.x-Namen sind historisch vermischt, inhaltlich konsistent).

## Neue Sessions 16/17/18 (8/5/3 Tests = 16 neu, Gesamt ~170)

---

## Session 16 — v3.8.0 Regression (8 Tests)

**Ziel**: Deckt alle Änderungen aus v3.7.x-v3.8.0 ab. Ausführung als admin + monteur + büro je nach Scope.

### T-160 · B020 DB-Fix verifiziert
- **Voraussetzung**: Sebastian hat `sql/B020_FIX.sql` ausgeführt (9×OK)
- **Schritt**: Als `paschinger/test1234` einloggen.
- **PASS**: Dashboard lädt, _authToken ist echter JWT (length > 200).
- **FAIL**: Toast "[B20-F]" oder Dashboard bleibt leer.

### T-161 · Photos-RLS-Fix (nach PHOTOS_RLS_FIX.sql)
- **Voraussetzung**: Sebastian hat Audit + Fix ausgeführt.
- **Schritt**: Als `paschinger` einloggen → `window._rlsAudit()`.
- **PASS**: Zeile "photos" zeigt count > 0 (eigene) aber < total_photos.
- **FAIL**: count==total (zu offen) oder count==0 (zu eng, bricht Feature).

### T-162 · Thundering-Herd Singleton
- **Voraussetzung**: `localStorage.__dev='1'`, als admin eingeloggt.
- **Schritt**: `await window._thunderTest()`.
- **PASS**: `verdict: '✅ SINGLETON OK (1 refresh)'`.
- **FAIL**: refreshCalls > 1 (Thundering-Herd) oder 0 (Refresh nie getriggert).

### T-163 · _selfTest Full-Mode grün
- **Schritt**: `await window._selfTest()` als admin.
- **PASS**: `summary.failed === 0` und alle 5 Sub-Tests durchgelaufen.
- **FAIL**: summary.failed > 0 — welcher?

### T-164 · _selfTest Security-Mode als Monteur
- **Schritt**: Als `schmid` einloggen → `await window._selfTest({mode:'security'})`.
- **PASS**: b017check PASS (nothing exposed), rlsAudit nur eigene Daten.
- **FAIL**: Leak oder unexpected failure.

### T-165 · WhatsApp Schema+Seeds deployed
- **Voraussetzung**: Sebastian hat WHATSAPP_SCHEMA + WHATSAPP_SEEDS ausgeführt.
- **Schritt**: Als admin → Browser-Console `await _sbGet('whatsapp_templates','select=name,event')`.
- **PASS**: Array mit >= 4 Templates.
- **FAIL**: Empty oder RLS-Block.

### T-166 · _forceExpireToken Dev-Helper
- **Voraussetzung**: `localStorage.__dev='1'`, als admin.
- **Schritt**: `window._forceExpireToken()` → irgendein `_sbGet`-Call → `window._restoreToken()`.
- **PASS**: Call succeeded via refresh-chain, Console zeigt `[Auth] Silent re-auth OK → request recovered`.
- **FAIL**: Call 401'd endgültig oder _restoreToken brach.

### T-167 · Index-Effekt sichtbar
- **Voraussetzung**: INDEX_AUDIT_v3.6+7 deployed.
- **Schritt**: `await window._perfBench()` als admin.
- **PASS**: AS-Suche-kundName < 500ms, Artikel-FTS-grohe < 300ms.
- **FAIL**: >1000ms = Index nicht aktiv/nicht effektiv.

---

## Session 17 — WhatsApp-Preflight (5 Tests)

**Ziel**: Sobald UI-Code in v3.9 gebaut wird, diese Tests durchziehen.

### T-170 · Template-CRUD
Create/Read/Update/Delete eines Templates als admin. Keine Fehler, keine Toast-Warn.

### T-171 · Template-Preview mit Placeholders
Body=`Hallo {{kunde}}` → Preview mit `kunde='Max'` zeigt `Hallo Max`.

### T-172 · Simulated-Send
Button "📤 Senden simulieren" → neuer Eintrag in `whatsapp_log` mit `status='simulated'`.

### T-173 · RLS: Büro sieht Templates aber nicht schreiben
Login als Büro → Template-Tabelle read-only (keine Edit-Buttons).

### T-174 · Phone-Number-Format-Validierung
Eingabe nicht-+43-Format → Client-validation-Warn, kein Submit.

---

## Session 18 — Perf-Regression (3 Tests)

### T-180 · _perfBench Baseline v3.7.0 vs v3.8.0
- Sebastian führt vor v3.8-Deploy `_perfBench` aus, speichert JSON.
- Nach Deploy (inkl. DB-Indizes) erneut.
- **PASS**: alle Queries gleich oder schneller.
- **FAIL**: eine Query >20% langsamer.

### T-181 · Index-Deploy-Effekt gemessen
- `INDEX_EFFECT_v3.8_RESULTS.md` ausgefüllt mit realen Daten aus EXPLAIN ANALYZE.
- **PASS**: ≥ 70% der Indizes in "EFFECTIVE"-Kategorie.
- **FAIL**: >30% INEFFECTIVE → DROP-Review.

### T-182 · Mobile-FPS beim Scroll
- Als Monteur im iPhone-Simulator, AS-Liste 100+ Zeilen.
- Chrome DevTools → Performance → record 10s scroll.
- **PASS**: FPS konstant ≥ 50.
- **FAIL**: FPS <40 → React.memo Kandidaten prüfen.

---

## Delta-Summary

| Session | Tests | Thema |
|---|---|---|
| 16 (NEU) | 8 | v3.8.0 Regression |
| 17 (NEU) | 5 | WhatsApp-Preflight |
| 18 (NEU) | 3 | Perf-Regression |

**Gesamt-Änderung**: +16 Tests. Total v4.4 ≈ 170 Tests in 18 Sessions.

**Sebastian**: Session 16 sofort nach Deploy durchführen. Session 17 erst wenn v3.9-WhatsApp-UI steht. Session 18 immer als Regression-Baseline vor jedem MAJOR.
