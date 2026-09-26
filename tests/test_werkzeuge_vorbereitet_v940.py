# -*- coding: utf-8 -*-
"""v3.9.940 - der BESTAND der Werkzeug-Ansicht, bevor sie umgebaut wird.

WOZU DIESE DATEI
────────────────
`WerkzeugView` soll beschriftete Reiter bekommen. Ein Umbau an einer 92-kB-
Funktion in einer 3,6-MB-Datei geht selten nur dorthin, wo er soll. Diese
Riegel halten fest, was JETZT da ist, damit der Umbau es nicht mitnimmt:

  * sechs Statuswerte, neun Kategorien - und zwar WAEHLBAR, nicht bloss
    irgendwo im Text
  * fuenf Filter-Chips mit ihren Zaehlern
  * "Ausleihen" je Geraet
  * die vier Kopfknoepfe an ihren HANDLERN
  * die fuenf Reiter mit ihren Kennungen und ihren Zielansichten

Sie sind JETZT gruen. Sie beschreiben den Ist-Zustand, sie fordern nichts.

WARUM HIER NODE LAEUFT UND NICHT NUR `in`
─────────────────────────────────────────
"Die Zeichenkette steht da" ist die schwaechste Form eines Riegels; sie war in
diesem Bestand mehrfach gruen, waehrend die Sache kaputt war. Deshalb werden
die Literale AUS DER DATEI GESCHNITTEN und AUSGEFUEHRT: `WZ_STATUS` muss sechs
Eintraege ERGEBEN, die Reiterliste muss fuenf Objekte ERGEBEN, `_wzQuickBtn`
muss fuer ein verfuegbares Geraet einen Knopf mit "Ausleihen" ZURUECKGEBEN.
Was nur dasteht, kann falsch geklammert, doppelt deklariert oder nie erreicht
sein - was laeuft, nicht.

WARUM DIE UMLAUTE TOLERANT VERGLICHEN WERDEN
────────────────────────────────────────────
Die App spricht Deutsch. In dieser Datei stehen Umlaute teils roh, teils als
HTML-Entity, teils als \\uXXXX. Verglichen wird deshalb mit einem Ausdruck, der
GENAU DIESE DREI Schreibweisen JE UMLAUT zulaesst - und sonst nichts. Ein
`in`-Vergleich auf "Verf" waere toleranter und daher wertlos: er wuerde auch
"Verfall" treffen.

DER KOEDER (Regel 3)
────────────────────
Jede Messung hier ist eine FUNKTION auf einem Quelltext, nicht auf einer
Datei. Am Ende der Datei werden dieselben Funktionen auf ABSICHTLICH
VERSTUEMMELTE Kopien angesetzt, und sie MUESSEN dort rot werden. Ein Riegel,
der zaehlt, wird beim eigenen Ausfall sonst gruen: nichts gefunden heisst dann
"nichts kaputt".
"""
import json
import os
import re
import subprocess
import sys

import pytest

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
sys.path.insert(0, HIER)
sys.path.insert(0, os.path.join(WURZEL, "scripts"))

from conftest import _extract_fn, EPK_TEST_TIMEOUT  # noqa: E402
from code_scan import ist_code, eichen  # noqa: E402


# ───────────────────────────────────────────────────────────────────────────
# Umlaut-Toleranz, eng gefasst
# ───────────────────────────────────────────────────────────────────────────
_SCHREIBWEISEN = {
    "ä": ["ä", "&auml;", "\\u00e4", "\\u00E4"],
    "ö": ["ö", "&ouml;", "\\u00f6", "\\u00F6"],
    "ü": ["ü", "&uuml;", "\\u00fc", "\\u00FC"],
    "Ä": ["Ä", "&Auml;", "\\u00c4", "\\u00C4"],
    "Ö": ["Ö", "&Ouml;", "\\u00d6", "\\u00D6"],
    "Ü": ["Ü", "&Uuml;", "\\u00dc", "\\u00DC"],
    "ß": ["ß", "&szlig;", "\\u00df", "\\u00DF"],
}


def uml(text):
    """Ausdruck, der `text` in den drei Umlaut-Schreibweisen trifft - nur die.

    Alles ausser den sieben Umlautzeichen wird woertlich verlangt. Damit kann
    kein Treffer entstehen, wo keiner ist.
    """
    teile = []
    for z in text:
        if z in _SCHREIBWEISEN:
            teile.append("(?:" + "|".join(re.escape(v)
                                          for v in _SCHREIBWEISEN[z]) + ")")
        else:
            teile.append(re.escape(z))
    return re.compile("".join(teile))


def passt(erwartet, tatsaechlich):
    """Voller Vergleich mit Umlaut-Toleranz."""
    return uml(erwartet).fullmatch(tatsaechlich or "") is not None


# ───────────────────────────────────────────────────────────────────────────
# Werkzeug: Bloecke aus dem Quelltext schneiden - ueber die Klammerbilanz,
# und zwar OHNE Klammern in Zeichenketten und Kommentaren mitzuzaehlen.
# ───────────────────────────────────────────────────────────────────────────
_FELD = {}


