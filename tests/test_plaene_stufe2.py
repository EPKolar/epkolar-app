# -*- coding: utf-8 -*-
"""Plaene Stufe 2 - "Buero-Tablet". Je Punkt ein Riegel MIT Umkehrprobe.

Die Rechnungen (Filter, Zentrieren, Grenzen, Listen-Scroll, Geschoss, Versionen)
sind reine Funktionen und werden woertlich aus index.html geschnitten und mit
Node AUSGEFUEHRT. Jede Umkehrprobe baut die Stelle gezielt zurueck und verlangt,
dass der Riegel dann anschlaegt - sonst waere er blind.

  1 Tablet       ab 900 px Plan | Liste dauerhaft, Auswahl synchron, Bildplaene zentrieren
  2 Filter       Status, Zustaendig, Frist, Ebene/Typ - EIN Filter fuer Pins und Liste, "n von m"
  3 Wischen      Grenzen beim Verschieben, Werkzeugknoepfe beschriftet, "Einpassen" benannt
  4 Version      "Version n · hochgeladen TT.MM.JJJJ", aeltere Versionen nur ansehen
  5 Hochladen    EIN Weg je Seite, danach im neuen Plan, Geschoss aus dem Dateinamen
  6 Schreibwege  createTicket/updateTicket/deleteTicket/Mangel-Spiegel unveraendert
"""
import hashlib
import json
import re

import pytest

from conftest import run_node_snippet


def _fn(src, name):
    a = src.index("function " + name + "(")
    m = re.compile(r"\r?\n(?:function |const |// |/\*)").search(src, a + 10)
    return src[a:m.start() if m else len(src)]


def _vplan(src):
    a = src.index("function VPlan(")
    return src[a:src.index("// ═══════════ OFFA EXPORT", a)]


def _node(node_exe, src, namen, ausdruck):
    js = "\n".join(_fn(src, n) for n in namen) + "\nprocess.stdout.write(JSON.stringify(" + ausdruck + "));"
    return json.loads(run_node_snippet(node_exe, js))


# ── 1 Tablet: Plan | Liste, synchron ───────────────────────────────────────
def pruef_tablet(src):
    v = _vplan(src)
    pv = _fn(src, "PlanViewerCanvas")
    li = src[src.index("const TicketListItem = React.memo("):src.index("function _tkFertig(")]
    b = []
    if "const _dauerListe=ww>=900;" not in v:
        b.append("keine 900-px-Schwelle fuer die dauerhafte Liste")
    if 'const _rechts=!isMob&&subView==="viewer"&&(_dauerListe||showSidebar||' not in v:
        b.append("rechte Spalte ab 900 px nicht dauerhaft")
    if "(!_dauerListe&&(_qtEl||_qdEl))" not in v or "(_qInListe&&_qOffen.id===t.id)" not in v:
        b.append("Blatt ersetzt ab 900 px wieder die Liste (Zeile nicht mehr sichtbar)")
    if "'data-tk': ticket.id" not in li:
        b.append("Listenzeile ohne Ticket-Kennung - die Liste kann nicht zum Ticket scrollen")
    if "_listeScrollZiel(cr.top,c.clientHeight,rr.top,rr.height,c.scrollTop,8)" not in v or "ref: _spalteRef" not in v:
        b.append("Liste scrollt nicht zum gewaehlten Ticket")
    if "_planZentrieren(vr.width, vr.height, el.offsetWidth, el.offsetHeight" not in pv or "if(_isPdf || !selectedTicket) return;" not in pv:
        b.append("Bildplaene werden beim Auswaehlen nicht zentriert")
    return b


def test_tablet(index_html):
    assert pruef_tablet(index_html) == []


