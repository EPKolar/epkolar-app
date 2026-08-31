# -*- coding: utf-8 -*-
"""v3.9.924 - Der Vorbau ueber der Arbeitsschein-Liste, offener Punkt 27.

GEMESSEN, BEVOR ETWAS GEAENDERT WURDE
─────────────────────────────────────
Mit `scripts/as_vorbau_messen.py` (neu, misst y-Werte statt Eindruecke):

  Schirm 1440x900   Tabellen-Kopfzeile y = 887, erste Schein-ZEILE y = 966
                    -> 107 % der Schirmhoehe, kein Schein ohne Rollen
  Schirm  390x900   erste Schein-KARTE y = 1189
                    -> 132 % der Schirmhoehe

Davon entfallen auf die elf Kennzahl-Kacheln 405 px am Rechner und 613 px am
Telefon - in beiden Faellen rund die HAELFTE des gesamten Vorbaus. Der Rest
sind Ueberschrift, Reiterzeile, sieben Schnellfilter, Suche und Zaehlzeile.

WAS DIE ELF KACHELN SIND - GEMESSEN, NICHT VERMUTET
───────────────────────────────────────────────────
Klickprobe (jede Kachel klicken, danach das Status-Auswahlfeld zuruecklesen,
mit Gegenprobe auf die Ueberschrift, die nichts setzen darf):

  Kachel                Status-Feld danach     Auswahlfeld-Eintrag darunter
  Gesamt                alle                   "Alle Status"
  Offen (alle)          offen_bearb            "— Offen (alle) —"
  8 x AS_STATUS         der jeweilige Wert     die acht Status-Eintraege
  Fertig (alle)         fertig                 "— Fertig (alle) —"

Die elf Kacheln setzen also GENAU die elf Werte, die das Auswahlfeld drei
Zeilen tiefer ohnehin anbietet - dieselbe Zustandsgroesse (`filterStatus`),
dieselbe Wirkung. Die Kachelreihe ist ein BILD des Auswahlfeldes.
Das ist derselbe Befund wie in v3.9.906 ("jeder Filter stand doppelt da"),
nur eine Etage hoeher und 405 px teuer statt 44.

WAS TROTZDEM NICHT GESTRICHEN WURDE
───────────────────────────────────
Die Zahlen. Eine Kachel auf 0 ist eine Aussage ("da liegt nichts"), und wer
sie verbirgt, nimmt die Aussage zurueck. Geaendert wird ausschliesslich die
GEOMETRIE: kein onClick, kein Wert, keine Kachel weniger, keine Unterzeile
weniger. Genau das nageln die Riegel unten fest.

GEMESSEN NACHHER (dieselbe Saat, dieselben Schirme)
───────────────────────────────────────────────────
  1440x900   Kachelblock 405 -> 161 px   erste Zeile  966 -> 722   sichtbar
   390x900   Kachelblock 613 -> 259 px   erste Karte 1189 -> 858   sichtbar

WAS NACHGEMESSEN UND DESHALB VERWORFEN WURDE
────────────────────────────────────────────
  * Vier Spalten am Telefon: bringt gemessen 25 px (833 statt 858) und
    SCHNEIDET dabei "erledigt+abgerechnet" ab - die Kachel traegt
    overflow:hidden. Fuenf Spalten schneidet die ZAHL ab. Das ist der
    Fehler aus v3.9.115, und er waere lautlos gewesen.
  * Die Unterzeile abschalten: bringt gemessen 50 px (858 -> 808).
    Zu wenig, um dafuer Text wegzunehmen.

WAS DIESE VERSION AUSDRUECKLICH NICHT LOEST
───────────────────────────────────────────
Am Telefon steht die erste Karte danach bei y = 858 von 900 - sichtbar,
aber knapp, und auf einem Geraet mit Browserleiste wieder nicht. Der Rest
des Vorbaus (Ueberschrift 114 px, Reiter 48, Schnellfilter 48, Suche 94,
Zaehlzeile 18, Sortierzeile 44) besteht aus Bedienelementen, die etwas tun.
Wer dort weiter will, muss WEGNEHMEN, nicht verkleinern - und das ist keine
Aufraeumarbeit mehr.

WIDERSPRICHT DAS DEN BESTEHENDEN RIEGELN?
─────────────────────────────────────────
Nein, und beide wurden geprueft:
  * `test_as_liste_entlastet_v906.py` haelt fest, dass die vier
    Auswahlfelder auf dem Handy einklappbar sind und die Chips bleiben.
    Hier wird an Auswahlfeldern, Chips und Zeilen-Editoren nichts
    angefasst - der Kachelblock steht ueber alledem.
  * `test_as_zeile_rangordnung_v918.py` haelt fest, dass die sechs
    Zeilen-Editoren bleiben. Auch daran aendert sich nichts.
Beide Riegel gelten unveraendert weiter.
"""
import re

