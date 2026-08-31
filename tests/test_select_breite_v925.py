# -*- coding: utf-8 -*-
"""v3.9.925 - dieselbe Invariante, an den Feldern hinter den Modalen.

WORAUS DAS ENTSTAND
-------------------
tests/test_select_wert_v923.py riegelt vier Stellen, an denen

    DER GEWAEHLTE WERT MUSS UNTER DEN ANGEBOTENEN OPTIONEN SEIN

verletzt war. Der Messlauf dazu (scripts/select_wert_messen.py) sagt aber
selbst, wo seine Grenze liegt: von 118 Auswahlfeldern hat er 25 GERENDERT.
"Keine Funde" hiess fuer die uebrigen 93 ausdruecklich NICHT "geprueft".

scripts/select_breite_messen.py hat die Reichweite auf 42 Fundorte erhoeht -
Projektmaske, Ticket-Fenster, Zeit-Modal, Dokumentenliste, drei Rollen - und
dabei die drei namentlich offenen Fundorte erreicht. Dieser Riegel haelt fest,
was dabei herauskam.

  Stelle                              VORHER (gemessen)          NACHHER
  Ticket-Formular Typ (leer)          -> "Mangel"                neutral
  Ticket-Formular Status (fremd)      -> "Offen"                 neutral
  Ticket-Formular Prio "normal"       -> "Kritisch"              neutral
  Ticket-Formular Ebene (Freitext)    -> "Elektro"               neutral
  Zeit-Modal Monteur (nicht zugew.)   -> "Aktiv Anton"           der gebuchte
  Dokument-Ordner (geloescht)         -> "— Ordner —"            unveraendert

Die letzte Zeile ist Absicht. Der Verdacht ist WIDERLEGT und wird deshalb nur
benannt: ein Dokument, dessen Ordner es nicht mehr gibt, faellt auf die leere
Option - und genau dasselbe sagen der Listenfilter, der Zaehler "Ohne Ordner"
und der Ordnerbaum. Die Anzeige stimmt mit jedem anderen Leser ueberein, es
gibt keine Folge, also wird nichts repariert. Der Riegel misst diese
UEBEREINSTIMMUNG - er wuerde rot, wenn jemand den Filter spaeter aendert und
die Anzeige damit zur Luege macht.

WARUM DIE VIER TICKET-FELDER MEHR SIND ALS ANZEIGE
--------------------------------------------------
saveEdit ruft onUpdate({...ticket,...ed}) und updateTicket schreibt daraus ein
PUT. Solange niemand das Feld anfasst, bleibt der alte Wert stehen - die
Anzeige luegt, sonst passiert nichts. Wer aber die scheinbar schon gewaehlte
Stufe ANKLICKT, schreibt sie:
  * "Mangel" laesst updateTicket einen Defect ANLEGEN (POST /api/defects,
    Spiegel in forms.maengel und damit im Kundenportal)
  * "Kritisch" eskaliert die Prioritaet samt Defect-Spiegel
Und in jedem Fall widerspricht die Maske dem abgelegten Beleg: Ticket-Liste,
PDF-Report und XLS-Export lassen die Spalte LEER, weil ihr Nachschlagen ins
Leere greift.

WIE HIER GEMESSEN WIRD
----------------------
Nicht durch Abschreiben der Schreibweise. Die Ausdruecke werden woertlich aus
index.html geschnitten und mit Node AUSGEFUEHRT, und zu jedem Riegel gehoert
eine Gegenprobe, die die alte Fassung zurueckbaut und verlangt, dass sie
bricht.
"""
import json
import subprocess

from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]
INDEX = WURZEL / "index.html"

NL = chr(10)


# ═══ Werkzeug zum Schneiden ══════════════════════════════════════════════
def _quelle():
    return INDEX.read_text(encoding="utf-8")


def _block(quelle, anfang, ende):
    """Von anfang (einschliesslich) bis vor ende - beide woertlich."""
    i = quelle.index(anfang)
    j = quelle.index(ende, i)
    return quelle[i:j].replace(chr(13), "")


def _funktion(quelle, kopf):
    """function name(...){...} ueber die Klammerbilanz schneiden."""
    i = quelle.index(kopf)
    d = 0
    k = quelle.index("{", i)
    while k < len(quelle):
        c = quelle[k]
        if c == "{":
            d += 1
        elif c == "}":
            d -= 1
            if d == 0:
                return quelle[i:k + 1].replace(chr(13), "")
        k += 1
    raise AssertionError("Klammern von %r nicht ausgeglichen" % kopf)


