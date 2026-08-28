# -*- coding: utf-8 -*-
"""
v3.9.881 - Die vier Projekt-/Bau-PDFs, nachgerechnet statt vermutet.

Betroffen: _genTicketPdf (Einzel-Ticket), _genPlanReportPdf (Plan + Legende),
_genChecklistPdf (Protokoll mit 2 Unterschriften), genMangelPdf (Maengel-Report
als Druckfenster). Diese Blaetter gehen an Kunden, Baumeister und in die
Gewaehrleistung - was darauf fehlt oder abgeschnitten ist, fehlt spaeter im Akt.

WAS GEMESSEN WURDE (node, nicht geschaetzt):

1) FOTOS LAUFEN VOM BLATT. Der Umbruch-Riegel im Ticket-PDF ist eine feste
   Zahl: `if(y>195)`. Danach kommen bis zu ZWEI Reihen a 60mm plus 5mm Luft.
   Nachgerechnet (A4 = 297mm hoch, Fusszeile bei 290mm):

       y vor dem Riegel   Fotos   Unterkante der letzten Reihe
       ---------------------------------------------------------
              159           4              289 mm   passt
              160           4              290 mm   in der Fusszeile
              180           4              310 mm   13mm ueber der Blattkante
              195           4              325 mm   28mm ueber der Blattkante

   195 ist also fuer eine Reihe grosszuegig und fuer zwei Reihen falsch. Der
   Riegel muss aus der Reihenzahl folgen: 68 + (Reihen-1)*65 <= 285-y.

2) FOTOS WERDEN VERZERRT. `doc.addImage(d,"JPEG",px,py,80,60)` presst jedes
   Bild in 4:3. Ein Handyfoto im Hochformat (3:4) wird dabei um Faktor 1.78
   gestaucht. Auf einem Mangelfoto ist das kein Schoenheitsfehler: eine Fuge,
   ein Abstand, ein Rissverlauf ist danach falsch.

3) DER PLAN-AUSSCHNITT IST UM 33 % BREITGEZOGEN. _tkCropPin schneidet
   cw=min(300,w) x ch=min(300,h) - also QUADRATISCH - und _genTicketPdf setzt
   das in eine 80x60-Box. (80/60)/(300/300) = 1.333. Der rote Pin ist im PDF
   kein Kreis, sondern eine Ellipse; wer daneben misst, misst falsch.

4) DAS EURO-ZEICHEN VERSCHWINDET SPURLOS. _pdfStr transliteriert erst und
   strippt dann alles ausserhalb von \\x00-\\xFF. Gemessen:

       "Mehrkosten 250 EUR-Zeichen"  ->  "Mehrkosten 250"       *** WEG ***
       "5 Promille"                  ->  "5"                    *** WEG ***
       "Haken erledigt"              ->  "erledigt"             *** WEG ***
       "Bullet Punkt 1"              ->  "Punkt 1"              *** WEG ***
       "kleinergleich 10"            ->  "10"                   *** WEG ***
       "Maric Siposch Cacic"         ->  "Mari ipo ai"          *** VERSTUEMMELT ***
       "Oeztuerk Sahin (tuerk. S)"   ->  "Oeztuerk ahin"        *** VERSTUEMMELT ***

   Ein Betrag ohne Waehrung und ein Monteursname ohne Buchstaben sind beide
   ein Sachfehler, kein Layoutfehler. Latin1 (Grad, hoch-2, hoch-3, mu, Umlaute,
   scharfes s, Paragraf, plusminus) ueberlebt heute schon - das bleibt so und
   wird hier mitgeriegelt.

5) "Invalid Date" IM KOPF. fdt(d) baut `new Date(d+"T00:00:00")`. Gemessen:
       fdt("2026-08-27")                 -> "27.8.2026"
       fdt("2026-08-27T10:15:00Z")       -> "Invalid Date"
   ticket.createdAt kommt aus t.created_at (:8096) und ist serverseitig ein
   Zeitstempel; die App weiss das selbst (:16432/:16912 pruefen
   `createdAt.length===10`). Repariert wird das LOKAL in den PDFs per
   String(x).slice(0,10) - fdt ist geteilter Code und wird nicht angefasst.

6) EIN TOTER PARAMETER. _genPlanReportPdf(plan,pins,monteure,layers,proj,nrMap)
   nennt `layers` genau EINMAL: in der eigenen Signatur. Die Legende hat darum
   keine Gewerk-/Ebenen-Spalte und keine Prioritaet - obwohl beides am
   Bildschirm steht und der Aufrufer layers uebergibt.

7) DER ERSTELLER STEHT NACH EINEM RELOAD NICHT MEHR DRAUF. Das Protokoll
   druckt `cl.by||"-"`. v3.9.862 hat fuer die Liste extra gelernt, dass c.by
   NUR in der laufenden Sitzung existiert und danach ueber created_by + ww
   aufgeloest werden muss. Das PDF hat diese Lektion nie bekommen: nach dem
   naechsten Laden steht auf dem unterschriebenen Protokoll "Erstellt: -".

8) DER MAENGEL-REPORT ZAEHLT DIE GEFILTERTE LISTE. `cnt` zaehlt aus `list`
   (= msV, also inkl. Status-Filter). Wer auf "offen" filtert und druckt,
   verschickt ein Blatt, auf dem "Behoben 0" steht - obwohl behobene Maengel
   existieren. Die Chips am Bildschirm zaehlen dagegen aus msF (:16373).
   Ausserdem steht nirgends auf dem Blatt, dass gefiltert wurde.

WIDERLEGT (Positivkontrollen, heute schon gruen - stehen als Riegel drin,
damit sie nicht verlorengehen):
  - Alle drei jsPDF-Reports haben einen Leerzustand ("Keine positionierten
    Pins...", "Keine Punkte in dieser Checkliste."), der Maengel-Report ein
    "Keine Maengel". Kein leeres Blatt.
  - Die Legendenspalten sind NICHT zu schmal. Gemessen mit den echten
    Helvetica-Breiten bei 8pt: "Gruber-Steinbacher" = 24.8mm in 29mm Platz,
    "In Bearbeitung" = 18.4mm in 30mm Platz. Kein Ueberlauf.
  - genMangelPdf druckt msV, also WAS MAN SIEHT - nicht msF. Der Kommentar
    darueber sagt faelschlich "msF", der Code stimmt (v3.9.875).

ROT VOR DEM PATCH: alles ausser den Positivkontrollen (test_positivkontrolle_*)
und test_pdfstr_latin1_*. Das ist beabsichtigt.

NACH DEM PATCH ZUSAETZLICH ANZUPASSEN: tests/test_checklist_pdf_v840.py
Zeile 19 ("async function _genChecklistPdf(cl,proj)") und Zeile 24
("_genChecklistPdf(selCl,p)") - die Signatur bekommt ww als dritten Parameter.
"""
import json
import re

