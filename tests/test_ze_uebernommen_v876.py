# -*- coding: utf-8 -*-
"""v3.9.876 - LOHN: der Uebernahme-Merker wurde an abgeschlossenen Scheinen nie gesetzt.

ABLAUF, wie er bis v3.9.875 lief (im Code nachgegangen, Zeile fuer Zeile):

  1. Monteur traegt an einem ABGESCHLOSSENEN Schein Zeit ein und speichert.
  2. _asZeitUebernahme legt den time_entry an  -> Zeit ist gebucht.  OK
  3. updAs(s.id,{ze_uebernommen:true})        -> Monteur-Riegel greift, `return`
                                                 VOR dem Write. Merker weg.
  4. Erfolgs-Meldung feuert trotzdem.

ZWEI FOLGEN, beide Geld:

  (a) Weil der Merker fehlt, laeuft Schritt 2 bei JEDEM weiteren Speichern erneut.
      Dass daraus keine doppelte Lohnstunde wird, verdankt sich allein dem
      partiellen UNIQUE-Index uq_time_entries_as (sql/TIME_ENTRIES_UNIQUE_v1.sql).
      Der Client versucht die Doppelbuchung dauerhaft; der Index faengt sie ab.
      Faellt der Index bei einer Migration, faellt Lohn. Der Index traegt damit
      eine Last, fuer die er nie gedacht war.

  (b) Schlimmer, weil es SCHON HEUTE eintritt: der Korrektur-Zweig ist an
      `if(!_row.ze_uebernommen)` gehaengt. Bleibt der Merker falsy, wird er nie
      erreicht. Monteur traegt 7h ein, merkt es waren 9h, korrigiert am Schein:
      der Schein zeigt 9h, die Lohnzeit bleibt fuer immer bei 7h. Gemeldet wird
      dabei "war bereits uebernommen (anderes Geraet)" - ein Geraet, das es nicht
      gibt. Schein und Lohnzeit laufen still auseinander, in beide Richtungen.

FIX, bewusst eng: eine Ausnahme im Riegel, die NUR greift, wenn ausser dem Merker
nichts mitgeschickt wird. Ein blosses `delete _u.ze_uebernommen; weiter` haette den
Riegel fuer alle uebrigen Felder mitgeoeffnet - das ist der Unterschied zwischen
einer Ausnahme und einem Loch.

Dazu meldet updAs jetzt zurueck, OB geschrieben wurde. Ohne das kann kein Aufrufer
zwischen Erfolg und stillem Block unterscheiden - genau daran lag es, dass die App
jahrelang Erfolg meldete, den sie nie geprueft hatte.

BEWUSST NICHT GEAENDERT: fahrzeit/stunden bleiben fuer Monteure an abgeschlossenen
Scheinen aenderbar (sie stehen nicht in _MT_GRUND). Das ist eine Regelfrage, keine
Fehlerbehebung - und mit diesem Fix folgt die Lohnzeit einer Korrektur jetzt nach.
Wer das sperren will, sperrt sichtbar (disabled), nicht durch stilles Zuruecksetzen.
"""
import re


def _updas(index_html):
    i = index_html.find("const updAs=(id,updates)=>{")
    assert i != -1, "updAs nicht gefunden"
    j = index_html.find("const exportOffa=", i)
    assert j != -1, "Ende von updAs nicht gefunden"
    return index_html[i:j]


def _uebernahme(index_html):
    i = index_html.find("const _asZeitUebernahme=async(schein)=>{")
    assert i != -1, "_asZeitUebernahme nicht gefunden"
    return index_html[i:i + 6000]


# -- Die Ausnahme existiert und ist ENG ---------------------------------------

def test_merker_darf_durch_den_riegel(index_html):
    block = _updas(index_html)
    assert "var _nurMerker=(Object.keys(_u).length===1&&'ze_uebernommen'in _u);" in block, (
        "Die Ausnahme fuer das reine Bookkeeping-Update fehlt - dann wird der "
        "Uebernahme-Merker an abgeschlossenen Scheinen wieder nie gesetzt:\n" + block[:900]
    )
    assert "&&!_nurMerker){" in block, (
        "Die Ausnahme haengt nicht am Riegel:\n" + block[:900]
    )


def test_ausnahme_greift_nur_bei_genau_einem_feld(index_html):
    """Die Grenze ist das Ganze. Ohne die Laengenpruefung waere es ein Loch:
    ein Client koennte ze_uebernommen zusammen mit beliebigen anderen Feldern
    schicken und damit den Riegel fuer alles aushebeln."""
    block = _updas(index_html)
    m = re.search(r"var _nurMerker=\((.*?)\);", block)
    assert m, "_nurMerker nicht auswertbar"
    bed = m.group(1)
    assert "Object.keys(_u).length===1" in bed, (
        "Die Ausnahme prueft nicht mehr, dass NUR der Merker mitkommt - damit "
        "waere der Monteur-Riegel fuer beliebige Felder offen:\n" + bed
    )
    assert "'ze_uebernommen'in _u" in bed, (
        "Die Ausnahme haengt nicht am Merker-Feld:\n" + bed
    )


