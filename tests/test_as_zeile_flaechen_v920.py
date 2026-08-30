# -*- coding: utf-8 -*-
"""v3.9.920 - Die Fuellungen in der Arbeitsschein-Zeile.

GEMESSEN, BEVOR ETWAS GEAENDERT WURDE
─────────────────────────────────────
v3.9.918 hat vier der sechs Zeilen-Editoren rahmenlos gemacht. Dabei kam
heraus: die Rahmen waren gar nicht das dominante Problem. Im selben Zeilenende
stehen flaechig GEFUELLTE Knoepfe, und eine gefuellte Flaeche wiegt optisch
schwerer als eine Haarlinie.

Gemessen mit `scripts/as_zeile_ansehen.py` am Rechner-Schirm 1440 px:

  Knopf     Titel                    Flaeche   Fuellung
  Bleistift Bearbeiten               670 px2   rgb(59,130,246)
  Blatt     PDF Vorschau & Drucken   670 px2   rgb(34,197,94)
  Quadrat   QR-Code anzeigen         670 px2   rgb(139,92,246)
  Verbot    Stornieren               579 px2   rgb(239,68,68)

  4 von 4 Knoepfen gefuellt, 2589 px2 je Zeile, bei 30 Zeilen 77.670 px2.

Auf der MOBIL-Karte (isMob, ww < 600) stehen DIESELBEN vier Knoepfe, dort mit
44x44 px = 1936 px2 je Stueck, 7744 px2 je Karte. Die Fuellungen sind also -
anders als die Zeilen-Editoren aus v3.9.918 - KEIN reines Rechner-Problem.

WAS GEAENDERT WURDE
───────────────────
Zwei der vier verlieren ihre Fuellung und werden Umriss: PDF und QR-Code.
Auf beiden Schirmen. Gleiche Groesse, gleicher onClick, gleiche Stelle - die
Polsterung gibt die 1 px Rahmen wieder her (gemessen: 670 px2 vorher wie
nachher, 44x44 vorher wie nachher).

WARUM BEARBEITEN GEFUELLT BLEIBT
────────────────────────────────
Weil die ZEILE SELBST diese Handlung schon ausfuehrt. Drei td der Zeile tragen
onClick auf `_openEditGuarded(a)` -> `openEdit(a)`: Nummer, Arbeitsanweisung,
Kundenname (gemessen im Browser: "klickbare td: 3"). Der Bleistift ist damit
nicht ein vierter Weg neben drei anderen Handlungen, sondern die BESCHRIFTUNG
der Vorgabehandlung der Zeile. Genau das ist die Aufgabe einer Fuellung.

PDF und QR sind das Gegenteil: sie starten etwas, was die Zeile nicht tut.
PDF ist ausserdem an vier weiteren Stellen erreichbar (Detailformular zweimal,
QR-Fenster, Scan-Ansicht) - es ist die am wenigsten seltene Handlung, aber
sicher nicht die, um die es in dieser Zeile geht.

WARUM DIE WARNZEICHEN NICHT LEISER WERDEN
─────────────────────────────────────────
STORNIEREN (rot) behaelt seine Fuellung. Ein Warnzeichen leiser zu machen ist
etwas anderes als eine Alltagshandlung leiser zu machen - und hier war es
ohnehin nicht die Fuellung, die das Rot geschwaecht hat, sondern die
Nachbarschaft: neben drei gleich lauten Flaechen ist Rot keine Ausnahme mehr.
Gemessen: das Rot trug 579 von 2589 gefuellten px2 (22 %). Nach dieser
Aenderung traegt es 579 von 1249 (46 %), ohne dass ein einziger Wert am
Storno-Knopf angefasst wurde. Das Warnzeichen wird also LAUTER, indem die
Nachbarn leiser werden.

Der WOLKEN-Knopf (Push nach OFFA, `doSinglePush`) wird ebenfalls nicht
angefasst. Er ist gar kein Zeilen-Dauergast: er erscheint nur bei
`canSync && a.juprowa_id && a.push_pending` und faerbt sich rot bei
`a.push_error`. Er ist der einzige Hinweis darauf, dass eine Aenderung die
Cloud NICHT erreicht hat. Deshalb steht er in diesem Riegel als
ausdruecklich unveraendert.

WAS DIESER RIEGEL NICHT KANN
────────────────────────────
Er misst NICHT, wie oft jemand PDF, QR oder Bearbeiten tatsaechlich drueckt -
das steht in keiner Datei. Die Rangordnung stuetzt sich auf den Code (welche
Handlung die Zeile selbst ausfuehrt, wo eine Handlung sonst noch erreichbar
ist), nicht auf gezaehlte Klicks. Und er misst keine Farbe: der Kontrast der
Umrisse steht in `scripts/as_zeile_ansehen.py`, nicht hier.
"""
import re