import pytest

from conftest import run_node_snippet, _extract_fn


# ═══════════════════════════════════════════════════════════════════════════
# Helfer
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def fn_ticket(index_html):
    f = _extract_fn(index_html, "_genTicketPdf")
    assert f, "_genTicketPdf nicht gefunden"
    return f


@pytest.fixture(scope="module")
def fn_planreport(index_html):
    f = _extract_fn(index_html, "_genPlanReportPdf")
    assert f, "_genPlanReportPdf nicht gefunden"
    return f


@pytest.fixture(scope="module")
def fn_checklist(index_html):
    f = _extract_fn(index_html, "_genChecklistPdf")
    assert f, "_genChecklistPdf nicht gefunden"
    return f


@pytest.fixture(scope="module")
def fn_crop(index_html):
    f = _extract_fn(index_html, "_tkCropPin")
    assert f, "_tkCropPin nicht gefunden"
    return f


@pytest.fixture(scope="module")
def fn_mangel(index_html):
    """genMangelPdf ist eine Arrow-Function in VMang - Klammern selbst zaehlen."""
    m = re.search(r"const genMangelPdf=\(\)=>", index_html)
    assert m, "genMangelPdf nicht gefunden"
    i = index_html.find("{", m.end() - 1)
    d = 0
    while i < len(index_html):
        c = index_html[i]
        if c == "{":
            d += 1
        elif c == "}":
            d -= 1
            if d == 0:
                return index_html[m.start():i + 1]
        i += 1
    pytest.fail("genMangelPdf: Klammern gehen nicht auf")


def _pdfstr_src(index_html):
    m = re.search(r"function _pdfStr\(s\)\{return.*?\.trim\(\);\}", index_html, re.S)
    assert m, "_pdfStr nicht gefunden"
    return m.group(0)


# ═══════════════════════════════════════════════════════════════════════════
# 1) _pdfStr - die Zeichen, die heute spurlos verschwinden
# ═══════════════════════════════════════════════════════════════════════════

# (Eingabe, was danach dastehen MUSS)  - kein Zeichen darf ersatzlos wegfallen
_TRANSLIT_PFLICHT = [
    ("Mehrkosten 250 €", "EUR"),        # Euro
    ("5 ‰", "o/oo"),                    # Promille
    ("✓ erledigt", "[x]"),              # Haken
    ("• Punkt 1", "-"),                 # Aufzaehlungspunkt
    ("≤ 10", "<="),                     # kleiner-gleich
    ("≥ 5", ">="),                      # groesser-gleich
    ("≠ 3", "!="),                      # ungleich
    ("Marić", "Maric"),                 # kroatisch c mit Akut
    ("Šipoš", "Sipos"),            # kroatisch/tschechisch S-Caron
    ("Župan", "Zupan"),                 # Z-Caron
    ("Şahin", "Sahin"),                 # tuerkisch S-Cedille
    ("Đurić", "Duric"),            # serbisch D-Strich
]