@pytest.mark.parametrize("alt,neu", [
    ("(_dauerListe||showSidebar||", "(showSidebar||"),
    ("'data-tk': ticket.id, ", ""),
    ("if(_isPdf || !selectedTicket) return;", "if(true) return;"),
])
def test_tablet_umkehrprobe(index_html, alt, neu):
    assert alt in index_html, alt
    assert pruef_tablet(index_html.replace(alt, neu, 1)), "Riegel blind fuer: " + alt


def test_zentrieren_rechnet_pin_in_die_mitte(index_html, node_exe):
    """Bildschirm-x des Pins = ox + pan.x + nx*w*zoom muss nach dem Zentrieren vw/2 sein (bei jedem Zoom, mit Flex-Versatz)."""
    def lauf(src):
        return _node(node_exe, src, ["_planZentrieren"],
                     "[[800,600,1200,900,-200,-150,.25,.75,1],[800,600,1200,900,-200,-150,.9,.1,2.5],[360,470,2400,1700,-1020,-615,.5,.5,.14]]"
                     ".map(a=>{const z=_planZentrieren.apply(null,a);return [a[4]+z.x+a[6]*a[2]*a[8], a[5]+z.y+a[7]*a[3]*a[8], a[0]/2, a[1]/2];})"
                     ".concat([[_planZentrieren(800,600,0,900,0,0,.5,.5,1), _planZentrieren(800,600,10,10,0,0,null,.5,1)]])")
    r = lauf(index_html)
    for sx, sy, mx, my in r[:3]:
        assert abs(sx - mx) < 1e-6 and abs(sy - my) < 1e-6
    assert r[3] == [None, None]
    # Umkehrprobe: ohne den Flex-Versatz landet der Pin daneben
    kaputt = lauf(index_html.replace("return {x:vw/2-(ox||0)-nx*w*zoom", "return {x:vw/2-nx*w*zoom", 1))
    assert any(abs(sx - mx) > 1 for sx, sy, mx, my in kaputt[:3])


def test_liste_scrollt_zum_ticket(index_html, node_exe):
    def lauf(src):
        # Container oben 100, 400 hoch, scrollTop 50. Zeile ganz sichtbar / unten raus / oben raus / hoeher als Container
        return _node(node_exe, src, ["_listeScrollZiel"],
                     "[_listeScrollZiel(100,400,200,60,50,8),_listeScrollZiel(100,400,560,80,50,8),_listeScrollZiel(100,400,40,60,300,8),_listeScrollZiel(100,400,150,900,0,8)]")
    sichtbar, unten, oben, gross = lauf(index_html)
    assert sichtbar is None
    assert unten == 50 + (460 + 80) - 400 + 8          # Unterkante 8 px ueber dem Rand
    assert oben == 300 + (40 - 100) - 8                # Oberkante 8 px unter dem Rand
    assert gross == 0 + 50 - 8                         # zu hoch: Oberkante zeigen
    kaputt = lauf(index_html.replace("if(oben>=r&&unten<=cH-r) return null;", "", 1))
    assert kaputt[0] is not None