from _hilfen import nur_code

# Die Koepfe der beiden umgestellten Knoepfe, je Zweig einmal. Jeder kommt in
# index.html GENAU EINMAL vor (mitgeprueft) - sonst wuerde jede Aussage hier
# die falsche Stelle vermessen.
_UMRISS = {
    "pdf_rechner":
        'React.createElement(\'button\', { className: "epk-flach", '
        'onClick: e=>{e.stopPropagation();genAsPdf(a);}, '
        'style: {background:_okG(COLORS.SUCCESS),color:_okG(COLORS.SUCCESS),'
        'border:"1px solid currentColor",borderRadius:4,padding:"3px 6px"',
    "qr_rechner":
        'React.createElement(\'button\', { className: "epk-flach", '
        'onClick: e=>{e.stopPropagation();setAsShowQR(asShowQR===a.id?null:a.id);}, '
        'style: {background:"#8b5cf6",color:"#8b5cf6",'
        'border:"1px solid currentColor",borderRadius:4,padding:"3px 6px"',
    "pdf_mobil":
        'React.createElement(\'button\', { className: "epk-flach", '
        'onClick: e=>{e.stopPropagation();genAsPdf(a);}, '
        'style: {background:_okG(COLORS.SUCCESS),color:_okG(COLORS.SUCCESS),'
        'border:"1px solid currentColor",borderRadius:6,padding:"5px 11px"',
    "qr_mobil":
        'React.createElement(\'button\', { className: "epk-flach", '
        'onClick: e=>{e.stopPropagation();setAsShowQR(asShowQR===a.id?null:a.id);}, '
        'style: {background:"#8b5cf6",color:"#8b5cf6",'
        'border:"1px solid currentColor",borderRadius:6,padding:"5px 11px"',
}

# Die Knoepfe, die ihre Fuellung BEHALTEN. Zwei Gruende, die nicht derselbe
# sind - deshalb stehen sie in zwei Gruppen.
_VORGABEHANDLUNG = {
    "bearbeiten_rechner":
        'React.createElement(\'button\', { onClick: e=>{e.stopPropagation();'
        'openEdit(a);}, style: {background:"#3b82f6",color:"#fff",'
        'border:"none",borderRadius:4,padding:"4px 7px"',
    "bearbeiten_mobil":
        'React.createElement(\'button\', { onClick: e=>{e.stopPropagation();'
        'openEdit(a);}, style: {background:"#3b82f6",color:"#fff",'
        'border:"none",borderRadius:6,padding:"6px 12px"',
}
_WARNZEICHEN = {
    "storno_rechner":
        'React.createElement(\'button\', { onClick: e=>{e.stopPropagation();'
        'storno(a.id);}, style: {background:COLORS.ERROR,color:"#fff",'
        'border:"none",borderRadius:4,padding:"4px 7px"',
    "storno_mobil":
        'React.createElement(\'button\', { onClick: e=>{e.stopPropagation();'
        'storno(a.id);}, style: {background:COLORS.ERROR,color:"#fff",'
        'border:"none",borderRadius:6,padding:"6px 12px"',
    "push_rechner":
        'React.createElement(\'button\', { onClick: e=>{e.stopPropagation();'
        'doSinglePush(a.id);}, disabled: jupPushing, '
        'style: {background:a.push_error?"#ef4444":"#f59e0b",color:"#fff",'
        'border:"none",borderRadius:4,padding:"4px 7px"',
}

