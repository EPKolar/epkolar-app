# -*- coding: utf-8 -*-
"""v3.9.927 - EIN SPEICHERNAME MIT PROJEKTKENNUNG KANN NIE IN STORES STEHEN.

WORAUS DAS ENTSTAND (offener Punkt 33)
--------------------------------------
Der Dokumentexplorer legt seine Listen so ab:

    ODB.save("docs_"+p.id, docs)      und      ODB.load("docs_"+p.id)

Dasselbe fuer "folders_", "fotos_" und "bt_". IndexedDB legt Speicher
AUSSCHLIESSLICH in onupgradeneeded an, aus der festen Liste STORES. Ein Name,
der die Projektkennung traegt, kann dort nie stehen. Also war _odbHasStore
falsch, ODB.set und ODB.get haben gewarnt und NICHTS getan - in beide
Richtungen. Der Dokumente-Reiter war ohne Netz immer leer, seit es ihn gibt.

Das wiegt schwer, weil v3.9.890 ausdruecklich "Plaene offline" gebaut hat. Es
gab kein Geraet, auf dem ein Plan dauerhaft lag. Dokumente, Ordner, Fotos und
Bautagebuch waren derselbe Fall, nur unbemerkt.

WAS AM 31.08. IM ECHTEN BROWSER GEMESSEN WURDE
----------------------------------------------
scripts/doku_offline_messen.py, Chromium, Projekt p4, Serverantworten ueber
playwright-route; ab Runde 2 wird JEDE Anfrage an /rest/v1/ abgebrochen - das
ist der Keller ohne Empfang. Runde 2b geht danach aus dem Projekt heraus und
wieder hinein, ohne neu zu laden: das ist der Tag auf der Baustelle.

    Fassung                     MIT Netz  OHNE Netz  2. Besuch  IndexedDB
    index.html (v3.9.926)       3 von 3   0 von 3    0 von 3    20 Speicher, DB 9
                                                                docs_p4 wirft
                                                                NotFoundError
    mit den Paaren unten        3 von 3   3 von 3    3 von 3    21 Speicher, DB 10
                                                                projektCache traegt
                                                                docs_p4, folders_p4

Und die Datenmenge, ein Dokument von 300 KiB im selben Lauf hochgeladen:

    Fassung                    Zwischenspeicher      syncQueue
    mit Deckel                 569 -> 823 Byte       1119 -> 411125 Byte
    ohne Deckel (Gegenprobe)   569 -> 410463 Byte    1119 -> 411125 Byte

Die base64-Nutzlast liegt also ohnehin schon in der syncQueue. Ohne Deckel
laege sie ein ZWEITES Mal im Zwischenspeicher - das waere offener Punkt 19
eine Etage tiefer.

DIE UEBERRASCHUNG, UND SIE IST DER GRUND FUER DIESEN RIEGEL
-----------------------------------------------------------
Der naheliegende Umbau - Speicher anlegen, Aufrufe umhaengen - ist GRUEN und
aendert NICHTS. Gemessen an einer Fassung, der nur die Leer-Sperre fehlt:

    ohne Leer-Sperre            3 von 3   0 von 3    0 von 3

Grund: die Speicher-Wirkung des Reiters laeuft beim Einhaengen mit einer noch
LEEREN Liste los, waehrend die Lade-Wirkung noch am fetch haengt. Der leere
Erstlauf ueberschreibt den Zwischenspeicher, BEVOR er gelesen wird. Wer nur
den Speicher nachlegt, hat einen funktionierenden Speicher und einen weiterhin
leeren Reiter - und haette es beim Ausliefern nicht gemerkt.

UND DIE ZWEITE UEBERRASCHUNG, DIESMAL AM EIGENEN UMBAU
------------------------------------------------------
Die erste Fassung dieser Sperre war feiner gebaut: eine leere Liste durfte
durch, sobald unter demselben Schluessel schon einmal eine gefuellte lag - das
sollte eine echte Loeschung von einem leeren Erstlauf unterscheiden. Sie war
im Messlauf gruen. Sie fiel erst um, als das Messgeraet das tat, was ein
Monteur den ganzen Tag tut: Projekt zu, Projekt wieder auf.

    erste Fassung der Sperre    3 von 3   3 von 3    0 von 3

Ohne Netz gibt es beim zweiten Aufschlagen keinen Server, der den leeren
Erstlauf hinterher wieder wegraeumt. Die Sperre gilt jetzt ausnahmslos, und
der Preis dafuer steht unten bei Abschnitt 5.

WIE HIER GEMESSEN WIRD
----------------------
Nicht durch Abschreiben der Schreibweise. Der ODB-Block wird woertlich aus
index.html geschnitten und mit Node AUSGEFUEHRT, gegen einen IndexedDB-Nachbau,
der den Vertrag des Browsers einhaelt: Speicher entstehen nur in
onupgradeneeded, onupgradeneeded laeuft nur bei hoeherer Fassungsnummer, und
eine Transaktion auf einen unbekannten Speicher WIRFT. Zu jedem Riegel gehoert
eine Gegenprobe, die die alte Fassung zurueckbaut und verlangt, dass sie
bricht.

SOLANGE DIE PAARE NICHT ANGEWENDET SIND, IST DIESE DATEI ROT. Das ist Absicht.
"""
import json
import re
import subprocess

