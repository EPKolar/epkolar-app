"""Paket 15 (GF 24.11.2026): Buero-Portal entdoppeln (vorsichtige Variante).

- Kopf-Liste = Vereinigung: Projektzeit-Liste (_bxMaListe) + alle weiteren Mitarbeiter (das Stempel-Dropdown
  PZEView liest ALLE workers ohne Filter). Test: jede Person mit Stempelzeit im Monat ist waehlbar.
- Alte Ansicht samt Umschalter entfernt.
- Doppelte Ueberschriften (Entfernungszulage, Stempelzeiten (PZE)) -> nur Sprunganker.
- Stempelzeiten im Mitarbeiter-Monat ohne eigene MA-Wahl (Kopf waehlt).
- Bauwochenbericht im Mitarbeiter-Monat ausgeblendet (nur unter Weiteres); der Export selbst bleibt.
- Exporte: KEINER entfernt oder umbenannt - die Erzeuger-Funktionen sind byte-gleich zum Stand vor Paket 15
  (md5 je Funktion, gemessen am Stapel-Stand direkt vor Paket 15 = 803a6ce, 3.9.1117; Export-Code dort gleich
  live 3.9.1113 adbfcf8), die Knoepfe stehen alle noch im Code.
  25.11.: Pins neu gemessen - die alten stammten vom verworfenen Zweig feature/kw-auswahl 82c622c (mit den
  abgespaltenen 13b-Exportaenderungen) und passten zu keinem Stand im neuen Stapel.
"""
import hashlib
import json
import re
import shutil
import subprocess

import pytest

NODE = shutil.which("node")
needs_node = pytest.mark.skipif(not NODE, reason="node fehlt")


def _block(src, kopf, ende):
    i = src.index(kopf)
    return src[i:src.index(ende, i + len(kopf)) + len(ende)]


def _node(js):
    r = subprocess.run([NODE, "-e", js], capture_output=True, text=True, encoding="utf-8", timeout=60)
    assert r.returncode == 0, r.stderr[-2000:]
    return json.loads(r.stdout)


# ── Mitarbeiter-Liste im Kopf ───────────────────────────────────────────────
@needs_node
def test_jede_person_mit_stempelzeit_ist_waehlbar(index_html):
    js = (_block(index_html, "function _maIstEhemalig(m,heute){", "\n}") + "\n"
          + _block(index_html, "function _bxKopfListe(monteure,ym){", "\n}") + "\n"
          + _block(index_html, "function _bxMaListe(monteure,ym){", "\n") + "\n" + r"""
const M=[{id:'w1',n:'Huber',r:'Monteur'},{id:'w2',n:'Aliti',r:'Monteur',austritt:'2026-07-22'},{id:'w3',n:'Lindhuber',r:'Backoffice'},
         {id:'w4',n:'Schober',r:'Verkauf/Buchhaltung'},{id:'w5',n:'Cracana',r:'Monteur',austritt:'2026-07-22'},{id:'w6',n:'Riedmann',r:'Monteur'}];
const stempel=[{worker_id:'w2',ts:'2026-07-10T06:00:00Z'},{worker_id:'w3',ts:'2026-07-10T06:00:00Z'},{worker_id:'w4',ts:'2026-07-11T06:00:00Z'},{worker_id:'w6',ts:'2026-07-11T06:00:00Z'}];
const k=_bxKopfListe(M,'2026-07');const ids=k.map(x=>x.m.id);
console.log(JSON.stringify({ids,zusatz:k.map(x=>x.zusatz),fehlt:stempel.filter(e=>ids.indexOf(e.worker_id)<0).map(e=>e.worker_id),
  alt:_bxMaListe(M,'2026-07').map(m=>m.id),alleDa:M.every(m=>ids.indexOf(m.id)>=0)}));""")
    r = _node(js)
    assert r["fehlt"] == [], "Person mit Stempelzeit nicht waehlbar"
    assert r["alleDa"] and len(r["ids"]) == len(set(r["ids"])) == 6
    assert r["ids"][:len(r["alt"])] == r["alt"], "Projektzeit-Liste bleibt vorne in ihrer Reihenfolge"
    assert set(r["zusatz"]) <= {"", "Büro", "ausgetreten"} and "Büro" in r["zusatz"]


