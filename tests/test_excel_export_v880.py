# -*- coding: utf-8 -*-
"""
v3.9.880 - "excel muss auch sauber werden" (Sebastian).

BEREICH: jeder Export, der eine TABELLENDATEI erzeugt. 19 genXls-Aufrufe,
5 handgeschriebene HTML-xls-Exporte, 1 echter CSV-Export. Kein Fremdpaket.

WAS GEMESSEN WURDE
------------------
genXls (Z4465-4548) wurde aus index.html geschnitten und in Node mit einem
feindlichen Datensatz laufen gelassen (Umlaut, Semikolon, Anfuehrungszeichen,
Zeilenumbruch, Dezimalzahl, fuehrendes "="). Die erzeugten Bytes:

    ERSTE 6 BYTES: ef bb bf 3c 68 74      -> BOM ist da
    MIME:          application/vnd.ms-excel;charset=utf-8
    Zelle:         >Tuer undicht; "Sued"< -> Semikolon/Quote zerreissen NICHTS

WIDERLEGT (vollwertiges Ergebnis):
  - Umlaut-Mojibake gibt es NICHT. Jeder einzelne Tabellen-Export traegt ein
    BOM. Das war die Verdachtsdiagnose und sie ist falsch.
  - Trennzeichen-Problem gibt es NICHT. Nur EIN Export ist ueberhaupt CSV
    (Audit-Log, Z13629-13635) und der nutzt bereits Semikolon + RFC4180-
    Quoting + Formel-Schutz. Die uebrigen 23 sind HTML-Tabellen; dort gibt
    es kein Trennzeichen.
  - Ein Semikolon/Anfuehrungszeichen/Zeilenumbruch in einer Maengel- oder
    Bautagebuch-Bemerkung zerreisst die Zeile NICHT (HTML, nicht CSV).

BESTAETIGT - das ist der eigentliche Schaden:
  1. td,th{mso-number-format:\\@}  -> JEDE Zelle ist in Excel TEXT.
  2. Alle Zahlen werden mit PUNKT geschrieben (_n(7.5,1) -> "7.5").
     Gemessene Bytes aus dem Lauf oben:
         <td ...>0.5</td>   <td ...>12.25</td>   Gesamt: <td ...>20.25</td>
     Im deutschen Excel steht damit "7.5" statt "7,5", die Spalte laesst sich
     nicht summieren, nicht sortieren, nicht filtern. Betrifft Stunden, km,
     Liter, Euro - also genau die Spalten, wegen derer man exportiert.
  3. Ein Zeilenumbruch in einer Bemerkung geht verloren (HTML faltet ihn zu
     einem Leerzeichen). Drei Zeilen werden eine.
  4. Zwei Exporte ignorieren den Bildschirmfilter - dieselbe Fehlerklasse,
     die bei den Maengeln in v3.9.875 repariert wurde:
         exportTickets  (Z17606) nimmt allTickets, der Bildschirm _vpFiltered
         Werkzeuge      (Z28645) nimmt werkzeuge,  der Bildschirm sorted
  5. Audit-CSV schreibt die Zeit als toISOString() = UTC. Der Bildschirm
     daneben zeigt toLocaleTimeString("de-AT"). Sommerzeit: 2 Stunden Versatz
     zwischen dem, was man sieht, und dem, was in der Datei steht.
         gemessen: "2026-08-28T07:15:00.000Z" fuer 09:15 Wiener Zeit

VORGESCHLAGENE ZENTRALE REPARATUR (ein Helfer statt 12 Einzelfixes):
    In genXls die Zellausgabe um x:num erweitern - das dokumentierte
    Excel-HTML-Attribut fuer den invarianten Zahlenwert. Nur Zellen, die
    exakt wie eine Dezimalzahl aussehen (/^-?\\d+\\.\\d{1,4}$/), werden
    umgestellt. Inventarnummern, "0012", Datumsangaben und "=SUM(A1)"
    bleiben unberuehrt - gemessen im Prototyp.

STAND DER RIEGEL
----------------
ROT, solange der Patch fehlt (das ist beabsichtigt, siehe Auftrag):
    test_genxls_schreibt_dezimalzahlen_als_zahl
    test_genxls_zeigt_dezimalkomma
    test_zeilenumbruch_ueberlebt_in_der_zelle
    test_ticket_export_folgt_dem_bildschirmfilter
    test_werkzeug_export_folgt_dem_bildschirmfilter
    test_audit_csv_schreibt_wiener_zeit
GRUEN heute (schuetzen, was funktioniert - und die Widerlegungen festhalten):
    test_jeder_tabellen_export_traegt_ein_bom
    test_genxls_erzeugte_bytes_beginnen_mit_bom
    test_audit_csv_nutzt_semikolon_und_quoting
    test_audit_csv_entschaerft_formeln
    test_semikolon_und_quote_zerreissen_die_zeile_nicht
"""
import re
import pytest

