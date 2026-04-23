# Duplicate String Audit · 2026-04-25 (Overnight #2 Block 5-2)

**Scope:** `index.html` String-Literale, Länge 4-60, >= 5× Vorkommen.
**Zweck:** Konstanten-Kandidaten identifizieren — Wartbarkeit + Typo-Prävention.
**Methode:** `$TEMP/epk_dupfind.py` (regex-scan + Counter).

## Scanning

- Total String-Literale gesehen: **20 505**
- Unique: **7 970**
- Mit ≥5 Vorkommen (nach Skip-Liste): **546**

## Top-20 Kandidaten (nach Duplicate-Count)

| Count | String | Kategorie |
|---:|---|---|
| 526 | `button` | HTML-element-string für React.createElement — Boilerplate |
| 452 | `optionalAccess` | Sucrase-Transpile-Artefakt |
| 369 | `access` | Sucrase-Transpile-Artefakt |
| 256 | `1px solid ` | CSS-Border-Prefix |
| 217 | `, {}, React.createElement(` | React-Boilerplate |
| 211 | `option` | `<option>`-Tag-String für createElement |
| 187 | `#22c55e` | EP-grün-Variante (Success) |
| 165 | `#ef4444` | Rot (Error) |
| 157 | `#f97316` | Orange (Warning) |
| 144 | `optionalCall` | Sucrase-Transpile-Artefakt |
| 140 | `100%` | CSS width/height |
| 114 | `space-between` | CSS flex-justify |
| 112 | `#fff` | Weiß |
| 101 | `#3b82f6` | Blau (Info) |
| 77 | `4px 8px` | CSS padding |
| 62 | `#009640` | **EP-GRÜN** (Brand-Primary!) |

## Zwei Kategorien

### 🎨 CSS-Farben — sollten Konstanten sein

Die Colors sind schon via `EP_GREEN` / `THEMES.dark` definiert, werden aber trotzdem wiederholt als Raw-Hex eingetippt. Eine Typo-Änderung am Markenton würde nicht überall durchschlagen.

| Hex | Nutzung | Count | Bestehende Konstante? |
|---|---|---:|---|
| `#22c55e` | Success-Grün | 187 | teilweise (V.ac?) |
| `#ef4444` | Error-Rot | 165 | — |
| `#f97316` | Warning-Orange | 157 | — |
| `#3b82f6` | Info-Blau | 101 | — |
| `#009640` | Brand-Grün | 62 | `EP_GREEN` (`const EP_GREEN="#009640"`) |
| `#eab308` | Gelb | 45 | — |
| `#8b5cf6` | Violett | 34 | — |
| `#71717a` | Grau | 36 | — |

**Empfehlung:** Ein `COLORS` Namespace-Object erstellen:
```js
const COLORS={
  brand: "#009640",       // EP-Grün
  success: "#22c55e",
  warning: "#f97316",
  error: "#ef4444",
  info: "#3b82f6",
  accent: "#8b5cf6",
  gold: "#eab308",
  neutral: "#71717a"
};
```
Dann schrittweise Callsites migrieren. **Aufwand:** groß (hunderte Stellen). Kann mit Regex-Replace gemacht werden, aber per R6 nicht in dieser Session.

### 🔤 Domain-Strings — potenzielle Typo-Quellen

| Value | Count | Bereich |
|---|---:|---|
| `arbeitsscheine` | 54 | Table-Name |
| `fahrzeuge` | 43 | Table-Name |
| `projektleiter` | 32 | Role-Name |
| `elektro` | 40 | Category-Value |
| `sanitaer` | 39 | Category-Value |

**Empfehlung:** Table-Names sollten in einem `TABLES`-Object zentralisiert werden. Role-Names existieren bereits als `SCHEINART_C` analog (aber sind dead code — siehe Block 5-1). Category-Values könnten aus `MATERIAL_CATS` (L9341) gezogen werden statt Raw.

### ⚙️ Transpile-Artefakte (nicht angetastet)

`optionalAccess`, `optionalCall`, `access` sind aus Sucrase-Transpile-Output (`_optionalChain([...])`-Pattern). Nicht manuell eingetippt → keine Konstanten-Kandidaten.

## Risiko-Beurteilung

- **Niedrig (aktuell):** Typos würden beim ersten Run auffallen (RLS-Error "table X not found" etc.).
- **Mittel (langfristig):** Schwerer zu refaktorieren ohne systematische Suche.
- **Hoch bei Markenfarben-Änderung:** wenn Sebastian je das EP-Grün feinjustiert → 62 Stellen per grep+replace, Fehlerrisiko.

## Empfehlung

**Keine Aktion in Overnight #2 (per H1/H5).** Ein separater Refactor-Block wäre ideal für:

1. `COLORS` Namespace einführen (1-2 h, +Bracket-Test pro Batch)
2. `TABLES` Namespace (`TABLES.ARBEITSSCHEINE = 'arbeitsscheine'` etc.)
3. Roles-Enum (analog zu SCHEINART_C-Muster, aber durchgesetzt)
4. Batch-Migration via regex-gesteuertes Find-Replace mit Tests nach jedem Batch

## Gemäß H1/H5

Kein Code-Touch in dieser Session.
