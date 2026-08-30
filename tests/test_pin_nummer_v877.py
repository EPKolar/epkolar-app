# -*- coding: utf-8 -*-
"""
v3.9.877 - Die Pin-Nummer auf dem Bauplan ist keine Nummer, sondern ein Listenplatz.

STATUS: DIESE RIEGEL SIND JETZT ROT. Sie beschreiben den Sollzustand nach dem
Eingriff; der Befund darunter ist an v3.9.875 gemessen.

BEFUND (drei Ursachen, alle am selben Symptom):

(1) DIE REIHENFOLGE KOMMT UNSORTIERT AUS DER DATENBANK.
    _ticketNr vergibt die Nummer als reinen Array-Index:
        planTickets.forEach((t,i)=>{m[t.id]=i+1;});
    planTickets stammt ueber allTickets aus planData.tickets, das aus
    API.getTickets() kommt:
        getTickets: function(pid) { return pid?_sbGet("tickets","project_id=eq."
            +encodeURIComponent(pid)):_sbGet("tickets"); },
    _sbGet baut die URL aus select=* + filter + limit=5000 - KEIN order=.
    PostgREST garantiert ohne order= keine Reihenfolge; Postgres liefert beim
    Seq-/Bitmap-Scan physische Heap-Reihenfolge. Jedes PATCH auf tickets
    (Status, Fortschritt, Kommentar, Foto - _sbPatch, und die Sync-Queue
    schickt sie im Minutentakt) schreibt eine NEUE Tupelversion und verschiebt
    die Zeile. Nirgends in VPlan wird auf Tickets .sort( angewandt - gesucht,
    nur [...plans].sort( existiert. Der Kommentar an _ticketNr behauptet
    "kanonische, stabile Pin-Nummer" - stabil ist daran nichts.
    Eine persistierte Nummer gibt es nicht: gemessen gegen die Live-DB
    (jiggujpruejkaomgxarp, anon) antwortet select=nr / pin_nr / nummer auf
    tickets UND defects mit 42703 "column does not exist"; created_at und
    page existieren.

(2) DIE NUMMERNBASIS IST ROLLENABHAENGIG.
    allTickets ist fuer Feldrollen auf die EIGENEN Tickets gefiltert:
        const _vpIsField=curUser&&!isAdmin&&(curUser.role==="monteur"||...);
        return _vpIsField?_raw.filter(t=>t.assignee===_vpMid):_raw;
    planTickets erbt das. Der Monteur zaehlt also 1..k ueber SEINE Tickets,
    Buero/PL/Admin 1..N ueber alle. Der Plan-Report-PDF-Knopf ist auf
    (isAdmin||role==="buero") beschraenkt - der Bauleiter druckt also die
    volle Nummerierung, das Handy des Monteurs zeigt eine andere. Das ist
    kein Heap-Zufall, das ist deterministisch bei JEDEM Aufruf falsch.
    Gleiche Klasse: die De-Duplizierung der Defect-Pins baut ihr Set
    ebenfalls aus allTickets - der Monteur bekommt Mangel-Pins zusaetzlich
    angezeigt, die fuer Admin als Ticket-Spiegel weggefiltert werden, und
    damit nochmals verschobene Nummern.

(3) BILDSCHIRM UND PDF ZAEHLEN UEBER VERSCHIEDENE MENGEN.
    _ticketNr nummeriert ALLE planTickets - auch die ohne Position (es gibt
    dafuer sogar einen eigenen Warn-Toast: "N Tickets ohne Plan-Position -
    in der Sidebar weiterhin sichtbar"). Der PDF wirft sie vorher weg und
    nummeriert dann neu:
        const _pins=(pins||[]).filter(t=>t&&t.x!=null&&t.y!=null);
        const _nrById={};_pins.forEach((t,i)=>{_nrById[t.id]=i+1;});
    Ein einziges positionsloses Ticket verschiebt damit jede folgende Nummer
    im PDF um eins gegen den Bildschirm.

SOLL (worauf diese Riegel pruefen):
  * tickets und defects werden mit order=id.asc geladen.
  * Die Nummer wird NICHT mehr aus planTickets vergeben, sondern aus einer
    eigenen, rollenunabhaengigen und deterministisch nach id sortierten
    Basis (_nrBase).
  * Sortierschluessel ist die id, NICHT created_at: uid() ist
    Date.now().toString(36)+Zufall, also zeitsortierend, und identisch vor
    und nach dem Sync. createdAt ist lokal td2() = "YYYY-MM-DD" (nur Datum),
    auf dem Server ein voller Zeitstempel - eine Sortierung danach waere vor
    dem Sync eine andere als danach.
  * Der PDF uebernimmt die Bildschirmnummer, statt eine zweite zu erfinden.
"""
import re


