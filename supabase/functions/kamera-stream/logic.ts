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
//   4. Konfiguration (Secret, Gateway-Basis)               -> sonst 503
//      Basis = KAMERA_GATEWAY_BASE (bevorzugt), sonst KAMERA_BACKEND_BASE (alter Name, Kompatibilitaet).
//      Ist KAMERA_GATEWAY_BASE gesetzt, aber ungueltig -> 503 (KEIN stiller Rueckfall auf den alten Namen).
//   5. Anfrage gueltig                                     -> sonst 400
//      Aufzeichnung: von/bis (ISO 8601 mit Zone) Pflicht, von < bis, Spanne <= 2 h, bis nicht in der Zukunft,
//      von nicht aelter als die harte Obergrenze 30 Tage (genau je Kamera: Schritt 7b in der DB) -> sonst 400
//   6. Aufzeichnung: Rolle in AUFZEICHNUNG_ROLLEN          -> sonst 403
//      (zusaetzlich geraet=pc - das ist NUR Bedienkomfort, KEINE Sicherheitsgrenze, siehe unten)
//   7. kamera_darf_sehen(kamera) mit dem JWT des Aufrufers, Serverzeit (Europe/Vienna in SQL) -> sonst 403
//   7b. Aufzeichnung: kamera_darf_sehen_bereich(kamera, von, bis) mit dem JWT des Aufrufers -> sonst 403.
//      DAS ist die echte Kontrolle fuer Aufzeichnungen: die Regel muss fuer JEDEN Augenblick des angefragten
//      Bereichs gelten (nicht nur jetzt), und der Bereich muss in der Aufbewahrung der Kamera liegen.
//   8. Backend-Zuordnung (service_role)                    -> sonst 503
//   9. kurzlebiges HMAC-Token (<= 120 s), URL bauen        -> 200
//      Aufzeichnung: von/bis (Unix-Sekunden) stehen SIGNIERT im Token und in der Adresse; der Proxy-Pruefer
//      (tools/kamera-proxy-auth/verify.mjs) verlangt, dass die Query-Werte exakt den signierten entsprechen.
//
// `geraet` ("pc"/"mobil") kommt aus dem Anfragekoerper, also vom Client. Es ist eine BEHAUPTUNG und damit
// KEINE Sicherheitsgrenze: jeder Client kann "pc" schicken. Es haelt nur ehrliche Handys auf Live (Bedienung).
// Wer Aufzeichnungen sehen darf, entscheiden ausschliesslich Rolle (Schritt 6) + Zeitfenster-Bereich (Schritt 7b).
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
// Aufzeichnungsbereich: hoechstens 2 h je Freigabe; harte Altersgrenze = CHECK-Obergrenze kameras.aufbewahrung_tage
// (30). Die genaue Aufbewahrung je Kamera prueft kamera_darf_sehen_bereich in der Datenbank.
export const AUFZEICHNUNG_MAX_SPANNE_S = 2 * 60 * 60;
export const AUFZEICHNUNG_MAX_ALTER_S = 30 * 24 * 60 * 60;
const ISO_RE = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.0{1,3})?(?:Z|[+-]\d{2}:\d{2})$/;

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
  // rpc kamera_darf_sehen_bereich(p_kamera, p_von, p_bis) mit dem JWT des Aufrufers (nur scope=aufzeichnung)
  darfSehenBereich: (jwt: string, kameraId: string, vonIso: string, bisIso: string) => Promise<boolean>;
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
  // nur sc=aufzeichnung: freigegebener Bereich [von, bis) in Unix-Sekunden (signiert)
  von?: number;
  bis?: number;
};

// ISO-Zeitpunkt (mit Zone, ganze Sekunden) -> Unix-Sekunden, sonst null
export function isoSekunden(roh: unknown): number | null {
  if (typeof roh !== "string" || roh.length > 40 || !ISO_RE.test(roh)) return null;
  const ms = Date.parse(roh);
  if (!Number.isFinite(ms) || ms % 1000 !== 0) return null;
  return ms / 1000;
}

