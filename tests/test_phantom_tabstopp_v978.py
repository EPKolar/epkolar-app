# -*- coding: utf-8 -*-
"""Kein gebauter Tastenbehandler darf einen LEEREN Rumpf haben.

🔴 DAS IST EIN FEHLER, DEN ICH SELBST EINGEBAUT HABE, UND ER STAND DREI
VERSIONEN LANG DA. v3.9.975 hat 41 einfachen Flaechen Tastaturzugang gegeben.
Das Bauwerkzeug nahm jede Stelle mit einem `onClick` und rief denselben
Ausdruck aus dem Tastenbehandler auf - die richtige Bauweise, denn so kann die
Taste nie etwas anderes tun als der Klick.

Bei EINER Stelle tut der Klick aber nichts: der Ziehgriff eines Dispo-Blocks
traegt

    onClick: function(e){ if(e&&e.stopPropagation) e.stopPropagation(); }

Das verhindert nur, dass ein Klick auf den Griff den Arbeitsschein oeffnet.
Die eigentliche Funktion - ziehen = Dauer aendern - haengt an
`onPointerDown` und hat gar keinen Tastenweg. Ergebnis: ein Tab-Stopp, der
NICHTS tut, und eine Vorlesehilfe, die "Schaltflaeche" sagt.

Genau das Phantom, das der Auftrag ausgeschlossen hat: *lieber ein fehlender
Zugang als ein Phantom in der Tab-Reihenfolge.*

🔴 WARUM ES DURCHKAM: eine zweite SCHREIBWEISE. Mein Klassifizierer hat reine
`stopPropagation`-Behandler ausgeschlossen - 29 von 30 richtig. Dieser eine
ist als `function(e){...}` geschrieben statt als Pfeilfunktion, und das
Muster kannte nur die Pfeilform. Dieselbe Fehlerform wie bei
`createElement` gegen `h(`, wie bei den fuenf Schriftgroessen-Formen und wie
bei den 17 Schreibweisen von `minHeight:<zahl>:0`.

🔴 UND GEFUNDEN WURDE ES NICHT VON EINEM RIEGEL, SONDERN VON EINER MESSUNG,
die einen Bereich geoeffnet hat, den vorher nie jemand geoeffnet hatte
(`scripts/inline_bereiche_messen.py`, Dispo-Ansicht). Drei Riegel zum
Tastaturzugang standen die ganze Zeit gruen - sie zaehlen ANWESENHEIT von
`tabIndex` und `onKeyDown`, und beides war ja da.
"""
import io
import os
import re

PFAD = os.path.join(os.path.dirname(__file__), "..", "index.html")

# Die Bauform aus v3.9.975: ein Tastenbehandler, der EINEN Ausdruck aufruft.
# Beide Auspraegungen - mit und ohne Bedingung - in EINEM Muster.
# 🔴 DAS `(?:if\(e\.target...\)return;)?` HAT EINE GESCHICHTE, und sie ist der
#    Grund, warum `test_es_gibt_ueberhaupt_gebaute_behandler` hier steht.
#    v3.9.985 hat allen 97 gebauten Behandlern einen Waechter VORANGESTELLT:
#
#        onKeyDown: e=>{if(e.target!==e.currentTarget)return;if(e.key===...
#
#    Damit traf dieses Muster auf einen Schlag NULL Stellen - und die beiden
#    Pruefungen darunter ("kein leerer Rumpf", "kein Objektliteral") waeren
#    ab sofort LEER GRUEN gewesen. Kein Riegel waere rot geworden, nichts
#    haette gemeldet, dass sie nichts mehr messen.
#
#    Gefangen hat es ausschliesslich die Gegenprobe auf die Grundgesamtheit.
#    Eine Null ist erst dann ein Ergebnis, wenn die Menge, ueber der sie
#    steht, nachweislich nicht leer ist.
BEHANDLER = re.compile(
    r'onKeyDown:\s*e=>\{(?:if\(e\.target!==e\.currentTarget\)return;)?'
    r'(?:const _h=\((?P<bed>.{0,400}?)\);)?'
    r'if\((?:_h&&)?\(?e\.key==="Enter"\|\|e\.key===" "\)?\)'
    r'\{e\.preventDefault\(\);(?:_h\(e\)|\((?P<ausdruck>.{0,400}?)\)\(e\));\}\}',
    re.S)

