// supabase/functions/juprowa_sync_kunden/index.ts
// =============================================================================
// EP Kolar — juprowa_sync_kunden Edge-Function (v3.9.587)
// Robuster Kundenstamm-Sync: ersetzt die DB-RPC juprowa_fetch_kunden, die auf der
// authenticated-Rolle am statement_timeout=8s scheiterte (RPC-Laufzeit ~7,5s für
// 7,6 MB KundeList → 500 "canceling statement due to statement timeout", Code 57014).
// Eine Edge-Function läuft AUSSERHALB des PostgREST/DB-statement_timeouts: Fetch +
// Parse + Batch-Upsert (500er) mit eigener Laufzeit-Grenze.
//
// HARTE GRENZE: ausschliesslich GET gegen Juprowa ServicePad (type=KundeList).
// Kein Write Richtung Juprowa/OFFA. Upsert nur in unsere public.kunden (service_role).
//
// Env (Supabase setzt beim Deploy): SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_ANON_KEY
// Aufruf: POST {SUPABASE_URL}/functions/v1/juprowa_sync_kunden
//         Headers: Authorization: Bearer <user-jwt>, Content-Type: application/json
// Autorisierung spiegelt is_staff(): users.role IN ('admin','buero','projektleiter').
// =============================================================================

// @ts-ignore - Deno-Runtime
import { serve } from "https://deno.land/std@0.224.0/http/server.ts";
// @ts-ignore - Deno-Runtime
import { createClient } from "https://esm.sh/@supabase/supabase-js@2.45.0";

const CORS_HEADERS: Record<string, string> = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

function json(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...CORS_HEADERS, "Content-Type": "application/json" },
  });
}

const JUPROWA_BASE = "https://services.juprowa.net/Cloud/WebService/v6.0/jsondata.php";
const BATCH = 500;

