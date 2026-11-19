// kamera-stream / logic.ts — reine Pruef- und Token-Logik (EPKolar Kameras Phase 1, 19.11.2026)
//
// Bewusst OHNE Importe und ohne Deno-Globals: alles, was nach aussen greift (Auth, Datenbank, Umgebung, Uhr),
// kommt ueber `Deps` herein. Dadurch laeuft genau dieser Code in Node (tests/test_kameras_phase1_v1055.py, Node 24
// mit Typ-Abstreifung) gegen Attrappen — und in Deno (index.ts) gegen die echten Dienste.
// Nur abstreifbare TypeScript-Syntax verwenden (keine enum/namespace/Parameter-Eigenschaften).
//
// SICHERHEITSKERN (Lehre fz_finanzen: Verstecken im Client ist KEIN Schutz):
//   1. JWT des Aufrufers pruefen (auth.getUser)            -> sonst 401
//   2. Nutzerzeile: aktiv, nicht gesperrt                  -> sonst 403
//   3. Rolle in ERLAUBTE_ROLLEN (Monteure NIE)             -> sonst 403   (vor jeder weiteren Abfrage)
//   4. Konfiguration (Secret, Backend-Basis)               -> sonst 503
//   5. Anfrage gueltig                                     -> sonst 400
//   6. Aufzeichnung: nur geraet=pc UND Rolle in AUFZEICHNUNG_ROLLEN -> sonst 403
//   7. kamera_darf_sehen(kamera) mit dem JWT des Aufrufers, Serverzeit (Europe/Vienna in SQL) -> sonst 403
//   8. Backend-Zuordnung (service_role)                    -> sonst 503
//   9. kurzlebiges HMAC-Token (<= 120 s), URL bauen        -> 200
//      Phase 2: die Adressart folgt kamera_backend.stream_typ (webrtc | llhls | mjpeg | snapshot) und wird
//      ERST NACH allen Pruefungen 1-8 gewaehlt; unbekannter Typ -> 503. Gleiches Token fuer jede Art.
// Fehlerantworten tragen NUR {error:<Code>} — nie eine Adresse, nie einen Streamnamen, nie Details.

export const ERLAUBTE_ROLLEN: readonly string[] = ["admin", "projektleiter", "buero", "lagerleitung"];
export const STANDARD_AUFZEICHNUNG_ROLLEN: readonly string[] = ["admin", "projektleiter", "buero"];
export const ALLOWED_ORIGINS: readonly string[] = ["https://epkolar.github.io"];
export const TTL_MIN = 30;
export const TTL_MAX = 120;
export const TTL_STANDARD = 90;
export const SECRET_MIN_LAENGE = 32;
export const MAX_BODY = 2048;
export const TOKEN_VERSION = 1;
// Phase 2: Adressarten je Kamera (Spalte kamera_backend.stream_typ). Fehlt der Wert -> webrtc (Phase-1-Verhalten).
export const STREAM_TYPEN: readonly string[] = ["webrtc", "llhls", "mjpeg", "snapshot"];
export const STANDARD_STREAM_TYP = "webrtc";

const ID_RE = /^[A-Za-z0-9_-]{1,64}$/;

export type Scope = "live" | "aufzeichnung";
export type StreamTyp = "webrtc" | "llhls" | "mjpeg" | "snapshot";

export type Nutzer = { id: string; role: string | null; active: unknown; locked: unknown };
export type Backend = { stream_name: string; aufzeichnung_quelle: string | null; stream_typ?: string | null };
export type Protokoll = {
  user_id: string | null;
  kamera_id: string | null;
  scope: Scope | null;
  ergebnis: "erteilt" | "abgelehnt";
  grund: string;
};

export type Deps = {
  env: (name: string) => string | undefined;
  now: () => number;
  authUser: (jwt: string) => Promise<string | null>;
  ladeNutzer: (authUid: string) => Promise<Nutzer | null>;
  darfSehen: (jwt: string, kameraId: string) => Promise<boolean>;
  ladeBackend: (kameraId: string) => Promise<Backend | null>;
  protokoll?: (e: Protokoll) => Promise<void>;
  nonce?: () => string;
};

export type TokenPayload = {
  v: number;
  k: string;
  s: string;
  u: string;
  sc: Scope;
  iat: number;
  exp: number;
  n: string;
};

