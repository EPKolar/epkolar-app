# -*- coding: utf-8 -*-
"""A55 BERICHT9 (17.11.2026) - Arbeitsschein-Oberflaeche am Samsung A55.

Nur Anzeige/Bedienung. Jede Pruefung ist eine Funktion, die eine Fehlerliste
liefert; die Umkehrprobe setzt den alten Zustand ein und verlangt, dass sie
anschlaegt (ein Riegel, der nie ausloest, ist kein Riegel).

  1  Aktionsreihe im Formular: Raster, nowrap, jede Taste mit Linien-Ikone
  2  Schein nicht mehr in OFFA gelistet: Aktualisieren / Storno /
     Speichern & PDF gesperrt, Hinweis oben (GF Sebastian 17.11.)
  3  Formular oeffnet oben, zweites Abbrechen am Ende
  4  Fussleiste weg, solange am Handy ein Textfeld den Fokus hat
  5  Kommentar-Platzhalter kurz, deutsch, ohne Tastenkuerzel
  6  'Alle' hebt Schnellfilter UND Status auf; kein doppelter 'Offen'-Chip
  7  Emoji -> Linien-Ikonen (Etiketten, Kontakt, Sync-Fenster)
  8  Ort nicht abgeschnitten, 'um' nur mit Uhrzeit
  9  Kennzeichen 'nicht mehr in OFFA' auf Karte und Tabellenzeile
"""
import json
import re
import shutil

import pytest

from conftest import run_node_snippet
from _hilfen import nur_code


def _zwischen(html, a, e):
    i = html.index(a)
    return html[i:html.index(e, i)]


# ---------- 1 ----------
def _p1(html):
    f = []
    try:
        reihe = _zwischen(html, "'data-as-aktionen': \"1\"", "v3.9.547 TASK B: Unterschriften-Karte")
    except ValueError:
        return ["Aktionsreihe (data-as-aktionen) nicht gefunden"]
    if 'display:"grid"' not in reihe:
        f.append("Aktionsreihe ist kein Raster")
    if "flex:1" in reihe:
        f.append("flex:1 in der Aktionsreihe zurueck")
    if "⊘" in reihe:
        f.append("Textzeichen statt Ikone bei Storno")
    knoepfe = reihe.count("React.createElement('button'")
    ikonen = reihe.count("_asIk(")
    if knoepfe != 4 or ikonen != 4:
        f.append("Knoepfe %d / Ikonen %d (erwartet 4/4)" % (knoepfe, ikonen))
    if reihe.count("_asAktKn") != 4:
        f.append("nicht jede Taste traegt das Knopfmass _asAktKn")
    if '_asIk("speichern",editId?"Aktualisieren":"Speichern")' not in reihe:
        f.append("Aktualisieren ohne Ikone")
    kn = re.search(r"const _asAktKn=\{[^}]*\}", html)
    if not kn or 'whiteSpace:"nowrap"' not in kn.group(0) or "padding" not in kn.group(0):
        f.append("_asAktKn ohne nowrap/padding")
    if "{...bpS,flex:1}}, editId?\"Aktualisieren\"" in html:
        f.append("alte Aktualisieren-Taste ohne Ikone")
    return f


def test_1_aktionsreihe(index_html):
    assert _p1(index_html) == []


def test_1_umkehr(index_html):
    k = index_html.replace('_asIk("speichern",editId?"Aktualisieren":"Speichern")', 'editId?"Aktualisieren":"Speichern"', 1)
    assert k != index_html and _p1(k)
    k = index_html.replace('_asIk("verbot","Storno")', '"⊘ Storno"', 1)
    assert k != index_html and _p1(k)


def test_1_rueckfrage_und_klickwege_bleiben(index_html):
    reihe = _zwischen(index_html, "'data-as-aktionen': \"1\"", "v3.9.547 TASK B: Unterschriften-Karte")
    for weg in ("onClick: saveAs,", "onClick: ()=>genAsPdf(form)", "onClick: ()=>{storno(editId);setSub(\"liste\");}",
                "onClick: ()=>deleteAs(editId)", "...bdS,"):
        assert weg in reihe, weg
    assert 'if(!await _confirmModal("Arbeitsschein wirklich stornieren?",{variant:"danger"}))return;' in index_html


