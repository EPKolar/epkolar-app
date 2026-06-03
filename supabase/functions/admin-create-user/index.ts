// supabase/functions/admin-create-user/index.ts
// =============================================================================
// EP Kolar — B-E Admin-Create-User Edge-Function (Sebastian-Spec v3.10.0)
// =============================================================================
// Ersetzt scheiterndes Client-RPC `/rpc/admin_reset_password` mit User-JWT.
// Atomar: auth.admin.createUser + public.users INSERT + workers-Verknüpfung,
// inkl. Rollback bei Teilfehler.
//
// Env-Vars (Supabase setzt diese automatisch beim Deploy):
//   - SUPABASE_URL
//   - SUPABASE_SERVICE_ROLE_KEY   (NIE clientseitig!)
//   - SUPABASE_ANON_KEY           (für Caller-JWT-Verify)
//
// Aufruf vom Client (siehe docs/B-E-EDGE-FUNCTION-PLAN.md):
//   POST {SUPABASE_URL}/functions/v1/admin-create-user
//   Headers: Authorization: Bearer <user-jwt>, Content-Type: application/json
//   Body:    { username, name, email, password, role, monteurId? }
//
// Responses:
//   200 { ok:true, user:{...}, workerCreated:boolean }
//   400 { ok:false, error:"validation", details:"..." }
//   401 { ok:false, error:"unauthorized" }
//   403 { ok:false, error:"forbidden", details:"caller is not admin" }
//   409 { ok:false, error:"conflict", details:"username/email already exists" }
//   500 { ok:false, error:"internal", details:"...", rolledBack:boolean }
// =============================================================================

// @ts-ignore - Deno-Runtime
import { serve } from "https://deno.land/std@0.224.0/http/server.ts";
// @ts-ignore - Deno-Runtime
import { createClient } from "https://esm.sh/@supabase/supabase-js@2.45.0";

// -- Types ---------------------------------------------------------------------
interface CreateUserBody {
  username: string;
  name: string;
  email: string;
  password: string;
  role: string;
  monteurId?: string | null;
}

interface ErrorResp {
  ok: false;
  error: string;
  details?: string;
  rolledBack?: boolean;
}

interface SuccessResp {
  ok: true;
  user: {
    id: string;
    username: string;
    name: string;
    email: string;
    role: string;
    monteur_id: string | null;
    auth_user_id: string;
    active: boolean;
    locked: boolean;
  };
  workerCreated: boolean;
}

// -- Helpers -------------------------------------------------------------------
const CORS_HEADERS: Record<string, string> = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Allow-Headers":
    "authorization, x-client-info, apikey, content-type",
};

function json(status: number, body: ErrorResp | SuccessResp): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...CORS_HEADERS, "Content-Type": "application/json" },
  });
}

function isValidEmail(s: string): boolean {
  // Pragmatic, no over-engineering — same shape as client (B-020).
  return typeof s === "string" && s.length >= 5 && s.indexOf("@") >= 1 &&
    s.indexOf(".", s.indexOf("@")) > s.indexOf("@");
}

function validate(b: Partial<CreateUserBody>): string | null {
  if (!b || typeof b !== "object") return "body missing";
  if (!b.username || typeof b.username !== "string" || b.username.trim().length < 2) {
    return "username required (min 2 chars)";
  }
  if (!b.name || typeof b.name !== "string" || b.name.trim().length < 2) {
    return "name required (min 2 chars)";
  }
  if (!b.email || !isValidEmail(b.email.trim())) {
    return "valid email required";
  }
  if (!b.password || typeof b.password !== "string" || b.password.length < 4) {
    return "password required (min 4 chars)";
  }
  if (!b.role || typeof b.role !== "string") return "role required";
  const allowedRoles = [
    "admin",
    "buero",
    "monteur",
    "techniker",
    "lehrling",
    "extern",
    "projektleiter",
    "geschaeftsfuehrer",
  ];
  if (allowedRoles.indexOf(b.role) === -1) return "role invalid";
  return null;
}

function genTextId(): string {
  // Mirrors client `uid()` pattern (text PK in public.users).
  return "u" + Math.random().toString(36).slice(2, 10) +
    Date.now().toString(36).slice(-4);
}

