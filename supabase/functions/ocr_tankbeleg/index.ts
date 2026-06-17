// supabase/functions/ocr_tankbeleg/index.ts
// EP Kolar — Tankbeleg-OCR via Google Cloud Vision (DOCUMENT_TEXT_DETECTION)
// v3.9.419: Aufrufer-Auth (gueltiges User-JWT Pflicht) + Bildgroessen-Limit gegen
//   Kosten-DoS auf der kostenpflichtigen Vision-API. Deploy mit verify_jwt=false
//   (In-Code-getUser-Check spiegelt das Muster von supplier-sync/admin-create-user).
// @ts-ignore - Deno-Runtime
import { createClient } from "https://esm.sh/@supabase/supabase-js@2.45.0";
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
function parseTankbeleg(text: string) {
  const t = text || "";
  const norm = (s: string) => String(s).replace(",", ".");
  const out: { datum: string; liter: string; preis: string; km: string } = { datum: "", liter: "", preis: "", km: "" };
  const dm = t.match(/\b(\d{1,2})[.\-\/](\d{1,2})[.\-\/](\d{2,4})\b/);
  if (dm) {
    let dd = +dm[1], mo = +dm[2], yy = +dm[3];
    if (yy < 100) yy += 2000;
    if (dd >= 1 && dd <= 31 && mo >= 1 && mo <= 12 && yy >= 2020 && yy <= 2099) {
      const p2 = (n: number) => (n < 10 ? "0" : "") + n;
      out.datum = `${yy}-${p2(mo)}-${p2(dd)}`;
    }
  }
  let liter: number | null = null;
  const lmA = t.match(/(?:DIESEL|BENZIN|SUPER|AD\s?BLUE|EUROSUPER|OTTO)\D{0,4}(\d{1,3}[.,]\d{1,2})/i);
  const lmB = t.match(/(\d{1,3}[.,]\d{1,2})\s*(?:Liter|Ltr|\bL\b)/i);
  const lcand = lmA?.[1] ?? lmB?.[1] ?? null;
  if (lcand) { const v = parseFloat(norm(lcand)); if (v >= 5 && v <= 200) { liter = v; out.liter = norm(lcand); } }
  let perL: number | null = null;
  const pl = t.match(/PREIS\s*\/?\s*L\D{0,4}(\d[.,]\d{2,3})/i);
  if (pl) { const v = parseFloat(norm(pl[1])); if (v >= 0.8 && v <= 3) perL = v; }
  let total: number | null = null;
  const sm = t.match(/(?:LIEFER\s*SUMME|BETRAG|GESAMT|SUMME|TOTAL|BP[-\s]?ROUTEX)\D{0,8}(\d{1,4}[.,]\d{2})/i) || t.match(/(\d{1,4}[.,]\d{2})\s*(?:€|EUR)/i);
  if (sm) { const v = parseFloat(norm(sm[1])); if (v >= 1 && v <= 5000) total = v; }
  if (liter && perL) {
    const exp = liter * perL;
    if (total && exp > 0 && Math.abs(total - exp) / exp <= 0.12) { } else if ((!total || total < 5) && exp >= 5) total = Math.round(exp * 100) / 100;
  }
  if (total && total >= 1 && total <= 5000) out.preis = total.toFixed(2);
  // km: zeilenbasiert — Label-Zeile finden, dann ueberselbe + max 2 Folgezeilen scannen.
  // (?!\s*\/\d) verwirft STAN/BATCH-Zahlen (z.B. "046183/420" wurde vorher als km gegriffen).
  // 0*([1-9]\d{2,6}) strippt fuehrende Nullen + verlangt erste Ziffer != 0.
  const _lines = t.split(/\r?\n/);
  const _ki = _lines.findIndex((l) => /KILOMETERSTAND/i.test(l));
  let kcand: string | null = null;
  if (_ki >= 0) {
    for (let i = _ki; i <= Math.min(_ki + 2, _lines.length - 1) && !kcand; i++) {
      const m = _lines[i].match(/\b0*([1-9]\d{2,6})\b(?!\s*\/\d)/);
      if (m) kcand = m[1];
    }
  }
  if (!kcand) { const m = t.match(/\b([1-9]\d{2,6})\s*km\b/i); if (m) kcand = m[1]; }
  if (kcand) { const k = parseInt(kcand, 10); if (k >= 1 && k <= 9999999) out.km = String(k); }
  return out;
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
  try { const body = await req.json(); image = String(body?.image || ""); }
  catch { return json({ ok: false, error: "Body muss JSON mit {image} sein" }, 400); }
  if (!image) return json({ ok: false, error: "Kein Bild uebergeben" }, 400);
  if (image.length > MAX_IMAGE_B64) return json({ ok: false, error: "Bild zu gross (max ~9 MB)" }, 413);
  const content = image.includes(",") ? image.split(",").pop()! : image;
  let visionResp: Response;
  try {
    visionResp = await fetch(`https://vision.googleapis.com/v1/images:annotate?key=${encodeURIComponent(KEY)}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ requests: [{ image: { content }, features: [{ type: "DOCUMENT_TEXT_DETECTION" }], imageContext: { languageHints: ["de"] } }] }),
    });
  } catch (e) { return json({ ok: false, error: "Vision nicht erreichbar: " + (e as Error).message }, 502); }
  const vj = await visionResp.json().catch(() => ({}));
  if (!visionResp.ok) { const msg = vj?.error?.message || ("Vision HTTP " + visionResp.status); return json({ ok: false, error: msg }, 502); }
  const r0 = vj?.responses?.[0] || {};
  if (r0?.error?.message) return json({ ok: false, error: r0.error.message }, 502);
  const rawText: string = r0?.fullTextAnnotation?.text || "";
  let confidence: number | null = null;
  try { const pages = r0?.fullTextAnnotation?.pages || []; if (pages.length && pages[0]?.confidence != null) confidence = Math.round(pages[0].confidence * 100); } catch { }
  const fields = parseTankbeleg(rawText);
  return json({ ok: true, ...fields, confidence, rawText });
});