# ---------- 2 ----------
def _p2(html):
    """GF 17.11. (Chat-Claude-Messung): 'nicht im Feed' ist fuer 2/3 aller Scheine der Normalzustand -> die
    Sperre von Aktualisieren/Storno daran war ein Fehlalarm und ist entfernt. Hier: sie darf nicht zurueckkommen."""
    f = []
    for sym in ("_asOffaSperre", "_AS_OFFA_SPERRE_TXT", "data-as-offa-sperre-hinweis", "data-as-offa-sperre-grund", "_nichtImFeed(form)"):
        if sym in html:
            f.append("Fehlalarm-Sperre wieder da: " + sym)
    return f


def test_2_sperre(index_html):
    assert _p2(index_html) == []


def test_2_umkehr(index_html):
    k = index_html.replace("onClick: saveAs,", "onClick: saveAs, disabled: _asOffaSperre,", 1)
    assert k != index_html and _p2(k)


@pytest.mark.skipif(shutil.which("node") is None, reason="node fehlt")
def test_2_bedingung_rechnet(node_exe, index_html):
    """Die Sperre haengt an derselben reinen Pruefung wie Hinweis und Kennzeichen."""
    fn = re.search(r"function _offaNichtImFeed\(s,maxMs\)\{.*?\n", index_html).group(0)
    js = ("const AS_GRP_OFFEN=['aufgenommen','freigegeben','aufgeschoben','in_bearbeitung'];" + fn +
          "const mx=Date.parse('2026-11-16T15:31:00Z');"
          "const sperre=(editId,form)=>!!(editId&&_offaNichtImFeed(form,mx));"
          "console.log(JSON.stringify([sperre('x',{juprowa_id:1,scheinstatus:'in_bearbeitung',juprowa_sync_at:'2026-09-02T10:00:00Z'}),"
          "sperre('x',{juprowa_id:1,scheinstatus:'in_bearbeitung',juprowa_sync_at:'2026-11-16T15:30:00Z'}),"
          "sperre(null,{juprowa_id:1,scheinstatus:'in_bearbeitung',juprowa_sync_at:'2026-09-02T10:00:00Z'}),"
          "sperre('x',{juprowa_id:null,scheinstatus:'in_bearbeitung',juprowa_sync_at:'2026-09-02T10:00:00Z'})]));")
    assert json.loads(run_node_snippet(node_exe, js)) == [True, False, False, False]


# ---------- 3 ----------
def _p3(html):
    f = []
    # A55 Vollpruefung 19.11.: der Formularkopf rollt selbst ins Bild (Uebersicht kann darueber stehen); Rueckfall weiter nach oben
    if "_react.useLayoutEffect.call(void 0, ()=>{if(sub!==\"form\")return;try{const _af=document.querySelector('[data-as-form=\"1\"]');if(_af&&_af.scrollIntoView){_af.scrollIntoView({block:\"start\"});}else{const _mp=document.querySelector('.main-pad');if(_mp)_mp.scrollTop=0;window.scrollTo(0,0);}}catch(_se){}},[sub,editId]);" not in html             or "key: \"as-form\", 'data-as-form': \"1\"" not in html:
        f.append("Formular springt nicht nach oben")
    m = re.search(r"'data-as-abbrechen-unten': \"1\".{0,400}", html)
    if not m or 'onClick: ()=>{setSub("liste");setEditId(null);}' not in m.group(0) or '_asIk("kreuz","Abbrechen")' not in m.group(0):
        f.append("zweites Abbrechen fehlt")
    return f


def test_3_oben_und_abbrechen_unten(index_html):
    assert _p3(index_html) == []


