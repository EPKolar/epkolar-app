# Bug-Hunt Report · Tag 1 · 2026-04-28 (Mo)

**Baseline:** `c0523f5` (v3.8.42 LIVE).
**Modus:** Pure Doku, kein Code-Touch (H1).
**Methodik:** 7 grep-basierte Kategorien + Snippet-Analyse + Severity-Matrix.

## Severity-Matrix

| Sym | Bedeutung |
|---|---|
| 🔴 **kritisch** | Datenverlust / Auth-Bypass / Crash bei normaler Nutzung |
| 🟠 **hoch** | Crash bei Edge-Case, Permission-Lücke, Race-Risk |
| 🟡 **mittel** | UX-Hitch, Memory-Drift, Inkonsistenz |
| 🟢 **niedrig** | Style, Doku-Lücke, Konventions-Bruch |

---

## Sektion 1 · Syntaktische Auffälligkeiten

### S1.1 · Kein TODO/FIXME/HACK/XXX/BUG · 🟢
- **Befund:** `grep -nE '\b(TODO|FIXME|HACK|XXX|BUG)\b' index.html` → 0 echte Treffer (nur Dummy-Hex in BIC-Strings).
- **Bewertung:** Code ist erstaunlich marker-frei. Bedeutet aber NICHT bug-frei — nur dass keine alten Notizen vergessen wurden.

### S1.2 · 32 `console.log`-Calls · 🟢
- **Verifikation v3.8.39 Block-D-Audit:** alle in Dev-Helpers (`window._selfTest`, `_a11yCheck`, `_perfBench`, etc.) oder via `dlog`-DEBUG-Gate. Keine Production-Noise.
- **Fix-Schätzung:** 0 min (keine Aktion).

### S1.3 · Magic-Numbers für Zeit-Konstanten · 🟡
- **Lines:** 370, 498, 903, 4177, 4184, 7195-7196 (8 Vorkommen)
- **Snippet (498):** `if(diff<60)return 'gerade eben';if(diff<3600)return ...if(diff<86400)return ...if(diff<604800)return ...`
- **Schätzung:** 30 min (TIME-Konstanten extrahieren: SECOND=1000, MINUTE=60_000, HOUR=3_600_000, DAY=86_400_000, WEEK=604_800_000)
- **Blast:** zentral verwendet, leicht zu konsolidieren ohne UI-Impact.

---

## Sektion 2 · Null/Undefined-Crashes

### S2.1 · 51 `JSON.parse`-Calls (gemischt try/no-try) · 🟠
- **Vollständige Liste:** `grep -nE 'JSON\.parse\(' index.html` → 51 Hits.
- **Stichprobenanalyse v3.8.32 Iter-19:** ein Anteil ist defensive-wrap (siehe L1616, L1633, L1638, L1656, L1674 Fahrzeug/Werkzeug-Korrupt-Handling). Andere wie L1088 (JWT-Parse), L1106, L4161 sind in äußerem try/catch.
- **Risiko-Hits:** L7242 `JSON.parse(d.data||"{}")` — falsy fallback, OK; L8716/8756 `JSON.parse(JSON.stringify(...))` deep-clone, OK.
- **Empfehlung:** Helper `_safeJsonParse(s, fallback)` einführen, schrittweise migrieren.
- **Fix-Schätzung:** 1-2 h für Helper + 50 Stellen.
- **Blast:** Helper-Refactor, niedrige Regressions-Chance bei zentraler Definition.

### S2.2 · `users[0].password_hash`-Deref vor Length-Check · 🟠
- **Line:** 1881: `let valid=false;try{valid=dcodeIO.bcrypt.compareSync(oldPw,users[0].password_hash);}catch(e){}`
- **Voraussetzung:** L1877 prüft `if(!users[0].password_hash)throw` davor → effektiv geschützt.
- **Aber:** L1873 `if(!users||!users.length)throw new Error("User not found");` ist die echte Vor-Bedingung. Annotation wäre Wert.
- **Fix:** 5 min Inline-Comment.

