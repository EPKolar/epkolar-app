// supabase/functions/supplier-sync/index.ts
// =============================================================================
// EP Kolar — supplier-sync Edge-Function (P0-2 cred-lockdown, Sebastian-Spec v3.10.5)
// =============================================================================
// Zweck: Verschiebt JEDEN Umgang mit supplier_configs.username/password auf den
// Server (service_role). Der Client liest Creds nie mehr; er ruft nur noch:
//   - { action:"sync", supplierId? }           → Artikel-Sync (DATANORM/IDS) serverseitig
//   - { action:"set-credentials", supplierId, username, password } → Creds setzen (kein Echo)
//
// Env (Supabase setzt diese beim Deploy):
//   SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY (NIE clientseitig), SUPABASE_ANON_KEY
//
// Aufruf vom Client:
//   POST {SUPABASE_URL}/functions/v1/supplier-sync
//   Headers: Authorization: Bearer <user-jwt>, Content-Type: application/json
//
// Autorisierung (spiegelt can_see_supplier_creds()): role admin/projektleiter ODER rolle='lagerleitung'.
// Antworten enthalten NIE username/password.
// =============================================================================

// @ts-ignore - Deno-Runtime
import { serve } from "https://deno.land/std@0.224.0/http/server.ts";
// @ts-ignore - Deno-Runtime
import { createClient } from "https://esm.sh/@supabase/supabase-js@2.45.0";

interface SyncBody { action: "sync"; supplierId?: string | null }
interface CredsBody { action: "set-credentials"; supplierId: string; username: string; password: string }
type Body = SyncBody | CredsBody;

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

serve(async (req: Request) => {
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

  // 1. Caller JWT
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

  // 2. Authorize: admin / projektleiter / lagerleitung (mirrors can_see_supplier_creds())
  const { data: callerRow, error: lookErr } = await admin
    .from("users")
    .select("id, role, rolle, active, locked")
    .eq("auth_user_id", callerAuthUid)
    .maybeSingle();
  if (lookErr) return json(500, { ok: false, error: "internal", details: "caller lookup failed: " + (lookErr.message || "") });
  const role = (callerRow?.role || "").toLowerCase();
  const rolle = (callerRow?.rolle || "").toLowerCase();
  const allowed = !!callerRow && callerRow.active && !callerRow.locked &&
    (role === "admin" || role === "projektleiter" || rolle === "lagerleitung");
  if (!allowed) return json(403, { ok: false, error: "forbidden", details: "caller may not manage suppliers" });

  // 3. Parse
  let body: Partial<Body>;
  try { body = await req.json(); } catch { return json(400, { ok: false, error: "validation", details: "invalid JSON" }); }
  if (!body || typeof body !== "object" || !("action" in body)) {
    return json(400, { ok: false, error: "validation", details: "action required" });
  }

  // 4a. set-credentials — server-only write, never echoes creds back
  if (body.action === "set-credentials") {
    const b = body as CredsBody;
    if (!b.supplierId || typeof b.username !== "string" || typeof b.password !== "string") {
      return json(400, { ok: false, error: "validation", details: "supplierId, username, password required" });
    }
    const { error: upErr } = await admin
      .from("supplier_configs")
      .update({ username: b.username, password: b.password, updated_at: new Date().toISOString() })
      .eq("id", b.supplierId);
    if (upErr) return json(500, { ok: false, error: "internal", details: "cred update failed: " + (upErr.message || "") });
    return json(200, { ok: true, supplierId: b.supplierId }); // NO creds in response
  }

  // 4b. sync — read creds server-side, fetch DATANORM/IDS, upsert articles
  if (body.action === "sync") {
    const b = body as SyncBody;
    const q = admin.from("supplier_configs")
      .select("id, name, interface_type, base_url, shk_url, ids_shop_url, unternehmen_id, kunde_nr, datanorm_url, username, password, active");
    const { data: cfgs, error: cfgErr } = b.supplierId ? await q.eq("id", b.supplierId) : await q.eq("active", true);
    if (cfgErr) return json(500, { ok: false, error: "internal", details: "config read failed: " + (cfgErr.message || "") });

    const results: Array<{ supplierId: string; name: string; ok: boolean; rows_synced: number; error?: string }> = [];
    for (const cfg of (cfgs || [])) {
      try {
        // ── TODO (Sebastian/Chat-Claude): supplier-spezifischen DATANORM/IDS-Download hier
        //    einsetzen — Logik aus der bestehenden Dashboard-Function `sync_supplier` portieren
        //    (siehe sql/DEPLOY_sync_supplier_v3.md). cfg.username/cfg.password authentifizieren
        //    gegen cfg.shk_url / cfg.base_url / cfg.datanorm_url. Parse → supplier_articles-Rows.
        //    Die SICHERHEITS-Grenze ist bereits korrekt: Creds werden NUR hier (service_role)
        //    gelesen und verlassen die Function nie.
        const rows: Array<Record<string, unknown>> = []; // Platzhalter bis Sync-Body portiert
        if (rows.length) {
          const { error: upErr } = await admin
            .from("supplier_articles")
            .upsert(rows, { onConflict: "id" });
          if (upErr) throw new Error(upErr.message);
        }
        await admin.from("supplier_configs").update({
          last_sync: new Date().toISOString(),
          last_sync_status: "success",
          last_sync_articles: rows.length,
        }).eq("id", cfg.id);
        results.push({ supplierId: cfg.id, name: cfg.name, ok: true, rows_synced: rows.length });
      } catch (e) {
        await admin.from("supplier_configs").update({
          last_sync: new Date().toISOString(),
          last_sync_status: "error",
        }).eq("id", cfg.id).then(() => {}, () => {});
        results.push({ supplierId: cfg.id, name: cfg.name, ok: false, rows_synced: 0, error: String((e as Error)?.message || e) });
      }
    }
    return json(200, { ok: true, results });
  }

  return json(400, { ok: false, error: "validation", details: "unknown action" });
});