def feld(quelle):
    """`ist_code`-Feld, einmal je Text (das Abtasten von 3,6 MB dauert).

    Der Schluessel ist der TEXT, nicht `id(text)`. Der erste Anlauf nahm
    `id()` - und ein freigegebener String gibt seine Adresse an den naechsten
    weiter. Der Koeder bekam dadurch das Feld eines fremden, laengeren Textes
    und lief aus dem Feld heraus. Ein Zwischenspeicher, der falsche Antworten
    ausliefert, ist schlimmer als keiner.
    """
    s = _FELD.get(quelle)
    if s is None:
        s = ist_code(quelle)
        _FELD[quelle] = s
    return s


_AUF = "{[("
_ZU = "}])"


def block(quelle, anker, erste_klammer=None):
    """Von `anker` bis zur passenden schliessenden Klammer - einschliesslich.

    `erste_klammer` sagt, welche Klammerart den Block eroeffnet; ohne Angabe
    wird die erste Klammer hinter dem Anker genommen. Klammern in
    Zeichenketten und Kommentaren zaehlen NICHT mit (Regel 5).
    """
    i = quelle.find(anker)
    assert i >= 0, "Anker nicht gefunden: " + anker[:60]
    f = feld(quelle)
    # Ab dem ANKERANFANG suchen, nicht ab seinem Ende: `const WZ_STATUS={verfuegbar:`
    # traegt die eroeffnende Klammer MITTEN im Anker. Der erste Anlauf suchte
    # dahinter, fand die innere `{` von `{l:"Verfuegbar"...}` und schnitt den
    # Block nach einem Sechstel ab - Node meldete daraufhin einen Syntaxfehler.
    # Genau so soll ein falscher Schnitt auffallen: laut, nicht als kleinere Zahl.
    j = i
    while j < len(quelle):
        if f[j] and quelle[j] in _AUF and (
                erste_klammer is None or quelle[j] == erste_klammer):
            break
        j += 1
    else:
        raise AssertionError("keine oeffnende Klammer hinter " + anker[:40])
    tiefe = 0
    for p in range(j, len(quelle)):
        if not f[p]:
            continue
        if quelle[p] in _AUF:
            tiefe += 1
        elif quelle[p] in _ZU:
            tiefe -= 1
            if tiefe == 0:
                return quelle[i:p + 1]
    raise AssertionError("Blockende nicht gefunden: " + anker[:40])


def nur_code_treffer(quelle, muster):
    """Treffer von `muster`, die wirklich im Code stehen.

    EINE FEINHEIT, DIE ZUERST DREI RIEGEL BLIND GEMACHT HAT: `ist_code`
    markiert das EROEFFNENDE Anfuehrungszeichen einer Zeichenkette nicht als
    Code - es schaltet den Zustand um. Ein Muster wie `"Werkzeug-Labels"` faengt
    aber genau damit an und konnte deshalb NIEMALS treffen. Drei Riegel meldeten
    "der Knopf ist weg", obwohl er dastand. Das ist die gefaehrliche Richtung
    nur zufaellig nicht gewesen: derselbe Fehler haette bei einem `not in`-Riegel
    ein gruenes Ergebnis erzeugt.

    Deshalb: faengt das Muster mit einem Anfuehrungszeichen an, entscheidet das
    Zeichen DAVOR. In einem Kommentar ist auch das nicht Code - ein
    `/* "Werkzeug-Labels" */` zaehlt also weiterhin nicht.
    """
    f = feld(quelle)
    aus = []
    for m in re.finditer(re.escape(muster), quelle):
        s = m.start()
        if f[s]:
            aus.append(s)
        elif s > 0 and f[s - 1] and quelle[s] in "\"'`":
            aus.append(s)
    return aus


def node_json(node_exe, tmp_path, code, name="probe.js"):
    """Programm in eine UTF-8-Datei schreiben und ausfuehren.

    Bewusst eine DATEI und nicht `node -e`: der geschnittene Code traegt
    Emoji und Umlaute, und der Weg ueber argv haengt auf Windows an der
    Konsolen-Codepage.
    """
    p = tmp_path / name
    p.write_text(code, encoding="utf-8")
    r = subprocess.run([node_exe, str(p)], capture_output=True, text=True,
                       encoding="utf-8", errors="replace",
                       timeout=EPK_TEST_TIMEOUT)
    assert r.returncode == 0, "node: " + (r.stderr or "")[:1200]
    return json.loads(r.stdout)


# ───────────────────────────────────────────────────────────────────────────
# Anker. EINMAL hier, nicht je Riegel neu - wer sie aendert, aendert sie
# fuer alle.
# ───────────────────────────────────────────────────────────────────────────
A_STATUS = 'const WZ_STATUS={verfuegbar:'
A_KAT = 'const WZ_KAT={elektro:'
A_REITER = '[{id:"scan",i:'
A_CHIPS = "{key:'alle',label:'Alle'}"
A_CHIPZAEHLER = "const cnt={alle:_wzPool.length"
A_QUICKBTN = 'const _wzQuickBtn=(w)=>{if(!w)return null;'
A_OPENNEW = 'const openNew=()=>{'
A_EXPORT = 'const exportWz=()=>{'

