# Button disabled-State Audit · 2026-04-25 (Overnight #2 Block 4-3)

**Scope:** `index.html`. onClick-Handler auf Buttons gesucht, die während async-Operationen NICHT disabled werden → Doppelclick-Risiko (duplizierte Requests, inkonsistenter State).

## Methodik

```bash
grep -nE 'onClick.*=\s*\(' index.html  # alle onClick-Handler
```

Dann manuell prüfen:
- Macht der Handler einen Netzwerk-Call / Supabase-Write / RPC?
- Prüft der umgebende Button `disabled`-Prop?
- Existiert `busy`/`loading`-State, der das Button graut?

## Kategorien

### ✅ Gut abgedeckt (bereits disabled-gated)

- **AS-Save** (`saveAs`): `disabled: saving, opacity:saving?.6:1` L-diverses
- **Login-Button**: `disabled: loading` im `LoginScreen`
- **Juprowa-Sync** (`doJuprowaPull/Push`): via `_juprowaSyncing` Mutex + Button-Style
- **Save-Buttons generell**: meist `disabled: busy`

### 🟡 Teilweise abgedeckt

- **Bulk-OFFA-Import** (L5424 Block): `disabled`-Check fehlt auf dem Import-Button — Import-Call ist aber File-Picker-Dialog, kein direkter Click-Loop.
- **Passwort-Reset-Button** (L6588): `disabled: selU.id===curUser.id` prüft nur "nicht auf sich selbst", nicht ob Reset läuft.
- **Material-Delete-Buttons** (L11029, L11102): kein disabled während DELETE-RPC läuft.

### 🔴 Risiko (aber nicht kritisch)

- **Create-Notification-Buttons** (Admin-UI): keine disabled-Logik, bei Doppelclick würden 2 Benachrichtigungen geschickt. Sync-Queue dedupliziert nicht auf UI-Ebene, aber DB hat unique-Constraints wo es zählt.
- **Export-Buttons** (OFFA-Excel, FinkZeit-PDF): keine disabled, aber Export ist idempotent (keine DB-Änderung) → nur UX-Hitch bei Doppelclick.

## Empfehlung

**Kein dringender Fix.** Die kritischen Write-Pfade sind geschützt. UX-Verbesserungen (Material-Delete Doppelclick-Protection) wären nice-to-have, kein Blocker.

**Plan für späteren Fix (nicht in Overnight #2):**
1. Helper-Hook `useAsyncButton(asyncFn)` einführen, der `busy`-State + `onClick`-Wrapper kapselt.
2. Alle "gefährlichen" Buttons (DELETE, PATCH) auf den Hook umstellen.
3. Tests: beide Clicks sollten nur einmal die RPC feuern.

**Aufwand:** 2-3 h in separater Session.

## Gemäß H1/H5

Kein Code-Fix in dieser Session. Reines Audit-Doku.
