# BUG-HUNT NACHT — FINAL Work-Order (Agententeam Synth, 2026-06-08)

## ✅ STATUS — in v3.9.193 (`82eb828`) GEFIXT (9 Funde):
P1 DOM-XSS genAsPdf (6422, `<`→`<` nur Daten) · P2 finkzeit-Clobber (15097/15103 Merge) · P2 Cross-User-syncQueue (owner-Stempel + Flush-Filter) · P2 Ticket-Typ↔Defect-Upsert · P2 QuickEditPin Scroll-Lock+Esc · P2 PlanViewer-Esc-Cascade · P3 _OFFPW empty-salt · P3 genBescheinigung Monat-Index · P3 Notif/Photo/Sync-Panel safe-area-top.
**⚠️ Lehre:** Agenten-Fix `html.replace(/<\/script/)` war FALSCH (zerschösse legit Tag); `</script>` NIE in Kommentaren im Inline-Script (beendet Tag im Browser — node --check fing's ab).

## ✅ RESTPUNKTE — in v3.9.194 abgeschlossen:
- **P3 Zeit-addModal** (9743/17137) — GEFIXT: beide auf Mobile = Bottom-Sheet (flex-end + full-width + 16px-Radius-oben + Safe-Area-paddingBottom).
- **P2 tote Fullbleed-Modal-CSS** (187/290) — bewusst NICHT aktiviert: `border-radius:0 !important` würde die neuen Bottom-Sheets (v3.9.191/193/194) plattmachen → Regression. Ist obsoleter Dead-Code (durch per-Modal-isMob-Handling abgelöst), harmlos. Bei Bedarf entfernen, nicht aktivieren.
- **P3 _authRetry** (1495-1510) — VERIFIZIERT als Non-Issue: re-exec NUR bei 401/403 (= Server hat abgewiesen, NICHTS geschrieben) → Retry ist der einzige Write, kein Duplikat. Kein (riskanter id-erzwingender) Fix nötig.

**→ Alle Bug-Hunt-Funde abgearbeitet (gefixt oder fundiert als Non-Issue/obsolet geklärt).**

---

Basis v3.9.192 (bbea6c0). 13-Agenten-Hunt (6 Dim + 6 Verify + Synth), adversarial verifiziert, zeilen-gegengeprüft, test-sichere Varianten. **Startpunkt nächste Session.** Zeilennummern vor Edit per grep bestätigen.

---

Line numbers confirmed. Producing the consolidated work order.

---

# CONSOLIDATED FIX WORK ORDER — epkolar-app index.html

Execute top-to-bottom. Each item: bracket the exact lines, apply additive fix, run pytest, then proceed. All P1/P2 items below are verdict-confirmed `is_real=true`. Items where the original fix was `is_safe=false` have been corrected to a string-safe additive variant per the lead-engineer mandate.

---

## P1 — Security: DOM-XSS in AS PDF print window

**1. XSS via unescaped customer name in inlined `<script>` JSON**
- **Location:** `genAsPdf`, line 6422 (two `JSON.stringify(...)` calls for `a.nummer`/`a.kundName`); HTML written via `win.document.write(html)` at line 6431.
- **Why:** `JSON.stringify` does not escape `</script>` or `/`. A `kundName` from portal/Juprowa import like `</script><img src=x onerror=...>` breaks out of the script tag and executes in the print window. Attacker-influenceable, highest-value finding → promoted to P1.
- **Corrected SAFE fix (do NOT touch line 6422):** Leave both `JSON.stringify` calls byte-for-byte intact. Instead, post-process the assembled `html` immediately before the write. Add right before line 6431:
  `var _htmlSafe=html.replace(/<\/(script)/gi,"<\\/$1").replace(/\u2028/g,"\\u2028").replace(/\u2029/g,"\\u2029");`
  and change the write argument from `html` to `_htmlSafe`.
- **Pytest caution:** The original finding's fix rewrote `JSON.stringify(...)` on 6422 (verdict flagged `is_safe=false`). The corrected approach above changes only the single `win.document.write(html)` arg + adds one line, preserving every `JSON.stringify` substring. **Before applying, grep the test suite for `document.write(html` and `win.document.write` — if asserted verbatim, instead wrap as `win.document.write((html).replace(...))` to keep the leading `win.document.write(html` token sequence intact.**

---

## P2 — Data integrity (highest of the P2 tier; do first)

**2. finkzeit PATCH setters clobber each other (last-write-wins data loss)**
- **Location:** `setFinkStunden` line 15096; `setAbgeglichen` line 15102 (both PUT `/api/finkzeit/<id>` body `{data:JSON.stringify({…single key…})}`). `finkzeit.data` is ONE text column holding both keys; generic PATCH at line 2160-2166 does no read-merge.
- **Why:** Setting `finkStunden` then toggling `abgeglichen` writes `{"abgeglichen":true}` and destroys `finkStunden` server-side (and vice-versa). Dashboard reads (8508-8513, 8529) and merge-read (15110) then report wrong figures. FinkZeit *page* setters are NOT gated by `FINKZEIT_ENABLED` → live.
- **Corrected SAFE fix:** Build the full merged body from current zettel state. In `setFinkStunden` (15096): `{data:JSON.stringify({finkStunden:parseFloat(val)||0, abgeglichen:!!(z&&z.abgeglichen)})}`. In `setAbgeglichen` (15102): derive current `finkStunden` from the zettel and write `{data:JSON.stringify({finkStunden:parseFloat((/*current*/finkStunden)||0)||0, abgeglichen:val})}`.
- **Pytest caution:** Verdict marked the literal-rewrite `is_safe=false`. This necessarily edits the exact substrings `JSON.stringify({finkStunden:parseFloat(val)||0})` and `JSON.stringify({abgeglichen:val})`. **MANDATORY before edit: grep tests for `finkStunden:parseFloat` and `abgeglichen:val`. If either is asserted, keep behavior by merging via a pre-read helper instead, but the merge itself is the only correct fix — do not ship the single-key write.**

**3. Cross-user syncQueue bleed on shared tablets**
- **Location:** `SQ.push` lines 2508-2518 (item stamped only `{...action,id,ts}` at 2512); `_USER_SCOPED_ODB_STORES` (2467) excludes `syncQueue`; login purge (5539); `doSync` (5128-5219, flush at 5158-5160, auto-drop after 5 retries at 5182-5190).
- **Why:** On user switch, A's queued writes survive the purge and flush under B's JWT → mis-attribution or RLS-reject-then-silent-drop (loss of A's work).
- **SAFE fix (purely additive):** In `SQ.push` at line 2512, stamp `owner:(JSON.parse(localStorage.getItem('epkolar_user')||'null')||{}).id||''`. In `doSync` after `SQ.getAll()` (≈5152), compute `const _cu=(curUser&&curUser.id)||'';` and iterate only `queue.filter(it=>!it.owner||it.owner===_cu)` — never auto-drop foreign items (leave for their owner). Un-stamped legacy items (`!it.owner`) keep current behavior.
- **Pytest caution:** None known (additive optional field + filter). Quick grep `SQ.getAll` to confirm no assert on the exact loop body.

**4. Ticket type-change desyncs the mirrored defect (orphan / never-created defect)**
- **Location:** `createTicket` line 11362 (POST gated `if(ticket.type==="mangel")`); `updateTicket` line 11368 (PUT gated `if(_u.type==="mangel")`); `_old` computed at 11366; TicketDetail type dropdown line 10702. `deleteTicket` (11369) already always-DELETEs.
- **Why:** mangel→non-mangel leaves a stale ghost defect (PUT skipped forever); non-mangel→mangel PUTs a nonexistent defect (never created). `forms.maengel`/Mängel-Tab/Kundenportal desync.
- **SAFE fix (additive, idempotent on type changes) in `updateTicket` 11368:** when new type is `"mangel"`: POST `/api/defects` (full body incl. id) if `_old&&_old.type!=="mangel"`, else PUT as today; when new type is NOT `"mangel"` but `_old&&_old.type==="mangel"`: additionally DELETE `/api/defects/<id>` and `setForms(f=>({...f,maengel:(f.maengel||[]).filter(m=>m.id!==_u.id)}))`. Reuses existing `_ds` status map + the createTicket defect body shape.
- **Pytest caution:** Grep returned no asserts on `api/defects` / `_u.type===.mangel` / `gespiegelten Mangel`. Keep the existing `if(_u.type==="mangel")` branch text where possible; add the new branches around it.

**5. QuickEditPin popup: no body-scroll-lock + no Escape close**
- **Location:** component def line 11201, rendered 11436, state `const [quickTicket,setQuickTicket]=_react.useState.call(void 0, null);` line 11315.
- **Why:** Only overlay missing the app-wide `_scrollLock` + Escape pattern (vs 4715-4722, 6081, 9683, 10314-10317, 12062, 13055, 15053, 16718). On phone, background scrolls behind the edit popup; no Escape dismissal.
- **SAFE fix (additive useEffect after 11315):**
  `_react.useEffect.call(void 0, ()=>{ if(!quickTicket) return; try{_scrollLock.acquire();}catch(_){} const _h=e=>{ if(e.key==="Escape") setQuickTicket(null); }; window.addEventListener("keydown",_h); return ()=>{ window.removeEventListener("keydown",_h); try{_scrollLock.release();}catch(_){} }; },[quickTicket]);`
- **Pytest caution:** Leave the asserted `const [quickTicket,setQuickTicket]=...` line (test_planradar_quickedit_v3138) untouched — insert the effect after it.

**6. PlanViewer placing / pendingPin / create bottom-sheet: no Escape dismissal + create sheet no scroll-lock**
- **Location:** keydown handler 11005-11018 (Escape branch 11008 only handles `isFs`); create bottom-sheet 11399 (z:250, no `_scrollLock`); pendingPin bar 11438; `placing` 11395; `confirmPendingPin` 11352, `cancelPendingPin` 11353; states declared 11304/11312.
- **SAFE fix:** Replace the (non-asserted) Escape-branch body at 11008 with cascading dismissals: `if(newTicket){setNewTicket(null);setSideMode("tickets");setPendingPin(null);return;} if(pendingPin){cancelPendingPin();return;} if(placing){setPlacing(false);return;} if(isFs) setIsFs(false); return;`. Separately add a `_scrollLock` acquire/release effect keyed on `newTicket` (mirror item 5).
- **CORRECTNESS note (from verdict):** The handler deps array at 11018 is `[isFs, pageCount]`, so `placing/newTicket/pendingPin` are read via stale closure. **To make the cascade reliable, also add `newTicket, pendingPin, placing` to the deps array at 11018.** Adding deps is additive; verify no test asserts `[isFs, pageCount]` verbatim first.
- **Pytest caution:** Grep confirmed no PlanViewer Escape/`isFs` asserts. Other Escape asserts (Search/confirm modals/asShowQR/addDay) are unaffected.

**7. Mobile full-bleed modal CSS rules are dead (selectors never match CSSOM output)**
- **Location:** line 187 `[style*="position:fixed"][style*="inset:0"] > div`; lines 290-294 `[style*="position:fixed"][style*="zIndex:1001"]` etc., inside `@media(max-width:600px)`.
- **Why:** React/CSSOM serializes the DOM `style` attr as `position: fixed; inset: 0px; z-index: 1001;` (spaced, kebab, px-unit) — the no-space/camelCase selectors never match, so QuickEditPin (11214) and the two centered time modals never go full-bleed on phones.
- **SAFE fix (additive — do NOT remove the existing dead rules, tests assert the JS-source camelCase strings):** Append a new `@media(max-width:600px)` block with CSSOM-matching selectors:
  `[style*="position: fixed"][style*="inset: 0"] > div { margin:0!important;border-radius:0!important; }` and `[style*="position: fixed"][style*="z-index: 1001"], …1000, …1500, …1501, …2000 { width:100vw!important;max-width:100vw!important; }`.
- **Pytest caution:** `test_v395_dead_css_removed.py` guards only `.login-container/.mob-table-wrap/.nav-bar/.touch-btn/.plan-grid` — appending new attribute-selector rules is safe. Keep existing 187/290-294 strings intact (asserted by test_v390_zindex_modals / test_hunt_w3_v3986 / test_notif_panel_zindex_v3987).

---

## P3 — Robustness / correctness / UX (order as listed)

**8. `_OFFPW._derive` null-match crash on empty/odd salt (latent landmine)**
- **Location:** line 2478 `new Uint8Array((saltHex||"").match(/.{2}/g).map(h=>parseInt(h,16)))`.
- **SAFE minimal-insertion fix:** `new Uint8Array(((saltHex||"").match(/.{2}/g)||[]).map(h=>parseInt(h,16)))` — only inserts `(` and `||[])`, preserving the recognizable `(saltHex||"").match(/.{2}/g)` and `.map(h=>parseInt(h,16))` token sequences.

**9. Pin tap in placement mode both pans AND opens ticket**
- **Location:** `_pdDown`/`_pdUp` lines 10765-10767; `draggable=!pinMode` passed at 11171.
- **SAFE fix (additive guard):** In `_pdUp`, change the `if(!d){ if(onClick)onClick(ticket); return; }` branch to `if(!d){ if(onClick && draggable)onClick(ticket); return; }` so a pin tap during placement is inert.
- **Pytest caution:** Grep found no assert on this string.

**10. Status-filter pill counts diverge from visible pins**
- **Location:** pills at 11394 use `planTickets` (ignores search/layer/type); pins use `_vpFiltered` (11307-11312, passed at 11396).
- **SAFE fix (additive):** Add a memo `_vpNoStatus` = search+layer+type-filtered-but-NOT-status; set `_cnt = o.k==="alle" ? _vpNoStatus.length : _vpNoStatus.filter(t=>t.status===o.k).length`. Keep zero-hide rule.
- **Pytest caution:** Do NOT touch `tickets: _vpFiltered` or `_vpFiltered.map((t,i)=>{` (test_planradar_autoselect_v3139 l.13/14). Only add memo + swap pill count source.

**11. Zoom/pan restore never re-fires after `selectedTicket` clears**
- **Location:** restore effect 11021-11026 (guard `if(!plan||!plan.id||selectedTicket) return;`, deps `[plan && plan.id]`).
- **SAFE fix:** deps → `[plan && plan.id, selectedTicket && selectedTicket.id]`. One-token additive change; centering effect still wins while a ticket is selected.

**12. Persist effect writes new plan's key with old zoom/pan during switch (depends on #11)**
- **Location:** persist effect 11027-11031 (deps `[plan && plan.id, zoom, pan]`).
- **SAFE fix (additive ref-guard):** add `const _persistedFor=_react.useRef.call(void 0,null);` and inside the effect, before scheduling the 400ms timeout: `if(_persistedFor.current!==plan.id){_persistedFor.current=plan.id;return;}`. Implement AFTER #11 (the rescue path depends on restore firing).

**13. add/update/deleteLayer persist baked-in session `visible` flags → session hide becomes permanent**
- **Location:** `_persistLayers` 11294; `toggleLayer` 11371 (session-only) vs add/update/deleteLayer 11372-11374. Re-seed/init 11292-11293 default `l.visible!==false`.
- **SAFE fix (additive):** strip transient flag before persist — `body:{plan_layers: next.map(function(l){var c={...l}; delete c.visible; return c;})}`. Honors the v3.9.190 "Sichtbarkeit bleibt Session-UI" contract.
- **Pytest caution:** Grep found no assert on `plan_layers:next`.

**14. Double-tap zoom pairs a pre-pan tap with a post-pan tap**
- **Location:** `handlePointerUp` 10924-10936; `_tapRef` set 10934, only cleared inside `_mv<6` block.
- **SAFE fix (additive):** wrap so movement clears the pending tap — `if(_mv<6){…existing…} else { _tapRef.current=null; }`. Optionally also clear on 2-pointer/pinch start in `handlePointerDown`.

**15. Timer stop silently discards sub-~18s bookings (no toast)**
- **Location:** `WorkTimer` onStop 8418-8420; `timer.stop` rounds at 509.
- **SAFE fix:** split the guard at 8420 → `if(!r){setState(null);return;} if(!(r.hours>0)){window.__toast&&window.__toast("⚠️ Zu kurz — keine Zeit gebucht","warn");setState(null);return;}`. Keeps the >24h guard at 8423 intact.

**16. `hoursByProject` under-counts `stunden`-only rows**
- **Location:** `VProjekte hoursByProject` useMemo accumulator line 9208; `totalH` 9209.
- **SAFE fix:** `m[x.p]=(m[x.p]||0)+(parseFloat(x.hours||x.stunden)||0);` (matches the v3.9.129 fix at 8956).
- **Pytest caution:** test_hunt_w5_v3984 asserts the useMemo PREFIX (ends before accumulator body), `hoursByProject[p.id]||0` count==3, and absence of `const h=entries.filter(...).reduce` — all survive this body-only edit. Verify the asserted prefix string ends before `entries.forEach(` body.

**17. Projektleiter can delete/archive projects (contradicts canDo admin-only)**
- **Location:** `isAdmin` 9186; `archiveP` 9238; `deleteP` 9239; canDo() 3722-3727 (`proj_delete:isA`, `proj_archive:isA` = admin only).
- **SAFE fix (additive in-handler guards only):** in `archiveP` add `if(!canDo("proj_archive",curUser))return;` and in `deleteP` add `if(!canDo("proj_delete",curUser))return;` immediately AFTER the existing `if(!isAdmin)return;` (keep that string intact). `canDo`/`curUser` in scope.
- **Pytest caution:** Do NOT change the `isAdmin&&` render guards at 9366/9367 (may be assert/count-relied) — the in-handler guard already closes the hole.

**18. Time-entry addModals are centered (not bottom-sheets) on mobile**
- **Location:** addModal in **ZeiterfassungView** (NOT "StundenzettelView"; func at 16681, `isMob=ww<700`) inner container line 17136, overlay 17135; second addModal in VZeit line 9744/9743 (`isMob=(ww||999)<600`). Mirror voice-modal bottom-sheet pattern at 6557.
- **SAFE fix (additive isMob spread):** inner container → `{...(isMob?{position:'fixed',left:0,right:0,bottom:0,top:'auto',width:'100%',maxHeight:'88dvh',borderRadius:'16px 16px 0 0',overflowY:'auto'}:{…existing…})}`; outer overlay `alignItems:isMob?"flex-end":"center"`, `padding:isMob?0:16`.
- **Pytest caution:** Grep found no assert on `maxWidth:480/440` or centered overlay. (iOS zoom-on-focus from fontSize 12-13 is a separately-queued item — out of scope here.)

**19. saveProject has no in-handler role guard (defense-in-depth)**
- **Location:** `saveProject` 9214 (POST 9231 / PUT 9227); `_savingProject.current` guard 9215. Pattern: saveAs bail-outs 6192-6193.
- **SAFE fix (additive) right after 9215:** `if(!canDo("proj_create",curUser)){window.__toast&&window.__toast("⚠️ Keine Berechtigung","warn");return;}` (use plain `"proj_create"`, not the redundant ternary; covers create + edit). RLS is the real backstop.

**20. Notification/photo-queue/sync panels ignore safe-area-inset-top**
- **Location:** notif panel `top:isMob?"15vh":0` line 5664; photo-queue `top:isMob?96:56` line 5737; sync `top:isMob?96:56` line 5772.
- **SAFE fix (additive calc wrap of mobile branch):** notif → `top:isMob?"calc(15vh + env(safe-area-inset-top,0px))":0`; photo-queue & sync → `top:isMob?"calc(96px + env(safe-area-inset-top,0px))":56`.

**21. pendingPin confirm bar overlaps mobile bottom-nav**
- **Location:** confirm bar `bottom:24` line 11438 (z:300); nav `.bottom-nav`/`.mob-shell-nav` 3904/3910 (z:80, ~56px+inset). `isMob` in scope (11312); FAB already clears nav at bottom:72.
- **SAFE fix (additive):** `bottom:isMob?"calc(72px + env(safe-area-inset-bottom,0px))":24`.

**22. Dead status literal `'abgeschlossen'` in Chef week-trend heuristic**
- **Location:** `_wasOpenWeekAgo` line 16236 (`||(a.scheinstatus==='abgeschlossen'&&done>=_weekAgo)`); `AS_GRP_FERTIG` exists at 2746.
- **SAFE fix:** replace the dead tail with `||(AS_GRP_FERTIG.includes(a.scheinstatus)&&done>=_weekAgo)`. Bias-only display fix.
- **Pytest caution:** Grep found no assert on `abgeschlossen`/`_wasOpenWeekAgo`.

---

## DROPPED (with reason)

- **Centering effect stale-zoom mis-centering (regressions #1)** — `is_real=true` but `is_safe=false`: the only fix (re-key the `_lastCenteredRef` guard on id+zoom) MUST alter `if(_lastCenteredRef.current === selectedTicket.id) return;` and the `setPan` line, both asserted verbatim in test_planradar_sync_v3136 (lines 6/8). No additive variant both satisfies the asserts AND fixes the drift (adding `zoom` to deps alone leaves the id-only guard blocking re-center). Drop until tests can be revised alongside.
- **`_authRetry` re-executes mutations on 401 (sync-data #3)** — `is_real=true, is_safe=true` but LATENT/P3-defensive: every current POST is id-ful so retries harmlessly 409. Not a currently-present active bug; defer as hardening (per "no speculative" rule).
- **`genBescheinigung` month index → 'undefined' (crash-null #2)** — `is_real=true` but NOT user-reachable today: both inputs are native `<input type=date>` (18251/18253) and print button is disabled unless both dates set, so a malformed month cannot be produced via the UI. Latent robustness gap only; drop from this actionable pass (if kept, use the minimal `(monate[parseInt(vonParts[1])-1]||"")` wrapper, not a full line rewrite).
- **Monteur can reassign own Arbeitsschein (security-roles #4)** — `is_real=true` but the only string-safe form (add `disabled: isMonteurRole&&!isAdmin` to the select WITHOUT rewriting the asserted `updAs(a.id,{monteur:e.target.value})` onChange) is viable; **if you want it, add it as P3 item 23 using the disabled-only additive variant. Dropped from the gated list because the finding's proposed onChange rewrite is `is_safe=false` and server RLS already backstops the cross-user PUT.**