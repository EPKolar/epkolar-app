# -*- coding: utf-8 -*-
"""v1016 Sammel-Auftrag des Geschaeftsfuehrers.

A1 Regiebericht: "0,5" h Fahrzeit wurde von parseFloat als 0 gelesen - die Gesamt-Zeile (abrechnungsrelevant)
   unterschlug sie. EIN Komma-Leser _dezKomma fuer Stunden und Fahrzeit.
A2 Arbeitsschein-Druckbild: Kopf/QR ueberdeckten "Arbeitsschein", Logo war ein "K"-Platzhalter, "Durchgefuehrte
   Arbeiten" trug einen blauen Rahmen. NUR Layout - Felder, Reihenfolge, Texte bleiben (hier gepinnt).
A3 Plan-Report: Legendenkopf Markengruen (der Wortlaut-Test v854 ist nachgezogen).
A4 Excel (nicht OFFA): Kennungen (Kundennummer, PLZ, ...) bleiben TEXT - entschieden ueber die Kopfzeile oder
   opts.textCols, nicht ueber den Wert. Stunden/Datum bleiben Zahl/Datum. OFFA unberuehrt.
B  OFFA-Hinweis "N offene Scheine evtl. in OFFA abgeschlossen" war ein Fehlalarm (Prod-DB: juprowa_sync_at zuletzt
   vor 2 Minuten). Er kommt nur noch, wenn das GLOBALE max(juprowa_sync_at) aelter als 7 Tage ist.
C  Datanorm: Haendlerkarte zeigt ehrlich "Letzter Sync <Datum>, <n> Artikel"; keine "nie eingerichtet"-Texte mehr.
"""
import json
import re

from conftest import run_node_snippet, _extract_fn
from test_exporte_ci_v1016 import _STUBS, _GENXLS_START, _GENXLS_END


def _zeile_mit(src, anfang):
    i = src.index(anfang)
    return src[i:src.index("\n", i)]


# ── A1 Regiebericht: Komma ─────────────────────────────────────────────────
def _dez_lauf(node_exe, quelle):
    js = quelle + r"""
const F=[["0,5"],["1,25"],["2"],[""],["0.5"],[null],[undefined],[3],["abc"],[" 1,5 "],["1.234,5"]];
process.stdout.write(JSON.stringify(F.map(f=>_dezKomma(f[0]))));"""
    return json.loads(run_node_snippet(node_exe, js))


def test_komma_parser_liest_dezimalkomma(index_html, node_exe):
    q = _zeile_mit(index_html, "function _dezKomma(")
    assert _dez_lauf(node_exe, q) == [0.5, 1.25, 2, 0, 0.5, 0, 0, 3, 0, 1.5, 1234.5]


def test_umkehrprobe_parsefloat_verliert_das_komma(node_exe):
    alt = "function _dezKomma(v){return parseFloat(v)||0;}"
    r = _dez_lauf(node_exe, alt)
    assert r[0] == 0 and r[1] == 1, "der alte Weg muss am Komma scheitern - sonst prueft der Test nichts"


def test_regiebericht_summen_nutzen_den_komma_parser(index_html):
    a = index_html.index('if(type==="regie"){')
    blk = index_html[a:index_html.index("<tbody>", a)]
    assert "_dezKomma(r.stunden)" in blk and "_dezKomma(r.fahrzeit)" in blk
    assert "parseFloat(r.stunden)" not in blk and "parseFloat(r.fahrzeit)" not in blk


def test_regiebericht_gesamtzeile_rechnet_komma_mit(index_html, node_exe):
    """Die echten zwei Summen-Zeilen aus printForm laufen in node."""
    a = index_html.index('if(type==="regie"){')
    blk = index_html[a:index_html.index("body=`", a)]
    zeilen = [z for z in blk.split("\n") if "const totalStd=" in z or "const totalFz=" in z]
    assert len(zeilen) == 2
    js = (_zeile_mit(index_html, "function _dezKomma(") + "\n" + _extract_fn(index_html, "_optionalChain") + "\n" + r"""
const d={personal:[{name:"A",stunden:"4",fahrzeit:"0,5"},{name:"B",stunden:"3,5",fahrzeit:"0.5"}]};
""" + "\n".join(zeilen) + "\nprocess.stdout.write(JSON.stringify([totalStd,totalFz]));")
    assert json.loads(run_node_snippet(node_exe, js)) == [7.5, 1.0]


# ── A2 Arbeitsschein-Druckbild ─────────────────────────────────────────────
def _as_druck(src):
    a = src.index("const genAsPdf=(a)=>{")
    return src[a:src.index('<div class="print-bar no-print">', a)]