// ── Hilfen ─────────────────────────────────────────────────────────────────────

export function corsHeaders(origin: string | null): Record<string, string> {
  const h: Record<string, string> = {
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
    "Access-Control-Max-Age": "600",
    "Vary": "Origin",
  };
  if (origin && ALLOWED_ORIGINS.indexOf(origin) >= 0) h["Access-Control-Allow-Origin"] = origin;
  return h;
}

function antwort(origin: string | null, status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...corsHeaders(origin), "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store" },
  });
}

// users.active ist INTEGER (1/0), users.locked int ODER bool — typ-agnostisch wie can_edit_urlaub() in SQL.
export function istAktiv(n: Nutzer): boolean {
  const a = n.active === null || n.active === undefined ? "1" : String(n.active).toLowerCase();
  const l = n.locked === null || n.locked === undefined ? "false" : String(n.locked).toLowerCase();
  return (a === "1" || a === "true" || a === "t") && (l === "0" || l === "false" || l === "f");
}

export function rolleVon(n: Nutzer): string {
  return String(n.role ?? "").trim().toLowerCase();
}

export function ttlSekunden(env: (name: string) => string | undefined): number {
  const roh = Number(env("KAMERA_TOKEN_TTL") ?? "");
  if (!Number.isFinite(roh) || roh <= 0) return TTL_STANDARD;
  return Math.max(TTL_MIN, Math.min(TTL_MAX, Math.floor(roh)));
}

export function aufzeichnungsRollen(env: (name: string) => string | undefined): string[] {
  const roh = env("KAMERA_AUFZEICHNUNG_ROLLEN");
  const liste = roh === undefined || roh.trim() === ""
    ? STANDARD_AUFZEICHNUNG_ROLLEN.slice()
    : roh.split(",").map((x) => x.trim().toLowerCase()).filter((x) => x.length > 0);
  // Nie mehr als die Kamerarollen — ein Tippfehler in der Konfiguration darf keinen Monteur freischalten.
  return liste.filter((r) => ERLAUBTE_ROLLEN.indexOf(r) >= 0);
}

// stream_typ aus kamera_backend: leer -> Standard webrtc; unbekannt -> null (die Function antwortet dann 503).
export function streamTyp(be: Backend | null): StreamTyp | null {
  const roh = be && be.stream_typ !== null && be.stream_typ !== undefined ? String(be.stream_typ).trim().toLowerCase() : "";
  const t = roh === "" ? STANDARD_STREAM_TYP : roh;
  return STREAM_TYPEN.indexOf(t) >= 0 ? (t as StreamTyp) : null;
}

// Live-Antwort je Adressart. Pfade (der Reverse-Proxy kennt genau diese, siehe README):
//   webrtc   -> /live/<s>/whep (WHEP-Angebot) + /live/<s>/index.m3u8 (HLS-Rueckfall)
//   llhls    -> /live/<s>/index.m3u8
//   mjpeg    -> /live/<s>/mjpeg
//   snapshot -> /live/<s>/snapshot.jpg (die App laedt das Bild alle 2 s neu)
export function liveAntwort(basis: string, ziel: string, typ: StreamTyp, token: string, exp: number, ttl: number): Record<string, unknown> {
  const p = basis + "/live/" + ziel + "/";
  const q = "?token=" + token;
  if (typ === "mjpeg") return { typ, mjpegUrl: p + "mjpeg" + q, exp, ttl };
  if (typ === "snapshot") return { typ, snapshotUrl: p + "snapshot.jpg" + q, exp, ttl };
  if (typ === "llhls") return { typ, liveUrl: p + "index.m3u8" + q, exp, ttl };
  return { typ, liveUrl: p + "index.m3u8" + q, webrtcUrl: p + "whep" + q, exp, ttl };
}

export function backendBasis(env: (name: string) => string | undefined): string | null {
  const roh = (env("KAMERA_BACKEND_BASE") ?? "").trim();
  if (!/^https:\/\/[A-Za-z0-9.-]+(:\d{1,5})?(\/[A-Za-z0-9._~\/-]*)?$/.test(roh)) return null;
  return roh.replace(/\/+$/, "");
}

