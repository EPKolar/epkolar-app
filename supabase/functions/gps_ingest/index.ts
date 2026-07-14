// supabase/functions/gps_ingest/index.ts
// EP Kolar — Traccar -> fz_positions. Die Aufnahme der GPS-Rohpunkte.
//
// WER RUFT DAS AUF: Traccar, nicht ein Benutzer. Traccar hat kein Supabase-JWT und wird
// nie eines haben. Darum:
//   - Deploy mit verify_jwt=false
//   - Authentifizierung ueber ein GEHEIMNIS (Header x-gps-token ODER ?token=..., weil
//     aeltere Traccar-Versionen keine Custom-Header im Forward koennen — dann bleibt nur
//     der Query-Parameter).
//   - Geschrieben wird mit dem SERVICE_ROLE_KEY: fz_positions hat bewusst KEINE
//     Insert-Policy (sql/GPS_v1.sql), niemand ausser dieser Function darf Rohpunkte anlegen.
//
// TRACCAR-EIGENHEITEN, die hier bewusst behandelt werden:
//   1. position.speed ist in KNOTEN, nicht km/h. Wer das ungerechnet speichert, hat eine
//      Flotte, die dauerhaft ~46% zu langsam faehrt (1 kn = 1,852 km/h). Das ist der
//      klassische Traccar-Fehler. Wir rechnen um und speichern km/h.
//   2. device.uniqueId ist die IMEI. Sie ist der EINZIGE Schluessel zum Fahrzeug
//      (fahrzeuge.tracker_imei). Ist sie dort nicht eingetragen, kennen wir das Fahrzeug
//      nicht — dann wird NICHT still verworfen, sondern mit 200 + unmapped:true geantwortet
//      und die IMEI geloggt. 200 ist Absicht: bei !=2xx wiederholt Traccar den Forward
//      endlos, und ein unbekannter Tracker wuerde die Queue zumuellen. Der Fix liegt im
//      Buero (IMEI am Fahrzeug eintragen), nicht im Retry.
//   3. fixTime ist der Zeitpunkt der Ortung, serverTime nur der Empfang. Wir nehmen
//      fixTime (Fallback deviceTime, dann serverTime) — sonst verschiebt eine
//      Funkloch-Nachlieferung die ganze Fahrt.
//   4. Traccar wiederholt Forwards bei Fehlern. Darum ist der Insert idempotent ueber den
//      Unique-Index (fahrzeug_id, ts) aus sql/GPS_INGEST_v1.sql -> ON CONFLICT DO NOTHING.
//
// @ts-ignore - Deno-Runtime
import { createClient } from "https://esm.sh/@supabase/supabase-js@2.45.0";

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type, x-gps-token",
};

const KNOTS_TO_KMH = 1.852;

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...CORS, "Content-Type": "application/json" },
  });
}