from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]
INDEX = WURZEL / "index.html"

AZ = chr(10)


# ═══ Werkzeug zum Schneiden ══════════════════════════════════════════════
def _quelle():
    return INDEX.read_text(encoding="utf-8")


def _block(quelle, anfang, ende):
    """Von anfang (einschliesslich) bis vor ende - beide woertlich."""
    i = quelle.index(anfang)
    j = quelle.index(ende, i)
    return quelle[i:j].replace(chr(13), "")


def _einmal(quelle, text, wofuer):
    n = quelle.count(text)
    assert n == 1, (
        "%s ist nicht mehr eindeutig zu finden (%d Treffer). Dieser Riegel "
        "misst dann nichts - genau der Zustand, in dem ein gruener Lauf "
        "wertlos ist." % (wofuer, n))


def _odb_block(quelle=None):
    """DB_NAME, DB_VER, STORES, die Helfer, openDB, _odbHasStore, ODB."""
    q = quelle if quelle is not None else _quelle()
    return _block(q, 'const DB_NAME="epkolar_offline"',
                  "const _USER_SCOPED_ODB_STORES=")


# ═══ Der IndexedDB-Nachbau ═══════════════════════════════════════════════
# Er steht bewusst HIER und nicht in index.html: gemessen werden soll der
# Code der App gegen den Vertrag des Browsers, nicht der Code der App gegen
# sich selbst. Drei Eigenschaften des Vertrags sind die, an denen Punkt 33
# haengt, und alle drei sind nachgebaut:
#   1) Speicher entstehen NUR in onupgradeneeded.
#   2) onupgradeneeded laeuft NUR, wenn die verlangte Fassung hoeher ist.
#   3) transaction() auf einen unbekannten Speicher WIRFT.
# Der "Datentraeger" ueberlebt mehrere open() - sonst liesse sich ueber die
# Fassungsnummer gar nichts aussagen.
SHIM = """
const _warns=[];
console.warn=(...a)=>{_warns.push(a.map(String).join(" "));};
const _platte={version:0,stores:{}};
function _mkDB(){
  return {
    version:_platte.version,
    objectStoreNames:{contains:n=>Object.prototype.hasOwnProperty.call(_platte.stores,n),
                      _alle:()=>Object.keys(_platte.stores)},
    createObjectStore(n){_platte.stores[n]=new Map();return {};},
    transaction(n){
      if(!Object.prototype.hasOwnProperty.call(_platte.stores,n))
        throw new Error("NotFoundError: object store not found: "+n);
      const m=_platte.stores[n]; const tx={};
      setTimeout(()=>{if(tx.oncomplete)tx.oncomplete();},0);
      tx.objectStore=()=>({
        get(k){const r={};setTimeout(()=>{r.result=m.get(k);if(r.onsuccess)r.onsuccess();},0);return r;},
        put(v,k){m.set(k,v);}, delete(k){m.delete(k);}, clear(){m.clear();},
        getAll(){const r={};setTimeout(()=>{r.result=[...m.values()];if(r.onsuccess)r.onsuccess();},0);return r;}
      });
      return tx;
    }
  };
}
globalThis.indexedDB={open(name,ver){
  const r={};
  setTimeout(()=>{
    const verlangt=(ver===undefined?_platte.version:ver);
    const db=_mkDB();
    if(verlangt>_platte.version){_platte.version=verlangt;db.version=verlangt;
      if(r.onupgradeneeded)r.onupgradeneeded({target:{result:db}});}
    if(r.onsuccess)r.onsuccess({target:{result:db}});
  },0);
  return r;
}};
globalThis.window={};
function _platteSetzen(version,namen){_platte.version=version;_platte.stores={};
  namen.forEach(n=>{_platte.stores[n]=new Map();});}
function _platteNamen(){return Object.keys(_platte.stores);}
"""