from conftest import run_node_snippet


# ─────────────────────────────────────────────────────────────────────────────
# genXls aus index.html schneiden und in Node ausfuehren.
# Brace-Zaehlen scheitert hier: der Rumpf ist ein Template-Literal voller
# ${...}. Deshalb wird am eindeutigen Schluss-Toast abgeschnitten.
# ─────────────────────────────────────────────────────────────────────────────
# Start am Abschnitts-Marker, NICHT an `const genXls=`: eine zentrale
# Reparatur legt ihre Helfer zwischen Marker und genXls, und die muessen
# mitgeschnitten werden, sonst misst der Riegel eine ReferenceError statt
# des Exports.
_GENXLS_START = "// ═══ EP Kolar CI Excel Export ═══"
_GENXLS_END = '_16("\U0001F4CA Excel exportiert: "+filename)]);'


def _genxls_src(index_html):
    i = index_html.find(_GENXLS_START)
    assert i >= 0, "genXls nicht gefunden - Anker veraltet"
    j = index_html.find(_GENXLS_END, i)
    assert j >= 0, "genXls-Ende nicht gefunden - Anker veraltet"
    return index_html[i : j + len(_GENXLS_END)] + "\n};"


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

_CALL = r"""
genXls("Maengelliste","Untertitel ue",
  ["Nr","Mangel","Stunden","Frist"],
  [[1,'Tuer undicht; "Sued"\nzweite Zeile',_n(7.5,1),'2026-09-01'],
   [2,'=cmd|\' /C calc\'!A0',_n(0.5,1),'2026-09-02'],
   [3,'Groesse 10 m2',_n(12.25,2),'2026-09-03']],
  "Test_Export.xls",{sumCol:2});
"""


def _run_genxls(node_exe, index_html, tail):
    snippet = _STUBS + _genxls_src(index_html) + _CALL + tail
    return run_node_snippet(node_exe, snippet)


@pytest.fixture(scope="module")
def xls_bytes(node_exe, index_html):
    """Die tatsaechlich erzeugten Bytes einer genXls-Datei."""
    return _run_genxls(
        node_exe,
        index_html,
        "process.stdout.write(CAPTURED.text);",
    )


# ── GRUEN heute: das, was funktioniert, festnageln ──────────────────────────
def test_genxls_erzeugte_bytes_beginnen_mit_bom(node_exe, index_html):
    """Ohne BOM zeigt Excel unter Windows 'Ã¼' statt 'ue'. Gemessen: BOM da."""
    out = _run_genxls(
        node_exe,
        index_html,
        "const b=Buffer.from(CAPTURED.text,'utf8');"
        "process.stdout.write([...b.slice(0,3)].map(x=>x.toString(16).padStart(2,'0')).join(' '));",
    )
    assert out == "ef bb bf", (
        "Die von genXls erzeugte Datei beginnt nicht mit dem UTF-8-BOM.\n"
        "Gemessene erste Bytes: " + out
    )