def test_kopf_nutzt_die_vereinigung(index_html):
    b = _block(index_html, "function BueroPortalNeu(props){", "\n}")
    assert "const kopfListe=_bxKopfListe(props.monteure,ym);" in b
    assert "kopfListe.map(function(x){return h(\"option\"" in b


# ── Alte Ansicht weg ────────────────────────────────────────────────────────
def test_alte_ansicht_entfernt(index_html):
    assert "data-bx-alte-ansicht" not in index_html
    assert '},"Alte Ansicht")' not in index_html
    b = _block(index_html, "function BueroPortal(props){", "\n}")
    assert "return React.createElement(BueroPortalNeu,props);" in b
    assert "localStorage" not in b


# ── doppelte Ueberschriften ─────────────────────────────────────────────────
def test_doppelte_ueberschriften_weg_anker_bleiben(index_html):
    assert ",\"Entfernungszulage\")\r\n" not in index_html and "\"Stempelzeiten (PZE)\")" not in index_html
    assert "React.createElement('div',{id:\"bx-abschnitt-zulagen\"" in index_html
    assert "React.createElement('div',{id:\"bx-abschnitt-stempel\"" in index_html
    assert "React.createElement('h3',{id:\"bx-abschnitt-stunden\"" in index_html


def test_stempelzeiten_folgen_dem_kopf(index_html):
    assert "(tab==='pze'&&!props.startWid)" in index_html


def test_bauwochenbericht_im_mitarbeiter_monat_nur_unter_weiteres(index_html):
    assert "_zeBwbDarf&&!(imPortal===true&&startWid)" in index_html
    assert '[["projekte","Bauwochenberichte"],["abwesend","Abwesenheiten"],["tank","Tank"]]' in index_html


# ── Exporte: keiner entfernt/umbenannt, Erzeuger byte-gleich ────────────────
EXPORTE = {
    # Name: (Anfang, Ende, md5 gemessen an Paket 14 / feature/kw-auswahl)
    "genXls": ("const genXls=(title,subtitle,headers,rows,filename,opts={})=>{", "\n};", None),
    "exportWochenStz": ("  const exportWochenStz=", "\n  const ", None),
    "exportTagesStz": ("  const exportTagesStz=", "\n  const ", None),
    "exportBauwochenbericht": ("  const exportBauwochenbericht=", "\n  const ", None),
    "exportAllXls": ("  const exportAllXls=", "\n  const ", None),
    "exportMonatXls": ("  const exportMonatXls=", "\n  const ", None),
    "exportMonatPdf": ("  const exportMonatPdf=", "\n  const ", None),
    "_pzePdf": ("function _pzePdf", "\n}", None),
    "generateBWB": ("  const generateBWB=", "\n  const ", None),
}
MD5 = {  # gemessen am Stand vor Paket 15 (803a6ce = 3.9.1117; Export-Code = live 3.9.1113) - vorher == nachher
    "_pzePdf": "28ce27f39a9ca80a1da2459c9f56ac5a", "exportAllXls": "455bd880ba495ce2b213339f63ae24a9",
    "exportBauwochenbericht": "5f9d538915a4fb03a775d5e3f007621f", "exportMonatPdf": "64b8b5fa3b504d0b17ecfffd3c167885",
    "exportMonatXls": "9da056ce95edf3fb89816f754da83338", "exportTagesStz": "8d9fa729062aa44f9500e87128f74f31",
    "exportWochenStz": "d26cc4f053fea48a7819e61959523199", "genXls": "8472db9de0084b7a6cdf1a492758c930",
    "generateBWB": "85fd68a888fd0aaca5a390129f5f157c",
}


def _md5(t):
    return hashlib.md5(t.replace("\r\n", "\n").encode("utf-8")).hexdigest()


@pytest.mark.parametrize("name", sorted(EXPORTE))
def test_exportweg_byte_gleich(index_html, name):
    a, e, _ = EXPORTE[name]
    assert _md5(_block(index_html, a, e)) == MD5[name], name


