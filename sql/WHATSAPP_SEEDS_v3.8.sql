-- ============================================================
-- WhatsApp Default-Templates · v3.7.9 Block 8
-- Nach WHATSAPP_SCHEMA_v3.8.sql ausführen.
-- ============================================================

INSERT INTO public.whatsapp_templates (name, event, language, body, placeholders, auto_send, active)
VALUES
  ('Terminbestätigung',
   'appointment_confirm',
   'de',
   'Hallo {{kunde}}, wir bestätigen den Termin am {{termin}}. Monteur: {{monteur}}. Bei Fragen: +43 2279 2361. EP Kolar',
   '["kunde","termin","monteur"]'::jsonb,
   true,
   true),

  ('Auftrag abgeschlossen',
   'completion',
   'de',
   'Hallo {{kunde}}, Ihr Auftrag {{asnummer}} wurde heute abgeschlossen. Arbeitsschein folgt per Email. Danke. EP Kolar',
   '["kunde","asnummer"]'::jsonb,
   true,
   true),

  ('Termin-Erinnerung (24h vorher)',
   'appointment_reminder',
   'de',
   'Erinnerung: Morgen {{termin}} haben Sie einen Termin mit unserem Monteur {{monteur}}. Absage bis heute 18:00 möglich. EP Kolar',
   '["termin","monteur"]'::jsonb,
   false,
   true),

  ('Frei formuliert',
   'manual',
   'de',
   '{{text}}',
   '["text"]'::jsonb,
   false,
   true)
ON CONFLICT DO NOTHING;

-- Verify
SELECT name, event, auto_send, active, created_at FROM public.whatsapp_templates ORDER BY created_at;