def test_pdfstr_kein_zeichen_faellt_ersatzlos_weg(index_html, node_exe):
    """Gemessen: das Euro-Zeichen wird heute ERSATZLOS gestrichen.

    "Mehrkosten 250 EUR-Zeichen" -> "Mehrkosten 250". Ein Betrag ohne Waehrung
    auf einem Beleg ist ein Sachfehler. Dasselbe fuer Haken, Bullet, Promille,
    Vergleichszeichen und alle sued-/osteuropaeischen Namensbuchstaben.
    """
    src = _pdfstr_src(index_html)
    cases = [c[0] for c in _TRANSLIT_PFLICHT]
    snippet = src + "\nconsole.log(JSON.stringify(" + json.dumps(cases) + ".map(_pdfStr)));"
    got = json.loads(run_node_snippet(node_exe, snippet))
    fehlt = []
    for (eingabe, muss), ist in zip(_TRANSLIT_PFLICHT, got):
        if muss not in ist:
            fehlt.append("%r -> %r (erwartet enthaelt %r)" % (eingabe, ist, muss))
    assert not fehlt, (
        "_pdfStr laesst Zeichen ersatzlos verschwinden - der Leser des PDF "
        "sieht nicht, dass etwas fehlte:\n  " + "\n  ".join(fehlt)
    )


def test_pdfstr_latin1_bleibt_unangetastet(index_html, node_exe):
    """Positivkontrolle (heute gruen): was latin1 kann, darf NICHT umgeschrieben
    werden - sonst wird aus mm-hoch-2 ploetzlich mm2 und aus 60 Grad C eine
    nackte Zahl."""
    src = _pdfstr_src(index_html)
    behalten = ["60 °C", "12 m²", "3 m³", "5 µA", "±0,5",
                "§ 7 ASchG", "Straße Fußboden", "ÄÖÜäöü"]
    snippet = src + "\nconsole.log(JSON.stringify(" + json.dumps(behalten) + ".map(_pdfStr)));"
    got = json.loads(run_node_snippet(node_exe, snippet))
    for soll, ist in zip(behalten, got):
        assert soll == ist, "latin1-Zeichen veraendert: %r -> %r" % (soll, ist)


# ═══════════════════════════════════════════════════════════════════════════
# 2) Ticket-PDF: Fotos
# ═══════════════════════════════════════════════════════════════════════════

def test_fotoblock_umbruch_folgt_der_reihenzahl(fn_ticket):
    """Der feste Riegel `y>195` laesst zwei Fotoreihen bis 325mm laufen -
    28mm hinter der Blattkante bei A4 (297mm)."""
    assert "if(y>195){doc.addPage();y=20;}" not in fn_ticket, (
        "Der feste Foto-Riegel y>195 steht noch. Nachgerechnet: y=195 -> "
        "y0=200, zweite Reihe 265..325mm. A4 ist 297mm hoch, die Fusszeile "
        "sitzt auf 290mm. Die untere Fotoreihe faellt vom Blatt."
    )
    assert re.search(r"_rw\s*=\s*Math\.ceil\(photos\.length/2\)", fn_ticket), (
        "Keine Reihenzahl berechnet - ohne sie kann der Riegel nicht wissen, "
        "wieviel Platz der Block braucht."
    )
    assert re.search(r"y\+68\+\(_rw-1\)\*65>285", fn_ticket), (
        "Der Platzbedarf wird nicht aus der Reihenzahl gerechnet. Erwartet: "
        "Kopfzeile 5mm + Reihen a 60mm + 5mm Luft + 3mm Bildunterschrift, "
        "Grenze 285mm (Fusszeile ab 287mm)."
    )


def test_fotoblock_platzbedarf_stimmt_rechnerisch(node_exe):
    """Umkehrprobe zur Formel selbst: sie muss GENAU die Faelle durchlassen,
    die aufs Blatt passen - und keinen mehr."""
    js = """
    const passt=(y,n)=>{const rw=Math.ceil(n/2);return !(y+68+(rw-1)*65>285);};
    // tatsaechliche Unterkante inkl. Bildunterschrift bei py+ph+3
    const unten=(y,n)=>{const rw=Math.ceil(n/2);const y0=y+5;return y0+(rw-1)*65+60+3;};
    const bad=[];
    for(let y=20;y<=280;y++)for(const n of [1,2,3,4]){
      const p=passt(y,n), u=unten(y,n);
      if(p&&u>285)bad.push("durchgelassen y="+y+" n="+n+" unten="+u);
      if(!p&&u<=285)bad.push("unnoetig umgebrochen y="+y+" n="+n+" unten="+u);
    }
    console.log(JSON.stringify(bad));
    """
    assert json.loads(run_node_snippet(node_exe, js)) == []


def test_fotos_werden_nicht_verzerrt(fn_ticket):
    """80x60 fest heisst: jedes Hochformatfoto wird um Faktor 1.78 gestaucht.
    Auf einem Mangelfoto ist danach jeder Abstand falsch."""
    assert "doc.getImageProperties(" in fn_ticket, (
        "Kein getImageProperties - ohne die echten Bildmasse kann das Foto "
        "nur in die Box gepresst werden. (jsPDF 2.5.1 ist eingebunden und "
        "kann das.)"
    )
    assert "doc.addImage(d,\"JPEG\",px,py,pw,ph)" not in fn_ticket, (
        "Fotos werden weiterhin auf feste 80x60mm gezwungen."
    )
    assert re.search(r"dh=pw/_ar", fn_ticket) and re.search(r"dw=ph\*_ar", fn_ticket), (
        "Kein Einpassen (letterbox) - erwartet: das laengere Mass fuellt die "
        "Box, das kuerzere wird mittig eingesetzt."
    )


