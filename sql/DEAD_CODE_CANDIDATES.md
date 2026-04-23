# Dead Code Candidates · 2026-04-24

**Scope:** `index.html`.
**Methodik:**
- Alle Top-Level `function NAME`, `const NAME = `, `let NAME = `, `var NAME = ` extrahieren.
- Für jedes `NAME`: Vorkommen-Count via `\bNAME\b`-Regex.
- `count == 1` → nur Deklaration, kein Use. Kandidat für Dead Code.

**Tool:** `C:/Users/technik/AppData/Local/Temp/epk_deadcode.mjs` (Node-Skript ad-hoc).

**Ergebnis:** 287 Top-Level-Namen. **7 Kandidaten** mit `count == 1`.

## Kandidaten

| Name | Line | Typ | Grund |
|------|------|-----|-------|
| `ESKALATION_RULES` | 2763 | const-Object | Escalation-Regelwerk ohne Consumer — Feature unvollständig? |
| `INIT_AS` | 2706 | const-Array | Initial-Seed für Arbeitsscheine — historische Fixture? |
| `INIT_WZ` | 2722 | const-Array | Initial-Seed für Werkzeuge — historische Fixture? |
| `LazyImg` | 13292 | function-Component | Image-lazy-load, nirgends importiert |
| `MATERIAL_UNITS` | 9345 | const-Array | Units-Liste, aber Code verwendet Raw-Strings |
| `SCHEINART_C` | 399 | Object.freeze Enum | Enum definiert, Code nutzt raw-Strings (`'stoerung'`) |
| `SCHEINSTATUS_C` | 398 | Object.freeze Enum | Enum definiert, Code nutzt raw-Strings (`'aufgenommen'`) |

## Manuell verifiziert

Jeder Kandidat wurde mit `grep -nE "\b<NAME>\b" index.html` gegengecheckt — alle 7 haben
exakt **einen** Treffer (= die Deklaration selbst).

## Interpretation

### Enum-Konstanten (SCHEINART_C, SCHEINSTATUS_C)
Wurden als Frozen-Objects angelegt (vermutlich als Best-Practice für Konstanten-
Definition), aber der bestehende Code greift direkt auf die String-Werte zu. Beide
Welten parallel = toter Code.

**Optionen:**
- **A** Aufräumen: Konstanten löschen, akzeptieren dass Code mit Strings arbeitet.
- **B** Durchsetzen: Code auf Konstanten-Referenz umstellen → Type-Safety via IDE.
  Groß (hunderte Callsites).
- **C** Minimal: `eslint-disable` an Konstanten, Kommentar "Reserviert für zukünftige
  Typsicherheit".

### Fixtures (INIT_AS, INIT_WZ)
Sehen aus wie Demo-Seeds oder Migration-Defaults. Wurden vermutlich beim Umstieg auf
Supabase irrelevant. **Löschen** (A) ist wahrscheinlich richtig.

### MATERIAL_UNITS
Units-Liste für Material-Bestellung. Das UI sollte eigentlich aus dieser Liste
renderieren — wenn nicht, ist das UX-Schwäche (inkonsistente Units), nicht nur
Dead Code. **Klären + ggf. UI verdrahten.**

### ESKALATION_RULES
Gutes Kandidat für abgerissenes Feature. Bei L2763 lesen und beurteilen: war das
ein Notification-Escalation-Plan? Wenn Business-Case lebt, wiederverdrahten;
sonst löschen.

### LazyImg
React-Komponente für Lazy-Loaded-Images. War vielleicht für Foto-Galerie geplant,
Stattdessen ist die aktuelle Implementation native `<img loading="lazy">`. **Löschen**.

## Regel: NICHT automatisch löschen (R6, D4)

Keine der 7 werden in dieser Overnight-Session gelöscht. Grund:
1. Heuristik kann False-Positives haben (z. B. wenn ein Name dynamisch über `window[name]`
   oder `import()` geladen würde — unwahrscheinlich in diesem Codebase, aber möglich).
2. Enum-Konstanten sind Dokumentations-Artefakte (lesbare API-Beschreibung), auch
   wenn technisch ungenutzt.
3. Löschung sollte mit Sebastian besprochen werden: "Was war die Absicht?"

## Empfohlener Ablauf

**Nächste Session**, wenn 30 min Zeit:

```
# Für jeden Kandidaten:
1. Line lesen, 3-5 Nachbarzeilen Kontext checken.
2. Git-Blame: wann wurde das eingefügt, mit welcher Message?
3. Entscheidung: Löschen / Verdrahten / Mit eslint-Kommentar markieren.
4. 1-2 Patches, Bracket+Syntax-Check nach jedem, commit.
```

Erwarteter Gewinn: ~200-400 Zeilen weniger `index.html`, weniger Lese-Rauschen.

## Limitations

- Das Skript erfasst nur `^function`, `^const`, `^let`, `^var` (Line-Start). Helfer
  innerhalb anderer Funktionen (`const foo = ...` eingerückt) sind nicht berücksichtigt.
- Es gibt 280 Namen (287 - 7), die min. 2x vorkommen — aber "2x = einmal + einmal genutzt"
  heißt nicht zwingend "richtig genutzt" (nur 1x genutzt kann auch Suboptimum sein).
  Für tiefere Analyse wäre ein AST-Scan (TypeScript-Compiler, babel-plugin-unused) nötig.
