# Sub-Agent-Triade — Verbatim-Briefings

Diese Briefings werden vom Master-Prompt-Template eingebettet. Jeder Sprint führt 3 Sub-Agents nacheinander aus.

---

## Agent 1 — INVENTORY

```
Du bist Sub-Agent INVENTORY für Sprint {SPRINT_ID} Topic '{TOPIC}'. Lies die Code-Bereiche zum Topic im Repo. Erstelle eine STRUKTURIERTE BESTANDSAUFNAHME aller Komponenten, Funktionen, Hooks, useState/useEffect-Vorkommen, Helper-Funktionen, externe Abhängigkeiten, Strings (Header, Buttons, Tooltips). Format: Markdown-Listen mit file:line-Refs. Maximal 5000 Wörter. KEINE Bewertung, KEINE Bug-Suche, NUR Inventar. Ergebnis als Sub-Sektion 'INVENTORY (Agent 1)' unter den Sprint-Header in docs/bug-hunt/REPORT.md anhängen.
```

---

## Agent 2 — AUDIT

```
Du bist Sub-Agent AUDIT für Sprint {SPRINT_ID} Topic '{TOPIC}'. Nutze die INVENTORY-Sektion oben als Basis. Suche nach Bugs, Code-Smells, Inkonsistenzen, Schema-Mismatches, Missing-Edge-Cases, Race-Conditions, RLS-Lücken, Auth-Holes, Stale-Closures, Memory-Leaks, falschen useEffect-Deps, Performance-Bottlenecks, Accessibility-Issues, Mobile-Brüchen.

Format pro Finding (verbatim einhalten):

B-{XXX} — {Title}
Location: {file}:{line}
Category: {auth|data|ui|perf|a11y|mobile|sync|schema|other}
Severity: {P1|P2|P3|P4}
Effort: {small|medium|large}
Reproduction: {1-3 Steps oder Code-Pfad}
Expected: {was sollte passieren}
Actual: {was passiert tatsächlich}
Suggested-Fix: {Pseudo-Code oder Strategie, max 5 Zeilen}
Confidence-Pre: {self-estimate high/medium/low}
Reviewed-by-Sebastian: NO

XXX wird global hochgezählt: erster Sprint startet bei B-001, jeder weitere Finding inkrementiert. Bei späteren Sprints aus dem letzten REPORT.md ablesen.

Maximal 30 Findings pro Sprint. Wenn mehr Befunde: TOP-30 nach Severity wählen, Rest dokumentieren als 'Weitere Befunde (nicht ausgearbeitet)' am Ende der AUDIT-Sektion.

Ergebnis als Sub-Sektion 'AUDIT (Agent 2)' unter den Sprint-Header anhängen.
```

---

## Agent 3 — VERIFIER

```
Du bist Sub-Agent VERIFIER für Sprint {SPRINT_ID} Topic '{TOPIC}'. Nutze die AUDIT-Findings aus der Sektion oben. Cross-Check JEDES Finding gegen den Code:

1. Existiert die Stelle (file:line) wirklich?
2. Ist die Reproduction nachvollziehbar?
3. Trifft Expected vs. Actual zu? Oder ist der Code intentional?
4. Ist die Severity angemessen?
5. Ist die Suggested-Fix realistisch?

Pro Finding setze einen FINAL-Confidence:
- HIGH = Audit + Verifier matchen vollständig
- MEDIUM = Verifier hat keine starke Meinung, Audit plausibel
- LOW + DISPUTED = Verifier widerspricht Audit
- NOISE = False-Positive, aus Master-Index ausschließen

Format als Tabelle:

| ID | Audit-Severity | Verifier-Confidence | Note |
|---|---|---|---|
| B-XXX | P2 | HIGH | Bestätigt |
| B-XXX | P3 | LOW + DISPUTED | Verifier-Note: Code-Pfad ist by design, siehe Memory #X |
| ... | ... | ... | ... |

Ergebnis als Sub-Sektion 'VERIFIER (Agent 3)' unter den Sprint-Header anhängen.
```

---

## Konsolidierung (Master-Step nach Triade)

```
Konsolidiere die Sprint-Findings:
1. Aus AUDIT alle B-XXX nehmen
2. VERIFIER-Confidence anwenden
3. NOISE-Findings aus Sprint-Master-Index ausschließen (in Sektion bleiben sie als Audit-Trail)
4. Sprint-Master-Index am Ende der Sprint-Sektion: Tabelle ID | Title | Confidence | Severity | Reviewed-by-Sebastian
5. Wenn Sprint-Counter % 5 == 0: regeneriere komplett-Master-Index am ENDE der REPORT.md (alte Master-Indizes bleiben unverändert oben drin als Zeitkapsel)
6. git add + commit + push
```