def _node(programm, tmp_path, name, arg=None):
    p = tmp_path / name
    p.write_text(programm, encoding="utf-8")
    cmd = ["node", str(p)]
    if arg is not None:
        cmd.append(json.dumps(arg))
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


def _einmal(quelle, text, wofuer):
    n = quelle.count(text)
    assert n == 1, (
        "%s ist nicht mehr eindeutig zu finden (%d Treffer). Dieser Riegel "
        "misst dann nichts - genau der Zustand, in dem ein gruener Lauf "
        "wertlos ist." % (wofuer, n))


# ═══ 1) TICKET-FORMULAR: vier Felder, eine Frage ═════════════════════════
# Die vier Auswahlfelder stehen in EINER Zeile desselben Formulars und hatten
# denselben Fehler. Eine Reparatur an einem von vier waere in diesem Repo
# keine - deshalb werden sie hier gemeinsam gemessen.
#
# Die Faelle sind nicht erfunden:
#   type ""            - ein Ticket ohne Typ; der Lesepfad faellt auf "info"
#   status fremd       - Altbestand
#   priority "normal"  - steht woertlich in der Notiz von v3.9.362 als Wert
#                        aus Alt-POSTs
#   gewerk Freitext    - die Schreibweise aus projects.gewerk
#   gewerk "maengel"   - schreibt die App beim Anlegen ohne Ebene selbst
TK_FELDER = [
    ("Typ", "TICKET_TYPES", "ed.type"),
    ("Status", "TICKET_STATUS", "ed.status"),
    ("Prioritaet", "TICKET_PRIO", "ed.priority"),
]
TK_FAELLE = {
    "Typ": [("leer", ""), ("fehlt", None), ("gueltig", "aufgabe")],
    "Status": [("fremd", "wartet_auf_kunde"), ("leer", ""),
               ("gueltig", "erledigt")],
    "Prioritaet": [("normal aus Alt-POST", "normal"), ("leer", ""),
                   ("gueltig", "hoch")],
}
# Die erste Option jedes Vorrats - genau das zeigte das Feld vorher.
TK_ERSTE = {"Typ": "mangel", "Status": "offen", "Prioritaet": "kritisch"}


def _vorrat_zeile(quelle, name):
    """Die eine Zeile `const NAME={...};` - ohne die Nachbarn."""
    i = quelle.index("const " + name + "=")
    j = quelle.index(chr(10), i)
    return quelle[i:j].replace(chr(13), "")


def _tk_programm(quelle, vorrat, mit_neutraler_option):
    return (
        "const COLORS={ERROR:'#ef4444',EP_GREEN:'#009640'};" + NL
        + _vorrat_zeile(quelle, vorrat) + NL
        + (_funktion(quelle, "function _optFremd(") + NL
           if mit_neutraler_option else "")
        + "const faelle=JSON.parse(process.argv[2]);" + NL
        + "console.log(JSON.stringify(faelle.map(function(f){" + NL
        + "  const roh=f.wert;" + NL
        + ("  const wert=String(roh==null?'':roh);"
           if mit_neutraler_option else
           "  const wert=String(roh);") + NL
        + ("  const optionen=(_optFremd(Object.keys(" + vorrat + "),roh)"
           "?[wert]:[]).concat(Object.keys(" + vorrat + "));"
           if mit_neutraler_option else
           "  const optionen=Object.keys(" + vorrat + ");") + NL
        + "  return {name:f.name, wert:wert, optionen:optionen," + NL
        + "          dabei:optionen.indexOf(wert)>=0," + NL
        + "          gezeigt:optionen.indexOf(wert)>=0?wert:"
          "(optionen.length?optionen[0]:null)};" + NL
        + "})));" + NL)


def _tk_anker(vorrat, wertausdruck):
    return ("_optFremd(Object.keys(" + vorrat + ")," + wertausdruck
            + ")&&_optNeutral(" + wertausdruck + ")")


