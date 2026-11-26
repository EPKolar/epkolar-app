"""v3.9.1017 GF: "Aktuelle Ansicht (n Scheine)" = GENAU die gefilterte Bildschirmliste, in der Datei nach
Scheinnummer (numerisch-natuerlich) sortiert, Text VOLL (die Datei geht nicht an OFFA).

Gefahren wird die ECHTE Quelle aus index.html in Node: das Filter-Praedikat von `filtered`, der Vergleicher
von `sorted` und `exportOffa` selbst - nur genXls ist durch einen Faenger ersetzt.
Die bisherigen Optionen (offen_bearb ... alle) sind per Byte-Vergleich (sha256 vorher/nachher) abgenommen;
hier steht nur der Riegel, dass sie weiter auf 80 Zeichen kuerzen und keinen Vollabruf mehr machen."""
import json
import re

from conftest import run_node_snippet, _extract_fn

LANG = ("Therme Vaillant ecoTEC; Druckverlust 0,4 bar\nAusdehnungsgefaess pruefen, Sicherheitsventil tauschen - "
        "Kunde ab 14:00 erreichbar; Schluessel beim Nachbarn Top 3. Ende-Marke ZZZ")

# nummer, status, art, monteur, sb, kunde, text, terminVorschlag
_SCHEINE = [
    ("S070010", "aufgenommen", "stoerung", "m1", "KOLAR", "Mueller Anna", LANG, "2026-11-10"),
    ("S070009", "freigegeben", "stoerung", "m1", "KOLAR", "Baeckerei Gross", "Therme stoerungsfrei machen", "2026-11-16"),
    ("S070100", "in_bearbeitung", "wartung", "m2", "WEBER", "Wohnbau Sued", "Jahreswartung Oelbrenner", "2026-11-20"),
    ("S070011", "aufgeschoben", "reparatur", "", "WEBER", "Oeztuerk", "Heizkoerper tauschen; Bad", ""),
    ("S07001", "erledigt", "stoerung", "m1", "KOLAR", "Huber KG", LANG, "2026-10-05"),
    ("S070200", "abgerechnet", "wartung", "m3", "KOLAR", "Weiss", "Wartung Gastherme", "2026-09-10"),
    ("S070012", "bar_bezahlt", "lieferung", "m2", "WEBER", "Cafe Zentral", "Lieferung Boiler", ""),
    ("S070013", "storniert", "stoerung", "m1", "KOLAR", "Storno AG", "Doppelt angelegt", "2026-11-07"),
    ("S070014", "aufgenommen", "stoerung", "m1", "WEBER", "Therme und Co", "Therme kalt", "2026-11-12"),
    ("S070002", "aufgenommen", "reparatur", "", "KOLAR", "Ohne Monteur", "Rohrbruch Keller", "2026-11-16"),
]
_AS = [{"id": "as%d" % i, "nummer": nr, "scheinstatus": st, "scheinart": art, "monteur": m, "sachbearbeiter": sb,
        "kundNr": nr, "kundName": kd, "projektnr": "PA-%d" % i, "arbeitsanweisungen": tx, "durchgefuehrte": "",
        "verrechnung": "verrechenbar", "aufgenommen": "2026-11-01", "terminVorschlag": tv, "terminBestaetigt": "",
        "prioritaet": "keine"} for i, (nr, st, art, m, sb, kd, tx, tv) in enumerate(_SCHEINE)]
_MONT = [{"id": "m1", "n": "Huber Markus"}, {"id": "m2", "n": "Oeztuerk Uemit"}, {"id": "m3", "n": "Weiss Juergen"}]
_BASIS = {"isMonteurRole": False, "isAdmin": True, "curUser": {"monteurId": "m1"}, "filterStatus": "alle",
          "filterArt": "alle", "filterMonteur": "alle", "filterSB": "alle", "search": "", "quickFilter": "",
          "_todayStr": "2026-11-16", "sortCol": "kundName", "sortDir": "asc"}