# ── 2 Filter ───────────────────────────────────────────────────────────────
HEUTE = "2026-11-18"   # Mittwoch; Woche = 16.11. bis 22.11.
TK = [
    {"id": "a", "status": "offen", "type": "mangel", "gewerk": "l1", "assignee": "w1", "dueDate": "2026-11-17", "title": "Steckdose fehlt", "description": "Wohnzimmer"},
    {"id": "b", "status": "erledigt", "type": "mangel", "layer": "l1", "assignee": "w2", "dueDate": "2026-11-10", "title": "FI loest aus"},
    {"id": "c", "status": "in_bearbeitung", "type": "aufgabe", "gewerk": "l2", "assignee": "", "dueDate": "2026-11-22", "title": "Leerrohr Kueche"},
    {"id": "d", "status": "offen", "type": "aufgabe", "gewerk": "l2", "assignee": "w1", "dueDate": "2026-11-23", "title": "Heizkreis"},
    {"id": "e", "status": "offen", "type": "mangel", "gewerk": "l3", "assignee": "", "dueDate": "", "title": "Kabel Kueche", "description": "nicht beschriftet"},
    {"id": "f", "status": "abgenommen", "type": "mangel", "gewerk": "l1", "assignee": "w1", "due_date": "2026-11-18T00:00:00Z", "title": "Abnahme"},
]
FALLE = [
    ("status offen", {"status": "offen"}, ["a", "d", "e"]),
    ("zustaendig w1", {"asg": "w1"}, ["a", "d", "f"]),
    ("nicht zugewiesen", {"asg": "_keiner"}, ["c", "e"]),
    ("ueberfaellig (fertig zaehlt nicht)", {"frist": "ueberfaellig"}, ["a"]),
    ("diese Woche Mo..So, offen", {"frist": "woche"}, ["a", "c"]),
    ("ohne Frist", {"frist": "ohne"}, ["e"]),
    ("Ebene gewerk||layer", {"ebene": "l1"}, ["a", "b", "f"]),
    ("Typ", {"typ": "aufgabe"}, ["c", "d"]),
    ("Suche Token-UND", {"suche": "kueche kabel"}, ["e"]),
    ("ausgeblendete Ebene", {"versteckt": ["l2", "l3"]}, ["a", "b", "f"]),
    ("kombiniert", {"status": "offen", "asg": "w1", "frist": "ueberfaellig"}, ["a"]),
    ("alles alle", {"status": "alle", "asg": "alle", "frist": "alle", "ebene": "alle", "typ": "alle"}, ["a", "b", "c", "d", "e", "f"]),
]


def _filter_lauf(node_exe, src):
    aus = "[" + ",".join("_planFilter(T,%s,%s).map(t=>t.id)" % (json.dumps(f), json.dumps(HEUTE)) for _, f, _ in FALLE) + \
          ",_planFilterAktiv({status:'offen',asg:'alle',suche:' x ',versteckt:['l1']}),_planWoche('2026-11-22'),_planWoche('2026-11-16')]"
    js = "\n".join(_fn(src, n) for n in ["_tkFertig", "_planWoche", "_planFilter", "_planFilterAktiv"]) + \
        "\nconst T=" + json.dumps(TK) + ";\nprocess.stdout.write(JSON.stringify(" + aus + "));"
    return json.loads(run_node_snippet(node_exe, js))


def test_filter_regeln(index_html, node_exe):
    r = _filter_lauf(node_exe, index_html)
    for (name, _f, soll), ist in zip(FALLE, r):
        assert ist == soll, name
    assert r[len(FALLE)] == 3
    assert r[len(FALLE) + 1] == ["2026-11-16", "2026-11-22"]   # Sonntag gehoert zur laufenden Woche
    assert r[len(FALLE) + 2] == ["2026-11-16", "2026-11-22"]   # Montag ebenso


@pytest.mark.parametrize("alt,neu", [
    ("if(!_d||!_h||!(_d<_h)||_tkFertig(t.status))return false;", "if(!_d||!_h||!(_d<=_h))return false;"),
    ('if(filterAsg==="_keiner"?_a!=="":_a!==filterAsg)return false;', "if(_a!==filterAsg)return false;"),
    ("var t=Date.UTC(+m[1],+m[2]-1,+m[3]), wt=(new Date(t).getUTCDay()+6)%7", "var t=Date.UTC(+m[1],+m[2]-1,+m[3]), wt=new Date(t).getUTCDay()"),
])
def test_filter_regeln_umkehrprobe(index_html, node_exe, alt, neu):
    assert alt in index_html, alt
    r = _filter_lauf(node_exe, index_html.replace(alt, neu, 1))
    falsch = [name for (name, _f, soll), ist in zip(FALLE, r) if ist != soll]
    falsch += ["woche"] if r[len(FALLE) + 1] != ["2026-11-16", "2026-11-22"] else []
    assert falsch, "Riegel blind fuer: " + alt