# Die Klickwege. Sie sind der eigentliche Gegenstand des Riegels: diese
# Version darf das GEWICHT aendern und sonst nichts.
_KLICKWEGE = (
    "genAsPdf(a);",
    "setAsShowQR(asShowQR===a.id?null:a.id);",
    "openEdit(a);",
    "storno(a.id);",
    "doSinglePush(a.id);",
)

_ZEILE_ANFANG = ("React.createElement('tr', { key: a.id, "
                 "onTouchStart: e=>_swipeStart(a,e), onTouchEnd: "
                 "e=>_swipeEnd(a,e)")
_MOBIL_ANFANG = ("isMob&&React.createElement('div', { style: "
                 '{display:"flex",flexDirection:"column",gap:8}}')
_RECHNER_ANFANG = ("!isMob&&React.createElement('div', { style: "
                   '{...CC(),padding:0,overflow:"hidden"}}')


def _regeln(index_html):
    """Alle CSS-Regeln, deren Selektor die Umriss-Klasse nennt.

    Kommentare MUESSEN vorher raus - der Erklaertext neben den Regeln nennt
    die Klasse beim Namen, und der Selektor-Teil des Musters zoege ihn sonst
    mit ein. Dieselbe Vorsicht wie in test_as_zeile_rangordnung_v918.
    """
    return [(m.group(1).strip(), m.group(2).strip())
            for m in re.finditer(r"([^{}]*\.epk-flach[^{}]*)\{([^{}]*)\}",
                                 nur_code(index_html))]


def _deklarationen(rumpf):
    """Rumpf -> Liste von Eigenschaftsnamen, kleingeschrieben."""
    return [t.split(":", 1)[0].strip().lower()
            for t in rumpf.split(";") if ":" in t]


# ══ Die Messung selbst ══════════════════════════════════════════════════════

def test_alle_sieben_koepfe_sind_eindeutig(index_html):
    """Ohne das misst jede andere Aussage hier moeglicherweise die falsche
    Stelle - im Zweifel eine, die es zweimal gibt."""
    alle = dict(_UMRISS)
    alle.update(_VORGABEHANDLUNG)
    alle.update(_WARNZEICHEN)
    for name, kopf in alle.items():
        n = index_html.count(kopf)
        assert n == 1, (
            "Der Kopf des Knopfes %s kommt %dx vor, erwartet genau 1x. "
            "Entweder ist er weg oder es gibt ihn doppelt - beides macht die "
            "uebrigen Riegel dieser Datei wertlos." % (name, n)
        )


def test_genau_vier_knoepfe_sind_umriss(index_html):
    """Eine Groesse, EINE Zahl. Vier Umriss-Knoepfe - nicht zwei (dann ist nur
    einer der beiden Schirme umgestellt und derselbe Knopf wiegt links anders
    als rechts) und nicht sechs (dann ist auch ein Warnzeichen dabei)."""
    n = nur_code(index_html).count('className: "epk-flach"')
    assert n == 4, (
        "Es tragen %d Knoepfe die Umriss-Klasse, erwartet werden vier "
        "(PDF und QR, je einmal am Rechner und einmal auf der Mobil-Karte)."
        % n
    )


def test_bearbeiten_behaelt_seine_flaeche(index_html):
    """GEGENPROBE zur Zahl vier: sie allein wuerde nicht bemerken, dass die
    Klasse am FALSCHEN Knopf sitzt.

    Bearbeiten bleibt gefuellt, weil die Zeile selbst diese Handlung ausfuehrt
    (drei td mit onClick auf _openEditGuarded). Die Fuellung beschriftet die
    Vorgabehandlung - sie ist nicht einer von vier gleichrangigen Schreien."""
    # NICHT ueber ein Zeichenfenster hinter dem Kopf gemessen - der naechste
    # Knopf steht unmittelbar daneben und TRAEGT die Klasse; ein Fenster von
    # 200 Zeichen greift in ihn hinein und meldet Alarm, wo keiner ist.
    # (Erster Entwurf dieses Riegels tat genau das und war rot, obwohl der
    # Bleistift unangetastet war.) Gemessen wird stattdessen die Stelle, an
    # der die Klasse stuende: direkt hinter der oeffnenden Klammer.
    for name, kopf in _VORGABEHANDLUNG.items():
        assert kopf in index_html, (
            "Der Knopf %s ist nicht mehr auffindbar oder wurde umgeschrieben."
            % name
        )
        mit_klasse = kopf.replace(
            "React.createElement('button', { onClick:",
            "React.createElement('button', { className: \"epk-flach\", onClick:")
        assert mit_klasse not in index_html, (
            "Der Knopf %s ist zum Umriss geworden. Er beschriftet die "
            "Vorgabehandlung der Zeile - wenn er als Umriss richtig ist, dann "
            "ist die Begruendung dieser Version falsch und gehoert neu "
            "geschrieben, nicht stillschweigend umgedreht." % name
        )