# (Filter, erwartete Scheinnummern IN DIESER REIHENFOLGE)
_FAELLE = {
    "ohne": ({}, ["S07001", "S070002", "S070009", "S070010", "S070011", "S070012", "S070013", "S070014", "S070100",
                  "S070200"]),
    "monteur": ({"filterMonteur": "m1"}, ["S07001", "S070009", "S070010", "S070013", "S070014"]),
    "suche_art": ({"search": "therme", "filterArt": "stoerung"}, ["S07001", "S070009", "S070010", "S070014"]),
    "sb_status": ({"filterSB": "WEBER", "filterStatus": "offen_bearb"}, ["S070011", "S070014", "S070100"]),
    "meine": ({"quickFilter": "meine"}, ["S07001", "S070009", "S070010", "S070013", "S070014"]),
    "heute": ({"quickFilter": "heute"}, ["S070002", "S070009"]),
    "ueberfaellig": ({"quickFilter": "ueberfaellig"}, ["S070010", "S070014"]),
    "keinmonteur": ({"quickFilter": "keinmonteur"}, ["S070002", "S070011"]),
    "monteurrolle": ({"isMonteurRole": True, "isAdmin": False, "curUser": {"monteurId": "m2"}},
                     ["S070012", "S070100"]),
}


def _zeile(src, name):
    m = re.search(r"^const %s *=.*$" % re.escape(name), src, re.M)
    assert m, name
    return m.group(0).rstrip("\r") + "\n"


def _teile(src):
    m = re.search(r"const exportOffa=(\(statusFilter\)=>\{.*?\n  \});", src, re.S)
    assert m, "exportOffa-Anker veraltet"
    a0 = "const filtered=_react.useMemo.call(void 0, ()=>_asSicht.filter("  # v1126: Liste = _asFuerRolle(arbeitsscheine) (fuer Admin/Buero/PL identisch)
    a = src.index(a0) + len(a0)
    flt = src[a:src.index("),[_asSicht,monteure,isMonteurRole", a)]
    s0 = "const sorted=_react.useMemo.call(void 0, ()=>[...filtered].sort("
    s = src.index(s0) + len(s0)
    srt = src[s:src.index("),[filtered,sortCol", s)]
    return m.group(1), flt, srt


def _lauf(node_exe, src, opt, filt):
    ex, flt, srt = _teile(src)
    glob = "".join(_zeile(src, n) for n in ("COLORS", "AS_STATUS", "AS_GRP_OFFEN", "AS_GRP_FERTIG", "AS_ART",
                                            "AS_VERRECH", "AS_PRIO", "_hasTermin", "_ymd", "td2", "_fdtC"))
    p = dict(_BASIS)
    p.update(filt)
    js = (
        _extract_fn(src, "_optionalChain") + "\n"  # die echte Sucrase-Hilfe, keine Attrappe
        "const COMPANY_FOOTER={name:'Andreas Kolar & Sohn GesmbH'};\n" + glob +
        "let CAP=null;const genXls=(t,st,h,rows,fn)=>{CAP={t,rows,fn};};\n"
        "const p=%s, AS=%s, MONT=%s;\n" % (json.dumps(p), json.dumps(_AS), json.dumps(_MONT)) +
        "const flt=(function(isMonteurRole,isAdmin,curUser,filterStatus,filterArt,filterMonteur,filterSB,search,"
        "quickFilter,_todayStr,monteure){return (" + flt + ");})(p.isMonteurRole,p.isAdmin,p.curUser,p.filterStatus,"
        "p.filterArt,p.filterMonteur,p.filterSB,p.search,p.quickFilter,p._todayStr,MONT);\n"
        "const cmp=(function(sortCol,sortDir,monteure){return (" + srt + ");})(p.sortCol,p.sortDir,MONT);\n"
        "const sorted=AS.filter(flt).sort(cmp);let API_N=0;\n"
        "const API={getToken:()=>'tok',exportOffa:()=>{API_N++;return Promise.resolve([]);}};\n"
        "const fn=(function(setShowExportPicker,API,sorted,arbeitsscheine,monteure){return (" + ex + ");})"
        "(()=>{},API,sorted,AS,MONT);\n"
        "fn(%s);\n" % json.dumps(opt) +
        "process.stdout.write(JSON.stringify({titel:CAP.t,datei:CAP.fn,rows:CAP.rows,bildschirm:sorted.length,api:API_N}));"
    )
    return json.loads(run_node_snippet(node_exe, js))


def _nummern(r):
    return [z[1] for z in r["rows"]]  # Spalte KdNr traegt im Testdatensatz die Scheinnummer