def _node(programm, tmp_path, name):
    p = tmp_path / name
    p.write_text(programm, encoding="utf-8")
    r = subprocess.run(["node", str(p)], capture_output=True, text=True,
                       encoding="utf-8")
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


def _lauf(tmp_path, name, koerper, quelle=None):
    """SHIM + der geschnittene ODB-Block + koerper, ausgefuehrt."""
    prog = SHIM + AZ + _odb_block(quelle) + AZ + koerper
    return _node(prog, tmp_path, name)


# ═══ 1) DER MASSSTAB - misst der Nachbau ueberhaupt etwas? ════════════════
# Diese Pruefung steht bewusst zuerst und ist heute schon gruen. Waere sie rot,
# waere jede Aussage weiter unten wertlos: dann saehe ein heiler und ein
# kaputter Stand gleich aus.
def test_der_nachbau_unterscheidet_bekannten_und_unbekannten_speicher(tmp_path):
    aus = _lauf(tmp_path, "massstab.js", """
(async()=>{
  await ODB.save("projects",[{id:"p4"}]);
  const gut=await ODB.load("projects");
  await ODB.save("gibt_es_nicht_p4",[{id:"x"}]);
  const schlecht=await ODB.load("gibt_es_nicht_p4");
  console.log(JSON.stringify({gut:gut, schlecht:schlecht===undefined?"UNDEFINED":schlecht,
                              warnungen:_warns}));
})();
""")
    assert aus["gut"] == [{"id": "p4"}], (
        "Ein Speicher AUS STORES muss durchgehen. Bekommen: %r" % (aus["gut"],))
    assert aus["schlecht"] == "UNDEFINED", (
        "Ein Speicher, den es nicht gibt, darf nichts liefern. Bekommen: %r"
        % (aus["schlecht"],))
    assert any("Store missing" in w for w in aus["warnungen"]), (
        "Der Nachbau meldet den fehlenden Speicher nicht - dann kann dieser "
        "Riegel den Befund von Punkt 33 nicht sehen. Warnungen: %r"
        % (aus["warnungen"],))


# ═══ 2) KEIN AUFRUF LAEUFT MEHR INS LEERE ═════════════════════════════════
# Die Regel dieses Repos: eine Reparatur an einer von vier Stellen ist keine.
# Deshalb wird NICHT auf "docs_" geprueft, sondern auf die Eigenschaft: jeder
# Speichername, den ODB.get/set/del/getAll/clear/save/load bekommt, muss in
# STORES stehen koennen. Ein zusammengesetzter Name kann das nie.
ERLAUBTE_BEZEICHNER = {
    "store",              # der Parameter von ODB.save/ODB.load selbst
    "_s",                 # laeuft ueber _USER_SCOPED_ODB_STORES
    "PLAN_CACHE_STORE",   # ist "planFiles"
    "PROJ_CACHE_STORE",   # ist "projektCache" (v3.9.927)
}