### S2.3 · OFFA-PDF-Datum-Parser ohne Fallback · 🟡
- **Line:** 2677: `const dp=mDt[1].split(".");if(dp.length===3){const yr=dp[2].length===2?(parseInt(dp[2])>50?"19":"20")+dp[2]:dp[2];r.aufgenommen=yr+"-"+dp[1].padStart(2,"0")+"-"+dp[0].padStart(2,"0");}`
- **Risiko:** Wenn `dp[2]` non-numeric, `parseInt` returns NaN → "20"+dp[2] anyway, aber `padStart` auf undefined würde crashen. dp[1] und dp[0] sind dadurch geschützt.
- **Fix:** explizite NaN-Behandlung oder Regex-strict; 15 min.

### S2.4 · SpeechRec onresult ohne onError-Fallback · 🟡
- **Line:** 3246: `rec.onresult=e=>{const t=e.results[e.results.length-1][0].transcript;...}`
- **Risiko:** Wenn `e.results` leer (race-condition bei Speech-Cancel), Zugriff auf `[length-1][0].transcript` crash.
- **Fix:** Length-Guard + early-return, 5 min.

---

## Sektion 3 · Permission-Gaps

### S3.1 · `deleteNotif` ohne Admin/Owner-Check · 🟢
- **Line:** 4296: `const deleteNotif=id=>{setNotifications(p=>{const upd=p.filter(n=>n.id!==id);ODB.save("notifications",upd);return upd;});SQ.push({url:"/api/notifications/"+id,method:"DELETE"});};`
- **Bewertung:** Notifications sind user-scoped (RLS schützt). Kein Code-Bug.

### S3.2 · `delE` (Regie-Eintrag) ohne Admin-Check · 🟢
- **Line:** 8820: `const delE=i=>{if(!confirm(...))return;...SQ.push({url:"/api/forms/"+saved[i].id,method:"DELETE"});}`
- **Bewertung:** Eigene Forms — RLS B-007 Policy schützt.

### S3.3 · `deleteLayer` (Plan-Layer) ohne Guard · 🟡
- **Line:** 9341: `const deleteLayer=id=>setPlanData(prev=>({...prev,layers:prev.layers.filter(l=>l.id!==id)}));`
- **Befund:** Lokaler State-Filter, kein SQ.push. Vermutlich UI-only (Layer ohne DB-Persistenz).
- **Risiko:** Wenn Layers später persistiert werden, fehlt Permission-Check. Kommentar wäre wert.
- **Fix:** 5 min Inline-Note "UI-only, keine DB-Persistenz".

### S3.4 · `delFolder` (Folder-Delete) — H1-Zone? · 🟡
- **Line:** 10163: `const delFolder=(id)=>{...}` — nicht voll inspiziert (off-screen).
- **Empfehlung:** Manueller Re-Audit in nächster Code-Session.

### S3.5 · `delPhoto` async ohne canDo · 🟡
- **Line:** 9970: `const delPhoto=async(ph)=>{...}` — nicht voll inspiziert.
- **Empfehlung:** prüfen ob `canDo("doc_delete", curUser)` davor steht oder fehlt.

---

## Sektion 4 · Async-Race-Conditions

### S4.1 · 108 `useEffect`-Calls — Cleanup-Anteil unklar · 🟡
- **Befund:** `grep -nE "useEffect\.call\(void 0,\s*\(\)" index.html | wc -l` → 108.
- **Methode-Limit:** Pure-Grep kann nicht prüfen ob jedes useEffect ein `return ()=>{}` hat. Ein AST-Scan wäre nötig.
- **Spot-Check:** L3767 (LastSync-Tick), L4097 (Heartbeat), L4195 (AutoNotifs), L7246 (LiveKpis), L7253 (now-Tick) → alle haben `return()=>clearInterval(...)`. Gut.
- **Risk-Pattern (Beispiel L3400):** `useEffect(()=>{if(!navigator.onLine)return;let active=true;(async()=>{...})();return()=>{active=false;};},[maengel.length])` — has cleanup ✓.
- **Fix-Schätzung:** Tiefen-Audit 2-3 h, Findings dann gezielt fixen.