STATUS_SOLL = [
    ("verfuegbar", "Verfügbar"),
    ("ausgegeben", "Ausgegeben"),
    ("reparatur", "In Reparatur"),
    ("kalibrierung", "Kalibrierung fällig"),
    ("verloren", "Verloren/Defekt"),
    ("stillgelegt", "Stillgelegt"),
]

KAT_SOLL = [
    ("elektro", "Elektrowerkzeug"),
    ("mess", "Messgeräte"),
    ("hand", "Handwerkzeug"),
    ("maschine", "Maschinen"),
    ("sicherheit", "Sicherheit/PSA"),
    ("verbrauch", "Verbrauchsmaterial"),
    ("kabel", "Kabelwerkzeug"),
    ("leiter", "Leiter/Gerüst"),
    ("sonstiges", "Sonstiges"),
]

CHIPS_SOLL = [
    ("alle", "Alle"),
    ("verfuegbar", "✅ Verfügbar"),
    ("ausgegeben", "📤 Ausgegeben"),
    ("kalib_faellig", "⚠️ Kalibrierung fällig"),
    ("verloren", "❌ Defekt"),
]

# Kennung -> (Emoji, Beschriftung im Code OHNE editId, Anker der Zielansicht).
# `form` heisst ohne editId "Neu" und mit editId "Bearbeiten" - beide Faelle
# hat test_der_reiter_form_beschriftet_sich_nach_editid.
REITER_SOLL = [
    ("scan", "📷", "QR Scan", '"📷 QR-Code scannen"'),
    ("liste", "📋", "Liste", A_CHIPS),
    ("checkout", "📤", "Check-In/Out", '"📤 Werkzeug ausgeben"'),
    ("kalib", "🔧", "Service", '"🔧 Geräte-Serviceheft"'),
    ("form", "✏️", "Neu",
     'editId?"✏️ Gerät bearbeiten":"🔧 Neues Gerät anlegen"'),
]


# ───────────────────────────────────────────────────────────────────────────
# Messfunktionen. Sie nehmen einen QUELLTEXT, keine Datei - nur so kann der
# Koeder am Ende dieselbe Messung auf eine verstuemmelte Kopie ansetzen.
# ───────────────────────────────────────────────────────────────────────────
def statuswerte(quelle, node_exe, tmp_path, name="status.js"):
    lit = block(quelle, A_STATUS, "{")
    code = ('const COLORS={ERROR:"#ef4444"};\n' + lit + ';\n'
            'console.log(JSON.stringify('
            'Object.entries(WZ_STATUS).map(([k,v])=>[k,v.l,v.i])));\n')
    return node_json(node_exe, tmp_path, code, name)


def kategorien(quelle, node_exe, tmp_path, name="kat.js"):
    lit = block(quelle, A_KAT, "{")
    code = ('const COLORS={ERROR:"#ef4444"};\n' + lit + ';\n'
            'console.log(JSON.stringify('
            'Object.entries(WZ_KAT).map(([k,v])=>[k,v.l,v.i])));\n')
    return node_json(node_exe, tmp_path, code, name)


def reiter(quelle, node_exe, tmp_path, darf_checkout=True, ist_admin=True,
           edit_id=None, name="reiter.js"):
    """Die Reiterliste AUSFUEHREN - mit den Rechten als Schalter."""
    lit = block(quelle, A_REITER, "[")
    code = (
        'const curUser={role:"admin"};\n'
        'const editId=%s;\n'
        'const isAdmin=%s;\n'
        'function canDo(p,u){return p==="wz_edit" ? %s : false;}\n'
        'const liste=%s;\n'
        'console.log(JSON.stringify(liste.map(t=>[t.id,t.i,t.l])));\n'
        % (json.dumps(edit_id), "true" if ist_admin else "false",
           "true" if darf_checkout else "false", lit))
    return node_json(node_exe, tmp_path, code, name)


def chips(quelle, node_exe, tmp_path, name="chips.js"):
    # Der Anker ist selbst schon ein Objekt - gebraucht wird die ganze Liste,
    # also einen Schritt nach links auf die eroeffnende [ .
    i = quelle.find(A_CHIPS)
    k = quelle.rfind("[", 0, i)
    assert k > 0, "keine Chip-Liste um den Anker gefunden"
    lit = block(quelle[k:], "[", "[")
    code = ('const liste=' + lit + ';\n'
            'console.log(JSON.stringify(liste.map(c=>[c.key,c.label])));\n')
    return node_json(node_exe, tmp_path, code, name)


def chipzaehler(quelle, node_exe, tmp_path, name="zaehler.js"):
    """Der Zaehlerblock der Chips, mit einem Bestand aus vier Geraeten."""
    i = quelle.find(A_CHIPZAEHLER)
    assert i >= 0, "Chip-Zaehlerblock nicht gefunden"
    j = quelle.find("return cnt;", i)
    assert j > i, "Ende des Chip-Zaehlerblocks nicht gefunden"
    rumpf = quelle[i:j + len("return cnt;")]
    code = (
        'function zaehl(_wzPool,_wzKalibFaellig){\n' + rumpf + '\n}\n'
        'const pool=[{id:"A",status:"verfuegbar",faellig:false},\n'
        '            {id:"B",status:"ausgegeben",faellig:false},\n'
        '            {id:"C",status:"verloren",faellig:false},\n'
        '            {id:"D",status:"verfuegbar",faellig:true}];\n'
        'console.log(JSON.stringify(zaehl(pool,w=>w.faellig===true)));\n')
    return node_json(node_exe, tmp_path, code, name)