def _odb_argumente(q):
    """Jedes erste Argument jedes ODB-Aufrufs, mit Zaehlung."""
    raus = {}
    for _m, arg in re.findall(
            r"ODB\.(get|set|del|getAll|clear|save|load)\(\s*([^,)]+)", q):
        a = arg.strip()
        raus[a] = raus.get(a, 0) + 1
    return raus


def test_jeder_odb_speichername_kann_in_stores_stehen(tmp_path):
    q = _quelle()
    stores = set(re.findall(
        r'"([^"]+)"', re.search(r"const STORES=\[(.*?)\];", q).group(1)))
    schlecht = []
    for arg, n in sorted(_odb_argumente(q).items()):
        lit = re.fullmatch(r"""["']([^"']+)["']""", arg)
        if lit:
            if lit.group(1) not in stores:
                schlecht.append("%s (%dx) - Name steht nicht in STORES" % (arg, n))
        elif arg not in ERLAUBTE_BEZEICHNER:
            schlecht.append("%s (%dx) - zusammengesetzter Name, kann in STORES "
                            "nie stehen" % (arg, n))
    assert not schlecht, (
        "Diese ODB-Aufrufe treffen keinen Speicher. _odbHasStore ist falsch, "
        "es folgt ein console.warn und ein No-Op - in BEIDE Richtungen." + AZ
        + AZ.join("   " + s for s in schlecht) + AZ
        + "Fuer projektbezogene Listen ist ODB.saveProj/ODB.loadProj da: EIN "
          "Speicher, der bisherige Name ist der SCHLUESSEL.")


def test_die_projektbezogenen_listen_gehen_ueber_saveProj_und_loadProj():
    q = _quelle()
    offen = []
    for praefix in ("docs_", "folders_", "fotos_", "bt_"):
        for m in re.finditer(
                r'ODB\.(save|load|get|set)\(\s*"' + praefix, q):
            if m.group(1) in ("save", "load", "get", "set"):
                offen.append(praefix + " ueber ODB." + m.group(1))
    assert not offen, (
        "Diese Listen laufen weiter ueber ODB.save/ODB.load mit einem "
        "zusammengesetzten Namen und damit ins Leere: " + ", ".join(offen))
    for praefix, wieviel in (("docs_", 3), ("folders_", 3),
                             ("fotos_", 3), ("bt_", 3)):
        n = len(re.findall(r'ODB\.(?:saveProj|loadProj)\(\s*"' + praefix, q))
        assert n == wieviel, (
            "Von %s werden %d Aufrufe erwartet, gefunden %d. Wenn hier eine "
            "Stelle fehlt, ist genau sie die, die ohne Netz leer bleibt."
            % (praefix, wieviel, n))


# ═══ 3) DIE FASSUNGSNUMMER - ohne sie legt niemand den Speicher an ════════
# Der Speicher entsteht in onupgradeneeded, und onupgradeneeded laeuft nur bei
# hoeherer Fassungsnummer. Auf einem Geraet, das die App schon benutzt hat,
# liegt die DB auf 9. Bleibt DB_VER auf 9, ist der neue Name in STORES ein
# frommer Wunsch: fuer JEDEN Bestandsnutzer aendert sich nichts. Genau diese
# Falle ist unten AUSGEFUEHRT, nicht behauptet.
BESTAND_V9 = ('["entries","forms","abs","absApprovals","files","planData",'
              '"werkzeuge","arbeitsscheine","monteure","syncQueue","meta",'
              '"projects","monteurProjekte","photoQueue","fahrzeuge",'
              '"stundenzettel","notifications","syncQueueFailed",'
              '"urlaubskontingent","planFiles"]')


