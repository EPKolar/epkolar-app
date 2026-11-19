// portal-foto — Kundenportal-Fotos in den privaten Speicher (EPKolar, v3.9.1047)
//
// Dauerregel 18.11.2026: die Datenbank speichert nie Dateien. Der anonyme Portal-Kunde darf nicht direkt in
// Supabase Storage schreiben; diese Function prueft den Portal-Code (wie portal_submit_defect), Typ, Groesse,
// Bildkennung (magic bytes) und Obergrenzen und legt das Foto mit dem Service-Schluessel im PRIVATEN Bucket ab.
//
// Deploy mit verify_jwt=true: das Portal schickt den anon-Schluessel als Bearer.
//
// POST {code, defect_id, name, dataUrl}
//   -> 200 {path:"sbpriv:epkolar-docs/portal/<projectId>/<defectId>/<name>.<ext>", url:<signierte Adresse, 7 Tage>}
//   name = Foto-Schluessel des Clients ([A-Za-z0-9_-]{8,64}); gleiche Anfrage nochmal = gleiches Objekt (idempotent).
//   Ungueltiger/fehlender name -> zufaellige UUID.
// POST {code, action:"sign", paths:[...]}
//   -> 200 {urls:{<eingegebener Pfad>: <signierte Adresse, 7 Tage>}} — nur Pfade unter portal/<projectId des Codes>/
//
// Fehler: {error:<kurzer Code>} — nie Details, nie Schluessel.
import { createClient } from "npm:@supabase/supabase-js@2";

const BUCKET = "epkolar-docs";
const REF_PREFIX = "sbpriv:" + BUCKET + "/";
const MAX_BYTES = 4 * 1024 * 1024; // decodiert
const MAX_BODY_CHARS = 6 * 1024 * 1024; // Base64 von 4 MB = ~5,6 Mio Zeichen + JSON
const MAX_PER_DEFECT = 10;
const MAX_PER_PROJECT_24H = 60;
const MAX_SIGN_PATHS = 50;
const SIGN_SECONDS = 7 * 24 * 3600;
const ALLOWED_ORIGINS = ["https://epkolar.github.io"];
const MIME_EXT: Record<string, string> = { "image/jpeg": "jpg", "image/png": "png", "image/webp": "webp" };
const SEG_RE = /^[A-Za-z0-9_-]{1,64}$/;
const KEY_RE = /^[A-Za-z0-9_-]{8,64}$/;

const SUPABASE_URL = Deno.env.get("SUPABASE_URL") ?? "";
const SERVICE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? "";
const sb = createClient(SUPABASE_URL, SERVICE_KEY, { auth: { persistSession: false, autoRefreshToken: false } });

function cors(req: Request): Record<string, string> {
  const o = req.headers.get("origin") ?? "";
  return {
    "Access-Control-Allow-Origin": ALLOWED_ORIGINS.includes(o) ? o : ALLOWED_ORIGINS[0],
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
    "Access-Control-Max-Age": "86400",
    "Vary": "Origin",
  };
}

function json(req: Request, status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...cors(req), "Content-Type": "application/json; charset=utf-8" },
  });
}

// Portal-Code genau wie portal_submit_defect: btrim, Laenge >= 3, projects.portal_code = Code AND portal_code <> ''
async function projectForCode(code: unknown): Promise<string | null> {
  if (typeof code !== "string") return null;
  const c = code.trim();
  if (c.length < 3 || c.length > 64) return null;
  const { data, error } = await sb.from("projects").select("id").eq("portal_code", c).neq("portal_code", "").limit(1);
  if (error || !data || !data.length) return null;
  const pid = String(data[0].id ?? "");
  // Pfadsegment muss sicher sein (Projekt-Ids sind uid()-Texte); sonst lieber ablehnen als einen kaputten Pfad bauen
  return SEG_RE.test(pid) ? pid : null;
}

function decodeBase64(b64: string): Uint8Array | null {
  try {
    const bin = atob(b64);
    const out = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
    return out;
  } catch {
    return null;
  }
}