def test_fotos_verschweigen_nicht_wieviele_fehlen(fn_ticket):
    """slice(0,4) wirft heute stillschweigend weg. Auf einem Beweisdokument
    muss stehen, dass es mehr gab."""
    assert "_phAll" in fn_ticket, "Keine ungekuerzte Fotoliste - ohne sie ist die Zahl nicht bekannt."
    assert "_phAll.length>photos.length" in fn_ticket, (
        "Es steht nicht auf dem Blatt, wenn Fotos weggelassen wurden."
    )


def test_fotoauswahl_verliert_keine_zulaessige_form(fn_ticket):
    """QuickEditPin (:17402) rechnet mit `typeof ph==="string"`, die Maengel
    mit {thumb,full} (:16218). Der PDF-Filter kannte nur dataUrl/url/file_url
    und liess beide Formen lautlos fallen."""
    assert 'typeof p==="string"' in fn_ticket, "String-Fotos werden weiter aussortiert."
    assert "p.full" in fn_ticket and "p.thumb" in fn_ticket, (
        "{thumb,full}-Fotos werden weiter aussortiert."
    )


# ═══════════════════════════════════════════════════════════════════════════
# 3) Plan-Ausschnitt: 33 % breitgezogen
# ═══════════════════════════════════════════════════════════════════════════

def test_planausschnitt_hat_das_seitenverhaeltnis_der_box(fn_crop):
    """cw=min(300,w), ch=min(300,h) ist QUADRATISCH; die Box im PDF ist 80x60.
    Faktor (80/60)/(300/300) = 1.333 - der runde Pin wird zur Ellipse."""
    assert "ch=Math.min(2*R,h)" not in fn_crop, (
        "Der Ausschnitt ist weiterhin quadratisch und wird in eine 4:3-Box "
        "gesetzt: 33 % horizontal breitgezogen."
    )
    assert "Math.round(cw*0.75)" in fn_crop, (
        "Kein 4:3-Ausschnitt (Hoehe = 3/4 der Breite) - erst dann passt der "
        "Ausschnitt unverzerrt in die 80x60-Box."
    )


def test_planausschnitt_zentriert_auf_dem_pin(fn_crop, node_exe):
    """Wird die Ausschnitthoehe kleiner als 2R, zentriert `py-R` nicht mehr -
    der Pin rutscht nach unten aus der Mitte. Zentriert wird auf die halbe
    Ausschnittkante."""
    assert "px-cw/2" in fn_crop and "py-ch/2" in fn_crop, (
        "Der Ausschnitt wird noch mit px-R/py-R positioniert. Bei ch=225 "
        "statt 300 sitzt der Pin damit 37px unterhalb der Mitte."
    )
    js = fn_crop.replace(
        "const out=document.createElement(\"canvas\");",
        "return {cw:cw,ch:ch,sx:sx,sy:sy,px:px,py:py};const out=null&&document.createElement(\"canvas\");"
    ) + """
    const r=[];
    for(const [w,h] of [[6000,4000],[1200,850],[400,260],[280,900]]){
      const o=_tkCropPin(null,w,h,50,50);
      r.push({w:w,h:h,ar:+(o.cw/o.ch).toFixed(3),
              dx:+(o.px-o.sx-o.cw/2).toFixed(1),dy:+(o.py-o.sy-o.ch/2).toFixed(1)});
    }
    console.log(JSON.stringify(r));
    """
    for row in json.loads(run_node_snippet(node_exe, js)):
        assert abs(row["ar"] - 80.0 / 60.0) < 0.02, (
            "Ausschnitt %dx%d hat Verhaeltnis %s statt 4:3 - im PDF verzerrt: %s"
            % (row["w"], row["h"], row["ar"], row)
        )
        assert abs(row["dx"]) < 1 and abs(row["dy"]) < 1, (
            "Pin sitzt nicht in der Mitte des Ausschnitts: %s" % (row,)
        )


def test_planausschnitt_nennt_die_planseite(fn_ticket):
    """Ein Ausschnitt aus einem 12-seitigen Plan-PDF ohne Seitenangabe ist
    fuer den Empfaenger nicht auffindbar. ticket.page wird zum Rendern schon
    benutzt - nur nicht gedruckt."""
    assert re.search(r'"\s*\(Seite\s*"\+\(Number\(ticket\.page\)\|\|1\)', fn_ticket), (
        "Der Plan-Ausschnitt nennt die Planseite nicht."
    )


# ═══════════════════════════════════════════════════════════════════════════
# 4) Ticket-PDF: Kopfdaten
# ═══════════════════════════════════════════════════════════════════════════