def ausleihknopf(quelle, node_exe, tmp_path, name="ausleihen.js"):
    """`_wzQuickBtn` wirklich aufrufen - drei Faelle."""
    lit = block(quelle, A_QUICKBTN, "{")
    code = (
        'const React={createElement:(t,p,...c)=>({t:t,c:c})};\n'
        'const bpS={},bgS={},isMob=false;\n'
        # v3.9.944: UI als Attrappe, dieselbe Art wie bpS. Seit die
        # Schriftgroessen aus dem Token-Objekt kommen, steht im geschnittenen
        # Code `fontSize:UI.fMeta`, und ohne diese Zeile wirft Node
        # "UI is not defined" - der Riegel waere rot, ohne dass am
        # Ausleihknopf etwas falsch waere.
        'const UI={fMeta:12,fKlein:13,fText:14,fTitel:15,fTitelGross:17,'
        'fSeiteMob:18,fZahl:20,fSeite:22,fZahlGross:24,fUeber:28};\n'
        'const _myMid="M1";\n'
        'const curUser={role:"monteur"};\n'
        'function canDo(){return false;}\n'
        'function wzSelfOut(){} function wzSelfIn(){}\n'
        + lit + '\n'
        'const aus=[_wzQuickBtn({id:"A",status:"verfuegbar"}),\n'
        '           _wzQuickBtn({id:"B",status:"ausgegeben",zugewiesen:"M1"}),\n'
        '           _wzQuickBtn({id:"C",status:"reparatur"})];\n'
        'console.log(JSON.stringify(aus.map(x=>x?x.c.join(""):null)));\n')
    return node_json(node_exe, tmp_path, code, name)


# ───────────────────────────────────────────────────────────────────────────
# Fixtures
# ───────────────────────────────────────────────────────────────────────────
@pytest.fixture(scope="module")
def wz(index_html):
    """Der Rumpf von `WerkzeugView` - alles, was hier gemessen wird, muss
    DARIN stehen, nicht irgendwo in 3,6 MB."""
    fn = _extract_fn(index_html, "WerkzeugView")
    assert fn, "function WerkzeugView nicht gefunden"
    assert len(fn) > 40000, (
        "WerkzeugView ist nur %d Zeichen gross - der Schnitt hat die Funktion "
        "nicht erwischt." % len(fn))
    return fn


# ───────────────────────────────────────────────────────────────────────────
# 0. Der Abtaster muss sich vorher selbst widerlegen (Regel 5)
# ───────────────────────────────────────────────────────────────────────────
def test_abtaster_besteht_die_eichprobe(index_html):
    """Ohne bestandene Eichung ist jede Zahl aus diesem Riegel wertlos.

    `accept:"application/pdf,image/*"` hat einen naiven Zaehler die letzten
    80 kB der Datei - WerkzeugView mitten darin - als Kommentar lesen lassen.
    """
    ok, gefunden, erwartet = eichen(index_html)
    assert ok, ("code_scan irrt sich: %d von %d isMob-Deklarationen als Code "
                "erkannt." % (gefunden, erwartet))
    assert erwartet >= 5, "leere Grundgesamtheit besteht keine Probe"


def test_werkzeugview_liegt_im_code_nicht_im_kommentar(index_html):
    """Genau diese Verwechslung hat die Funktion zweimal unsichtbar gemacht."""
    stellen = nur_code_treffer(index_html, "function WerkzeugView(")
    assert len(stellen) == 1, (
        "function WerkzeugView( steht %d mal im CODE - erwartet genau einmal."
        % len(stellen))


# ───────────────────────────────────────────────────────────────────────────
# 1. Sechs Statuswerte - waehlbar
# ───────────────────────────────────────────────────────────────────────────
def test_sechs_statuswerte_ergeben_sich_aus_dem_literal(index_html, node_exe,
                                                        tmp_path):
    ist = statuswerte(index_html, node_exe, tmp_path)
    assert len(ist) == 6, "WZ_STATUS ergibt %d Eintraege statt 6: %r" % (
        len(ist), [k for k, _l, _i in ist])
    assert [k for k, _l, _i in ist] == [k for k, _l in STATUS_SOLL], (
        "Schluessel oder Reihenfolge von WZ_STATUS haben sich geaendert: %r"
        % [k for k, _l, _i in ist])
    for (k_soll, l_soll), (k, l, ikone) in zip(STATUS_SOLL, ist):
        assert passt(l_soll, l), (
            "Status %s heisst %r, erwartet %r" % (k, l, l_soll))
        assert ikone, "Status %s hat keine Ikone" % k


