/* ===========================================================================
   freivar.js - DAUERRIEGEL gegen FREIE VARIABLEN in index.html
   ---------------------------------------------------------------------------
   Fehlerklasse, die er faengt (live am 2026-08-29 durch alle drei Tore
   gekommen): ein Rueckruf war als `tf` deklariert und als `f` gelesen.
   Kein Syntaxfehler, kein Tippfehler-Muster - ein ReferenceError im Render,
   weisser Schirm, sobald der Codepfad betreten wird.

   ECHTER Parser (espree) + ECHTE Sichtbarkeitsanalyse (eslint-scope) -
   dieselbe Maschine, die hinter ESLints no-undef steckt.  Eine Heuristik
   waere hier wertlos: index.html enthaelt 8143 Pfeilfunktionen, 838
   Funktionsausdruecke, 7530 Bloecke, 832 catch-Klauseln und 198261
   Bezeichner.  Wer das mit regulaeren Ausdruecken angeht, erzeugt entweder
   Fehlalarme (dann wird der Riegel abgeschaltet) oder uebersieht Faelle
   (dann ist er wertlos).

   WERKZEUGKETTE: die drei Pakete liegen MITVERSIONIERT unter
   scripts/freivar/node_modules/ (25 Dateien, 511 KB - siehe HERKUNFT.txt).
   Kein `npm install`, kein package.json im Repo noetig.  Fehlt der Ordner
   trotzdem, ist der Ausgang ROT (Code 4) - NIEMALS ein stilles Ueberspringen.

   RUECKGABECODES  (jeder ist ein EIGENER Ausgang, keiner ist "so ungefaehr")
     0  sauber - gemessen, nichts gefunden
     1  FREIE VARIABLE(N) gefunden
     2  Aufruffehler (Datei fehlt / kein Argument)
     3  KONNTE NICHT MESSEN - Parsefehler, kein <script>-Block, o.ae.
        (ausdruecklich NICHT dasselbe wie "nichts gefunden": ein frueherer
         Mantel meldete eine syntaktisch kaputte Datei als SAUBER)
     4  WERKZEUGKETTE FEHLT - der Riegel kann nichts messen
     5  EIGENPROBE GESCHEITERT - der Riegel findet seinen eigenen,
        kuenstlich eingebauten Fehler nicht, misst also nichts

   Aufruf:  node scripts/freivar/freivar.js index.html [--json] [--alle]
=========================================================================== */
'use strict';
const fs = require('fs');
const path = require('path');

/* ---------- 0. Werkzeugkette: da oder ROT, nie uebersprungen ------------- */
const VEND = path.join(__dirname, 'node_modules');
let espree, escope, globalsPkg;
try {
  /* Absolute Pfade, mit Absicht: ein blankes require('espree') koennte ein
     FREMDES node_modules irgendwo oberhalb erwischen.  Dann liefe der Riegel
     gegen eine unbekannte Version - und die Probe "Werkzeugkette fehlt ->
     ROT" waere nicht mehr messbar, weil sie zufaellig gruen wuerde. */
  espree = require(path.join(VEND, 'espree'));
  escope = require(path.join(VEND, 'eslint-scope'));
  globalsPkg = require(path.join(VEND, 'globals'));
} catch (e) {
  console.error('WERKZEUGKETTE FEHLT - der Riegel kann NICHTS messen.');
  console.error('  erwartet: ' + VEND);
  console.error('  ' + e.message.split('\n')[0]);
  console.error('  Die Pakete sind mitversioniert. Fehlen sie, ist die Arbeitskopie');
  console.error('  unvollstaendig:  git checkout -- scripts/freivar/node_modules');
  console.error('  Ersatzweise:     npm i espree@10 eslint-scope@8 globals@15');
  console.error('                   in scripts/freivar/');
  process.exit(4);
}