// Bereich einer Aufzeichnungsanfrage pruefen (rein). -> {von, bis} in Unix-Sekunden oder null (= 400)
export function aufzeichnungsBereich(vonRoh: unknown, bisRoh: unknown, nowMs: number): { von: number; bis: number } | null {
  const von = isoSekunden(vonRoh);
  const bis = isoSekunden(bisRoh);
  if (von === null || bis === null) return null;
  const jetzt = Math.floor(nowMs / 1000);
  if (!(von < bis)) return null;
  if (bis - von > AUFZEICHNUNG_MAX_SPANNE_S) return null;
  if (bis > jetzt) return null;
  if (von < jetzt - AUFZEICHNUNG_MAX_ALTER_S) return null;
  return { von, bis };
}

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
//               + /live/<s>/snapshot.jpg (Einzelbild-Rueckfall, wenn WHEP/ICE scheitert; Gateway 20.11.2026:
//               die QNAP-Vorlage hat HLS aus, das Einzelbild ist dort freigeschaltet). Gleiches Token, gleicher Stream.
//   llhls    -> /live/<s>/index.m3u8
//   mjpeg    -> /live/<s>/mjpeg
//   snapshot -> /live/<s>/snapshot.jpg (die App laedt das Bild alle 2 s neu)
export function liveAntwort(basis: string, ziel: string, typ: StreamTyp, token: string, exp: number, ttl: number): Record<string, unknown> {
  const p = basis + "/live/" + ziel + "/";
  const q = "?token=" + token;
  if (typ === "mjpeg") return { typ, mjpegUrl: p + "mjpeg" + q, exp, ttl };
  if (typ === "snapshot") return { typ, snapshotUrl: p + "snapshot.jpg" + q, exp, ttl };
  if (typ === "llhls") return { typ, liveUrl: p + "index.m3u8" + q, exp, ttl };
  return { typ, liveUrl: p + "index.m3u8" + q, webrtcUrl: p + "whep" + q, snapshotUrl: p + "snapshot.jpg" + q, exp, ttl };
}

// Basisadresse des Kamera-Gateways (Reverse-Proxy vor go2rtc), EIN konfigurierbarer Wert.
// Reihenfolge: KAMERA_GATEWAY_BASE (bevorzugt) -> KAMERA_BACKEND_BASE (alter Name, bleibt fuer Kompatibilitaet).
// Ein gesetzter (nicht leerer) KAMERA_GATEWAY_BASE gewinnt IMMER - auch wenn er ungueltig ist: dann null (= 503),
// kein stiller Rueckfall auf den alten Namen (fail closed, ein Tippfehler darf nicht unbemerkt auf alt umschalten).
// Pruefung fuer beide Namen gleich: nur https://, Host aus [A-Za-z0-9.-], optional Port und Pfad, abschliessende
// Schraegstriche werden entfernt. Fehlt beides -> null (App: "Kamera-Server noch nicht in Betrieb").
export const BASIS_NAMEN: readonly string[] = ["KAMERA_GATEWAY_BASE", "KAMERA_BACKEND_BASE"];

