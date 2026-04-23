# Bug Hunt Round 2 — v3.8-Diff Review · Block 16

Basis: `git diff 879c535..HEAD` · 264 Zeilen hinzugefügt, 30 geändert. Fokus nur auf neu/geänderten Code dieser Session.

## Gescannte Änderungen

### B-020 Code-Fix (v3.6.3 — Block 1 der vorherigen Session, jetzt v3.7.3 hier)
- Bereits in v3.7.3 Block 2 als M-1 (NOT A BUG) re-evaluiert.
- Keine neuen Code-Änderungen in diesem Run.

### _selfTest (v3.7.4)
**Finding R2-01 P3**: `try{localStorage.setItem('selftest_last_run',JSON.stringify({summary,results}))}catch(_){}` — wenn Quota voll, silent-swallow. Nicht Bug, bewusst.

**Finding R2-02 P3**: `step()` catcht alle Exceptions. Wenn ein Helper z.B. Promise-rejected ohne error.message, steht `err:'undefined'`. Kosmetik.

### _forceExpireToken / _restoreToken (v3.7.7)
**Finding R2-03 P2**: `_forceExpireToken` überschreibt `obj.at` im localStorage. Das module-level `_authToken` in Closure bleibt jedoch die frische Version (wurde bei Login gesetzt, wird erst durch `_restoreAuth` aus localStorage gelesen). → `_forceExpireToken` ist **wirkungslos** wenn `_authToken` schon in JS-Memory ist und `_sbH()` aus closure liest.
  - **Mitigation**: Module-level `_authToken=null` setzen zusätzlich? Nur möglich via direkte `window._authToken` — existiert aber nicht (v3.5.177 B-017 Admin-Gate entfernte das).
  - **Alternative**: Reload nach _forceExpireToken damit _restoreAuth aus localStorage liest.
  - **Status**: RE-INVESTIGATE bei Block 7 `_thunderTest` Sebastian-Run. Wenn Thundering-Herd-Test immer NO REFRESH liefert → diese Theorie bestätigt.

### _thunderTest (v3.7.8)
**Finding R2-04 P2**: Nutzt `window.fetch=async function(){...}` Wrapping. Wenn ein async _sbGet-Call JETZT läuft und dazwischen fetch-wrap kommt → das eine Promise benutzt noch origFetch. Shouldn't matter da wir `await Promise.all` abwarten, aber: wenn `visibilitychange`-handler parallel `_sbAuthRefresh` triggert (Line 636+), umgeht das den Counter.
  - **Status**: hypothetisch — in Test-Kontext wird Tab aktiv bleiben (Sebastian schaut ja auf Console).

### _a11yCheck (v3.7.15)
**Finding R2-05 P3**: Input-Check akzeptiert `placeholder` als label-Äquivalent. Screen-Reader-Standard sagt: placeholder ist KEIN label (verschwindet bei input). 
  - **Mitigation**: Strenger-Modus `_a11yCheck({strict:true})` der placeholder nicht als label zählt.
  - **Status**: Doku-only (kein Fix — Standard-Modus ist für Quick-Scan ausreichend).

### _syncDiag (v3.7.16)
**Finding R2-06 P3**: `q.ts` Datumsparse kann failen (wenn ts ungültig). `new Date('garbage').getTime()` → NaN → `(now-NaN)=NaN` → alle Buckets under1min.
  - **Mitigation**: `const created=q.ts?new Date(q.ts).getTime():null; if(!created||isNaN(created))byAge.under1min++; ...`
  - **Status**: Kosmetik — passiert nur wenn DB korrupt. Nicht fixen.

### Block 6 _forceExpireToken Guard
**Finding R2-07 P3**: localStorage.__dev='1' Check ist clientseitig → kein Security-Fence gegen Angreifer mit DevTools-Zugriff. Aber: das ist nur Dev-Helper, **nicht** security-kritisch.

## Zusammenfassung Round 2

| # | Finding | Prio | Status |
|---|---|---|---|
| R2-01 | _selfTest localStorage quota swallow | P3 | ACCEPTED (bewusst) |
| R2-02 | step() err.message undefined | P3 | Cosmetic |
| R2-03 | _forceExpireToken wirkungslos wenn _authToken im JS-Memory | P2 | **RE-INVESTIGATE** nach _thunderTest-Lauf |
| R2-04 | _thunderTest window.fetch wrap Race mit visibilitychange | P2 | Hypothetisch |
| R2-05 | _a11yCheck placeholder=label | P3 | Doku |
| R2-06 | _syncDiag NaN-Date | P3 | Cosmetic |
| R2-07 | _forceExpireToken __dev-Guard clientseitig | P3 | Not-A-Bug (Dev-Helper) |

**0 echte P1-Findings in der v3.8-Diff**. R2-03 ist der interessanteste — sollte in nächster Session mit Sebastian verifiziert werden.
