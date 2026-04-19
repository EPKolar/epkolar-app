# WhatsApp Integration Plan · v3.8 Stub-Phase · Block 8

## Scope v3.8

**IN SCOPE**:
- DB-Schema (`whatsapp_templates`, `whatsapp_log`) — `sql/WHATSAPP_SCHEMA_v3.8.sql`
- Default-Seeds (4 Templates) — `sql/WHATSAPP_SEEDS_v3.8.sql`
- RLS-Policies (Admin full, Büro read-only)

**OUT OF SCOPE (v3.8)** — explizit nicht gebaut:
- UI-Code in index.html für Template-Editor
- Meta-API-Integration (benötigt Meta Business Account)
- Auto-Send-Cron-Job
- Phone-Number-Validierung

**Begründung**: Die UI-Arbeit wäre 2-3h solide Feature-Dev. Ehrlicher ist: Schema + Seeds deployen, UI-Block in separater Session mit Sebastian-Input machen.

## Schritte nach v3.8-Deploy

### Schritt 1: Schema anlegen (Sebastian, 1 min)
```
supabase SQL-Editor → sql/WHATSAPP_SCHEMA_v3.8.sql ausführen
Verify: 2 Tabellen, je RLS=true, >=1 Policy.
```

### Schritt 2: Default-Templates seeden (Sebastian, 1 min)
```
supabase SQL-Editor → sql/WHATSAPP_SEEDS_v3.8.sql ausführen
Verify: 4 Templates in whatsapp_templates.
```

### Schritt 3: Feature-Block "WhatsApp UI" planen (Sebastian → nächste Session)

**User-Stories**:
- [WA-1] Admin sieht Sub-Tab "WhatsApp" unter Einstellungen.
- [WA-2] Template-Liste (Name, Event, Active) als Tabelle.
- [WA-3] Template-Editor (Name, Event-Dropdown, Sprache, Body-Textarea, Placeholders, Auto-Send-Checkbox).
- [WA-4] Preview-Feld das Body mit Dummy-Werten rendert.
- [WA-5] "📤 Senden simulieren" Button → schreibt whatsapp_log mit status='simulated'.
- [WA-6] Log-Tabelle zeigt letzte 50 Einträge mit status-Badge.

**Schätzung**: 2-3h Implementation + 1h Testing.

### Schritt 4: Meta-API-Integration (Feature Phase 2, separat)
- Meta Business Account anlegen (Sebastian)
- Approved WhatsApp Business Number bestellen
- Edge Function `whatsapp_send` mit Meta-Graph-API-Call
- Auto-Send-Cron (pg_cron): täglich um X Uhr für `auto_send=true` Templates durchgehen

## DB-Schema-Referenz

### whatsapp_templates
| Column | Type | Notiz |
|---|---|---|
| id | uuid PK | default gen_random_uuid |
| name | text NOT NULL | UI-sichtbarer Template-Name |
| event | text NOT NULL | 'appointment_confirm' / 'completion' / 'manual' |
| language | text | default 'de' |
| body | text NOT NULL | Template mit `{{placeholder}}` |
| placeholders | jsonb | Liste der erkannten Placeholders |
| auto_send | boolean | nur wirksam wenn Meta-API connected |
| active | boolean | soft-delete |

### whatsapp_log
| Column | Type | Notiz |
|---|---|---|
| id | uuid PK | |
| template_id | uuid FK → templates | |
| sent_to | text | +43-Format |
| sent_at | timestamptz | |
| status | text | 'queued'/'sent'/'delivered'/'read'/'failed'/'simulated' |
| meta_message_id | text | von Meta API, wenn echt gesendet |
| error | text | |
| arbeitsschein_id | text | optional FK zu arbeitsscheine |
| projekt_id | text | optional FK zu projects |
| rendered_body | text | body mit ersetzen Placeholders |

## Sicherheits-Notizen

- RLS: Nur Admin kann Templates schreiben (verhindert dass Monteure Nachrichten-Texte ändern)
- Büro sieht Templates (um zu wissen was rausgeht), kann aber nicht editieren
- Log: Admin+Büro sehen alles (Compliance/Audit), Monteure sehen nichts (PII-Schutz)
- Phone-Numbers werden in `sent_to` als Plaintext geloggt — EU-DSGVO-Hinweis: Log-Retention max 6 Monate vorschlagen
