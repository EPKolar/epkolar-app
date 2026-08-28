# -*- coding: utf-8 -*-
"""v3.9.875 - Der Maengel-Report druckte, was gar nicht auf dem Schirm stand.

BEFUND: Der Status-Filter (fSt) wirkte NUR beim Rendern der Liste, nicht in der
gefilterten Menge msF. Alles, was aus msF gespeist wurde, ignorierte den geklickten
Status-Chip:

    PDF-Report      -> behobene Maengel im Report an den Kunden
    Excel-Export    -> dasselbe
    Sammelauswahl   -> markierte Maengel, die nicht sichtbar waren
                       (Bulk-Status/Bulk-Zuweisung trafen damit Unbeteiligte)

WARUM DER NAHELIEGENDE FIX FALSCH GEWESEN WAERE: einfach `fSt` in msF hineinzufiltern
haette die Status-Zaehler zerstoert - die zaehlen AUS msF (`msF.filter(m=>m.status===s)`).
Nach einem Klick auf "offen" haetten alle anderen Chips 0 gezeigt.

Deshalb drei Ebenen (Facetten-Logik):

    _msWS         = Verantwortlicher + Suche      -> Basis der PRIO-Zaehler
    msF           = _msWS + Prio                  -> Basis der STATUS-Zaehler
    msV           = msF   + Status                -> das WIRKLICH Sichtbare
    _msPrioBasis  = _msWS + Status                -> Basis der PRIO-Zaehler

MITGEFUNDEN, gleiche Fehlerklasse: die PRIO-Zaehler zaehlten aus msF, das bereits nach
Prio gefiltert ist. Stand der Filter auf "hoch", zeigten "mittel" und "niedrig" beide 0
- der Nutzer sah, es gebe keine, und filterte deshalb nie zurueck.

Jede Ebene hat hier ihren eigenen Riegel, weil ein spaeterer "Aufraeumer" sie sonst
wieder zusammenlegt - genau das war der Ausgangszustand.
"""
import re


def _vmang(index_html):
    """Der Filter-Kopf von VMang: von der Deklaration bis zu _msPrioBasis."""
    i = index_html.find("const [fSt,setFSt]=")
    assert i != -1, "fSt-Deklaration weg - VMang umgebaut?"
    j = index_html.find("const _msPrioBasis=", i)
    assert j != -1, (
        "_msPrioBasis fehlt - die Facetten-Trennung ist zurueckgebaut. Dann zaehlen "
        "die Prio-Chips wieder aus einer bereits nach Prio gefilterten Menge."
    )
    return index_html[i:index_html.find("\n", j)]


# -- Die drei Ebenen existieren und bauen aufeinander auf --------------------

def test_grundmenge_filtert_nur_verantwortlichen_und_suche(index_html):
    block = _vmang(index_html)
    m = re.search(r"const _msWS=ms\.filter\(m=>\{(.*?)\n  \}\);", block, re.S)
    assert m, "_msWS nicht gefunden:\n" + block[:500]
    body = m.group(1)
    assert "fWorker" in body and "fSearch" in body, (
        "Die Grundmenge filtert nicht mehr nach Verantwortlichem und Suche:\n" + body
    )
    assert "m.prio" not in body and "m.status" not in body, (
        "In der Grundmenge steht Prio oder Status - dann zaehlen die Facetten-Chips "
        "wieder gegen sich selbst:\n" + body
    )


def test_msF_ist_grundmenge_plus_prio(index_html):
    block = _vmang(index_html)
    assert 'const msF=_msWS.filter(m=>fPr==="alle"||m.prio===fPr);' in block, (
        "msF baut nicht mehr auf _msWS + Prio auf:\n" + block[:600]
    )


def test_msV_ist_das_wirklich_sichtbare(index_html):
    block = _vmang(index_html)
    assert 'const msV=msF.filter(m=>fSt==="alle"||m.status===fSt);' in block, (
        "msV fehlt oder ist veraendert - msV ist die Menge, die der Nutzer sieht.\n" + block[:600]
    )


