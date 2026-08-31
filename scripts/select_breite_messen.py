# -*- coding: utf-8 -*-
"""Reichweite: dieselbe Frage, aber an den Feldern, die kein Reiter-Klick erreicht.

WORAUS DAS ENTSTAND (v3.9.925)
------------------------------
scripts/select_wert_messen.py misst die Invariante

    DER GEWAEHLTE WERT MUSS UNTER DEN ANGEBOTENEN OPTIONEN SEIN

und hat damit vier echte Fehler gefunden. Sein Bericht sagt aber selbst, wo
seine Grenze liegt: von 118 Auswahlfeldern in index.html hat sein Lauf 25
Fundorte GERENDERT. Fuer die uebrigen 93 heisst "keine Funde" ausdruecklich
NICHT "geprueft" - sie stecken in Modalen und Detailformularen, die ein
Reiter-Klick gar nicht erreicht.

Dieses Werkzeug erhoeht die Reichweite. Es benutzt dieselbe Huelle und
dieselbe Gegenprobe (importiert, nicht abgeschrieben - eine zweite Kopie waere
die naechste Stelle, die auseinanderlaeuft), aber es geht drei Wege weiter:

  1) ES BETRITT DIE PROJEKTMASKE. Die Projektliste ist ein Reiter; alles
     dahinter - Dashboard, Zeiterfassung, Berichte, Plaene, Formulare,
     Checklisten, Maengel, Bautagebuch, Fotos, Material, Dokumente, OFFA -
     haengt an einem Klick auf eine PROJEKTKARTE. Die Karte ist ein div mit
     cursor:pointer, kein button; die Positivliste des Vorlaeufers konnte sie
     gar nicht sehen.

  2) ES BEANTWORTET DIE SERVERFRAGEN. Dokumente und Ordner werden NUR vom
     Server geladen - ODB.load("docs_"+pid) laeuft ins Leere, weil "docs_p4"
     kein Store in STORES ist. Ohne Antwort auf project_documents bleibt die
     Dokumentenliste leer und das Ordner-Auswahlfeld wird nie gerendert.
     Geantwortet wird ueber playwright-route, nicht durch einen Eingriff in
     index.html.

  3) ES LAEUFT ZWEIMAL, MIT VERSCHIEDENEN ROLLEN. Ein Teil der Felder haengt
     an der Rolle: VZeit rechnet fuer admin/projektleiter mit ALLEN Monteuren
     und fuer alle anderen nur mit den dem Projekt ZUGEWIESENEN. Ein Lauf nur
     als Administrator misst die Haelfte der App - und zwar genau die Haelfte
     OHNE die Einschraenkung, aus der die Fehler entstehen.

WAS GESAET WIRD (und warum genau das)
-------------------------------------
Wie beim Vorlaeufer absichtlich VERALTETE bzw. FREMDE Verweise, weil ein
Bestand, in dem jeder Verweis auf ein lebendes Ziel zeigt, die Frage gar nicht
beantworten kann:

  * ein Ticket mit einem GEWERK-FREITEXT ("Elektro komplett" - genau die
    Schreibweise, die in projects.gewerk steht)
  * ein Ticket mit gewerk "maengel" - das schreibt die App SELBST, wenn beim
    Anlegen keine Ebene mitkommt (index.html, Suchbegriff
    'gewerk:ticket.gewerk||ticket.layer||"maengel"'), und "maengel" ist keine
    Ebenen-Kennung
  * ein Ticket mit unbekanntem Typ und unbekanntem Status
  * ein Dokument in einem GELOESCHTEN Ordner
  * ein Zeiteintrag auf einem Monteur, der dem Projekt NICHT zugewiesen ist
  * ein Feldbenutzer, der dem Projekt NICHT zugewiesen ist

BENUTZUNG
---------
    python scripts/select_breite_messen.py
    python scripts/select_breite_messen.py --zeigen     # Knopfnamen mitloggen
"""
import json
import os
import sys
import threading

for _strom in (sys.stdout, sys.stderr):
    try:
        _strom.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
sys.path.insert(0, HIER)

from tab_sweep import DB_NAME, SEED_JS  # noqa: E402
from select_wert_messen import (  # noqa: E402
    GEGENPROBE_JS, HUELLE_JS, KLICK_TAB_JS, OEFFNEN_JS, SCHLIESSEN_JS,
    SUBTABS_JS, TABS_JS,
)

