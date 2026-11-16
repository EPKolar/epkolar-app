"""v1016 Exporte: CI und Funktion der Exportdateien.

AUFTRAG (Geschaeftsfuehrer): "alle export file auch checken, muss sauberes ci haben und funktionieren".

GEMESSEN (Harnisch: jede Datei offline erzeugt, PDF zu PNG gerendert, Excel-Dateien mit ECHTEM Excel
geoeffnet und als xlsx gespeichert, dann Zellen gelesen):
  * Excel: ganze Zahlen ('8' Stunden) standen als TEXT neben 7,5 als Zahl - =SUMME ueber die
    Stundenspalte ergab 13,75 statt der exportierten 25,75. Datum war Text. Titel trug das Emoji des
    Aufrufers, der Blattname verlor jeden Umlaut ('Mngelliste'), keine fixierte Kopfzeile.
  * PDF: sechs jsPDF-Belege mit je eigenem gruenem Vollbalken, nur einer mit Logo; Fahrtenbuch ohne
    Fuss/Seitenzahl, Kopf "EP KOLAR", Adressen mit "..." abgeschnitten; Checkliste und Bautagebuch
    schnitten Projektzeile/Bauvorhaben ab.
  * Druckfenster: Emojis auf dem Papier (Regiebericht-Titel, Maengel-Report, Warenkorb, Monatszettel).

HARTE GRENZE: der OFFA-Excel-Export laeuft ueber denselben Erzeuger genXls und muss BYTE-GLEICH bleiben.
"""
import re
import json

import pytest

from conftest import run_node_snippet, _extract_fn

_GENXLS_START = "// ═══ EP Kolar CI Excel Export ═══"
_GENXLS_END = '_16("\U0001F4CA Excel exportiert: "+filename)]);'

_STUBS = r"""
function _nullishCoalesce(a,f){return (a===null||a===undefined)?f():a;}
function _optionalChain(ops){let l=0,v=ops[0],s;while(l<ops.length){const op=ops[l+1],fn=ops[l+2];l+=3;
 if((op==='optionalAccess'||op==='optionalCall')&&(v===null||v===undefined))return undefined;
 if(op==='access'||op==='optionalAccess'){s=v;v=fn(v);}else if(op==='call'||op==='optionalCall'){v=fn((...a)=>v.call(s,...a));s=undefined;}}
 return v;}
function _n(v,d){const n=parseFloat(v);return (isNaN(n)||!isFinite(n))?(d!==undefined?(0).toFixed(d):0):d!==undefined?n.toFixed(d):n;}
var CF_HTML_LINE1="L1", CF_HTML_LINE2="L2", CF_HTML_AGB="AGB";
var COMPANY_FOOTER={name:"Andreas Kolar & Sohn GesmbH",web:"www.ep-kolar.at"};
var CAPTURED=null;
class Blob{constructor(parts,opts){this.parts=parts;this.type=opts&&opts.type;}}
function _dl(blob,filename){CAPTURED={text:blob.parts.join(""),type:blob.type,filename:filename};}
var window={};
"""

_ZEILEN = r"""[[1,"05.10.2026","Huber Markus",8,"0012","10234"],
 [2,"2026-09-01","Öztürk Ümit",7.5,"PA-2026-118","10871"]]"""


def _genxls(node_exe, index_html, titel):
    i = index_html.find(_GENXLS_START)
    j = index_html.find(_GENXLS_END, i)
    assert i >= 0 and j >= 0, "genXls-Anker veraltet"
    quelle = index_html[i: j + len(_GENXLS_END)] + "\n};"
    aufruf = "genXls(%s,'Untertitel',['Nr','Datum','Name','Stunden','Inventar','KdNr'],%s,'t.xls',{sumCol:3});" % (
        json.dumps(titel), _ZEILEN)
    return run_node_snippet(node_exe, _STUBS + quelle + aufruf + "process.stdout.write(CAPTURED.text);")


@pytest.fixture(scope="module")
def xls_ci(node_exe, index_html):
    return _genxls(node_exe, index_html, "⏱️ Zeiterfassung — Mängelliste")


@pytest.fixture(scope="module")
def xls_offa(node_exe, index_html):
    return _genxls(node_exe, index_html, "\U0001F4CB OFFA Export — Alle (2)")


# ── Excel: Zahlen und Datum ─────────────────────────────────────────────────
def test_ganze_zahl_ist_eine_zahl(xls_ci):
    """'8' Stunden muss summierbar sein - sonst laesst =SUMME sie aus."""
    assert 'x:num="8"' in xls_ci, "Ganze Stundenzahl steht weiter als Text in der Datei."
    assert 'x:num="7.5"' in xls_ci, "Dezimalzahl verliert x:num (v3.9.880-Riegel)."


def test_fuehrende_null_bleibt_text(xls_ci):
    assert 'x:num="0012"' not in xls_ci and ">0012<" in xls_ci, (
        "'0012' (Inventarnummer) wurde zur Zahl - die fuehrende Null ginge verloren.")