export function backendBasis(env: (name: string) => string | undefined): string | null {
  const gw = env("KAMERA_GATEWAY_BASE");
  const roh = (gw !== undefined && gw.trim() !== "" ? gw : (env("KAMERA_BACKEND_BASE") ?? "")).trim();
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
  if (p.sc === "aufzeichnung" && !(Number.isInteger(p.von) && Number.isInteger(p.bis) && Number(p.von) < Number(p.bis))) return null;
  if (p.sc === "live" && (p.von !== undefined || p.bis !== undefined)) return null;
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

// Spiegel von public.kamera_darf_sehen_bereich (Bereichspruefung fuer Aufzeichnungen) - wie entscheide() nur
// Referenz und Test-Attrappe; entschieden wird in der Datenbank.
// Exakt, nicht geschaetzt: Regelgrenzen sind ganze Minuten (CHECK kamera_zugriff_minuten_chk), Wiener
// Zonenversaetze und Umstellungen liegen auf ganzen Minuten. Damit ist die Entscheidung auf jedem Stueck
// [volle Minute, naechste volle Minute) konstant; geprueft werden der Anfang `von` und JEDE volle Minute in (von, bis).
// Bereich halboffen [von, bis). Zusaetzlich: von < bis, Spanne <= 2 h, bis <= jetzt, von >= jetzt - Aufbewahrung.
export function entscheideBereich(
  regeln: Regel[],
  nutzer: { id: string; role: string },
  vonMs: number,
  bisMs: number,
  nowMs: number,
  aufbewahrungTage: number,
  kameraAktiv = true,
): boolean {
  if (!Number.isFinite(vonMs) || !Number.isFinite(bisMs) || !(vonMs < bisMs)) return false;
  if (bisMs > nowMs) return false;
  if (bisMs - vonMs > AUFZEICHNUNG_MAX_SPANNE_S * 1000) return false;
  if (!(aufbewahrungTage > 0) || vonMs < nowMs - aufbewahrungTage * 24 * 60 * 60 * 1000) return false;
  if (!entscheide(regeln, nutzer, vonMs, kameraAktiv)) return false;
  for (let t = Math.floor(vonMs / 60000) * 60000 + 60000; t < bisMs; t += 60000) {
    if (!entscheide(regeln, nutzer, t, kameraAktiv)) return false;
  }
  return true;
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
    // Client-Behauptung, KEINE Sicherheitsgrenze (siehe Kopf). Nur Bedienkomfort: ehrliche Handys bleiben auf Live.
    const geraet = body.geraet === "pc" ? "pc" : "mobil";
    // Aufzeichnung: angefragter Bereich (ISO). Ohne gueltigen Bereich keine Aufzeichnung (400).
    let bereich: { von: number; bis: number } | null = null;
    if (scope === "aufzeichnung") {
      bereich = aufzeichnungsBereich(body.von, body.bis, deps.now());
      if (!bereich) return antwort(origin, 400, { error: "ungueltig" });
    }

    // 6. Aufzeichnung: Rolle in den Aufzeichnungsrollen = Kontrolle; geraet=pc = nur Bedienung (faelschbar)
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

    // 7b. Aufzeichnung: die Regel muss fuer den GANZEN angefragten Bereich gelten (nicht nur jetzt) und der
    //     Bereich muss in der Aufbewahrung der Kamera liegen - entschieden in der DB mit dem JWT des Aufrufers.
    if (scope === "aufzeichnung") {
      const b = bereich as { von: number; bis: number };
      const darfBereich = await deps.darfSehenBereich(jwt, kameraId, new Date(b.von * 1000).toISOString(), new Date(b.bis * 1000).toISOString());
      if (darfBereich !== true) {
        await merke(deps, { user_id: nutzer.id, kamera_id: kameraId, scope, ergebnis: "abgelehnt", grund: "bereich" });
        return antwort(origin, 403, { error: "kein_zugriff" });
      }
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
    if (bereich) {
      payload.von = bereich.von;
      payload.bis = bereich.bis;
    }
    const token = encodeURIComponent(await signiere(secret, payload));
    await merke(deps, { user_id: nutzer.id, kamera_id: kameraId, scope, ergebnis: "erteilt", grund: "ok" });
    if (scope === "live") return antwort(origin, 200, liveAntwort(basis, ziel, typ as StreamTyp, token, payload.exp, ttl));
    const b = bereich as { von: number; bis: number };
    // von/bis stehen signiert im Token; der Proxy-Pruefer verlangt exakt diese Werte in der Query.
    return antwort(origin, 200, {
      aufzeichnungUrl: basis + "/aufzeichnung/" + ziel + "?token=" + token + "&von=" + b.von + "&bis=" + b.bis,
      von: b.von,
      bis: b.bis,
      exp: payload.exp,
      ttl,
    });
  } catch {
    return antwort(origin, 500, { error: "intern" });
  }
}