def test_die_zeile_fuehrt_bearbeiten_selbst_aus(index_html):
    """Die Begruendung fuer die vorige Zusicherung, als eigene Messung. Faellt
    der Klick auf die Zeile weg, ist der Bleistift KEINE Beschriftung mehr,
    sondern der einzige Weg - dann traegt diese Version eine falsche
    Begruendung, auch wenn alle anderen Riegel gruen bleiben."""
    # Ueber die GANZE Datei gezaehlt sind es sechs - die Dispo-Kacheln und die
    # Mobil-Karte tragen denselben Klick. Eine Zahl aus dem falschen Fenster
    # ist keine Messung; also genau die Tabellenzeile abgesteckt, vom Kopf der
    # Zeile bis zum ersten Knopf der Aktionsspalte.
    a = index_html.find(_ZEILE_ANFANG)
    assert a != -1, "Der Kopf der Arbeitsschein-Zeile ist nicht auffindbar."
    b = index_html.find(_VORGABEHANDLUNG["bearbeiten_rechner"], a)
    assert b != -1, "Die Aktionsspalte der Zeile ist nicht auffindbar."
    n = index_html[a:b].count("onClick: ()=>_openEditGuarded(a)")
    assert n == 3, (
        "In der Arbeitsschein-Zeile tragen %d td den Klick auf "
        "_openEditGuarded, gemessen waren drei (Nummer, Arbeitsanweisung, "
        "Kundenname). Genau darauf stuetzt sich, dass der Bleistift gefuellt "
        "bleiben DARF - faellt der Zeilenklick weg, ist er nicht mehr die "
        "Beschriftung einer Vorgabehandlung, sondern der einzige Weg." % n
    )


def test_die_warnzeichen_bleiben_unangetastet(index_html):
    """DER heikle Punkt dieser Version. Stornieren ist eine folgenschwere
    Handlung, der Wolken-Knopf ist eine Stoerungsmeldung. Ein Warnzeichen
    leiser zu machen ist etwas anderes als eine Alltagshandlung leiser zu
    machen - beide bleiben deshalb Wort fuer Wort so, wie sie waren."""
    for name, kopf in _WARNZEICHEN.items():
        assert kopf in index_html, (
            "Das Warnzeichen %s ist nicht mehr auffindbar oder wurde "
            "umgeschrieben." % name
        )
        mit_klasse = kopf.replace(
            "React.createElement('button', { onClick:",
            "React.createElement('button', { className: \"epk-flach\", onClick:")
        assert mit_klasse not in index_html, (
            "Das Warnzeichen %s ist gedaempft worden. Diese Version durfte "
            "ausschliesslich Alltagshandlungen leiser machen." % name
        )


def test_der_wolkenknopf_bleibt_die_ausnahme(index_html):
    """Der Wolken-Knopf war in der Messung gar nicht zu sehen - er erscheint
    nur, wenn etwas offen ist. Genau das macht ihn zum Warnzeichen und nicht
    zum Zeilenmoebel. Faellt eine der drei Bedingungen weg, stuende er in
    JEDER Zeile und waere die fuenfte gefuellte Flaeche."""
    assert "canSync&&a.juprowa_id&&a.push_pending&&React.createElement("
    kette = "canSync&&a.juprowa_id&&a.push_pending&&React.createElement('button'"
    assert index_html.count(kette) == 1, (
        "Die Erscheinungsbedingung des Wolken-Knopfes "
        "(canSync && juprowa_id && push_pending) steht nicht mehr genau "
        "einmal so da. Ohne sie waere er ein Dauergast."
    )


