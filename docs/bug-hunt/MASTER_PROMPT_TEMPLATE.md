# Master-Prompt für Sprint {SPRINT_ID} — Topic '{TOPIC}'

Datum: {DATE}
Branch: `cc-bug-hunt-eternal/2026-04-26`

Du bist Sub-Sprint-Driver. Führe folgende Schritte aus:

## 1. Branch-Setup

```bash
cd "T:\05_Claude\02_Baumanagment & Zeiterfassungs - APP\03_Repos\epkolar-app"
git fetch origin
git checkout cc-bug-hunt-eternal/2026-04-26
git pull --ff-only
```

## 2. Sprint-Header in REPORT.md anhängen

```markdown
---

## Sprint {SPRINT_ID} — {TOPIC}
Date: {DATE}
Round: <ableiten aus SPRINT_ID: 1-15=R1, 16-25=R2, 26+=R3+>
Repo-State: <git rev-parse HEAD kurz>

### INVENTORY (Agent 1)
<wird durch Agent 1 gefüllt>

### AUDIT (Agent 2)
<wird durch Agent 2 gefüllt>

### VERIFIER (Agent 3)
<wird durch Agent 3 gefüllt>

### Sprint-Master-Index
<wird durch Konsolidierung gefüllt — Tabelle der finalen Findings>

---
```

## 3. Agent 1 — INVENTORY

Verbatim wie in `docs/bug-hunt/SUB_AGENT_BRIEFINGS.md` Sektion "Agent 1 — INVENTORY". Substituiere `{SPRINT_ID}` und `{TOPIC}` mit den aktuellen Werten.

## 4. Agent 2 — AUDIT

Verbatim wie in `SUB_AGENT_BRIEFINGS.md` "Agent 2 — AUDIT".

**ID-Counter**: Nimm letzte `B-XXX` aus REPORT.md +1 als Startwert. Falls keine Findings vorhanden: starte bei `B-001`.

## 5. Agent 3 — VERIFIER

Verbatim wie in `SUB_AGENT_BRIEFINGS.md` "Agent 3 — VERIFIER".

## 6. Konsolidierung

Verbatim wie in `SUB_AGENT_BRIEFINGS.md` "Konsolidierung".

## 7. Master-Index alle 5 Sprints

Wenn `SPRINT_ID % 5 == 0`:

- Regeneriere Master-Index am **ENDE** von REPORT.md (alte bleiben oben drin als Audit-Trail)
- Format: `## Master-Index nach Sprint {SPRINT_ID} (Stand {DATE})`
- Tabelle: `ID | Title | Confidence | Severity | Sprint | Reviewed-by-Sebastian`
- NUR non-NOISE-Findings

## 8. Push

```bash
git add docs/bug-hunt/REPORT.md
git commit -m "sprint {SPRINT_ID}: {TOPIC} — N findings (X high, Y medium, Z low)"
git push origin cc-bug-hunt-eternal/2026-04-26
```

## ABSOLUTE NO-GOs für jeden Sprint

- KEIN Touch an `index.html`, `sw.js`, `tests/`, `package.json` (existiert nicht)
- KEIN Code-Fix — nur Doku/Findings
- KEIN merge in main, KEIN cherry-pick, KEIN rebase auf main
- KEIN Push auf main, NUR auf `cc-bug-hunt-eternal/2026-04-26`
- KEINE neuen Dependencies
- KEIN Touch an Auth-Code (`_silentReAuth`, `_sbAuthRefresh`, `_sbRH`, `_sbWH`, `_sbH`)
- KEIN Touch an `_optionalChain`
