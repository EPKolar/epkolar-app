// supabase/functions/ocr_tankbeleg/index.ts
// EP Kolar — Tankbeleg-OCR via Google Cloud Vision (DOCUMENT_TEXT_DETECTION)
// v3.9.1096: km-Erkennung neu (logic.ts): Bezeichnungen KM-STAND/Km:/Tacho/Laufleistung, "123.456 km",
//   Zeilen aus Wortboxen (Spaltensatz), Plausibilitaet gegen kmVorher; Betriebsart art:"tacho" fuer das
//   Tacho-Foto. Antwort abwaertskompatibel (datum/liter/preis/km/confidence/rawText) + km_quelle/km_sicher/art.
// v3.9.419: Aufrufer-Auth (gueltiges User-JWT Pflicht) + Bildgroessen-Limit gegen
//   Kosten-DoS auf der kostenpflichtigen Vision-API. Deploy mit verify_jwt=false
//   (In-Code-getUser-Check spiegelt das Muster von supplier-sync/admin-create-user).
// @ts-ignore - Deno-Runtime
import { createClient } from "https://esm.sh/@supabase/supabase-js@2.45.0";
import { kmAusVision, parseTankbeleg } from "./logic.ts";
const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};
// Max base64-Laenge (~9 MB Binaer). Tankbelege sind komprimierte Handyfotos; verhindert
// 50-MB-Payload-Abuse + Memory-Druck, ohne legitime Fotos abzulehnen.
const MAX_IMAGE_B64 = 12_000_000;
function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { ...CORS, "Content-Type": "application/json" } });
}
Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: CORS });
  if (req.method !== "POST") return json({ ok: false, error: "POST erwartet" }, 405);
  // ── v3.9.419 Aufrufer-Auth: gueltiges User-JWT Pflicht (sonst Kosten-DoS auf Vision) ──
  // @ts-ignore
  const SUPABASE_URL = Deno.env.get("SUPABASE_URL") || "";
  // @ts-ignore
  const ANON_KEY = Deno.env.get("SUPABASE_ANON_KEY") || "";
  const authHdr = req.headers.get("Authorization") || "";
  const jwt = authHdr.toLowerCase().startsWith("bearer ") ? authHdr.slice(7).trim() : "";
  if (!SUPABASE_URL || !ANON_KEY) return json({ ok: false, error: "internal", details: "edge env not configured" }, 500);
  if (!jwt) return json({ ok: false, error: "unauthorized" }, 401);
  try {
    const caller = createClient(SUPABASE_URL, ANON_KEY, {
      global: { headers: { Authorization: `Bearer ${jwt}` } },
      auth: { persistSession: false, autoRefreshToken: false },
    });
    const { data: au, error: aerr } = await caller.auth.getUser();
    if (aerr || !au?.user) return json({ ok: false, error: "unauthorized" }, 401);
  } catch { return json({ ok: false, error: "unauthorized" }, 401); }
  const KEY = Deno.env.get("GOOGLE_VISION_KEY");
  if (!KEY) return json({ ok: false, error: "GOOGLE_VISION_KEY nicht gesetzt" }, 500);
  let image = "";
  let art = "beleg";
  let kmVorher = 0;
  try {
    const body = await req.json();
    image = String(body?.image || "");
    if (body?.art === "tacho") art = "tacho";
    const kv = parseInt(String(body?.kmVorher ?? "").replace(/[^\d]/g, ""), 10);
    if (isFinite(kv) && kv > 0 && kv <= 9999999) kmVorher = kv;
  }
  catch { return json({ ok: false, error: "Body muss JSON mit {image} sein" }, 400); }
  if (!image) return json({ ok: false, error: "Kein Bild uebergeben" }, 400);
  if (image.length > MAX_IMAGE_B64) return json({ ok: false, error: "Bild zu gross (max ~9 MB)" }, 413);
  const content = image.includes(",") ? image.split(",").pop()! : image;
  let visionResp: Response;
  try {
    visionResp = await fetch(`https://vision.googleapis.com/v1/images:annotate?key=${encodeURIComponent(KEY)}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ requests: [{ image: { content }, features: [{ type: art === "tacho" ? "TEXT_DETECTION" : "DOCUMENT_TEXT_DETECTION" }], imageContext: { languageHints: ["de"] } }] }),
    });
  } catch (e) { return json({ ok: false, error: "Vision nicht erreichbar: " + (e as Error).message }, 502); }
  const vj = await visionResp.json().catch(() => ({}));
  if (!visionResp.ok) { const msg = vj?.error?.message || ("Vision HTTP " + visionResp.status); return json({ ok: false, error: msg }, 502); }
  const r0 = vj?.responses?.[0] || {};
  if (r0?.error?.message) return json({ ok: false, error: r0.error.message }, 502);
  const rawText: string = r0?.fullTextAnnotation?.text || "";
  let confidence: number | null = null;
  try { const pages = r0?.fullTextAnnotation?.pages || []; if (pages.length && pages[0]?.confidence != null) confidence = Math.round(pages[0].confidence * 100); } catch { }
  const kmErg = kmAusVision(rawText, r0?.fullTextAnnotation, kmVorher, art);
  const fields = art === "tacho" ? { datum: "", liter: "", preis: "", km: kmErg.km } : parseTankbeleg(rawText, kmErg);
  return json({ ok: true, ...fields, km_quelle: kmErg.quelle, km_sicher: kmErg.sicher, km_stelle: kmErg.stelle, km_unplausibel: kmErg.unplausibel, art, confidence, rawText });
});
