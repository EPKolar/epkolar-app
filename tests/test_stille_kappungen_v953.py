# -*- coding: utf-8 -*-
"""v3.9.953 - die dritte Form des Beschnitts, systematisch.

DIE DREI FORMEN
───────────────
(a) `overflow:hidden` + `text-overflow:ellipsis` - es wird wirklich gekuerzt,
    und der Nutzer sieht es an den Punkten.
(b) Kastenueberlauf bei `overflow:visible` - der Text wird ausserhalb des
    Kastens gezeichnet und geht NICHT verloren. Das Kriterium
    `scrollWidth > clientWidth` allein unterscheidet (a) und (b) nicht.
(c) Der Text wird IN JAVASCRIPT gekappt, bevor er ins DOM kommt. Kein
    overflow, kein ellipsis, kein Kasten - ein CSS-Pruefstand kann sie
    grundsaetzlich nicht finden, weil CSS gar nicht beteiligt ist. Der
    Beschnitt-Melder meldete fuer die Auswertungen "0 wirklich gekuerzt":
    korrekt nach seiner Vorschrift und trotzdem die falsche Antwort auf die
    Frage, ob Text verloren geht.

DIE SCHAEDLICHE KOMBINATION
───────────────────────────
Nicht jede Kappung ist ein Fehler. Schaedlich ist sie, wenn BEIDES fehlt: der
Nutzer sieht NICHT, dass etwas fehlt (kein Auslassungszeichen), UND er kommt
nicht heran (kein title, keine Detailansicht). Dann haelt er die gekuerzte
Fassung fuer den ganzen Wert.

WAS GEMESSEN WURDE
──────────────────
256 programmatische Kuerzungen im Code. Davon sind die allermeisten keine
Anzeigekuerzung: 65 mal `slice(0,10)` auf ein ISO-Datum (Formatierung),
Fehlermeldungen und Protokollauszuege fuer die Konsole, Dateinamenlaengen,
und Listenbegrenzungen (`.slice(0,8).map(...)` zeigt weniger ZEILEN, nicht
weniger Zeichen - eigene Frage, nicht diese).
Es blieben 45 Stellen, deren Ergebnis als KIND eines createElement gerendert
wird. Zwoelf davon kuerzten Anzeigetext ohne Zeichen und ohne Zugang. Sie
gehen jetzt ueber `_kurz`.
"""
import io
import re

from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]


def _roh():
    return io.open(str(WURZEL / "index.html"), encoding="utf-8",
                   newline="").read()


def _code_feld(roh):
    import sys
    sys.path.insert(0, str(WURZEL / "scripts"))
    from code_scan import ist_code, eichen
    ok, gefunden, erwartet = eichen(roh)
    assert ok, "Eichung gescheitert (%d von %d)" % (gefunden, erwartet)
    return ist_code(roh)


# ── Die bewussten Faelle, NAMENTLICH ──────────────────────────────────────
# Kein Muster wie "alles unter 20 Zeichen ist Absicht" - das wuerde die
# naechste stille Kappung durchlassen. Jede Ausnahme steht hier mit ihrem
# Grund, und eine NEUE Stelle macht diesen Riegel rot.
BEWUSST = {
    "(name||'?').substring(0,2)":
        "Namenskuerzel im Sprechblasenbild - zwei Zeichen sind der Zweck",
    'a.entity_id.substring(0,16)':
        "Kennung eines Protokolleintrags - eine volle UUID ist unlesbar",
    'jupCfg.passport.slice(0,8)':
        "Anfang eines Geheimnisses, TRAEGT bereits ein Auslassungszeichen",
}

# Datums- und Zeitschnitte: das ist Formatierung, kein Beschnitt.
DATUMS_LAENGEN = {4, 7, 10}


