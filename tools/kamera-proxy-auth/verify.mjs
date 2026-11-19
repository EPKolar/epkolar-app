#!/usr/bin/env node
// kamera-proxy-auth / verify.mjs - Token-Pruefer fuer den Reverse-Proxy (EPKolar Kameras Phase 2, 19.11.2026)
//
// Kleiner Dienst OHNE Abhaengigkeiten fuer Caddy `forward_auth` bzw. nginx `auth_request`.
// Der Proxy fragt fuer JEDE Anfrage an /live/* und /aufzeichnung/* hier nach; nur bei 204 wird weitergeleitet.
//
//   204  Token gueltig, Pfad passt (Kopf X-Kamera-Stream / X-Kamera-User fuer das Zugriffsprotokoll des Proxys)
//   401  kein Token, Signatur falsch, abgelaufen, zu lang gueltig, aus der Zukunft, kaputt
//   403  Token an sich gueltig, aber Pfad-Stream != s, Pfad-Art != sc, Pfadform/Methode nicht erlaubt,
//        Aufzeichnung: Query von/bis fehlt, doppelt, kodiert oder nicht zeichengleich mit dem signierten von/bis
//
// Woher der Originalpfad kommt: AUSSCHLIESSLICH aus dem per KAMERA_AUTH_URI_HEADER festgelegten Kopf
// (x-forwarded-uri fuer Caddy forward_auth, x-original-uri fuer nginx auth_request). Kein Rueckfall auf die
// eigene Anfrage-URL. Steht bei einer Anfrage der JEWEILS ANDERE Kopf (Uri oder Methode) dabei, ist das ein
// vom Client eingeschleuster Kopf -> 403. Sonst koennte ein Client mit Token fuer Kamera A den Pfad von
// Kamera B abrufen und dem Pruefer per Kopf den Pfad von A vorspielen (nginx reicht Client-Koepfe durch).
// Woher das Token kommt: Query ?token= ; sonst Kopf X-Kamera-Token ; sonst Authorization: Bearer ; sonst Cookie kam_t
// (nur fuer HLS-Teilstuecke, die der Browser ohne Query nachlaedt).
//
// Tokens, Query-Strings und Cookies werden NIE protokolliert. KAMERA_AUTH_LOG=1 schreibt je Anfrage nur
// Zeit, Status, Art, Stream und users.id.
//
// Umgebung:
//   KAMERA_TOKEN_SECRET       (Pflicht, >= 32 Zeichen; derselbe Wert wie das Secret der Edge Function)
//   KAMERA_TOKEN_SECRET_FILE  (statt dessen: Pfad einer Datei mit dem Secret, z. B. Docker-Secret)
//   KAMERA_AUTH_HOST          (Standard 127.0.0.1; im Docker-Netz 0.0.0.0, NIE nach aussen veroeffentlichen)
//   KAMERA_AUTH_PORT          (Standard 9099)
//   KAMERA_AUTH_LOG           (1 = knappes Protokoll ohne Token)
//   KAMERA_AUTH_URI_HEADER    (Pflicht: x-forwarded-uri [Caddy] ODER x-original-uri [nginx])
//   KAMERA_AUTH_METHOD_HEADER (Pflicht, passend: x-forwarded-method bzw. x-original-method)
//   Fehlt eines oder passt das Paar nicht -> Start abgebrochen.
import { createServer } from "node:http";
import { readFileSync } from "node:fs";
import { pathToFileURL } from "node:url";
import { pruefeToken } from "./token.mjs";

export const SECRET_MIN_LAENGE = 32;
export const MAX_URI = 4096;
export const MAX_AUFZEICHNUNG_SPANNE_S = 2 * 3600; // gleich AUFZEICHNUNG_MAX_SPANNE_S in logic.ts
// Erlaubte Kopf-Paare (Uri -> Methode). Genau EIN Paar ist vertrauenswuerdig, das andere ist verboten.
export const KOPF_PAARE = { "x-forwarded-uri": "x-forwarded-method", "x-original-uri": "x-original-method" };