function b64url(bytes: Uint8Array): string {
  let s = "";
  for (let i = 0; i < bytes.length; i++) s += String.fromCharCode(bytes[i]);
  return btoa(s).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function b64urlDecode(t: string): Uint8Array | null {
  if (!/^[A-Za-z0-9_-]*$/.test(t)) return null;
  try {
    const pad = t.length % 4 === 0 ? "" : "=".repeat(4 - (t.length % 4));
    const bin = atob(t.replace(/-/g, "+").replace(/_/g, "/") + pad);
    const out = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
    return out;
  } catch {
    return null;
  }
}

async function hmacKey(secret: string, usage: "sign" | "verify"): Promise<CryptoKey> {
  return await crypto.subtle.importKey("raw", new TextEncoder().encode(secret), { name: "HMAC", hash: "SHA-256" }, false, [usage]);
}

// TOKEN = base64url(JSON payload) "." base64url(HMAC-SHA256(secret, <erster Teil als ASCII>))
export async function signiere(secret: string, p: TokenPayload): Promise<string> {
  const teil = b64url(new TextEncoder().encode(JSON.stringify(p)));
  const sig = new Uint8Array(await crypto.subtle.sign("HMAC", await hmacKey(secret, "sign"), new TextEncoder().encode(teil)));
  return teil + "." + b64url(sig);
}

// Referenz-Pruefer fuer den Reverse-Proxy (gleiche Regeln wie im README-Vertrag). Gibt das Payload oder null.
export async function pruefeToken(
  secret: string,
  token: string,
  nowMs: number,
  erwartet?: { s?: string; sc?: Scope },
): Promise<TokenPayload | null> {
  if (typeof token !== "string" || token.length > 2048) return null;
  const teile = token.split(".");
  if (teile.length !== 2) return null;
  const sig = b64urlDecode(teile[1]);
  const roh = b64urlDecode(teile[0]);
  if (!sig || !roh) return null;
  const ok = await crypto.subtle.verify("HMAC", await hmacKey(secret, "verify"), sig, new TextEncoder().encode(teile[0]));
  if (!ok) return null;
  let p: TokenPayload;
  try {
    p = JSON.parse(new TextDecoder().decode(roh)) as TokenPayload;
  } catch {
    return null;
  }
  const jetzt = Math.floor(nowMs / 1000);
  if (!p || p.v !== TOKEN_VERSION) return null;
  if (typeof p.exp !== "number" || typeof p.iat !== "number") return null;
  if (p.exp - p.iat > TTL_MAX || p.exp - p.iat <= 0) return null;
  if (p.exp <= jetzt) return null;
  if (p.iat > jetzt + 5) return null; // Uhrversatz hoechstens 5 s
  if (p.sc !== "live" && p.sc !== "aufzeichnung") return null;
  if (erwartet && erwartet.s !== undefined && p.s !== erwartet.s) return null;
  if (erwartet && erwartet.sc !== undefined && p.sc !== erwartet.sc) return null;
  return p;
}

// ── Referenz der Vorrangregel (Spiegel von public.kamera_pruefen) ───────────────
// Wird von der Edge Function NICHT zur Entscheidung benutzt — entschieden wird in der Datenbank
// (kamera_darf_sehen). Die Funktion dokumentiert die Regel ausfuehrbar und dient den Tests als Attrappe der DB.
export type Regel = {
  rolle?: string | null;
  user_id?: string | null;
  wochentage?: number[] | null;
  von?: string | null; // "HH:MM" (Wiener Ortszeit)
  bis?: string | null; // "HH:MM", exklusiv, "24:00" erlaubt
  erlaubt: boolean;
};

export function wienerZeit(ms: number): { dow: number; minuten: number } {
  const f = new Intl.DateTimeFormat("en-GB", {
    timeZone: "Europe/Vienna",
    weekday: "short",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
  });
  let wd = "";
  let hh = 0;
  let mm = 0;
  for (const t of f.formatToParts(new Date(ms))) {
    if (t.type === "weekday") wd = t.value;
    if (t.type === "hour") hh = Number(t.value);
    if (t.type === "minute") mm = Number(t.value);
  }
  const dow = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].indexOf(wd) + 1;
  return { dow, minuten: hh * 60 + mm };
}