serve(async (req: Request) => {
  const t0 = Date.now();
  if (req.method === "OPTIONS") return new Response("ok", { headers: CORS_HEADERS });
  if (req.method !== "POST") return json(405, { ok: false, error: "method_not_allowed" });

  // @ts-ignore
  const SUPABASE_URL = Deno.env.get("SUPABASE_URL") || "";
  // @ts-ignore
  const SERVICE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") || "";
  // @ts-ignore
  const ANON_KEY = Deno.env.get("SUPABASE_ANON_KEY") || "";
  if (!SUPABASE_URL || !SERVICE_KEY || !ANON_KEY) {
    return json(500, { ok: false, error: "internal", details: "edge env not configured" });
  }

  // 1. Caller JWT -> auth.uid()
  const authHdr = req.headers.get("Authorization") || "";
  const jwt = authHdr.toLowerCase().startsWith("bearer ") ? authHdr.slice(7).trim() : "";
  if (!jwt) return json(401, { ok: false, error: "unauthorized" });

  const callerClient = createClient(SUPABASE_URL, ANON_KEY, {
    global: { headers: { Authorization: `Bearer ${jwt}` } },
    auth: { persistSession: false, autoRefreshToken: false },
  });
  const { data: callerAuth, error: callerErr } = await callerClient.auth.getUser();
  if (callerErr || !callerAuth?.user) return json(401, { ok: false, error: "unauthorized", details: "jwt invalid" });
  const callerAuthUid = callerAuth.user.id;

  const admin = createClient(SUPABASE_URL, SERVICE_KEY, {
    auth: { persistSession: false, autoRefreshToken: false },
  });

  // 2. Authorize: spiegelt is_staff() — role IN (admin, buero, projektleiter), aktiv & nicht gesperrt.
  const { data: callerRow, error: lookErr } = await admin
    .from("users")
    .select("id, role, active, locked")
    .eq("auth_user_id", callerAuthUid)
    .maybeSingle();
  if (lookErr) return json(500, { ok: false, error: "internal", details: "caller lookup failed: " + (lookErr.message || "") });
  const role = (callerRow?.role || "").toLowerCase();
  const allowed = !!callerRow && callerRow.active !== false && !callerRow.locked &&
    (role === "admin" || role === "buero" || role === "projektleiter");
  if (!allowed) return json(403, { ok: false, error: "forbidden", details: "staff only" });

  // 3. Juprowa-Config (UID/PASSPORT) server-seitig lesen
  const { data: cfg, error: cfgErr } = await admin
    .from("juprowa_config")
    .select("uid, passport, sync_enabled")
    .eq("id", "default")
    .maybeSingle();
  if (cfgErr) return json(500, { ok: false, error: "internal", details: "config read failed: " + (cfgErr.message || "") });
  if (!cfg) return json(500, { ok: false, error: "config_missing" });
  if (cfg.sync_enabled === false) return json(400, { ok: false, error: "sync_disabled" });

  // 4. GET KundeList von Juprowa (read-only). AbortController-Timeout 45s.
  const url = `${JUPROWA_BASE}?UID=${encodeURIComponent(cfg.uid)}&PASSPORT=${encodeURIComponent(cfg.passport)}&type=KundeList&ts=${Date.now()}`;
  let payload: Record<string, any>;
  try {
    const ac = new AbortController();
    const to = setTimeout(() => ac.abort(), 45000);
    const resp = await fetch(url, { method: "GET", signal: ac.signal });
    clearTimeout(to);
    if (resp.status !== 200) {
      return json(502, { ok: false, error: "juprowa_status", status: resp.status, passport_expired: resp.status === 401 || resp.status === 403 });
    }
    payload = await resp.json();
  } catch (e) {
    return json(502, { ok: false, error: "juprowa_fetch", details: String((e as Error)?.message || e) });
  }
  if (!payload || typeof payload !== "object") return json(502, { ok: false, error: "juprowa_bad_payload" });

  // 5. Map + dedup auf kunde_nr (latest LAST_MODIFIED gewinnt)
  const nowIso = new Date().toISOString();
  const byNr = new Map<string, Record<string, unknown>>();
  let sourceCount = 0;
  for (const [kuId, rec] of Object.entries(payload)) {
    sourceCount++;
    const stamm = (rec as any)?.STAMM || {};
    const kunde_nr = String(stamm.KU_NUMMER || "").trim();
    if (!kunde_nr) continue;
    const contacts = (rec as any)?.CONTACTS;
    const email = (Array.isArray(contacts) && contacts[0] && contacts[0].KK_EMAIL) ? String(contacts[0].KK_EMAIL) : "";
    const lastMod = String((rec as any)?.LAST_MODIFIED || "");
    const row = {
      kunde_nr,
      juprowa_id: kuId,
      name: stamm.KU_NAME || null,
      strasse: stamm.KU_STREET || null,
      plz: stamm.KU_ZIP || null,
      ort: stamm.KU_CITY || null,
      land: stamm.KU_COUNTRY || null,
      matchcode: stamm.KU_MATCH || null,
      titel: stamm.KU_TITEL || null,
      gesperrt: String(stamm.KU_GESPERRT) === "1",
      email: email || null,
      tel: ((rec as any)?.PHONENUMBERS ? String((rec as any).PHONENUMBERS) : "") || null,
      juprowa_raw: rec,
      last_modified: lastMod || null,
      synced_at: nowIso,
      updated_at: nowIso,
    };
    const prev = byNr.get(kunde_nr) as any;
    if (!prev || (lastMod >= (prev.last_modified || ""))) byNr.set(kunde_nr, row);
  }
  const rows = [...byNr.values()];

  // 6. Batch-Upsert (500er) — idempotent ON CONFLICT (kunde_nr)
  let imported = 0;
  let batches = 0;
  for (let i = 0; i < rows.length; i += BATCH) {
    const chunk = rows.slice(i, i + BATCH);
    const { error: upErr } = await admin.from("kunden").upsert(chunk, { onConflict: "kunde_nr" });
    if (upErr) return json(500, { ok: false, error: "upsert", details: upErr.message || "", imported, batches });
    imported += chunk.length;
    batches++;
  }

  return json(200, {
    ok: true,
    source_count: sourceCount,
    deduped: rows.length,
    imported,
    batches,
    duration_ms: Date.now() - t0,
  });
});
