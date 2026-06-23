#!/usr/bin/env node
/* ─────────────────────────────────────────────────────────────────────────
   Tankfoto-Migration Base64 → Supabase Storage (einmalig, idempotent)
   Spiegelt exakt window._migrateTankFotos: Bucket 'epkolar-files',
   Pfad fahrzeuge/<fzId>/tank/<eid>.jpg, foto → Public-URL.

   AUSFÜHRUNG (im Repo-Ordner, Node 18+):
     node migrate_tankfotos.mjs            # DRY-RUN (nur Log, KEINE Writes)
     node migrate_tankfotos.mjs --go       # migriert (Backup → Upload → tank_log-Patch)

   AUTH (eine der beiden Varianten als ENV setzen — werden NICHT geloggt):
     SUPABASE_SERVICE_KEY=<service_role_jwt>            # bypassed RLS
       — ODER —
     ADMIN_EMAIL=<admin@…>  ADMIN_PASSWORD=<pw>         # Login (admin-Rolle nötig für fahrzeuge-Update)

   SUPABASE_URL + anon-Key werden automatisch aus ./index.html gelesen.
   Idempotent: nur foto die mit 'data:' beginnt; bereits migrierte (http) übersprungen.
   ───────────────────────────────────────────────────────────────────────── */
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";

const GO = process.argv.includes("--go");
const BUCKET = "epkolar-files";

// ── Config aus index.html ziehen (URL + anon-Key sind öffentlich) ──
const html = readFileSync(new URL("./index.html", import.meta.url), "utf-8");
const URL_M = html.match(/const SUPABASE_URL="([^"]+)"/);
const KEY_M = html.match(/const SUPABASE_KEY="([^"]+)"/);
if (!URL_M || !KEY_M) { console.error("✗ SUPABASE_URL/KEY nicht in index.html gefunden"); process.exit(1); }
const SUPABASE_URL = URL_M[1];
const ANON = KEY_M[1];

// ── Auth ──
let bearer, apikey;
if (process.env.SUPABASE_SERVICE_KEY) {
  bearer = process.env.SUPABASE_SERVICE_KEY; apikey = process.env.SUPABASE_SERVICE_KEY;
  console.log("Auth: SERVICE_KEY (RLS-bypass)");
} else if (process.env.ADMIN_EMAIL && process.env.ADMIN_PASSWORD) {
  const r = await fetch(SUPABASE_URL + "/auth/v1/token?grant_type=password", {
    method: "POST", headers: { apikey: ANON, "Content-Type": "application/json" },
    body: JSON.stringify({ email: process.env.ADMIN_EMAIL, password: process.env.ADMIN_PASSWORD })
  });
  const j = await r.json();
  if (!r.ok || !j.access_token) { console.error("✗ Login fehlgeschlagen:", r.status, j.error_description || j.msg || ""); process.exit(1); }
  bearer = j.access_token; apikey = ANON;
  console.log("Auth: Login als", process.env.ADMIN_EMAIL, "(role:", (JSON.parse(Buffer.from(j.access_token.split(".")[1], "base64").toString()).app_metadata || {}).role || "?", ")");
} else {
  console.error("✗ Keine Auth gesetzt. Setze SUPABASE_SERVICE_KEY  ODER  ADMIN_EMAIL + ADMIN_PASSWORD."); process.exit(1);
}
const H = { apikey, Authorization: "Bearer " + bearer };

// ── Fahrzeuge laden ──
const fzRes = await fetch(SUPABASE_URL + "/rest/v1/fahrzeuge?select=id,kennzeichen,tank_log", { headers: H });
if (!fzRes.ok) { console.error("✗ fahrzeuge-Fetch:", fzRes.status, await fzRes.text()); process.exit(1); }
const fahrzeuge = await fzRes.json();

// ── Backup vor --go ──
if (GO) {
  const withFotos = fahrzeuge.filter(f => (f.tank_log || "").includes("data:image"));
  mkdirSync(new URL("./docs/db/", import.meta.url), { recursive: true });
  const bpath = new URL("./docs/db/tank-log-backup-prego-" + new Date().toISOString().slice(0, 10) + ".json", import.meta.url);
  writeFileSync(bpath, JSON.stringify(withFotos.map(f => ({ id: f.id, kennzeichen: f.kennzeichen, tank_log: f.tank_log })), null, 2), "utf-8");
  console.log("Backup geschrieben:", withFotos.length, "Fahrzeuge →", bpath.pathname);
}

const out = { mode: GO ? "GO" : "DRY-RUN", scanned: 0, toMigrate: 0, uploaded: 0, skipped: 0, patched: 0, errors: [] };

for (const f of fahrzeuge) {
  let tl; try { tl = JSON.parse(f.tank_log || "[]"); if (!Array.isArray(tl)) continue; } catch { continue; }
  let changed = false;
  for (const e of tl) {
    out.scanned++;
    const foto = (e && e.foto) || "";
    if (!foto.startsWith("data:")) { out.skipped++; continue; }
    out.toMigrate++;
    const mime = foto.slice(5, foto.indexOf(";")) || "image/jpeg";
    const ext = mime.split("/")[1] || "jpg";
    const path = "fahrzeuge/" + f.id + "/tank/" + (e.id || ("tk" + out.toMigrate)) + "." + (ext === "jpeg" ? "jpg" : ext);
    if (!GO) { console.log("[DRY]", f.kennzeichen, "→", path, Math.round(foto.length / 1024) + "KB"); continue; }
    try {
      const buf = Buffer.from(foto.slice(foto.indexOf(",") + 1), "base64");
      const up = await fetch(SUPABASE_URL + "/storage/v1/object/" + BUCKET + "/" + path,
        { method: "POST", headers: { ...H, "Content-Type": mime, "x-upsert": "true" }, body: buf });
      if (!up.ok) throw new Error("HTTP " + up.status + " " + (await up.text()));
      e.foto = SUPABASE_URL + "/storage/v1/object/public/" + BUCKET + "/" + path;
      changed = true; out.uploaded++;
      console.log("[GO] hochgeladen:", f.kennzeichen, "→", e.foto);
    } catch (err) { out.errors.push(f.id + "/" + e.id + ": " + err.message); console.error("[upload-fail]", f.kennzeichen, err.message); }
  }
  if (GO && changed) {
    const pr = await fetch(SUPABASE_URL + "/rest/v1/fahrzeuge?id=eq." + encodeURIComponent(f.id),
      { method: "PATCH", headers: { ...H, "Content-Type": "application/json", Prefer: "return=minimal" },
        body: JSON.stringify({ tank_log: JSON.stringify(tl), updated_at: new Date().toISOString() }) });
    if (pr.ok) out.patched++; else { out.errors.push("patch " + f.id + ": HTTP " + pr.status + " " + (await pr.text())); console.error("[patch-fail]", f.kennzeichen, pr.status); }
  }
}

console.table([out]);
if (!GO) console.log("\nDRY-RUN fertig — echter Lauf:  node migrate_tankfotos.mjs --go");
else console.log("\nMigration fertig. Verify in DB: foto sollte jetzt http… sein.");