def _kandidaten(roh, feld):
    """Kuerzungen, deren Ergebnis als Kind eines createElement gerendert wird.

    Die Abgrenzung laeuft ueber das schliessende `}}` der Eigenschaften: was
    danach und vor dem naechsten `createElement` steht, ist Kind-Teil.
    """
    aus = []
    for m in re.finditer(r"\.(?:slice|substring)\(0,\s*(\d{1,3})\)", roh):
        if not feld[m.start()]:
            continue
        n = int(m.group(1))
        if n >= 150:
            continue                      # Fehlermeldung / Protokollauszug
        vor = roh[max(0, m.start() - 260):m.start()]
        i = vor.rfind("}}")
        if i < 0 or not vor[i:].startswith("}}") or "createElement" in vor[i:]:
            continue
        nach = roh[m.end():m.end() + 24]
        if re.match(r"\s*\.(map|join|forEach|filter|reverse|sort)\b", nach):
            continue                      # Listenbegrenzung, nicht Text

        # Drei Arten, die mein erster Sucher faelschlich gemeldet hat. Sie
        # werden nach ART ausgeschlossen, nicht nach Namen - eine Liste von
        # Namen waere Blindheit auf Bestellung, eine Art ist eine Aussage.
        kopf = roh[max(0, m.start() - 90):m.start()]
        #  (1) Das Ergebnis wird einer Variablen ZUGEWIESEN - dann ist es kein
        #      gerendertes Kind. Beleg: `ps=ps.slice(0,50)` (PLZ-Liste).
        if re.search(r"(?:var|let|const\s)?\s*[\w$.]+\s*=\s*[\w$.()|'\"\[\] ]*$",
                     kopf) and "=" in kopf[-60:]:
            continue
        #  (2) Es steht in einer KONSOLENMELDUNG. Beleg: der Hinweis auf
        #      korruptes JSON in `_jo`. Die Konsole ist nicht das Bild.
        #      Geprueft wird ueber die NAEHE, nicht ueber ein Klammermuster:
        #      mein erster Versuch verlangte `console.x(` ohne Klammer bis zur
        #      Kuerzung, und der Aufruf enthielt selbst eine (`(s+'')`).
        i_console = max(kopf.rfind("console." + w) for w in
                        ("log", "warn", "error", "info", "table", "debug"))
        if i_console >= 0 and i_console > kopf.rfind("createElement"):
            continue
        #  (3) Es ist das Argument eines ZUSTANDSSETZERS. Beleg:
        #      `setJupSyncLog(rows.slice(0,20))` - das begrenzt eine Liste,
        #      bevor sie ueberhaupt gerendert wird.
        if re.search(r"\bset[A-Z]\w*\s*\([^)]{0,120}$", kopf):
            continue

        aus.append((m.start(), n,
                    roh[m.start() - 30:m.end()].replace("\r\n", " ")))
    return aus


def test_keine_stille_kappung_von_anzeigetext():
    """DER RIEGEL. Rot, sobald eine neue Kappung ohne Zeichen und ohne
    Ausnahme dazukommt."""
    roh = _roh()
    feld = _code_feld(roh)
    kand = _kandidaten(roh, feld)

    assert kand, (
        "KOEDER STUMM: keine einzige gerenderte Kuerzung gefunden. Der Sucher "
        "misst dann nichts - und die Datums-Schnitte allein gibt es mit "
        "Sicherheit noch.")

    still = []
    for p, n, kennung in kand:
        if n in DATUMS_LAENGEN:
            continue                      # Datum/Monat/Jahr
        if any(b in kennung for b in BEWUSST):
            continue
        nach = roh[p:p + 80]
        if "…" in nach[:40]:
            continue                      # traegt ein Zeichen
        still.append((roh.count("\n", 0, p) + 1, n, kennung))

    assert not still, (
        "Stille Kappungen von Anzeigetext (Zeile, Laenge, Stelle): %s\n"
        "Jede gekuerzte Anzeige braucht mindestens EINES von beidem:\n"
        "  * ein Auslassungszeichen, damit der Nutzer SIEHT, dass etwas fehlt\n"
        "  * einen Zugang zum vollen Wert (title, Detailansicht)\n"
        "Der Helfer `_kurz(text,n)` liefert das Zeichen; einen title gibt es "
        "nur dort, wo ein eigenes Element steht.\n"
        "Ist die Kuerzung fachlich richtig (Kuerzel, Kennung, fester "
        "Laenge), gehoert sie namentlich in BEWUSST - mit Grund." % still)


def test_der_helfer_haengt_das_zeichen_nur_bei_kuerzung_an():
    """Ein Zeichen an jedem Wert waere Laerm und wuerde bedeuten, dass man
    dem Zeichen nicht mehr glaubt."""
    roh = _roh()
    i = roh.find("function _kurz(t,n){")
    assert i > 0, "KOEDER STUMM: `_kurz` wurde nicht gefunden."
    rumpf = roh[i:i + 200]
    assert "s.length>n?" in rumpf, (
        "`_kurz` prueft nicht mehr, OB gekuerzt wird - dann haengt es das "
        "Zeichen auch an ungekuerzte Werte.")
    assert "\\u2026" in rumpf or "…" in rumpf, (
        "`_kurz` haengt kein Auslassungszeichen mehr an.")
    assert 'String(t==null?""' in rumpf, (
        "`_kurz` faengt null/undefined nicht mehr ab - dann steht 'null' im "
        "Bild, wo vorher nichts stand.")