from _hilfen import nur_code

# Der Anker des Kachelblocks - ab hier bis zur Reiterzeile stehen die elf.
BLOCK_START = 'className: "kpi-grid epk-leiste"'
BLOCK_ENDE = 'className: "tab-bar"'


def _kachelblock(index_html):
    i = index_html.find(BLOCK_START)
    assert i != -1, (
        "Der Kachelblock der Arbeitsschein-Liste traegt die Klasse "
        "epk-leiste nicht mehr - dann ist der Vorbau wieder 405 px hoch."
    )
    j = index_html.find(BLOCK_ENDE, i)
    assert j != -1, "Die Reiterzeile hinter dem Kachelblock fehlt."
    return index_html[i:j]


# ══ Die Klasse selbst ═══════════════════════════════════════════════════════

def test_die_klasse_gibt_es_und_sie_ist_an_kpi_grid_gebunden(index_html):
    """Der Vorsatz .kpi-grid ist keine Zierde. Die Klasse .kpi-grid wird an
    ELF Stellen der App benutzt, und mehrere Breiten-Regeln setzen fuer sie
    !important. Ohne Vorsatz haetten die neuen Regeln dieselbe Spezifitaet und
    wuerden dort verlieren - lautlos, und nur auf manchen Schirmbreiten."""
    treffer = re.findall(r"[^\s,{]*\.epk-leiste", index_html)
    assert treffer, "Die Klasse .epk-leiste steht nirgends im CSS."
    ohne_vorsatz = [t for t in treffer if not t.startswith(".kpi-grid")]
    assert not ohne_vorsatz, (
        "Diese .epk-leiste-Regeln stehen ohne den Vorsatz .kpi-grid: %s. "
        "Sie verlieren dann gegen die !important-Regeln der Breiten-Bloecke."
        % ohne_vorsatz
    )


def test_die_klasse_wird_genau_einmal_angewendet(index_html):
    """GEGENPROBE gegen das Ueberlaufen. Es gibt elf kpi-grid-Bloecke in der
    App (Projekte, Fahrzeuge, Plaene, Chef-Portal ...). Eine zweite Anwendung
    waere eine Aenderung an einem Reiter, der hier gar nicht gemessen wurde."""
    n = nur_code(index_html).count('"kpi-grid epk-leiste"')
    assert n == 1, (
        "epk-leiste ist %d mal angewendet, erwartet wird genau einmal "
        "(die Arbeitsschein-Liste). Jede weitere Stelle aendert einen "
        "Reiter, fuer den kein y-Wert gemessen wurde." % n
    )


def test_die_klasse_verbirgt_nichts(index_html):
    """DIE LEITREGEL DIESER VERSION. Eine Kachel auf 0 ist eine Aussage. Der
    Weg 'wir blenden die Nullen aus' waere billig gewesen und haette dem Chef
    die Information genommen, dass da nichts liegt. Die Klasse darf deshalb
    NICHTS auf display:none setzen - sie darf nur kleiner machen."""
    regeln = re.findall(r"\.kpi-grid\.epk-leiste[^{}]*\{[^{}]*\}", index_html)
    assert len(regeln) >= 5, (
        "Nur %d epk-leiste-Regeln gefunden - der Block sieht unvollstaendig "
        "aus, dann misst dieser Riegel womoeglich gar nichts." % len(regeln)
    )
    versteckt = [r for r in regeln if "display" in r and "none" in r]
    assert not versteckt, (
        "Eine epk-leiste-Regel blendet etwas aus: %s. Der Vorbau sollte "
        "kleiner werden, nicht luegen." % versteckt
    )


def test_die_unterzeile_bleibt_und_wird_nur_kleiner(index_html):
    """Die Unterzeile ('offen', 'fertig', 'zu erledigen') abzuschalten haette
    gemessen 50 px gebracht. Sie ist aber Text, und 50 px sind kein Grund."""
    regel = re.search(
        r"\.kpi-grid\.epk-leiste > div > div:nth-child\(4\)[^{}]*\{([^{}]*)\}",
        index_html)
    assert regel, "Die Regel fuer die Unterzeile fehlt."
    assert "font-size" in regel.group(1), (
        "Die Unterzeile wird nicht verkleinert - dann traegt der Block "
        "wieder die alte Hoehe."
    )
    assert "display" not in regel.group(1), (
        "Die Unterzeile wird ausgeblendet statt verkleinert."
    )