# ═══ SITZUNG ══════════════════════════════════════════════════════════════
# Wie tab_sweep.INIT, aber die Rolle ist einstellbar. Ohne das misst der Lauf
# nur die Administrator-Haelfte der App.
INIT_VORLAGE = """
try{
  var b=function(s){return btoa(s).replace(/=+$/,'');};
  var jwt=b(JSON.stringify({alg:"HS256",typ:"JWT"}))+"."+
          b(JSON.stringify({sub:"1",role:"authenticated",
                            exp:Math.floor(Date.now()/1000)+86400}))+".sig";
  localStorage.setItem('epkolar_auth',JSON.stringify({at:jwt,rt:"r",exp:Date.now()+86400000}));
  localStorage.setItem('epkolar_user',JSON.stringify(__NUTZER__));
}catch(e){}
"""


def _init(nutzer):
    return INIT_VORLAGE.replace("__NUTZER__", json.dumps(nutzer))


ROLLEN = [
    ("admin", {"id": "1", "username": "admin", "name": "Sweep Admin",
               "role": "admin", "rolle": "Geschaeftsfuehrer",
               "monteurId": "", "permissions": [], "perms_override": {}}),
    # Das BUERO ist die entscheidende dritte Rolle, und zwar aus einem Grund,
    # der sich erst beim Messen gezeigt hat: VZeit rechnet nur fuer
    # admin/projektleiter mit ALLEN Monteuren, fuer alle anderen mit den dem
    # Projekt ZUGEWIESENEN. Der Feldbenutzer kommt an diese Grenze NICHT heran
    # (ProjList zeigt ihm ohnehin nur seine eigenen Projekte, er steht also
    # immer in der Zuweisung) - das Buero schon: es sieht jedes Projekt und
    # bekommt trotzdem nur die zugewiesenen Monteure zur Auswahl.
    ("buero", {"id": "5", "username": "buero", "name": "Sweep Buero",
               "role": "buero", "rolle": "Backoffice",
               "monteurId": "", "permissions": [], "perms_override": {}}),
    # Der Feldbenutzer laeuft trotzdem mit - ohne ihn waere nicht belegt, dass
    # die Read-Only-Pfade (Dokumente, Ticket-Zuweisung) dieselbe Frage
    # bestehen.
    ("monteur", {"id": "9", "username": "anton", "name": "Aktiv Anton",
                 "role": "monteur", "rolle": "Monteur",
                 "monteurId": "M1", "permissions": [], "perms_override": {}}),
]

# ═══ SERVERANTWORTEN ══════════════════════════════════════════════════════
# Nur zwei Tabellen tragen Inhalt; alles andere wird mit einer LEEREN Liste
# beantwortet. Das ist Absicht: eine leere Antwort laesst jede Uebernahme-
# Bedingung der App (`if(x&&x.length)`) falsch werden, die Saat aus der
# IndexedDB bleibt also stehen. Ein 401 waere das Gegenteil - dann liefe
# zusaetzlich _onAuthFail, und ein abgemeldeter Lauf misst nichts.
PID = "p4"          # DR.-GSCHMEIDLERSTRASSE 10, gewerk "Elektro komplett"
DOK_ROWS = [
    # Der Fall: der Ordner F_WEG existiert nicht mehr.
    {"id": "d1", "name": "Bauplan EG", "category": "plaene",
     "folder_id": "F_WEG", "note": "", "file_url": "", "file_name": "eg.pdf",
     "file_type": "application/pdf", "file_size": 1234,
     "uploaded_at": "2026-01-02T00:00:00", "kunde_freigabe": 0},
    # Und einer, dessen Ordner es gibt - sonst waere nicht belegt, dass das
    # Feld ueberhaupt einen Treffer haben KANN.
    {"id": "d2", "name": "Protokoll", "category": "baubesprechung",
     "folder_id": "f1", "note": "", "file_url": "", "file_name": "prot.pdf",
     "file_type": "application/pdf", "file_size": 2345,
     "uploaded_at": "2026-01-03T00:00:00", "kunde_freigabe": 0},
]
ORDNER_ROWS = [
    {"id": "f1", "name": "Fotos", "color": "#888888", "parent_id": "",
     "created_at": "2026-01-01T00:00:00"},
]