def test_ansicht_filter_und_nummernfolge(node_exe, index_html):
    for name, (filt, erwartet) in _FAELLE.items():
        r = _lauf(node_exe, index_html, "ansicht", filt)
        assert _nummern(r) == erwartet, name
        assert r["bildschirm"] == len(r["rows"]), name + ": Datei-Zeilen != Bildschirmliste"
        assert r["titel"].endswith("Aktuelle Ansicht (%d)" % len(erwartet)), r["titel"]
        assert r["api"] == 0, name + ": Vollabruf API.exportOffa wieder da"


def test_ansicht_voller_text(node_exe, index_html):
    r = _lauf(node_exe, index_html, "ansicht", {"filterMonteur": "m1"})
    texte = [z[8] for z in r["rows"]]
    voll = LANG.replace("\n", " ")
    assert texte.count(voll) == 2, texte
    assert any(";" in t for t in texte), "Semikolon im Ansichts-Export verschluckt"


def test_bisherige_option_kuerzt_weiter(node_exe, index_html):
    """Bytegleichheit der alten Optionen ist im Byte-Protokoll belegt - hier der Riegel im Test."""
    r = _lauf(node_exe, index_html, "alle", {"filterMonteur": "m1"})
    assert len(r["rows"]) == len(_AS), "'Alle' darf die Bildschirmfilter nicht anwenden"
    assert [z[1] for z in r["rows"]] == [a["nummer"] for a in _AS], "'Alle' bleibt in Ladereihenfolge"
    t = [z[8] for z in r["rows"]]
    assert all(len(x) <= 80 for x in t) and (LANG.replace("\n", " ").replace(";", " ")[:80]) in t
    assert r["api"] == 0
    r = _lauf(node_exe, index_html, "offen_bearb", {})
    assert {z[5] for z in r["rows"]} <= {"aufgenommen", "freigegeben", "in Bearbeitung", "aufgeschoben"}
    assert r["datei"].startswith("OFFA_Export_Offen (alle)_")


def test_toter_zweig_fertig_weg_und_menue(index_html):
    ex = _teile(index_html)[0]
    assert 'statusFilter==="fertig"' not in ex and "Erledigt/Abgerechnet" not in ex
    assert "API.exportOffa" not in ex
    assert "exportOffa: function() { return _sbGet(\"arbeitsscheine\"); }," in index_html, "API-Eintrag bleibt"
    assert '[["ansicht","Aktuelle Ansicht ("+sorted.length+(sorted.length===1?" Schein)":" Scheine)")],' in index_html
    # das Menue bietet genau diese Schluessel - "fertig" nie
    m = re.search(r'\[\["ansicht",.*?\]\]\.map\(\(\[k,l\]\)=>React\.createElement\(\'button\',\{key:k,onClick:\(\)=>exportOffa\(k\)',
                  index_html)
    assert m and '"fertig"' not in m.group(0)
    assert index_html.count("exportOffa(") == 1  # nur der Menue-Aufruf; Definition ist "exportOffa=(", API-Methode "exportOffa:"


# ── Umkehrproben: jede Eigenschaft muss an ihrer Stelle haengen ─────────────
def test_umkehr_ohne_nummernsortierung(node_exe, index_html):
    alt = '_ansicht?[...sorted].sort((x,y)=>String(x.nummer||"").localeCompare(String(y.nummer||""),"de",{numeric:true})):'
    assert alt in index_html
    r = _lauf(node_exe, index_html.replace(alt, "_ansicht?sorted:", 1), "ansicht", {})
    assert _nummern(r) != _FAELLE["ohne"][1]


def test_umkehr_mit_kuerzung(node_exe, index_html):
    alt = 'const _asTxt=t=>_ansicht?String(t||"").replace(/\\r?\\n/g," "):'
    assert alt in index_html
    r = _lauf(node_exe, index_html.replace(alt, "const _asTxt=t=>false?0:", 1), "ansicht", {"filterMonteur": "m1"})
    assert LANG.replace("\n", " ") not in [z[8] for z in r["rows"]]


def test_umkehr_filter_monteur_fehlt(node_exe, index_html):
    alt = 'if(filterMonteur!=="alle"&&a.monteur!==filterMonteur) return false;'
    assert alt in index_html
    r = _lauf(node_exe, index_html.replace(alt, "", 1), "ansicht", {"filterMonteur": "m1"})
    assert _nummern(r) != _FAELLE["monteur"][1]
