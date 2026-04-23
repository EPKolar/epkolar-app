# WhatsApp UI Preview · README

**Datei:** `preview/whatsapp_ui_v0.html`
**Version:** v0 (Mock · Preview-only)
**Gebaut:** 2026-04-24 Overnight Block B
**Schema-Basis:** `sql/WHATSAPP_SCHEMA_v3.8.sql` (v3.8.9 audit-fix)

## Öffnen

```bash
# Einfach: Doppel-Klick in Explorer (Browser öffnet file://)
start preview/whatsapp_ui_v0.html          # Windows
open  preview/whatsapp_ui_v0.html          # macOS

# Oder Local Server (empfohlen für MIME-Check):
python -m http.server 8000 --directory .
# → http://localhost:8000/preview/whatsapp_ui_v0.html
```

Keine Build-Tools nötig. React 18 kommt via `unpkg.com` CDN (production.min.js). Kein Supabase, kein Netzwerk-Call außer React-CDN beim ersten Load.

## Was ist Mock · Was ist real

| Bereich | In Preview | In echtem System |
|---|---|---|
| **3 Templates** | hardcoded im JS | `whatsapp_templates` Tabelle |
| **5 Log-Einträge** | hardcoded im JS | `whatsapp_log` Tabelle |
| **Rolle** | per Dropdown umstellbar | `public.users.role` + RLS |
| **RLS-Logik** | `perm(role)` Pure-Function | Supabase-Policies (`wt_admin_all`, `wt_buero_read`, `wl_admin_buero`, `wl_pl_read`) |
| **Send-Simulation** | `setLog([...l])` Pure-State | Edge Function `whatsapp_send` → Meta Graph API |
| **Meta-Credentials** | readonly Placeholder | Edge Function ENV (nicht im Client!) |
| **Auto-Send** | Toggle ohne Effekt | pg_cron → `auto_send=true` Templates |
| **Kontingent 47/1000** | hardcoded | Meta-API-Header `x-business-use-case-usage` |

## Integration-Plan (wann was)

### Stufe 1 · Schema-Deploy (Sebastian, 1 min pro File)

```
SQL-Editor:
  1. sql/WHATSAPP_SCHEMA_v3.8.sql   # Tabellen + RLS
  2. sql/WHATSAPP_SEEDS_v3.8.sql    # 4 Default-Templates
```

Verify: `SELECT tablename, rowsecurity FROM pg_tables WHERE tablename LIKE 'whatsapp%'` — 2 Zeilen, rls=true.
Siehe `sql/WHATSAPP_P3_TYPECHECK.sql` für FK-Typ-Verifikation (arbeitsschein_id/projekt_id).

### Stufe 2 · UI-Integration in `index.html` (CC, 2-3 h)

Vorbedingung: Stufe 1 deployt.

- [ ] Neuer Tab-Entry im `tabs[]` Array mit `perm:"admin"` (oder ähnlich)
- [ ] `AdminWhatsApp` Component extrahiert aus Preview nach index.html
- [ ] Supabase-Reads: `_sbGet("whatsapp_templates","order=name.asc")`, `_sbGet("whatsapp_log","order=sent_at.desc&limit=50")`
- [ ] Supabase-Writes: `_sbPost`/`_sbPatch` mit `_authRetry`-Wrap (Standard-Pattern)
- [ ] Simulate-Send: direkt `_sbPost("whatsapp_log", {...,status:"simulated"})`, Edge Function kommt in Stufe 3
- [ ] RLS-Tests: als Büro einloggen → Template-Edit-Buttons weg, aber Log sichtbar

### Stufe 3 · Echte Meta-API (Feature-Phase 2, separate Session)

Vorbedingung: Sebastian hat Meta Business Account + WhatsApp Business Number.

- Edge Function `whatsapp_send` (Deno) mit `fetch("https://graph.facebook.com/v20.0/{PHONE_ID}/messages")`
- ENV: `WHATSAPP_TOKEN`, `WHATSAPP_PHONE_ID`, `WHATSAPP_BUSINESS_ID`
- Rate-Limit-Handling (429 → exponential backoff)
- Webhook für `delivered`/`read`-Status (neuer Endpoint `/webhook/whatsapp`, schreibt `meta_message_id`)
- pg_cron `whatsapp_auto_send_tick()` — täglich um 08:00, geht `auto_send=true` Templates + passende Events durch

### Stufe 4 · Monitoring (Feature-Phase 2+)

- Kontingent-Widget im AdminPanel (aus Meta-Header abgeleitet)
- Opt-out-Log (wenn Empfänger `stop` schreibt, Meta sendet Webhook)
- DSGVO: Log-Retention 6 Monate, Daily-Delete-Job für Einträge älter als 180 Tage

## Bekannte Schema-Lücken / Felder die noch fehlen

### whatsapp_log
- `opt_out boolean default false` — falls Empfänger `stop` schrieb
- `delivered_at timestamptz` — separat von `sent_at`
- `read_at timestamptz` — delivered-to-read Gap oft interessant
- `cost_usd numeric(6,4)` — pro-Nachricht-Kosten von Meta-Header

### whatsapp_templates
- `meta_template_id text` — Meta-gepflegte Template-ID nach Approval
- `meta_approval_status text` — pending/approved/rejected
- `variables_map jsonb` — Mapping `{{placeholder}}` → DB-Feld oder RPC-Call

Diese Felder sind NICHT im aktuellen Schema — separater Migration-Commit wenn Meta-API-Integration beginnt.

## Sicherheits-Hinweise

- **Keine Credentials im Client.** Access Token lebt in Edge Function ENV.
- **Keine Phone-Numbers in Klartext loggen** — aktuell zu Demo-Zwecken, Produktions-Schema maskiert hoffentlich.
- **RLS-Absicherung ist DB-seitig** — Client-Side `perm(role)` ist UI-Optimierung, keine Security.
- **Opt-out ehren** — falls `opt_out=true` → Auto-Send muss skippen.

## Bekannte Einschränkungen der Preview

- React-CDN-Load bei jedem Öffnen — ohne Internet: kein React → kein UI.
- Kein Routing — alles im `<div id="root">`.
- Kein Dark-Mode-Toggle — nur Dark hardcoded (matcht index.html Default).
- Kein Realzeit-Sync zwischen Browser-Tabs — State ist pro-Tab lokal.
- Kein Persist — Refresh löscht Mock-State (inkl. Simulate-Sends).

## Design-Token-Sync

CSS-Variablen `--bg/--sb/--cd/--bd/--tx/--dm/--mt/--ep` sind 1:1 aus `THEMES.dark` in index.html kopiert. Falls die Haupt-App ihre Tokens ändert, Preview manuell nachziehen (es gibt keinen Import).

## Feedback-Punkte für Sebastian

1. Event-Liste (`appointment_confirm`, `completion`, `reminder`, `manual`) — ausreichend oder fehlt was?
2. Placeholder-Liste per Template — soll UI die möglichen Placeholders vorschlagen (aus AS/Projekt-Schema)?
3. PL-RLS für Log: nur eigene AS oder alle AS?
4. Auto-Send-Eskalation: wenn delivered-Fail 3× → Admin-Mail?
5. Template-Approval-Flow bei Meta: soll UI das `meta_approval_status` zeigen?