def _route(auftrag):
    u = auftrag.request.url
    koerper = "[]"
    if "project_documents" in u:
        koerper = json.dumps(DOK_ROWS)
    elif "project_folders" in u:
        koerper = json.dumps(ORDNER_ROWS)
    try:
        auftrag.fulfill(status=200, content_type="application/json",
                        body=koerper)
    except Exception:
        pass


# ═══ SAAT ═════════════════════════════════════════════════════════════════
def _saat(mid):
    import datetime
    heute = datetime.date.today()
    frueher = (heute - datetime.timedelta(days=90)).isoformat()
    montag = heute + datetime.timedelta(days=(7 - heute.weekday()))
    tage = [(montag + datetime.timedelta(days=k)).isoformat() for k in range(5)]
    # Zeiteintraege muessen in der ANGEZEIGTEN Woche liegen. Der erste Lauf
    # sass daneben: die Scheine brauchen kuenftige Termine (fixMap nimmt nur
    # ab heute), der Wochenkalender der Zeiterfassung startet aber in der
    # LAUFENDEN Woche - die Eintraege waren gesaet, die Tageskacheln leer,
    # und der Bearbeiten-Stift, hinter dem das Feld sitzt, existierte nicht.
    dmontag = heute - datetime.timedelta(days=heute.weekday())
    dtage = [(dmontag + datetime.timedelta(days=k)).isoformat() for k in range(5)]

    monteure = [
        {"id": "M1", "n": "Aktiv Anton", "r": "Monteur", "austritt": "", "fs": "B,C"},
        {"id": "M2", "n": "Aktiv Berta", "r": "Obermonteur", "austritt": "", "fs": "B"},
        {"id": "M9", "n": "Ehemalig Egon", "r": "Monteur", "austritt": frueher, "fs": "B,C"},
    ]
    # M9 ist dem Projekt NICHT zugewiesen. Damit ist assignedWorkers nicht
    # leer (VZeit faellt dann NICHT auf "alle Monteure" zurueck) und der
    # Feldbenutzer steht trotzdem nicht drin - genau der gefragte Fall.
    monteur_projekte = {"M1": [PID, "p1"], "M2": [PID]}

    scheine = []
    for k, t in enumerate(tage, start=1):
        scheine.append({
            "id": "S%d" % k, "nummer": "AS-%d" % (1000 + k),
            "kundName": "Kunde %d" % k, "arbeitsort": "Krems", "plz": "3500",
            "monteur": ["M1", "M2", "M9", "M_GELOESCHT", "M1"][k - 1],
            "terminBestaetigt": t, "terminZeit": "08:30",
            "scheinstatus": "freigegeben" if k != 4 else None,
            "sachbearbeiter": "" if k % 2 else "Gibt Es Nicht",
            "projekt": PID, "dauer": "2h",
        })

    plaene = [{
        "id": "PL1", "pid": PID, "project_id": PID, "name": "Grundriss EG",
        "filename": "eg.png", "geschoss": "Erdgeschoss",
        "dataUrl": ("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAAB"
                    "CAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5"
                    "ErkJggg=="),
        "width": 1, "height": 1, "page_count": 1, "version": 1,
        "uploadedAt": "2026-01-01",
    }]
    gemeinsam = {"pid": PID, "planId": "PL1", "plan_id": "PL1", "page": 1,
                 "x": 40, "y": 40, "photos": [], "comments": [],
                 "createdAt": "2026-01-02", "progress": 0, "dueDate": ""}
    tickets = [
        # 1) GEWERK-FREITEXT. Genau die Schreibweise aus projects.gewerk.
        dict(gemeinsam, id="T1", title="Freitext-Gewerk", description="",
             status="offen", priority="mittel", type="mangel",
             assignee=mid or "M1", layer="", gewerk="Elektro komplett"),
        # 2) "maengel" - schreibt die App selbst beim Anlegen ohne Ebene,
        #    ist aber keine Ebenen-Kennung.
        dict(gemeinsam, id="T2", title="Ohne Ebene", description="",
             status="offen", priority="hoch", type="mangel",
             assignee=mid or "M1", layer="", gewerk="maengel"),
        # 3) Der saubere Fall - ohne ihn waere nicht belegt, dass das Feld
        #    ueberhaupt treffen KANN.
        dict(gemeinsam, id="T3", title="Saubere Ebene", description="",
             status="offen", priority="niedrig", type="info",
             assignee=mid or "M1", layer="l3", gewerk="l3"),
        # 4) Unbekannter Typ, unbekannter Status, Prioritaet "normal" -
        #    dieselbe Frage an den Nachbarfeldern desselben Formulars.
        #    "normal" ist nicht erfunden: die Notiz von v3.9.362 in
        #    TicketDetail nennt genau diesen Wert als das, was Alt-POSTs
        #    hinterlassen haben.
        dict(gemeinsam, id="T4", title="Fremder Typ und Status",
             description="", status="wartet_auf_kunde", priority="normal",
             type="", assignee=mid or "M1", layer="l1", gewerk="l1"),
    ]

    eintraege = []
    for k, t in enumerate(dtage[:3], start=1):
        w = ["M1", "M9", "M2"][k - 1]
        eintraege.append({
            # E2 haengt an einem Monteur, der dem Projekt NICHT zugewiesen
            # ist - das ist der Fall fuer den Bearbeiten-Weg in VZeit.
            "id": "E%d" % k, "pid": PID, "p": PID, "worker": w, "w": w,
            "datum": t, "date": t, "von": "07:00", "bis": "16:00",
            "pause": 1, "stunden": 8, "hours": 8, "gw": "elektro",
            "taetigkeit": "Montage", "bemerkung": "",
        })

    fahrzeuge = [{"id": "F1", "kennzeichen": "KR-1", "marke": "VW",
                  "typ": "Bus", "fahrer": "M9", "vignette_typ": ""}]
    werkzeuge = [
        {"id": "W1", "inventarnr": "WZ-1", "name": "Bohrer", "kat": "elektro",
         "status": "verfuegbar", "zugewiesen": "M9", "projekt": "p7"},
        {"id": "W2", "inventarnr": "WZ-2", "name": "Messgeraet", "kat": "mess",
         "status": "verfuegbar", "zugewiesen": "M1", "projekt": "P_WEG"},
    ]
    formulare = {
        "maengel": [{"id": "MG1", "pid": PID, "name": "Riss in der Wand",
                     "ebene": "Erdgeschoss", "worker": "M9", "prio": "hoch",
                     "status": "offen", "frist": tage[0], "date": tage[0],
                     "planId": "PL1", "plan_id": "PL1", "page": 1,
                     "x": 60, "y": 60}],
        "bautagebuch": [{"id": "BT1", "pid": PID, "date": tage[0],
                         "wetter": "sonnig", "temp": 20, "text": "Aufbau",
                         "worker": "M9"}],
    }
    return {"monteure": monteure, "arbeitsscheine": scheine,
            "fahrzeuge": fahrzeuge, "werkzeuge": werkzeuge,
            "monteurProjekte": monteur_projekte, "entries": eintraege,
            "forms": formulare,
            "planData": {"plans": plaene, "tickets": tickets}}