/** Traccar-Position -> fz_positions-Zeile. Gibt null zurueck, wenn der Punkt unbrauchbar ist. */
function mapPosition(p: any, fahrzeugId: string) {
  if (!p) return null;
  const lat = Number(p.latitude);
  const lon = Number(p.longitude);
  // Ein Tracker ohne Fix meldet gern 0/0 (Nullinsel im Golf von Guinea). Solche Punkte
  // wuerden die Karte und jede Distanzrechnung zerstoeren.
  if (!isFinite(lat) || !isFinite(lon)) return null;
  if (lat === 0 && lon === 0) return null;
  if (lat < -90 || lat > 90 || lon < -180 || lon > 180) return null;
  // valid:false = Traccar selbst haelt den Fix fuer unbrauchbar.
  if (p.valid === false) return null;

  const ts = p.fixTime || p.deviceTime || p.serverTime;
  if (!ts) return null;

  const attrs = (p.attributes && typeof p.attributes === "object") ? p.attributes : {};
  const knots = Number(p.speed);
  const speedKmh = isFinite(knots) ? Math.round(knots * KNOTS_TO_KMH * 10) / 10 : null;

  let ignition: boolean | null = null;
  if (typeof attrs.ignition === "boolean") ignition = attrs.ignition;

  return {
    fahrzeug_id: fahrzeugId,
    ts: new Date(ts).toISOString(),
    lat,
    lon,
    speed: speedKmh,
    ignition,
    raw: p, // Rohpunkt aufheben — was wir heute nicht auswerten, wollen wir spaeter nicht neu erfinden.
  };
}

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: CORS });
  if (req.method !== "POST") return json({ error: "method_not_allowed" }, 405);

  // ── Geheimnis pruefen ──────────────────────────────────────────────────────
  const expected = Deno.env.get("GPS_INGEST_TOKEN");
  if (!expected) {
    // Lieber laut scheitern als ungeschuetzt Rohpunkte annehmen.
    console.error("[gps_ingest] GPS_INGEST_TOKEN ist nicht gesetzt — Function verweigert den Dienst.");
    return json({ error: "not_configured" }, 500);
  }
  const url = new URL(req.url);
  const got = req.headers.get("x-gps-token") || url.searchParams.get("token") || "";
  if (got !== expected) return json({ error: "unauthorized" }, 401);

  // ── Payload ────────────────────────────────────────────────────────────────
  let body: any;
  try {
    body = await req.json();
  } catch {
    return json({ error: "bad_json" }, 400);
  }

  // Traccar schickt {position, device}. Wir akzeptieren zusaetzlich ein Array davon,
  // falls jemand spaeter buendelt.
  const items: any[] = Array.isArray(body) ? body : [body];

  const supabase = createClient(
    Deno.env.get("SUPABASE_URL") ?? "",
    Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? "",
    { auth: { persistSession: false } },
  );

  // IMEI -> fahrzeug_id. Ein Request enthaelt fast immer genau einen Tracker; der Cache
  // spart den zweiten Lookup, wenn doch gebuendelt wird.
  const imeiCache = new Map<string, string | null>();
  async function fahrzeugFuerImei(imei: string): Promise<string | null> {
    if (imeiCache.has(imei)) return imeiCache.get(imei) ?? null;
    const { data, error } = await supabase
      .from("fahrzeuge")
      .select("id")
      .eq("tracker_imei", imei)
      .limit(1);
    if (error) {
      console.error("[gps_ingest] fahrzeuge-Lookup fehlgeschlagen:", error.message);
      imeiCache.set(imei, null);
      return null;
    }
    const id = (data && data[0] && data[0].id) ? String(data[0].id) : null;
    imeiCache.set(imei, id);
    return id;
  }

  const rows: any[] = [];
  const unmapped: string[] = [];
  let verworfen = 0;

  for (const it of items) {
    const pos = it?.position ?? it;
    const dev = it?.device ?? {};
    const imei = String(dev.uniqueId ?? pos?.uniqueId ?? "").trim();
    if (!imei) { verworfen++; continue; }

    const fid = await fahrzeugFuerImei(imei);
    if (!fid) {
      // Tracker meldet, aber niemand hat die IMEI am Fahrzeug hinterlegt.
      if (!unmapped.includes(imei)) unmapped.push(imei);
      continue;
    }

    const row = mapPosition(pos, fid);
    if (!row) { verworfen++; continue; }
    rows.push(row);
  }

  if (rows.length) {
    // Idempotent: Traccar wiederholt Forwards. Der Unique-Index (fahrzeug_id, ts) faengt
    // die Wiederholung ab, statt die Historie zu verdoppeln.
    const { error } = await supabase
      .from("fz_positions")
      .upsert(rows, { onConflict: "fahrzeug_id,ts", ignoreDuplicates: true });
    if (error) {
      console.error("[gps_ingest] Insert fehlgeschlagen:", error.message);
      // 500 -> Traccar wiederholt. Das ist hier RICHTIG: ein DB-Ausfall darf keine
      // Positionen verschlucken (anders als eine unbekannte IMEI, die nie besser wird).
      return json({ error: "insert_failed", detail: error.message }, 500);
    }
  }

  if (unmapped.length) {
    console.warn("[gps_ingest] IMEI keinem Fahrzeug zugeordnet:", unmapped.join(", "));
  }

  // Immer 200, wenn die DB mitgespielt hat — auch bei unmapped/verworfen. Sonst retryt
  // Traccar einen Zustand, den nur das Buero aufloesen kann.
  return json({
    ok: true,
    gespeichert: rows.length,
    verworfen,
    unmapped, // IMEIs ohne Fahrzeug — im Fahrzeug-Formular eintragen
  });
});
