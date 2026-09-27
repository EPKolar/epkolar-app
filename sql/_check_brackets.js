// ═══════════════════════════════════════════════════════════════════════════
// ABGELOEST am 27.09.2026 (v3.9.960). Dieses Werkzeug zaehlte ROHE Zeichen.
//
// WAS ES TAT: es lief ueber jedes Zeichen von index.html und zaehlte Klammern -
// auch die in Zeichenketten und Kommentaren. Seine Grundlinie war `() -2`.
//
// WARUM DAS NICHT TRAEGT: jede neue Zeile mit einer Klammer im Kommentar
// verschiebt die Zahl. Am 27.09.2026 stand sie bei `-6` und das Werkzeug
// beendete sich mit 1 - nicht weil in index.html eine Klammer fehlt, sondern
// weil Kommentare dazugekommen sind. Ein Tor, dessen Grundlinie mit jedem
// Kommentar wandert, meldet irgendwann rot fuer nichts, und dann glaubt ihm
// niemand mehr.
//
// UND ES WAR EINE FALLE: README.md, RUNBOOK.md und ARCHITECTURE.md wiesen an,
// es zu fahren, und nannten die `-2`. Wer dem folgte, bekam ein rotes Tor ohne
// Erklaerung. Aufgerufen hat es dabei KEIN Skript, kein Test und keine Kette -
// gefunden wurde das erst von einer Messung, die jeden Pruefer im Repo gegen
// die Ketten abgeglichen hat.
//
// WAS STATTDESSEN GILT: scripts/_bracket_check.py. Es streicht ZUERST
// Zeichenketten, Vorlagen-Literale und Kommentare und beurteilt nur den Rest;
// seine Grundlinie ist `() -1` und sie ist stabil. Es traegt ausserdem ein
// Lebenszeichen gegen die 0-Byte-Falle: eine leere Datei hat ausgeglichene
// Klammern, und wer nur auf die Zahlen schaut, haelt Datenverlust fuer eine
// Verbesserung.
// (Was auch _bracket_check.py NICHT kann, steht in
//  tests/test_klammertor_blindheit_v956.py: es beurteilt 28 % der Datei.
//  Ob der Streicher neu gebaut wird, ist Frage 15 in
//  docs/ENTSCHEIDUNGEN-OFFEN.md.)
//
// Diese Datei bleibt liegen (Hausregel "parken, nicht loeschen") und tut das
// einzig Sinnvolle: sie sagt es und ruft das gueltige Werkzeug auf, damit die
// Zeile im RUNBOOK weiter funktioniert.
// ═══════════════════════════════════════════════════════════════════════════
const { spawnSync } = require('child_process');
const path = require('path');

console.log('_check_brackets.js ist ABGELOEST (v3.9.960).');
console.log('Es zaehlte ROHE Zeichen, also auch Klammern in Kommentaren -');
console.log('seine Grundlinie -2 wanderte mit jedem neuen Kommentar.');
console.log('Gueltig ist scripts/_bracket_check.py. Wird jetzt gefahren:');
console.log('');

const ziel = path.join(__dirname, '..', 'scripts', '_bracket_check.py');
const r = spawnSync('python', [ziel], { stdio: 'inherit' });

if (r.error) {
  console.error('');
  console.error('Der Aufruf von python ist fehlgeschlagen: ' + r.error.message);
  console.error('Bitte direkt fahren:  python scripts/_bracket_check.py');
  process.exit(1);
}
process.exit(r.status === null ? 1 : r.status);