// -> {uriHeader, methodHeader, fremd:[...]} oder null (ungueltig/fehlend)
export function ladeKopfConfig(env) {
  const u = String(env.KAMERA_AUTH_URI_HEADER || "").trim().toLowerCase();
  const m = String(env.KAMERA_AUTH_METHOD_HEADER || "").trim().toLowerCase();
  if (!Object.prototype.hasOwnProperty.call(KOPF_PAARE, u) || KOPF_PAARE[u] !== m) return null;
  const fremd = [];
  for (const k of Object.keys(KOPF_PAARE)) if (k !== u) fremd.push(k, KOPF_PAARE[k]);
  return { uriHeader: u, methodHeader: m, fremd };
}

const STREAM = "[A-Za-z0-9_-]{1,64}";
const TEIL = "[A-Za-z0-9_-][A-Za-z0-9._-]{0,127}";
const LIVE_RE = new RegExp("^/live/(" + STREAM + ")/(whep|index[.]m3u8|mjpeg|snapshot[.]jpg|hls/" + TEIL + ")$");
const REC_RE = new RegExp("^/aufzeichnung/(" + STREAM + ")((?:/" + TEIL + "){0,8})$");

// Pfad (ohne Query) -> {s, sc, art} oder null. Erlaubt sind GENAU die Formen aus dem Vertrag (README).
export function pfadArt(pfad) {
  if (typeof pfad !== "string" || pfad.length > MAX_URI) return null;
  if (pfad.indexOf("%") >= 0 || pfad.indexOf("..") >= 0 || pfad.indexOf("//") >= 0) return null;
  let m = LIVE_RE.exec(pfad);
  if (m) {
    const art = m[2].indexOf("hls/") === 0 ? "hls_teil" : m[2] === "index.m3u8" ? "hls" : m[2] === "snapshot.jpg" ? "snapshot" : m[2];
    return { s: m[1], sc: "live", art };
  }
  m = REC_RE.exec(pfad);
  if (m) return { s: m[1], sc: "aufzeichnung", art: m[2] ? "aufzeichnung_teil" : "aufzeichnung" };
  return null;
}

function kopf(headers, name) {
  const v = headers[name];
  if (Array.isArray(v)) return v.length === 1 ? String(v[0]) : null;
  return v === undefined ? "" : String(v);
}

function cookieToken(cookie) {
  if (!cookie) return "";
  const treffer = [];
  for (const teil of cookie.split(";")) {
    const i = teil.indexOf("=");
    if (i > 0 && teil.slice(0, i).trim() === "kam_t") treffer.push(teil.slice(i + 1).trim());
  }
  return treffer.length === 1 ? treffer[0] : "";
}

// Rohe (nicht dekodierte) Werte eines Query-Parameters mit genau diesem rohen Namen.
function rohParameter(roheQuery, name) {
  const out = [];
  for (const teil of roheQuery.split("&")) {
    const i = teil.indexOf("=");
    if ((i >= 0 ? teil.slice(0, i) : teil) === name) out.push(i >= 0 ? teil.slice(i + 1) : "");
  }
  return out;
}

function zahl(t) {
  return typeof t === "string" && /^[0-9]{1,12}$/.test(t) ? Number(t) : NaN;
}