def test_prio_basis_laesst_die_prio_frei(index_html):
    """Die Prio-Zaehler duerfen nicht aus einer nach Prio gefilterten Menge zaehlen."""
    block = _vmang(index_html)
    assert 'const _msPrioBasis=_msWS.filter(m=>fSt==="alle"||m.status===fSt);' in block, (
        "_msPrioBasis fehlt oder filtert falsch:\n" + block[:600]
    )
    assert "_msPrioBasis=_msF" not in block and "_msPrioBasis=msF" not in block, (
        "Die Prio-Basis haengt an msF - genau der Fehler, der 'mittel: 0' erzeugt hat."
    )


# -- Was aus welcher Menge gespeist wird ------------------------------------

def test_pdf_report_druckt_nur_sichtbares(index_html):
    assert "const list=msV.slice().sort(" in index_html, (
        "Der PDF-Report laeuft nicht ueber msV - dann stehen behobene Maengel im "
        "Report, den der Kunde bekommt."
    )


def test_excel_export_exportiert_nur_sichtbares(index_html):
    assert "const data=msV.map(m=>{" in index_html, (
        "Der Excel-Export laeuft nicht ueber msV - gleicher Fehler wie beim PDF."
    )


def test_sammelauswahl_greift_nur_auf_sichtbares(index_html):
    assert "const _bulkAll=()=>{const ids=msV.map(m=>m.id);" in index_html, (
        "'Alle auswaehlen' greift nicht auf msV - dann trifft eine Sammelaktion "
        "(Status setzen, zuweisen) Maengel, die der Nutzer gar nicht sieht."
    )
    assert "checked: msV.length>0&&msV.every" in index_html, (
        "Das Haekchen 'alle ausgewaehlt' rechnet gegen eine andere Menge als die "
        "Auswahl selbst - dann steht es dauerhaft falsch."
    )


def test_status_zaehler_bleiben_auf_msF(index_html):
    """Bewusste Grenze: die Status-Chips MUESSEN aus msF zaehlen, nicht aus msV -
    sonst zeigt nach einem Klick jeder andere Chip 0."""
    assert 's==="alle"?msF.length:msF.filter(m=>m.status===s).length' in index_html, (
        "Die Status-Zaehler wurden auf msV umgestellt. Dann zeigt nach einem Klick "
        "auf 'offen' der Chip 'behoben' 0 an - und niemand filtert zurueck."
    )


def test_prio_zaehler_zaehlen_aus_der_prio_basis(index_html):
    assert 'pr==="alle"?_msPrioBasis.length:_msPrioBasis.filter(m=>m.prio===pr).length' in index_html, (
        "Die Prio-Zaehler zaehlen nicht aus _msPrioBasis."
    )


# -- Umkehrprobe -------------------------------------------------------------

def test_selbsttest_riegel_schlagen_beim_rueckbau_an(index_html):
    """Der alte Zustand wird rekonstruiert; die Riegel muessen dann rot werden."""
    alt = index_html.replace("const list=msV.slice().sort(",
                             "const list=msF.slice().sort(", 1)
    assert alt != index_html, "Rueckbau griff nicht - Anker veraltet"
    assert "const list=msV.slice().sort(" not in alt, (
        "Umkehrprobe: der PDF-Riegel wuerde nicht anschlagen"
    )

    alt2 = index_html.replace(
        'const _msPrioBasis=_msWS.filter(m=>fSt==="alle"||m.status===fSt);', "", 1)
    assert alt2 != index_html, "Rueckbau 2 griff nicht - Anker veraltet"
    try:
        _vmang(alt2)
    except AssertionError:
        pass
    else:
        raise AssertionError(
            "Umkehrprobe: ohne _msPrioBasis muesste der Kopf-Extraktor scheitern"
        )