# Was ein Rumpf enthalten darf, ohne etwas zu TUN.
LEERLAUF = (
    re.compile(r'if\(e&&e\.stopPropagation\)e\.stopPropagation\(\);'),
    re.compile(r'e\.stopPropagation\(\);'),
    re.compile(r'e\.preventDefault\(\);'),
)


def _rumpf(ausdruck):
    """Der Rumpf des aufgerufenen Ausdrucks, ohne Huelle und ohne Leerlauf."""
    k = ausdruck.strip()
    # function(e){...}  oder  e=>{...}  oder  ()=>{...}
    m = re.match(r'^(?:function\s*\([^)]*\)|\([^)]*\)\s*=>|\w+\s*=>)\s*\{(.*)\}$',
                 k, re.S)
    if not m:
        return k          # ein blosser Aufruf wie `moveRow(r.id,-1)` - tut etwas
    inner = m.group(1)
    for muster in LEERLAUF:
        inner = muster.sub("", inner)
    return inner.strip().strip(";").strip()


def _ist_objektliteral(ausdruck):
    """Ruft der Behandler ein OBJEKT auf statt einer Funktion?

    🔴 DIESER RIEGEL HAT EINEN ECHTEN FEHLER DURCHGELASSEN, und der Grund ist
    lehrreich. Er prueft, ob der Rumpf des aufgerufenen Ausdrucks LEER ist -
    "tut nichts". Ein Messagent fand am 29.09.2026 eine Stelle, die etwas
    ganz anderes tut: sie ruft das STIL-OBJEKT als Funktion auf.

        onKeyDown: e=>{...e.preventDefault();
          ({marginBottom: 8, cursor: "pointer", ...})(e);}

    Enter oder Leertaste auf der Seitenvorschau eines Plans wirft damit
    `TypeError: ... is not a function`. Der Mausweg (`onClick`) ist nicht
    betroffen - deshalb faellt es beim Klicken nie auf, und deshalb hat es
    niemand gemeldet.

    URSACHE: an dieser Stelle steht `onClick` als KURZSCHREIBWEISE
    (`onClick,` statt `onClick: <ausdruck>`). Das Bauwerkzeug aus v3.9.975
    suchte `onClick` und dann den naechsten Doppelpunkt - und fand den von
    `style:`. Es hat also das falsche Feld kopiert.

    „Leerer Rumpf" und „gar nicht aufrufbar" sind zwei verschiedene Mangel.
    Der erste war geprueft, der zweite nicht.
    """
    k = ausdruck.strip()
    if not k.startswith("{"):
        return False
    # Ein Objektliteral erkennt man am `schluessel:` auf der obersten Ebene.
    return bool(re.match(r'^\{\s*[A-Za-z_$][\w$]*\s*:', k))


def _text():
    return io.open(PFAD, encoding="utf-8", newline="").read()


def test_koeder_der_sucher_findet_beide_bauformen():
    """🔴 SELBSTPROBE mit ZWEI Schreibweisen - die zweite ist der ganze Punkt.

    Ein Koeder, der nur die Pfeilform benutzt, teilt die Luecke des Musters,
    das den Fehler durchgelassen hat. Er wuerde die Blindheit bestaetigen
    statt sie aufzudecken.
    """
    faelle = [
        ('onKeyDown: e=>{if(e.key==="Enter"||e.key===" ")'
         '{e.preventDefault();(function(e){if(e&&e.stopPropagation)'
         'e.stopPropagation();})(e);}}', True, "function-Schreibweise, LEER"),
        ('onKeyDown: e=>{if(e.key==="Enter"||e.key===" ")'
         '{e.preventDefault();(e=>{e.stopPropagation();})(e);}}',
         True, "Pfeil-Schreibweise, LEER"),
        ('onKeyDown: e=>{if(e.key==="Enter"||e.key===" ")'
         '{e.preventDefault();(()=>setSel(f.id))(e);}}',
         False, "ruft etwas auf - kein Phantom"),
        ('onKeyDown: e=>{const _h=(x?()=>go():undefined);'
         'if(_h&&(e.key==="Enter"||e.key===" "))'
         '{e.preventDefault();_h(e);}}',
         False, "bedingte Form - kein Phantom"),
    ]
    for text, soll_leer, warum in faelle:
        treffer = list(BEHANDLER.finditer(text))
        assert treffer, ("Der Sucher findet die Bauform nicht: %s" % warum)
        a = treffer[0].group("ausdruck")
        leer = bool(a) and not _rumpf(a)
        assert leer == soll_leer, (
            "%s: leer=%s erwartet, gemessen %s" % (warum, soll_leer, leer))