def test_3_umkehr(index_html):
    k = index_html.replace("'data-as-abbrechen-unten'", "'data-x'", 1)
    assert _p3(k)
    k = index_html.replace("},[sub,editId]);", "},[]);", 1)
    assert _p3(k)


# ---------- 4 ----------
def _p4(html):
    f = []
    if "@media(max-width:600px){html.epk-tastatur .bottom-nav{display:none !important}}" not in html:
        f.append("CSS-Regel fehlt")
    if 'document.documentElement.classList.toggle("epk-tastatur",mob&&_epkIstTextfeld(document.activeElement))' not in html:
        f.append("Klassenschalter fehlt")
    if 'document.addEventListener("focusin",setz);document.addEventListener("focusout",function(){setTimeout(setz,0);});' not in html:
        f.append("focusin/focusout fehlt")
    return f


def test_4_fussleiste(index_html):
    assert _p4(index_html) == []


def test_4_umkehr(index_html):
    k = index_html.replace("html.epk-tastatur .bottom-nav{display:none !important}", "html.epk-tastatur .bottom-nav{}", 1)
    assert _p4(k)


@pytest.mark.skipif(shutil.which("node") is None, reason="node fehlt")
def test_4_textfeld_erkennung(node_exe, index_html):
    fn = re.search(r"function _epkIstTextfeld\(el\)\{.*?\n", index_html).group(0)
    js = (fn + "const e=(tag,o)=>Object.assign({tagName:tag},o||{});"
          "console.log(JSON.stringify([_epkIstTextfeld(e('INPUT',{type:'text'})),_epkIstTextfeld(e('INPUT',{type:'search'})),"
          "_epkIstTextfeld(e('TEXTAREA')),_epkIstTextfeld(e('INPUT',{type:'date'})),_epkIstTextfeld(e('INPUT',{type:'checkbox'})),"
          "_epkIstTextfeld(e('SELECT')),_epkIstTextfeld(e('INPUT',{type:'text',disabled:true})),_epkIstTextfeld(e('TEXTAREA',{readOnly:true})),"
          "_epkIstTextfeld(null),_epkIstTextfeld(e('DIV',{isContentEditable:true}))]));")
    assert json.loads(run_node_snippet(node_exe, js)) == [True, True, True, False, False, False, False, False, False, True]


# ---------- 5 ----------
def _p5(html):
    f = []
    m = re.search(r"placeholder:'(Kommentar[^']*)',rows:2", html)
    if not m:
        return ["Kommentarfeld nicht gefunden"]
    ph = m.group(1)
    for w in ("Ctrl", "Mention", "Enter"):
        if w in ph:
            f.append("'%s' im Platzhalter" % w)
    if len(ph) > 30:
        f.append("Platzhalter zu lang (%d)" % len(ph))
    if "matchMedia('(pointer:fine)')" not in html or "'Strg+Enter sendet'" not in html:
        f.append("Tastenhinweis fuer Maus fehlt")
    return f


def test_5_kommentar(index_html):
    assert _p5(index_html) == []


def test_5_umkehr(index_html):
    k = index_html.replace("placeholder:'Kommentar, @Name erwähnen'", "placeholder:'Kommentar… (@Name = Mention, Ctrl+Enter = Senden)'", 1)
    assert k != index_html and _p5(k)


# ---------- 6 ----------
def _p6(html):
    f = []
    if "onClickCapture:chip.key===\"\"?()=>setFilterStatus(\"alle\"):undefined" not in html:
        f.append("'Alle' hebt den Status-Filter nicht auf")
    if "onClick:()=>setQuickFilter(chip.key)" not in html:
        f.append("Klickweg setQuickFilter verloren")
    if "const _asQuickDoppelt=(quickFilter===\"offen\"&&filterStatus===\"offen_bearb\")||(quickFilter===\"erledigt\"&&filterStatus===\"fertig\");" not in html:
        f.append("Doppel-Erkennung fehlt")
    if "if(quickFilter&&!_asQuickDoppelt)chips.push(" not in html:
        f.append("doppelter Schnellfilter-Chip")
    if "(quickFilter&&!_asQuickDoppelt?1:0)" not in html:
        f.append("Doppelung zaehlt im Sammelknopf mit")
    if "Kein Schnellfilter - der Status-Filter darunter wirkt weiter" in nur_code(html):
        f.append("alter Titel")
    return f