function minuten(hhmm: string): number {
  const m = /^(\d{1,2}):(\d{2})/.exec(hhmm);
  return m ? Number(m[1]) * 60 + Number(m[2]) : NaN;
}

export function fensterTrifft(r: Regel, dow: number, min: number): boolean {
  const tage = r.wochentage && r.wochentage.length ? r.wochentage : [1, 2, 3, 4, 5, 6, 7];
  if (tage.indexOf(dow) < 0) return false;
  if (!r.von || !r.bis) return true;
  return min >= minuten(r.von) && min < minuten(r.bis);
}

export function entscheide(regeln: Regel[], nutzer: { id: string; role: string }, ms: number, kameraAktiv = true): boolean {
  const rolle = String(nutzer.role || "").toLowerCase();
  if (ERLAUBTE_ROLLEN.indexOf(rolle) < 0) return false;
  if (!kameraAktiv) return false;
  const z = wienerZeit(ms);
  const trifft = (r: Regel) => fensterTrifft(r, z.dow, z.minuten);
  const eigene = regeln.filter((r) => r.user_id === nutzer.id && trifft(r));
  if (eigene.some((r) => !r.erlaubt)) return false;
  if (eigene.some((r) => r.erlaubt)) return true;
  const rolleR = regeln.filter((r) => !r.user_id && r.rolle === rolle && trifft(r));
  if (rolleR.some((r) => !r.erlaubt)) return false;
  if (rolleR.some((r) => r.erlaubt)) return true;
  return false;
}

// ── Anfrage ────────────────────────────────────────────────────────────────────

async function merke(deps: Deps, e: Protokoll): Promise<void> {
  if (!deps.protokoll) return;
  try {
    await deps.protokoll(e);
  } catch {
    // Protokoll ist best effort; ein Fehler darf weder eine Freigabe erzeugen noch Details verraten.
  }
}

// Einrichtungsabfrage: genau {"pruefen":"einrichtung"} (weitere Felder egal). Alles andere ist eine Stream-Anfrage.
export function istEinrichtungsAbfrage(text: string): boolean {
  if (text.length > MAX_BODY) return false;
  try {
    const p = JSON.parse(text);
    return !!p && typeof p === "object" && !Array.isArray(p) && (p as Record<string, unknown>).pruefen === "einrichtung";
  } catch {
    return false;
  }
}