def test_die_zwoelf_stellen_benutzen_den_helfer():
    """Namentlich, damit eine Rueckumstellung auffaellt."""
    roh = _roh()
    erwartet = [
        ("AS-Karte, Kunde oder Arbeitstext", "a.kundName||_kurz(a.arbeitsanweisungen,25)"),
        ("AS-Karte, Arbeitstext", '_kurz(a.arbeitsanweisungen,60)'),
        ("Regie, Arbeitstext", "_kurz(f.arbeit,60)"),
        ("Material, Artikelname", "_kurz(p.name,20)"),
        ("Wochenplan, Bauvorhaben 22", "_kurz(rr.bvh,22)"),
        ("Wochenplan, Bauvorhaben 18", "_kurz(rr.bvh,18)"),
        ("Wochenplan, Monteursname", "_kurz(nm,6)"),
        ("Abwesenheiten, Art am Telefon", "_kurz(v.l,12)"),
        ("Admin, Datanorm-Adresse", "_kurz(s.datanorm_url"),
        ("AS-Formular, Push-Fehler", "_kurz(form.push_error,40)"),
        ("Maengel, Beschreibung", "_kurz(m.beschreibung,60)"),
        ("Formularliste, Zusammenfassung", "_kurz((f.arbeit||f.bv||f.bereich"),
    ]
    fehlt = [name for name, marke in erwartet if marke not in roh]
    assert not fehlt, (
        "Diese Stellen kuerzen wieder ohne Zeichen: %s" % fehlt)


def test_wo_ein_element_da_war_gibt_es_auch_den_vollen_wert():
    """Das Zeichen sagt, DASS etwas fehlt. Der title gibt es her.

    Nur dort geprueft, wo ein eigenes Element steht - bei einem Textstueck
    mitten in einer Verkettung gibt es kein Element, an das ein title
    gehoerte, und dann ist das Zeichen alles, was bleibt. Das ist eine
    Grenze des Verfahrens und keine vergessene Stelle.
    """
    roh = _roh()
    for name, marke in (
        ("Regie, Arbeitstext", 'title:(f.arbeit||"")'),
        ("Material, Artikelname", 'title:(p.name||"")'),
    ):
        assert marke in roh, (
            "%s: der volle Wert steht nicht mehr im title." % name)


def test_koeder_der_sucher_findet_eine_eingesetzte_stille_kappung():
    """DIE SELBSTPROBE. Ein Riegel mit Ausnahmen kann blind werden - drei
    Arten sind hier ausgeschlossen (Zuweisung, Konsolenmeldung,
    Zustandssetzer), und jede Ausnahme ist eine Gelegenheit, zu viel
    auszuschliessen.

    Also wird eine stille Kappung EINGESETZT und verlangt, dass der Sucher sie
    findet. Findet er sie nicht, meldet er gruen, weil er nichts sieht - und
    das ist der haeufigste Ausfall dieser ganzen Riegelsammlung.
    """
    roh = _roh()
    feld = _code_feld(roh)
    vorher = len(_kandidaten(roh, feld))

    # Eine Kappung in Kind-Position, ohne Zeichen, ohne title - genau die
    # schaedliche Kombination. Angehaengt an eine Stelle, die sicher Code ist.
    koeder = ('React.createElement(\'div\', { style: {fontSize:12}}, '
              '(__koeder_wert||"").substring(0,30))')
    marke = "function _kurz(t,n){"
    i = roh.index(marke)
    kaputt = roh[:i] + koeder + roh[i:]

    feld2 = _code_feld(kaputt)
    gefunden = _kandidaten(kaputt, feld2)
    assert len(gefunden) == vorher + 1, (
        "KOEDER NICHT GEFUNDEN: der Sucher fand vorher %d und mit der "
        "eingesetzten stillen Kappung %d Stellen. Er sieht sie also nicht - "
        "dann ist sein Gruen oben kein Ergebnis, sondern Blindheit. "
        "Vermutlich schliesst eine der drei Arten zu viel aus."
        % (vorher, len(gefunden)))

    # Und sie muss auch als STILL erkannt werden, nicht nur gefunden.
    neu = [k for k in gefunden if "__koeder_wert" in k[2]]
    assert len(neu) == 1, "Der Koeder wurde nicht als eigene Stelle gezaehlt."
    assert neu[0][1] == 30, "Die Laenge des Koeders wurde falsch gelesen."