# ═══ NAVIGATION ═══════════════════════════════════════════════════════════
# Die Projektkarte ist ein div mit cursor:pointer, kein button - deshalb
# findet sie keine Knopf-Positivliste. Geklickt wird das INNERSTE Element mit
# cursor:pointer, das die Projektnummer traegt.
KARTE_JS = r"""(nr) => {
  const els=[...document.querySelectorAll('div')]
    .filter(d=>(d.textContent||'').indexOf(nr)>=0);
  for(let i=els.length-1;i>=0;i--){
    const e=els[i];
    if(e.style&&e.style.cursor==='pointer'){e.click();return true;}
  }
  return false;
}"""

# Die Projektnummern der sichtbaren Karten.
PROJ_NRN_JS = r"""() => {
  const raus=[];
  const rx=/PA\d{6}/g;
  const txt=document.body.innerText||'';
  let m;
  while((m=rx.exec(txt))){ if(raus.indexOf(m[0])<0) raus.push(m[0]); }
  return raus;
}"""

# Die Untermaske eines Projekts. Ihre Knoepfe stehen NICHT in .tab-bar -
# daran werden sie von der Hauptleiste unterschieden.
PROJ_NAV_JS = r"""() => {
  const t=e=>(e.textContent||'').trim().replace(/\s+/g,' ');
  const ZIEL=["Dashboard","Zeiterfassung","Berichte","Pläne","Formulare",
              "Checklisten","Mängel","Bautagebuch","Fotos","Material",
              "Dokumente","OFFA"];
  const raus=[];
  for(const b of document.querySelectorAll('button')){
    if(b.closest('.tab-bar'))continue;
    const s=t(b);
    if(s.length<5)continue;
    if(ZIEL.some(z=>s.indexOf(z)>=0)&&raus.indexOf(s)<0)raus.push(s);
  }
  return raus;
}"""