def test_riegel_bleibt_fuer_alles_andere_scharf(index_html):
    """Gegenprobe: der Riegel und seine Meldung muessen unveraendert stehen."""
    block = _updas(index_html)
    assert "if(s&&!AS_GRP_OFFEN.includes(s.scheinstatus)" in block, (
        "Der Abschluss-Riegel selbst ist weg - Monteure koennten dann Termin, "
        "Status und Grunddaten abgeschlossener Scheine aendern."
    )
    assert "Abgeschlossener Schein" in block, "Die Riegel-Meldung ist weg"
    assert "if('monteur'in _u)delete _u.monteur;" in block, (
        "Der Monteur-Zuweisungsschutz ist weg (v3.9.535) - das war die Ursache "
        "eines echten RLS-403, der den Sync still abbrechen liess."
    )


# -- updAs sagt, ob geschrieben wurde ----------------------------------------

def test_updas_meldet_erfolg_zurueck(index_html):
    block = _updas(index_html)
    assert "return true;" in block, (
        "updAs meldet keinen Erfolg zurueck - dann kann kein Aufrufer einen still "
        "geblockten Write von einem echten unterscheiden."
    )
    assert block.count("return false;") >= 2, (
        "Die Abbruch-Pfade melden keinen Misserfolg zurueck (erwartet: Riegel + "
        "Leer-Update). Gefunden: %d" % block.count("return false;")
    )


def test_beide_meldungen_pruefen_den_ausgang(index_html):
    """Der Kern der Ehrlichkeit: kein Erfolgstext ohne geprueften Erfolg."""
    block = _uebernahme(index_html)
    assert "var _mOk=updAs(s.id,{ze_uebernommen:true});" in block, (
        "Der Erst-Uebernahme-Zweig faengt den Rueckgabewert nicht ab."
    )
    assert "var _mOkD=updAs(s.id,{ze_uebernommen:true});" in block, (
        "Der UNIQUE-Konflikt-Zweig faengt den Rueckgabewert nicht ab."
    )
    assert "_mOk!==false?" in block and "_mOkD!==false?" in block, (
        "Mindestens eine Meldung feuert weiterhin unabhaengig vom Ausgang - genau "
        "das liess die App jahrelang Erfolg melden, den sie nie geprueft hatte."
    )
    assert "bitte dem Buero melden" in block, (
        "Es fehlt der Weg nach vorn in der Fehlermeldung. Ein Monteur, der nur "
        "'ging nicht' liest, meldet es niemandem."
    )


def test_marker_kommt_weiterhin_erst_nach_bestaetigtem_insert(index_html):
    """v3.9.811 #3 darf nicht verloren gehen: erst buchen, dann merken.
    Andersherum entstuende ein Merker ohne Zeiteintrag - die Zeit waere weg."""
    block = _uebernahme(index_html)
    i_post = block.find('await _sbPost("time_entries"')
    i_mark = block.find("var _mOk=updAs(s.id,{ze_uebernommen:true});")
    assert i_post != -1 and i_mark != -1, "Insert oder Merker nicht gefunden"
    assert i_post < i_mark, (
        "Der Merker wird vor dem bestaetigten Insert gesetzt - bei einem "
        "fehlgeschlagenen Insert waere die Zeit dann dauerhaft verloren."
    )


def test_merker_ist_kein_push_feld(index_html):
    """ze_uebernommen darf NIE nach Juprowa/OFFA gehen - sonst loest ein reines
    App-Bookkeeping einen Fremdsystem-Push aus."""
    i = index_html.find("JUPROWA_PUSH_FIELDS")
    assert i != -1, "JUPROWA_PUSH_FIELDS nicht gefunden"
    block = index_html[i:i + 3000]
    assert "ze_uebernommen" not in block, (
        "ze_uebernommen steht in der Push-Feldliste - dann wuerde der Merker "
        "einen OFFA-Push ausloesen."
    )


# -- Umkehrprobe --------------------------------------------------------------

def test_selbsttest_riegel_schlagen_beim_rueckbau_an(index_html):
    ohne = index_html.replace("&&!_nurMerker){", "){", 1)
    assert ohne != index_html, "Rueckbau griff nicht - Anker veraltet"
    assert "&&!_nurMerker){" not in _updas(ohne), (
        "Umkehrprobe: der Ausnahme-Riegel wuerde nicht anschlagen"
    )

    ohne2 = index_html.replace("var _mOk=updAs(s.id,{ze_uebernommen:true});",
                               "updAs(s.id,{ze_uebernommen:true});", 1)
    assert ohne2 != index_html, "Rueckbau 2 griff nicht - Anker veraltet"
    assert "var _mOk=updAs(s.id,{ze_uebernommen:true});" not in _uebernahme(ohne2), (
        "Umkehrprobe: der Ehrlichkeits-Riegel wuerde nicht anschlagen"
    )