def test_kpi_grid_selbst_bleibt_unangetastet(index_html):
    """GEGENPROBE zur Abgrenzung: zehn andere Reiter haengen an derselben
    Grundregel. Wer sie anfasst, aendert Bildschirme, die niemand gemessen
    hat - genau der Fehler, den v3.9.918/920 vermieden haben."""
    assert (".kpi-grid { display: grid; grid-template-columns: repeat(4,1fr);"
            " gap: 12px; }" in index_html), (
        "Die Grundregel .kpi-grid wurde veraendert. Sie gilt fuer elf "
        "Bloecke in der App; gemessen wurde nur einer."
    )


# ══ Die elf Kacheln ═════════════════════════════════════════════════════════

def test_alle_elf_kacheln_behalten_ihren_klick(index_html):
    """DIE EIGENTLICHE EIGENSCHAFT. Der Befund war: die Kacheln SIND
    Bedienelemente, keine Dekoration - jede setzt filterStatus. Genau deshalb
    durften sie bleiben. Verlieren sie den Klick, waeren 161 px Dekoration
    uebrig, und die ganze Begruendung dieser Version faellt."""
    block = _kachelblock(index_html)
    n = block.count("onClick: ()=>_scrollToScheinListe(")
    assert n == 4, (
        "Im Kachelblock haengen %d Klick-Zuweisungen, erwartet werden vier "
        "(Gesamt, Offen alle, die Schleife ueber AS_KPI_KACHELN, Fertig "
        "alle). Eine Kachel ohne Klick ist Dekoration mit voller Hoehe." % n
    )


def test_es_sind_weiterhin_elf_kacheln(index_html):
    """Drei feste plus acht aus AS_KPI_KACHELN. Diese Version nimmt keine
    einzige weg - sie legt sie nur flacher.

    ERSTER ANLAUF WAR FALSCH und hat sofort angeschlagen: gezaehlt wurden
    "feste" Kacheln als `React.createElement(Kpi, {` - aber die Schleife
    enthaelt denselben Aufruf, also kamen vier statt drei heraus. Der Riegel
    hatte recht und die Erwartung war falsch. Jetzt getrennt gezaehlt."""
    block = _kachelblock(index_html)
    aufrufe = block.count("React.createElement(Kpi, {")
    assert aufrufe == 4, (
        "Im Kachelblock stehen %d Kpi-Aufrufe, erwartet werden vier: drei "
        "feste (Gesamt, Offen alle, Fertig alle) und einer in der Schleife."
        % aufrufe
    )
    schleife = block.count("AS_KPI_KACHELN.map(")
    assert schleife == 1, (
        "Die Status-Kacheln kommen %d mal aus AS_KPI_KACHELN, erwartet wird "
        "genau einmal - sonst ist Sebastians Entscheidungszeile wirkungslos "
        "oder sie wirkt doppelt." % schleife
    )
    # Und die Schleife laeuft heute ueber acht Status: 3 + 8 = 11 Kacheln,
    # genau die elf, die am 30.08. gemessen wurden.
    i = index_html.find("const AS_STATUS={")
    j = index_html.find("};", i)
    assert i != -1 and j != -1, "AS_STATUS wurde nicht gefunden."
    n = index_html[i:j].count("grp:")
    assert n == 8, (
        "AS_STATUS traegt %d Status, gemessen wurden acht (3 feste Kacheln "
        "+ 8 = die elf, um die es in Punkt 27 geht)." % n
    )


# ══ Die eine Zeile, die Sebastian gehoert ═══════════════════════════════════

def test_die_auswahl_ist_eine_zeile_und_heute_vollstaendig(index_html):
    """Welche Kennzahlen der Chef taeglich braucht, steht in KEINER Datei -
    das kann hier niemand entscheiden. Also wird die Entscheidung vorbereitet
    statt getroffen: AS_KPI_KACHELN ist heute die vollstaendige Liste, es
    faellt nichts weg, und wer kuerzen will, aendert genau diese Zeile."""
    code = nur_code(index_html)
    m = re.search(r"const AS_KPI_KACHELN=([^;]+);", code)
    assert m, "AS_KPI_KACHELN gibt es nicht - dann ist die Auswahl keine Zeile."
    assert m.group(1).strip() == "Object.keys(AS_STATUS)", (
        "AS_KPI_KACHELN ist bereits gekuerzt (%s). Diese Version darf nichts "
        "wegnehmen; das Kuerzen ist Sebastians Entscheidung, nicht ihre."
        % m.group(1).strip()
    )