def pruef_filter_gemeinsam(src):
    v = _vplan(src)
    b = []
    if "tickets: _vpFiltered.concat(_defGef)" not in v:
        b.append("Pins nehmen nicht denselben gefilterten Satz (Mangel-Pins ungefiltert)")
    if "return _vpFiltered.filter(t=>(t.planId||t.plan_id)===_pid).concat(_defGef).filter(t=>_vsLy.indexOf(t.gewerk||t.layer)<0)" not in v:
        b.append("Liste nimmt nicht denselben Satz wie die Pins")
    if "return _planFilter(allTickets,{typ:filterType,status:filterStatus,ebene:filterLayer,asg:filterAsg,frist:filterFrist,suche:_q},td2());" not in v:
        b.append("_vpFiltered laeuft nicht ueber _planFilter (Zustaendig/Frist fehlen)")
    if 'const _fZaehler=filteredTickets.length+" von "+_planAlle.length' not in v:
        b.append("kein Zaehler 'n von m'")
    for s in ('setFilterAsg("alle")', 'setFilterFrist("alle")', 'setFilterStatus("alle")', 'setFilterLayer("alle")', 'setFilterSearch("")'):
        if s not in v[v.index("const _fReset="):v.index("const _fReset=") + 600]:
            b.append("Zuruecksetzen laesst %s aus" % s)
    for lab in ("Nach Status filtern", "Nach Zuständig filtern", "Nach Frist filtern", "Nach Ebene filtern"):
        if "'aria-label': \"%s\"" % lab not in v:
            b.append("Filterfeld fehlt: " + lab)
    return b


def test_filter_gemeinsam(index_html):
    assert pruef_filter_gemeinsam(index_html) == []


@pytest.mark.parametrize("alt,neu", [
    ("tickets: _vpFiltered.concat(_defGef)", "tickets: _vpFiltered.concat(_defectPins)"),
    ('setFilterAsg("alle");setFilterFrist("alle");', ""),
    ("'aria-label': \"Nach Frist filtern\"", "'aria-label': \"x\""),
])
def test_filter_gemeinsam_umkehrprobe(index_html, alt, neu):
    assert alt in index_html, alt
    assert pruef_filter_gemeinsam(index_html.replace(alt, neu, 1)), "Riegel blind fuer: " + alt


# ── 3 Wischen: Grenzen, Beschriftung ───────────────────────────────────────
def _grenze_lauf(node_exe, src):
    # Sichtfenster 360x470, Plan 1000x700 Layout, Ursprung (-320,-115), Zoom .34 -> 340x238 auf dem Schirm
    return _node(node_exe, src, ["_planPanGrenze"],
                 "[[5000,5000],[-5000,-5000],[100,20],[-900,300]].map(p=>{const g=_planPanGrenze(p[0],p[1],360,470,1000,700,-320,-115,.34,80);"
                 "const l=-320+g.x, o=-115+g.y, r=l+340, u=o+238;return {g:g, sichtX:Math.min(r,360)-Math.max(l,0), sichtY:Math.min(u,470)-Math.max(o,0)};})"
                 ".concat([_planPanGrenze(7,8,0,470,1000,700,0,0,1,80)])")


def test_grenzen_halten_den_plan_im_bild(index_html, node_exe):
    r = _grenze_lauf(node_exe, index_html)
    for e in r[:2]:
        assert e["sichtX"] >= 80 - 1e-6 and e["sichtY"] >= 80 - 1e-6, e
    assert r[2]["g"] == {"x": 100, "y": 20}              # innerhalb der Grenzen unveraendert
    assert r[4] == {"x": 7, "y": 8}                      # ohne Masse: nichts erfinden
    kaputt = _grenze_lauf(node_exe, index_html.replace("return {x:Math.max(rx-o1-bw, Math.min(vw-rx-o1, px)), y:Math.max(ry-o2-bh, Math.min(vh-ry-o2, py))};", "return {x:px, y:py};", 1))
    assert kaputt[0]["sichtX"] < 80 or kaputt[1]["sichtY"] < 80