def test_statuswerte_sind_in_zwei_auswahlfeldern_waehlbar(wz):
    """WIRKUNG, nicht Anwesenheit: das Literal muss OPTIONEN erzeugen.

    Zwei Felder: der Listenfilter (`filtSt`) und das Statusfeld im Formular
    (`form.status`). Steht das Literal nur irgendwo herum, ist kein Status
    waehlbar - und genau das wuerde ein Textvergleich nicht merken.
    """
    quelle = "Object.entries(WZ_STATUS).map(([k,v])=>(React.createElement('option'"
    stellen = nur_code_treffer(wz, quelle)
    assert len(stellen) == 2, (
        "WZ_STATUS speist %d Auswahlfelder in WerkzeugView, erwartet 2."
        % len(stellen))
    # ... und zwar diese beiden. Der Filter und das Formular, nicht zweimal
    # dasselbe.
    assert "value: filtSt" in wz, "der Statusfilter der Liste ist weg"
    assert "value: form.status" in wz, "das Statusfeld im Formular ist weg"
    for pos in stellen:
        umfeld = wz[max(0, pos - 420):pos]
        assert ("value: filtSt" in umfeld) or ("value: form.status" in umfeld), (
            "ein WZ_STATUS-Auswahlfeld haengt an keinem der beiden bekannten "
            "Werte: ..." + umfeld[-160:])


# ───────────────────────────────────────────────────────────────────────────
# 2. Neun Kategorien - waehlbar
# ───────────────────────────────────────────────────────────────────────────
def test_neun_kategorien_ergeben_sich_aus_dem_literal(index_html, node_exe,
                                                      tmp_path):
    ist = kategorien(index_html, node_exe, tmp_path)
    assert len(ist) == 9, "WZ_KAT ergibt %d Eintraege statt 9: %r" % (
        len(ist), [k for k, _l, _i in ist])
    assert [k for k, _l, _i in ist] == [k for k, _l in KAT_SOLL], (
        "Schluessel oder Reihenfolge von WZ_KAT haben sich geaendert: %r"
        % [k for k, _l, _i in ist])
    for (k_soll, l_soll), (k, l, ikone) in zip(KAT_SOLL, ist):
        assert passt(l_soll, l), (
            "Kategorie %s heisst %r, erwartet %r" % (k, l, l_soll))
        assert ikone, "Kategorie %s hat keine Ikone" % k


def test_kategorien_sind_in_zwei_auswahlfeldern_waehlbar(wz):
    quelle = "Object.entries(WZ_KAT).map(([k,v])=>(React.createElement('option'"
    stellen = nur_code_treffer(wz, quelle)
    assert len(stellen) == 2, (
        "WZ_KAT speist %d Auswahlfelder in WerkzeugView, erwartet 2."
        % len(stellen))
    assert "value: filtKat" in wz, "der Kategoriefilter der Liste ist weg"
    assert "value: form.kat" in wz, "das Kategoriefeld im Formular ist weg"
    for pos in stellen:
        umfeld = wz[max(0, pos - 420):pos]
        assert ("value: filtKat" in umfeld) or ("value: form.kat" in umfeld), (
            "ein WZ_KAT-Auswahlfeld haengt an keinem der beiden bekannten "
            "Werte: ..." + umfeld[-160:])


# ───────────────────────────────────────────────────────────────────────────
# 3. Fuenf Filter-Chips mit Zaehlern
# ───────────────────────────────────────────────────────────────────────────
def test_fuenf_filter_chips(wz, node_exe, tmp_path):
    ist = chips(wz, node_exe, tmp_path)
    assert len(ist) == 5, "%d Filter-Chips statt 5: %r" % (
        len(ist), [k for k, _l in ist])
    assert [k for k, _l in ist] == [k for k, _l in CHIPS_SOLL], (
        "Chip-Schluessel oder -Reihenfolge geaendert: %r"
        % [k for k, _l in ist])
    for (k_soll, l_soll), (k, l) in zip(CHIPS_SOLL, ist):
        assert passt(l_soll, l), "Chip %s heisst %r, erwartet %r" % (k, l, l_soll)


def test_jeder_chip_tragt_seinen_zaehler(wz, node_exe, tmp_path):
    """Der Zaehler ist keine Zierde: der Chip rendert `label (n)`.

    Gemessen wird beides - dass der Zaehlerblock fuer JEDEN Chipschluessel
    einen Wert liefert, und dass die Zahl auch angezeigt wird.
    """
    cnt = chipzaehler(wz, node_exe, tmp_path)
    for k, _l in CHIPS_SOLL:
        assert k in cnt, "der Zaehlerblock liefert keinen Wert fuer %r" % k
    # Vier Geraete: A verfuegbar, B ausgegeben, C verloren, D verfuegbar+faellig
    assert cnt["alle"] == 4, cnt
    assert cnt["verfuegbar"] == 2, cnt
    assert cnt["ausgegeben"] == 1, cnt
    assert cnt["verloren"] == 1, cnt
    assert cnt["kalib_faellig"] == 1, cnt
    assert 'chip.label+" ("+cnt+")"' in wz, (
        "der Chip zeigt seinen Zaehler nicht mehr an")
    assert nur_code_treffer(wz, "setWerkStatusFilter(chip.key)"), (
        "der Chip schaltet den Statusfilter nicht mehr um")


def test_kalib_faellig_haengt_nicht_am_status(wz):
    """Ein verfuegbares Geraet kann faellig sein - der Chip zaehlt ueber
    `_wzKalibFaellig`, nicht ueber `w.status`. Wer das beim Umbau vereinfacht,
    verliert genau die Faelle, um die es geht."""
    assert nur_code_treffer(wz, "if(_wzKalibFaellig(w))cnt.kalib_faellig++;"), (
        "der Chip 'Kalibrierung faellig' zaehlt nicht mehr ueber "
        "_wzKalibFaellig")


