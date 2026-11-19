// kamera-stream — kurzlebige Stream-Freigaben fuer die Kameras (EPKolar Phase 1, 19.11.2026)
//
// NICHT DEPLOYT. Deploy-Parameter und Token-Vertrag: README.md daneben.
// Die gesamte Entscheidung steht in ./logic.ts (rein, in Node getestet). Diese Datei verdrahtet nur:
//   authUser    -> auth.getUser(jwt) mit dem Service-Client (prueft Signatur + Ablauf beim Auth-Server)
//   ladeNutzer  -> public.users (id, role, active, locked) per auth_user_id, Service-Client
//   darfSehen   -> rpc kamera_darf_sehen(p_kamera) mit dem JWT DES AUFRUFERS (auth.uid() = Aufrufer),
//                  OHNE p_zeitpunkt -> die Datenbank nimmt now() (Serverzeit, Wiener Ortszeit in SQL)
//   ladeBackend -> public.kamera_backend (nur service_role lesbar), Phase 2 mit stream_typ
//   protokoll   -> public.kamera_abruf_log (nur service_role schreibt)
// Secrets: KAMERA_TOKEN_SECRET (>= 32 Zeichen), KAMERA_BACKEND_BASE (https://...), optional KAMERA_TOKEN_TTL
// (30..120 s, Standard 90) und KAMERA_AUFZEICHNUNG_ROLLEN (Standard admin,projektleiter,buero).
import { createClient } from "npm:@supabase/supabase-js@2";
import { bearbeite, type Deps, type Nutzer, type Backend, type Protokoll } from "./logic.ts";

const SUPABASE_URL = Deno.env.get("SUPABASE_URL") ?? "";
const ANON_KEY = Deno.env.get("SUPABASE_ANON_KEY") ?? "";
const SERVICE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? "";
const OHNE_SITZUNG = { persistSession: false, autoRefreshToken: false };

const dienst = createClient(SUPABASE_URL, SERVICE_KEY, { auth: OHNE_SITZUNG });

function aufruferClient(jwt: string) {
  return createClient(SUPABASE_URL, ANON_KEY, {
    global: { headers: { Authorization: "Bearer " + jwt } },
    auth: OHNE_SITZUNG,
  });
}

const deps: Deps = {
  env: (name: string) => Deno.env.get(name),
  now: () => Date.now(),
  authUser: async (jwt: string) => {
    const { data, error } = await dienst.auth.getUser(jwt);
    if (error || !data || !data.user) return null;
    return data.user.id;
  },
  ladeNutzer: async (authUid: string): Promise<Nutzer | null> => {
    const { data, error } = await dienst.from("users").select("id, role, active, locked").eq("auth_user_id", authUid).limit(1);
    if (error) throw new Error("db");
    if (!data || !data.length) return null;
    const r = data[0] as Record<string, unknown>;
    return { id: String(r.id ?? ""), role: r.role === null || r.role === undefined ? null : String(r.role), active: r.active, locked: r.locked };
  },
  darfSehen: async (jwt: string, kameraId: string) => {
    const { data, error } = await aufruferClient(jwt).rpc("kamera_darf_sehen", { p_kamera: kameraId });
    if (error) throw new Error("db");
    return data === true;
  },
  ladeBackend: async (kameraId: string): Promise<Backend | null> => {
    const { data, error } = await dienst.from("kamera_backend").select("stream_name, aufzeichnung_quelle, stream_typ").eq("kamera_id", kameraId).limit(1);
    if (error) throw new Error("db");
    if (!data || !data.length) return null;
    const r = data[0] as Record<string, unknown>;
    return {
      stream_name: String(r.stream_name ?? ""),
      aufzeichnung_quelle: r.aufzeichnung_quelle === null || r.aufzeichnung_quelle === undefined ? null : String(r.aufzeichnung_quelle),
      stream_typ: r.stream_typ === null || r.stream_typ === undefined ? null : String(r.stream_typ),
    };
  },
  protokoll: async (e: Protokoll) => {
    await dienst.from("kamera_abruf_log").insert(e);
  },
};

Deno.serve(async (req: Request) => {
  if (!SUPABASE_URL || !ANON_KEY || !SERVICE_KEY) {
    return new Response(JSON.stringify({ error: "nicht_konfiguriert" }), {
      status: 503,
      headers: { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store" },
    });
  }
  return await bearbeite(req, deps);
});
