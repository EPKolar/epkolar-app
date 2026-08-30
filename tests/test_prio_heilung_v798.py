# -*- coding: utf-8 -*-
"""v3.9.798 TEIL D — Prio-Heilung "keine" -> "normal" (offene Scheine, App heilt + pusht).

Sebastian: bei EP Kolar ist Prio "keine" = vergessen. Ein OFFENER Schein (AS_GRP_OFFEN) mit
Prio "keine" wird beim Pull auf "normal" gehoben und regulaer gepusht (AK_PRIOR 4 laeuft ueber
den v615-Dirty-Check, weil lokal normal != roh keine; push_pending + bestehender Drain).
Erledigt/abgerechnet/storniert werden NIE angefasst. "keine" ist aus den App-Selects raus.

popstate/async-Sync ist nicht node-testbar -> die Heil-ENTSCHEIDUNG ist als pure Funktion
_prioHeilBedarf ausgelagert und wird hier per node-eval geprueft; die Verdrahtung (Update-Block,
Neu-Zweig, Select-Filter) wird statisch gepinnt.
"""
from conftest import run_node_snippet

_OFFEN = 'const AS_GRP_OFFEN=["aufgenommen","freigegeben","in_bearbeitung","aufgeschoben"];'


def _heal(node_exe, index_html, prio, status):
    a = index_html.index("function _prioHeilBedarf(")
    fn = index_html[a:index_html.index("}", a) + 1]
    snip = _OFFEN + fn + f";process.stdout.write(String(_prioHeilBedarf({prio!r},{status!r})))"
    return run_node_snippet(node_exe, snip).strip()


def test_keine_offen_wird_geheilt(node_exe, index_html):
    for st in ("aufgenommen", "freigegeben", "in_bearbeitung", "aufgeschoben"):
        assert _heal(node_exe, index_html, "keine", st) == "true", "keine+offen (%s) muss heilen" % st


def test_keine_erledigt_bleibt(node_exe, index_html):
    for st in ("erledigt", "abgerechnet", "bar_bezahlt", "storniert"):
        assert _heal(node_exe, index_html, "keine", st) == "false", "keine+%s darf NICHT heilen" % st


def test_nicht_keine_bleibt(node_exe, index_html):
    assert _heal(node_exe, index_html, "normal", "aufgenommen") == "false"
    assert _heal(node_exe, index_html, "hoch", "aufgenommen") == "false"
    # Leer/undefined ist NICHT "keine" (d1: strikt "keine") -> keine Heilung.
    assert _heal(node_exe, index_html, "", "aufgenommen") == "false"


def test_verdrahtung_pull_pfad(index_html):
    # Update-Block: effektiver Wert nach Mapping/Guards, dann push_pending.
    assert "const _effPrio798=(('prioritaet' in upd)?upd.prioritaet:existing.prioritaet);" in index_html
    assert "if(_prioHeilBedarf(_effPrio798,_effStatus798)){upd.prioritaet='normal';upd.push_pending=true;}" in index_html
    # Neu-Scheine-Zweig.
    assert "if(_prioHeilBedarf(newAs.prioritaet,newAs.scheinstatus)){newAs.prioritaet='normal';newAs.push_pending=true;}" in index_html
    # KEIN Sonder-Push-Weg: der bestehende Post-Sync-Drain bleibt der einzige Sender.
    assert "const _dr=await _juprowaDrainPending(10);" in index_html, "Drain-Aufruf veraendert (Sonder-Push-Weg?)"


# v3.9.919 NACHGEZOGEN - nicht abgeschwaecht. Hier stand:
#     assert 'filter(([k])=>k!="keine"||a.prioritaet==="keine")' in index_html
#     assert 'filter(([k])=>k!="keine"||form.prioritaet==="keine")' in index_html
#
# Das war GENAU die kaputte Bedingung: sie prueft die ZEICHENKETTE, waehrend
# die Wertzeile darueber den ZUSTAND prueft (a.prioritaet||"keine"). Bei einem
# Schein ohne Prioritaet - Feld fehlt, null oder leerer Text, alle drei kommen
# vor - stand der Wert damit auf einer Option, die herausgefiltert war, und das
# Auswahlfeld zeigte die erste Stufe aus AS_PRIO: "aufgeschoben". Ein Schein
# ohne Prioritaet sah aus wie ein ruhender Auftrag.
#
# Der Riegel haette das nie gefunden, aber er waere gegen die Reparatur ROT
# geworden - er hielt den Fehler fest. Der dritte dieser Art an einem Tag.
#
# Die Absicht (v3.9.798 d3) bleibt unveraendert und wird jetzt AUSGEFUEHRT:
# tests/test_prio_leer_v919.py schickt beide Fundorte mit sechs Faellen durch
# Node und prueft die Eigenschaft, aus der der Fehler entstand -
#     DER GEWAEHLTE WERT MUSS UNTER DEN ANGEBOTENEN OPTIONEN SEIN -
# plus, dass "keine" bei einem Schein MIT Prioritaet nicht waehlbar ist.
def test_keine_aus_selects_raus(index_html):
    """Beide Auswahlen filtern "keine" heraus, solange der Schein sie nicht traegt.

    Gemessen wird die Bedingung am ZUSTAND, nicht an der Zeichenkette.
    """
    for name, ausdruck in (("Liste", "a.prioritaet"),
                           ("Formular", "form.prioritaet")):
        muster = ("filter(([k])=>k!==\"keine\"||(" + ausdruck
                  + "||\"keine\")===\"keine\")")
        assert index_html.count(muster) == 1, (
            "%s prueft nicht den ZUSTAND, sondern wieder die Zeichenkette - "
            "genau daraus entstand v3.9.919: ein Schein OHNE Prioritaet zeigte "
            "die erste Stufe aus AS_PRIO, also aufgeschoben." % name)