def test_arbeitsschein_logo_statt_k_und_kein_blau(index_html):
    h = _as_druck(index_html)
    assert 'class="logo-k"' not in h and ">K</div>" not in h, "K-Platzhalter steht noch im Kopf"
    assert '<img class="logo-img" src="${LOGO_MD}"' in h
    assert "#3b82f6" not in h, "blauer Rahmen/Titel um Durchgefuehrte Arbeiten"
    assert ".work-box{border:1px solid #ddd;" in h
    # Kopf: Titel und QR teilen sich einen Block mit Abstand (kein Ueberdecken)
    assert '<div class="hdr-r">' in h and ".hdr-r{display:flex;" in h and "white-space:nowrap" in h


def test_arbeitsschein_felder_und_reihenfolge_unveraendert(index_html):
    """NUR Layout: die Feld-Beschriftungen in ihrer Reihenfolge sind der Inhalt des Scheins."""
    h = _as_druck(index_html)
    labels = re.findall(r'field-label">([^<]+):</span>', h)
    assert labels == ["Kd-Nr", "Name", "Adresse", "Ort", "Kontakt", "Störungsmelder", "Art", "Priorität",
                      "Verrechnung", "Projekt-Nr", "Monteur", "Sachbearbeiter", "Aufgenommen", "Termin",
                      "Vorschlag", "Dauer", "Fahrzeit", "Arbeitszeit", "Gesamtzeit", "Erstellt"], labels
    titel = re.findall(r'class="(?:work-title|box-title)">([^<]+)<', h)
    assert titel[:5] == ["Auftraggeber / Kunde", "Auftragsdaten", "Termine",
                         "Arbeitsanweisungen / Durchzuführende Arbeiten", "Durchgeführte Arbeiten"], titel
    for t in ("<h1>Arbeitsschein</h1>", "Andreas Kolar &amp; Sohn GesmbH", "Unterschrift Monteur / Techniker",
              "Unterschrift Auftraggeber / Kunde", "Allgemeine Geschäftsbedingungen (Auszug)"):
        assert t in h, t


# ── A3 Plan-Report ────────────────────────────────────────────────────────
def test_planreport_legendenkopf_markengruen(index_html):
    a = index_html.index("const _legCols=()=>{")
    k = index_html[a:index_html.index("};", a)]
    assert "doc.setFillColor(0,150,64)" in k and "setFillColor(238,238,238)" not in k
    assert k.index("setTextColor(255,255,255)") < k.index('doc.text("Nr"') < k.index("setTextColor(20,20,20)")


# ── A4 Excel: Kennungen bleiben Text ───────────────────────────────────────
_KOPF = "['Nr','Kundennr','Kunde','PLZ','Stunden','Datum','Kd-Nr','Art.-Nr.','Telefon']"
_ROWS = r"""[[1,"00123","4711","01067",8,"05.10.2026","10234","12345","22792361"],
 [2,"10234","Groß","3470",7.5,"2026-10-06","00999","4711","0664123"]]"""


def _xls(node_exe, src, titel, opts="{sumCol:4,textCols:[2]}"):
    i = src.find(_GENXLS_START)
    j = src.find(_GENXLS_END, i)
    q = src[i: j + len(_GENXLS_END)] + "\n};"
    aufruf = "genXls(%s,'U',%s,%s,'t.xls',%s);" % (json.dumps(titel), _KOPF, _ROWS, opts)
    return run_node_snippet(node_exe, _STUBS + q + aufruf + "process.stdout.write(CAPTURED.text);")


def _ohne_kennung(src):
    alt = "    if(_txtCol[ci])return '<td style=\"'+style+'\">'+_xBr(esc(cs))+'</td>';\n"
    assert alt in src
    return src.replace(alt, "", 1)


def test_kennungen_bleiben_text_werte_bleiben_zahl(index_html, node_exe):
    x = _xls(node_exe, index_html, "Kunden – Test")
    for kenn in ("00123", "01067", "3470", "10234", "00999", "12345", "22792361", "0664123"):
        assert 'x:num="%s"' % kenn not in x, kenn
        assert ">%s<" % kenn in x, kenn
    assert 'x:num="4711"' not in x, "opts.textCols greift nicht"
    assert 'x:num="8"' in x and 'x:num="7.5"' in x, "Stunden muessen Zahl bleiben"
    assert 'class="xd" x:num="46300"' in x, "Datum muss Datum bleiben"
    assert 'class="xn" x:num="1"' in x, "die laufende Nr ist keine Kennung"


def test_umkehrprobe_ohne_kennung_wird_plz_zur_zahl(index_html, node_exe):
    x = _xls(node_exe, _ohne_kennung(index_html), "Kunden – Test")
    assert 'x:num="3470"' in x and 'x:num="10234"' in x


