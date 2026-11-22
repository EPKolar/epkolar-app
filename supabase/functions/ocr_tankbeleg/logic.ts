// ocr_tankbeleg / logic.ts — reine Lese-Logik fuer Tankbeleg- und Tacho-Fotos (v3.9.1096)
//
// Bewusst OHNE Importe und ohne Deno-Globals: laeuft unveraendert in Node (tests/test_ocr_km_v1096.py,
// node --experimental-strip-types). Die App (index.html, Block @OCR-KM) traegt eine Abschrift von
// kmAusText(); der Test prueft beide gegen dieselben Proben.
//
// Befund 22.11.2026 ("km-Stand wird nie erkannt"): der alte Parser suchte nur das Wort KILOMETERSTAND
// und danach eine Zahl in derselben/2 Folgezeilen bzw. "123456 km" ohne Tausenderpunkt. Belege mit
// "KM-STAND", "Km:", "Tacho", "123.456 km" oder Spaltensatz (Vision liefert erst alle Bezeichnungen,
// dann alle Werte) liefen leer. Neu: Bezeichnungs-/Einheiten-Kandidaten, Zeilen aus den Wortboxen,
// Plausibilitaet gegen den bisherigen km-Stand, eigene Tacho-Betriebsart.

export type KmQuelle = "" | "beleg_label" | "beleg_einheit" | "tacho";
/** km: uebernehmbarer Vorschlag ("" = keiner). stelle: Textzeile, aus der die Zahl stammt (fuer den Kontrolldialog).
 *  unplausibel: gefundene Zahl, die NICHT vorgeschlagen wird (unter bisherigem Stand / zu grosser Sprung) - nur markieren. */
export type KmErgebnis = { km: string; quelle: KmQuelle; sicher: boolean; stelle: string; unplausibel: string };

/** Hoechster plausibler Sprung seit dem letzten bekannten km-Stand. */
export const KM_SPRUNG_BELEG = 100000;
export const KM_SPRUNG_TACHO = 20000;
/** "sicher" = nah am bisherigen Stand (eine Tankfuellung bzw. ein paar Wochen Fahrt). */
export const KM_SICHER = 5000;

const LABEL =
  /(KILOMETER\s*-?\s*STAND|KM\s*[-.]?\s*STAND|KM\s*[-.]?\s*STD\b\.?|TACHO\s*-?\s*STAND|TACHO|ODOMETER|LAUFLEISTUNG|KILOMETER(?!\s*-?\s*PREIS)|(?:^|[^A-Z0-9])KM\s*[:=](?!\s*\/)|^\s*KM\b(?!\s*\/))/i;