/* ---------- 1. Inline-<script>-Bloecke herausschneiden ------------------- */
function bloecke(raw) {
  const out = []; const re = /<script([^>]*)>/gi; let m;
  while ((m = re.exec(raw))) {
    const attrs = m[1], start = m.index + m[0].length;
    const end = raw.indexOf('</script>', start);
    if (end < 0) { const err = new Error('<script> ohne Schlusstag ab Offset ' + start); err.nichtMessbar = 1; throw err; }
    re.lastIndex = end + 9;
    if (/\bsrc\s*=/i.test(attrs)) continue;      // externes Skript
    if (/\btype\s*=\s*["']?(?!text\/javascript|module|application\/javascript)/i.test(attrs)) continue;
    out.push({ start, end, code: raw.slice(start, end) });
  }
  return out;
}

const PARSE = { ecmaVersion: 'latest', sourceType: 'script', loc: false, range: true, comment: false };

function elternSetzen(wurzel) {
  (function go(n, par) {
    if (!n || typeof n !== 'object') return;
    if (Array.isArray(n)) { n.forEach(x => go(x, par)); return; }
    if (!n.type) return;
    Object.defineProperty(n, '_eltern', { value: par, enumerable: false, configurable: true });
    for (const k in n) { if (k === '_eltern' || k === 'range') continue; go(n[k], n); }
  })(wurzel, null);
  return wurzel;
}

/* ---------- 2. Kern: eine Zeichenkette -> Liste freier Namen ------------- */
/* Gibt { treffer, zeichen, bloecke } zurueck oder wirft mit .nichtMessbar. */
function messen(raw, quelle) {
  const blks = bloecke(raw);
  if (!blks.length) {
    const err = new Error('kein einziger inline-<script>-Block gefunden - hier wurde NICHTS gemessen');
    err.nichtMessbar = 1; throw err;
  }
  let zeichen = 0;
  const asts = blks.map(b => {
    zeichen += b.code.length;
    try { return { b, ast: elternSetzen(espree.parse(b.code, PARSE)) }; }
    catch (e) {
      const err = new Error(e.message);
      err.nichtMessbar = 1; err.absOffset = b.start + (e.index || 0);
      throw err;
    }
  });

  /* --- erlaubte globale Namen --- */
  const erlaubt = new Set();
  const add = n => erlaubt.add(n);
  for (const k of ['browser', 'es2025', 'worker', 'serviceworker']) Object.keys(globalsPkg[k] || {}).forEach(add);
  [ // per <script src> geladene Bibliotheken + Sucrase-Hilfsnamen
    'React', 'ReactDOM', 'L', 'bcrypt', 'dcodeIO', 'jspdf', 'jsPDF', 'pdfjsLib', 'qrcode',
    '_react', '_reactdom', '_optionalChain', '_nullishCoalesce', '_asyncNullishCoalesce',
    '_asyncOptionalChain', '_asyncOptionalChainDelete', '_optionalChainDelete',
    '_createNamedExportFrom', '_createStarExport', '_interopRequireDefault', '_interopRequireWildcard',
    'exports', 'module', 'require', 'globalThis', 'arguments'
  ].forEach(add);

  /* alles, was die Datei selbst auf window.* legt */
  {
    const re = /\bwindow\s*\.\s*([A-Za-z_$][A-Za-z0-9_$]*)\s*=(?!=)/g; let m;
    while ((m = re.exec(raw))) add(m[1]);
    const re2 = /\bwindow\s*\[\s*['"]([A-Za-z_$][A-Za-z0-9_$]*)['"]\s*\]\s*=(?!=)/g;
    while ((m = re2.exec(raw))) add(m[1]);
  }

  /* Deklarationen auf oberster Ebene JEDES Blocks teilen sich das globale
     Objekt.  ACHTUNG, hier lag ein Fehlalarm-Erzeuger: eslint-scope reicht im
     GLOBALEN Sichtbereich AUCH aufgeloeste Referenzen durch `through` (darum
     braucht ESLints no-undef eine eigene Globalenliste).  Eine eigene Sammlung
     ueber `ast.body` verfehlt jedes `var` in einem Block - z.B. `try{var _bi=..}`
     am Dateiende.  Darum die Namen von eslint-scope selbst nehmen:
     `globalScope.variables` enthaelt das var-Hoisting vollstaendig. */
  const analysen = asts.map(({ b, ast }) => ({
    b, ast,
    sm: escope.analyze(ast, {
      ecmaVersion: 2025, sourceType: 'script',
      ignoreEval: true, nodejsScope: false, impliedStrict: false,
      fallback: 'iteration'
    })
  }));
  for (const { sm } of analysen) for (const v of sm.globalScope.variables) add(v.name);

  /* --- Sichtbarkeitsanalyse --- */
  const treffer = [];
  for (const { b, sm } of analysen) {
    for (const ref of sm.globalScope.through) {
      const name = ref.identifier.name;
      if (erlaubt.has(name)) continue;
      /* `typeof x` auf einen undeklarierten Namen ist in JS LEGAL und wirft
         NICHT.  Ohne diese Ausnahme meldet der Riegel jede Faehigkeitsabfrage
         als Fehler. */
      const el = ref.identifier._eltern;
      if (el && el.type === 'UnaryExpression' && el.operator === 'typeof' && el.argument === ref.identifier) continue;
      const off = b.start + ref.identifier.range[0];
      treffer.push({ name, off, schreibend: ref.isWrite(), lesend: ref.isRead() });
    }
  }
  treffer.sort((a, b) => a.off - b.off);
  return { treffer, zeichen, bloecke: blks.length, quelle };
}

/* ---------- 3. EIGENPROBE - laeuft bei JEDEM Aufruf --------------------- */
/* Ein gruener Riegel beweist nur dann etwas, wenn derselbe Lauf zeigt, dass
   er ueberhaupt rot werden KANN.  Darum baut er sich hier den bekannten
   Fehler selbst ein (Rueckruf als `tf` deklariert, als `f` gelesen) und
   verlangt, ihn zu finden - und verlangt zugleich, dass die saubere Fassung
   still bleibt.  Kosten: unter 5 ms. */
/* Die gruene Probe deckt mit Absicht auch die ANDERE Richtung ab: sie nutzt
   einen Browser-Globalen (document), einen Namen aus einem ANDEREN
   <script>-Block, eine window.*-Zuweisung und ein `typeof` auf einen
   undeklarierten Namen.  Wer eines dieser Zugestaendnisse ausbaut, erzeugt
   Fehlalarme - und der Riegel faellt hier auf, statt draussen abgeschaltet
   zu werden.  (Gemessen: ohne diese Zutaten blieb eine ausgehebelte
   Erlaubtliste unbemerkt - 527 Fehlalarme, Eigenprobe trotzdem still.) */
const PROBE_ROT = '<script>function _p(xs){return xs.map(function(tf){return f.id});}</script>';
const PROBE_GRUEN =
  '<script>var _pq=1;window._pq=_pq;</script>' +
  '<script>function _p(xs){return xs.map(function(tf){return document.title+tf.id+_pq});}' +
  'window._p=_p;if(typeof _pnichtDa==="undefined"){_p([]);}</script>';
function eigenprobe() {
  let rot, gruen;
  try { rot = messen(PROBE_ROT, 'eigenprobe-rot').treffer.map(t => t.name); }
  catch (e) { return 'die rote Eigenprobe war nicht messbar: ' + e.message; }
  try { gruen = messen(PROBE_GRUEN, 'eigenprobe-gruen').treffer.map(t => t.name); }
  catch (e) { return 'die gruene Eigenprobe war nicht messbar: ' + e.message; }
  if (!rot.includes('f')) return 'der eingebaute Fehler (`f` statt `tf`) wurde NICHT gefunden -> der Riegel misst nichts. Gefunden: ' + JSON.stringify(rot);
  if (gruen.length) return 'die SAUBERE Eigenprobe schlug an -> der Riegel erzeugt Fehlalarme. Gefunden: ' + JSON.stringify(gruen);
  return null;
}

/* ---------- 4. Mantel ---------------------------------------------------- */
const file = process.argv[2];
const JSONOUT = process.argv.includes('--json');
const ALLE = process.argv.includes('--alle');
if (!file || file.startsWith('--')) {
  console.error('Aufruf: node scripts/freivar/freivar.js <index.html> [--json] [--alle]');
  process.exit(2);
}
if (!fs.existsSync(file)) { console.error('Datei nicht gefunden: ' + file); process.exit(2); }

const t0 = Date.now();
const fehler = eigenprobe();
if (fehler) {
  console.error('EIGENPROBE GESCHEITERT - dieser Lauf beweist NICHTS.');
  console.error('  ' + fehler);
  process.exit(5);
}
const tProbe = Date.now() - t0;

const raw = fs.readFileSync(file, 'utf8');
const zeilenAnfang = [0];
for (let i = 0; i < raw.length; i++) if (raw.charCodeAt(i) === 10) zeilenAnfang.push(i + 1);
function zeile(off) {
  let lo = 0, hi = zeilenAnfang.length - 1;
  while (lo < hi) { const mid = (lo + hi + 1) >> 1; if (zeilenAnfang[mid] <= off) lo = mid; else hi = mid - 1; }
  return lo + 1;
}
const alleZeilen = raw.split(String.fromCharCode(10));

let erg;
try { erg = messen(raw, file); }
catch (e) {
  if (!e.nichtMessbar) throw e;
  console.error('KONNTE NICHT MESSEN - das ist NICHT "nichts gefunden".');
  if (e.absOffset != null) {
    const z = zeile(e.absOffset);
    console.error('  ' + path.basename(file) + ':' + z + '  ' + e.message);
    console.error('  ' + (alleZeilen[z - 1] || '').trim().slice(0, 200));
    console.error('  Die Datei ist syntaktisch kaputt - die App startet so gar nicht.');
  } else {
    console.error('  ' + e.message);
  }
  process.exit(3);
}

const treffer = erg.treffer.map(t => Object.assign({ zeile: zeile(t.off) }, t));
const ms = Date.now() - t0;
/* Immer auf stderr, damit --json-Leser die Messmenge pruefen koennen:
   "0 Treffer" ist nur dann gruen, wenn auch wirklich etwas gemessen wurde. */
console.error('# GEMESSEN bloecke=' + erg.bloecke + ' zeichen=' + erg.zeichen +
  ' eigenprobe_ms=' + tProbe + ' gesamt_ms=' + ms);

if (JSONOUT) { console.log(JSON.stringify(treffer, null, 1)); process.exit(treffer.length ? 1 : 0); }

const proName = new Map();
for (const t of treffer) { if (!proName.has(t.name)) proName.set(t.name, []); proName.get(t.name).push(t); }
if (!treffer.length) {
  console.log('KEINE freie Variable in ' + path.basename(file) +
    '  (' + erg.bloecke + ' Bloecke, ' + erg.zeichen + ' Zeichen JS, ' + ms + ' ms)');
  process.exit(0);
}
console.log('FREIE NAMEN: ' + proName.size + ' verschiedene, ' + treffer.length + ' Fundstellen');
for (const [name, list] of [...proName.entries()].sort((a, b) => a[1][0].off - b[1][0].off)) {
  console.log('');
  console.log('== ' + name + '  (' + list.length + 'x)' + (list.some(x => x.schreibend) ? '  [schreibend]' : ''));
  for (const t of (ALLE ? list : list.slice(0, 6))) {
    console.log('   ' + path.basename(file) + ':' + t.zeile + '  |  ' + (alleZeilen[t.zeile - 1] || '').trim().slice(0, 180));
  }
  if (!ALLE && list.length > 6) console.log('   ... ' + (list.length - 6) + ' weitere');
}
process.exit(1);