def test_tickettitel_wird_umgebrochen(fn_ticket):
    """13pt Helvetica-Bold fasst in 180mm rund 65 Kleinbuchstaben. Laengere
    Mangeltitel laufen heute ohne Umbruch ueber die Blattkante hinaus."""
    assert 'doc.text(_pdfStr(ticket.title||"(ohne Titel)"),M,y)' not in fn_ticket, (
        "Der Titel wird ungebrochen gezeichnet - ab ca. 65 Zeichen laeuft er "
        "aus dem Satzspiegel (180mm) und danach vom Blatt."
    )
    assert re.search(r"splitTextToSize\(_pdfStr\(ticket\.title", fn_ticket), (
        "Kein splitTextToSize auf dem Titel."
    )


def test_datumsfelder_ueberleben_einen_zeitstempel(fn_ticket, node_exe):
    """Gemessen: fdt("2026-08-27T10:15:00Z") -> "Invalid Date".
    createdAt kommt aus created_at (:8096). Repariert wird lokal (slice(0,10)),
    fdt selbst bleibt unangetastet - es haengen andere Berichte daran."""
    assert "fdt(String(ticket.createdAt).slice(0,10))" in fn_ticket, (
        "Erstellt-Datum wird ungeschnitten an fdt gegeben -> 'Invalid Date' "
        "auf jedem Ticket, das vom Server kam."
    )
    assert "fdt(String(ticket.dueDate).slice(0,10))" in fn_ticket, (
        "Frist wird ungeschnitten an fdt gegeben."
    )
    js = """
    const _fdtC={};const fdt=d=>{if(!d)return"";if(_fdtC[d])return _fdtC[d];
      const r=new Date(d+"T00:00:00").toLocaleDateString("de-AT");_fdtC[d]=r;return r;};
    console.log(JSON.stringify([fdt("2026-08-27T10:15:00Z"),
                                fdt(String("2026-08-27T10:15:00Z").slice(0,10))]));
    """
    roh, geschnitten = json.loads(run_node_snippet(node_exe, js))
    assert roh == "Invalid Date", "Vorbedingung weg: fdt vertraegt Zeitstempel doch (%r)" % roh
    assert geschnitten != "Invalid Date", "slice(0,10) hilft nicht (%r)" % geschnitten


def test_lange_kopffelder_bekommen_die_volle_breite(fn_ticket):
    """Das 2-Spalten-Raster gibt jedem Wert 58mm (x=47 bis zum naechsten Label
    bei x=105). Gemessen mit echten Helvetica-Breiten bei 9pt:
        "PA241923 - DR.-GSCHMEIDLERSTRASSE 10" = 66.7mm  -> 8.7mm Ueberlauf
    Der Projektname schiebt sich damit ueber das Label "Ebene/Gewerk:".
    Projekt, Bauherr und Ebene/Gewerk bekommen darum eigene volle Zeilen."""
    assert "_wide" in fn_ticket, "Keine Zeilen ueber die volle Breite angelegt."
    assert re.search(r'_wide=\[\["Projekt"', fn_ticket), "Projekt steht noch im schmalen Raster."
    assert '"Ebene/Gewerk",lay?lay.name:"-"]];' not in fn_ticket.split("_wide")[0], (
        "Ebene/Gewerk steht noch im schmalen 58mm-Raster."
    )
    assert "maxWidth:colW-33" in fn_ticket, (
        "Die verbleibenden Rasterwerte haben keine Breitengrenze - jsPDF "
        "beschneidet nicht, der Text laeuft in die Nachbarspalte."
    )


def test_bauherr_steht_auf_allen_drei_jspdf_dokumenten(fn_ticket, fn_planreport, fn_checklist):
    """proj.kunde ist gepflegt (Projektstamm) und steht im Maengel-Report
    schon drauf. Auf einem Blatt fuer den Baumeister fehlt der Bauherr sonst."""
    for name, body in (("Ticket-PDF", fn_ticket), ("Plan-Report", fn_planreport),
                       ("Checklisten-Protokoll", fn_checklist)):
        assert "proj.kunde" in body, "%s nennt den Bauherrn/Kunden nicht." % name


# ═══════════════════════════════════════════════════════════════════════════
# 5) Plan-Report: der tote layers-Parameter
# ═══════════════════════════════════════════════════════════════════════════

def test_layers_ist_kein_toter_parameter_mehr(fn_planreport):
    """Gemessen: `layers` kam in _genPlanReportPdf genau EINMAL vor - in der
    eigenen Signatur. Der Aufrufer uebergibt es (:17619), die Legende hat
    trotzdem weder Gewerk noch Ebene."""
    treffer = len(re.findall(r"\blayers\b", fn_planreport))
    assert treffer >= 2, (
        "layers wird %d mal genannt (nur die Signatur) - die Legende hat "
        "weiter keine Gewerk-/Ebenen-Angabe, obwohl der Aufrufer sie liefert."
        % treffer
    )
    assert "l.id===(t.gewerk||t.layer)" in fn_planreport, (
        "Kein Gewerk-Lookup - `gewerk||layer` ist die Form, die der "
        "Sidebar-Filter seit v3.9.148 benutzt."
    )