// -- Main handler --------------------------------------------------------------
serve(async (req: Request) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: CORS_HEADERS });
  }
  if (req.method !== "POST") {
    return json(405, { ok: false, error: "method_not_allowed" });
  }

  // @ts-ignore - Deno-Runtime
  const SUPABASE_URL = Deno.env.get("SUPABASE_URL") || "";
  // @ts-ignore - Deno-Runtime
  const SERVICE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") || "";
  // @ts-ignore - Deno-Runtime
  const ANON_KEY = Deno.env.get("SUPABASE_ANON_KEY") || "";
  if (!SUPABASE_URL || !SERVICE_KEY || !ANON_KEY) {
    return json(500, {
      ok: false,
      error: "internal",
      details: "edge-function env not configured",
    });
  }

  // -- 1. Caller-JWT extraction
  const authHdr = req.headers.get("Authorization") || "";
  const jwt = authHdr.toLowerCase().startsWith("bearer ")
    ? authHdr.slice(7).trim()
    : "";
  if (!jwt) return json(401, { ok: false, error: "unauthorized" });

  // -- 2. Verify caller + role=admin via public.users (auth_user_id join).
  const callerClient = createClient(SUPABASE_URL, ANON_KEY, {
    global: { headers: { Authorization: `Bearer ${jwt}` } },
    auth: { persistSession: false, autoRefreshToken: false },
  });
  const { data: callerAuth, error: callerErr } = await callerClient.auth
    .getUser();
  if (callerErr || !callerAuth?.user) {
    return json(401, { ok: false, error: "unauthorized", details: "jwt invalid" });
  }
  const callerAuthUid = callerAuth.user.id;

  // service_role client for privileged ops
  const adminClient = createClient(SUPABASE_URL, SERVICE_KEY, {
    auth: { persistSession: false, autoRefreshToken: false },
  });

  const { data: callerRow, error: callerLookupErr } = await adminClient
    .from("users")
    .select("id, role, active, locked")
    .eq("auth_user_id", callerAuthUid)
    .maybeSingle();
  if (callerLookupErr) {
    return json(500, {
      ok: false,
      error: "internal",
      details: "caller lookup failed: " + (callerLookupErr.message || ""),
    });
  }
  if (!callerRow || callerRow.role !== "admin" || !callerRow.active || callerRow.locked) {
    return json(403, {
      ok: false,
      error: "forbidden",
      details: "caller is not active admin",
    });
  }

  // -- 3. Validate input
  let body: Partial<CreateUserBody>;
  try {
    body = await req.json();
  } catch (_e) {
    return json(400, { ok: false, error: "validation", details: "invalid JSON" });
  }
  const vErr = validate(body);
  if (vErr) return json(400, { ok: false, error: "validation", details: vErr });
  const b = body as CreateUserBody;
  const username = b.username.trim();
  const name = b.name.trim();
  const email = b.email.trim().toLowerCase();
  const password = b.password;
  const role = b.role;
  const monteurId = b.monteurId && String(b.monteurId).trim()
    ? String(b.monteurId).trim()
    : null;

  // -- 4. Conflict pre-check (username + email) — zwei sichere .eq()-Lookups statt
  //       .or() mit roher String-Interpolation (PostgREST-Filter-Injection via ,/) vermeiden).
  const { data: dupUser, error: dupUErr } = await adminClient
    .from("users").select("id").eq("username", username).maybeSingle();
  if (dupUErr) {
    return json(500, { ok: false, error: "internal", details: "dup-check(username) failed: " + (dupUErr.message || "") });
  }
  const { data: dupEmail, error: dupEErr } = await adminClient
    .from("users").select("id").eq("email", email).maybeSingle();
  if (dupEErr) {
    return json(500, { ok: false, error: "internal", details: "dup-check(email) failed: " + (dupEErr.message || "") });
  }
  if (dupUser || dupEmail) {
    return json(409, {
      ok: false,
      error: "conflict",
      details: "username or email already exists",
    });
  }

  // -- 5. auth.admin.createUser
  let authUuid = "";
  const { data: created, error: createErr } = await adminClient.auth.admin
    .createUser({
      email,
      password,
      email_confirm: true,
      user_metadata: { username, name, role },
    });
  if (createErr || !created?.user) {
    return json(500, {
      ok: false,
      error: "internal",
      details: "auth.admin.createUser failed: " +
        (createErr?.message || "no user returned"),
    });
  }
  authUuid = created.user.id;

  // -- 6. Optional workers-Row (monteur/techniker without explicit monteurId)
  let workerCreated = false;
  let resolvedMonteurId: string | null = monteurId;
  if (!resolvedMonteurId && (role === "monteur" || role === "techniker")) {
    const newWorkerId = "w" + Math.random().toString(36).slice(2, 10) +
      Date.now().toString(36).slice(-4);
    const { data: wRow, error: wErr } = await adminClient
      .from("workers")
      .insert({
        id: newWorkerId,
        name,        // workers.name = "Nachname Vorname" (Client komponiert getrennte Felder)
        vorname: "", // Tabelle hat separate vorname-Spalte — explizit leer statt silent default
        role,
        active: true,
      })
      .select("id")
      .maybeSingle();
    if (wErr) {
      // Rollback auth.users — partial state must not persist.
      await adminClient.auth.admin.deleteUser(authUuid).catch(() => {});
      return json(500, {
        ok: false,
        error: "internal",
        details: "workers insert failed: " + (wErr.message || ""),
        rolledBack: true,
      });
    }
    resolvedMonteurId = wRow?.id || newWorkerId;
    workerCreated = true;
  }

  // -- 7. public.users INSERT (atomic with auth.users — rollback on failure)
  const newUserId = genTextId();
  const insertPayload = {
    id: newUserId,
    username,
    name,
    email,
    role,
    monteur_id: resolvedMonteurId,
    auth_user_id: authUuid,
    active: true,
    locked: false,
    // v3.9.104 FIX: public.users hat KEINE 'created'-Spalte (nur created_at, DB-default) →
    // der frühere created-Insert ließ jeden Call mit PGRST204 fehlschlagen (500). Entfernt.
  };
  const { data: userRow, error: insErr } = await adminClient
    .from("users")
    .insert(insertPayload)
    .select(
      "id, username, name, email, role, monteur_id, auth_user_id, active, locked",
    )
    .maybeSingle();
  if (insErr || !userRow) {
    // Rollback: delete auth.users (and worker if we just created it)
    await adminClient.auth.admin.deleteUser(authUuid).catch(() => {});
    if (workerCreated && resolvedMonteurId) {
      await adminClient.from("workers").delete().eq("id", resolvedMonteurId).then(
        () => {},
        () => {},
      );
    }
    return json(500, {
      ok: false,
      error: "internal",
      details: "users insert failed: " + (insErr?.message || "no row returned"),
      rolledBack: true,
    });
  }

  return json(200, { ok: true, user: userRow as SuccessResp["user"], workerCreated });
});