def test_ticket_formular_behauptet_keine_fremde_stufe(tmp_path):
    q = _quelle()
    _einmal(q, "function _optFremd(", "der Stufen-Helfer")
    _einmal(q, "function _optNeutral(", "die neutrale Option")

    for name, vorrat, ausdruck in TK_FELDER:
        _einmal(q, _tk_anker(vorrat, ausdruck),
                "die neutrale Option des Feldes " + name)
        _einmal(q, "value: " + ausdruck + '||"", onChange: e=>setEd(',
                "die Wertzeile des Feldes " + name)

        arg = [{"name": n, "wert": w} for n, w in TK_FAELLE[name]]
        aus = _node(_tk_programm(q, vorrat, True), tmp_path,
                    "tk_neu_%s.js" % vorrat, arg)
        for r in aus:
            assert r["dabei"], (
                "Feld %s, Fall '%s': der Wert %r steht NICHT unter %r. Das "
                "Feld zeigt dann %r - eine Stufe, die niemand gewaehlt hat, "
                "waehrend Liste, PDF und XLS-Export leer bleiben."
                % (name, r["name"], r["wert"], r["optionen"], r["gezeigt"]))
        # Die neutrale Option darf NUR auftauchen, solange der Wert keine
        # gueltige Stufe IST - sonst waere "unbekannt" eine waehlbare Stufe
        # geworden und stuende ueber jeder echten.
        gueltig = next(r for r in aus if r["name"] == "gueltig")
        assert gueltig["optionen"][0] == TK_ERSTE[name], gueltig["optionen"]
        assert gueltig["gezeigt"] == dict(TK_FAELLE[name])["gueltig"], gueltig


def test_gegenprobe_ticket_formular_alt_zeigt_die_erste_stufe(tmp_path):
    """Ohne diese Umkehr waere nicht belegt, dass der Aufbau den Fehler SIEHT."""
    q = _quelle()
    for name, vorrat, _ausdruck in TK_FELDER:
        arg = [{"name": n, "wert": w} for n, w in TK_FAELLE[name]]
        aus = _node(_tk_programm(q, vorrat, False), tmp_path,
                    "tk_alt_%s.js" % vorrat, arg)
        verloren = [r["name"] for r in aus if not r["dabei"]]
        erwartet = [n for n, _w in TK_FAELLE[name] if n != "gueltig"]
        assert verloren == erwartet, (
            "Feld %s: die alte Fassung MUSS genau %r verlieren - sonst misst "
            "dieser Riegel nichts. Verloren: %r" % (name, erwartet, verloren))
        for r in aus:
            if not r["dabei"]:
                assert r["gezeigt"] == TK_ERSTE[name], (
                    "Feld %s, Fall '%s' haette %r gezeigt, erwartet war %r - "
                    "die erste Stufe des Vorrats."
                    % (name, r["name"], r["gezeigt"], TK_ERSTE[name]))


# ═══ 2) TICKET-FORMULAR EBENE: derselbe Helfer, anderer Vorrat ═══════════
LY_ANKER = ("_optFremd(layers.map(l=>l.id),ed.gewerk||ed.layer)"
            "&&_optNeutral(ed.gewerk||ed.layer)")
LY_FAELLE = [
    ("Gewerk-Freitext", {"gewerk": "Elektro komplett"}),
    ("maengel", {"gewerk": "maengel"}),
    ("gar nichts", {}),
    ("leerer Text", {"gewerk": "", "layer": ""}),
    ("gueltige Ebene", {"gewerk": "l3"}),
    ("nur layer gesetzt", {"layer": "l2"}),
]


def _ly_programm(quelle, mit_neutraler_option):
    return (
        "const COLORS={INFO:'#3b82f6',ERROR:'#ef4444'};" + NL
        + _vorrat_zeile(quelle, "DEF_LAYERS") + NL
        + (_funktion(quelle, "function _optFremd(") + NL
           if mit_neutraler_option else "")
        + "const layers=DEF_LAYERS;" + NL
        + "const faelle=JSON.parse(process.argv[2]);" + NL
        + "console.log(JSON.stringify(faelle.map(function(f){" + NL
        + "  const ed=f.ed;" + NL
        + ("  const wert=String(ed.gewerk||ed.layer||'');"
           if mit_neutraler_option else
           "  const wert=String(ed.gewerk||ed.layer);") + NL
        + ("  const optionen=(_optFremd(layers.map(function(l){return l.id;}),"
           "ed.gewerk||ed.layer)?[wert]:[])"
           ".concat(layers.map(function(l){return l.id;}));"
           if mit_neutraler_option else
           "  const optionen=layers.map(function(l){return l.id;});") + NL
        + "  return {name:f.name, wert:wert, optionen:optionen," + NL
        + "          dabei:optionen.indexOf(wert)>=0," + NL
        + "          gezeigt:optionen.indexOf(wert)>=0?wert:"
          "(optionen.length?optionen[0]:null)};" + NL
        + "})));" + NL)