def test_ein_bestandsgeraet_bekommt_den_neuen_speicher_nachgelegt(tmp_path):
    aus = _lauf(tmp_path, "bestand.js", """
(async()=>{
  _platteSetzen(9,""" + BESTAND_V9 + """);
  const vorher=_platteNamen().length;
  await ODB.saveProj("docs_p4",[{id:"d1",name:"Bauplan"}]);
  const gelesen=await ODB.loadProj("docs_p4");
  console.log(JSON.stringify({DB_VER:DB_VER, vorher:vorher,
    nachher:_platteNamen().length, hat:_platteNamen().indexOf(PROJ_CACHE_STORE)>=0,
    gelesen:gelesen===undefined?"UNDEFINED":gelesen, warnungen:_warns}));
})();
""")
    assert aus["DB_VER"] > 9, (
        "DB_VER steht auf %s. Der neue Speicher entsteht nur in "
        "onupgradeneeded, und das laeuft nur bei hoeherer Fassungsnummer - "
        "fuer jedes Geraet, auf dem die App schon lief, aendert sich sonst "
        "NICHTS." % aus["DB_VER"])
    assert aus["hat"], (
        "Nach dem Sprung von 9 auf %s fehlt %r immer noch. Angelegt wurden "
        "%d statt %d Speicher." % (aus["DB_VER"], "projektCache",
                                   aus["nachher"], aus["vorher"] + 1))
    assert aus["gelesen"] == [{"id": "d1", "name": "Bauplan"}], (
        "Auf dem Bestandsgeraet kommt die Liste nicht zurueck: %r"
        % (aus["gelesen"],))


def test_gegenprobe_ohne_fassungssprung_bleibt_alles_beim_alten(tmp_path):
    """Die alte Fassung zurueckgebaut: DB_VER bleibt 9. Muss brechen."""
    q = _quelle().replace(chr(13), "")
    neu = re.sub(r'(const DB_NAME="epkolar_offline";const DB_VER=)\d+',
                 r"\g<1>9", q, count=1)
    assert neu != q, "DB_VER war nicht zu finden - die Gegenprobe misst nichts."
    aus = _lauf(tmp_path, "gegen_ver.js", """
(async()=>{
  _platteSetzen(9,""" + BESTAND_V9 + """);
  await ODB.saveProj("docs_p4",[{id:"d1"}]);
  const gelesen=await ODB.loadProj("docs_p4");
  console.log(JSON.stringify({hat:_platteNamen().indexOf(PROJ_CACHE_STORE)>=0,
    gelesen:gelesen===undefined?"UNDEFINED":gelesen}));
})();
""", quelle=neu)
    assert not aus["hat"] and aus["gelesen"] == "UNDEFINED", (
        "Mit DB_VER 9 muesste der Speicher auf einem Bestandsgeraet FEHLEN. "
        "Er ist da (%r) - dann misst der Riegel darueber nicht die "
        "Fassungsnummer, sondern irgendetwas anderes." % (aus,))


# ═══ 4) DER DECKEL - base64 darf nicht ein zweites Mal in die IndexedDB ═══
# addDoc legt die hochgeladene Datei als vollstaendige data-URL in den Zustand
# und kennt KEINE Groessengrenze (offener Punkt 19; der Bucket laesst 50 MiB je
# Datei). Dieselben Bytes liegen bereits in der syncQueue - im Browser gemessen
# waren es bei 300 KiB Datei 409640 Zeichen dort. Ein Zwischenspeicher ohne
# Deckel schriebe sie ein zweites Mal.
GROSSES_DOKUMENT = """
const gross="data:application/pdf;base64,"+"Z".repeat(400000);
const doku=[{id:"d1",name:"Bauplan",cat:"plaene",filename:"eg.pdf",
             size:300000,dataUrl:gross,fileUrl:""}];
"""


