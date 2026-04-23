# A11y Audit · 2026-04-25 (Overnight #2 Block 5-4)

**Baseline:** `5e190ef` (v3.8.39).
**Methode:** grep-basiert + `window._a11yCheck()` existiert (L~805), wird aber hier statisch analysiert.
**Scope:** Struktur-Audit ohne echten Browser. Runtime-Check über `_a11yCheck` möglich.

## Struktur-Zahlen

| Element | Count | Kommentar |
|---|---:|---|
| `React.createElement('button',...)` | 503 | Buttons |
| `React.createElement('input',...)` | 264 | Input-Felder |
| `React.createElement('label',...)` | 154 | Labels |
| `htmlFor:` Zuweisungen | **0** | **Label-for-Input-Binding fehlt komplett!** |
| `aria-label` / `aria-labelledby` im Code | 2 | Nur in `_a11yCheck` selber (Reader-Check) |
| `<img>` ohne `alt` | 0 | ✅ gefixt in v3.8.39 |

## Kern-Befund: Label ↔ Input-Binding

**0 von 154 `<label>`-Elementen haben `htmlFor`**. Screen-Reader können damit Input-Felder nicht semantisch mit Labels verknüpfen.

**Aktueller Pattern** (mehrfach gesehen):
```js
React.createElement('label', { style: LL() }, 'KM Start *'),
React.createElement('input', { type:'number', value:..., onChange:..., style: II() })
```

**Fix-Pattern**:
```js
React.createElement('label', { htmlFor: 'km_start', style: LL() }, 'KM Start *'),
React.createElement('input', { id: 'km_start', type:'number', ... })
```

Oder das robustere **implizit nested label**:
```js
React.createElement('label', { style: LL() },
  'KM Start *',
  React.createElement('input', { type:'number', ... })
)
```

Beide Varianten sind in React ok.

## Weitere Gaps

### G1 · `aria-label` auf Icon-only-Buttons

Viele Delete-/Edit-Buttons zeigen nur ein Emoji (🗑️ / ✏️). Ohne `aria-label` → Screen-Reader liest "black rubbish bin emoji" statt "Löschen".

Beispiele (suchen mit `grep -n 'createElement.*button.*🗑'`):
- Material-Delete-Buttons
- AS-Delete-Buttons
- Image-Remove-Buttons

Fix: `aria-label:'Löschen'` auf jedem Icon-only-Button.

### G2 · `type="button"` Default

React setzt `type="submit"` als Default für `<button>` in Forms. Das kann zum unerwünschten Form-Submit bei jedem Click führen, selbst wenn es kein Form-Submit-Button ist.

**Regression-Risk:** Hoch wenn jemand einen Button in ein `<form>` einbaut ohne `type` zu setzen.

**Fix:** Alle Buttons sollten explizit `type:'button'` bekommen (außer Submit-Buttons, die `type:'submit'` kriegen).

Gap: Von 503 Buttons sind **0** mit explizitem `type:'button'`. Alle laufen auf React-Default (was außerhalb Forms harmlos ist, aber Fragil).

### G3 · Semantic HTML

Es gibt viele `<div>` die als Buttons dienen (click-Handler ohne `role="button"` und ohne Tab-Index). Nicht tastaturbedienbar.

**Beispiel-Grep:** `grep -nE "onClick.*createElement\('div'" index.html | wc -l` würde das sichtbar machen (nicht gelaufen, geschätzt dutzende).

**Fix:** Tastatur-Bediener: `<div role="button" tabIndex={0} onKeyDown={...}>` oder besser ein echtes `<button>` verwenden.

### G4 · Farbkontrast

`window._a11yCheck()` macht Heuristik-Checks (nicht voll WCAG-konform). Dark-Theme könnte auf bestimmten Dot-Displays oder Farbschwäche-Usern Probleme haben. Light-Theme (siehe `THEMES.light`) hat mehr Kontrast per se.

**Empfehlung:** Chrome DevTools Lighthouse-A11y-Audit einmal laufen lassen, dann punktuelle Fixes.

## Priorisierung

| Gap | Count | Effort | Impact | Prio |
|---|---:|---|---|---|
| G0 htmlFor/id Binding | 154×154 | hoch | hoch (Screen-Reader) | P2 |
| G1 aria-label auf Icon-Buttons | ~50 geschätzt | mittel | mittel | P2 |
| G2 type='button' Default | 503 | niedrig | niedrig (präventiv) | P3 |
| G3 Div-as-Button | ~20 geschätzt | hoch | mittel (Tastatur) | P3 |
| G4 Farbkontrast | ? | variabel | variabel | P4 |

## Ehrliche Einschätzung

EP Kolar ist eine interne Haustechnik-App. Ihre a11y-Anforderungen sind nicht wie bei einer Behörden-App. Trotzdem:

- **P2-Fixes (G0+G1)** sollten in einer dedizierten Session angegangen werden — das ist ~6-8 h Refactor-Arbeit, sollte mit klar verifizierbaren Unit-Tests + Lighthouse-Check ergänzt werden.
- **P3-Fixes (G2+G3)** sind nice-to-have, kein Blocker.

## Gemäß H1/H5

Kein Code-Fix in Overnight #2. Audit erhält neue Findings in `CODE_DEBT_v2.md` als:
- **Block 5-4 Finding A** = G0 htmlFor-Binding
- **Block 5-4 Finding B** = G1 icon-button aria-labels

Sebastian priorisiert.