def test_6_filter(index_html):
    assert _p6(index_html) == []


def test_6_umkehr(index_html):
    k = index_html.replace("if(quickFilter&&!_asQuickDoppelt)chips.push(", "if(quickFilter)chips.push(", 1)
    assert k != index_html and _p6(k)
    k = index_html.replace("onClickCapture:chip.key===\"\"?()=>setFilterStatus(\"alle\"):undefined", "", 1)
    assert k != index_html and _p6(k)


# ---------- 7 ----------
WEG = ['"Durchzuführen * 🎤"', '"Notizen 🎤"', '"📞 Kontakt (OFFA)"', "\"☎\")", "\"✉\")",
       '"📡 Verbindung & Sync"', '"✅ Alles synchron"', '"🔄 Jetzt synchronisieren"', '"⏳ Synchronisiere..."']


def _p7(html):
    code = nur_code(html)
    f = [w for w in WEG if w in code]
    for s in ('_asIk("person","Kontakt (OFFA)")', '"Tel.")', '_ik("brief",14)', '_ik("verbindung",16), "Verbindung & Sync"',
              '_ik("abnahme",14), "Alles synchron"', '_ik("drehen",14)'):
        if s not in html:
            f.append("fehlt: " + s)
    return f


def test_7_ikonen_statt_emoji(index_html):
    assert _p7(index_html) == []


def test_7_umkehr(index_html):
    k = index_html.replace('"Notizen" )', '"Notizen 🎤" )', 1)
    assert k != index_html and _p7(k)


def test_7_offa_excel_bleibt(index_html):
    """test_offa_import_removed_v780 pinnt den Wortlaut (seit GF-Freigabe 19.11.2026 ohne Emoji)."""
    assert 'style: {...xBtn("xls")}}, "EXCEL Export"  )' in index_html  # GF 24.11.2026: Beschriftung 'OFFA Excel' -> 'EXCEL Export' (nur Text; Export, Spalten, Format unveraendert)


# ---------- 8 ----------
def _p8(html):
    f = []
    if 'fdt(form.aufgenommen), " um "  , form.aufgZeit)' in html:
        f.append("'um' ohne Uhrzeit")
    if 'fdt(form.aufgenommen), form.aufgZeit?" um "+form.aufgZeit:"")' not in html:
        f.append("Aufgenommen-Zeile fehlt")
    if 'gridTemplateColumns:isMob?"88px minmax(0,1fr)":"80px 1fr"' not in html:
        f.append("PLZ/Ort-Raster am Handy alt")
    if "value: form.kundOrt, title: form.kundOrt||undefined," not in html:
        f.append("voller Ort nicht im title")
    return f


def test_8_ort_und_uhrzeit(index_html):
    assert _p8(index_html) == []


def test_8_umkehr(index_html):
    k = index_html.replace('fdt(form.aufgenommen), form.aufgZeit?" um "+form.aufgZeit:"")', 'fdt(form.aufgenommen), " um "  , form.aufgZeit)', 1)
    assert k != index_html and _p8(k)


# ---------- 9 ----------
def _p9(html):
    """GF 17.11.: Kennzeichen 'nicht mehr in OFFA' auf Karte/Zeile entfernt (Fehlalarm) - darf nicht zurueckkommen."""
    return ["Kennzeichen wieder da"] if ("data-offa-nicht-im-feed-karte" in html or "_nichtImFeed(a)" in html) else []


def test_9_kennzeichen(index_html):
    assert _p9(index_html) == []


def test_9_umkehr(index_html):
    k = index_html + "<span data-offa-nicht-im-feed-karte></span>"
    assert _p9(k)