# ── Helfer ────────────────────────────────────────────────────────────────────

def _zeile(index_html, marker):
    """Die (einzige) Zeile, die marker enthaelt - ohne die Changelog-Zeile."""
    treffer = [ln for ln in index_html.replace("\r\n", "\n").split("\n")
               if marker in ln and "const APP_VERSION=" not in ln]
    assert treffer, "Anker verschwunden: " + marker
    assert len(treffer) == 1, (
        "Anker nicht mehr eindeutig (%d Treffer): %s" % (len(treffer), marker)
    )
    return treffer[0]


def _ticketnr_memo(index_html):
    m = re.search(r"const _ticketNr=_react\.useMemo\.call\(void 0, .*", index_html)
    assert m, "_ticketNr ist weg - dann zeigt der Pin gar keine Nummer mehr."
    return m.group(0)


# ── (1) Reihenfolge an der Quelle ─────────────────────────────────────────────

def test_tickets_werden_sortiert_geladen(index_html):
    """Ohne order= entscheidet die Heap-Reihenfolge, und die aendert ein PATCH."""
    zeile = _zeile(index_html, "getTickets: function(pid)")
    assert "order=id.asc" in zeile, (
        "API.getTickets laedt weiter OHNE order=. PostgREST gibt dann die "
        "physische Heap-Reihenfolge zurueck; jede Statusaenderung (PATCH) "
        "schreibt eine neue Tupelversion und verschiebt die Zeile - die "
        "Pin-Nummer wandert beim naechsten Laden:\n" + zeile
    )


def test_beide_zweige_von_getTickets_sortieren(index_html):
    """getTickets hat zwei Zweige (mit/ohne pid). Der Boot-Load ruft den OHNE
    pid auf - genau der darf nicht vergessen werden."""
    # v3.9.913 - DIE ZAHL IST WEG. Vorher: `zeile.count("order=id.asc") >= 1`.
    # `>= 1` ist woertlich dasselbe wie `"order=id.asc" in zeile` - und genau
    # das steht schon im Test darueber. Eine Zahl, die nichts einschraenkt, ist
    # keine Zusicherung, sondern Buchhaltung: sie sah nach Messung aus und mass
    # nichts. Die eigentliche Aussage dieses Riegels ("auch der pid-LOSE Zweig
    # sortiert") steht in den benannten Zeilen darunter und bleibt.
    zeile = _zeile(index_html, "getTickets: function(pid)")
    ohne_pid = re.search(r":_sbGet\(\"tickets\"([^)]*)\)", zeile)
    assert ohne_pid, "Der pid-lose Zweig von getTickets ist nicht mehr auffindbar:\n" + zeile
    assert "order" in ohne_pid.group(1), (
        "Der pid-lose Zweig laedt unsortiert - und genau den ruft der "
        "Boot-Load auf (API.getTickets() ohne Argument):\n" + zeile
    )


def test_defects_werden_sortiert_geladen(index_html):
    """_defectPins erben ihre Nummer aus der Reihenfolge von forms.maengel,
    und die kommt aus getDefects."""
    zeile = _zeile(index_html, "getDefects: function()")
    assert "order=" in zeile, (
        "getDefects laedt unsortiert - die Nummern der Maengel-Pins "
        "(T+1..N) wandern damit genauso:\n" + zeile
    )


def test_sortierschluessel_ist_die_id_nicht_created_at(index_html):
    """created_at waere die naheliegende Wahl und die falsche: lokal steht in
    createdAt td2() = nur das Datum, auf dem Server ein voller Zeitstempel.
    Ein frisch angelegtes Ticket sortierte vor dem Sync anders als danach -
    die Nummer waere genau in dem Moment instabil, in dem sie vergeben wird."""
    zeile = _zeile(index_html, "getTickets: function(pid)")
    assert "created_at.asc" not in zeile, (
        "Sortiert nach created_at. Lokal ist createdAt datumsgenau (td2()), "
        "auf dem Server zeitstempelgenau - die Client-Sortierung kann diese "
        "Reihenfolge vor dem Sync nicht reproduzieren:\n" + zeile
    )


# ── (2) Nummernbasis rollenunabhaengig ────────────────────────────────────────

