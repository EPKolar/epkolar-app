// Verhaltens-Test FIX 1 (403-Wedge, index.html:5139-5164 v3.9.159) + FIX 2 (PhotoQ, index.html:2541-2553 v3.9.160).
// Repliziert die ECHTE Loop-Logik VERBATIM mit gemockten Calls — beweist das Laufzeit-Verhalten (was pytest nicht testet).
let navigator = { onLine: true };
let PASS = true;
const log = (...a) => console.log(...a);
const chk = (name, cond) => { log("  " + (cond ? "✅" : "❌") + " " + name); PASS = PASS && cond; };

// ── doSync-Loop verbatim aus index.html (5135-5166) ──────────────────────────
async function runDoSyncOnce(queue, mockExec, syncQueueFailed) {
  let ok = 0, fail = 0; const okIds = [], skipIds = [];
  for (const item of queue) {
    try {
      await mockExec(item);
      okIds.push(item.id); ok++;
    } catch (e) {
      const isAuth = e.message && e.message.startsWith("Auth:");
      const _authSt = isAuth ? (parseInt(e.message.slice(5), 10) || 0) : 0;
      if (isAuth && _authSt !== 403) { fail++; break; }
      const _hm = /^HTTP(\d{3})/.exec(e.message || ""); const _st = _hm ? parseInt(_hm[1], 10) : 0;
      const _transient = !navigator.onLine || _st >= 500 || _st === 408 || _st === 429 || e.message === 'Failed to fetch';
      if (_transient) { fail++; break; }
      const retries = (item._retries || 0) + 1;
      if (retries >= 5) { skipIds.push(item.id); syncQueueFailed.push({ id: item.id, lastError: e.message }); }
      else { item._retries = retries; }
      fail++;
    }
  }
  const removeIds = new Set([...okIds, ...skipIds]);
  return { ok, fail, okIds, skipIds, remaining: queue.filter(x => !removeIds.has(x.id)) };
}
const mockExec = (item) => {
  if (item.mock === '403') return Promise.reject(new Error("Auth:403"));
  if (item.mock === '401') return Promise.reject(new Error("Auth:401"));
  if (item.mock === '5xx') return Promise.reject(new Error("HTTP503 server unavailable"));
  return Promise.resolve();
};

// ── PhotoQ.flush-Loop verbatim aus index.html (2540-2548) ────────────────────
async function runPhotoFlush(pending, mockUpload) {
  let ok = 0, fail = 0; const statuses = {}; const removed = []; let broke = false;
  for (const ph of pending) {
    try {
      statuses[ph.id] = "uploading";
      await mockUpload(ph);
      removed.push(ph.id); ok++;
    } catch (e) {
      statuses[ph.id] = "error"; ph.retries = (ph.retries || 0) + 1; fail++;
      const _hm = /(?:HTTP|Auth:)(\d{3})/.exec(e.message || ""); const _st = _hm ? parseInt(_hm[1], 10) : 0;
      if (!navigator.onLine || _st >= 500 || _st === 408 || _st === 429 || (e.message || "").includes("Failed to fetch")) { broke = true; break; }
    }
  }
  return { ok, fail, statuses, removed, broke };
}
const mockUpload = (ph) => {
  if (ph.mock === 'bad') return Promise.reject(new Error("Invalid dataUrl"));      // permanent (kein Status)
  if (ph.mock === 'offline') return Promise.reject(new Error("Failed to fetch"));   // transient
  if (ph.mock === '500') return Promise.reject(new Error("HTTP500 storage error")); // transient
  return Promise.resolve();
};