# ───────────────────────────────────────────────────────────────────────────
# 4. "Ausleihen" je Geraet
# ───────────────────────────────────────────────────────────────────────────
def test_ausleihen_kommt_aus_dem_aufruf_nicht_aus_dem_text(wz, node_exe,
                                                           tmp_path):
    ist = ausleihknopf(wz, node_exe, tmp_path)
    assert len(ist) == 3, ist
    assert ist[0] and uml("Ausleihen").search(ist[0]), (
        "ein verfuegbares Geraet gibt keinen Ausleih-Knopf: %r" % (ist[0],))
    assert ist[1] and uml("Zurück").search(ist[1]), (
        "ein an mich ausgegebenes Geraet gibt keinen Rueckgabe-Knopf: %r"
        % (ist[1],))
    assert ist[2] is None, (
        "ein Geraet in Reparatur gibt einen Knopf, obwohl es keinen geben "
        "darf: %r" % (ist[2],))


def test_ausleihknopf_steht_an_beiden_listenstellen(wz):
    """Karte am Telefon UND Tabellenzeile am Rechner. Faellt eine weg, ist der
    Knopf fuer die halbe Belegschaft verschwunden."""
    stellen = nur_code_treffer(wz, "_wzQuickBtn(w)")
    assert len(stellen) == 2, (
        "_wzQuickBtn(w) wird %d mal aufgerufen, erwartet 2 (Mobil-Karte und "
        "Tabellenzeile)." % len(stellen))


# ───────────────────────────────────────────────────────────────────────────
# 5. Die vier Kopfknoepfe - ihre HANDLER
# ───────────────────────────────────────────────────────────────────────────
def test_kopfknopf_neues_geraet_oeffnet_das_formular(wz):
    assert nur_code_treffer(wz, "onClick: openNew"), (
        "der Knopf 'Neues Geraet' haengt nicht mehr an openNew")
    rumpf = block(wz, A_OPENNEW, "{")
    for muss in ("setForm(defWz())", "setEditId(null)", 'setSub("form")'):
        assert muss in rumpf, (
            "openNew macht %r nicht mehr - Rumpf: %s" % (muss, rumpf[:200]))


def test_kopfknopf_labels_druckt_etiketten(wz):
    assert nur_code_treffer(wz, '"Werkzeug-Labels"'), (
        "der Labels-Knopf ruft printLabels nicht mehr mit 'Werkzeug-Labels' auf")
    assert nur_code_treffer(
        wz, "printLabels(_list.map(w=>({name:w.name,code:w.inventarnr,"
            "inventarnr:w.inventarnr}))"), (
        "der Labels-Knopf uebergibt nicht mehr Name+Code je Geraet")
    assert nur_code_treffer(wz, '["stillgelegt","verloren"].includes(w.status)'), (
        "der Labels-Knopf filtert stillgelegte/verlorene Geraete nicht mehr")
    assert nur_code_treffer(wz, "_isVAdminWz&&React.createElement('button'"), (
        "das Rechte-Gatter des Labels-Knopfes ist weg")


def test_kopfknopf_excel_haengt_an_exportwz(wz):
    assert nur_code_treffer(wz, "onClick: exportWz"), (
        "der Excel-Knopf haengt nicht mehr an exportWz")
    rumpf = block(wz, A_EXPORT, "{")
    assert "genXls(" in rumpf, "exportWz erzeugt keine Tabelle mehr"
    assert "sorted.map(" in rumpf, (
        "exportWz exportiert nicht mehr `sorted` - das war der Befund aus "
        "v3.9.880 (rohe Prop statt gerenderter Liste)")


def test_kopfknopf_pdf_ruft_den_druckdialog(wz):
    assert nur_code_treffer(wz, 'onClick: ()=>window.print(), style: xBtn("pdf")'), (
        "der PDF-Knopf ruft window.print() nicht mehr")


def test_alle_vier_kopfknoepfe_stehen_in_einer_zeile(wz):
    """Sie gehoeren zusammen: derselbe Behaelter, `mob-stack` fuer das Telefon.
    Wer einen davon herausloest, bricht die Kopfzeile am Telefon um."""
    kopf = wz[wz.find('className: "header-row"'):]
    kopf = kopf[:kopf.find('className: "kpi-grid"')]
    assert kopf, "die Kopfzeile von WerkzeugView ist nicht mehr auffindbar"
    assert 'className: "mob-stack"' in kopf, (
        "die Knopfreihe im Kopf tragt kein mob-stack mehr")
    for muss in ("onClick: openNew", '"Werkzeug-Labels"', "onClick: exportWz",
                 "()=>window.print()"):
        assert muss in kopf, (
            "%r steht nicht mehr in der Kopfzeile von WerkzeugView" % muss)