def test_nummer_kommt_nicht_mehr_aus_der_rollengefilterten_liste(index_html):
    """planTickets stammt aus allTickets, und allTickets ist fuer Monteur/
    Helfer/Techniker/Obermonteur auf assignee===eigene-id gefiltert."""
    memo = _ticketnr_memo(index_html)
    assert "planTickets.forEach((t,i)=>{m[t.id]=i+1;});" not in memo, (
        "Die Pin-Nummer wird weiter aus planTickets vergeben. planTickets "
        "erbt den Rollenfilter aus allTickets - der Monteur zaehlt 1..k ueber "
        "seine eigenen Tickets, das gedruckte PDF 1..N ueber alle. Dieselbe "
        "'14' meint zwei verschiedene Pins:\n" + memo[:400]
    )


def test_es_gibt_eine_eigene_rollenunabhaengige_nummernbasis(index_html):
    assert "const _nrBase=" in index_html, (
        "Es gibt keine eigene Nummernbasis. Die Nummer haengt dann weiter an "
        "der Menge, die der jeweilige Benutzer sehen darf."
    )
    basis = _zeile(index_html, "const _nrBase=")
    assert "allTickets" not in basis, (
        "Die Nummernbasis greift wieder auf allTickets zu - damit ist der "
        "Rollenfilter zurueck:\n" + basis
    )
    assert "planData" in basis, (
        "Die Nummernbasis liest nicht aus planData.tickets (der ungefilterten "
        "Quelle):\n" + basis
    )


def test_nummernbasis_ist_deterministisch_sortiert(index_html):
    """Der Client sortiert selbst. Sonst haengt die Nummer an der Liefer-
    Reihenfolge der REST-Antwort - und ein noch nicht synchronisiertes Ticket
    (das lokal ans Ende gehaengt wird) bekaeme nach dem Reload eine andere."""
    basis = _zeile(index_html, "const _nrBase=")
    assert ".sort(" in basis, (
        "Die Nummernbasis wird nicht sortiert:\n" + basis
    )
    assert "a.id" in basis and "b.id" in basis, (
        "Sortiert nicht nach id - dann stimmt die Client-Reihenfolge nicht "
        "mit order=id.asc auf dem Server ueberein:\n" + basis
    )
    assert "created_at" not in basis and "createdAt" not in basis, (
        "Sortiert (auch) nach created_at - lokal datumsgenau, auf dem Server "
        "zeitstempelgenau, also vor und nach dem Sync verschieden:\n" + basis
    )


def test_nummernbasis_kopiert_vor_dem_sortieren(index_html):
    """.sort() sortiert in-place. Ohne Kopie wuerde der React-State
    (planData.tickets) mutiert - React sieht dieselbe Array-Referenz, rendert
    nicht neu, und die alte Reihenfolge ist trotzdem weg."""
    basis = _zeile(index_html, "const _nrBase=")
    assert ".slice().sort(" in basis or "].sort(" in basis, (
        "Es wird ohne Kopie sortiert - .sort() arbeitet in-place und wuerde "
        "planData.tickets (React-State) selbst umstellen:\n" + basis
    )


def test_defectpin_dedup_ist_rollenunabhaengig(index_html):
    """Die Doppel-Pin-Sperre der Maengel baut ihr Set aus allTickets. Fuer den
    Monteur enthaelt das nur SEINE Tickets - fremde Mangel-Ticket-Spiegel
    kommen bei ihm als zusaetzliche Defect-Pins durch und verschieben die
    Nummern T+1..N gegenueber dem PDF."""
    assert "const _ids=new Set((allTickets||[]).map(t=>t.id));" not in index_html, (
        "Die De-Duplizierung der Defect-Pins filtert weiter gegen die "
        "rollengefilterte allTickets-Liste."
    )


# ── (3) Bildschirm und PDF zaehlen ueber dieselbe Menge ───────────────────────

def test_pdf_uebernimmt_die_bildschirmnummer(index_html):
    """Sonst zaehlt der PDF ueber die positionierten Pins neu - und jedes
    Ticket ohne Position (dafuer gibt es einen eigenen Warn-Toast) verschiebt
    alle folgenden Nummern um eins gegen den Bildschirm."""
    sig = _zeile(index_html, "async function _genPlanReportPdf(")
    assert re.search(r"async function _genPlanReportPdf\([^)]*nrMap", sig), (
        "_genPlanReportPdf nimmt die Bildschirm-Nummernkarte nicht entgegen "
        "und erfindet weiter eine eigene:\n" + sig
    )
    assert "nrMap[t.id]" in index_html, (
        "Die uebergebene Nummernkarte wird im PDF nicht ausgewertet."
    )


def test_pdf_aufruf_reicht_die_nummernkarte_durch(index_html):
    aufruf = _zeile(index_html, "_genPlanReportPdf(selPlan,")
    assert "_ticketNr" in aufruf, (
        "Die Aufrufstelle uebergibt _ticketNr nicht - der PDF bekommt die "
        "Bildschirmnummer nie zu sehen:\n" + aufruf
    )


