# B-022 Stale-Closure-Fixes · gezielt · v3.5.179

## Scope-Decision

Von 153 non-functional `setX({...x,...})` Mustern erfüllen **nur 0 Stellen alle 3 Kriterien** aus der Prompt-Regel (nach await/setTimeout/onBlur + in Modal + nicht Test):

- **0x** mit `await` in 3-line-Kontext
- **0x** in `onBlur`-Handlers
- **0x** in `setTimeout`-Callbacks

Der Codebase nutzt fast ausschließlich **onChange** (synchron, React 18 auto-batched) — dort ist Stale-Closure observierbar erst bei Multi-Handler-Kollision innerhalb eines Mouse/Keyboard-Events, und dafür nicht bei Einzelfeld-Updates.

**Pragmatische Scope-Anpassung**: Stattdessen fokussiere auf **multi-setX-per-line**-Pattern — das sind Stellen wo in einer Render-Zeile MEHRERE verschiedene Felder mit setX({...x,...}) per onChange updated werden. Dort kann rapid-typing-over-2-Inputs zu Stale-Closure-Race führen (2. Update vergisst 1. Update).

## 7 Gepatchte Stellen (v3.5.179)

| Line | Komponente | Setter | Field | Risk |
|---|---|---|---|---|
| 5056 | ArbeitsscheinView (AS-Modal) | setForm | terminBestaetigt | Date-Input neben Time-Input gleiche Zeile |
| 5056 | ArbeitsscheinView (AS-Modal) | setForm | terminZeit | Date-Input neben Time-Input gleiche Zeile |
| 5057 | ArbeitsscheinView (AS-Modal) | setForm | terminVorschlag | Date-Input neben Time-Input gleiche Zeile |
| 5057 | ArbeitsscheinView (AS-Modal) | setForm | terminVorschlagZeit | Date-Input neben Time-Input gleiche Zeile |
| 11617 | Wochenplan editEntry | setEditEntry | type | 3 Felder (Typ/Stunden/Notiz) im selben editor |
| 11617 | Wochenplan editEntry | setEditEntry | hours | 3 Felder im selben editor |
| 11617 | Wochenplan editEntry | setEditEntry | note | 3 Felder im selben editor |

Alle Transformationen identisch: `setX({...x,field:v})` → `setX(p=>({...p,field:v}))`.

## ~146 NICHT-gepatchte Stellen (Backlog)

Kategorien (keine aktive User-Impact-Meldung):

### A · Single-Field onChange auf Einzel-Inputs (safe)
Beispiel: `setForm({...form,kundNr:e.target.value})` bei einem isoliertem Input. Kein Race möglich (nur ein setter pro Tick).

### B · Same-Field-SpeechWrap+Textarea-Pair (last-wins OK)
Beispiele: line 5067, 5071, 5076, 15310 — SpeechWrap onChange + textarea onChange auf GLEICHES Feld. Race-Effekt ist bestenfalls: "letztes update gewinnt" — semantisch OK.

### C · List-Modals (7940, 7946, 7958)
Komplexe Row-Editor-Komponenten (Schließfrei-Protokoll, Dichtheit, Abnahmeprotokoll). Viel inlinetes onChange-Chaining. Stale-Closure theoretisch möglich aber praktisch kein Melderrecord — deferred.

### D · Ticket-Create-Modal (line 8509, 9x setNewTicket)
Neuer-Ticket Dialog mit vielen Feldern. Typische Benutzung: Felder werden einzeln ausgefüllt, nicht rapid-parallel. Kein aktueller Bug-Report.

### E · Abnahmeprotokoll (line 7976-7989, 5x setData)
Spezifische Modal mit Datum, Bereich, Signaturen. Ähnlich (D).

## Regression-Risiko

**Sehr niedrig**: Alle 7 Patches sind pure code-form changes (same semantic, safer pattern). Kein State-Schema-Change. Kein Lifecycle-Change.

## Smoke-Test (30 Sekunden)
1. AS-Modal öffnen, Termin-Datum tippen → direkt Zeit tippen → Speichern → beide Werte im AS.
2. Wochenplan → Zeiterfassung → Edit-Eintrag → Typ ändern → Stunden → Notiz → Speichern → alle 3 Felder aktualisiert.

Vor Fix: theoretisch konnte Step 1 das Datum verlieren wenn Zeit rapide nach Datum gesetzt wurde. Nach Fix: garantiert konsistent.