# ───────────────────────────────────────────────────────────────────────────
# 6. Die fuenf Reiter und ihre Zielansichten
# ───────────────────────────────────────────────────────────────────────────
def test_fuenf_reiter_ergeben_sich_aus_der_liste(wz, node_exe, tmp_path):
    ist = reiter(wz, node_exe, tmp_path)
    assert len(ist) == 5, "%d Reiter statt 5: %r" % (
        len(ist), [k for k, _i, _l in ist])
    assert [k for k, _i, _l in ist] == [k for k, _i, _l, _a in REITER_SOLL], (
        "Kennungen oder Reihenfolge der Reiter geaendert: %r"
        % [k for k, _i, _l in ist])
    for (k_soll, i_soll, l_soll, _a), (k, ikone, l) in zip(REITER_SOLL, ist):
        assert ikone == i_soll, (
            "Reiter %s tragt %r statt %r" % (k, ikone, i_soll))
        assert passt(l_soll, l), (
            "Reiter %s heisst im Code %r, erwartet %r" % (k, l, l_soll))


def test_jeder_reiter_fuehrt_zu_seiner_ansicht(wz):
    """Der Reiter setzt `sub`, und zu jedem `sub` gibt es genau einen
    Renderzweig mit einer erkennbaren Ueberschrift. Das ist der Unterschied
    zwischen 'der Reiter ist da' und 'der Reiter fuehrt irgendwohin'."""
    assert nur_code_treffer(
        wz, 'onClick: ()=>{if(t.id==="scan")switchToScan();'
            'else{stopScan();setSub(t.id);}}'), (
        "der gemeinsame Klickweg der Reiter ist weg")
    for kennung, _i, _l, anker in REITER_SOLL:
        zweige = nur_code_treffer(wz, 'sub==="%s"&&' % kennung)
        assert len(zweige) == 1, (
            "zu Reiter %r gibt es %d Renderzweige, erwartet genau einen."
            % (kennung, len(zweige)))
        assert nur_code_treffer(wz, anker), (
            "der Renderzweig von %r hat seine Ueberschrift verloren (%s)"
            % (kennung, anker[:60]))


def test_scan_hat_seinen_eigenen_einstieg(wz):
    """`scan` ist der einzige Reiter, der nicht bloss `setSub` aufruft - er
    raeumt Scanner, letzten Treffer, Meldung und manuellen Code auf."""
    assert nur_code_treffer(
        wz, 'const switchToScan=()=>{stopScan();setScannedWz(null);'
            'setScanMsg("");setManualCode("");setSub("scan");};'), (
        "switchToScan ist weg oder anders - dann bleibt beim Reiterwechsel "
        "die Kamera an")


def test_die_rechte_schalten_zwei_reiter_ab(wz, node_exe, tmp_path):
    """Ein Monteur sieht DREI Reiter, ein Admin fuenf. Eine Messung nur mit
    Admin-Rechten wuerde beide Gatter uebersehen."""
    ohne = reiter(wz, node_exe, tmp_path, darf_checkout=False, ist_admin=False,
                  name="reiter_ohne.js")
    assert [k for k, _i, _l in ohne] == ["scan", "liste", "kalib"], (
        "ohne wz_edit und ohne isAdmin bleiben %r - erwartet scan/liste/kalib"
        % [k for k, _i, _l in ohne])
    nur_checkout = reiter(wz, node_exe, tmp_path, darf_checkout=True,
                          ist_admin=False, name="reiter_ck.js")
    assert [k for k, _i, _l in nur_checkout] == ["scan", "liste", "checkout",
                                                 "kalib"], nur_checkout


def test_der_reiter_form_beschriftet_sich_nach_editid(wz, node_exe, tmp_path):
    """Heute schon: 'Neu' ohne editId, 'Bearbeiten' mit. Eine feste
    Beschriftung waere in einem der beiden Faelle falsch."""
    neu = reiter(wz, node_exe, tmp_path, edit_id=None, name="reiter_neu.js")
    bearb = reiter(wz, node_exe, tmp_path, edit_id="W1", name="reiter_bearb.js")
    assert neu[-1][0] == "form" and bearb[-1][0] == "form"
    assert passt("Neu", neu[-1][2]), neu[-1]
    assert passt("Bearbeiten", bearb[-1][2]), bearb[-1]


def test_die_reiter_tragen_am_telefon_nur_die_ikone(wz):
    """DER IST-ZUSTAND, festgehalten - nicht gefordert.

    Die Beschriftung existiert im Code (`l`), wird unter BP_MOB aber
    weggelassen. Das ist der Grund fuer diese ganze Vorarbeit. Der Riegel
    prueft NICHT, dass das so bleibt - er haelt fest, dass die Beschriftung
    im Code vorhanden ist und die Unterdrueckung an EINER Stelle sitzt.
    """
    assert nur_code_treffer(wz, 'isMob?"":t.l'), (
        "die Stelle, an der die Reiterbeschriftung am Telefon unterdrueckt "
        "wird, ist nicht mehr auffindbar - entweder behoben oder verschoben. "
        "Beides will nachgesehen werden.")
    assert nur_code_treffer(wz, "const isMob=ww<BP_MOB;"), (
        "WerkzeugView misst die Breite nicht mehr ueber BP_MOB")


