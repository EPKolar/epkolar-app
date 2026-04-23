# Consolidation-Sprint 19.04.2026 — Ergebnis

## Timeline (Wien-Zeit)

- **Start**: 10:53 · HEAD dbda2df · baseline grün
- **Phase A (B-017)**: 10:53 → 10:59 — **Status: v3.5.177 deployed**
- **Phase B (B-021)**: 10:59 → 11:02 — **Status: v3.5.178 deployed**
- **Phase C (B-022)**: 11:02 → 11:05 — **Status: v3.5.179 deployed**
- **Wrap**: 11:05 — ~12 Min total, 2h 48min Budget-Rest unbenutzt.

## Commits (3 + 1 Handoff, HEAD = `d1b3d8d`)

```
d1b3d8d v3.5.179 B-022 gezielt: 7 multi-setX-per-line Stale-Closure-Fixes
0cb7804 v3.5.178 B-021: Silent-Re-Auth komplett + 2nd-round-401 Detection
8378c75 v3.5.177 B-017: Window-Exposures reduziert (SB_REST/URL/KEY raus, _sbH admin-gated)
```

Baseline auf allen 3 Commits: `() -2, {} 0, [] 0` ✓ · `node --check` ✓ · GH Pages ✓.

## Kurzfassung pro Phase

### Phase A · B-017 Window-Exposures (v3.5.177)
- **CRITICAL-Credentials entfernt**: `window.SUPABASE_URL`, `window.SB_REST`, `window.SUPABASE_KEY` — bleiben jetzt Closure-privat.
- **Admin-gated**: `window._sbH`, `window._sbAuthLogin`, `window._sbAuthRefresh`, `window._silentReAuth` werden nach Login nur für Admin exposed; bei Logout wieder gecleant.
- **Utility bleibt**: 25 harmlose window-Exposures (Formatter, Events, Masking) unverändert.
- **TC-S Tests angepasst**: prüfen jetzt dass SB_REST unexposed ist, _sbH optional.
- **Inventur-Doc**: `sql/B017_INVENTORY.md` (30 Exposures kategorisiert).

### Phase B · B-021 Silent-Re-Auth (v3.5.178)
- **FINDING**: B-021 war substantiell vor Session schon implementiert. `_authRetry(fn)` (line 641) umschließt alle `_sb*` Wrappers; bei 401/403 ruft `_sbAuthRefresh()` → `_silentReAuth()` (via `epkolar_gc`) und retry.
- **v3.5.178 Strengthening**: 2nd-round-401-Detection — wenn Retry nach Re-Auth ERNEUT 401 gibt, feuert jetzt auch `_onAuthFail` (vorher silent).
- **Thundering-Herd** bereits via `_authRefreshInflight` (v3.5.112) abgesichert — 5 parallele 401s lösen nur 1 Refresh aus.
- **Success-Logging**: `console.log('[Auth] Silent re-auth OK → request recovered')` für Diagnose.
- **Verify-Doc**: `sql/B021_VERIFY.md` mit 4 Smoke-Test-Scripts + Edge-Case-Matrix.

### Phase C · B-022 Stale-Closure (v3.5.179)
- **Scope-Decision**: Von 153 non-functional `setX({...x,...})` erfüllt **0** die strikten 3-Kriterien (nach await/setTimeout/onBlur + Modal). Codebase nutzt fast ausschließlich synchrone onChange-Handler.
- **Pragmatische Alternative**: multi-setX-per-line Pattern gefixt — 7 Transformationen auf 3 Zeilen:
  - AS-Modal Line 5056: `setForm` terminBestaetigt + terminZeit
  - AS-Modal Line 5057: `setForm` terminVorschlag + terminVorschlagZeit
  - Wochenplan editEntry Line 11617: `setEditEntry` type + hours + note
- Alle: `setX({...x,f:v})` → `setX(p=>({...p,f:v}))` (semantisch identisch, safer Pattern)
- ~146 nicht-gepatchte Stellen in 5 Kategorien (A-E) dokumentiert als Backlog.
- **Patch-Doc**: `sql/B022_PATCHED.md`.