def test_offa_zweig_von_der_kennung_unberuehrt(index_html, node_exe):
    """OFFA-Titel: die Ausgabe ist mit und ohne die Kennungs-Logik byte-gleich."""
    t = "\U0001F4CB OFFA Export — Alle (2)"
    assert _xls(node_exe, index_html, t) == _xls(node_exe, _ohne_kennung(index_html), t)


def test_kennung_nach_kopfzeile(index_html, node_exe):
    i = index_html.index("const _XKENN=")
    q = index_html[i:index_html.index("\n", index_html.index("const _xKennung=", i))]
    js = r"""const _xOhneEmoji=s=>String(s);""" + q + r"""
const K=["Kundennr","Kd-Nr","KdNr","PLZ","Postleitzahl","PLZ/Ort","Telefon","Tel.","ArtNr","Art.-Nr.","Inventar-Nr","Seriennr","Nummer","Nr.","Matchcode","Kennzeichen"];
const W=["Nr","Stunden","Datum","Menge","Betrag €","km","Wert €","Kunde","Ort","Status","Baujahr","Fortschritt"];
process.stdout.write(JSON.stringify({k:K.filter(h=>!_xKennung(h)),w:W.filter(h=>_xKennung(h))}));"""
    r = json.loads(run_node_snippet(node_exe, js))
    assert r == {"k": [], "w": []}, r


# ── B OFFA-Hinweis: Feed-Gesundheit global ─────────────────────────────────
def _b_quelle(src):
    a = src.index("var OFFA_VERWAIST_TAGE=")
    e = src.index("if(typeof window!=='undefined')window._offaFeedStand=_offaFeedStand;", a)
    komp = [_zeile_mit(src, "  const _offaFeed=(()=>{"), _zeile_mit(src, "  const _isVerwaist=(a)=>{")]
    return src[a:e], "\n".join(komp)


_B_LAUF = r"""
var AS_GRP_OFFEN=["aufgenommen","freigegeben","in_bearbeitung","aufgeschoben"];
var window={};
%s
window._isOffaVerwaist=_isOffaVerwaist;window._offaFeedStand=_offaFeedStand;
var DAY=864e5,NOW=Date.now();
function iso(ms){return new Date(ms).toISOString();}
function zaehle(arbeitsscheine,_lastJupPull){%s
 return {zustand:_offaFeed.zustand,n:arbeitsscheine.filter(_isVerwaist).length};}
var alt={juprowa_id:"J1",scheinstatus:"in_bearbeitung",juprowa_sync_at:iso(NOW-30*DAY)};
var r={
 frisch:zaehle([alt,{juprowa_id:"J2",scheinstatus:"erledigt",juprowa_sync_at:iso(NOW-2*60000)}],NOW-60000),
 still:zaehle([alt,{juprowa_id:"J2",scheinstatus:"erledigt",juprowa_sync_at:iso(NOW-10*DAY)}],NOW-60000),
 ohneStempel:zaehle([{juprowa_id:"J1",scheinstatus:"in_bearbeitung",juprowa_sync_at:""},{juprowa_id:"J2",scheinstatus:"in_bearbeitung"}],NOW-60000),
 leer:zaehle([],NOW-60000)
};
process.stdout.write(JSON.stringify(r));"""


def test_offa_hinweis_nur_wenn_der_feed_global_steht(index_html, node_exe):
    fn, komp = _b_quelle(index_html)
    r = json.loads(run_node_snippet(node_exe, _B_LAUF % (fn, komp)))
    assert r["frisch"] == {"zustand": "frisch", "n": 0}, "frischer Feed darf nicht warnen (Fehlalarm)"
    assert r["still"] == {"zustand": "still", "n": 1}, "Feed >7 Tage still muss warnen"
    assert r["ohneStempel"] == {"zustand": "unbekannt", "n": 0}, "ohne Stempel: ehrlich unbekannt, kein Alarm"
    assert r["leer"] == {"zustand": "unbekannt", "n": 0}


def test_umkehrprobe_ohne_globales_max_kommt_der_fehlalarm(index_html, node_exe):
    fn, komp = _b_quelle(index_html)
    alt = komp.replace('_offaFeed.zustand==="still"&&', "", 1)
    assert alt != komp
    r = json.loads(run_node_snippet(node_exe, _B_LAUF % (fn, alt)))
    assert r["frisch"]["n"] == 1, "der alte Einzel-Schein-Weg muss den Fehlalarm zeigen"