def test_die_base64_nutzlast_wird_vor_dem_schreiben_entfernt(tmp_path):
    aus = _lauf(tmp_path, "deckel.js", GROSSES_DOKUMENT + """
(async()=>{
  const ok=await ODB.saveProj("docs_p4",doku);
  const zurueck=await ODB.loadProj("docs_p4");
  const z=(zurueck||[])[0]||{};
  console.log(JSON.stringify({geschrieben:ok, zeilen:(zurueck||[]).length,
    bytes:JSON.stringify(zurueck===undefined?null:zurueck).length,
    dataUrl:String(z.dataUrl||"").slice(0,12),
    name:z.name, filename:z.filename, size:z.size, cat:z.cat}));
})();
""")
    assert aus["geschrieben"] is True and aus["zeilen"] == 1, (
        "Das Dokument muss ankommen - nur eben ohne die Nutzlast. Bekommen: %r"
        % (aus,))
    assert aus["dataUrl"] == "", (
        "Die base64-Nutzlast steht immer noch im Zwischenspeicher (%r). Sie "
        "liegt bereits in der syncQueue; ein zweites Mal ist offener Punkt 19 "
        "eine Etage tiefer." % aus["dataUrl"])
    assert aus["bytes"] < 1000, (
        "Der Eintrag ist %d Byte gross. Erwartet wird eine Liste, kein "
        "Dateispeicher." % aus["bytes"])
    # Und die Gegenprobe im selben Test: das Bleibende muss BLEIBEN. Ein
    # Deckel, der die Zeile ausraeumt, waere so nutzlos wie gar keiner.
    assert (aus["name"], aus["filename"], aus["size"], aus["cat"]) == \
        ("Bauplan", "eg.pdf", 300000, "plaene"), (
        "Vom Dokument ist zu wenig uebrig: %r. Ohne Name, Dateiname, Groesse "
        "und Kategorie ist die Liste ohne Netz wertlos." % (aus,))


def test_gegenprobe_ohne_entfernen_landet_die_nutzlast_im_speicher(tmp_path):
    """_pcSchlank auf Durchreichen zurueckgebaut. Muss brechen."""
    q = _quelle().replace(chr(13), "")
    _einmal(q, "function _pcSchlank(daten){", "_pcSchlank")
    neu = q.replace("function _pcSchlank(daten){",
                    "function _pcSchlank(daten){return daten;", 1)
    aus = _lauf(tmp_path, "gegen_deckel.js", GROSSES_DOKUMENT + """
(async()=>{
  const ok=await ODB.saveProj("docs_p4",doku);
  const zurueck=await ODB.loadProj("docs_p4");
  console.log(JSON.stringify({geschrieben:ok,
    bytes:JSON.stringify(zurueck===undefined?null:zurueck).length}));
})();
""", quelle=neu)
    assert aus["bytes"] > 100000, (
        "Ohne das Entfernen muessten die 400000 Zeichen im Zwischenspeicher "
        "landen. Gemessen wurden %d Byte - dann misst der Riegel darueber "
        "nicht das Entfernen." % aus["bytes"])


def test_was_auch_geschlankt_zu_gross_bleibt_wird_gar_nicht_geschrieben(tmp_path):
    """Gekuerzt wird NICHT: eine gekuerzte Liste sieht aus wie geloeschte Dateien."""
    aus = _lauf(tmp_path, "zugross.js", """
(async()=>{
  const viele=[]; for(let i=0;i<40000;i++)viele.push({id:"d"+i,
    name:"Dokument mit einem recht langen Namen Nummer "+i,note:"xxxxxxxxxx"});
  const gut=[{id:"d1",name:"Bauplan"}];
  const okGut=await ODB.saveProj("docs_p4",gut);
  const okViel=await ODB.saveProj("docs_p4",viele);
  const zurueck=await ODB.loadProj("docs_p4");
  console.log(JSON.stringify({max:PROJ_CACHE_MAX, okGut:okGut, okViel:okViel,
    zeilen:(zurueck||[]).length, warnungen:_warns}));
})();
""")
    assert aus["okGut"] is True, "Die kleine Liste muss durchgehen: %r" % (aus,)
    assert aus["okViel"] is False, (
        "Eine Liste ueber %s Byte muss abgelehnt werden, nicht gekuerzt. "
        "Bekommen: %r" % (aus["max"], aus))
    assert aus["zeilen"] == 1, (
        "Nach der Ablehnung muss die LETZTE gute Liste stehen bleiben "
        "(%d Zeilen gefunden). Eine halb ueberschriebene Liste waere "
        "schlimmer als eine alte." % aus["zeilen"])
    assert any("zu gross" in w for w in aus["warnungen"]), (
        "Die Ablehnung muss in der Konsole stehen - sonst ist es ein stiller "
        "Verlust. Warnungen: %r" % (aus["warnungen"],))