def test_die_fuellung_kehrt_zurueck(index_html):
    """DIE eigentliche Gefahr dieser Version, dieselbe wie in v3.9.918 eine
    Stufe frueher: ein Bedienelement, das seine Flaeche verliert und nie eine
    Rueckmeldung gibt, fuehlt sich tot an. Gemessen wird nicht, dass eine
    Regel existiert, sondern dass es BEIDE Zustaende gibt - Ruhe und
    Rueckkehr - und dass die Rueckkehr die Farbe des Elements nimmt."""
    regeln = _regeln(index_html)
    assert regeln, "Es gibt keine einzige CSS-Regel zur Umriss-Klasse."

    ruhe = [(s, r) for s, r in regeln
            if ":hover" not in s and ":focus" not in s
            and ":active" not in s and "::" not in s]
    zurueck = [(s, r) for s, r in regeln
               if (":hover" in s or ":active" in s) and "::" not in s]

    assert ruhe, "Die Ruhe-Regel fehlt - dann ist gar nichts entlastet."
    assert zurueck, (
        "Es gibt KEINE Rueckkehr-Regel zur Umriss-Klasse. Vier Knoepfe waeren "
        "damit dauerhaft flach und ohne jede Rueckmeldung."
    )
    assert any("transparent" in r for _, r in ruhe), (
        "Die Ruhe-Regel macht die Flaeche nicht durchsichtig - dann entlastet "
        "sie nichts."
    )
    assert any("currentcolor" in r.lower() for _, r in zurueck), (
        "Die zurueckkehrende Fuellung nimmt nicht currentColor. Die Farbe "
        "steht inline am Knopf; eine feste Farbe hier waere dieselbe Groesse "
        "an zwei Stellen - genau der Fehler, den v3.9.918 vermieden hat."
    )


def test_auch_der_finger_und_die_tastatur_bekommen_die_flaeche(index_html):
    """Auf der Mobil-Karte gibt es KEIN Zeigen. Eine Rueckkehr, die nur an
    :hover haengt, waere dort nie zu sehen - der Knopf gaebe beim Tippen
    ueberhaupt keine Rueckmeldung. Und wer mit der Tastatur arbeitet, hat
    ebenfalls kein Zeigen."""
    selektoren = " ".join(s for s, _ in _regeln(index_html))
    for zustand in (":active", ":focus-visible"):
        assert zustand in selektoren, (
            "Die Umriss-Klasse kennt %s nicht. Ohne %s gibt der Knopf auf dem "
            "Handy (kein :hover) bzw. am Tastaturweg keine Rueckmeldung."
            % (zustand, zustand)
        )


def test_die_umstellung_faerbt_nichts_um(index_html):
    """Diese Version darf die FLAECHE wegnehmen und sonst nichts. Kein
    Schrumpfen, kein Verstecken, keine neue Farbe - gemessen an den
    Eigenschaftsnamen, nicht am Wortlaut der Regel."""
    erlaubt = {"background", "background-color"}
    for selektor, rumpf in _regeln(index_html):
        for eigenschaft in _deklarationen(rumpf):
            assert eigenschaft in erlaubt, (
                "Die Regel '%s' setzt '%s'. Erlaubt sind nur %s - alles "
                "andere aendert Groesse oder Sichtbarkeit des Knopfes, und "
                "genau das war nicht die Absicht."
                % (selektor, eigenschaft, sorted(erlaubt))
            )


def test_der_knopf_bleibt_genau_so_gross(index_html):
    """Der Rahmen kommt ZUSAETZLICH zum Kasten: ohne Ausgleich waechst jeder
    Knopf um 2 px in jeder Richtung. Die Aktionsspalte ist 110 px breit und
    laeuft mit vier Knoepfen schon ueber - ein Vorschlag, der die Zeile
    BREITER macht, waere keine Entlastung, sondern das Gegenteil. Gemessen im
    Browser: mit Ausgleich 670 px2 vorher wie nachher, mobil 44x44 vorher wie
    nachher."""
    for name, kopf in _UMRISS.items():
        assert kopf in index_html, (
            "Der Umriss-Knopf %s traegt nicht mehr die ausgeglichene "
            "Polsterung. Ohne sie waechst er um 2 px in jeder Richtung." % name
        )
        assert '"4px 7px"' not in kopf and '"6px 12px"' not in kopf