def test_v850_zusage_bleibt_bestehen(index_html):
    """v3.9.850 hat die Defect-Pins in die Nummerierung einsortiert (vorher
    fielen sie auf den gefilterten Loop-Index zurueck). Das darf beim Umbau
    nicht wieder herausfallen."""
    memo = _ticketnr_memo(index_html)
    assert "_defectPins.forEach(" in memo, (
        "Die Defect-Pins werden nicht mehr mitnummeriert - dann faellt der "
        "Pin im Viewer auf den gefilterten Loop-Index zurueck (Regression "
        "auf den Stand vor v3.9.850):\n" + memo[:400]
    )
    assert "_defectPins]" in memo or "_defectPins," in memo, (
        "_defectPins fehlt in der useMemo-Abhaengigkeitsliste - stale Nummern."
    )


def test_viewer_und_liste_lesen_dieselbe_karte(index_html):
    """Drei Lesestellen, eine Quelle: Canvas-Export, Ticket-Liste, Sidebar."""
    assert "pinNr: _ticketNr" in index_html, "Der Viewer bekommt _ticketNr nicht mehr."
    assert "nr: _ticketNr[t.id]" in index_html, "Die Ticket-Liste liest nicht mehr aus _ticketNr."


# ── Umkehrprobe ───────────────────────────────────────────────────────────────

# Der Stand vom 28.08.2026 (v3.9.875), wortgetreu - das ist der Zustand, den
# die Riegel oben als FEHLER erkennen muessen.
_STAND_v875 = (
    '    getTickets: function(pid) { return pid?_sbGet("tickets","project_id=eq."'
    '+encodeURIComponent(pid)):_sbGet("tickets"); },\n'
    '    getDefects: function() { return _sbGet("defects"); },\n'
    '  const _ticketNr=_react.useMemo.call(void 0, ()=>{const m={};'
    'planTickets.forEach((t,i)=>{m[t.id]=i+1;});'
    '_defectPins.forEach((d,i)=>{if(m[d.id]==null)m[d.id]=planTickets.length+i+1;});'
    'return m;},[planTickets,_defectPins]);\n'
    '    const _ids=new Set((allTickets||[]).map(t=>t.id));\n'
    'async function _genPlanReportPdf(plan,pins,monteure,layers,proj){\n'
    '    const _nrById={};_pins.forEach((t,i)=>{_nrById[t.id]=i+1;});\n'
    '_genPlanReportPdf(selPlan,planTickets.concat(_defectPins),monteure,layers,p);\n'
    '        pinNr: _ticketNr,\n'
    '        nr: _ticketNr[t.id],\n'
)


def test_umkehrprobe_riegel_schlagen_am_alten_stand_an(index_html):
    """Ein Riegel, der auch am kaputten Code gruen bliebe, ist kein Riegel,
    sondern ein Messgeraet ohne Zeiger. Hier laufen dieselben Pruefungen gegen
    den woertlichen v3.9.875-Stand - JEDE muss anschlagen."""
    muessen_scheitern = [
        test_tickets_werden_sortiert_geladen,
        test_beide_zweige_von_getTickets_sortieren,
        test_defects_werden_sortiert_geladen,
        test_nummer_kommt_nicht_mehr_aus_der_rollengefilterten_liste,
        test_es_gibt_eine_eigene_rollenunabhaengige_nummernbasis,
        test_defectpin_dedup_ist_rollenunabhaengig,
        test_pdf_uebernimmt_die_bildschirmnummer,
    ]
    stumm = []
    for fn in muessen_scheitern:
        try:
            fn(_STAND_v875)
        except AssertionError:
            continue
        except Exception as e:          # Anker gar nicht gefunden = auch kein Beweis
            stumm.append(fn.__name__ + " (" + type(e).__name__ + ")")
            continue
        stumm.append(fn.__name__ + " (blieb GRUEN)")
    assert not stumm, (
        "Diese Riegel wuerden den Fehlerstand v3.9.875 NICHT bemerken - sie "
        "messen nichts:\n  " + "\n  ".join(stumm)
    )


def test_umkehrprobe_die_beibehaltungs_riegel_bleiben_gruen(index_html):
    """Gegenprobe zur Gegenprobe: die beiden Riegel, die BESTEHENDES sichern
    (v850-Defect-Pins, die drei Lesestellen), muessen am alten Stand gruen
    sein - sonst pruefen sie in Wahrheit den Umbau mit."""
    test_v850_zusage_bleibt_bestehen(_STAND_v875)
    test_viewer_und_liste_lesen_dieselbe_karte(_STAND_v875)