KNOEPFE = ["onClick:exportMonatXls", "onClick:exportMonatPdf", "onClick:exportWochenStz", "onClick:exportXls",
           "onClick:()=>exportTagesStz(i)", "onClick:exportAllXls", "Monat Excel", "Monat PDF", "Wochen-Stundenbestätigung",
           "Übersicht Excel", "PZE-PDF (Lohnverrechner)"]


@pytest.mark.parametrize("k", KNOEPFE)
def test_exportknopf_unveraendert_da(index_html, k):
    assert k in index_html, k


# ── Paket 15 Nachbau: EINE Export-Leiste je Abschnitt, Leerzustand, Kopf-Monat ────────────────────
# Verhalten im Browser: tests/test_bueroportal_p15_leiste_browser.py (jeder Exportweg liefert dieselbe Datei wie vorher).
def test_exportleisten_im_mitarbeiter_monat(index_html):
    assert "function _bxExporte(kinder){" in index_html and "'data-bx-exporte':'1'" in index_html
    kv = _block(index_html, "function KVZulagenReport(props){", "\n}")
    pze = _block(index_html, "function PZEView(props){", "\n}")
    assert "_imMaMonat?_bxExporte([_pzeKnopf])" in kv
    assert "_bxExporte([_xlsKnopf,_pdfKnopf])" in pze
    assert "_zeExpHuelle(isAdmin&&selWorker&&" in index_html
    assert "return _zeImMaMonat?_bxExporte(k):React.createElement.apply(null,[React.Fragment,{}].concat(k));" in index_html


# Die Knopf-Elemente selbst (onClick, Sperre, Beschriftung) sind Wort fuer Wort die alten - nur ihr Platz aendert sich.
KNOPF_AUSDRUECKE = [
    "h('button',{onClick:_pzeBtn,disabled:!ezWid||ezStand!=='ok',",
    "h('button',{onClick:_xls,style:{...btnS,background:COLORS.SUCCESS,color:'#fff',border:'none'}},_ikVw('tabelle','Excel'))",
    "h('button',{onClick:_pdf,disabled:pzeEzStand!=='ok',",
    "React.createElement('button',{onClick:exportMonatXls,disabled:zeMonLaedt,style:{...xBtn(\"xls\"),...(zeMonLaedt?_zeAus:{})}},_ik(\"tabelle\",16),\"Monat Excel\")",
    "React.createElement('button',{onClick:exportMonatPdf,disabled:zeMonLaedt,style:{...xBtn(\"pdf\"),...(zeMonLaedt?_zeAus:{})}},_ik(\"drucker\",16),\"Monat PDF\")",
    "React.createElement('button',{onClick:exportWochenStz,disabled:!(weekTotal>0),",
    "React.createElement('button',{onClick:exportXls,disabled:!_nEintrZE,",
    "React.createElement('button',{onClick:()=>window.print(),disabled:!_nEintrZE,",
    "onClick:()=>exportTagesStz(i),",
]


@pytest.mark.parametrize("k", KNOPF_AUSDRUECKE)
def test_knopf_ausdruck_wortgleich(index_html, k):
    assert index_html.count(k) == 1, k


def test_leerzustand_einheitlich(index_html):
    assert "function _bxLeer(detail){" in index_html
    b = _block(index_html, "function _bxLeer(detail){", "\n")
    assert "'Keine Einträge'" in b
    assert index_html.count("_bxLeer(") >= 5  # Definition + Stunden + Zulagen (2) + Stempelzeiten


def test_kopfmonat_ohne_eigene_pfeile(index_html):
    kv = _block(index_html, "function KVZulagenReport(props){", "\n}")
    pze = _block(index_html, "function PZEView(props){", "\n}")
    assert "const _imMaMonat=!!(props.startWid&&props.startYm);" in kv and "const _imMaMonat=!!(props.startWid&&props.startYm);" in pze
    assert ",_imMaMonat?null:h('button',{onClick:_ezHeute," in kv
    assert ",_imMaMonat?null:h('input',{type:'date',value:von," in pze and ",_imMaMonat?null:h('input',{type:'date',value:bis," in pze
    assert "_zeImMaMonat?React.createElement('span',{'data-bx-monat-fest':'1'" in index_html