def _ly_arg():
    return [{"name": n, "ed": e} for n, e in LY_FAELLE]


def test_ticket_formular_behauptet_keine_fremde_ebene(tmp_path):
    q = _quelle()
    _einmal(q, LY_ANKER, "die neutrale Option der Ebenen-Auswahl")
    _einmal(q, 'value: ed.gewerk||ed.layer||"", onChange: e=>setEd(',
            "die Wertzeile der Ebenen-Auswahl")

    aus = _node(_ly_programm(q, True), tmp_path, "ly_neu.js", _ly_arg())
    for r in aus:
        assert r["dabei"], (
            "Fall '%s': der Wert %r steht NICHT unter %r. Das Feld zeigt dann "
            "%r - also eine Ebene, die niemand gewaehlt hat, waehrend Liste, "
            "PDF und XLS-Export an derselben Stelle leer bleiben."
            % (r["name"], r["wert"], r["optionen"], r["gezeigt"]))
    # Der getragene Freitext bleibt SICHTBAR - er ist der Grund, warum der
    # Export leer ist, und wer ihn nicht sieht, kann ihn nicht beheben.
    freitext = next(r for r in aus if r["name"] == "Gewerk-Freitext")
    assert freitext["gezeigt"] == "Elektro komplett", freitext
    # Die gueltigen Faelle bekommen KEINE neutrale Option davor.
    gueltig = next(r for r in aus if r["name"] == "gueltige Ebene")
    assert gueltig["optionen"][0] == "l1", gueltig["optionen"]
    assert gueltig["gezeigt"] == "l3", gueltig
    nur_layer = next(r for r in aus if r["name"] == "nur layer gesetzt")
    assert nur_layer["gezeigt"] == "l2", nur_layer


def test_gegenprobe_ticket_ebene_alt_zeigt_die_erste_ebene(tmp_path):
    aus = _node(_ly_programm(_quelle(), False), tmp_path, "ly_alt.js",
                _ly_arg())
    verloren = [r["name"] for r in aus if not r["dabei"]]
    assert verloren == ["Gewerk-Freitext", "maengel", "gar nichts",
                        "leerer Text"], (
        "Die alte Fassung MUSS genau diese vier Formen verlieren - sonst "
        "misst dieser Riegel nichts. Verloren: %r" % verloren)
    for r in aus:
        if not r["dabei"]:
            assert r["gezeigt"] == "l1", (
                "Fall '%s' haette %r gezeigt, erwartet war 'l1' - die erste "
                "Ebene aus DEF_LAYERS, also 'Elektro'."
                % (r["name"], r["gezeigt"]))


# ═══ 3) ZEIT-MODAL: wer bekommt die Stunden ══════════════════════════════
# VZeit rechnet nur fuer admin/projektleiter mit ALLEN Monteuren; fuer alle
# anderen Rollen ist der Vorrat auf die dem Projekt ZUGEWIESENEN eingeschraenkt
# (allWorkers). Der Bearbeiten-Stift eines bestehenden Eintrags setzt addWorker
# auf entry.worker. Gehoert dieser Monteur nicht (mehr) zur Zuweisung, fiel der
# Wert aus dem Vorrat - und das Feld zeigte den ERSTEN Zugewiesenen. Im Browser
# gemessen als Buero: acht Stunden auf M9, das Feld sagte "Aktiv Anton".
MT_ANKER = ('_mtMitGetragenem(allWorkers,(monteure||MONT),'
            '_vzIsField?_vzMid:addWorker)')
MT_FAELLE = [
    ("zugewiesener Monteur", "M1"),
    ("gebucht auf einen NICHT zugewiesenen", "M9"),
    ("geloeschte Kennung", "M_WEG"),
    ("ohne Wert", ""),
]
MT_ALLE = [{"id": "M1", "n": "Aktiv Anton"}, {"id": "M2", "n": "Aktiv Berta"},
           {"id": "M9", "n": "Ehemalig Egon"}]