function magicMatches(mime: string, b: Uint8Array): boolean {
  if (mime === "image/jpeg") return b.length > 3 && b[0] === 0xff && b[1] === 0xd8 && b[2] === 0xff;
  if (mime === "image/png") {
    const sig = [0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a];
    return b.length > 8 && sig.every((v, i) => b[i] === v);
  }
  if (mime === "image/webp") {
    // "RIFF" ???? "WEBP"
    return b.length > 12 && b[0] === 0x52 && b[1] === 0x49 && b[2] === 0x46 && b[3] === 0x46 &&
      b[8] === 0x57 && b[9] === 0x45 && b[10] === 0x42 && b[11] === 0x50;
  }
  return false;
}

type Entry = { name: string; id: string | null; created_at?: string | null };

async function listFolder(prefix: string): Promise<Entry[] | null> {
  const { data, error } = await sb.storage.from(BUCKET).list(prefix, { limit: 1000, offset: 0 });
  if (error) return null;
  return (data ?? []) as Entry[];
}

// Objekte (id != null) der letzten 24 h unter portal/<pid>/*/ zaehlen; bricht ab, sobald die Grenze erreicht ist.
async function countProject24h(pid: string): Promise<number | null> {
  const folders = await listFolder("portal/" + pid);
  if (folders === null) return null;
  const since = Date.now() - 24 * 3600 * 1000;
  let n = 0;
  for (const f of folders) {
    if (f.id !== null) continue; // nur Unterordner (= Maengel)
    const objs = await listFolder("portal/" + pid + "/" + f.name);
    if (objs === null) return null;
    for (const o of objs) {
      if (o.id === null) continue;
      const t = o.created_at ? Date.parse(o.created_at) : Date.now();
      if (t >= since) n++;
    }
    if (n >= MAX_PER_PROJECT_24H) return n;
  }
  return n;
}

async function signOne(path: string): Promise<string | null> {
  const { data, error } = await sb.storage.from(BUCKET).createSignedUrl(path, SIGN_SECONDS);
  if (error || !data?.signedUrl) return null;
  return data.signedUrl;
}

async function handleUpload(req: Request, pid: string, body: Record<string, unknown>): Promise<Response> {
  const did = typeof body.defect_id === "string" ? body.defect_id : "";
  if (!SEG_RE.test(did)) return json(req, 400, { error: "invalid_defect" });

  const dataUrl = typeof body.dataUrl === "string" ? body.dataUrl : "";
  const m = /^data:([a-z0-9.+\/-]+);base64,/i.exec(dataUrl.slice(0, 80));
  if (!m) return json(req, 400, { error: "bad_type" });
  const mime = m[1].toLowerCase();
  const ext = MIME_EXT[mime];
  if (!ext) return json(req, 415, { error: "bad_type" });
  const b64 = dataUrl.slice(m[0].length);
  if (b64.length > Math.ceil(MAX_BYTES / 3) * 4 + 4) return json(req, 413, { error: "too_large" });
  const bytes = decodeBase64(b64);
  if (!bytes || bytes.length === 0) return json(req, 400, { error: "bad_image" });
  if (bytes.length > MAX_BYTES) return json(req, 413, { error: "too_large" });
  if (!magicMatches(mime, bytes)) return json(req, 400, { error: "bad_image" });

  const key = typeof body.name === "string" && KEY_RE.test(body.name) ? body.name : crypto.randomUUID();
  const folder = "portal/" + pid + "/" + did;
  const objName = key + "." + ext;
  const path = folder + "/" + objName;

  const inFolder = await listFolder(folder);
  if (inFolder === null) return json(req, 503, { error: "storage_unavailable" });
  // Wiederholung desselben Fotos (gleicher Schluessel): vorhandenes Objekt zurueckgeben, nichts neu anlegen
  if (inFolder.some((o) => o.id !== null && o.name === objName)) {
    return json(req, 200, { path: REF_PREFIX + path, url: await signOne(path) });
  }
  if (inFolder.filter((o) => o.id !== null).length >= MAX_PER_DEFECT) return json(req, 429, { error: "limit_defect" });
  const n24 = await countProject24h(pid);
  if (n24 === null) return json(req, 503, { error: "storage_unavailable" });
  if (n24 >= MAX_PER_PROJECT_24H) return json(req, 429, { error: "limit_project" });

  const { error } = await sb.storage.from(BUCKET).upload(path, bytes, { contentType: mime, upsert: false, cacheControl: "3600" });
  if (error) {
    const msg = String((error as { message?: string }).message ?? "");
    const sc = String((error as { statusCode?: string | number }).statusCode ?? "");
    // Wettlauf zweier gleicher Versuche: das Objekt existiert schon -> wie Wiederholung behandeln
    if (sc === "409" || /exists|duplicate/i.test(msg)) {
      return json(req, 200, { path: REF_PREFIX + path, url: await signOne(path) });
    }
    console.error("[portal-foto] upload failed", sc);
    return json(req, 502, { error: "upload_failed" });
  }
  return json(req, 200, { path: REF_PREFIX + path, url: await signOne(path) });
}