export async function bearbeite(req: Request, deps: Deps): Promise<Response> {
  const origin = req.headers.get("origin");
  if (origin !== null && ALLOWED_ORIGINS.indexOf(origin) < 0) return antwort(null, 403, { error: "origin" });
  if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: corsHeaders(origin) });
  if (req.method !== "POST") return antwort(origin, 405, { error: "methode" });

  try {
    // 1. JWT
    const auth = req.headers.get("authorization") ?? "";
    const m = /^Bearer\s+([A-Za-z0-9._-]{20,4096})$/.exec(auth.trim());
    if (!m) return antwort(origin, 401, { error: "nicht_angemeldet" });
    const jwt = m[1];
    const authUid = await deps.authUser(jwt);
    if (!authUid) return antwort(origin, 401, { error: "nicht_angemeldet" });

    // 2. Nutzer aktiv, nicht gesperrt
    const nutzer = await deps.ladeNutzer(authUid);
    if (!nutzer || !istAktiv(nutzer)) return antwort(origin, 403, { error: "kein_zugriff" });

    // 3. harte Rollenliste — Monteure (und jede andere Rolle) enden HIER, vor jeder Kamera-/Backend-Abfrage
    const rolle = rolleVon(nutzer);
    if (ERLAUBTE_ROLLEN.indexOf(rolle) < 0) {
      await merke(deps, { user_id: nutzer.id, kamera_id: null, scope: null, ergebnis: "abgelehnt", grund: "rolle" });
      return antwort(origin, 403, { error: "kein_zugriff" });
    }

    // 3b. Einrichtungsabfrage der App (Ansicht "Einrichtung", nur Admin). Steht NACH der Rollensperre:
    //     ein Monteur endet oben, bevor diese Stelle erreicht wird. Antwort: nur, ob das Secret gesetzt ist,
    //     und die Basisadresse des Video-Hosts (ohne Token, ohne Streamnamen, ohne Kamera) - damit die App
    //     pruefen kann, ob der Kamera-Server im Buero erreichbar ist. Keine DB-Abfrage, kein Protokoll.
    const text = await req.text();
    if (istEinrichtungsAbfrage(text)) {
      if (rolle !== "admin") return antwort(origin, 403, { error: "kein_zugriff" });
      const s = deps.env("KAMERA_TOKEN_SECRET") ?? "";
      return antwort(origin, 200, { einrichtung: true, secret: s.length >= SECRET_MIN_LAENGE, basis: backendBasis(deps.env) ?? "" });
    }

    // 4. Konfiguration
    const secret = deps.env("KAMERA_TOKEN_SECRET") ?? "";
    const basis = backendBasis(deps.env);
    if (secret.length < SECRET_MIN_LAENGE || !basis) return antwort(origin, 503, { error: "nicht_konfiguriert" });

    // 5. Anfrage
    if (text.length > MAX_BODY) return antwort(origin, 400, { error: "ungueltig" });
    let body: Record<string, unknown>;
    try {
      const p = JSON.parse(text);
      if (!p || typeof p !== "object" || Array.isArray(p)) return antwort(origin, 400, { error: "ungueltig" });
      body = p as Record<string, unknown>;
    } catch {
      return antwort(origin, 400, { error: "ungueltig" });
    }
    const kameraId = typeof body.kamera_id === "string" ? body.kamera_id : "";
    if (!ID_RE.test(kameraId)) return antwort(origin, 400, { error: "ungueltig" });
    const scopeRoh = body.scope === undefined ? "live" : body.scope;
    if (scopeRoh !== "live" && scopeRoh !== "aufzeichnung") return antwort(origin, 400, { error: "ungueltig" });
    const scope: Scope = scopeRoh;
    const geraet = body.geraet === "pc" ? "pc" : "mobil";

    // 6. Aufzeichnung: nur am PC und nur fuer die Aufzeichnungsrollen
    if (scope === "aufzeichnung" && (geraet !== "pc" || aufzeichnungsRollen(deps.env).indexOf(rolle) < 0)) {
      await merke(deps, { user_id: nutzer.id, kamera_id: kameraId, scope, ergebnis: "abgelehnt", grund: "aufzeichnung" });
      return antwort(origin, 403, { error: "kein_zugriff" });
    }

    // 7. Regel in der Datenbank, mit dem JWT des Aufrufers, zur Serverzeit
    const darf = await deps.darfSehen(jwt, kameraId);
    if (darf !== true) {
      await merke(deps, { user_id: nutzer.id, kamera_id: kameraId, scope, ergebnis: "abgelehnt", grund: "regel" });
      return antwort(origin, 403, { error: "kein_zugriff" });
    }

    // 8. Backend-Zuordnung
    const be = await deps.ladeBackend(kameraId);
    const ziel = be ? (scope === "live" ? be.stream_name : be.aufzeichnung_quelle) : null;
    if (!ziel || !ID_RE.test(ziel)) return antwort(origin, 503, { error: "nicht_konfiguriert" });
    const typ = streamTyp(be);
    if (scope === "live" && !typ) return antwort(origin, 503, { error: "nicht_konfiguriert" });

    // 9. Token + Adresse
    const ttl = ttlSekunden(deps.env);
    const iat = Math.floor(deps.now() / 1000);
    const payload: TokenPayload = {
      v: TOKEN_VERSION,
      k: kameraId,
      s: ziel,
      u: nutzer.id,
      sc: scope,
      iat,
      exp: iat + ttl,
      n: deps.nonce ? deps.nonce() : crypto.randomUUID(),
    };
    const token = encodeURIComponent(await signiere(secret, payload));
    await merke(deps, { user_id: nutzer.id, kamera_id: kameraId, scope, ergebnis: "erteilt", grund: "ok" });
    if (scope === "live") return antwort(origin, 200, liveAntwort(basis, ziel, typ as StreamTyp, token, payload.exp, ttl));
    return antwort(origin, 200, {
      aufzeichnungUrl: basis + "/aufzeichnung/" + ziel + "?token=" + token,
      exp: payload.exp,
      ttl,
    });
  } catch {
    return antwort(origin, 500, { error: "intern" });
  }
}