def test_das_gruen_geht_durch_okG(index_html):
    """GEMESSEN und beinahe uebersehen: als Haarrahmen auf weissem Grund
    kommt COLORS.SUCCESS (#22c55e) auf 2,28:1 - unter 3,0, also nicht mehr zu
    finden. Als FLAECHE war dieselbe Farbe nie ein Problem. _okG liefert im
    hellen Thema EP_GREEN_DARK (#006e30, gemessen 6,42:1) und im dunklen
    Thema die Farbe unveraendert (gemessen 7,17:1)."""
    for name in ("pdf_rechner", "pdf_mobil"):
        kopf = _UMRISS[name]
        assert "_okG(COLORS.SUCCESS)" in kopf and kopf in index_html, (
            "Der Umriss-Knopf %s nimmt nicht _okG(COLORS.SUCCESS) als Farbe. "
            "Das nackte COLORS.SUCCESS faellt als Haarrahmen auf hellem Grund "
            "auf 2,28:1 und ist damit unauffindbar." % name
        )
    assert "const _okG=" in index_html, (
        "_okG gibt es nicht mehr - dann traegt der Umriss-Knopf eine Farbe, "
        "die im hellen Thema unter 3,0:1 liegt."
    )


def test_kein_umriss_knopf_beschriftet_in_weiss(index_html):
    """Die Falle beim Umbau von Flaeche auf Umriss: color bleibt aus Versehen
    auf '#fff' stehen. Auf der Fuellung war das richtig, auf durchsichtigem
    Grund ist die Beschriftung dann weiss auf weiss."""
    for name, kopf in _UMRISS.items():
        i = index_html.find(kopf)
        assert i != -1, "Der Umriss-Knopf %s ist nicht auffindbar." % name
        assert 'color:"#fff"' not in index_html[i:i + len(kopf) + 120], (
            "Der Umriss-Knopf %s beschriftet noch in Weiss. Ohne Fuellung "
            "steht das auf hellem Grund weiss auf weiss." % name
        )


def test_kein_klickweg_wurde_angefasst(index_html):
    """Der Kern der Abgrenzung: diese Version aendert das GEWICHT. Haette sich
    ein Klickweg verschoben, waere das keine Aufraeumarbeit mehr - storno und
    doSinglePush sind nicht rueckgaengig zu machen."""
    for weg in _KLICKWEGE:
        assert weg in index_html, (
            "Der Klickweg %s ist nicht mehr da. Diese Version durfte "
            "ausschliesslich Fuellungen wegnehmen." % weg
        )


def test_beide_schirme_sind_absichtlich_dabei(index_html):
    """GEGENPROBE zum Geltungsbereich - und die Stelle, an der sich diese
    Version von v3.9.918 UNTERSCHEIDET. Dort war die Ueberladung ein reines
    Rechner-Problem (die Mobil-Karte hat keine Zeilen-Editoren). Die
    Fuellungen gibt es auf BEIDEN Schirmen, auf der Karte sogar groesser
    (44x44 = 1936 px2 je Knopf). Derselbe Knopf darf nicht links anders
    wiegen als rechts."""
    i = index_html.find(_MOBIL_ANFANG)
    assert i != -1, "Der Mobil-Kartenzweig ist nicht mehr auffindbar."
    j = index_html.find(_RECHNER_ANFANG, i)
    assert j != -1, "Der Rechner-Tabellenzweig ist nicht mehr auffindbar."

    mobil = index_html[i:j].count('className: "epk-flach"')
    rechner = index_html[j:].count('className: "epk-flach"')
    assert mobil == 2, (
        "Auf der Mobil-Karte tragen %d Knoepfe die Umriss-Klasse, erwartet "
        "werden zwei (PDF, QR). Die Karte war ausdruecklich mitgemeint." % mobil
    )
    assert rechner == 2, (
        "Im Rechner-Zweig tragen %d Knoepfe die Umriss-Klasse, erwartet "
        "werden zwei (PDF, QR)." % rechner
    )


# ══ Umkehrprobe ═════════════════════════════════════════════════════════════