def test_offa_hinweis_text_und_unbekannt_zeile(index_html):
    assert '(_verwaisteN>0&&canSync)&&React.createElement' in index_html
    assert 'canSync&&_offaFeed.zustand==="unbekannt"' in index_html
    assert "Zustand unbekannt, keine Warnung." in index_html


def test_ladeabbild_reicht_juprowa_sync_at_durch(index_html, node_exe):
    i = index_html.index("function _mapArbeitsschein(a){")
    fn = index_html[i:index_html.index("\n}\n", i) + 2]
    js = "function _jp(x){return x;}\n" + fn + r"""
const m=_mapArbeitsschein({id:"x",juprowa_id:"J1",juprowa_sync_at:"2026-11-16T09:58:00Z",scheinstatus:"in_bearbeitung"});
process.stdout.write(String(m.juprowa_sync_at));"""
    assert run_node_snippet(node_exe, js) == "2026-11-16T09:58:00Z"


# ── C Datanorm ─────────────────────────────────────────────────────────────
def _c_lauf(node_exe, src):
    q = "\n".join(_zeile_mit(src, n) if n.startswith("function _suppT") else
                  src[src.index(n):src.index("\n}\n", src.index(n)) + 2]
                  for n in ("function _suppTausender(", "function _supplierSyncText("))
    js = q + r"""
process.stdout.write(JSON.stringify([
 _supplierSyncText({last_sync:"2026-04-12T08:00:00Z",last_sync_status:"success",last_sync_articles:25000}),
 _supplierSyncText({last_sync:"2026-04-12T08:00:00Z",last_sync_status:"success",last_sync_articles:null}),
 _supplierSyncText({last_sync:"2026-04-12T08:00:00Z",last_sync_status:"error",last_sync_articles:0}),
 _supplierSyncText({last_sync:null}),
 _supplierSyncText({last_sync:"2026-04-12T08:00:00Z",last_sync_articles:1234567})]));"""
    return json.loads(run_node_snippet(node_exe, js))


def test_haendlerkarte_letzter_sync_mit_artikeln(index_html, node_exe):
    assert _c_lauf(node_exe, index_html) == [
        "Letzter Sync 12.04.2026, 25.000 Artikel", "Letzter Sync 12.04.2026",
        "Letzter Sync-Versuch 12.04.2026 fehlgeschlagen", "Kein Sync-Stand",
        "Letzter Sync 12.04.2026, 1.234.567 Artikel"]
    assert "const lastSync=_supplierSyncText(s);" in index_html
    f = index_html[index_html.index("function _supplierSyncText("):]
    f = f[:f.index("\n}\n")]
    assert "password" not in f and "username" not in f and "console." not in f


def test_haendlerkarte_ohne_nie_platzhalter(index_html):
    assert ':"nie";' not in index_html[index_html.index('adminTab==="haendler"&&('):][:60000]


def test_keine_nie_eingerichtet_texte(index_html, repo_root):
    import os
    assert "noch nicht eingerichtet" not in index_html
    assert "dann loeschte JEDES Bearbeiten" not in index_html
    doku = open(os.path.join(repo_root, "sql", "DEPLOY_sync_supplier_v3.md"), encoding="utf-8").read()
    assert "12.04.2026" in doku and "25.000 Artikel" in doku and "5 von 9" in doku
    ts = open(os.path.join(repo_root, "supabase", "functions", "supplier-sync", "index.ts"), encoding="utf-8").read()
    assert "obwohl nie etwas geladen wurde" not in ts and "12.04.2026" in ts


def test_umkehrprobe_layout_und_karten_riegel(index_html):
    """Die String-Riegel aus A2/A3/C schlagen an, wenn der alte Stand zurueckkommt."""
    h = _as_druck(index_html)
    alt_as = h.replace('<img class="logo-img" src="${LOGO_MD}" alt="EP: Kolar &amp; Sohn">', '<div class="logo-k">K</div>', 1) \
              .replace('<div class="work-box">\n    <div class="work-title">Durchgeführte Arbeiten</div>',
                       '<div class="work-box" style="border-color:#3b82f6">\n    <div class="work-title" style="color:#3b82f6">Durchgeführte Arbeiten</div>', 1)
    assert alt_as != h and 'class="logo-k"' in alt_as and "#3b82f6" in alt_as
    a = index_html.index("const _legCols=()=>{")
    k = index_html[a:index_html.index("};", a)]
    assert "setFillColor(238,238,238)" in k.replace("setFillColor(0,150,64)", "setFillColor(238,238,238)")
    alt_karte = index_html.replace("const lastSync=_supplierSyncText(s);",
                                   'const lastSync=s.last_sync?"x":"nie";', 1)
    assert ':"nie";' in alt_karte[alt_karte.index('adminTab==="haendler"&&('):][:60000]