## Smoke-Test für Sebastian (alle drei, ~5 min)

### 1. v3.5.177 B-017 Exposure-Check (1 min)
F12 → Console:
```js
// Erwartung: alles undefined (geheim bleibt geheim)
console.log(
  typeof window.SUPABASE_URL,    // 'undefined'
  typeof window.SB_REST,          // 'undefined'
  typeof window.SUPABASE_KEY,     // 'undefined'
  typeof window._authToken        // 'undefined'
);

// Als Admin nach Login: Debug-Helper da
console.log(typeof window._sbH);  // 'function' (nur Admin)
```

### 2. v3.5.178 B-021 Silent-Re-Auth (2 min)
F12 → Console als eingeloggter User:
```js
// Force 401: gefälschten Token setzen
const _saved=_authToken;
_authToken='eyJhbGciOiJIUzI1NiJ9.eyJyb2xlIjoiYW5vbiJ9.fake';
const r=await _sbGet('users','limit=1');
console.log('Token changed:',_authToken!==_saved,'Result:',r);
// Erwartung: '[Auth] Silent re-auth OK → request recovered (200)' im Log
```

Siehe `sql/B021_VERIFY.md` für 4 weitere Smoke-Tests (Thundering-Herd etc.).

### 3. v3.5.179 B-022 Termin-Stale-Closure (1 min)
- AS-Modal öffnen, neuer AS
- Rapid tippen: Bestätigt-Datum (heute) → Bestätigt-Zeit (14:00) → Speichern
- **Erwartung**: beide Werte in DB korrekt (vorher theoretisch Race möglich).
- Wochenplan → Zeiterfassung → Edit-Eintrag: Typ ändern → Stunden → Notiz → Speichern — alle 3 Felder erhalten.

## Offene Punkte / Backlog

| ID | Thema | Status | Empfehlung |
|---|---|---|---|
| **B-020** | UI-Login silent-fail (schober/test1234) | P1 OPEN — Diagnose committed, wartet auf Browser-Artefakte | Sebastian liefert F12-Artefakte, dann gezielter Fix (~15min) |
| B-022-rest | ~146 non-functional setX Stellen | P3 Backlog | Bei nächster Modal-Überarbeitung mitfixen |
| B-017 rest | Weitere `window._api`, `window._allUsers` etc. | Bewusst-bleibt | Bei echter Sicherheits-Audit auditieren |

## Next Session Empfehlung

Priorität 1: **B-020 Browser-Debug + Fix** — wartet nur auf Sebastian-Artefakte, 15-25 min.

Priorität 2: **Session 8 Auth-Deep-Dive** — Test mit echtem JWT-Ablauf (>1h warten), Race gegen Close-Patch. Testbarkeit jetzt deutlich besser dank B-021 strengthening + v3.5.178 Logging.

Priorität 3: **C · Block-8 AS-Signature-Auto-Close Test in echtem Betrieb** — Sebastian soll mit echten Monteuren testen, T-149..T-153 aus `sql/HANDOFF_BLOCK8.md`.

## Tagesbilanz 19.04.2026

- **Overnight** (v3.5.163..174, 12 commits): Null-Safety, NaN-Guards, Timeouts, Tabnabbing
- **Vormittags-2h** (v3.5.175..176): Block 8 (AS-Signature-Close) + Block 13+ CSV-Export
- **Consolidation** (v3.5.177..179): B-017/B-021/B-022 konsolidiert

**Gesamt heute: 17 Commits, Version v3.5.162 → v3.5.179**. Code sehr stabil.

## Nach dem Run (Sebastian-Aktion)

**PAT rotieren** — siehe prev 2h-Handoff.

## 📌 Letzter Stand in einer Zeile

```
HEAD: d1b3d8d · v3.5.179 · 3 Phasen konsolidiert in 12min · B-017 + B-021 + B-022 LIVE · B-020 wartet auf Artefakte
```

☕ Mittagspause Sebastian.
