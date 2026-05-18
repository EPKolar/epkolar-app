-- WhatsApp Integration — Schema v3.9.19 / v3.9.20 (siehe Sprint-Plan)
-- NICHT auf Supabase ausführen — Sebastian-Action morgen früh.

CREATE TABLE IF NOT EXISTS whatsapp_config (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  meta_business_id text,
  meta_phone_number_id text,
  meta_access_token text,
  webhook_verify_token text,
  enabled boolean DEFAULT false,
  updated_at timestamptz DEFAULT now(),
  updated_by text
);

CREATE TABLE IF NOT EXISTS whatsapp_templates (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL UNIQUE,
  language text DEFAULT 'de',
  category text,
  body_text text NOT NULL,
  meta_template_name text,
  meta_approved boolean DEFAULT false,
  enabled boolean DEFAULT true,
  auto_trigger text,
  created_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS whatsapp_messages (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  template_id uuid REFERENCES whatsapp_templates(id),
  to_phone text NOT NULL,
  payload_vars jsonb,
  status text DEFAULT 'pending',
  meta_message_id text,
  error_message text,
  created_at timestamptz DEFAULT now(),
  sent_at timestamptz,
  updated_at timestamptz
);

ALTER TABLE whatsapp_config ENABLE ROW LEVEL SECURITY;
ALTER TABLE whatsapp_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE whatsapp_messages ENABLE ROW LEVEL SECURITY;

CREATE POLICY wa_config_admin ON whatsapp_config FOR ALL TO authenticated
  USING (EXISTS(SELECT 1 FROM public.users WHERE auth_user_id = auth.uid() AND role = 'admin'));
CREATE POLICY wa_templates_read ON whatsapp_templates FOR SELECT TO authenticated USING (true);
CREATE POLICY wa_templates_insert ON whatsapp_templates FOR INSERT TO authenticated WITH CHECK (EXISTS(SELECT 1 FROM public.users WHERE auth_user_id = auth.uid() AND role = 'admin'));
CREATE POLICY wa_templates_update ON whatsapp_templates FOR UPDATE TO authenticated USING (EXISTS(SELECT 1 FROM public.users WHERE auth_user_id = auth.uid() AND role = 'admin'));
CREATE POLICY wa_templates_delete ON whatsapp_templates FOR DELETE TO authenticated USING (EXISTS(SELECT 1 FROM public.users WHERE auth_user_id = auth.uid() AND role = 'admin'));
CREATE POLICY wa_messages_read ON whatsapp_messages FOR SELECT TO authenticated USING (true);
CREATE POLICY wa_messages_insert ON whatsapp_messages FOR INSERT TO authenticated WITH CHECK (true);

INSERT INTO whatsapp_templates (name, body_text, auto_trigger, meta_template_name) VALUES
  ('as_status_abgeschlossen', 'Hallo {{1}}, Ihr Auftrag {{2}} wurde abgeschlossen. EP Kolar GmbH', 'as_status_change', 'epkolar_as_done'),
  ('appointment_confirm', 'Hallo {{1}}, Ihr Termin am {{2}} um {{3}} ist bestätigt. EP Kolar GmbH', 'appointment_confirm', 'epkolar_appt_confirm')
ON CONFLICT (name) DO NOTHING;