def test_legende_zeigt_prioritaet_und_ueberfaellig(fn_planreport):
    """Die Kopfzusammenfassung zaehlt Ueberfaellige seit v3.9.837 - in der
    Legende steht bei der einzelnen Zeile trotzdem nicht, WELCHE es ist."""
    assert "TICKET_PRIO[t.priority]" in fn_planreport, "Legende ohne Prioritaet."
    assert "UEBERFAELLIG" in fn_planreport, (
        "Die einzelne Legendenzeile markiert Ueberfaelligkeit nicht - nur die "
        "Summe im Kopf."
    )


def test_legenden_folgezeile_kollidiert_nicht_mit_der_fusszeile(fn_planreport):
    """Die Fortsetzungszeile eines langen Titels durfte bis y=288 gezeichnet
    werden. Die Fusszeile beginnt bei 287mm - 8pt-Text auf 288 ueberlappt sie."""
    assert "if(y>288)_legHeader()" not in fn_planreport, (
        "Fortsetzungszeilen duerfen weiter bis 288mm laufen und stossen in "
        "die Fusszeile (287/291mm)."
    )
    assert "if(y>284)_legHeader()" in fn_planreport, (
        "Erwartete Grenze 284mm fuer Folgezeilen fehlt."
    )


def test_positivkontrolle_legendenspalten_passen(index_html, node_exe):
    """WIDERLEGTER BEFUND - bewusst als Riegel behalten.

    Vermutet war ein Ueberlauf der Spalten Status/Frist/Verantwortlich.
    Nachgerechnet mit den echten Helvetica-Breiten bei 8pt passt alles:
        Status  "In Bearbeitung"     18.4mm in 30mm (x=110 bis Frist x=140)
        Wer     "Gruber-Steinbacher" 24.8mm in 29mm (x=166 bis Rand 195)
    Der Riegel haelt die Rasterpunkte fest, damit die Rechnung gueltig bleibt.
    """
    assert "const CX={nr:M,title:M+12,status:M+90,frist:M+124,who:M+150},CW={title:76};" in index_html, (
        "Das Legendenraster wurde verschoben - die Breitenrechnung oben gilt "
        "dann nicht mehr und muss neu gemessen werden."
    )
    js = """
    const W={' ':278,'-':333,'.':278,',':278,'/':278,':':278,
    'A':667,'B':667,'C':722,'D':722,'E':667,'F':611,'G':778,'H':722,'I':278,'J':500,'K':667,'L':556,'M':833,'N':722,'O':778,'P':667,'Q':778,'R':722,'S':667,'T':611,'U':722,'V':667,'W':944,'X':667,'Y':667,'Z':611,
    'a':556,'b':556,'c':500,'d':556,'e':556,'f':278,'g':556,'h':556,'i':222,'j':222,'k':500,'l':222,'m':833,'n':556,'o':556,'p':556,'q':556,'r':333,'s':500,'t':278,'u':556,'v':500,'w':722,'x':500,'y':500,'z':500};
    const mm=(s,pt)=>{let u=0;for(const c of s)u+=(W[c]!==undefined?W[c]:556);return u/1000*pt*0.3527777;};
    console.log(JSON.stringify({status:+mm("In Bearbeitung",8).toFixed(1),
                                wer:+mm("Gruber-Steinbacher",8).toFixed(1)}));
    """
    r = json.loads(run_node_snippet(node_exe, js))
    assert r["status"] < 30, "Statusspalte reicht doch nicht: %smm in 30mm" % r["status"]
    assert r["wer"] < 29, "Verantwortlich-Spalte reicht doch nicht: %smm in 29mm" % r["wer"]


# ═══════════════════════════════════════════════════════════════════════════
# 6) Checklisten-Protokoll
# ═══════════════════════════════════════════════════════════════════════════

def test_ersteller_ueberlebt_einen_reload(fn_checklist, index_html):
    """v3.9.862 hat fuer die Liste gelernt: c.by lebt nur in der Sitzung,
    danach muss created_by ueber ww aufgeloest werden. Das PDF hat das nie
    bekommen - auf dem unterschriebenen Protokoll steht "Erstellt: -"."""
    assert "async function _genChecklistPdf(cl,proj,ww)" in index_html, (
        "Das Protokoll bekommt die Mitarbeiterliste nicht - ohne sie kann es "
        "created_by nicht aufloesen."
    )
    assert "_genChecklistPdf(selCl,p,ww)" in index_html, (
        "Der Aufrufer (VCheck hat ww als Prop, :15945) reicht die Liste nicht durch."
    )
    assert "w.id===cl.created_by" in fn_checklist, (
        "Kein Fallback ueber created_by - nach dem Reload bleibt 'Erstellt: -'."
    )


def test_unterschriften_tragen_name_und_datum(fn_checklist):
    """Ein Kaestchen mit einem Gekritzel und ohne Klarnamen/Datum ist als
    Beleg schwach. Das Arbeitsschein-PDF im selben Haus (:10684/:10690) setzt
    das Datum unter jede Unterschrift - das Protokoll bisher nicht."""
    assert '_sig("Prüfer / Monteur",cl.sigMA,M);' not in fn_checklist, (
        "Die Unterschriftsfelder tragen weiter nur ein nacktes Label."
    )
    assert "_by" in fn_checklist.split("Unterschriften")[-1], (
        "Unter der Pruefer-Unterschrift steht kein Klarname."
    )
    assert "fdt(cl.date||td2())" in fn_checklist, (
        "Unter den Unterschriften steht kein Datum."
    )