// Reine Entscheidung (ohne Netz). req = {method, url, headers}; headers mit kleingeschriebenen Namen.
// cfg = ladeKopfConfig(env) - Pflicht. -> {status, headers, info:{art, s, u}} ; info nie mit Token.
export async function entscheide(req, secret, nowMs, cfg) {
  const h = req.headers || {};
  const nein = (status, info) => ({ status, headers: { "Cache-Control": "no-store" }, info: info || {} });
  if (!cfg || !cfg.uriHeader || !cfg.methodHeader || !Array.isArray(cfg.fremd)) return nein(403);
  // eingeschleuster Kopf des jeweils anderen Proxys -> 403 (auch wenn leer)
  for (const k of cfg.fremd) if (h[k] !== undefined) return nein(403);
  const uri = kopf(h, cfg.uriHeader);
  if (uri === null || uri === "") return nein(403);
  if (uri.length > MAX_URI || uri.charAt(0) !== "/") return nein(403);
  const q = uri.indexOf("?");
  const pfad = q >= 0 ? uri.slice(0, q) : uri;
  const query = new URLSearchParams(q >= 0 ? uri.slice(q + 1) : "");
  const ziel = pfadArt(pfad);
  if (!ziel) return nein(403);

  const methodeRoh = kopf(h, cfg.methodHeader);
  if (methodeRoh === null || methodeRoh === "") return nein(403, { art: ziel.art, s: ziel.s });
  const methode = methodeRoh.toUpperCase();
  const erlaubt = ziel.art === "whep" ? ["POST"] : ["GET", "HEAD"];
  if (erlaubt.indexOf(methode) < 0) return nein(403, { art: ziel.art, s: ziel.s });

  // Token: Query, dann Kopf, dann Bearer, dann Cookie. Mehrdeutigkeit (zwei token-Parameter) = kein Token.
  const qt = query.getAll("token");
  if (qt.length > 1) return nein(401, { art: ziel.art, s: ziel.s });
  let token = qt.length === 1 ? qt[0] : "";
  let quelle = token ? "query" : "";
  if (!token) {
    const kt = kopf(h, "x-kamera-token");
    if (kt) { token = kt; quelle = "kopf"; }
  }
  if (!token) {
    const m = /^Bearer\s+(\S+)$/.exec(kopf(h, "authorization") || "");
    if (m) { token = m[1]; quelle = "bearer"; }
  }
  if (!token && (ziel.art === "hls_teil" || ziel.art === "aufzeichnung_teil")) {
    token = cookieToken(kopf(h, "cookie"));
    if (token) quelle = "cookie";
  }
  if (!token) return nein(401, { art: ziel.art, s: ziel.s });

  const p = await pruefeToken(secret, token, nowMs);
  if (!p) return nein(401, { art: ziel.art, s: ziel.s });
  // Erst jetzt Pfadbindung: Signatur stimmt, aber falscher Stream oder falsche Art -> 403.
  const gebunden = await pruefeToken(secret, token, nowMs, { s: ziel.s, sc: ziel.sc });
  if (!gebunden) return nein(403, { art: ziel.art, s: ziel.s, u: String(p.u || "") });

  // Aufzeichnung: der freigegebene Bereich steht SIGNIERT im Token (von/bis, Unix-Sekunden). Die Query-Parameter
  // von/bis, nach denen der Proxy die Aufzeichnung abruft, muessen GENAU diesen Werten entsprechen: je genau ein
  // Parameter (dekodiert UND roh, kein %-kodierter Doppelgaenger), nur Ziffern, zeichengleich mit dem Token.
  // Fuer Teilstuecke (aufzeichnung_teil) gilt: fehlen von/bis, binden die Antwortkoepfe X-Kamera-Von/-Bis;
  // stehen sie da, muessen sie ebenso exakt passen.
  if (gebunden.sc === "aufzeichnung") {
    const gv = String(gebunden.von), gb = String(gebunden.bis);
    const pflicht = ziel.art === "aufzeichnung";
    const ok = (name, soll) => {
      const dek = query.getAll(name);
      const roh = rohParameter(q >= 0 ? uri.slice(q + 1) : "", name);
      if (!pflicht && dek.length === 0 && roh.length === 0) return true;
      return dek.length === 1 && roh.length === 1 && roh[0] === dek[0] && /^[0-9]{1,12}$/.test(roh[0]) && roh[0] === soll;
    };
    if (!ok("von", gv) || !ok("bis", gb)) return nein(403, { art: ziel.art, s: ziel.s, u: String(p.u || "") });
    const von = zahl(gv);
    const bis = zahl(gb);
    const jetzt = Math.floor(nowMs / 1000);
    if (!(von < bis) || bis - von > MAX_AUFZEICHNUNG_SPANNE_S || bis > jetzt + 5) return nein(403, { art: ziel.art, s: ziel.s, u: String(p.u || "") });
  }

  const out = { "Cache-Control": "no-store", "X-Kamera-Stream": gebunden.s, "X-Kamera-User": String(gebunden.u || "") };
  if (gebunden.sc === "aufzeichnung") {
    // Der Proxy baut die Frigate-Adresse NUR aus diesen Koepfen (copy_headers / auth_request_set), nie aus der Client-Query.
    out["X-Kamera-Von"] = String(gebunden.von);
    out["X-Kamera-Bis"] = String(gebunden.bis);
  }
  // HLS: Teilstuecke laedt der Browser ohne Query nach -> Token als Cookie, nur fuer diesen Stream-Pfad,
  // hoechstens bis zum Token-Ablauf (<= 120 s). nginx reicht ihn per auth_request_set weiter (README).
  if (quelle === "query" && (ziel.art === "hls" || ziel.art === "aufzeichnung")) {
    const rest = Math.max(1, gebunden.exp - Math.floor(nowMs / 1000));
    const pfadCookie = ziel.sc === "live" ? "/live/" + gebunden.s + "/" : "/aufzeichnung/" + gebunden.s + "/";
    out["Set-Cookie"] = "kam_t=" + token + "; Path=" + pfadCookie + "; Max-Age=" + rest + "; HttpOnly; Secure; SameSite=None";
  }
  return { status: 204, headers: out, info: { art: ziel.art, s: gebunden.s, u: String(gebunden.u || "") } };
}

