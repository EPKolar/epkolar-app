# -*- coding: utf-8 -*-
"""v3.9.961 - der VOLLSTAENDIGE Riegel: kein Knopf, der nie ein Wort zeigt,
bleibt ohne Namen. Beide Erzeuger, beide Anfuehrungszeichen, auch Ternaere.

WARUM ES DIESE DATEI GIBT - drei Luecken in meinen eigenen Riegeln
─────────────────────────────────────────────────────────────────
v3.9.957 hat 33 Knoepfe benannt, v3.9.958 weitere 32, und beide haben je einen
EIGENEN Abtaster mitgebracht. Beide hatten dieselben drei Luecken:

  1. Sie suchten nur `createElement('button'`. Die Datei fuehrt **97** Stellen
     `h('button'` (der lokale Kuerzel `const h=React.createElement`) - die
     wurden NIE angesehen.
  2. Sie lasen den Inhalt nur in DOPPELTEN Anfuehrungszeichen. Sieben Stellen
     stehen in einfachen.
  3. Sie verlangten EIN Literal als ganzen Inhalt. Ein Ternaer aus zwei
     Literalen (`imeiBusy?'…':'✓'`) faellt durch. Und die Zeichenklasse von
     v958 kennt 0x229E (⊞) und 0x00D7 (×) nicht.

Folge, gemessen: **17 Knoepfe**, die nie ein Wort zeigen und keinen Namen
tragen, waren fuer BEIDE Riegel unsichtbar. Sie sind in v3.9.961 benannt.

🔴 UND DAS IST DAS BITTERSTE DARAN: die Regel dagegen ist einen Tag vorher
aufgeschrieben worden - "ein Zaehler, der EINE Schreibweise nicht kennt, meldet
kommt nicht vor". Ich habe sie notiert und am selben Abend zwei Riegel gebaut,
die genau daran vorbeilaufen. Eine Regel, die man kennt, ist keine Regel, die
wirkt; erst ein gemeinsamer Abtaster mit Eichung ist eine.

WAS SICH GEAENDERT HAT
──────────────────────
Der Abtaster liegt jetzt in `scripts/code_scan.py` (`knopf_stellen`,
`hat_namen`, `eichen_knoepfe`) - EINMAL, mit einer Eichung, die alle vier
Formen an einem selbstgebauten Text belegt und zwei Nicht-Treffer ausschliesst.
`hat_namen` liest ausserdem nur die OBERSTE Ebene des Eigenschaftenobjekts: eine
flache Suche zaehlt ein `title:` mit, das im Rumpf eines `onClick` steht, und
genau das hat in einem der alten Abtaster drei Knoepfe falsch als benannt
gefuehrt.

WAS GEPRUEFT WIRD
─────────────────
Ein Knopf muss einen Namen tragen, wenn sein Inhalt NUR aus Symbol-Literalen
bestehen kann - also wenn nach Abzug aller Zeichenketten nichts uebrig ist, was
ein Wort beitragen koennte (kein Bezeichner ausser in der Bedingung eines
Ternaers, kein Plus, kein Index). Traegt er irgendwo ein Wort, verlangt der
Riegel nichts: der Text IST dann der Name.

WAS DIESE DATEI NICHT MISST
───────────────────────────
Ob eine Vorlesehilfe den Namen ansagt, und ob der Name GUT ist - gezaehlt ist
nur, ob einer da ist. Nicht gemessen: Knoepfe, deren Inhalt eine Variable ist
(die kann zur Laufzeit leer werden und ist mit Quelltext nicht entscheidbar),
Bedienelemente, die keine `button` sind (133 Klickflaechen ohne `role` und
`tabIndex`, 461 Eingabefelder ohne Namen - beides gemessen und in
`docs/befunde/BEDIENELEMENTE_OHNE_NAMEN.md` aufgelistet, beides eine
Entscheidung), und die 27 Stellen, die Bedienelemente mit `document.createElement`
statt React bauen.
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import code_scan  # noqa: E402

PFAD = os.path.join(os.path.dirname(__file__), "..", "index.html")

WORT = re.compile(r"[0-9A-Za-zÀ-ɏ]")
LITERAL = re.compile(r'"(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\'')
LIT_GRUPPE = re.compile(r'"((?:[^"\\]|\\.)*)"|\'((?:[^\'\\]|\\.)*)\'')
# Was nach Abzug der Literale noch ein Wort beitragen kann.
TRAEGER = re.compile(r"[A-Za-z0-9_$+\[\]]")


def _lies():
    roh = io.open(PFAD, encoding="utf-8", newline="").read()
    if len(roh) < 3_000_000:
        raise AssertionError(
            "index.html hat nur %d Bytes - Datenverlust. Eine leere Datei hat "
            "keine namenlosen Knoepfe." % len(roh))
    return roh


def _ansicht(text, p):
    tr = list(re.finditer(r"function\s+([A-Za-z_]\w*)\s*\(", text[:p]))
    return tr[-1].group(1) if tr else "?"


def _nur_symbole(kinder):
    """Kann der Inhalt NUR aus Symbolen bestehen?

    Der Kern wird von den Literalen befreit; bleibt danach ein Bezeichner, ein
    Plus oder ein Index uebrig, kann ein Wort dazukommen und der Knopf traegt
    seinen Namen selbst. Fragezeichen und Doppelpunkt sind erlaubt - ein
    Ternaer aus zwei Literalen zeigt in BEIDEN Zustaenden kein Wort.

    Die Bedingung eines Ternaers wird mitgestrichen: `imeiBusy?'…':'✓'` zeigt
    nie ein Wort, obwohl `imeiBusy` ein Bezeichner ist. Seit v3.9.963 gilt
    das auch, wenn die Bedingung ein AUFRUF ist - `isPlanFreigegeben(id)?`.
    """
    kern = kinder.strip()
    if kern.startswith(","):
        kern = kern[1:].strip()
    if not kern:
        return False, []
    # Bedingung eines Ternaers abtrennen, wenn danach nur Literale stehen.
    # v3.9.963: die Bedingung darf ein AUFRUF sein. Vorher stand hier nur
    # der nackte Bezeichner, und `isPlanFreigegeben(pl.id)?"A":"B"` fiel
    # durch - ein Knopf, der nie ein Wort zeigt, galt als benannt.
    # Eine Ebene Verschachtelung in den Argumenten ist abgedeckt; tiefer
    # verschachtelte Bedingungen bleiben eine bekannte Grenze.
    ohne_bed = re.sub(
        r"^!?[A-Za-z_$][\w$.]*\s*"
        r"(?:\((?:[^()]|\([^()]*\))*\))?\s*\?", "?", kern)
    rest = LITERAL.sub("", ohne_bed).replace("?", "").replace(":", "")
    rest = rest.replace(",", "").strip()
    if TRAEGER.search(rest):
        return False, []
    texte = [x or y for x, y in LIT_GRUPPE.findall(kern)]
    if not texte:
        return False, []
    if any(WORT.search(t) for t in texte):
        return False, texte
    return True, texte


def _namenlos(text):
    """(Ansicht, Zeile, Form, Inhalt) je Knopf, der nie ein Wort zeigt und
    keinen Namen traegt."""
    aus = []
    for start, props, kinder in code_scan.knopf_stellen(text):
        if code_scan.hat_namen(props):
            continue
        nur, texte = _nur_symbole(kinder)
        if not nur:
            continue
        aus.append((_ansicht(text, start), text.count("\n", 0, start) + 1,
                    "h(" if not text.startswith("createElement", start) else "cE",
                    "".join(texte)[:24]))
    return sorted(aus, key=lambda x: x[1])


def test_kein_symbolknopf_ohne_namen_in_KEINER_schreibweise():
    """Die Aussage - und diesmal ueber alle 797 Knoepfe, nicht ueber 174."""
    roh = _lies()
    alle = code_scan.knopf_stellen(roh)
    assert len(alle) > 500, (
        "Nur %d Knoepfe gefunden, erwartet um 797. Das ist kein gruenes "
        "Ergebnis: entweder ist der Abtaster blind, oder die Knoepfe sind "
        "anders geschrieben." % len(alle))
    # Und die h(-Form ist wirklich dabei - sonst messen wir wieder nur die
    # Haelfte und merken es nicht.
    hform = sum(1 for s, _, _ in alle
                if not roh.startswith("createElement", s))
    assert hform > 50, (
        "Nur %d Knoepfe in der h(-Form gefunden, erwartet um 97. Genau diese "
        "Form haben die Riegel aus v957/v958 nie angesehen - wenn sie hier "
        "auch fehlt, ist die Luecke zurueck." % hform)
    fund = _namenlos(roh)
    assert not fund, (
        "%d Knopf/Knoepfe zeigen NIE ein Wort und haben keinen Namen:\n%s\n\n"
        "Eine Vorlesehilfe sagt dort nur \"Schaltflaeche\". Den Namen aus dem "
        "onClick ABLESEN, nicht formulieren - und wenn der Knopf umschaltet, "
        "den Namen an dieselbe Bedingung haengen wie den Inhalt.\n"
        "Wortschatz der schon benannten Knoepfe benutzen (\"Schliessen\", "
        "\"Abbrechen\", \"Eintrag loeschen\", \"Zeile hinzufuegen\", \"Monat "
        "zurueck\"), damit die App nicht zwei Woerter fuer dieselbe Handlung "
        "fuehrt."
        % (len(fund),
           "\n".join("  %-20s Z%-7d %-3s %s" % f for f in fund)))


def test_der_abtaster_kennt_alle_vier_formen():
    """EICHUNG - ohne sie ist die 0 oben wertlos."""
    ok, gef, erw = code_scan.eichen_knoepfe()
    assert ok, (
        "Knopf-Eichung gescheitert: %d von %d Formen. Der Abtaster kennt nicht "
        "alle Schreibweisen (oder zaehlt zu viel). Genau daran sind v957 und "
        "v958 vorbeigelaufen." % (gef, erw))


def test_koeder_je_schreibweise():
    """KOEDER, und zwar EINER JE FORM - nicht einer fuer den Zaehler.

    Ein Koeder, der nur die haeufigste Form nachstellt, laesst genau die
    Luecke offen, die hier geschlossen wurde. Vier Faelle, jeder muss
    gefunden werden.
    """
    roh = _lies()
    # 🔴 DER ANKER MUSS `React.` EINSCHLIESSEN. Die erste Fassung verankerte
    # nur an `createElement(...` - und setzte den Koeder damit genau dort ein,
    # wo davor `React.` steht. Aus `h('button'` wurde `React.h('button'`, und
    # die Sperre `(?<![A-Za-z0-9_$.])` vor dem Kuerzel griff zu Recht. Der
    # Koeder meldete "nicht gefunden" und der Abtaster war in Ordnung: ein
    # Koeder, der die Form falsch nachstellt, prueft nichts.
    anker = ", React.createElement('button', { title: \"Abbrechen\""
    assert anker in roh, "Anker fuer die Koeder fehlt."
    faelle = [
        ("createElement, doppelt", "React.createElement('button',{onClick:()=>0},\"✕\")"),
        ("createElement, einfach", "React.createElement('button',{onClick:()=>0},'✕')"),
        ("Kuerzel h(, einfach", "h('button',{onClick:()=>0},'✕')"),
        ("Ternaer aus Literalen", "h('button',{onClick:()=>0},x?'✓':'·')"),
    ]
    for name, code in faelle:
        kaputt = roh.replace(anker, ", " + code + anker, 1)
        fund = _namenlos(kaputt)
        assert fund, (
            "KOEDER '%s' NICHT GEFUNDEN: %s wird nicht erkannt. Genau diese "
            "Form ist v957/v958 durchgegangen." % (name, code))


def test_gegenprobe_ein_knopf_mit_wort_wird_NICHT_gemeldet():
    """Die andere Richtung, und sie ist genauso wichtig.

    Ein Zaehler, der ALLES meldet, schlaegt bei jedem Koeder an und ist
    trotzdem kaputt: er erzeugt Arbeit ohne Wirkung, wird dann gelockert, und
    verliert dabei die echten Faelle.
    """
    roh = _lies()
    anker = ", React.createElement('button', { title: \"Abbrechen\""
    vorher = len(_namenlos(roh))
    for code in ("React.createElement('button',{onClick:()=>0},\"Speichern\")",
                 "h('button',{onClick:()=>0},'Abbrechen')",
                 "h('button',{onClick:()=>0},x?'Ja':'Nein')",
                 "h('button',{onClick:()=>0},'✕ Schliessen')"):
        kaputt = roh.replace(anker, ", " + code + anker, 1)
        assert len(_namenlos(kaputt)) == vorher, (
            "Ein Knopf MIT Wort wird als namenlos gemeldet: %s\n"
            "Dann meldet der Riegel zu viel - und ein Riegel, der zu viel "
            "meldet, wird gelockert und verliert die echten Faelle." % code)


def test_hat_namen_liest_nur_die_oberste_ebene():
    """Ein `title:` im Rumpf eines onClick ist KEIN Name des Knopfes.

    Die flache Suche der alten Abtaster hat genau das mitgezaehlt. Hier wird
    belegt, dass die neue Fassung unterscheidet - sonst gilt ein Knopf als
    benannt, weil irgendwo in seinem Klickrumpf das Wort title steht.
    """
    assert code_scan.hat_namen('{ title: "Da", onClick: ()=>0 }')
    assert code_scan.hat_namen("{ 'aria-label': \"Da\", onClick: ()=>0 }")
    assert not code_scan.hat_namen(
        '{ onClick: ()=>{ el.setAttribute("title", "nur im Rumpf"); } }'), (
        "Ein title INNERHALB des onClick-Rumpfes gilt als Name des Knopfes. "
        "Dann ist jeder Knopf benannt, der irgendwo das Wort title enthaelt.")
    assert not code_scan.hat_namen('{ onClick: ()=>0 }')


def test_koeder_bedingung_ist_ein_aufruf():
    """🔴 Der Koeder, den es bis v3.9.962 nicht gab.

    Der alte Koeder benutzte `imeiBusy?'…':'✓'` - einen nackten Bezeichner,
    also die Form, die der Riegel ohnehin kannte. Er hat die Blindheit
    BESTAETIGT statt sie aufzudecken, und dahinter stand ein echter Knopf:
    der Freigabe-Umschalter der Planliste in VPlan, reines Symbol, ohne Text
    und ohne Attribut, gefunden erst am 27.09.2026 mit einem fremden Messgeraet.

    Dieser Koeder traegt die Form, an der der Riegel gescheitert ist.
    """
    fall = ("h('button',{onClick:x},"
            "istFrei(pl.id)?'\U0001F517':'\U0001F4E4')")
    fund = _namenlos(fall)
    assert fund, (
        "\U0001F534 Ein Knopf mit einem AUFRUF als Ternaer-Bedingung und zwei "
        "reinen Symbolen wurde NICHT gemeldet.\n"
        "  Genau daran ist der Riegel aus v3.9.961 vorbeigelaufen."
    )


def test_gegenprobe_aufruf_mit_sichtbarem_wort():
    """Und die andere Richtung: mit einem Wort darf er NICHT anschlagen.

    Ohne diese Probe waere ein Melder, der jeden Ternaer meldet, gruen - und
    ein Riegel, der alles meldet, misst so wenig wie einer, der schweigt.
    """
    fall = ("h('button',{onClick:x},"
            "istFrei(pl.id)?'\U0001F517 Freigegeben':'\U0001F4E4 Freigeben')")
    assert not _namenlos(fall), (
        "\U0001F534 Ein Knopf mit sichtbarem Wort wurde als namenlos gemeldet."
    )