def test_datum_ist_echtes_excel_datum(xls_ci):
    """05.10.2026 = Excel-Seriennummer 46300, 2026-09-01 = 46266; angezeigt TT.MM.JJJJ."""
    assert 'class="xd" x:num="46300"' in xls_ci, "TT.MM.JJJJ wird nicht als Datum geschrieben."
    assert 'class="xd" x:num="46266"' in xls_ci, "JJJJ-MM-TT wird nicht als Datum geschrieben."
    assert ">01.09.2026<" in xls_ci, "ISO-Datum wird nicht in TT.MM.JJJJ angezeigt."
    assert 'td.xd{mso-number-format:"dd\\.mm\\.yyyy";}' in xls_ci, "Datumsformat fehlt im Stil."


def test_titel_ohne_emoji_blattname_mit_umlaut(xls_ci):
    assert "⏱" not in xls_ci and "️" not in xls_ci, "Emoji des Aufrufers steht in der Datei."
    m = re.search(r"<x:Name>(.*?)</x:Name>", xls_ci)
    assert m and "Mängelliste" in m.group(1), "Blattname verliert Umlaute: %r" % (m and m.group(1))


def test_kopfzeile_fixiert(xls_ci):
    """Zeile 5 ist der Spaltenkopf unter dem 4-zeiligen Briefkopf (mit Excel gemessen: freeze A6)."""
    assert "<x:FreezePanes/>" in xls_ci and "<x:SplitHorizontal>5</x:SplitHorizontal>" in xls_ci


def test_zebra_neutral(xls_ci):
    assert "#e8f5e9" not in xls_ci and "#f0f7f2" not in xls_ci, "Gruen-Toenung in Datenzellen."


# ── OFFA: unveraendert ──────────────────────────────────────────────────────
def test_offa_export_bleibt_beim_alten_format(xls_offa):
    """Harte Grenze. Fuer den OFFA-Titel gilt KEINE der Aenderungen."""
    assert "<x:FreezePanes/>" not in xls_offa
    assert 'x:num="10234"' not in xls_offa and 'x:num="8"' not in xls_offa
    assert 'class="xd"' not in xls_offa and "td.xd" not in xls_offa
    assert "\U0001F4CB OFFA Export" in xls_offa, "OFFA-Titel veraendert."
    assert "#e8f5e9" in xls_offa, "OFFA-Zellfarben veraendert."


def test_umkehrprobe_offa_weiche_trennt(xls_ci, xls_offa):
    """Ohne Weiche saehen beide Dateien gleich typisiert aus - dann waere der OFFA-Riegel wertlos."""
    assert 'x:num="10234"' in xls_ci and 'x:num="10234"' not in xls_offa


def test_offa_aufruf_traegt_den_weichen_titel(index_html):
    """Die Weiche erkennt den OFFA-Export an seinem Titel. Aendert jemand den Titel, muss dieser Test rot werden."""
    assert 'genXls("\U0001F4CB OFFA Export — "+lbl+' in index_html
    assert 'const _xCI=t=>String(t).indexOf("\\uD83D\\uDCCB OFFA Export")!==0;' in index_html


# ── PDF: ein CI-Kopf ────────────────────────────────────────────────────────
_GENERATOREN = ["_genTicketPdf", "_genPlanReportPdf", "_genChecklistPdf", "_genBautagPdf", "_pzePdf"]


def test_alle_jspdf_belege_nutzen_den_ci_kopf(index_html):
    for name in _GENERATOREN:
        fn = _extract_fn(index_html, name)
        assert fn, name + " nicht gefunden"
        assert "_pdfCIKopf(doc," in fn, name + " zeichnet keinen CI-Kopf."
        assert not re.search(r"doc\.rect\(0,0,PW,2\d", fn), name + " zeichnet weiter den gruenen Vollbalken."
    m = re.search(r"const exportFahrtenPdf=function\(\)\{.*?\n  \};", index_html, re.S)
    assert m, "exportFahrtenPdf nicht gefunden"
    fb = m.group(0)
    assert "_pdfCIKopf(doc," in fb and "_pdfCIFuss(doc," in fb, "Fahrtenbuch ohne CI-Kopf/-Fuss."
    assert "doc.text('EP KOLAR" not in fb, "Fahrtenbuch-Kopf schreibt wieder 'EP KOLAR'."
    assert "slice(0,platz-1)+'…'" not in fb, "Fahrtenbuch schneidet Adressen wieder ab."