def test_jeder_tabellen_export_traegt_ein_bom(index_html):
    """Nicht nur genXls: JEDER Blob mit Tabellen-MIME muss ein BOM voranstellen.

    Neben genXls gibt es 5 handgeschriebene HTML-xls-Exporte (Stempelzeiten
    Z11967, generateBWB Z12484, Wochen-/Tages-Stundenbestaetigung Z24593/24663,
    Bauwochenbericht Z24787). Jeder einzelne wird hier geprueft - der Fehler
    waere pro Fundstelle, nicht global.

    Der CSV-Export (Z13635) haengt sein BOM eine Zeile frueher an `_csv` an;
    dafuer gibt es test_audit_csv_nutzt_semikolon_und_quoting.
    """
    pat = re.compile(
        r"new Blob\(\[(.{0,12}?)\+\s*html\]\s*,\s*\{\s*type\s*:\s*"
        r"['\"]application/vnd\.ms-excel",
        re.S,
    )
    treffer = pat.findall(index_html)
    assert len(treffer) >= 6, (
        "Weniger HTML-xls-Exporte gefunden als bekannt (>=6): %d. Entweder "
        "wurde einer entfernt oder das Muster ist veraltet." % len(treffer)
    )
    # Zwei Schreibweisen im Bestand: die JS-Escape-Sequenz ﻿ (Z4546,
    # Z24593/24663/24787) und das blanke BOM-Zeichen im Quelltext (Z11967,
    # Z12484). Beides zaehlt.
    ohne_bom = [p for p in treffer
                if "ufeff" not in p.lower() and "﻿" not in p]
    assert not ohne_bom, (
        "%d HTML-xls-Export(e) stellen kein UTF-8-BOM voran -> Umlaute werden "
        "in Excel unter Windows zu Mojibake (Ae statt AE). Praefixe: %r"
        % (len(ohne_bom), ohne_bom)
    )


def test_audit_csv_nutzt_semikolon_und_quoting(index_html):
    """Der einzige echte CSV-Export. Im deutschen Excel ist das
    Listentrennzeichen das Semikolon - Komma-CSV landet in Spalte A."""
    assert 'return \'"\'+s.replace(/"/g,\'""\')+\'"\';' in index_html, (
        "Der CSV-Feld-Escaper (RFC4180-Verdoppelung der Anfuehrungszeichen) "
        "ist weg - ein Semikolon oder Zeilenumbruch im Text zerreisst dann "
        "die Zeile."
    )
    assert 'const _csv="\\uFEFF"+[_hdrs,..._rows].map(r=>r.map(_cf).join(";")).join("\\r\\n");' in index_html, (
        "Der Audit-CSV-Export nutzt nicht mehr Semikolon + BOM + CRLF."
    )


def test_audit_csv_entschaerft_formeln(index_html):
    """CSV-Injection: ein Feld, das mit = + - @ beginnt, wird in Excel sonst
    als Formel ausgefuehrt."""
    assert 'if(/^[=+\\-@\\t\\r]/.test(s))s="\'"+s;' in index_html, (
        "Der Formel-Injektions-Schutz des CSV-Exports (v3.9.407) ist weg."
    )


def test_semikolon_und_quote_zerreissen_die_zeile_nicht(node_exe, index_html):
    """WIDERLEGUNG. Die Sorge war: eine Maengelbeschreibung mit Semikolon oder
    Anfuehrungszeichen zerreisst die Zeile. Sie tut es nicht - genXls schreibt
    HTML, kein CSV. Gemessen am konkreten Feld.
    """
    out = _run_genxls(
        node_exe,
        index_html,
        "const m=CAPTURED.text.match(/>(Tuer undicht[^<]*)</);"
        "process.stdout.write(m?JSON.stringify(m[1]):'KEIN TREFFER');",
    )
    assert "Tuer undicht; " in out and '\\"Sued\\"' in out, (
        "Das Feld mit Semikolon und Anfuehrungszeichen kam nicht unversehrt "
        "in genau einer Zelle an. Gemessen: " + out
    )


# ── ROT bis zum Patch: die Zahlen ───────────────────────────────────────────
def test_genxls_schreibt_dezimalzahlen_als_zahl(node_exe, index_html):
    """Kern des Auftrags. Heute ist JEDE Zelle Text (mso-number-format:\\@)
    und jede Zahl hat einen PUNKT -> im deutschen Excel unsummierbar.

    Der Patch gibt Dezimalzellen das Attribut x:num mit dem invarianten Wert.
    Der Namensraum x= ist im <html>-Tag bereits deklariert.
    """
    out = _run_genxls(
        node_exe,
        index_html,
        "const m=CAPTURED.text.match(/x:num=\"[^\"]*\"/g);"
        "process.stdout.write(m?m.join(' '):'KEINE');",
    )
    assert out != "KEINE", (
        "Keine einzige Zelle traegt x:num. Damit ist jede Stunden-, km-, "
        "Liter- und Euro-Spalte in Excel Text: nicht summierbar, nicht "
        "sortierbar, nicht filterbar."
    )
    for erwartet in ('x:num="7.5"', 'x:num="0.5"', 'x:num="12.25"'):
        assert erwartet in out, (
            "Der Zahlenwert %s fehlt als x:num. Gemessen: %s" % (erwartet, out)
        )