def pruef_wischen(src):
    pv = _fn(src, "PlanViewerCanvas")
    b = []
    if "setPan(_g ? _planPanGrenze(_nx, _ny, _g.vw, _g.vh, _g.w, _g.h, _g.ox, _g.oy, zoom, Math.max(80, Math.round(Math.min(_g.vw, _g.vh) * 0.35))) : {x: _nx, y: _ny});" not in pv:
        b.append("Ziehen ist nicht begrenzt")
    if "g: _panGeo()};" not in pv:
        b.append("Geometrie wird beim Aufsetzen nicht gemessen")
    leiste = pv[pv.index("'aria-orientation': \"vertical\""):pv.index("pageCount > 1 ? React.createElement('div', {style: {position: \"absolute\", top: 58")]
    knoepfe = leiste.count("React.createElement('button',")
    if knoepfe < 6 or leiste.count("_pvT(") != knoepfe:
        b.append("nicht jeder Werkzeugknopf hat ein sichtbares Kurzwort (%d Knoepfe, %d Worte)" % (knoepfe, leiste.count("_pvT(")))
    if leiste.count("'aria-label'") + leiste.count('"aria-label"') != knoepfe:
        b.append("Werkzeugknopf ohne aria-label")
    if '"aria-label": "Einpassen – ganzen Plan zeigen"' not in leiste or '_pvT("Einpassen")' not in leiste:
        b.append("'Einpassen' nicht klar benannt")
    if '"aria-label": "Zoom zurücksetzen"' in leiste:
        b.append("Einpassen heisst wieder 'Zoom zuruecksetzen'")
    return b


def test_wischen(index_html):
    assert pruef_wischen(index_html) == []


@pytest.mark.parametrize("alt,neu", [
    ("setPan(_g ? _planPanGrenze(_nx, _ny, _g.vw, _g.vh, _g.w, _g.h, _g.ox, _g.oy, zoom, Math.max(80, Math.round(Math.min(_g.vw, _g.vh) * 0.35))) : {x: _nx, y: _ny});", "setPan({x: _nx, y: _ny});"),
    (', _pvT("Breite")', ""),
    ('"aria-label": "Einpassen – ganzen Plan zeigen"', '"aria-label": "Zoom zurücksetzen"'),
])
def test_wischen_umkehrprobe(index_html, alt, neu):
    assert alt in index_html, alt
    assert pruef_wischen(index_html.replace(alt, neu, 1)), "Riegel blind fuer: " + alt


# ── 4 Version ──────────────────────────────────────────────────────────────
def test_versionskette(index_html, node_exe):
    pl = [
        {"id": "v1", "pid": "p", "version": 1, "archived": True, "replacesPlanId": ""},
        {"id": "v3", "pid": "p", "version": 3, "archived": False, "replacesPlanId": "v2"},
        {"id": "x", "pid": "p", "version": 1, "replacesPlanId": ""},
        {"id": "v2", "pid": "p", "version": 2, "archived": True, "replacesPlanId": "v1"},
        {"id": "z1", "pid": "q", "replacesPlanId": "z2"}, {"id": "z2", "pid": "q", "replacesPlanId": "z1"},
    ]
    def lauf(src):
        return _node(node_exe, src, ["_planVersionen"],
                     "(()=>{const P=%s;const k=p=>_planVersionen(P,P.find(x=>x.id===p)).map(x=>x.id);return [k('v3'),k('v1'),k('x'),k('z1'),_planVersionen(P,null)];})()" % json.dumps(pl))
    v3, v1, x, zyklus, leer = lauf(index_html)
    assert v3 == ["v1", "v2", "v3"] and v1 == ["v1", "v2", "v3"]
    assert x == ["x"] and leer == []
    assert sorted(zyklus) == ["z1", "z2"]                 # zyklenfest
    kaputt = lauf(index_html.replace("kette.unshift(cur);", "kette.push(cur);", 1))
    assert kaputt[0] != ["v1", "v2", "v3"]