### S4.2 · 2 setInterval ohne sichtbaren Cleanup · 🟠
- **L2458** `_juprowaSyncTimer=setInterval(...,300000)` — module-level Timer, hat `_juprowaStopAutoSync()`-Wrapper, wird beim Logout gecleart? **NICHT verifiziert** (Logout-Handler L4337 tut das nicht — `_juprowaStopAutoSync` nicht im `delete window._sb*`-Block).
- **L3851** `swUpdateTimer.current=setInterval(()=>reg.update(),60000)` — ref-basiert, useEffect-Scope. Cleanup im selben useEffect?
- **Risiko:** Wenn _juprowaSyncTimer beim Logout läuft und neuer User einloggt → mit altem Token-Pfad.
- **Fix:** v3.8.30+ hat `_juprowaSyncing`-Mutex, der schützt vor Race. Aber sauberer: explizit beim Logout stoppen.
- **Fix-Schätzung:** 5 min `_juprowaStopAutoSync()` in logout (L4337) ergänzen.
- **Blast:** niedrig, isolierte Funktion.

### S4.3 · `addEventListener`/`removeEventListener` Δ=2 · 🟡
- **Befund:** 15 add vs 13 remove. 2 potentielle Listener-Leaks bei Komponenten-Unmount.
- **Fix-Schätzung:** Zuordnung 30 min, Cleanup 15 min/Hit.

---

## Sektion 5 · Resource-Leaks

### S5.1 · `URL.createObjectURL` (5×) vs `revokeObjectURL` (3×) · 🟠
- **Add-Sites:** L328 (boot-debug), L2000 (PDF-Open), L2876 (Excel-Download), 2× nicht im Sample.
- **Revoke-Sites:** L2000 (60s-timeout-revoke), 2 weitere.
- **Lücke:** L328 Boot-Debug-JSON → wird nie revoked (nur einmalig, akzeptabel). L2876 Excel-Download → vermutlich never-revoked (Browser GC bei window.close). Akzeptabel für Single-Page-App-Lebenszyklus.
- **Fix-Schätzung:** 0 min (akzeptiert) oder 30 min (defensive revoke nach 60 s wie L2000-Pattern).
- **Blast:** marginal, nur Memory bei sehr langen Sessions.

### S5.2 · No EventSource/WebSocket-Usage · 🟢
- **Befund:** `grep` für `new EventSource\(|new WebSocket\(` → 0 Treffer. Kein Real-Time-Push-Channel.
- **Bewertung:** Stattdessen Polling-basiert (5-Min Auto-Sync). Kein Cleanup-Risk.

### S5.3 · Polling-Timer beim Logout nicht alle gestoppt · 🟡
- Siehe S4.2. `_juprowaStopAutoSync` + diverse Timer im Logout-Handler nicht aufgeführt.
- Cumulativer Logout-Cleanup-Audit wäre wert (eigene Session).

---

## Sektion 6 · Offline/Sync-Risiken (READ-ONLY per H1)

### S6.1 · `SQ.push` (122×) — UUID-Generierung in Queue · 🟢
- **Befund:** `SQ._serial(async()=>{const q=await ODB.load("syncQueue")||[];q.push({...action,id:Date.now()+"_"+Math.random().toString(36).slice(2),ts:...});...})` — Server-Side oder Client-Side ID-Schema mit Date.now+Math.random.
- **Bewertung:** Pseudo-UUID-Schema ist NICHT collision-proof bei high-rate-pushes (~ms-precision + 30bit Random ≈ 10⁹). Aber per `_serial`-Mutex serialisiert → realistisch keine Kollision.
- **Risk-Level:** niedrig.

### S6.2 · `navigator.onLine`-Patterns (10+ Vorkommen) · 🟡
- **Lines:** 1940, 2104, 2138, 2180, 2459, 2631, 3400, 3421, 3647, 3690.
- **Bewertung:** Alle defensive (return early bei offline). Konsistentes Muster.
- **Risk:** `navigator.onLine` ist false-positive-anfällig (zeigt true bei "verbunden mit lokalem WLAN ohne Internet"). Echte Verfügbarkeit wäre nur durch Probe-Request testbar.
- **Mitigation existiert:** `_authRetry` fängt 401, fetch-Failures landen in Catch. OK.