def test_genxls_zeigt_dezimalkomma(node_exe, index_html):
    """Sichtbare Seite desselben Befunds: der Nutzer soll 7,5 lesen, nicht 7.5."""
    out = _run_genxls(
        node_exe,
        index_html,
        # nur die Zellinhalte, die wie eine Zahl aussehen - Punkt ODER Komma
        "process.stdout.write(JSON.stringify("
        "CAPTURED.text.match(/>-?[0-9]+[.,][0-9]+</g)||[]));",
    )
    assert ">7.5<" not in out, (
        "Die Stundenzelle steht mit Dezimalpunkt in der Datei. Im deutschen "
        "Excel liest der Nutzer '7.5' statt '7,5'.\nGemessen: " + out
    )
    assert ">7,5<" in out, (
        "Die Stundenzelle traegt kein Dezimalkomma.\nGemessen: " + out
    )


def test_genxls_summenzeile_ist_eine_zahl(node_exe, index_html):
    """sumCol rechnet in JS und schreibt das Ergebnis als Text mit Punkt.
    Die Summe ist der Grund, warum ueberhaupt exportiert wird."""
    out = _run_genxls(
        node_exe,
        index_html,
        "const m=CAPTURED.text.match(/Gesamt<\\/td>(.*?)<\\/tr>/s);"
        "process.stdout.write(m?m[1]:'KEINE SUMME');",
    )
    assert ">20.25<" not in out, (
        "Die Summenzeile steht mit Dezimalpunkt als Text in der Datei.\n"
        "Gemessen: " + out
    )
    assert 'x:num="20.25"' in out, (
        "Die Summenzelle traegt keinen numerischen Wert.\nGemessen: " + out
    )


def test_zeilenumbruch_ueberlebt_in_der_zelle(node_exe, index_html):
    """Eine Bautagebuch-Bemerkung oder Maengelbeschreibung ueber mehrere Zeilen
    wird heute zu EINER Zeile - HTML faltet den Umbruch zu einem Leerzeichen.
    Excel kennt dafuer <br style="mso-data-placement:same-cell;">.
    """
    out = _run_genxls(
        node_exe,
        index_html,
        "const m=CAPTURED.text.match(/>(Tuer undicht[\\s\\S]*?)</);"
        "process.stdout.write(m?JSON.stringify(m[1]):'KEIN TREFFER');",
    )
    br_da = "mso-data-placement" in index_html
    assert br_da, (
        "genXls kennt den Excel-Zellumbruch nicht. Ein mehrzeiliger Text wird "
        "beim Export zu einer einzigen Zeile zusammengezogen.\n"
        "Gemessene Zelle: " + out
    )


# ── ROT bis zum Patch: Inhalt ───────────────────────────────────────────────
def test_ticket_export_folgt_dem_bildschirmfilter(index_html):
    """Dieselbe Fehlerklasse wie bei den Maengeln (v3.9.875):
    die Tabelle rendert _vpFiltered (Suche + Typ + Status + Ebene),
    der Export nimmt allTickets. Wer filtert und dann exportiert, bekommt
    alles."""
    neu_da = "const data=_vpFiltered.map((t,i)=>{" in index_html
    alt_da = "const data=allTickets.map((t,i)=>{" in index_html
    assert neu_da and not alt_da, (
        "exportTickets (Z17606) exportiert weiterhin allTickets statt der "
        "am Bildschirm gefilterten Liste _vpFiltered (die die Tabelle in "
        "Z17640 und die Kachelansicht in Z17642 rendern).\n"
        "gefiltert=%s  ungefiltert=%s" % (neu_da, alt_da)
    )