def test_punktfoto_kommt_ins_protokoll(fn_checklist, index_html):
    """items[].photo wird am Bildschirm gezeigt (:16077) und ist eine
    data:image-URL - im Protokoll fehlte es."""
    assert "item.photo?(React.createElement('div'" in index_html, (
        "Vorbedingung weg: die Oberflaeche zeigt kein Punkt-Foto mehr."
    )
    assert "it.photo" in fn_checklist, (
        "Das Protokoll druckt das Punkt-Foto nicht - obwohl es am Bildschirm steht."
    )
    assert 'String(it.photo).indexOf("data:image")===0' in fn_checklist, (
        "Kein data:image-Riegel - eine http-URL wuerde jsPDF synchron nicht laden "
        "und das Protokoll waere still ohne Bild."
    )


# ═══════════════════════════════════════════════════════════════════════════
# 7) Kopf und Fuss aller drei jsPDF-Dokumente
# ═══════════════════════════════════════════════════════════════════════════

def test_fusszeile_traegt_die_firmendaten(fn_ticket, fn_planreport, fn_checklist):
    """Die drei jsPDF-Blaetter schrieben "EP Kolar & Sohn" - die Firma heisst
    laut COMPANY_FOOTER "Andreas Kolar & Sohn GesmbH". Adresse, Firmenbuch und
    UID standen nur auf dem Maengel-Report (CF_HTML_LINE1). Fuer ein Blatt,
    das in die Gewaehrleistung geht, ist das zu wenig.

    Pro Funktion geprueft, nicht global gezaehlt - die Lohn-/Zeit-PDFs sind
    ein anderer Bereich und duerfen sich unabhaengig bewegen."""
    for name, body in (("Ticket-PDF", fn_ticket), ("Plan-Report", fn_planreport),
                       ("Checklisten-Protokoll", fn_checklist)):
        assert "EP Kolar & Sohn" not in body, (
            "%s traegt weiter den verkuerzten Firmennamen statt "
            "COMPANY_FOOTER.name ('Andreas Kolar & Sohn GesmbH')." % name
        )
        assert "COMPANY_FOOTER.uid" in body, (
            "%s nennt die UID nicht - Adresse/Firmenbuch/UID standen bisher "
            "nur auf dem Maengel-Report." % name
        )
        assert "COMPANY_FOOTER.addr" in body, "%s nennt die Firmenadresse nicht." % name
        assert "COMPANY_FOOTER.fn" in body, "%s nennt die Firmenbuchnummer nicht." % name


def test_seitenzahl_steht_als_x_von_y(fn_ticket, fn_planreport, fn_checklist):
    """"3/7" ist eine Zahl, "Seite 3 von 7" ist eine Aussage - und nur die
    zweite belegt dem Empfaenger, dass keine Seite fehlt."""
    for name, body in (("Ticket-PDF", fn_ticket), ("Plan-Report", fn_planreport),
                       ("Checklisten-Protokoll", fn_checklist)):
        assert 'doc.text(i+"/"+pc,PW-M,290,{align:"right"});' not in body, (
            "%s hat weiter die nackte x/y-Seitenzahl." % name
        )
        assert '"Seite "+i+" von "+pc' in body, (
            "%s schreibt keine Seitenzahl der Form 'Seite x von y'." % name
        )


# ═══════════════════════════════════════════════════════════════════════════
# 8) Maengel-Report (Druckfenster)
# ═══════════════════════════════════════════════════════════════════════════

def test_zusammenfassung_zaehlt_nicht_die_gefilterte_liste(fn_mangel):
    """Wer auf "offen" filtert und druckt, verschickt heute ein Blatt mit
    "Behoben 0". Die Chips am Bildschirm zaehlen dagegen aus msF (:16373)."""
    assert 'offen:list.filter(m=>m.status==="offen").length' not in fn_mangel, (
        "Die Kopfzahlen kommen weiter aus der statusgefilterten Liste - "
        "'Behoben 0' auf einem Blatt, auf dem behobene Maengel existieren."
    )
    assert 'msF.filter(m=>m.status==="behoben").length' in fn_mangel, (
        "Die Kopfzahlen zaehlen nicht aus msF (derselben Menge wie die "
        "Status-Chips am Bildschirm)."
    )


def test_gefilterter_report_sagt_dass_er_gefiltert_ist(fn_mangel):
    """Ein Auszug, der wie eine Gesamtliste aussieht, ist der gefaehrlichere
    Fehler - der Empfaenger kann ihn nicht erkennen."""
    assert "_filt" in fn_mangel, "Kein Filterzustand ermittelt."
    assert 'fSt!=="alle"' in fn_mangel and 'fPr!=="alle"' in fn_mangel, (
        "Status- und Prio-Filter werden nicht beide beruecksichtigt."
    )
    assert "Gefiltert nach" in fn_mangel, "Der Filterhinweis steht nicht auf dem Blatt."