def test_das_auswahlfeld_bleibt_vollstaendig_egal_was_in_der_zeile_steht(index_html):
    """DIE BEDINGUNG, UNTER DER DIE EINE ZEILE BILLIG IST. Wird eine Kachel
    gestrichen, muss ihre Zahl anders erreichbar bleiben - sonst ist es kein
    Aufraeumen, sondern ein Funktionsverlust (dieselbe Pruefung, an der in
    v3.9.918 der sachbearbeiter-Editor haengen geblieben ist).
    Das Status-Auswahlfeld liest AS_STATUS, NICHT AS_KPI_KACHELN. Es bietet
    also weiter jeden Status an, auch einen ohne Kachel."""
    # "value: filterStatus" kommt DREIMAL vor (andere Reiter fuehren eine
    # gleichnamige Groesse). Der Eintrag offen_bearb kommt genau einmal vor
    # und gehoert zum Auswahlfeld der Arbeitsschein-Liste - deshalb er.
    marke = '{ value: "offen_bearb"}'
    assert index_html.count(marke) == 1, (
        "Der Anker fuers Status-Auswahlfeld ist nicht mehr eindeutig "
        "(%d Treffer) - dann misst dieser Riegel womoeglich ein anderes Feld."
        % index_html.count(marke)
    )
    i = index_html.find(marke)
    feld = index_html[i - 320:i + 520]
    assert "value: filterStatus, onChange:" in feld, (
        "Der gefundene Eintrag haengt nicht am Status-Auswahlfeld."
    )
    assert "Object.entries(AS_STATUS).map(" in feld, (
        "Das Status-Auswahlfeld liest nicht mehr AS_STATUS. Damit waere eine "
        "gestrichene Kachel nirgends mehr erreichbar - und das Kuerzen von "
        "AS_KPI_KACHELN waere teuer statt billig."
    )
    assert "AS_KPI_KACHELN" not in feld, (
        "Das Auswahlfeld haengt jetzt an AS_KPI_KACHELN. Dann nimmt eine "
        "gestrichene Kachel den Status komplett aus der Bedienung."
    )


def test_die_chips_lesen_ebenfalls_as_status(index_html):
    """Zweiter Weg zur selben Zahl: der aktive Filter steht als Chip da und
    benennt sich aus AS_STATUS."""
    assert ("(AS_STATUS[filterStatus]&&AS_STATUS[filterStatus].l)"
            in index_html), (
        "Der Status-Chip benennt sich nicht mehr aus AS_STATUS."
    )


# ══ Umkehrprobe ═════════════════════════════════════════════════════════════

def test_selbsttest_riegel_schlagen_beim_rueckbau_an(index_html):
    """Vier Rueckbauten, vier Riegel. Ein Riegel, der seinen eigenen Rueckbau
    nicht bemerkt, ist im Bestand dieses Repos mehrfach gruen gewesen und hat
    nichts gemessen."""
    # 1. Klasse wieder abgenommen
    z1 = index_html.replace('"kpi-grid epk-leiste"', '"kpi-grid"', 1)
    assert z1 != index_html, "Rueckbau 1 griff nicht"
    assert nur_code(z1).count('"kpi-grid epk-leiste"') == 0, (
        "Umkehrprobe: der Anwendungs-Riegel wuerde eine abgenommene Klasse "
        "nicht bemerken"
    )

    # 2. Klasse ein zweites Mal angewendet
    z2 = index_html.replace('className: "kpi-grid", style: {marginBottom:16}',
                            'className: "kpi-grid epk-leiste", '
                            'style: {marginBottom:16}', 1)
    assert z2 != index_html, "Rueckbau 2 griff nicht"
    assert nur_code(z2).count('"kpi-grid epk-leiste"') == 2, (
        "Umkehrprobe: eine zweite Anwendung wuerde unbemerkt bleiben"
    )

    # 3. Nullen verstecken - der Weg, der ausdruecklich nicht gegangen wurde
    z3 = index_html.replace(
        ".kpi-grid.epk-leiste > div > div:nth-child(3) { font-size: 18px",
        ".kpi-grid.epk-leiste > div > div:nth-child(3) { display: none; "
        "font-size: 18px", 1)
    assert z3 != index_html, "Rueckbau 3 griff nicht"
    regeln = re.findall(r"\.kpi-grid\.epk-leiste[^{}]*\{[^{}]*\}", z3)
    assert [r for r in regeln if "display" in r and "none" in r], (
        "Umkehrprobe: der Versteck-Riegel wuerde ein display:none nicht sehen"
    )

    # 4. Einer Kachel den Klick genommen
    z4 = index_html.replace(
        'sub: "zu erledigen" , color: "#eab308", i: 1, '
        'onClick: ()=>_scrollToScheinListe("offen_bearb")',
        'sub: "zu erledigen" , color: "#eab308", i: 1', 1)
    assert z4 != index_html, "Rueckbau 4 griff nicht"
    assert _kachelblock(z4).count(
        "onClick: ()=>_scrollToScheinListe(") == 3, (
        "Umkehrprobe: eine Kachel ohne Klick wuerde unbemerkt bleiben"
    )