KLICK_PROJ_NAV_JS = r"""(name) => {
  const t=e=>(e.textContent||'').trim().replace(/\s+/g,' ');
  for(const b of document.querySelectorAll('button')){
    if(b.closest('.tab-bar'))continue;
    if(t(b)===name){ b.click(); return true; }
  }
  return false;
}"""

ZURUECK_JS = r"""() => {
  const t=e=>(e.textContent||'').trim().replace(/\s+/g,' ');
  for(const b of document.querySelectorAll('button')){
    if(t(b).indexOf('Zurück')>=0){ b.click(); return true; }
  }
  return false;
}"""

# Die Unteransichten der Plan-Maske sind KEINE .tab-bar - SUBTABS_JS sieht
# sie nicht. Ohne diesen Klick bleibt die Ticket-Liste zu, und ohne die Liste
# ist das Ebenen-Feld unerreichbar.
PLAN_ANSICHT_JS = r"""(name) => {
  const t=e=>(e.textContent||'').trim().replace(/\s+/g,' ');
  for(const b of document.querySelectorAll('button')){
    if(b.closest('.tab-bar'))continue;
    if(t(b).indexOf(name)>=0){ b.click(); return true; }
  }
  return false;
}"""

# In der Plan-Maske: eine Ticketzeile anklicken, danach "Bearbeiten". Erst
# dahinter steht das Ebenen-Feld (es haengt an `editing`).
#
# ERSTER VERSUCH, UND ER MASS NICHTS: gefiltert wurde auf `e.onclick`. React 18
# haengt seine Handler EINMAL an die Wurzel und delegiert - die
# onclick-Eigenschaft der Zeile ist null. Der Filter lieferte also immer eine
# leere Liste, der Lauf meldete brav "fertig", und die Plan-Maske blieb
# ungemessen, ohne dass irgendwo etwas rot geworden waere. Geklickt wird
# stattdessen die Zeile selbst; der Klick blubbert bis zur Wurzel und loest
# den React-Handler aus.
TICKET_OEFFNEN_JS = r"""(nr) => {
  const t=e=>(e.textContent||'').trim().replace(/\s+/g,' ');
  const RX=/Freitext-Gewerk|Ohne Ebene|Saubere Ebene|Fremder Typ/;
  let zeilen=[...document.querySelectorAll('tr')].filter(e=>RX.test(t(e)));
  if(!zeilen.length){
    zeilen=[...document.querySelectorAll('div')]
      .filter(e=>RX.test(t(e))&&e.style&&e.style.cursor==='pointer');
  }
  const e=zeilen[nr];
  if(!e) return {fertig:true, anzahl:zeilen.length};
  try{ e.click(); }catch(x){}
  return {fertig:false, anzahl:zeilen.length, text:t(e).slice(0,40)};
}"""

# Der Bearbeiten-Knopf des Ticket-Fensters traegt nur "✏️" als Text - erkannt
# wird er deshalb an seiner aria-Beschriftung, nicht am Text (mehrere andere
# Knoepfe tragen dasselbe Zeichen).
BEARBEITEN_JS = r"""() => {
  const k=[...document.querySelectorAll('button[aria-label="Bearbeiten"]')]
    .filter(b=>!b.disabled);
  if(!k.length) return 0;
  try{ k[0].click(); }catch(e){}
  return k.length;
}"""

# In der Projekt-Zeiterfassung: das Eintrags-Modal oeffnen. Der Tagesknopf
# heisst "+ Eintrag" - die geerbte Positivliste aus select_wert_messen.py
# trifft ihn NICHT, weil ihr `^(\+|...)\b` zwischen "+" und dem Leerzeichen
# keine Wortgrenze findet. Das ist der Grund, warum das Modal im ersten Lauf
# nie aufging.
ZEIT_MODAL_JS = r"""(runde) => {
  const t=e=>(e.textContent||'').trim().replace(/\s+/g,' ');
  const k=[...document.querySelectorAll('button,[role=button]')]
    .filter(b=>!b.disabled&&/^(\+|＋)/.test(t(b)));
  const b=k[runde];
  if(!b) return {fertig:true, anzahl:k.length};
  try{ b.click(); }catch(e){}
  return {fertig:false, anzahl:k.length};
}"""