export function ladeSecret(env) {
  let s = env.KAMERA_TOKEN_SECRET || "";
  if (!s && env.KAMERA_TOKEN_SECRET_FILE) {
    try { s = readFileSync(env.KAMERA_TOKEN_SECRET_FILE, "utf8").trim(); } catch { s = ""; }
  }
  return s.length >= SECRET_MIN_LAENGE ? s : null;
}

export function starte(env) {
  const secret = ladeSecret(env);
  if (!secret) {
    process.stderr.write("kamera-proxy-auth: KAMERA_TOKEN_SECRET fehlt oder ist kuerzer als 32 Zeichen - Start abgebrochen\n");
    process.exit(1);
  }
  const cfg = ladeKopfConfig(env);
  if (!cfg) {
    process.stderr.write("kamera-proxy-auth: KAMERA_AUTH_URI_HEADER/KAMERA_AUTH_METHOD_HEADER fehlen oder passen nicht "
      + "(x-forwarded-uri + x-forwarded-method fuer Caddy, x-original-uri + x-original-method fuer nginx) - Start abgebrochen\n");
    process.exit(1);
  }
  const log = env.KAMERA_AUTH_LOG === "1";
  const server = createServer(async (req, res) => {
    let e;
    try {
      if (req.url === "/gesund" && !req.headers["x-forwarded-uri"] && !req.headers["x-original-uri"]) {
        res.writeHead(200, { "Content-Type": "text/plain", "Cache-Control": "no-store" });
        res.end("ok");
        return;
      }
      e = await entscheide({ method: req.method, url: req.url, headers: req.headers }, secret, Date.now(), cfg);
    } catch {
      e = { status: 401, headers: { "Cache-Control": "no-store" }, info: {} };
    }
    res.writeHead(e.status, e.headers);
    res.end();
    if (log) {
      // bewusst OHNE Token, Query, Cookie und Kopfzeilen
      process.stdout.write(JSON.stringify({ t: new Date().toISOString(), status: e.status, art: e.info.art || "", s: e.info.s || "", u: e.info.u || "" }) + "\n");
    }
  });
  server.headersTimeout = 5000;
  server.requestTimeout = 5000;
  const port = Number(env.KAMERA_AUTH_PORT || 9099);
  const host = env.KAMERA_AUTH_HOST || "127.0.0.1";
  server.listen(port, host, () => process.stdout.write("kamera-proxy-auth hoert auf " + host + ":" + port + "\n"));
  return server;
}

// Direkt gestartet (node verify.mjs) -> Dienst; importiert (Tests) -> nur die Funktionen.
const direkt = !!process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href;
if (direkt) starte(process.env);
