// supabase/functions/supplier-sync/index.ts
// =============================================================================
// EP Kolar — supplier-sync Edge-Function (P0-2 cred-lockdown, Sebastian-Spec v3.10.5)
//   + P2-Fix 2026-06-29 (BUGHUNT-2026-06-17-OFFEN A2): set-credentials validiert
//     jetzt supplierId-Existenz (.select().maybeSingle() → 404 statt stillem No-Op-200)
//     und lehnt leere username/password ab. Rest byte-identisch zur Dashboard-v2.
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
// Autorisierung: sync -> role admin/projektleiter ODER rolle='lagerleitung' (aktiv, nicht gesperrt).
//   set-credentials -> NUR role admin (aktiv, nicht gesperrt) - seit v3.9.1052.
//   public.can_see_supplier_creds() existiert in Prod NICHT; nichts hier stuetzt sich darauf.
// v3.9.1052 Zugangsdaten liegen in public.supplier_credentials (sql/LIEFERANTEN_ZUGANG_v1052_ENTWURF.sql),
//   nicht mehr in supplier_configs. Der Umleit-Trigger dort vertraut service_role NICHT - diese Function
//   schreibt deshalb direkt nach supplier_credentials, erst NACH der Admin-Pruefung. Fehlt die Tabelle
//   (SQL nicht eingespielt), antwortet set-credentials 503 statt Klartext in supplier_configs zu schreiben.
//   AUSLIEFERUNG: diese Function zusammen mit (bzw. vor) dem SQL deployen - die alte live-Fassung schreibt
//   nach supplier_configs, und das verwirft der Trigger nach dem Apply.
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

// v3.9.1052: fehlt die Tabelle (SQL nicht eingespielt)? PostgREST 42P01 / PGRST205.
// deno-lint-ignore no-explicit-any
function tabelleFehlt(e: any): boolean {
  const code = String(e?.code || "");
  return code === "42P01" || code === "PGRST205";
}