MT_ZUGEWIESEN = [{"id": "M1", "n": "Aktiv Anton"},
                 {"id": "M2", "n": "Aktiv Berta"}]


def _mt_programm(quelle, mit_getragenem):
    kopf = ("const ALLE=" + json.dumps(MT_ALLE) + ";" + NL
            + "const ZUGEWIESEN=" + json.dumps(MT_ZUGEWIESEN) + ";" + NL)
    if mit_getragenem:
        kopf += _funktion(quelle, "function _mtMitGetragenem(") + NL
    return (
        kopf
        + "const faelle=JSON.parse(process.argv[2]);" + NL
        + "console.log(JSON.stringify(faelle.map(function(f){" + NL
        + "  const w=f.wert;" + NL
        + ("  const liste=_mtMitGetragenem(ZUGEWIESEN,ALLE,w);"
           if mit_getragenem else "  const liste=ZUGEWIESEN;") + NL
        + "  const optionen=liste.map(function(m){return m.id;});" + NL
        + "  const namen=liste.map(function(m){return m.n;});" + NL
        + "  const i=optionen.indexOf(w);" + NL
        + "  return {name:f.name, wert:w, optionen:optionen, namen:namen," + NL
        + "          dabei:i>=0," + NL
        + "          gezeigt:i>=0?optionen[i]:(optionen.length?optionen[0]:null),"
        + NL
        + "          gezeigterName:i>=0?namen[i]:(namen.length?namen[0]:null)};"
        + NL + "})));" + NL)


def _mt_arg():
    return [{"name": n, "wert": w} for n, w in MT_FAELLE]


def test_zeit_modal_zeigt_den_gebuchten_monteur(tmp_path):
    q = _quelle()
    _einmal(q, "function _mtMitGetragenem(", "der Monteur-Helfer")
    _einmal(q, MT_ANKER, "die Monteur-Auswahl im Zeit-Modal")

    aus = _node(_mt_programm(q, True), tmp_path, "mt_neu.js", _mt_arg())
    for r in aus:
        assert r["dabei"], (
            "Fall '%s': der Wert %r steht NICHT unter %r - das Feld zeigt "
            "dann %r, also einen fremden Namen fuer fremde Stunden."
            % (r["name"], r["wert"], r["optionen"], r["gezeigterName"]))

    getragen = next(r for r in aus
                    if r["name"] == "gebucht auf einen NICHT zugewiesenen")
    assert getragen["gezeigterName"] == "Ehemalig Egon", getragen
    # Eine Kennung, die es gar nicht mehr gibt, kann kein Filter mit einem
    # Namen fuellen - sie muss aber trotzdem stehenbleiben, sonst schreibt der
    # naechste Speichern-Klick jemand anderen in den Eintrag.
    weg = next(r for r in aus if r["name"] == "geloeschte Kennung")
    assert weg["gezeigt"] == "M_WEG", weg
    assert "unbekannt" in weg["gezeigterName"], weg
    # Ohne Wert wird KEIN Name behauptet.
    ohne = next(r for r in aus if r["name"] == "ohne Wert")
    assert ohne["gezeigt"] == "", ohne
    assert ohne["gezeigterName"] == "—", ohne
    # Und der Zusatz erscheint NUR, wenn er getragen wird.
    normal = next(r for r in aus if r["name"] == "zugewiesener Monteur")
    assert normal["optionen"] == ["M1", "M2"], normal["optionen"]


def test_gegenprobe_zeit_modal_alt_zeigt_einen_fremden_monteur(tmp_path):
    aus = _node(_mt_programm(_quelle(), False), tmp_path, "mt_alt.js",
                _mt_arg())
    verloren = [r["name"] for r in aus if not r["dabei"]]
    assert verloren == ["gebucht auf einen NICHT zugewiesenen",
                        "geloeschte Kennung", "ohne Wert"], (
        "Der rohe Vorrat MUSS genau diese drei verlieren - sonst misst dieser "
        "Riegel nichts. Verloren: %r" % verloren)
    for r in aus:
        if not r["dabei"]:
            assert r["gezeigterName"] == "Aktiv Anton", (
                "Fall '%s' haette %r gezeigt - erwartet war 'Aktiv Anton', "
                "also der erste Zugewiesene als angeblicher Empfaenger "
                "fremder Stunden." % (r["name"], r["gezeigterName"]))


