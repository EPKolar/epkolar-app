// kamera-proxy-auth / token.mjs - 1:1-Portierung der Token-Funktionen aus
// supabase/functions/kamera-stream/logic.ts (EPKolar Kameras Phase 2, 19.11.2026).
//
// Warum eine Kopie statt Import: der Pruefer laeuft auf dem Video-Host als eigenstaendiger Node-Dienst
// ohne das App-Repo. Damit die Kopie nicht still auseinanderlaeuft, prueft
// tests/test_kameras_phase2_v1056.py BEIDE Umsetzungen gegen dieselben Vektoren (vektoren.json),
// signiert kreuzweise (logic.ts signiert -> token.mjs prueft und umgekehrt) und vergleicht die
// Regelzeilen woertlich. Aenderungen am Vertrag IMMER in beiden Dateien.
//
// Keine Abhaengigkeiten. Nur Web Crypto (globalThis.crypto.subtle, Node >= 20), atob/btoa, TextEncoder.
// HMAC-Vergleich: crypto.subtle.verify (konstante Laufzeit, wie in logic.ts).

export const TOKEN_VERSION = 1;
export const TTL_MAX = 120;
export const UHRVERSATZ_S = 5;

function b64url(bytes) {
  let s = "";
  for (let i = 0; i < bytes.length; i++) s += String.fromCharCode(bytes[i]);
  return btoa(s).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function b64urlDecode(t) {
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

async function hmacKey(secret, usage) {
  return await crypto.subtle.importKey("raw", new TextEncoder().encode(secret), { name: "HMAC", hash: "SHA-256" }, false, [usage]);
}

// TOKEN = base64url(JSON payload) "." base64url(HMAC-SHA256(secret, <erster Teil als ASCII>))
export async function signiere(secret, p) {
  const teil = b64url(new TextEncoder().encode(JSON.stringify(p)));
  const sig = new Uint8Array(await crypto.subtle.sign("HMAC", await hmacKey(secret, "sign"), new TextEncoder().encode(teil)));
  return teil + "." + b64url(sig);
}

// Gleiche Regeln wie logic.ts pruefeToken. Gibt das Payload oder null.
export async function pruefeToken(secret, token, nowMs, erwartet) {
  if (typeof token !== "string" || token.length > 2048) return null;
  const teile = token.split(".");
  if (teile.length !== 2) return null;
  const sig = b64urlDecode(teile[1]);
  const roh = b64urlDecode(teile[0]);
  if (!sig || !roh) return null;
  const ok = await crypto.subtle.verify("HMAC", await hmacKey(secret, "verify"), sig, new TextEncoder().encode(teile[0]));
  if (!ok) return null;
  let p;
  try {
    p = JSON.parse(new TextDecoder().decode(roh));
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