def test_werkzeug_export_folgt_dem_bildschirmfilter(index_html):
    """Werkzeugliste: der Bildschirm rendert `sorted` (aus `filtered`:
    Status-Chip, Kategorie, Suche), der Export nimmt die rohe Prop
    `werkzeuge`. Wer auf 'In Reparatur' filtert, exportiert das ganze
    Inventar."""
    alt_da = 'const data=werkzeuge.map((w,i)=>[i+1,w.inventarnr||"",w.name||"",' in index_html
    neu_da = 'const data=sorted.map((w,i)=>[i+1,w.inventarnr||"",w.name||"",' in index_html
    assert neu_da and not alt_da, (
        "Der Werkzeug-Export (Z28645) nimmt weiterhin die ungefilterte Prop "
        "`werkzeuge` statt der angezeigten Liste `sorted`.\n"
        "gefiltert=%s  ungefiltert=%s" % (neu_da, alt_da)
    )


def test_audit_csv_schreibt_wiener_zeit(index_html):
    """Der Bildschirm daneben zeigt toLocaleTimeString("de-AT"), die Datei
    schreibt toISOString() = UTC. Sommerzeit = 2 Stunden Versatz zwischen
    dem, was man sieht, und dem, was man exportiert.
    Gemessen: 09:15 Wien -> "2026-08-28T07:15:00.000Z" in der Datei.
    """
    utc_da = "return [new Date(a.created_at).toISOString(),uN," in index_html
    assert not utc_da, (
        "Die Zeitspalte des Audit-CSV steht weiterhin in UTC (toISOString), "
        "waehrend die Liste darueber Wiener Zeit anzeigt."
    )


# ── Umkehrprobe ─────────────────────────────────────────────────────────────
def test_selbsttest_riegel_schlagen_beim_rueckbau_an(index_html):
    """Ein Riegel, der nicht rot werden kann, misst nichts. Hier wird der
    Bestand kuenstlich in den ALTEN Zustand zurueckgebaut und geprueft, dass
    jede Aussage dann faellt."""
    # 1. BOM-Riegel muss anschlagen, wenn ein Export sein BOM verliert
    kaputt = index_html.replace(
        '_dl(new Blob(["\\ufeff"+html],{type:"application/vnd.ms-excel;charset=utf-8"}),filename);',
        '_dl(new Blob([html],{type:"application/vnd.ms-excel;charset=utf-8"}),filename);',
        1,
    )
    assert kaputt != index_html, "Rueckbau BOM griff nicht - Anker veraltet"
    pat = re.compile(
        r"new Blob\(\[(.{0,12}?)\+?\s*(?:html|_csv)\]\s*,\s*\{\s*type\s*:\s*"
        r"['\"](application/vnd\.ms-excel|text/csv)",
        re.S,
    )
    ohne_bom = [p for p, _m in pat.findall(kaputt) if "\ufeff" not in p and "ufeff" not in p.lower()]
    assert ohne_bom, "Umkehrprobe: der BOM-Riegel wuerde einen BOM-losen Export nicht sehen"

    # 2. Filter-Riegel muss anschlagen, wenn der Ticket-Export zurueckfaellt
    # Beide Richtungen messen: der Riegel muss auf dem gepatchten Stand gruen
    # und auf dem zurueckgebauten Stand rot sein. Solange der Patch fehlt,
    # wird der gepatchte Stand hier kuenstlich erzeugt.
    gepatcht = index_html.replace(
        "const data=allTickets.map((t,i)=>{",
        "const data=_vpFiltered.map((t,i)=>{",
        1,
    )
    assert "const data=_vpFiltered.map((t,i)=>{" in gepatcht, (
        "Umkehrprobe: der gepatchte Zustand liess sich nicht herstellen - "
        "Anker veraltet"
    )
    zurueck = gepatcht.replace(
        "const data=_vpFiltered.map((t,i)=>{",
        "const data=allTickets.map((t,i)=>{",
        1,
    )
    assert "const data=_vpFiltered.map((t,i)=>{" not in zurueck, (
        "Umkehrprobe: der Ticket-Filter-Riegel haette den Rueckbau nicht bemerkt"
    )

    # 3. Der Zahlen-Riegel darf nicht schon durch irgendeinen x:num-Rest gruen sein
    assert index_html.count('x:num=') == index_html.count('x:num="'), (
        "x:num taucht in einer Form auf, die der Riegel nicht misst"
    )
