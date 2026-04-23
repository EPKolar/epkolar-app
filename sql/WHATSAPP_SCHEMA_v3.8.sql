-- ============================================================
-- WhatsApp UI-Stub Schema · v3.7.9 Block 8
-- Sebastian führt manuell im Supabase SQL-Editor aus (nach Review).
-- KEIN Meta-API-Call in der App — nur Template-Editor + Log-Stub.
-- ============================================================

-- ── whatsapp_templates: Nachrichten-Vorlagen ──
CREATE TABLE IF NOT EXISTS public.whatsapp_templates (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name         text NOT NULL UNIQUE,
  event        text NOT NULL,  -- 'appointment_confirm' | 'completion' | 'manual' | ...
  language     text NOT NULL DEFAULT 'de',
  body         text NOT NULL,
  placeholders jsonb DEFAULT '[]'::jsonb,
  auto_send    boolean DEFAULT false,
  active       boolean DEFAULT true,
  created_at   timestamptz DEFAULT now(),
  updated_at   timestamptz DEFAULT now()
);

COMMENT ON TABLE public.whatsapp_templates IS 'v3.8 Stub: Templates für WhatsApp-Nachrichten. Keine Meta-API-Integration, nur UI-Editor + Preview.';

-- ── whatsapp_log: Audit-Trail für simulierte/echte Sends ──
CREATE TABLE IF NOT EXISTS public.whatsapp_log (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  template_id     uuid REFERENCES public.whatsapp_templates(id) ON DELETE SET NULL,
  sent_to         text,
  sent_at         timestamptz DEFAULT now(),
  status          text,        -- 'queued' | 'sent' | 'delivered' | 'read' | 'failed' | 'simulated'
  meta_message_id text,
  error           text,
  arbeitsschein_id text,
  projekt_id      text,
  rendered_body   text         -- finaler text mit Placeholder-Replacement
);

COMMENT ON TABLE public.whatsapp_log IS 'v3.8 Stub: Log aller Send-Versuche. Status=simulated für Stub-Phase.';

-- ── RLS ──
ALTER TABLE public.whatsapp_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.whatsapp_log       ENABLE ROW LEVEL SECURITY;

-- Templates: Admin full, Büro read-only
DROP POLICY IF EXISTS wt_admin_all  ON public.whatsapp_templates;
DROP POLICY IF EXISTS wt_buero_read ON public.whatsapp_templates;

CREATE POLICY wt_admin_all ON public.whatsapp_templates
  FOR ALL TO authenticated
  USING      (EXISTS (SELECT 1 FROM public.users WHERE auth_user_id=auth.uid() AND role='admin'))
  WITH CHECK (EXISTS (SELECT 1 FROM public.users WHERE auth_user_id=auth.uid() AND role='admin'));

CREATE POLICY wt_buero_read ON public.whatsapp_templates
  FOR SELECT TO authenticated
  USING (EXISTS (SELECT 1 FROM public.users WHERE auth_user_id=auth.uid() AND role IN ('admin','buero','projektleiter')));

-- Log: Admin+Büro full
DROP POLICY IF EXISTS wl_admin_buero ON public.whatsapp_log;

CREATE POLICY wl_admin_buero ON public.whatsapp_log
  FOR ALL TO authenticated
  USING      (EXISTS (SELECT 1 FROM public.users WHERE auth_user_id=auth.uid() AND role IN ('admin','buero')))
  WITH CHECK (EXISTS (SELECT 1 FROM public.users WHERE auth_user_id=auth.uid() AND role IN ('admin','buero')));

-- v3.8-Audit 24.04: PL darf Log lesen (Rückfrage-Kontext Kunde "keine WhatsApp bekommen")
-- SELECT-only, kein Write. Monteur-Rolle bleibt weiterhin komplett ausgesperrt.
DROP POLICY IF EXISTS wl_pl_read ON public.whatsapp_log;
CREATE POLICY wl_pl_read ON public.whatsapp_log
  FOR SELECT TO authenticated
  USING (EXISTS (
    SELECT 1 FROM public.users
    WHERE auth_user_id = auth.uid() AND role = 'projektleiter'
  ));

-- ── Verify ──
SELECT tablename, rowsecurity AS rls, (
  SELECT count(*) FROM pg_policies WHERE tablename=t.tablename
) AS policies
FROM pg_tables t
WHERE tablename IN ('whatsapp_templates','whatsapp_log');
-- Erwartet: je 2 Zeilen mit rls=true, policies>=1