(async () => {
  navigator.onLine = true;

  log("\n=== TEST A: 403-Item blockiert nachfolgende NICHT + landet nach 5 in syncQueueFailed ===");
  let q = [{ id: 'bad403', mock: '403' }, { id: 'ok1', mock: 'ok' }, { id: 'ok2', mock: 'ok' }];
  let failed = [];
  let r = await runDoSyncOnce(q, mockExec, failed);
  log("  Run1 okIds=" + JSON.stringify(r.okIds) + " remaining=" + JSON.stringify(r.remaining.map(x => x.id + "(r" + (x._retries || 0) + ")")));
  chk("ok1+ok2 laufen trotz 403 davor durch", r.okIds.includes('ok1') && r.okIds.includes('ok2'));
  chk("403-Item bleibt in Queue mit _retries=1 (kein Wedge-break)", r.remaining.length === 1 && r.remaining[0].id === 'bad403' && r.remaining[0]._retries === 1);
  q = r.remaining;
  for (let i = 2; i <= 5; i++) { r = await runDoSyncOnce(q, mockExec, failed); q = r.remaining; }
  log("  Nach 5 Runs: syncQueueFailed=" + JSON.stringify(failed.map(f => f.id)) + " queue=" + JSON.stringify(q.map(x => x.id)));
  chk("403-Item nach 5 Fails in syncQueueFailed", failed.some(f => f.id === 'bad403'));
  chk("Queue danach leer (kein Dauer-Wedge)", q.length === 0);

  log("\n=== TEST B: transienter 5xx HÄLT die Queue (break) + retryt, kein Skip ===");
  q = [{ id: 'trans5xx', mock: '5xx' }, { id: 'ok3', mock: 'ok' }]; failed = [];
  r = await runDoSyncOnce(q, mockExec, failed);
  chk("5xx bricht ab → ok3 NICHT verarbeitet", !r.okIds.includes('ok3'));
  chk("beide Items bleiben in Queue", r.remaining.some(x => x.id === 'trans5xx') && r.remaining.some(x => x.id === 'ok3'));
  chk("nichts in syncQueueFailed (kein vorschneller Drop)", failed.length === 0);

  log("\n=== TEST C: 401 bricht weiterhin ab (Re-Auth-Pfad unverändert) ===");
  q = [{ id: 'auth401', mock: '401' }, { id: 'ok4', mock: 'ok' }]; failed = [];
  r = await runDoSyncOnce(q, mockExec, failed);
  chk("401 break → ok4 nicht verarbeitet", !r.okIds.includes('ok4'));
  chk("401-Item bleibt (kein Drop, wartet auf Re-Login)", r.remaining.some(x => x.id === 'auth401') && failed.length === 0);

  log("\n=== TEST D: PhotoQ [kaputt, gut1, gut2] → gute hoch, kaputtes='error', KEIN Block ===");
  navigator.onLine = true;
  let photos = [{ id: 'pbad', mock: 'bad' }, { id: 'pg1', mock: 'ok' }, { id: 'pg2', mock: 'ok' }];
  let pr = await runPhotoFlush(photos, mockUpload);
  log("  removed=" + JSON.stringify(pr.removed) + " statuses=" + JSON.stringify(pr.statuses) + " broke=" + pr.broke);
  chk("gut1+gut2 hochgeladen (removed)", pr.removed.includes('pg1') && pr.removed.includes('pg2'));
  chk("kaputtes Foto als 'error' markiert (kein stiller Verlust)", pr.statuses['pbad'] === 'error');
  chk("kein break — alle 3 durchlaufen", pr.broke === false);

  log("\n=== TEST E: PhotoQ transient (offline) → break, nachfolgendes NICHT hochgeladen ===");
  let photos2 = [{ id: 'poff', mock: 'offline' }, { id: 'pg3', mock: 'ok' }];
  let pr2 = await runPhotoFlush(photos2, mockUpload);
  chk("offline → break", pr2.broke === true);
  chk("pg3 NICHT hochgeladen (Queue gehalten)", !pr2.removed.includes('pg3'));
  chk("poff als 'error' markiert", pr2.statuses['poff'] === 'error');

  log("\n" + (PASS ? "✅✅✅ ALLE VERHALTENS-TESTS GRÜN" : "❌ MINDESTENS EIN TEST ROT"));
  process.exit(PASS ? 0 : 1);
})();