# ───────────────────────────────────────────────────────────────────────────
# 7. DIE KOEDER (Regel 3)
#
# Jede Messung oben ist eine Funktion auf einem Quelltext. Hier bekommen
# dieselben Funktionen absichtlich verstuemmelte Kopien - und MUESSEN rot
# werden. Ohne diesen Abschnitt waere ein ausgefallener Riegel gruen.
# ───────────────────────────────────────────────────────────────────────────
def test_koeder_ein_fehlender_status_wird_gefunden(index_html, node_exe,
                                                   tmp_path):
    kaputt = index_html.replace('stillgelegt:{l:"Stillgelegt"',
                                'xxlgelegt:{l:"Stillgelegt"', 1)
    assert kaputt != index_html, "der Koeder konnte nichts verstuemmeln"
    ist = statuswerte(kaputt, node_exe, tmp_path, name="koeder_status.js")
    assert [k for k, _l, _i in ist] != [k for k, _l in STATUS_SOLL], (
        "EIN UMBENANNTER STATUS BLIEB UNBEMERKT. Der Riegel oben kann nicht "
        "rot werden und ist damit wertlos.")


def test_koeder_eine_fehlende_kategorie_wird_gefunden(index_html, node_exe,
                                                      tmp_path):
    kaputt = index_html.replace('kabel:{l:"Kabelwerkzeug"', 'kabel:{l:"X"', 1)
    assert kaputt != index_html, "der Koeder konnte nichts verstuemmeln"
    ist = kategorien(kaputt, node_exe, tmp_path, name="koeder_kat.js")
    beschriftungen = [l for _k, l, _i in ist]
    assert not all(passt(s, l) for (_k, s), l in zip(KAT_SOLL, beschriftungen)), (
        "EINE GEAENDERTE KATEGORIE-BESCHRIFTUNG BLIEB UNBEMERKT.")


def test_koeder_ein_fehlender_chip_wird_gefunden(wz, node_exe, tmp_path):
    kaputt = wz.replace("{key:'verloren',label:'❌ Defekt'}", "", 1)
    assert kaputt != wz, "der Koeder konnte nichts verstuemmeln"
    ist = chips(kaputt, node_exe, tmp_path, name="koeder_chips.js")
    assert len(ist) != 5, (
        "EIN ENTFERNTER FILTER-CHIP BLIEB UNBEMERKT - es wurden weiter 5 "
        "gezaehlt.")


def test_koeder_ein_verlorener_reiter_wird_gefunden(wz, node_exe, tmp_path):
    kaputt = wz.replace('{id:"kalib",i:"🔧",l:"Service"},', "", 1)
    assert kaputt != wz, "der Koeder konnte nichts verstuemmeln"
    ist = reiter(kaputt, node_exe, tmp_path, name="koeder_reiter.js")
    assert [k for k, _i, _l in ist] != [k for k, _i, _l, _a in REITER_SOLL], (
        "EIN ENTFERNTER REITER BLIEB UNBEMERKT.")


def test_koeder_ein_verschwundener_ausleihknopf_wird_gefunden(wz, node_exe,
                                                             tmp_path):
    kaputt = wz.replace('&&_myMid)return React.createElement', "&&false)return "
                        "React.createElement", 1)
    assert kaputt != wz, "der Koeder konnte nichts verstuemmeln"
    ist = ausleihknopf(kaputt, node_exe, tmp_path, name="koeder_ausleihen.js")
    assert ist[0] is None, (
        "DER AUSLEIH-KNOPF WURDE WEITER GEMELDET, obwohl seine Bedingung "
        "abgeschaltet ist: %r" % (ist[0],))


def test_koeder_ein_toter_handler_wird_gefunden(wz):
    """`nur_code_treffer` darf nicht auf Kommentare anspringen - und muss
    anspringen, wenn der Handler wirklich weg ist."""
    kaputt = wz.replace("onClick: openNew", "onClick: nichts", 1)
    assert kaputt != wz, "der Koeder konnte nichts verstuemmeln"
    assert not nur_code_treffer(kaputt, "onClick: openNew"), (
        "EIN ERSETZTER HANDLER BLIEB UNBEMERKT.")
    # Und die Gegenrichtung: derselbe Text IM KOMMENTAR darf NICHT zaehlen.
    getarnt = "var a=1;/* hier stand mal onClick: openNew */var b=2;"
    assert not nur_code_treffer(getarnt, "onClick: openNew"), (
        "ein Handler im Kommentar wurde als vorhanden gezaehlt - dann misst "
        "dieser Riegel Prosa.")


def test_koeder_die_umlaut_toleranz_ist_nicht_zu_weit(index_html):
    """Regel: tolerant suchen, aber nicht so tolerant, dass ein Treffer
    entsteht, wo keiner ist."""
    assert passt("Verfügbar", "Verfügbar")
    assert passt("Verfügbar", "Verf&uuml;gbar")
    assert passt("Verfügbar", "Verf\\u00fcgbar")
    assert not passt("Verfügbar", "Verfall")
    assert not passt("Verfügbar", "Verfügbare")
    assert not passt("Verfügbar", "Verfgbar")
    assert not passt("Messgeräte", "Messgerate")
    # Der Umlaut ist die EINZIGE Stelle mit Spielraum - ein anderer Buchstabe
    # darf nicht durchgehen.
    assert not passt("Stillgelegt", "Stilllegung")