# ═══ 4) WIDERLEGT: das Dokument im geloeschten Ordner ════════════════════
# Der Verdacht war benannt und ist im Browser auch angeschlagen: ein Dokument,
# dessen folderId auf einen geloeschten Ordner zeigt, faellt aus dem Vorrat und
# das Feld zeigt die erste Option, "— Ordner —".
#
# Repariert wird trotzdem NICHTS, und das ist das eigentliche Ergebnis: genau
# dasselbe sagen der Listenfilter (fil), der Zaehler noFolderCount und der
# Ordnerbaum. Die Anzeige stimmt also mit JEDEM anderen Leser ueberein; es gibt
# weder Export noch Beleg noch Absenden, das etwas anderes behaupten wuerde.
# Gemessen wird deshalb die UEBEREINSTIMMUNG. Wer den Filter spaeter aendert
# (Waise bleibt in ihrem Ordner), macht die Anzeige zur Luege - und dieser
# Riegel wird rot, bevor das jemand merkt.
DOK_OPT = ("React.createElement('option', { value: \"\"}, \"— Ordner —\"  ), "
           "allFolderOpts.map(f=>(React.createElement('option', "
           "{ key: f.id, value: f.id}, f.label)))")


def test_dokument_im_geloeschten_ordner_verdacht_widerlegt(tmp_path):
    q = _quelle()
    _einmal(q, DOK_OPT, "die Ordner-Auswahl der Dokumentenzeile")
    _einmal(q, 'value: d.folderId||""', "die Wertzeile der Ordner-Auswahl")

    prog = (
        "const folders=[{id:'f1',name:'Fotos',parentId:''}];" + NL
        + "const docs=[{id:'d1',name:'Bauplan',folderId:'F_WEG'},"
          "{id:'d2',name:'Protokoll',folderId:'f1'},"
          "{id:'d3',name:'Lose',folderId:''}];" + NL
        + "const curFolder=null; const search='';" + NL
        + _block(q, "const getChildren=(parentId)=>", "/* v3.9.581 dead-code")
        + NL
        + _block(q, "const flatFolderOpts=(parentId,depth)=>{",
                 "const allFolderOpts=") + NL
        + 'const allFolderOpts=flatFolderOpts("",0);' + NL
        + _block(q, "const fil=docs.filter(d=>{", "const noFolderCount=") + NL
        + _block(q, "const noFolderCount=docs.filter(",
                 "const freigegebenCount=") + NL
        + "const optionen=[''].concat(allFolderOpts.map(function(f){return f.id;}));"
        + NL
        + "console.log(JSON.stringify({optionen:optionen," + NL
        + "  felder:docs.map(function(d){const w=d.folderId||'';"
          "return {id:d.id, wert:w, dabei:optionen.indexOf(w)>=0,"
          "gezeigt:optionen.indexOf(w)>=0?w:optionen[0]};})," + NL
        + "  ohneOrdner:noFolderCount, sichtbar:fil.map(function(d){return d.id;})}));"
        + NL)
    aus = _node(prog, tmp_path, "dok.js")

    d1 = next(f for f in aus["felder"] if f["id"] == "d1")
    # Die Invariante IST hier verletzt - das wird festgehalten, nicht behoben.
    assert not d1["dabei"], (
        "Der Fall ist verschwunden: 'F_WEG' steht jetzt unter %r. Dann misst "
        "dieser Riegel etwas anderes als das, was er beschreibt."
        % aus["optionen"])
    assert d1["gezeigt"] == "", d1
    # UND jeder andere Leser sagt genau dasselbe: das Dokument gilt ueberall
    # als "ohne Ordner". Genau deshalb ist der Fund folgenlos.
    assert aus["ohneOrdner"] == 2, (
        "Der Zaehler 'Ohne Ordner' zaehlt das Dokument im geloeschten Ordner "
        "NICHT mehr mit. Damit widerspricht die Anzeige des Auswahlfeldes "
        "('— Ordner —') dem Rest der Maske - der Verdacht waere dann NICHT "
        "mehr widerlegt. Bekommen: %r" % aus["ohneOrdner"])
    assert aus["sichtbar"] == ["d1", "d2", "d3"], aus["sichtbar"]