# Und der Bearbeiten-Stift eines BESTEHENDEN Zeiteintrags. Er ist der Weg, auf
# dem addWorker den Wert eines gespeicherten Datensatzes bekommt - genau der
# Fall, den ein frisch geoeffnetes Modal nie erzeugt.
ZEIT_STIFT_JS = r"""(runde) => {
  const k=[...document.querySelectorAll('[aria-label="Eintrag bearbeiten"]')];
  const b=k[runde];
  if(!b) return {fertig:true, anzahl:k.length};
  try{ b.click(); }catch(e){}
  return {fertig:false, anzahl:k.length};
}"""

STELLEN_JS = "() => Object.keys(window.__selOrte||{}).length"


def _server():
    import http.server
    import socketserver
    os.chdir(WURZEL)

    class Still(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass

    srv = socketserver.TCPServer(("127.0.0.1", 0), Still)
    srv.daemon_threads = True
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv.server_address[1]


def _modale_runden(seite, wieviel=10):
    for runde in range(wieviel):
        r = seite.evaluate(OEFFNEN_JS, runde)
        if r.get("fertig"):
            break
        seite.wait_for_timeout(400)
        seite.evaluate(SCHLIESSEN_JS)
        seite.wait_for_timeout(200)


def _projekt_durchgehen(seite, zeigen):
    """Eine Projektmaske vollstaendig: jede Untermaske, jedes Modal."""
    nav = seite.evaluate(PROJ_NAV_JS)
    if zeigen:
        print("      Untermasken:", " | ".join(nav))
    for name in nav:
        if not seite.evaluate(KLICK_PROJ_NAV_JS, name):
            continue
        seite.wait_for_timeout(800)
        seite.evaluate(SUBTABS_JS)
        seite.wait_for_timeout(600)
        if "Pläne" in name:
            for ansicht in ("Alle Tickets", "Ebenen", "Planverwaltung",
                            "Plan-Viewer"):
                seite.evaluate(PLAN_ANSICHT_JS, ansicht)
                seite.wait_for_timeout(700)
                if ansicht != "Alle Tickets":
                    continue
                for nr in range(4):
                    r = seite.evaluate(TICKET_OEFFNEN_JS, nr)
                    if r.get("fertig"):
                        break
                    seite.wait_for_timeout(700)
                    seite.evaluate(BEARBEITEN_JS)
                    seite.wait_for_timeout(700)
                    seite.evaluate(PLAN_ANSICHT_JS, "Alle Tickets")
                    seite.wait_for_timeout(500)
        if "Zeiterfassung" in name:
            for runde in range(8):
                r = seite.evaluate(ZEIT_MODAL_JS, runde)
                if r.get("fertig"):
                    break
                seite.wait_for_timeout(500)
                seite.evaluate(SCHLIESSEN_JS)
                seite.wait_for_timeout(250)
            for runde in range(6):
                r = seite.evaluate(ZEIT_STIFT_JS, runde)
                if r.get("fertig"):
                    break
                seite.wait_for_timeout(500)
                seite.evaluate(SCHLIESSEN_JS)
                seite.wait_for_timeout(250)
        _modale_runden(seite, 8)


def _lauf(pw, url, rolle, nutzer, zeigen):
    b = pw.chromium.launch()
    c = b.new_context(viewport={"width": 1600, "height": 1000})
    c.add_init_script(_init(nutzer))
    c.route("**/rest/v1/**", _route)
    p = c.new_page()
    p.goto(url, wait_until="domcontentloaded")
    p.wait_for_timeout(5000)

    erg = p.evaluate(SEED_JS,
                     {"db": DB_NAME, "daten": _saat(nutzer.get("monteurId"))})
    print("  Saat:", erg.get("gelesen"), "fehlend:", erg.get("fehlend"))
    if erg.get("fehlend"):
        print("  ABBRUCH: Speicher fehlen -", erg["fehlend"])
        b.close()
        return None

    p.reload(wait_until="domcontentloaded")
    p.wait_for_timeout(5000)

    if p.evaluate(HUELLE_JS) not in ("gesetzt", "schon da"):
        print("  ABBRUCH: Huelle nicht gesetzt")
        b.close()
        return None
    gp = p.evaluate(GEGENPROBE_JS)
    if gp.get("zuwachs") != 1 or gp.get("wert") != "GIBT-ES-NICHT":
        print("  ABBRUCH: die Huelle sieht den gebauten Fehler NICHT:", gp)
        b.close()
        return None
    p.evaluate("() => { window.__selFunde = []; }")

    tabs = p.evaluate(TABS_JS)
    if not tabs:
        print("  ABBRUCH: keine Reiterleiste - laedt die App?")
        b.close()
        return None
    print("  Ansichten:", len(tabs))

    for i, name in enumerate(tabs):
        p.evaluate(KLICK_TAB_JS, i)
        p.wait_for_timeout(800)
        p.evaluate(SUBTABS_JS)
        p.wait_for_timeout(700)
        _modale_runden(p, 10)
        if "Projekte" in name:
            nrn = p.evaluate(PROJ_NRN_JS)
            if zeigen:
                print("    Projekte sichtbar:", nrn)
            for nr in nrn[:4]:
                p.evaluate(KLICK_TAB_JS, i)
                p.wait_for_timeout(600)
                if not p.evaluate(KARTE_JS, nr):
                    continue
                p.wait_for_timeout(1200)
                if zeigen:
                    print("    Projekt", nr)
                _projekt_durchgehen(p, zeigen)
                p.evaluate(ZURUECK_JS)
                p.wait_for_timeout(500)
        print("    %-22s Stellen bisher %d" % (name, p.evaluate(STELLEN_JS)))

    funde = p.evaluate("() => window.__selFunde")
    gesehen = p.evaluate("() => window.__selGesehen")
    orte = p.evaluate("() => window.__selOrte")
    b.close()
    return {"rolle": rolle, "funde": funde, "gesehen": gesehen, "orte": orte}


def main(argv):
    from playwright.sync_api import sync_playwright

    zeigen = "--zeigen" in argv
    port = _server()
    url = "http://127.0.0.1:%d/index.html" % port

    laeufe = []
    with sync_playwright() as pw:
        for rolle, nutzer in ROLLEN:
            print("=== Lauf als %s ===" % rolle)
            r = _lauf(pw, url, rolle, nutzer, zeigen)
            if r is None:
                return 2
            laeufe.append(r)

    alle_orte = {}
    alle_funde = []
    for r in laeufe:
        for o, n in r["orte"].items():
            alle_orte.setdefault(o, {})[r["rolle"]] = n
        for f in r["funde"]:
            alle_funde.append(dict(f, rolle=r["rolle"]))

    print()
    for r in laeufe:
        print("Lauf %-8s: %4d select-Aufrufe, %3d verschiedene Fundorte"
              % (r["rolle"], r["gesehen"], len(r["orte"])))
    print()
    # Ehrlichkeit ueber die Reichweite: ohne diese Liste liest der naechste
    # "keine Funde" als "alles geprueft".
    print("GEMESSENE STELLEN (zusammen): %d" % len(alle_orte))

    def _sort(k):
        t = k.split(":")
        try:
            return (0, int(t[1]))
        except Exception:
            return (1, 0)

    for o in sorted(alle_orte, key=_sort):
        print("   %-26s %s" % (o, alle_orte[o]))

    print()
    if not alle_funde:
        print("KEIN Auswahlfeld hatte einen Wert ausserhalb seiner Optionen.")
        return 0

    nach_ort = {}
    for f in alle_funde:
        s = nach_ort.setdefault((f["ort"], f["wert"], f["rolle"]), dict(f, n=0))
        s["n"] += 1
    print("FUNDE: %d Stellen (%d Aufrufe)" % (len(nach_ort), len(alle_funde)))
    print()
    for (ort, wert, rolle), f in sorted(nach_ort.items(), key=lambda x: -x[1]["n"]):
        print("  %s   x%d   (%s)" % (ort or "(ohne Ort)", f["n"], rolle))
        print("     Wert %r (%s) steht NICHT unter %d Optionen"
              % (wert, f["roh"], f["anzahl"]))
        print("     Das Feld zeigt stattdessen: %r" % f["zeigt"])
        print("     Optionen: %s" % ", ".join(repr(o) for o in f["optionen"]))
        print()
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