def pruef_version(src):
    v = _vplan(src)
    b = []
    if 'const _verText=(pl)=>"Version "+_verNr(pl)+(pl&&pl.uploadedAt?" · hochgeladen "+fdt(String(pl.uploadedAt).slice(0,10)):"");' not in v:
        b.append("Versionstext fehlt oder ohne Datum")
    if "_versionEl" not in v[v.index("zweite Zeile"):v.index("zweite Zeile") + 600]:
        b.append("Version steht nicht im Kopf")
    if "const _neuesTicketAn=(pos)=>{if(!selPlan||!selPlan.id||_altPlan)return;" not in v:
        b.append("aeltere Version laesst neue Tickets zu")
    if "plan: _altPlan||selPlan" not in v or ", selPlan&&plans.length>0&&!_altPlan&&!pendingPin&&" not in v:
        b.append("aeltere Version: Anzeige oder Plus-Knopf falsch")
    if '"Zur aktuellen Version"' not in v:
        b.append("kein Weg zurueck zur aktuellen Version")
    return b


def test_version(index_html):
    assert pruef_version(index_html) == []


@pytest.mark.parametrize("alt,neu", [
    ("if(!selPlan||!selPlan.id||_altPlan)return;", "if(!selPlan||!selPlan.id)return;"),
    (", selPlan&&plans.length>0&&!_altPlan&&!pendingPin&&", ", selPlan&&plans.length>0&&!pendingPin&&"),
    ('(pl&&pl.uploadedAt?" · hochgeladen "', '(false?" · hochgeladen "'),
])
def test_version_umkehrprobe(index_html, alt, neu):
    assert alt in index_html, alt
    assert pruef_version(index_html.replace(alt, neu, 1)), "Riegel blind fuer: " + alt


# ── 5 Hochladen ────────────────────────────────────────────────────────────
GESCHOSS = [
    ("plan_eg.png", "Erdgeschoss"), ("E-Plan EG.pdf", "Erdgeschoss"), ("Grundriss Erdgeschoss", "Erdgeschoss"),
    ("E-Plan 1.OG.pdf", "1. Obergeschoss"), ("2OG_Elektro.pdf", "2. Obergeschoss"), ("OG 3 Licht.pdf", "3. Obergeschoss"),
    ("Obergeschoss.png", "1. Obergeschoss"), ("Keller.pdf", "Keller"), ("KG Heizung", "Keller"), ("UG-Plan", "Untergeschoss"),
    ("DG_Ausbau.pdf", "Dachgeschoss"), ("TG Lueftung", "Tiefgarage"), ("Außenanlage.pdf", "Außenanlage"),
    ("Regal-Liste.pdf", ""), ("Beleg 100kg.pdf", ""), ("Plan_2024.pdf", ""), ("", ""),
]


def _geschoss_lauf(node_exe, src):
    return _node(node_exe, src, ["_geschossAusName"], "%s.map(_geschossAusName)" % json.dumps([n for n, _ in GESCHOSS], ensure_ascii=False))


def test_geschoss_aus_dateiname(index_html, node_exe):
    r = _geschoss_lauf(node_exe, index_html)
    assert r == [s for _, s in GESCHOSS], [(n, s, i) for (n, s), i in zip(GESCHOSS, r) if s != i]
    kaputt = _geschoss_lauf(node_exe, index_html.replace("|(^|[^a-z0-9])eg([^a-z]|$)/.test(s)", "|eg/.test(s)", 1))
    assert kaputt != [s for _, s in GESCHOSS]            # ohne Wortgrenze traefe "Regal"