async function handleSign(req: Request, pid: string, body: Record<string, unknown>): Promise<Response> {
  const paths = Array.isArray(body.paths) ? body.paths : null;
  if (!paths || paths.length > MAX_SIGN_PATHS) return json(req, 400, { error: "invalid_paths" });
  const prefix = "portal/" + pid + "/";
  const wanted: { input: string; path: string }[] = [];
  for (const p of paths) {
    if (typeof p !== "string" || p.length > 300) continue;
    const path = p.startsWith(REF_PREFIX) ? p.slice(REF_PREFIX.length) : p;
    if (!path.startsWith(prefix)) continue; // fremdes Projekt / anderer Bereich: still auslassen
    const rest = path.slice(prefix.length).split("/");
    if (rest.length !== 2 || !SEG_RE.test(rest[0]) || !/^[A-Za-z0-9_-]{1,64}\.(jpg|png|webp)$/.test(rest[1])) continue;
    wanted.push({ input: p, path });
  }
  const urls: Record<string, string> = {};
  if (wanted.length) {
    const { data, error } = await sb.storage.from(BUCKET).createSignedUrls(wanted.map((w) => w.path), SIGN_SECONDS);
    if (error) return json(req, 503, { error: "storage_unavailable" });
    for (const d of data ?? []) {
      if (!d || d.error || !d.signedUrl) continue;
      const w = wanted.find((x) => x.path === d.path);
      if (w) urls[w.input] = d.signedUrl;
    }
  }
  return json(req, 200, { urls });
}

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors(req) });
  if (req.method !== "POST") return json(req, 405, { error: "method_not_allowed" });
  try {
    if (!SUPABASE_URL || !SERVICE_KEY) return json(req, 500, { error: "not_configured" });
    const len = Number(req.headers.get("content-length") ?? "0");
    if (len > MAX_BODY_CHARS) return json(req, 413, { error: "too_large" });
    const text = await req.text();
    if (text.length > MAX_BODY_CHARS) return json(req, 413, { error: "too_large" });
    let body: Record<string, unknown>;
    try {
      const parsed = JSON.parse(text);
      if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) return json(req, 400, { error: "bad_request" });
      body = parsed as Record<string, unknown>;
    } catch {
      return json(req, 400, { error: "bad_request" });
    }
    const pid = await projectForCode(body.code);
    if (!pid) return json(req, 403, { error: "invalid_code" });
    if (body.action === "sign") return await handleSign(req, pid, body);
    if (body.action !== undefined && body.action !== "upload") return json(req, 400, { error: "bad_request" });
    return await handleUpload(req, pid, body);
  } catch (e) {
    console.error("[portal-foto] unexpected", e instanceof Error ? e.name : "error");
    return json(req, 500, { error: "server_error" });
  }
});