// v3.9.1016: Download je Haendler. null = fuer diesen Haendler NICHT implementiert
// (dann meldet sync not_implemented und setzt keinen Sync-Stand). Ein Array = geladene
// supplier_articles-Zeilen (supplier_id, art_nr, ...). Bisher fuer KEINEN Haendler umgesetzt.
// deno-lint-ignore no-explicit-any
async function downloadArticles(_cfg: any): Promise<Array<Record<string, unknown>> | null> {
  return null;
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
  const aktiv = !!callerRow && callerRow.active && !callerRow.locked;
  const allowed = aktiv && (role === "admin" || role === "projektleiter" || rolle === "lagerleitung");
  if (!allowed) return json(403, { ok: false, error: "forbidden", details: "caller may not manage suppliers" });
  const istAdmin = aktiv && role === "admin";

  // 3. Parse
  let body: Partial<Body>;
  try { body = await req.json(); } catch { return json(400, { ok: false, error: "validation", details: "invalid JSON" }); }
  if (!body || typeof body !== "object" || !("action" in body)) {
    return json(400, { ok: false, error: "validation", details: "action required" });
  }

  // 4a. set-credentials — server-only write, never echoes creds back
  if (body.action === "set-credentials") {
    // v3.9.1052: Zugangsdaten setzen NUR Admin (wie die RLS-Policy auf supplier_credentials).
    if (!istAdmin) return json(403, { ok: false, error: "forbidden", details: "only admin may set credentials" });
    const b = body as CredsBody;
    // P2-Fix: leere Strings sind keine gültigen Creds (trim-Check, nicht nur typeof).
    const uName = typeof b.username === "string" ? b.username : "";
    const pWord = typeof b.password === "string" ? b.password : "";
    if (!b.supplierId || !uName.trim() || !pWord.trim()) {
      return json(400, { ok: false, error: "validation", details: "supplierId, non-empty username and password required" });
    }
    // P2-Fix: Existenz der supplierId pruefen (sonst 200 trotz No-Op).
    const { data: cfgRow, error: cfgErr } = await admin
      .from("supplier_configs").select("id").eq("id", b.supplierId).maybeSingle();
    if (cfgErr) return json(500, { ok: false, error: "internal", details: "supplier lookup failed" });
    if (!cfgRow) return json(404, { ok: false, error: "not_found", details: "supplierId does not exist" });
    // v3.9.1052: direkt nach supplier_credentials (service_role), nie mehr nach supplier_configs.
    const { error: upErr } = await admin
      .from("supplier_credentials")
      .upsert({ supplier_id: b.supplierId, username: uName.trim(), password: pWord }, { onConflict: "supplier_id" });
    if (upErr) {
      if (tabelleFehlt(upErr)) return json(503, { ok: false, error: "credentials_table_missing", details: "SQL LIEFERANTEN_ZUGANG_v1052 not applied" });
      return json(500, { ok: false, error: "internal", details: "cred update failed" }); // keine DB-Meldung (koennte Werte zitieren)
    }
    return json(200, { ok: true, supplierId: b.supplierId }); // NO creds in response
  }

  // 4b. sync — read creds server-side, fetch DATANORM/IDS, upsert articles
  if (body.action === "sync") {
    const b = body as SyncBody;
    const q = admin.from("supplier_configs")
      .select("id, name, interface_type, base_url, shk_url, ids_shop_url, unternehmen_id, kunde_nr, datanorm_url, active");
    const { data: cfgRows, error: cfgErr } = b.supplierId ? await q.eq("id", b.supplierId) : await q.eq("active", true);
    if (cfgErr) return json(500, { ok: false, error: "internal", details: "config read failed: " + (cfgErr.message || "") });
    // v3.9.1052: Zugangsdaten aus supplier_credentials (service_role), nur serverseitig an cfg gehaengt.
    const credMap: Record<string, { username: string | null; password: string | null }> = {};
    const ids = (cfgRows || []).map((c: { id: string }) => c.id);
    if (ids.length) {
      const { data: creds, error: credErr } = await admin
        .from("supplier_credentials").select("supplier_id, username, password").in("supplier_id", ids);
      if (credErr && !tabelleFehlt(credErr)) return json(500, { ok: false, error: "internal", details: "credentials read failed" });
      for (const c of (creds || [])) credMap[c.supplier_id] = { username: c.username, password: c.password };
    }
    const cfgs = (cfgRows || []).map((c: Record<string, unknown>) => {
      const z = credMap[c.id as string];
      return { ...c, username: z ? z.username : null, password: z ? z.password : null };
    });

    // v3.9.1016 (Datanorm sauber): KEINE Erfolgsmeldung ohne Download. Vorher war der
    //   Download ein Platzhalter (rows=[]), die Function schrieb trotzdem
    //   last_sync_status="success" mit 0 Artikeln - die App haette dann einen gruenen
    //   "Letzter Sync" ohne geladene Artikel gezeigt. Das betrifft NUR diese Repo-Function
    //   (die App ruft sie nicht auf). Die PRODUKTIVE Function ist sync_supplier im Supabase-
    //   Dashboard (nicht im Repo): sie hat real synchronisiert - Holter am 12.04.2026 rund
    //   25.000 Artikel (shk_connect), seitdem lief kein Sync mehr (Prod-DB, Stand 16.11.2026).
    //   Jetzt: fuer jeden Haendler ohne
    //   implementierten Download ok:false + error:"not_implemented", und last_sync /
    //   last_sync_status bleiben UNBERUEHRT (der Stand des letzten echten Imports gilt weiter).
    //   Einen Download einsetzen = downloadArticles() fuer den Haendler ausfuellen; erst
    //   wenn sie ein Array liefert, wird gespeichert und success gesetzt.
    const results: Array<{ supplierId: string; name: string; ok: boolean; rows_synced: number; error?: string }> = [];
    for (const cfg of (cfgs || [])) {
      try {
        // ── TODO (Sebastian/Chat-Claude): supplier-spezifischen DATANORM/IDS-Download in
        //    downloadArticles einsetzen — Logik aus der Dashboard-Function `sync_supplier`
        //    portieren (siehe sql/DEPLOY_sync_supplier_v3.md). cfg.username/cfg.password
        //    authentifizieren gegen cfg.shk_url / cfg.base_url / cfg.datanorm_url.
        //    Die SICHERHEITS-Grenze ist bereits korrekt: Creds werden NUR hier (service_role)
        //    gelesen und verlassen die Function nie.
        const rows = await downloadArticles(cfg);
        if (rows === null) {
          results.push({ supplierId: cfg.id, name: cfg.name, ok: false, rows_synced: 0, error: "not_implemented" });
          continue; // last_sync / last_sync_status NICHT anfassen
        }
        if (rows.length) {
          const { error: upErr } = await admin
            .from("supplier_articles")
            .upsert(rows, { onConflict: "supplier_id,art_nr" });
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
    const anyOk = results.some((r) => r.ok);
    const allNotImpl = results.length > 0 && results.every((r) => r.error === "not_implemented");
    if (allNotImpl) return json(200, { ok: false, error: "not_implemented", details: "kein automatischer DATANORM-Download fuer diese Haendler eingerichtet - Dateien im Haendlerportal laden und in der App hochladen", results });
    return json(200, { ok: results.length === 0 || anyOk, results });
  }

  return json(400, { ok: false, error: "validation", details: "unknown action" });
});