def pruef_hochladen(src):
    v = _vplan(src)
    verw = v[v.index('subView==="upload"&&'):v.index("/* Plaene Stufe 1: am Handy genau EIN Blatt")]
    b = []
    verw = re.sub(r"/\*.*?\*/", "", verw, flags=re.S)
    if "hierher ziehen" in verw or "onDrop: handleDrop" in verw:
        b.append("Planverwaltung hat wieder die Ablagezone (dritter Hochlade-Weg)")
    if verw.count("fileRef, 'access'") != 1:
        b.append("Planverwaltung hat nicht genau EINEN Hochlade-Knopf (%d)" % verw.count("fileRef, 'access'"))
    if ', isAdmin&&plans.length>0&&_mPunkt("export","Plan hochladen",' not in v:
        b.append("Menue bietet Hochladen auch neben dem Leer-Knopf an")
    if v.count('_setNeuPlan({id:np.id,gs:_gs,vorschlag:_gs});') != 2 or v.count('setSelPlan(np);setSubView("viewer");_setNeuPlan(') != 2:
        b.append("nach dem Hochladen nicht im neuen Plan mit Geschoss-Hinweis")
    if "const _gs=_geschossAusName(file.name);" not in v or v.count("...(_gs?{category:_gs}:{})") != 2:
        b.append("Geschoss wird nicht aus dem Dateinamen vorgeschlagen")
    return b


def test_hochladen(index_html):
    assert pruef_hochladen(index_html) == []


@pytest.mark.parametrize("alt,neu", [
    (', isAdmin&&plans.length>0&&_mPunkt("export","Plan hochladen",', ', isAdmin&&_mPunkt("export","Plan hochladen",'),
    ('setSelPlan(np);setSubView("viewer");_setNeuPlan({id:np.id,gs:_gs,vorschlag:_gs});};', 'setSelPlan(np);setSubView("viewer");};'),
    ("const _gs=_geschossAusName(file.name);", "const _gs=\"\";"),
])
def test_hochladen_umkehrprobe(index_html, alt, neu):
    assert alt in index_html, alt
    assert pruef_hochladen(index_html.replace(alt, neu, 1)), "Riegel blind fuer: " + alt


# ── 6 Schreibwege unveraendert ─────────────────────────────────────────────
SCHREIB_MD5 = {   # gemessen an origin/main v3.9.1025; create/updateTicket neu gemessen fuer Plaene Stufe 3 (bewusste Aenderung)
    "createTicket": "951a7a90b9c5d572ba94821aa1d525a1",
    "updateTicket": "14605d6bb657baab3592a962708e36db",
    "deleteTicket": "c8aef3ad2e09bb2d5948642505313c12",   # Offen-4 17.11.2026 neu gemessen: Storage-Fotos des geloeschten Tickets aufraeumen, an Projekt+Ticket gebunden (bewusste Aenderung, Auftrag Punkt 4 + Sicherheits-Nachzug)
    "_qdEl": "70e8d515018b401da91ee98ea1b93f15",
}


def _schreibwege(src):
    s = src.replace("\r\n", "\n")
    out = {}
    for a, z in (("createTicket", "const updateTicket="), ("updateTicket", "const deleteTicket=")):
        i = s.index("const " + a + "=")
        out[a] = hashlib.md5(s[i:s.index(z, i)].encode("utf-8")).hexdigest()
    for a in ("deleteTicket", "_qdEl"):
        i = s.index("const " + a + "=")
        out[a] = hashlib.md5(s[i:s.index("\n", i)].encode("utf-8")).hexdigest()
    return out


def test_schreibwege_unveraendert(index_html):
    assert _schreibwege(index_html) == SCHREIB_MD5


def test_schreibwege_umkehrprobe(index_html):
    kaputt = index_html.replace("const deleteTicket=async id=>{if(!isAdmin)return;", "const deleteTicket=async id=>{", 1)
    assert kaputt != index_html
    assert _schreibwege(kaputt) != SCHREIB_MD5