# ═══ 5) DIE LEER-SPERRE - der eigentliche Fund ════════════════════════════
# Der Reiter haengt seine Speicher-Wirkung mit einer noch LEEREN Liste ein,
# waehrend die Lade-Wirkung noch am fetch haengt. Im Browser gemessen, an
# ZWEI Fassungen dieses Umbaus:
#
#   Fassung                              ohne Netz   ohne Netz, 2. Besuch
#   alles fertig, nur ohne Leer-Sperre   0 von 3     0 von 3
#   (index_v927_ohne_leersperre.html)
#   leere Liste erlaubt, sobald schon    3 von 3     0 von 3
#   einmal eine gefuellte darunter lag
#   leere Liste NIE (die Paare unten)    3 von 3     3 von 3
#
# Die mittlere Zeile ist die Lehre. Sie sah richtig aus, sie war es beim
# ersten Aufschlagen auch, und sie fiel erst um, als das Messgeraet das tat,
# was ein Monteur den ganzen Tag tut: Projekt zu, Projekt wieder auf. Ohne
# diese eine Runde waere sie ausgeliefert worden.
#
# DER PREIS steht ausdruecklich hier: wer das LETZTE Dokument eines Projekts
# loescht, sieht ohne Netz weiter die alte Liste. Genau so halten es die
# app-weiten Zwischenspeicher seit jeher, siehe die sieben Ablagen mit
# `if(curUser&&X.length)`.
def test_eine_leere_liste_wird_nie_geschrieben(tmp_path):
    aus = _lauf(tmp_path, "leer.js", """
(async()=>{
  // 1) Genau die Reihenfolge des Reiters: erst der leere Erstlauf.
  const erst=await ODB.saveProj("docs_p4",[]);
  const nachErst=await ODB.loadProj("docs_p4");
  // 2) Dann kommt die Liste - aus dem Server oder aus dem Zwischenspeicher.
  await ODB.saveProj("docs_p4",[{id:"d1",name:"Bauplan"},{id:"d2",name:"Abnahme"}]);
  const nachFuellen=(await ODB.loadProj("docs_p4")||[]).length;
  // 3) Und jetzt das ZWEITE Aufschlagen desselben Projekts ohne Netz: wieder
  //    ein leerer Erstlauf. Er darf die Liste nicht abraeumen.
  const zweitesMal=await ODB.saveProj("docs_p4",[]);
  const nachZweitem=(await ODB.loadProj("docs_p4")||[]).length;
  // 4) Und die Sperre haengt am Schluessel, nicht am Speicher.
  await ODB.saveProj("docs_p9",[{id:"x"}]);
  const anderes=(await ODB.loadProj("docs_p9")||[]).length;
  console.log(JSON.stringify({erst:erst,
    nachErst:nachErst===undefined?"UNDEFINED":nachErst,
    nachFuellen:nachFuellen, zweitesMal:zweitesMal,
    nachZweitem:nachZweitem, anderes:anderes}));
})();
""")
    assert aus["erst"] is False and aus["nachErst"] == "UNDEFINED", (
        "Der leere Erstlauf darf nichts schreiben. Bekommen: %r" % (aus,))
    assert aus["nachFuellen"] == 2, (
        "Die gefuellte Liste muss ankommen: %r" % (aus,))
    assert aus["zweitesMal"] is False and aus["nachZweitem"] == 2, (
        "Beim ZWEITEN Aufschlagen desselben Projekts ohne Netz kommt wieder "
        "ein leerer Erstlauf - und diesmal kein Server, der den Schaden "
        "hinterher wegraeumt. Genau hier ist die erste Fassung dieses Umbaus "
        "umgefallen. Bekommen: %r" % (aus,))
    assert aus["anderes"] == 1, (
        "Ein anderes Projekt darf von alldem nichts merken. %r" % (aus,))


