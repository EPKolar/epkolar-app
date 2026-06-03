# Urlaub-Verwaltungsrecht — exakte Effektiv-Rechte-Logik (für guard_urlaub_edit / guard_kontingent)

**Für Chat-Claude/Sebastian, 2026-06-03.** Damit der Server-Trigger DIESELBE Logik nutzt wie die App.

## 🔴 WICHTIG: 'urlaub' kann NICHT der Verwaltungs-Key sein
`'urlaub'` steht im **modules-Default JEDER Rolle** — admin, projektleiter, buero, obermonteur,
techniker, **monteur**, helfer, viewer (index.html ~L2635-2642). Es ist die **Tab-Sichtbarkeit**
("Urlaub-Tab sehen + eigene Anträge stellen"), die praktisch jeder hat.

→ Würde man Bearbeiten/Genehmigen an `hasPerm('urlaub')` koppeln, bekäme **jeder Monteur** sofort
Voll-Verwaltung (alle MA-Salden sehen, fremde Anträge genehmigen). **Das ist der Over-Grant, den wir
vermeiden müssen.** Deshalb bleibt der Verwaltungs-Key ein SEPARATER, NICHT-Default-Key: **`urlaub_edit`**
(in KEINER Rolle per Default → Default = deny → nur per-Person zuweisbar → genau Sebastians Anforderung
"pro Person setzbar, by default nur admin").

Der sichtbare Zuweisungs-Toggle existiert bereits (Admin-Panel → Benutzer → Berechtigungen → Zeile
"Urlaub/ZA…", ⚙️-Button). Empfehlung: nur das **Label** schärfen (siehe unten), Key bleibt `urlaub_edit`.

## Effektive-Rechte-Funktion (1:1 wie die App, `hasPerm`, index.html ~L3603)
```
hasPerm(user, key):
  if user == null            -> false
  if user.locked (truthy)    -> false            # gesperrt = nie
  role = ROLES[user.role]
  if role == null            -> false            # unbekannte Rolle = deny
  # perms_override ist ein JSONB-OBJEKT { key: true|false } (NICHT das permissions-Array!)
  if user.perms_override[key] === false -> false # explizite Aberkennung gewinnt
  if user.perms_override[key] === true  -> true  # explizite Erteilung
  return (key IN role.modules)                   # sonst Rollen-Default
```
Wichtig: **dreiwertig** — Override kann `true` (erteilen), `false` (aberkennen) ODER fehlen (→ Rollen-Default).

### Zuweisung (Admin-Panel, `togglePermOverride`, index.html ~L7402)
Beim ⚙️-Klick: `roleHas = key IN ROLES[role].modules`. Existiert noch kein Override →
`perms_override[key] = !roleHas`; existiert schon → Override löschen (zurück zum Default).
Persistiert via `PUT /api/users/:id { perms_override: {...} }`. Für `urlaub_edit` (roleHas=false bei allen
außer via override) → erster Klick setzt `perms_override.urlaub_edit = true`. ✅ persistent.

## Trigger-Logik, die das EXAKT spiegelt (für guard_urlaub_edit + guard_kontingent)
```sql
-- effektives urlaub_edit-Recht des aktuellen JWT-Users:
WITH me AS (
  SELECT role, perms_override
  FROM public.users
  WHERE auth_user_id::text = (auth.jwt() ->> 'sub')
  LIMIT 1
)
SELECT
  role = 'admin'                                                    -- admin immer voll
  OR (perms_override -> 'urlaub_edit')::text = 'true'               -- explizite Erteilung
  -- KEIN Rollen-Default für urlaub_edit (in keiner Rolle enthalten) → sonst nichts
FROM me;
```

### ⚠️ Bug-Hinweis zur aktuellen Live-Logik `perms ~ '%urlaub_edit%'`
Ein reiner **String-Match** (`~`/`LIKE '%urlaub_edit%'`) auf `perms_override::text` ist falsch für den
**Aberkennungs-Fall**: `perms_override = {"urlaub_edit": false}` enthält den String "urlaub_edit" →
`~` matcht → Trigger würde fälschlich **erlauben**. Korrekt ist der **Wert-Check**:
`(perms_override -> 'urlaub_edit')::text = 'true'` (bzw. `(perms_override->>'urlaub_edit')::boolean IS TRUE`).
Solange niemand `urlaub_edit:false` setzt, ist der Unterschied unsichtbar — aber sauberer ist der Wert-Check.

Falls auch das `permissions`-Array (JSONB `["..."]`) als Quelle gelten soll, zusätzlich:
`OR (permissions @> '["urlaub_edit"]')`. Die App nutzt für Berechtigungen aber **perms_override**, nicht
das permissions-Array — der Admin-Toggle schreibt nach perms_override.

## Empfohlene Label-Schärfung (CC kann das in der App umsetzen, low-risk)
Damit Sebastian den richtigen Toggle erkennt:
- `urlaub`      → Label "Urlaub-Tab sehen (eigene Anträge)"     (Tab-Sichtbarkeit, Default für alle)
- `urlaub_edit` → Label "Urlaub/Abwesenheit verwalten (bearbeiten + genehmigen)"  (Verwaltung, per-Person)

## Status
- Client-Gate (AbsView Bearbeiten/Speichern/Alle-genehmigen/Übersicht) = `isAdmin = admin||PL || hasPerm('urlaub_edit')` (v3.9.104/107).
- Server-Trigger live = `admin OR perms~'urlaub_edit'` → bei Wert-Check-Umstellung 1:1 deckungsgleich.
- **Trigger bleibt auf `urlaub_edit`** (Sebastian-Entscheidung "bis dahin sicher"). KEIN Flip auf 'urlaub'.