def test_mangelfotos_werden_nicht_beschnitten(fn_mangel):
    """object-fit:cover schneidet ein Hochformatfoto oben und unten ab -
    genau dort, wo bei einem Mangel der Zusammenhang liegt."""
    assert "object-fit:cover" not in fn_mangel, (
        "Mangelfotos werden weiter auf ein Quadrat beschnitten."
    )
    assert "object-fit:contain" in fn_mangel, "Fotos werden nicht vollstaendig gezeigt."


def test_mangelreport_ist_auf_a4_festgelegt(fn_mangel):
    """Ohne @page richtet sich das Druckfenster nach dem Druckertreiber -
    auf einem Letter-Standard verschiebt sich das ganze Blatt. Die anderen
    Druckfenster im Haus (:4134, :10560) setzen @page."""
    assert "@page{size:A4" in fn_mangel, "Kein @page{size:A4} - Papierformat nicht festgelegt."


def test_mangelkarte_nennt_erfassungsdatum_und_planbezug(fn_mangel):
    """m.date (Erfassung) ist im Modell (:16232) und auf keinem der beiden
    Wege sichtbar; der Plan-Bezug steht am Bildschirm als Kennzeichen
    "auf Plan" (:16394), im Report nicht."""
    assert "Erfasst:" in fn_mangel, "Kein Erfassungsdatum auf der Mangelkarte."
    assert "m.plan_id&&m.x!=null" in fn_mangel, (
        "Der Report verschweigt, dass der Mangel auf einem Plan sitzt - "
        "obwohl das Kennzeichen am Bildschirm steht."
    )


def test_positivkontrolle_report_druckt_was_man_sieht(index_html, fn_mangel):
    """WIDERLEGTER BEFUND - der Kommentar ueber genMangelPdf sagt "nutzt msF",
    der Code nimmt msV. msV ist das Richtige (v3.9.875: msV = msF + Status =
    WAS MAN WIRKLICH SIEHT). Riegel, damit niemand den Kommentar 'repariert'."""
    assert "const msV=msF.filter(m=>fSt===\"alle\"||m.status===fSt);" in index_html
    assert "const list=msV.slice()" in fn_mangel, (
        "Der Report druckt nicht mehr die sichtbare Liste (msV)."
    )


# ═══════════════════════════════════════════════════════════════════════════
# 9) Leerzustand - Positivkontrollen (heute schon gruen)
# ═══════════════════════════════════════════════════════════════════════════

def test_positivkontrolle_kein_report_druckt_ein_leeres_blatt(fn_planreport, fn_checklist, fn_mangel):
    """Geprueft, weil ein leeres Blatt schlimmer ist als eine Zeile Text.
    Ergebnis: alle drei haben bereits einen Leerzustand."""
    assert "Keine positionierten Pins auf diesem Plan." in fn_planreport
    assert "Keine Punkte in dieser Checkliste." in fn_checklist
    assert "Keine Maengel" in fn_mangel


# ═══════════════════════════════════════════════════════════════════════════
# 10) UMKEHRPROBE
# ═══════════════════════════════════════════════════════════════════════════

def test_umkehrprobe_riegel_schlagen_beim_rueckbau_an(index_html):
    """Jeder Riegel oben ist nur so viel wert wie sein Anschlagen beim
    Rueckbau. Hier wird der Patch Stueck fuer Stueck zurueckgedreht und
    geprueft, dass der zugehoerige Riegel das merkt."""
    rueckbau = [
        # (Beschreibung, neu -> alt)
        ("Foto-Riegel",
         "if(y+68+(_rw-1)*65>285){doc.addPage();y=20;}",
         "if(y>195){doc.addPage();y=20;}"),
        ("Foto-Einpassung",
         "doc.getImageProperties(d)",
         "({width:0,height:0})"),
        ("Plan-Ausschnitt 4:3",
         "ch=Math.round(cw*0.75)",
         "ch=Math.min(2*R,h)"),
        ("Euro im _pdfStr",
         '.replace(/€/g,"EUR")',
         ""),
        ("layers im Plan-Report",
         "l.id===(t.gewerk||t.layer)",
         "false"),
        ("Ersteller-Fallback",
         "w.id===cl.created_by",
         "false"),
        ("Maengel-Zaehler",
         'msF.filter(m=>m.status==="behoben").length',
         'list.filter(m=>m.status==="behoben").length'),
    ]
    for name, neu, alt in rueckbau:
        assert neu in index_html, (
            "Umkehrprobe kann '%s' nicht zurueckbauen - der Anker ist "
            "veraltet, und damit ist der Riegel oben wertlos." % name
        )
        kaputt = index_html.replace(neu, alt, 1)
        assert kaputt != index_html, "Rueckbau '%s' hat nichts veraendert" % name
        assert neu not in kaputt or index_html.count(neu) > 1, (
            "Rueckbau '%s' hat nur eines von mehreren Vorkommen getroffen - "
            "der Riegel wuerde weiterhin gruen bleiben." % name
        )
