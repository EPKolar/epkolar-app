"""Regression-Tests fuer v3.9.349 Fix-A planData Server-Pull Merge statt Overwrite.

Diagnose-Doc: docs/DIAGNOSE_TICKET_VERLUST.md, Schwachstelle #1.

Befund (BVH Sparkasse Ravelsbach): 3 lokal angelegte Tickets, DB hat 1
gespeichert; 2 verschwanden. Ursache: Z.5305 Server-Pull-Resolve hat
planData.tickets KOMPLETT durch server.tkts ersetzt, statt zu mergen.
Lokal-pending Tickets in SyncQueue gingen verloren, wenn der naechste
Server-Pull vor dem SyncQueue-Drain lief.

Fix:
  - SQ.getAll() vor setPlanData; extrahiere pending POST-IDs (Tickets+Plans)
    und pending DELETE-IDs.
  - setPlanData merged:
      Server-Stand (gefiltert: pending DELETEs raus) + lokale prev-Tickets,
      deren id NICHT in serverIds aber EIN pending POST in SQ ist.
  - Analog fuer Plans.

NICHT angetastet:
  - Speicher-Logik anderer Stores (time_entries/forms/defects/arbeitsscheine)
    — gleiche Schwaeche dokumentiert, separater Fix in spaeterer Welle.
  - _juprowaPush, Tank-Flow, RLS-Welle-1.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")


def test_app_version_at_least_349():
    m = re.search(r'APP_VERSION="3\.9\.(\d+)-supabase"', INDEX)
    assert m and int(m.group(1)) >= 349


def test_sw_ver_at_least_349():
    m = re.search(r"SW_VER\s*=\s*'epkolar-v3\.9\.(\d+)'", INDEX)
    assert m and int(m.group(1)) >= 349


def test_cache_name_at_least_349():
    sw_js = (ROOT / "sw.js").read_text(encoding="utf-8")
    m = re.search(r'CACHE_NAME\s*=\s*"epkolar-v3\.9\.(\d+)"', sw_js)
    assert m and int(m.group(1)) >= 349


def test_sw_header_at_least_349():
    sw_js = (ROOT / "sw.js").read_text(encoding="utf-8")
    m = re.match(r"//\s*EP Kolar Service Worker v3\.9\.(\d+)", sw_js)
    assert m and int(m.group(1)) >= 349


def test_sq_getall_called_before_planData_merge():
    """SQ.getAll() muss VOR der setPlanData-Merge-Stelle stehen."""
    sq_pos = INDEX.find("await SQ.getAll()")
    assert sq_pos >= 0, "SQ.getAll-Aufruf fehlt im Initial-Load-Merge"
    # Eine der setPlanData-Resolve-Stellen
    setplandata_merge_pos = INDEX.find("_v349PendingTicketPosts")
    assert setplandata_merge_pos >= 0, "v349-Pending-Ticket-Posts-Set fehlt"
    assert sq_pos < setplandata_merge_pos, "SQ.getAll muss VOR der Merge-Logik laufen"


def test_pending_ticket_post_set_built():
    """Pending Ticket-POST-IDs werden gesammelt."""
    assert '_v349PendingTicketPosts.add(it.body.id)' in INDEX, \
        "Pending Ticket-POST-IDs werden nicht gesammelt"


def test_pending_ticket_delete_set_built():
    """Pending Ticket-DELETE-IDs werden gesammelt."""
    assert "_v349PendingTicketDeletes" in INDEX
    assert '"/api/tickets/"' in INDEX or "'/api/tickets/'" in INDEX or \
        '"/api/tickets/")' in INDEX or '.startsWith("/api/tickets/")' in INDEX, \
        "DELETE-URL-Pattern /api/tickets/ fehlt"


def test_pending_plan_post_set_built():
    """Plans bekommen das gleiche Merge-Pattern."""
    assert "_v349PendingPlanPosts.add(it.body.id)" in INDEX, \
        "Pending Plan-POST-IDs werden nicht gesammelt"


def test_server_tickets_filtered_by_pending_deletes():
    """Server-Tickets, die lokal pending-DELETE haben, werden NICHT zurueck in den State gespiegelt."""
    pattern = re.compile(
        r"tkts\.filter\(t=>!\s*_v349PendingTicketDeletes\.has\(t\.id\)\)"
    )
    assert pattern.search(INDEX), \
        "Server-Tickets werden nicht gegen pending DELETEs gefiltert"


def test_local_pending_tickets_preserved():
    """Lokal-POST-pending Tickets bleiben im State, wenn Server sie noch nicht kennt."""
    # Muster: prev.tickets||[]).filter(t=>!_srvTicketIds.has(t.id)&&_v349PendingTicketPosts.has(t.id)
    pattern = re.compile(
        r"prev\.tickets\|\|\[\]\)\.filter\(t=>!\s*_srvTicketIds\.has\(t\.id\)\s*&&\s*_v349PendingTicketPosts\.has\(t\.id\)\)"
    )
    assert pattern.search(INDEX), \
        "Lokale Pending-Tickets werden nicht bewahrt"


def test_local_pending_plans_preserved():
    """Lokal-POST-pending Plans bleiben analog im State."""
    pattern = re.compile(
        r"prev\.plans\|\|\[\]\)\.filter\(p=>!\s*_srvPlanIds\.has\(p\.id\)\s*&&\s*_v349PendingPlanPosts\.has\(p\.id\)\)"
    )
    assert pattern.search(INDEX), \
        "Lokale Pending-Plans werden nicht bewahrt"


def test_upd_tickets_concatenates_server_then_local():
    """upd.tickets = [...serverTickets, ...localPendingTickets] Pattern."""
    pattern = re.compile(
        r"upd\.tickets\s*=\s*\[\s*\.\.\._serverTickets\s*,\s*\.\.\._localPendingTickets\s*\]"
    )
    assert pattern.search(INDEX), \
        "upd.tickets-Concat-Pattern (server + local) fehlt"


def test_upd_plans_concatenates_server_then_local():
    pattern = re.compile(
        r"upd\.plans\s*=\s*\[\s*\.\.\._serverPlans\s*,\s*\.\.\._localPendingPlans\s*\]"
    )
    assert pattern.search(INDEX), \
        "upd.plans-Concat-Pattern (server + local) fehlt"


def test_juprowa_push_call_unchanged():
    """_juprowaPush HART unangetastet (Phase-2-sensitiv)."""
    anchor = "_juprowaPush(editId).then(r=>{if(!r||(!r.ok&&r.error))console.warn"
    assert anchor in INDEX, "_juprowaPush-Anker veraendert"


def test_createTicket_sq_push_unchanged():
    """createTicket SQ.push fuer POST /api/tickets bleibt unveraendert."""
    # Anker auf einen einzigartigen Substring der SQ.push-Body-Struktur
    anchor = 'SQ.push({url:"/api/tickets",method:"POST",body:{id:ticket.id,plan_id:'
    assert anchor in INDEX, "createTicket SQ.push-Anker veraendert"
