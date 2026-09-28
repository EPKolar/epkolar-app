# -*- coding: utf-8 -*-
"""Anklickbare Elemente, die KEINE Knoepfe sind - und ohne Tastaturzugang.

🔴 WARUM ES DIESEN RIEGEL GIBT
Der Auftrag vom 27.09.2026 nannte "drei namenlose Symbol-Knoepfe in ProjList"
und sagte dazu: *die Luecke im Suchmuster ist wichtiger als die drei Knoepfe.*
Das hat sich bestaetigt, nur anders als vermutet. Gemessen hat ProjList NULL
namenlose Knoepfe. Was dort steht, sind anklickbare `div`-Elemente.

Und die kann ein Knopf-Abtaster **prinzipiell** nicht finden. Seine
Grundgesamtheit ist `button`; ein `div` mit `onClick` liegt ausserhalb, egal
wie viele Schreibweisen und Anfuehrungszeichen er kennt. Das ist nicht mehr
die Krankheit "zu kleines Alphabet" - es ist ein blindes Messgeraet: es misst
einwandfrei, nur eine ANDERE Menge, und eine Abwesenheit darin belegt nichts.
Alle Riegel aus v3.9.957 bis v3.9.963 sind gegen diese Klasse blind, und
keiner von ihnen konnte das melden.

🔴 UND DIE ZAHL KIPPT IN BEIDE RICHTUNGEN
Ein naiver Zaehler "onClick ohne role" meldet zu VIEL. Von den fuenf Faellen
in ProjList waren DREI `onClick: e=>e.stopPropagation()` - Installation, damit
der Klick nicht zur Karte durchschlaegt, kein Bedienelement. Haetten die
`role="button"` bekommen, waeren drei Phantom-Knoepfe in die Tab-Reihenfolge
gewandert: die Kur waere schlimmer als der Mangel gewesen. App-weit sind das
29 von 154.

WAS HIER ALS "ERREICHBAR" GILT
Fokussierbar (`tabIndex`) UND ein Tastenbehandler (`onKeyDown`/`onKeyPress`).
`role` ist ausdruecklich NICHT verlangt: die Projektzeile und die Projektkachel
enthalten selbst einen Knopf, und ein Knopf in einem Knopf ist ungueltiges
ARIA. Fokussierbar plus Tastenbehandler wirkt, ohne zu luegen.

DIE KLINKE
`GRENZE` ist der gemessene Stand, nicht ein Wunsch. Sie darf fallen, nie
steigen. Ein Riegel, der eine Zahl festnagelt, ohne sie senken zu koennen,
waere eine Attrappe - deshalb meldet die Probe auch, wenn die Zahl SINKT, und
verlangt, dass die Grenze nachgezogen wird.
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import code_scan  # noqa: E402

PFAD = os.path.join(os.path.dirname(__file__), "..", "index.html")

# Erzeuger mit einem Tag in Anfuehrungszeichen, beide Schreibweisen, beide
# Anfuehrungszeichen. Dasselbe Alphabet wie code_scan - siehe dort, warum.
ERZEUGER = re.compile(
    r"(?:createElement|(?<![A-Za-z0-9_$.])h)\(\s*['\"](\w+)['\"]\s*,")

# Von Natur aus fokussierbar: die brauchen kein tabIndex.
NATIV = {"a", "input", "select", "textarea", "button", "option"}

# Reine Weiterleitungssperre - kein Bedienelement.
NUR_STOP = re.compile(
    r"onClick\s*:\s*(?:e|ev|evt|_e)\s*=>\s*\{?\s*"
    r"(?:e|ev|evt|_e)\.stopPropagation\(\)\s*;?\s*\}?\s*[,}]")

GRENZE = 69  # gemessen an v3.9.975. 126 vor der ersten Kur, 124 nach
#               v3.9.964, 110 nachdem v3.9.969 die vierzehn Sortierkoepfe
#               erreichbar gemacht hat. Sie darf fallen, nie steigen -
#               und sie MELDET, wenn sie nachgezogen werden muss.


def _lies():
    return io.open(PFAD, encoding="utf-8", newline="").read()


def _ansichten(text, feld):
    return [(m.start(), m.group(1))
            for m in re.finditer(r"function\s+([A-Z]\w+)\s*\(", text)
            if feld[m.start()]]


def ohne_tastatur(text):
    """(pos, tag) je anklickbarem Nicht-Knopf ohne Tastaturzugang."""
    feld = code_scan.ist_code(text)
    aus = []
    for m in ERZEUGER.finditer(text):
        if not feld[m.start()]:
            continue
        tag = m.group(1)
        if tag in NATIV or tag in ("img", "canvas"):
            # img/canvas sitzen praktisch immer IN einem erreichbaren Eltern-
            # element; sie hier zu fordern erzeugt Rauschen statt Befunde.
            continue
        i = m.end()
        while i < len(text) and text[i] in " \t\r\n":
            i += 1
        if i >= len(text) or text[i] != "{":
            continue
        pe = code_scan._klammer_zu(text, i, "{", "}")
        if pe <= 0:
            continue
        props = text[i:pe]
        if "onClick" not in props:
            continue
        if NUR_STOP.search(props):
            continue
        if "tabIndex" in props and ("onKeyDown" in props
                                   or "onKeyPress" in props):
            continue
        aus.append((m.start(), tag))
    return aus


def test_die_zahl_steigt_nicht():
    """Die Klinke. Sie darf fallen, nie steigen."""
    text = _lies()
    fund = ohne_tastatur(text)
    assert len(fund) <= GRENZE, (
        "\U0001F534 %d anklickbare Nicht-Knoepfe ohne Tastaturzugang - die "
        "Grenze ist %d.\n"
        "  Es ist mindestens einer dazugekommen. Ein Element mit onClick, das "
        "kein button ist,\n"
        "  braucht tabIndex UND einen Tastenbehandler, sonst ist es fuer die "
        "Tastatur\n"
        "  kein Bedienelement." % (len(fund), GRENZE)
    )
    assert len(fund) >= GRENZE - 6, (
        "\U0001F7E2 Nur noch %d statt %d - das ist gut, aber die Grenze muss "
        "nachgezogen werden.\n"
        "  Eine Klinke, die nicht mitgeht, misst irgendwann nichts mehr."
        % (len(fund), GRENZE)
    )


def test_projektliste_ist_erreichbar():
    """Die zwei echten Faelle aus Punkt 5, namentlich.

    Nicht "die Zahl ist gesunken" - das waere Anwesenheit. Hier wird die
    WIRKUNG an der Stelle gemessen, um die es ging.
    """
    text = _lies()
    feld = code_scan.ist_code(text)
    a = text.index("function ProjList(")
    b = min(q for q, _ in _ansichten(text, feld) if q > a)
    fund = [x for x in ohne_tastatur(text) if a <= x[0] < b]
    assert not fund, (
        "\U0001F534 Die Projektliste hat wieder %d anklickbare Elemente ohne "
        "Tastaturzugang: %s" % (len(fund), fund)
    )
    # Und die Gegenrichtung: die zwei MUESSEN da sein, sonst misst die Probe
    # oben eine leere Grundgesamtheit.
    seg = text[a:b]
    assert seg.count("onOpen(p)") >= 2, (
        "\U0001F534 In ProjList stehen keine zwei onOpen(p)-Stellen mehr - "
        "die Probe oben\n  wuerde dann eine leere Menge gruen melden."
    )
    assert seg.count("tabIndex: 0") >= 2, (
        "\U0001F534 Die zwei Bedienelemente der Projektliste sind nicht mehr "
        "fokussierbar."
    )


def test_koeder_anklickbares_div():
    """\U0001F534 Der Fall, den KEIN Knopf-Riegel dieser Sammlung sehen kann."""
    fall = "h('div',{style:{},onClick:()=>oeffne(p)},'Projekt')"
    assert ohne_tastatur(fall), (
        "\U0001F534 Ein anklickbares div ohne tabIndex wurde nicht gemeldet.\n"
        "  Gegenprobe zur Vollstaendigkeit: code_scan.knopf_stellen findet "
        "hier NICHTS,\n"
        "  und genau das ist der Grund, warum es diesen Riegel gibt."
    )
    assert not code_scan.knopf_stellen(fall), (
        "\U0001F534 Der Knopf-Abtaster meldet hier etwas - dann ist die "
        "Begruendung dieses\n  Riegels falsch und er gehoert neu gedacht."
    )


def test_koeder_beide_schreibweisen():
    """Auch hier: ein Koeder JE FORM, nicht einer in der bekannten Form."""
    for fall, wie in (
            ("h('div',{onClick:()=>x()},'a')", "h( mit einfachen"),
            ('h("div",{onClick:()=>x()},"a")', "h( mit doppelten"),
            ("React.createElement('div',{onClick:()=>x()},'a')", "cE einfach"),
            ('React.createElement("div",{onClick:()=>x()},"a")', "cE doppelt")):
        assert ohne_tastatur(fall), (
            "\U0001F534 Die Form '%s' wird nicht erkannt - dieselbe Krankheit, "
            "die v957/v958/v961 hatten." % wie)


def test_gegenprobe_erreichbares_div_schweigt():
    """Ein div MIT tabIndex und Tastenbehandler darf nicht gemeldet werden."""
    fall = ("h('div',{tabIndex:0,onKeyDown:e=>{if(e.key==='Enter')x();},"
            "onClick:()=>x()},'a')")
    assert not ohne_tastatur(fall), (
        "\U0001F534 Ein erreichbares div wurde gemeldet - der Riegel meldet "
        "dann alles,\n  und einer, der alles meldet, misst so wenig wie einer, "
        "der schweigt."
    )


def test_gegenprobe_stoppropagation_schweigt():
    """\U0001F534 Die Fehlmeldung, die mir am 27.09. selbst passiert ist.

    Drei der fuenf ProjList-Faelle waren `onClick: e=>e.stopPropagation()` -
    Installation, kein Bedienelement. Ihnen role="button" zu geben haette drei
    Phantom-Knoepfe in die Tab-Reihenfolge gesetzt.
    """
    assert not ohne_tastatur("h('div',{onClick:e=>e.stopPropagation()},'a')")
    assert not ohne_tastatur(
        'React.createElement("div",{onClick:e=>{e.stopPropagation();}},"a")')
    # Aber eine Sperre MIT echter Wirkung dahinter ist ein Bedienelement.
    assert ohne_tastatur(
        "h('div',{onClick:e=>{e.stopPropagation();oeffne(p);}},'a')"), (
        "\U0001F534 Ein Element, das nach dem stopPropagation noch etwas TUT, "
        "wurde\n  uebersehen - die Sperre darf nicht zum Freibrief werden."
    )


def test_natives_element_schweigt():
    """Ein a oder input braucht kein tabIndex - es ist von sich aus dran."""
    for fall in ("h('a',{href:'#',onClick:()=>x()},'a')",
                 "h('input',{onClick:()=>x()})",
                 "h('select',{onClick:()=>x()})"):
        assert not ohne_tastatur(fall), (
            "\U0001F534 %s wurde gemeldet - nativ fokussierbare Elemente "
            "gehoeren nicht dazu." % fall)