/** Ganze km-Zahl aus einem Token, sonst null. Zeiten, Datumsangaben, Dezimalzahlen und STAN/BATCH fallen raus. */
export function tokenZahl(roh: string): number | null {
  const t = String(roh || "").replace(/[.,:]+$/, "");
  if (!t) return null;
  if (/[:\/]/.test(t)) return null; // 12:34, 046183/420
  if (/^\d{1,2}\.\d{1,2}\.\d{2,4}$/.test(t)) return null; // Datum
  let s = "";
  if (/^\d+$/.test(t)) s = t;
  else if (/^\d{1,3}([.'’]\d{3})+$/.test(t)) s = t.replace(/[.'’]/g, "");
  else return null; // 1234,5 / 45,32 / 1,789 / 45.32
  const n = parseInt(s, 10);
  return isFinite(n) ? n : null;
}

/** Alle ganzen Zahlen eines Textstuecks. "123 456" (Tausender-Leerzeichen) wird zu 123456. */
export function zahlenIn(seg: string): number[] {
  let s = String(seg || "");
  s = s.replace(/\b\d{1,2}[.\-\/]\d{1,2}[.\-\/]\d{2,4}\b/g, " "); // Datum
  s = s.replace(/\b\d{1,2}:\d{2}(?::\d{2})?\b/g, " "); // Uhrzeit
  s = s.replace(/(^|[^\d.,])(\d{1,3}(?:[  ]\d{3})+)(?![\d]|[.,]\d)/g, (_m, a: string, b: string) => a + b.replace(/[  ]/g, ""));
  const out: number[] = [];
  const re = /\d[\d.,:'’\/]*/g;
  let m: RegExpExecArray | null;
  while ((m = re.exec(s))) {
    const after = s.slice(re.lastIndex, re.lastIndex + 8);
    if (/^\s*(km\s*\/\s*h|°|%|l\s*\/|min\b|u\s*\/\s*min|rpm|kw\b|ps\b)/i.test(after)) continue;
    const n = tokenZahl(m[0]);
    if (n !== null) out.push(n);
  }
  return out;
}

function plausibel(n: number, vorher: number, sprung: number, ohneVorherMin: number): boolean {
  if (!(n > 0) || n > 9999999) return false;
  if (vorher > 0) return n >= vorher && n <= vorher + sprung;
  return n >= ohneVorherMin;
}

function nurZahlZeile(l: string): boolean {
  return /^[\s\d.,'’]*\d[\s\d.,'’]*(km)?\s*$/i.test(l);
}

/**
 * km aus OCR-Text.
 * art "beleg": nur Zahlen hinter einer km-Bezeichnung (gleiche Zeile oder reine Zahlzeile direkt darunter)
 *              oder mit Einheit "km" — Preise, Liter, Datum, Belegnummern werden nie genommen.
 * art "tacho": groesste plausible ganze Zahl (nahe am bisherigen Stand, sonst 4–7 Stellen).
 */
export function kmAusText(text: string, vorherKm?: number | string | null, art?: string): KmErgebnis {
  const leer: KmErgebnis = { km: "", quelle: "", sicher: false, stelle: "", unplausibel: "" };
  const raw = String(text || "");
  if (!raw.trim()) return leer;
  const vk0 = parseInt(String(vorherKm == null ? "" : vorherKm).replace(/[^\d]/g, ""), 10);
  const vk = isFinite(vk0) && vk0 > 0 ? vk0 : 0;
  const L = raw.split(/\r?\n/);
  const kurz = (z: string) => String(z || "").replace(/\s+/g, " ").trim().slice(0, 80);
  const fertig = (n: number, q: KmQuelle, z: string): KmErgebnis =>
    ({ km: String(n), quelle: q, sicher: vk > 0 && n - vk <= KM_SICHER, stelle: kurz(z), unplausibel: "" });
  let unpl: { n: number; z: string } | null = null;
  const merke = (n: number, z: string) => { if (!unpl && n > 0) unpl = { n, z }; };
  const ende = (): KmErgebnis => {
    const u = unpl as { n: number; z: string } | null;
    return u ? { ...leer, stelle: kurz(u.z), unplausibel: String(u.n) } : leer;
  };

  if (art === "tacho") {
    const ok: { n: number; z: string }[] = [];
    for (const l of L) for (const n of zahlenIn(l)) {
      if (plausibel(n, vk, KM_SPRUNG_TACHO, 1000)) ok.push({ n, z: l });
      else if (vk > 0 && n >= 10000) merke(n, l);
    }
    if (!ok.length) return ende();
    ok.sort((a, b) => (vk > 0 ? a.n - b.n : b.n - a.n)); // mit Vorstand: naechste darueber; sonst groesste
    return fertig(ok[0].n, "tacho", ok[0].z);
  }

  // 1) Bezeichnung + Zahl
  for (let i = 0; i < L.length; i++) {
    const m = L[i].match(LABEL);
    if (!m) continue;
    const rest = L[i].slice((m.index || 0) + m[0].length);
    let kand = zahlenIn(rest);
    let z = L[i];
    if (!kand.length) {
      for (let k = 1; k <= 2 && i + k < L.length; k++) {
        if (nurZahlZeile(L[i + k])) { kand = zahlenIn(L[i + k]); z = L[i] + " " + L[i + k]; break; }
        if (LABEL.test(L[i + k])) break;
      }
    }
    for (const n of kand) { if (plausibel(n, vk, KM_SPRUNG_BELEG, 1)) return fertig(n, "beleg_label", z); merke(n, z); }
  }
  // 2) Zahl + Einheit km (nicht km/h, nicht €/km)
  const reE = /(\d[\d.'\u2019 \u00a0]*)\s*km\b(?!\s*\/)/gi;
  for (const l of L) {
    let m: RegExpExecArray | null;
    reE.lastIndex = 0;
    while ((m = reE.exec(l))) {
      const vor = l.slice(0, m.index);
      if (/[,]\s*$|\d[,]$/.test(vor)) continue; // 12,5 km = Teilstrecke
      const zz = zahlenIn(m[1]);
      const n = zz.length ? zz[zz.length - 1] : null;
      if (n === null) continue;
      if (plausibel(n, vk, KM_SPRUNG_BELEG, 1000)) return fertig(n, "beleg_einheit", l);
      if (n >= 1000) merke(n, l);
    }
  }
  return ende();
}

// ── Zeilen aus den Vision-Wortboxen ──────────────────────────────────────────
// DOCUMENT_TEXT_DETECTION gibt zweispaltige Belege oft blockweise aus ("KILOMETERSTAND\nFAHRER\n...\n123456\n0001").
// Aus den Wortboxen werden Zeilen nach y-Mitte gebildet und links->rechts sortiert, damit Bezeichnung und Wert
// wieder nebeneinander stehen.
type Pt = { x?: number; y?: number };
type Wort = { text: string; x: number; y: number; h: number };

export function zeilenAusAnnotation(fta: unknown): string {
  const worte: Wort[] = [];
  try {
    // deno-lint-ignore no-explicit-any
    const pages = (fta as any)?.pages || [];
    for (const p of pages) for (const b of p?.blocks || []) for (const par of b?.paragraphs || []) for (const w of par?.words || []) {
      const text = (w?.symbols || []).map((s: { text?: string }) => s?.text || "").join("");
      const v: Pt[] = w?.boundingBox?.vertices || [];
      if (!text || v.length < 4) continue;
      const ys = v.map((q) => q.y || 0), xs = v.map((q) => q.x || 0);
      const y0 = Math.min(...ys), y1 = Math.max(...ys);
      worte.push({ text, x: Math.min(...xs), y: (y0 + y1) / 2, h: Math.max(1, y1 - y0) });
    }
  } catch { return ""; }
  if (!worte.length) return "";
  const hs = worte.map((w) => w.h).sort((a, b) => a - b);
  const tol = hs[Math.floor(hs.length / 2)] * 0.6;
  worte.sort((a, b) => a.y - b.y);
  const zeilen: Wort[][] = [];
  for (const w of worte) {
    const z = zeilen[zeilen.length - 1];
    if (z && Math.abs(z[0].y - w.y) <= tol) z.push(w); else zeilen.push([w]);
  }
  return zeilen.map((z) => z.sort((a, b) => a.x - b.x).map((w) => w.text).join(" ")).join("\n");
}

/** Ergebnis fuer die Antwort: zuerst die Zeilen aus den Boxen, dann der Rohtext. */
export function kmAusVision(rawText: string, fta: unknown, vorherKm?: number | string | null, art?: string): KmErgebnis {
  const zeilen = zeilenAusAnnotation(fta);
  const a = zeilen ? kmAusText(zeilen, vorherKm, art) : null;
  if (a && a.km) return a;
  const b = kmAusText(rawText, vorherKm, art);
  return b.km || !a ? b : (b.unplausibel ? b : a);
}

// ── Tankbeleg (Datum/Liter/Preis unveraendert seit v3.9.419, km neu) ─────────
export function parseTankbeleg(text: string, kmErg?: KmErgebnis) {
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
  const k = kmErg || kmAusText(t, null, "beleg");
  out.km = k.km;
  return out;
}