### S6.3 · OFFLINE-Login-Pfad (L3647-3690) · 🟢
- Verwendet `_OFFPW.verify` (PBKDF2 v3.8.33). Keine bekannten Issues.

---

## Sektion 7 · UI-Inkonsistenzen

### S7.1 · Spinner-Patterns konsistent · 🟢
- **Befund:** Nur `ep-spin` + `ep-spin-sm` (CSS-basiert seit v3.8.28). Keine `<img src="spin.gif">`-Alt-Reste, keine inkonsistenten Animations-Klassen.
- **Bewertung:** Sehr clean. Keine Aktion.

### S7.2 · Toast/Alert/Confirm gemischt · 🟡
- **Befund:** 46× `window.__toast(...)` (info/success), aber nativen `confirm(...)`-Dialog für destructive ops (deleteAs L5163, storno L5140, deleteP L8009, delMonteur L4890, delUser L6401, delE L8820, delM L9020, deletePlan L9327, deleteTicket L9337, delPhoto, delFolder, ...).
- **Bewertung:** native `confirm()` ist UX-suboptimal (Browser-Modal statt App-Modal mit EP-CI), aber **funktional konsistent** (alle destructive ops haben Bestätigung).
- **Empfehlung:** Modal-Helper `_confirmModal(title, body)` als Alternative. Migration optional, low priority.
- **Fix-Schätzung:** Helper 30 min, Migration 1 h.

### S7.3 · Tab-Statuswechsel nutzt setKat()-Variante · 🟢
- Spot-Check: konsistent.

### S7.4 · Modal-Pattern (Edit-AS, Edit-Form, ...) · 🟡
- Vermutlich verschiedene Inline-`<div style={{position:fixed,...}}>` ohne extrahierten Modal-Component.
- **Empfehlung:** `Modal`-Component mit Standard-Header+Body+Footer extrahieren.
- **Fix-Schätzung:** 2 h Refactor.

---

## Zusammenfassung

| Sektion | Findings | Davon hoch+ |
|---|---:|---:|
| S1 Syntaktisch | 3 | 0 |
| S2 Null/Undefined | 4 | 2 |
| S3 Permission | 5 | 0 |
| S4 Async-Race | 3 | 1 |
| S5 Resource-Leaks | 3 | 1 |
| S6 Offline/Sync | 3 | 0 |
| S7 UI-Inkonsistenzen | 4 | 0 |
| **Total** | **25** | **4** |

Plus aus früheren Audits (Block D Overnight #1+#2):
- 154 `<label>` ohne `htmlFor` → A11Y_AUDIT.md (P2)
- 0 von 264 Inputs mit `id` → ditto
- ~50 Icon-only-Buttons ohne `aria-label`
- 4 Pull-Only-Felder im Push-Race (RE_ADR_*, AK_BAUADR_NUMMER) — jetzt v3.8.41 gefixt
- COLORS-Hex 562 Vorkommen → DUPLICATE_STRINGS.md
- Token-Key-Duplikate (`epkolar_auth` + `_token` + `_refresh`)

**Summe inkl. älterer Findings: 50+ Items.**

## Top-3-Fix-Empfehlungen für Sebastian

1. **S4.2** `_juprowaStopAutoSync()` im Logout (5 min, isoliert) — verhindert Token-Race nach User-Wechsel.
2. **S2.1** `_safeJsonParse(s, fallback)` Helper + Migration (1-2 h) — eliminiert 51 potentielle Crash-Sites.
3. **S7.2** Modal-`_confirmModal`-Helper (30 min + 1 h Migration) — UX-Konsistenz für destructive ops.

## Out-of-Scope für diese Woche (H1-Zone)

- `_juprowaPush`/`_juprowaSync` Modifikationen
- Auth-Path Touch
- SyncQueue-Änderung
- Schema-Migration (z. B. für separate Rechnungsadress-Spalten)

Diese Items in Sebastian-Session nach Urlaub einplanen.