def test_gegenprobe_ohne_leersperre_geht_die_liste_verloren(tmp_path):
    """Die Sperre zurueckgebaut - genau die Fassung, die im Browser 0 von 3 zeigte."""
    q = _quelle().replace(chr(13), "")
    sperre = "if(Array.isArray(daten)&&daten.length===0)return false;"
    _einmal(q, sperre, "die Leer-Sperre in ODB.saveProj")
    aus = _lauf(tmp_path, "gegen_leer.js", """
(async()=>{
  await ODB.saveProj("docs_p4",[{id:"d1"},{id:"d2"}]);
  const erst=await ODB.saveProj("docs_p4",[]);
  const danach=(await ODB.loadProj("docs_p4")||[]).length;
  console.log(JSON.stringify({erst:erst, danach:danach}));
})();
""", quelle=q.replace(sperre, "", 1))
    assert aus["danach"] == 0, (
        "Ohne die Sperre MUSS die leere Liste die gefuellte ausloeschen - das "
        "ist der im Browser gemessene Zustand. Sie tut es nicht (%r), also "
        "misst der Riegel darueber nicht die Sperre." % (aus,))


# ═══ 6) DER NUTZERWECHSEL - geteiltes Baustellen-Tablet ═══════════════════
# Der Purge beim Nutzerwechsel macht ODB.del(store,'data') und traefe die
# Schluessel "docs_<projekt>" nie. Genau dieselbe Luecke hatte v3.9.890 bei
# planFiles - dort steht deshalb ein eigenes ODB.clear daneben.
def test_der_nutzerwechsel_raeumt_den_projekt_zwischenspeicher(tmp_path):
    q = _quelle()
    _einmal(q, 'try{await ODB.clear("planFiles");}catch(_){}',
            "der planFiles-Purge beim Nutzerwechsel")
    assert 'try{await ODB.clear(PROJ_CACHE_STORE);}catch(_){}' in q, (
        "Beim Nutzerwechsel wird der Projekt-Zwischenspeicher nicht geraeumt. "
        "Auf einem geteilten Baustellen-Tablet blieben Dokument- und "
        "Ordnernamen fremder Projekte des Vorgaengers stehen - der Purge "
        "darueber macht ODB.del(store,'data') und trifft die Schluessel nicht.")
    # Und ausgefuehrt: clear() muss auf diesem Speicher ueberhaupt greifen.
    aus = _lauf(tmp_path, "purge.js", """
(async()=>{
  await ODB.saveProj("docs_p4",[{id:"d1"}]);
  await ODB.saveProj("folders_p4",[{id:"f1"}]);
  const vorher=(await ODB.loadProj("docs_p4")||[]).length;
  await ODB.del(PROJ_CACHE_STORE,"data");   // was der alte Purge tut
  const nachDel=(await ODB.loadProj("docs_p4")||[]).length;
  await ODB.clear(PROJ_CACHE_STORE);        // was jetzt daneben steht
  const nachClear=(await ODB.loadProj("docs_p4")||[]).length;
  const ordner=(await ODB.loadProj("folders_p4")||[]).length;
  console.log(JSON.stringify({vorher:vorher, nachDel:nachDel,
                              nachClear:nachClear, ordner:ordner}));
})();
""")
    assert aus["vorher"] == 1, "Die Saat kommt nicht an: %r" % (aus,)
    assert aus["nachDel"] == 1, (
        "ODB.del(store,'data') darf die Projekt-Schluessel NICHT treffen - "
        "wenn doch, misst dieser Riegel den Unterschied nicht. %r" % (aus,))
    assert aus["nachClear"] == 0 and aus["ordner"] == 0, (
        "ODB.clear muss beide Schluessel raeumen: %r" % (aus,))