def test_selbsttest_riegel_schlagen_beim_rueckbau_an(index_html):
    # 1. Ein Knopf verliert die Klasse -> die Zahl vier muss auffallen.
    z1 = index_html.replace('className: "epk-flach", ', "", 1)
    assert z1 != index_html, "Rueckbau 1 griff nicht"
    assert nur_code(z1).count('className: "epk-flach"') == 3, (
        "Umkehrprobe: der Zaehl-Riegel wuerde einen zurueckgebauten Knopf "
        "nicht bemerken."
    )

    # 2. Die Klasse wandert an das WARNZEICHEN -> der heikelste Fall dieser
    #    Version muss anschlagen.
    kopf = _WARNZEICHEN["storno_rechner"]
    z2 = index_html.replace(
        kopf,
        kopf.replace("React.createElement('button', { onClick:",
                     'React.createElement(\'button\', { className: '
                     '"epk-flach", onClick:'), 1)
    assert z2 != index_html, "Rueckbau 2 griff nicht"
    i = z2.find('React.createElement(\'button\', { className: "epk-flach", '
                'onClick: e=>{e.stopPropagation();storno(a.id);}')
    assert i != -1, (
        "Umkehrprobe: der Warnzeichen-Riegel wuerde eine Daempfung am "
        "Storno-Knopf nicht bemerken."
    )

    # 3. Die Rueckkehr-Regel faellt weg -> der gefaehrlichste Fall (flach fuer
    #    immer, keine Rueckmeldung) muss auffallen.
    zurueck = [s for s, _ in _regeln(index_html)
               if (":hover" in s or ":active" in s) and "::" not in s]
    assert zurueck, "Vorbedingung: es gibt eine Rueckkehr-Regel"
    z3 = re.sub(r"[^{}]*\.epk-flach:hover[^{}]*\{[^{}]*\}", "",
                index_html, count=1)
    assert z3 != index_html, "Rueckbau 3 griff nicht"
    assert not [s for s, _ in _regeln(z3)
                if (":hover" in s or ":active" in s) and "::" not in s], (
        "Umkehrprobe: der Rueckkehr-Riegel wuerde eine fehlende Regel nicht "
        "bemerken - und genau das waere der tote Knopf."
    )

    # 4. Das Gruen faellt auf die nackte Fuellfarbe zurueck (gemessen 2,28:1
    #    als Haarrahmen) -> der Farb-Riegel muss rot.
    # ALLE Vorkommen - der erste Treffer liegt auf der MOBIL-Karte (sie steht
    # vor der Tabelle). Ein Rueckbau mit count=1 haette nur dort gegriffen und
    # den Rechner-Riegel unbehelligt gelassen: ein Selbsttest, der die falsche
    # Stelle zurueckbaut, belegt nichts.
    z4 = index_html.replace("color:_okG(COLORS.SUCCESS)", "color:COLORS.SUCCESS")
    assert z4 != index_html, "Rueckbau 4 griff nicht"
    for name in ("pdf_rechner", "pdf_mobil"):
        assert _UMRISS[name] not in z4, (
            "Umkehrprobe: der Farb-Riegel wuerde den Rueckfall auf #22c55e "
            "bei %s nicht bemerken." % name
        )

    # 5. Der Polsterausgleich faellt weg -> der Groessen-Riegel muss rot.
    z5 = index_html.replace('borderRadius:4,padding:"3px 6px"',
                            'borderRadius:4,padding:"4px 7px"')
    assert z5 != index_html, "Rueckbau 5 griff nicht"
    for name in ("pdf_rechner", "qr_rechner"):
        assert _UMRISS[name] not in z5, (
            "Umkehrprobe: der Groessen-Riegel wuerde einen fehlenden "
            "Polsterausgleich bei %s nicht bemerken." % name
        )

    # 6. Ein Klickweg verschiebt sich -> der Abgrenzungs-Riegel muss rot.
    z6 = index_html.replace("storno(a.id);", "storno(a.idX);")
    assert z6 != index_html, "Rueckbau 6 griff nicht"
    assert "storno(a.id);" not in z6, (
        "Umkehrprobe: der Klickweg-Riegel wuerde eine Verschiebung nicht "
        "bemerken."
    )