_DOC_ATTRAPPE = r"""
var LOG=[];
var doc={internal:{pageSize:{getWidth:function(){return 210;},getHeight:function(){return 297;}}},
 getImageProperties:function(){return {width:300,height:100};},addImage:function(){LOG.push(['img']);},
 setTextColor:function(){},setFont:function(){},setFontSize:function(){},setLineWidth:function(){},
 setDrawColor:function(r,g,b){LOG.push(['draw',r,g,b]);},setFillColor:function(r,g,b){LOG.push(['fill',r,g,b]);},
 rect:function(){LOG.push(['rect'].concat([].slice.call(arguments)));},line:function(){LOG.push(['line']);},
 splitTextToSize:function(t){return [t];},text:function(t){LOG.push(['text',t]);},
 getNumberOfPages:function(){return 2;},setPage:function(){}};
var LOGO_MD="x";var COMPANY_FOOTER={name:"Andreas Kolar & Sohn GesmbH",addr:"A",phone:"P",web:"W",fn:"FN",fnCourt:"LG",uid:"U"};
function fdt(){return "16.11.2026";} function td2(){return "2026-11-16";}
"""


def _kopf_lauf(node_exe, index_html, titel):
    pdfstr = re.search(r"function _pdfStr\(s\)\{return.*?\.trim\(\);\}", index_html, re.S).group(0)
    kopf = _extract_fn(index_html, "_pdfCIKopf")
    fuss = _extract_fn(index_html, "_pdfCIFuss")
    assert kopf and fuss, "_pdfCIKopf/_pdfCIFuss fehlen"
    js = _DOC_ATTRAPPE + pdfstr + kopf + fuss + (
        "_pdfCIKopf(doc,%s,'Unter');_pdfCIFuss(doc,'Z');process.stdout.write(JSON.stringify(LOG));" % json.dumps(titel))
    return json.loads(run_node_snippet(node_exe, js))


def test_ci_kopf_logo_markengruen_latin1(node_exe, index_html):
    log = _kopf_lauf(node_exe, index_html, "Fahrtenbuch — Prüfung")
    assert ["img"] in log, "Kein Logo im Kopf."
    assert ["draw", 0, 150, 64] in log, "Akzentlinie nicht Markengruen #009640."
    farben = [e[1:] for e in log if e[0] in ("fill", "draw")]
    for f in farben:
        assert f in ([0, 150, 64], [0, 0, 0]), "Fremdfarbe im Kopf: %r" % (f,)
    texte = [e[1] for e in log if e[0] == "text"]
    assert "Seite 1 von 2" in texte and "Seite 2 von 2" in texte, "Fuss ohne 'Seite x von y'."
    assert any("Erstellt am 16.11.2026" in t for t in texte), "Fuss ohne Erstelldatum."
    for t in texte:
        assert all(ord(c) <= 0xFF for c in t), "Nicht-WinAnsi-Zeichen im PDF-Text: %r" % t


def test_umkehrprobe_emoji_im_titel_landet_nicht_im_pdf(node_exe, index_html):
    log = _kopf_lauf(node_exe, index_html, "\U0001F4C4 Bericht € 5")
    texte = [e[1] for e in log if e[0] == "text"]
    assert "Bericht EUR 5" in texte, "Titel nicht ueber _pdfStr gefuehrt: %r" % texte


# ── Druckfenster: keine Emojis auf dem Papier ───────────────────────────────
_EMO = re.compile("[\U0001F000-\U0001FAFF⌀-⏿☀-⛿✅✔✖❌]")


def _papier_emojis(text):
    """Emojis ausserhalb von Toast-Aufrufen (Toast-Texte sind laut Auftrag tabu)."""
    rest = re.sub(r"__toast[^;]*;|_showToast[^;]*;", "", text)
    return _EMO.findall(rest)


def test_druckfenster_ohne_emoji(index_html):
    stellen = {
        "printForm": _extract_fn(index_html, "printForm"),
        "genMangelPdf": re.search(r"const genMangelPdf=\(\)=>\{.*?\n  \};", index_html, re.S).group(0),
        "druckAnsicht": re.search(r"const druckAnsicht=async\(z\)=>\{.*?\n  \};", index_html, re.S).group(0),
        "exportMonat": re.search(r"const exportMonat=\(\)=>\{.*?\n  \};", index_html, re.S).group(0),
        "printLabels": re.search(r"const printLabels=\(items,title\)=>\{.*?\n\};", index_html, re.S).group(0),
    }
    for name, body in stellen.items():
        assert body, name + " nicht gefunden"
        # printForm: die Formular-Reiter (tabs) danach sind Bildschirm, nicht Papier
        if name == "printForm":
            body = body.split("const tabs=")[0]
        # Ankreuzfelder (U+2610/U+2611) sind Formularsymbole, kein Schmuck
        gefunden = [c for c in _papier_emojis(body) if c not in "☐☑"]
        assert not gefunden, "%s druckt Emojis: %r" % (name, gefunden)
    assert "\U0001F6D2 Material-Warenkorb" not in index_html


def test_umkehrprobe_emoji_suche_greift():
    assert _papier_emojis('<div class="title">\U0001F4CB Regiebericht</div>')
    assert not _papier_emojis('window.__toast("⚠️ Popup blockiert");')