def test_kein_tastenbehandler_laeuft_leer():
    """Kein gebauter Behandler ruft einen Ausdruck auf, der nichts tut."""
    t = _text()
    phantome = []
    for m in BEHANDLER.finditer(t):
        a = m.group("ausdruck")
        if a and not _rumpf(a):
            phantome.append((t.count("\n", 0, m.start()) + 1, a[:70]))
    assert not phantome, (
        "%d Tastenbehandler rufen einen Ausdruck auf, der NICHTS tut:\n%s\n"
        "Ein Tab-Stopp ohne Wirkung ist schlechter als kein Tab-Stopp: der\n"
        "Fokus bleibt darauf stehen, eine Vorlesehilfe sagt 'Schaltflaeche',\n"
        "und nichts passiert. Entweder bekommt die Stelle eine ECHTE\n"
        "Tastenfunktion - oder Rolle, tabIndex und Behandler kommen weg."
        % (len(phantome), "\n".join("   Zeile %d: %s" % p for p in phantome)))


def test_es_gibt_ueberhaupt_gebaute_behandler():
    """🔴 Gegenprobe zur Null oben: findet der Sucher in der ECHTEN Datei
    ueberhaupt etwas, oder ist die leere Liste eine leere Grundgesamtheit?"""
    t = _text()
    n = len(list(BEHANDLER.finditer(t)))
    assert n >= 30, (
        "Nur %d gebaute Tastenbehandler gefunden. v3.9.975 hat 41 Flaechen "
        "gebaut;\n  bei so wenigen Treffern misst das Muster nicht mehr die "
        "Bauform, und die\n  Null der anderen Pruefung ist wertlos." % n)


def test_kein_behandler_ruft_ein_OBJEKT_auf():
    """🔴 Enter auf der Seitenvorschau warf eine Ausnahme - drei Versionen lang.

    Gefunden am 29.09.2026 von einem Messagenten, nicht von diesem Riegel:
    er prueft "tut nichts", und ein Stil-Objekt tut nicht nichts, es ist nur
    nicht aufrufbar. Zwei verschiedene Mangel, einer davon ungeprueft.
    """
    t = _text()
    fund = []
    for m in BEHANDLER.finditer(t):
        a = m.group("ausdruck")
        if a and _ist_objektliteral(a):
            fund.append((t.count("\n", 0, m.start()) + 1, a.strip()[:60]))
    assert not fund, (
        "%d Tastenbehandler rufen ein OBJEKTLITERAL als Funktion auf:\n%s\n"
        "Enter oder Leertaste wirft dort `TypeError: ... is not a function`.\n"
        "Der Mausweg ist nicht betroffen - deshalb faellt es beim Klicken nie\n"
        "auf. Ursache ist fast immer eine KURZSCHREIBWEISE (`onClick,` statt\n"
        "`onClick: <ausdruck>`): wer `onClick` sucht und dann den naechsten\n"
        "Doppelpunkt nimmt, erwischt das Feld DANACH."
        % (len(fund), "\n".join("   Zeile %d: %s..." % f for f in fund)))


def test_koeder_objektliteral_wird_erkannt():
    """🔴 Selbstprobe mit Gegenproben - sonst ist die Null oben wertlos."""
    faelle = [
        ('{marginBottom: 8, cursor: "pointer"}', True, "Stil-Objekt"),
        ('{a:1}', True, "kurzes Objekt"),
        ('()=>setSel(f.id)', False, "Pfeilfunktion"),
        ('function(e){go();}', False, "function-Ausdruck"),
        ('moveRow(r.id,-1)', False, "Aufruf"),
        ('{...spread}', False, "Spread - kein Schluessel:Wert"),
    ]
    for text, soll, warum in faelle:
        assert _ist_objektliteral(text) is soll, (
            "%s (%r): erwartet %s" % (warum, text, soll))
